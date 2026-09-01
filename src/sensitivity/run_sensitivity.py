"""Run the frozen RetailRocket sensitivity and negative-control analyses."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import adjusted_rand_score
from sklearn.preprocessing import StandardScaler

from src.clustering.engine import _classix_fit, load_representations
from src.protocol import load_protocol
from src.representation.features import RICH_FEATURES

from .core import (
    evaluate_labels,
    feature_ablation,
    permutation_dimension_control,
    perturbation_stability,
)
from .schema import SCHEMAS, write_schemas
from .sessions import reconstruct_session_counts, replace_session_feature


def _truthy(value: Any) -> bool:
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return bool(value)


def _selected(path: Path) -> dict[tuple[str, str], pd.Series]:
    frame = pd.read_csv(path)
    frame = frame[frame["selection"].eq("deployment_acceptable")].copy()
    frame = frame[frame["deployment_acceptable"].map(_truthy)]
    out: dict[tuple[str, str], pd.Series] = {}
    for _, row in frame.iterrows():
        key = (str(row["representation"]), str(row["method"]))
        if key in out:
            raise ValueError(f"duplicate deployment configuration {key}")
        out[key] = row
    expected = {(rep, method) for rep in ("compact", "rich") for method in ("kmeans", "classix")}
    if set(out) != expected:
        raise ValueError(f"missing deployment configurations {sorted(expected - set(out))}")
    return out


def _selected_labels(path: Path, visitorids: dict[str, np.ndarray]) -> dict[tuple[str, str], np.ndarray]:
    frame = pd.read_csv(path)
    frame = frame[frame["selection"].eq("deployment_acceptable")]
    out: dict[tuple[str, str], np.ndarray] = {}
    for (rep, method), sub in frame.groupby(["representation", "method"], sort=True):
        ordered = sub.set_index("visitorid").reindex(visitorids[str(rep)])
        if ordered["label"].isna().any():
            raise ValueError(f"selected labels do not cover {rep} {method}")
        out[(str(rep), str(method))] = ordered["label"].to_numpy(dtype=int)
    return out


def _fit_function(method: str, parameters: str, primary_seed: int) -> Callable[..., np.ndarray]:
    params = json.loads(str(parameters))

    def fit(X: np.ndarray, seed: int | None = None) -> np.ndarray:
        if method == "kmeans":
            return KMeans(
                n_clusters=int(params["n_clusters"]), init="k-means++", n_init=20,
                random_state=primary_seed if seed is None else int(seed),
            ).fit_predict(X).astype(int)
        return _classix_fit(np.asarray(X, dtype=float), params)[0]

    return fit


def _transform_raw(frame: pd.DataFrame, features: list[str], schema: pd.DataFrame) -> np.ndarray:
    values = frame[features].to_numpy(dtype=float, copy=True)
    transforms = schema.set_index("feature")["transform"].astype(str)
    for index, feature in enumerate(features):
        if transforms[feature].strip().lower() == "log1p":
            if np.any(values[:, index] < 0):
                raise ValueError(f"negative log1p input {feature}")
            values[:, index] = np.log1p(values[:, index])
    return StandardScaler().fit_transform(values)


def _pca_resampling(
    transformed: np.ndarray,
    visitorids: np.ndarray,
    fit: Callable[..., np.ndarray],
    protocol: dict[str, Any],
) -> tuple[float, float, int]:
    scores: list[float] = []
    fraction = float(protocol["resampling_fraction"])
    n_draw = int(np.floor(fraction * len(visitorids)))
    primary = int(protocol["primary_seed"])
    for pair in range(int(protocol["resampling_pairs"])):
        left_seed, right_seed = primary + 2 * pair, primary + 2 * pair + 1
        left = np.random.default_rng(left_seed).choice(len(visitorids), n_draw, replace=False)
        right = np.random.default_rng(right_seed).choice(len(visitorids), n_draw, replace=False)
        fitted: list[tuple[np.ndarray, np.ndarray]] = []
        for indices, seed in ((left, left_seed), (right, right_seed)):
            scaled = StandardScaler().fit_transform(transformed[indices])
            projected = PCA(n_components=0.90, svd_solver="full").fit_transform(scaled)
            fitted.append((visitorids[indices], fit(projected, seed=seed)))
        left_pos = {int(v): i for i, v in enumerate(fitted[0][0])}
        right_pos = {int(v): i for i, v in enumerate(fitted[1][0])}
        common = sorted(set(left_pos).intersection(right_pos))
        scores.append(float(adjusted_rand_score(
            [fitted[0][1][left_pos[v]] for v in common],
            [fitted[1][1][right_pos[v]] for v in common],
        )))
    return float(np.mean(scores)), float(np.std(scores, ddof=0)), len(scores)


def run(project_root: Path, output_dir: Path) -> dict[str, Any]:
    protocol = load_protocol(project_root / "protocol" / "analysis_protocol.json")
    representations = load_representations(
        project_root / "data" / "derived",
        project_root / "protocol" / "analysis_protocol.json",
    )
    selected = _selected(project_root / "results" / "retailrocket" / "selected_configurations.csv")
    labels = _selected_labels(
        project_root / "results" / "retailrocket" / "selected_labels.csv",
        {name: data.visitorid for name, data in representations.items()},
    )
    primary = int(protocol["primary_seed"])

    ablation_frames: list[pd.DataFrame] = []
    rich = representations["rich"]
    for method in ("kmeans", "classix"):
        config = selected[("rich", method)]
        fit = _fit_function(method, config["parameters"], primary)
        result = feature_ablation(
            rich.scaled, rich.features, fit,
            reference_labels=labels[("rich", method)],
            algorithm=method, representation="rich", standardize=False,
        )
        result["selection"] = "deployment_acceptable"
        result["candidate_id"] = config["candidate_id"]
        result["parameters"] = config["parameters"]
        ablation_frames.append(result)
    ablation = pd.concat(ablation_frames, ignore_index=True)

    pca = PCA(n_components=0.90, svd_solver="full").fit(rich.scaled)
    projected = pca.transform(rich.scaled)
    cumulative = float(np.sum(pca.explained_variance_ratio_))
    main_stability = pd.read_csv(project_root / "results" / "retailrocket" / "resampling_stability.csv")
    pca_rows: list[dict[str, Any]] = []
    for method in ("kmeans", "classix"):
        config = selected[("rich", method)]
        fit = _fit_function(method, config["parameters"], primary)
        baseline = labels[("rich", method)]
        named_metrics = evaluate_labels(rich.scaled, baseline, baseline)
        named_scores = main_stability[
            main_stability["representation"].eq("rich")
            & main_stability["method"].eq(method)
            & main_stability["selection"].eq("deployment_acceptable")
        ]["ari_overlap"].dropna().to_numpy(dtype=float)
        pca_labels = fit(projected, seed=primary)
        pca_metrics = evaluate_labels(projected, pca_labels, baseline)
        pca_mean, pca_std, pca_pairs = _pca_resampling(rich.transformed, rich.visitorid, fit, protocol)
        for space, metrics, n_components, variance, mean, std, pairs in (
            ("rich_named", named_metrics, len(rich.features), 1.0,
             float(named_scores.mean()), float(named_scores.std(ddof=0)), len(named_scores)),
            ("pca_90", pca_metrics, int(pca.n_components_), cumulative,
             pca_mean, pca_std, pca_pairs),
        ):
            pca_rows.append({
                "representation": "rich", "space": space, "algorithm": method,
                "selection": "deployment_acceptable", "candidate_id": config["candidate_id"],
                "parameters": config["parameters"], "variance_threshold": 0.90,
                "n_features": len(rich.features), "n_components": n_components,
                "cumulative_explained_variance": variance, "standardized": True,
                "use_for_rules": False, "n_clusters": metrics["n_clusters"],
                "largest_non_noise_cluster_share": metrics["largest_non_noise_cluster_share"],
                "silhouette": metrics["silhouette"], "davies_bouldin": metrics["davies_bouldin"],
                "calinski_harabasz": metrics["calinski_harabasz"], "n_noise": metrics["n_noise"],
                "noise_fraction": metrics["noise_fraction"], "reference_ari": metrics["ari"],
                "resampling_ari_mean": mean, "resampling_ari_std": std,
                "resampling_pairs": pairs,
            })
    pca_frame = pd.DataFrame(pca_rows)

    perturb_frames: list[pd.DataFrame] = []
    for representation, data in representations.items():
        config = selected[(representation, "classix")]
        result = perturbation_stability(
            data.scaled, _fit_function("classix", config["parameters"], primary),
            sigmas=protocol["perturbation_standard_deviations"],
            seeds=[primary + i for i in range(int(protocol["nonzero_perturbation_repeats"]))],
            baseline_labels=labels[(representation, "classix")],
            algorithm="classix", representation=representation,
        )
        result["selection"] = "deployment_acceptable"
        result["candidate_id"] = config["candidate_id"]
        result["parameters"] = config["parameters"]
        perturb_frames.append(result)
    perturb = pd.concat(perturb_frames, ignore_index=True)

    schema = pd.read_csv(project_root / "data" / "derived" / "feature_schema.csv")
    rich_frame = pd.read_csv(project_root / "data" / "derived" / "rich_features.csv")
    events_path = project_root / "data" / "derived" / "purchaser_event_timestamps.csv"
    events = pd.read_csv(
        events_path,
        usecols=["visitorid", "timestamp"],
        dtype={"visitorid": "int64", "timestamp": "int64"},
    )
    session_counts = reconstruct_session_counts(events, (15, 30, 60))
    session_rows: list[dict[str, Any]] = []
    for window in (15, 30, 60):
        altered, affected = replace_session_feature(rich_frame, session_counts, window)
        matrix = _transform_raw(altered, list(rich.features), schema)
        for method in ("kmeans", "classix"):
            config = selected[("rich", method)]
            current = _fit_function(method, config["parameters"], primary)(matrix, seed=primary)
            metrics = evaluate_labels(matrix, current, labels[("rich", method)])
            session_rows.append({
                "algorithm": method, "representation": "rich", "selection": "deployment_acceptable",
                "candidate_id": config["candidate_id"], "parameters": config["parameters"],
                "window_minutes": window, "affected_dimension": affected,
                "n_features": len(rich.features), **metrics,
            })
    session = pd.DataFrame(session_rows)

    compact = representations["compact"]
    compact_scaled = pd.DataFrame(compact.scaled, columns=compact.features)
    rich_scaled = pd.DataFrame(rich.scaled, columns=rich.features)
    non_shared = [name for name in rich.features if name not in compact.features]
    permutation_frames: list[pd.DataFrame] = []
    for method in ("kmeans", "classix"):
        config = selected[("compact", method)]
        result = permutation_dimension_control(
            compact_scaled, rich_scaled, compact.features, non_shared,
            _fit_function(method, config["parameters"], primary),
            baseline_labels=labels[("compact", method)], seed=primary,
            algorithm=method,
        )
        result["selection"] = "deployment_acceptable"
        result["candidate_id"] = config["candidate_id"]
        result["parameters"] = config["parameters"]
        permutation_frames.append(result)
    permutation = pd.concat(permutation_frames, ignore_index=True)

    frames = {
        "feature_ablation.csv": ablation,
        "pca_sensitivity.csv": pca_frame,
        "classix_perturbation_stability.csv": perturb,
        "session_window_sensitivity.csv": session,
        "permutation_dimension_control.csv": permutation,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, frame in frames.items():
        missing = set(SCHEMAS[filename]) - set(frame.columns)
        if missing:
            raise ValueError(f"{filename} missing columns {sorted(missing)}")
        frame.loc[:, SCHEMAS[filename]].to_csv(output_dir / filename, index=False)
    write_schemas(output_dir)
    metadata = {
        "protocol_version": protocol["protocol_version"], "status": "complete",
        "selected_configuration_source": "results/retailrocket/selected_configurations.csv",
        "pca_use_for_rules": False, "pca_variance_threshold": 0.90,
        "session_windows_minutes": [15, 30, 60],
        "permutation_joint_structure_preserved": False,
        "sigma_zero_required_ari": 1.0,
    }
    (output_dir / "sensitivity_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("results/sensitivity"))
    args = parser.parse_args()
    run(args.project_root.resolve(), args.output_dir)


if __name__ == "__main__":
    main()
