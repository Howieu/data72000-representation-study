"""Main dual-representation clustering engine.

The module owns only the clustering stage.  Feature engineering and the
cohort definition are read from the frozen derived tables and protocol.
"""

from __future__ import annotations

import contextlib
import io
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from ..protocol import classix_radii, load_protocol
from .metrics import (
    cluster_sizes,
    evaluate_partition,
    hungarian_alignment,
    paired_partition_metrics,
)
from .schema import SCHEMAS, validate_schema, write_schema_files

try:
    from classix import CLASSIX
except ImportError:  # pragma: no cover - exercised only in minimal installs
    CLASSIX = None


ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PROTOCOL = ROOT / "protocol" / "analysis_protocol.json"
DEFAULT_DERIVED = ROOT / "data" / "derived"
DEFAULT_RESULTS = ROOT / "results" / "retailrocket"


def _stable_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _classix_fit(X: np.ndarray, params: dict[str, Any]) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    if CLASSIX is None:
        raise RuntimeError("classixclustering==1.5.1 is required for the primary run")
    with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
        estimator = CLASSIX(
            sorting="pca", metric="euclidean", radius=float(params["radius"]),
            minPts=int(params["minPts"]), group_merging=str(params["group_merging"]),
            mergeScale=1.5, post_alloc=False, mergeTinyGroups=True, verbose=0,
        )
        estimator.fit(X)
    labels = np.asarray(estimator.labels_, dtype=int)
    return labels, time.perf_counter() - started


@dataclass(frozen=True)
class RepresentationData:
    name: str
    visitorid: np.ndarray
    raw: np.ndarray
    features: tuple[str, ...]
    transformed: np.ndarray
    scaled: np.ndarray
    scaler: StandardScaler


def load_representations(
    derived_dir: Path = DEFAULT_DERIVED,
    protocol_path: Path = DEFAULT_PROTOCOL,
) -> dict[str, RepresentationData]:
    """Load, transform and separately standardize compact and rich tables."""
    protocol = load_protocol(protocol_path)
    del protocol  # loading here makes an accidental unfrozen run conspicuous
    schema = pd.read_csv(derived_dir / "feature_schema.csv")
    schema_map = dict(zip(schema["feature"].astype(str), schema["transform"].astype(str)))
    compact = pd.read_csv(derived_dir / "compact_features.csv")
    rich = pd.read_csv(derived_dir / "rich_features.csv")
    if not compact["visitorid"].equals(rich["visitorid"]):
        raise ValueError("compact and rich tables must have identical visitor order")
    if compact["snapshot_id"].nunique() != 1 or rich["snapshot_id"].nunique() != 1:
        raise ValueError("each representation must have one snapshot")
    if compact["snapshot_id"].iloc[0] != rich["snapshot_id"].iloc[0]:
        raise ValueError("representations must use the same snapshot")
    auxiliary = {"visitorid", "snapshot_id", "category_coverage_flag"}
    names = {
        "compact": tuple(c for c in compact.columns if c not in auxiliary),
        "rich": tuple(c for c in rich.columns if c not in auxiliary),
    }
    tables = {"compact": compact, "rich": rich}
    out: dict[str, RepresentationData] = {}
    for name, features in names.items():
        if any(feature not in schema_map for feature in features):
            raise ValueError(f"feature schema missing columns for {name}")
        raw = tables[name].loc[:, list(features)].to_numpy(dtype=float)
        transformed = raw.copy()
        for index, feature in enumerate(features):
            if schema_map[feature].strip().lower() == "log1p":
                if np.any(raw[:, index] < 0):
                    raise ValueError(f"log1p feature is negative: {feature}")
                transformed[:, index] = np.log1p(raw[:, index])
        scaler = StandardScaler()
        scaled = scaler.fit_transform(transformed)
        if not np.isfinite(scaled).all():
            raise ValueError(f"non-finite scaled values in {name}")
        out[name] = RepresentationData(
            name=name,
            visitorid=tables[name]["visitorid"].to_numpy(dtype=np.int64),
            raw=raw,
            features=features,
            transformed=transformed,
            scaled=scaled,
            scaler=scaler,
        )
    return out


