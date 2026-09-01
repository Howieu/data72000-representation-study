"""Re-run the CLASSIX distance-count experiment in the pinned environment.

Usage: ``conda run -n exkmc python -m src.mathematics.complexity_run``.
The generated table intentionally reports counts and bounds; elapsed time is
descriptive and must not be read as a speed claim.
"""

from __future__ import annotations

import csv
import time
from pathlib import Path

import numpy as np

from .classix_math import complexity_summary


def run(output: str | Path | None = None) -> Path:
    import classix

    target = Path(output) if output is not None else Path(__file__).parents[2] / "results/sensitivity/distance_complexity_classix.csv"
    target.parent.mkdir(parents=True, exist_ok=True)
    rows: list[dict[str, object]] = []
    rng = np.random.default_rng(20260828)
    for n, d in ((64, 2), (128, 2), (256, 2), (64, 8), (128, 8), (256, 8)):
        values = rng.normal(size=(n, d))
        started = time.perf_counter()
        model = classix.CLASSIX(
            sorting="pca", metric="euclidean", radius=0.45, minPts=1,
            group_merging="distance", mergeScale=1.5, verbose=0,
        ).fit(values)
        elapsed_ms = (time.perf_counter() - started) * 1000.0
        q = len(np.unique(model.groups_))
        summary = complexity_summary(n, d, q, int(model.nrDistComp_), sorting="pca")
        rows.append({
            "runtime": "exkmc",
            "package_version": "1.5.1",
            "metric": "euclidean",
            "sorting": "pca",
            "group_merging": "distance",
            "radius": 0.45,
            "mergeScale": 1.5,
            "n_samples": n,
            "n_features": d,
            "groups": q,
            "aggregation_distance_count": int(model.nrDistComp_),
            "aggregation_pair_bound": summary["aggregation_pair_bound"],
            "merge_pair_bound": summary["merge_pair_bound"],
            "worst_case_distance_arithmetic_units": summary["worst_case_distance_arithmetic_units"],
            "elapsed_ms": round(elapsed_ms, 6),
        })
    with target.open("w", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    return target


if __name__ == "__main__":
    print(run())

