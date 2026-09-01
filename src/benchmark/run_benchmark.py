"""Reproducible nine-dataset benchmark runner and label-free selector."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans

from . import datasets, methods
from .metrics import evaluate

SEEDS = (0, 1, 2, 3, 4)
METRIC_COLS = ("ari", "nmi", "silhouette", "davies_bouldin", "calinski_harabasz",
               "n_clusters_excluding_noise", "n_noise", "runtime_seconds")


def _params(run: methods.Run) -> str:
    return json.dumps(run.params, sort_keys=True, separators=(",", ":"))


def _retime(X: np.ndarray, run: methods.Run, repeats: int) -> tuple[tuple[float, ...], bool | None]:
    """Repeat a fixed candidate and audit label identity as well as timing."""
    if repeats < 1:
        raise ValueError("runtime_repeats must be positive")
    if not run.deterministic:
        return run.runtime_samples_s or (run.runtime_s,), None
    p = run.params
    if run.method == "ward":
        factory = lambda: AgglomerativeClustering(n_clusters=int(p["n_clusters"]), linkage="ward")
    elif run.method == "dbscan":
        factory = lambda: DBSCAN(eps=float(p["eps"]), min_samples=int(p["min_samples"]))
    elif run.method == "classix":
        radius, min_pts, merging = float(p["radius"]), int(p["minPts"]), str(p["group_merging"])
        factory = lambda: _ClassixEstimator(radius, min_pts, merging)
    else:
        raise ValueError(f"unknown deterministic method {run.method}")
    samples = [run.runtime_s]
    repeated_structure_identical = True
    for _ in range(repeats - 1):
        labels, elapsed = methods._timed_fit_predict(factory(), X)
        repeated_structure_identical &= bool(np.array_equal(labels, run.labels))
        samples.append(elapsed)
    return tuple(samples), repeated_structure_identical


class _ClassixEstimator:
    """Small adapter exposing fit_predict for the optional CLASSIX runner."""
    def __init__(self, radius: float, min_pts: int, merging: str):
        self.radius, self.min_pts, self.merging = radius, min_pts, merging

    def fit_predict(self, X: np.ndarray) -> np.ndarray:
        labels, _ = methods._classix_fit(X, self.radius, self.min_pts, self.merging)
        return labels


def _row(ds: datasets.Dataset, run: methods.Run, seed: int | None,
         X: np.ndarray, runtime_samples: tuple[float, ...],
         repeated_structure_identical: bool | None = None) -> dict[str, object]:
    scored = evaluate(X, ds.y, run.labels)
    mean_runtime = float(np.mean(runtime_samples))
    return {
        "dataset": ds.name, "dataset_kind": ds.kind,
        "n_samples": ds.n_samples, "n_features": ds.n_features,
        "method": run.method, "params": _params(run),
        "seed": seed,
        "deterministic_structure": bool(run.deterministic and repeated_structure_identical),
        "structural_repeats_identical": repeated_structure_identical,
        "structural_repeat_count": len(runtime_samples) if run.deterministic else 1,
        "runtime_samples_s": json.dumps([float(x) for x in runtime_samples]),
        "runtime_repeats": len(runtime_samples),
        "runtime_seconds": mean_runtime,
        "runtime_std_seconds": float(np.std(runtime_samples, ddof=0)),
        **scored,
    }


def run_all(seeds: tuple[int, ...] = SEEDS, dataset_names: tuple[str, ...] | None = None,
            runtime_repeats: int = methods.RUNTIME_REPEATS) -> pd.DataFrame:
    """Run all candidates and audit repeated labels for single-row methods."""
    if not seeds:
        raise ValueError("at least one seed is required")
    wanted = set(dataset_names) if dataset_names is not None else set(datasets.REGISTRY)
    unknown = wanted.difference(datasets.REGISTRY)
    if unknown:
        raise KeyError(f"unknown datasets: {sorted(unknown)}")
    rows: list[dict[str, object]] = []
    for ds in datasets.load_all():
        if ds.name not in wanted:
            continue
        X = datasets.standardize(ds)
        deterministic: list[methods.Run] = []
        deterministic.extend(methods.run_ward(X))
        deterministic.extend(methods.run_dbscan(X))
        deterministic.extend(methods.run_classix(X))
        for run in deterministic:
            runtime_samples, identical = _retime(X, run, runtime_repeats)
            rows.append(_row(ds, run, None, X, runtime_samples, identical))
        for seed in seeds:
            for run in methods.run_kmeans(X, seed=seed):
                rows.append(_row(ds, run, seed, X, (run.runtime_s,), None))
    return pd.DataFrame(rows)


def aggregate(raw: pd.DataFrame) -> pd.DataFrame:
    """Aggregate stochastic rows while retaining timing distributions."""
    required = {"dataset", "method", "params"}
    missing = required.difference(raw.columns)
    if missing:
        raise ValueError(f"raw benchmark missing columns: {sorted(missing)}")
    records = []
    for (dataset, method, params), sub in raw.groupby(["dataset", "method", "params"], dropna=False):
        record: dict[str, object] = {
            "dataset": dataset,
            "dataset_kind": sub["dataset_kind"].iloc[0],
            "n_samples": int(sub["n_samples"].iloc[0]),
            "n_features": int(sub["n_features"].iloc[0]),
            "method": method,
            "params": params,
            "n_structure_rows": len(sub),
            "deterministic_structure": bool(sub["deterministic_structure"].iloc[0]),
            "structural_repeats_identical": (
                bool(sub["structural_repeats_identical"].dropna().all())
                if "structural_repeats_identical" in sub and sub["structural_repeats_identical"].notna().any()
                else None
            ),
        }
        for col in METRIC_COLS:
            if col not in sub:
                continue
            values = pd.to_numeric(sub[col], errors="coerce")
            record[f"{col}_mean"] = values.mean(skipna=True)
            record[f"{col}_std"] = values.std(ddof=0, skipna=True)
        runtime_stds = pd.to_numeric(sub["runtime_std_seconds"], errors="coerce")
        record["runtime_repeat_std_mean"] = runtime_stds.mean()
        record["runtime_repeat_count"] = int(sub["runtime_repeats"].sum())
        records.append(record)
    return pd.DataFrame(records)


def select_label_free(raw: pd.DataFrame) -> pd.DataFrame:
    """Pick one parameter candidate per dataset/method using mean silhouette.

    The noise and cluster-count guards are deployment constraints, not label
    information.  Stochastic seeds are repetitions, not tunable candidates,
    so selection is performed on parameter-level aggregates.  ARI/NMI remain
    outcomes and never enter the selector.
    """
    aggregated = aggregate(raw)
    selected: list[dict[str, object]] = []
    for (dataset, method), sub in aggregated.groupby(["dataset", "method"], sort=True):
        eligible = sub.copy()
        for column in (
            "n_clusters_excluding_noise_mean",
            "n_noise_mean",
            "n_samples",
            "silhouette_mean",
            "davies_bouldin_mean",
            "calinski_harabasz_mean",
        ):
            eligible[column] = pd.to_numeric(eligible[column], errors="coerce")
        eligible = eligible[eligible["silhouette_mean"].notna()]
        eligible = eligible[eligible["n_clusters_excluding_noise_mean"].between(2, 12)]
        eligible = eligible[eligible["n_noise_mean"] <= 0.2 * eligible["n_samples"]]
        # A collapsed method has no valid internal score; retaining its first
        # candidate makes the failure visible without consulting reference labels.
        choice = (eligible.sort_values(
            ["silhouette_mean", "davies_bouldin_mean", "calinski_harabasz_mean", "params"],
            ascending=[False, True, False, True],
            na_position="last",
        ).iloc[0]
                  if not eligible.empty else sub.sort_values("params").iloc[0])
        rec = choice.to_dict()
        rec["selection"] = "max_silhouette_with_constraints" if not eligible.empty else "no_valid_internal_score"
        selected.append(rec)
    return pd.DataFrame(selected)


def oracle_by_ari(raw: pd.DataFrame) -> pd.DataFrame:
    """Supplementary parameter-level oracle; never used by the main selector."""
    aggregated = aggregate(raw)
    records = []
    for (dataset, method), sub in aggregated.groupby(["dataset", "method"], sort=True):
        choice = sub.loc[pd.to_numeric(sub["ari_mean"], errors="coerce").idxmax()].copy()
        choice["selection"] = "oracle_max_ari_supplementary"
        records.append(choice)
    return pd.DataFrame(records)


def write_outputs(raw: pd.DataFrame, output_dir: Path, started_at: str, elapsed: float,
                  runtime_repeats: int | None = None) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    agg = aggregate(raw)
    selected = select_label_free(raw)
    raw.to_csv(output_dir / "metrics_raw.csv", index=False)
    agg.to_csv(output_dir / "metrics_agg.csv", index=False)
    selected.to_csv(output_dir / "selected_label_free.csv", index=False)
    oracle_by_ari(raw).to_csv(output_dir / "selected_oracle_supplementary.csv", index=False)
    metadata = {
        "protocol": "frozen benchmark protocol v1",
        "started_at_utc": started_at, "elapsed_seconds": elapsed,
        "source_manifest": {"path": "data/raw/benchmarks/manifest.json",
                             "source_repository": datasets.MANIFEST["source_repository"],
                             "source_revision": datasets.MANIFEST["source_revision"],
                             "license": datasets.MANIFEST["source_license"]},
        "datasets": datasets.frozen_inventory(), "seeds": list(SEEDS),
        "runtime_repeats": runtime_repeats if runtime_repeats is not None else (
            int(raw["runtime_repeats"].max()) if not raw.empty else 0),
        "parameter_budget": {"k": list(methods.K_GRID),
          "dbscan_eps": list(methods.DBSCAN_EPS_GRID),
          "dbscan_min_samples": list(methods.DBSCAN_MIN_SAMPLES_GRID),
          "classix_radius": list(methods.CLASSIX_RADIUS_GRID),
          "classix_minPts": list(methods.CLASSIX_MIN_PTS_GRID),
          "classix_group_merging": list(methods.CLASSIX_MERGING_GRID)},
        "classix_engine": "classix" if methods.classix_available() else "density_connected_fallback",
        "python": sys.version, "platform": platform.platform(),
    }
    (output_dir / "run_meta.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", default="results/benchmark")
    parser.add_argument("--datasets", nargs="*", choices=sorted(datasets.REGISTRY))
    parser.add_argument("--runtime-repeats", type=int, default=methods.RUNTIME_REPEATS)
    args = parser.parse_args()
    started = datetime.now(timezone.utc).isoformat()
    begin = time.perf_counter()
    raw = run_all(dataset_names=tuple(args.datasets) if args.datasets else None,
                  runtime_repeats=args.runtime_repeats)
    write_outputs(raw, Path(args.output_dir), started, time.perf_counter() - begin,
                  runtime_repeats=args.runtime_repeats)
    print(f"wrote {len(raw)} structure rows to {args.output_dir}")


if __name__ == "__main__":
    main()