def candidate_grids(protocol: dict[str, Any]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Construct the frozen K Means and CLASSIX candidate lists."""
    kmeans = []
    for k in protocol["kmeans"]["k"]:
        kmeans.append({
            "method": "kmeans", "candidate_id": f"kmeans_k{int(k):02d}",
            "parameters": {"n_clusters": int(k), "init": "k-means++", "n_init": 20},
            "seed": int(protocol["primary_seed"]),
        })
    classix = []
    spec = protocol["classix"]
    for radius in classix_radii(protocol):
        for min_pts in spec["minPts"]:
            for merging in spec["group_merging"]:
                params = {
                    "sorting": "pca", "metric": "euclidean", "radius": float(radius),
                    "minPts": int(min_pts), "group_merging": str(merging),
                    "mergeScale": float(spec["mergeScale"]),
                    "mergeTinyGroups": True, "post_alloc": False,
                }
                classix.append({
                    "method": "classix",
                    "candidate_id": (
                        f"classix_r{radius:.2f}_m{int(min_pts)}_{merging}"
                    ),
                    "parameters": params, "seed": None,
                })
    if len(kmeans) != 11 or len(classix) != 186:
        raise AssertionError(f"frozen candidate count mismatch {len(kmeans)}, {len(classix)}")
    return kmeans, classix


KMEANS_CANDIDATES: tuple[dict[str, Any], ...] = tuple(
    {"method": "kmeans", "candidate_id": f"kmeans_k{k:02d}",
     "parameters": {"n_clusters": k, "init": "k-means++", "n_init": 20}, "seed": 20260801}
    for k in range(2, 13)
)
# This constant is populated from the frozen grid at import time where possible.
try:
    CLASSIX_CANDIDATES: tuple[dict[str, Any], ...] = tuple(candidate_grids(load_protocol(DEFAULT_PROTOCOL))[1])
except (FileNotFoundError, KeyError):  # pragma: no cover
    CLASSIX_CANDIDATES = ()


def run_candidate_grid(
    representations: dict[str, RepresentationData],
    protocol_path: Path = DEFAULT_PROTOCOL,
) -> tuple[pd.DataFrame, dict[tuple[str, str, str], np.ndarray]]:
    """Fit every frozen candidate and return rows plus in-memory labels."""
    protocol = load_protocol(protocol_path)
    kmeans_grid, classix_grid = candidate_grids(protocol)
    records: list[dict[str, Any]] = []
    labels: dict[tuple[str, str, str], np.ndarray] = {}
    for representation, data in representations.items():
        for candidate in [*kmeans_grid, *classix_grid]:
            params = candidate["parameters"]
            try:
                started = time.perf_counter()
                if candidate["method"] == "kmeans":
                    estimator = KMeans(
                        n_clusters=int(params["n_clusters"]), init="k-means++",
                        n_init=20, random_state=int(protocol["primary_seed"]),
                    )
                    candidate_labels = estimator.fit_predict(data.scaled).astype(int)
                    runtime = time.perf_counter() - started
                else:
                    candidate_labels, runtime = _classix_fit(data.scaled, params)
                diagnostics = evaluate_partition(data.scaled, candidate_labels)
                labels[(representation, candidate["method"], candidate["candidate_id"])] = candidate_labels
            except Exception as exc:  # retain invalid candidates as requested
                candidate_labels = np.full(len(data.visitorid), -1, dtype=int)
                labels[(representation, candidate["method"], candidate["candidate_id"])] = candidate_labels
                diagnostics = evaluate_partition(data.scaled, candidate_labels)
                diagnostics["error"] = f"{type(exc).__name__}: {exc}"
                runtime = time.perf_counter() - started
            row = {
                "representation": representation, "method": candidate["method"],
                "candidate_id": candidate["candidate_id"],
                "parameters": _stable_json(params), "seed": candidate["seed"],
                **diagnostics, "runtime_seconds": float(runtime),
                "cluster_sizes": _stable_json(cluster_sizes(candidate_labels)),
            }
            row["n_clusters_excluding_noise"] = row["n_clusters"]
            records.append(row)
    frame = pd.DataFrame(records)
    # Keep the documented order while allowing an optional error column.
    validate_schema(frame, "candidate_grid.csv")
    return frame, labels


def _sort_key(row: pd.Series) -> tuple[Any, ...]:
    def neg(value: Any, fallback: float = -np.inf) -> float:
        return -float(value) if pd.notna(value) else fallback
    return (
        neg(row.get("silhouette")), float(row.get("davies_bouldin")) if pd.notna(row.get("davies_bouldin")) else np.inf,
        neg(row.get("calinski_harabasz")), float(row.get("largest_non_noise_cluster_share", np.inf)),
        float(row.get("noise_fraction", np.inf)), int(row.get("n_clusters", 0)),
        str(row.get("parameters", "")),
    )


def select_configurations(
    candidates: pd.DataFrame,
    protocol: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Select both unconstrained and deployment-acceptable configurations."""
    protocol = protocol or load_protocol(DEFAULT_PROTOCOL)
    constraints = protocol["deployment_constraints"]
    rows: list[dict[str, Any]] = []
    for (representation, method), group in candidates.groupby(["representation", "method"], sort=True):
        sub = group.copy()
        valid = sub[sub["internal_valid"].fillna(False).astype(bool)].copy()
        acceptable = valid[
            valid["n_clusters"].between(int(constraints["min_clusters"]), int(constraints["max_clusters"]))
            & (valid["noise_fraction"] <= float(constraints["max_noise_fraction"]))
            & (valid["largest_non_noise_cluster_share"] <= float(constraints["max_largest_non_noise_cluster_share"]))
        ]
        choices = [
            ("unconstrained_silhouette", valid, "silhouette_max_unconstrained"),
            ("deployment_acceptable", acceptable, "silhouette_max_with_constraints"),
        ]
        for selection, pool, status in choices:
            if pool.empty:
                # Preserve the failure visibly.  Deterministically choose the
                # first candidate to keep labels and downstream schemas total.
                choice = sub.sort_values(["candidate_id"]).iloc[0]
                current_status = "no_valid_candidate" if valid.empty else "no_deployment_acceptable_candidate"
            else:
                choice = min((row for _, row in pool.iterrows()), key=_sort_key)
                current_status = status
            record = choice.to_dict()
            record["n_clusters_excluding_noise"] = record["n_clusters"]
            record.update({"selection": selection, "deployment_acceptable": bool(choice["candidate_id"] in set(acceptable["candidate_id"])),
                           "selection_status": current_status})
            rows.append(record)
    result = pd.DataFrame(rows)
    validate_schema(result, "selected_configurations.csv")
    return result


def _fixed_fit(data: RepresentationData, method: str, params: dict[str, Any], X: np.ndarray | None = None) -> np.ndarray:
    matrix = data.scaled if X is None else X
    if method == "kmeans":
        return KMeans(n_clusters=int(params["n_clusters"]), init="k-means++", n_init=20,
                      random_state=20260801).fit_predict(matrix).astype(int)
    labels, _ = _classix_fit(matrix, params)
    return labels


def selected_labels_frame(
    representations: dict[str, RepresentationData], selected: pd.DataFrame,
    labels: dict[tuple[str, str, str], np.ndarray],
) -> pd.DataFrame:
    records = []
    for _, row in selected.iterrows():
        key = (str(row["representation"]), str(row["method"]), str(row["candidate_id"]))
        visitorids = representations[str(row["representation"])].visitorid
        for visitorid, label in zip(visitorids, labels[key]):
            records.append({"visitorid": int(visitorid), "representation": key[0],
                            "method": key[1], "selection": row["selection"],
                            "candidate_id": key[2], "label": int(label)})
    frame = pd.DataFrame(records)
    validate_schema(frame, "selected_labels.csv")
    return frame


def paired_comparisons(
    representations: dict[str, RepresentationData],
    labels: dict[tuple[str, str, str], np.ndarray],
    selected: pd.DataFrame,
) -> pd.DataFrame:
    """Create fixed-k, fixed-CLASSIX-unit and independent-selection views."""
    rows: list[dict[str, Any]] = []
    left, right = "compact", "rich"
    by_id = lambda rep, method, cid: labels[(rep, method, cid)]
    for k in range(2, 13):
        cid = f"kmeans_k{k:02d}"
        rows.append({"comparison": "fixed_k", "method": "kmeans", "parameter_key": "n_clusters",
                     "parameter_value": str(k), "k": k, "left_representation": left,
                     "right_representation": right, "n_samples": len(by_id(left, "kmeans", cid)),
                     **paired_partition_metrics(by_id(left, "kmeans", cid), by_id(right, "kmeans", cid))})
    classix_ids = sorted(cid for (rep, method, cid) in labels if rep == left and method == "classix")
    for cid in classix_ids:
        params = json.loads(selected.iloc[0]["parameters"]) if False else None
        # Candidate ID fully identifies the fixed parameter unit and is stable
        # even when a candidate is invalid.
        rows.append({"comparison": "fixed_classix_parameter", "method": "classix",
                     "parameter_key": "candidate_id", "parameter_value": cid, "k": None,
                     "left_representation": left, "right_representation": right,
                     "n_samples": len(by_id(left, "classix", cid)),
                     **paired_partition_metrics(by_id(left, "classix", cid), by_id(right, "classix", cid))})
    for method in ("kmeans", "classix"):
        lrow = selected[(selected["representation"] == left) & (selected["method"] == method) &
                        (selected["selection"] == "deployment_acceptable")].iloc[0]
        rrow = selected[(selected["representation"] == right) & (selected["method"] == method) &
                        (selected["selection"] == "deployment_acceptable")].iloc[0]
        if not bool(lrow["deployment_acceptable"]) or not bool(rrow["deployment_acceptable"]):
            metric = {"ari": None, "nmi": None, "vi": None}
            comparison = "independent_deployment_selection_unavailable"
        else:
            metric = paired_partition_metrics(by_id(left, method, lrow["candidate_id"]),
                                               by_id(right, method, rrow["candidate_id"]))
            comparison = "independent_deployment_selection"
        rows.append({"comparison": "independent_deployment_selection", "method": method,
                     "parameter_key": "independent_candidate_ids",
                     "parameter_value": _stable_json({"compact": lrow["candidate_id"], "rich": rrow["candidate_id"]}),
                     "k": None, "left_representation": left, "right_representation": right,
                     "n_samples": len(by_id(left, method, lrow["candidate_id"])), **metric,
                     "availability": comparison})
    frame = pd.DataFrame(rows)
    validate_schema(frame, "paired_partition_comparison.csv")
    return frame


def transition_matrix(
    representations: dict[str, RepresentationData],
    labels: dict[tuple[str, str, str], np.ndarray],
    selected: pd.DataFrame,
) -> pd.DataFrame:
    """Build long-form Hungarian-aligned transition matrices for deployment."""
    records: list[dict[str, Any]] = []
    for method in ("kmeans", "classix"):
        lrow = selected[(selected["representation"] == "compact") & (selected["method"] == method) &
                        (selected["selection"] == "deployment_acceptable")].iloc[0]
        rrow = selected[(selected["representation"] == "rich") & (selected["method"] == method) &
                        (selected["selection"] == "deployment_acceptable")].iloc[0]
        if not bool(lrow["deployment_acceptable"]) or not bool(rrow["deployment_acceptable"]):
            continue
        source = labels[("compact", method, lrow["candidate_id"])]
        target = labels[("rich", method, rrow["candidate_id"])]
        mapping = hungarian_alignment(source, target)
        parameter_value = _stable_json({"compact": lrow["candidate_id"], "rich": rrow["candidate_id"]})
        for source_cluster in sorted(np.unique(source)):
            for target_cluster in sorted(np.unique(target)):
                count = int(np.sum((source == source_cluster) & (target == target_cluster)))
                if not count:
                    continue
                matched = int(mapping[int(target_cluster)])
                records.append({
                    "method": method, "comparison": "independent_deployment_selection",
                    "parameter_key": "independent_candidate_ids", "parameter_value": parameter_value,
                    "source_representation": "compact", "target_representation": "rich",
                    "source_cluster": int(source_cluster), "target_cluster_original": int(target_cluster),
                    "target_cluster_matched": matched, "n_customers": count,
                    "share_of_customers": float(count / len(source)),
                    "migration_flag": bool(int(source_cluster) != matched),
                })
    frame = pd.DataFrame(records, columns=[
        "method", "comparison", "parameter_key", "parameter_value", "source_representation",
        "target_representation", "source_cluster", "target_cluster_original",
        "target_cluster_matched", "n_customers", "share_of_customers", "migration_flag",
    ])
    validate_schema(frame, "cluster_transition_matrix.csv")
    return frame


def cluster_profiles(
    representations: dict[str, RepresentationData], labels: dict[tuple[str, str, str], np.ndarray],
    selected: pd.DataFrame,
) -> pd.DataFrame:
    records = []
    for _, row in selected.iterrows():
        values = labels[(row["representation"], row["method"], row["candidate_id"])]
        sizes = cluster_sizes(values)
        non_noise = int(np.sum(values != -1))
        data = representations[str(row["representation"])]
        for cluster, count in sizes.items():
            member = values == cluster
            for col, feature in enumerate(data.features):
                cluster_values = data.raw[member, col]
                global_values = data.raw[:, col]
                q25, median, q75 = ((float(np.quantile(cluster_values, q)) for q in (.25, .5, .75))
                                    if len(cluster_values) else (None, None, None))
                global_median = float(np.median(global_values))
                global_iqr = float(np.quantile(global_values, .75) - np.quantile(global_values, .25))
                records.append({"representation": row["representation"], "method": row["method"],
                                "selection": row["selection"], "candidate_id": row["candidate_id"],
                                "cluster": int(cluster), "cluster_is_noise": bool(cluster == -1),
                                "feature": feature, "n_customers": int(count),
                                "share_of_all_customers": float(count / len(values)),
                                "share_of_non_noise_customers": float(count / non_noise) if cluster != -1 and non_noise else 0.0,
                                "median": median, "q25": q25, "q75": q75,
                                "global_median": global_median,
                                "iqr_effect": (float((median - global_median) / global_iqr)
                                                if median is not None and global_iqr else None)})
    frame = pd.DataFrame(records)
    validate_schema(frame, "cluster_profiles.csv")
    return frame
