"""Clustering candidates and frozen parameter budgets.

Every function here returns candidates only.  Selection belongs to the
label-free selector in :mod:`run_benchmark`; reference labels never enter a
constructor or a parameter grid.
"""

from __future__ import annotations

import contextlib
import io
import time
from dataclasses import dataclass

import numpy as np
from sklearn.cluster import AgglomerativeClustering, DBSCAN, KMeans

try:  # CLASSIX remains optional for the benchmark interface.
    from classix import CLASSIX as _CLASSIX
except ImportError:  # pragma: no cover - exercised on minimal environments
    _CLASSIX = None


K_GRID = tuple(range(2, 13))
DBSCAN_EPS_GRID = tuple(round(0.10 + 0.10 * i, 2) for i in range(12))
DBSCAN_MIN_SAMPLES_GRID = (3, 5, 10)
CLASSIX_RADIUS_GRID = tuple(round(0.10 + 0.10 * i, 2) for i in range(15))
CLASSIX_MIN_PTS_GRID = (1, 5, 10)
CLASSIX_MERGING_GRID = ("distance", "density")
RUNTIME_REPEATS = 2


@dataclass(frozen=True)
class Run:
    method: str
    params: dict[str, object]
    labels: np.ndarray
    runtime_s: float
    deterministic: bool = False
    runtime_samples_s: tuple[float, ...] = ()


def classix_available() -> bool:
    return _CLASSIX is not None


def _timed_fit_predict(estimator, X: np.ndarray) -> tuple[np.ndarray, float]:
    started = time.perf_counter()
    labels = estimator.fit_predict(X) if hasattr(estimator, "fit_predict") else estimator.fit(X).labels_
    return np.asarray(labels, dtype=int), time.perf_counter() - started


def _classix_fit(X: np.ndarray, radius: float, min_pts: int, merging: str) -> tuple[np.ndarray, float]:
    if _CLASSIX is None:
        # A deterministic density-connected fallback preserves the method's
        # no-k contract when the optional implementation is unavailable.
        return _timed_fit_predict(DBSCAN(eps=radius, min_samples=max(1, min_pts)), X)
    with contextlib.redirect_stdout(io.StringIO()):
        estimator = _CLASSIX(radius=radius, minPts=min_pts,
                              group_merging=merging, verbose=0)
        return _timed_fit_predict(estimator, X)


def run_kmeans(X: np.ndarray, seed: int = 0,
               k_values: tuple[int, ...] | None = None) -> list[Run]:
    """Return a label-free k-grid."""
    ks = k_values or K_GRID
    runs = []
    for k in ks:
        if not 2 <= k < len(X):
            continue
        labels, elapsed = _timed_fit_predict(
            KMeans(n_clusters=k, init="k-means++", n_init=20, random_state=seed), X)
        runs.append(Run("kmeans", {"n_clusters": k, "init": "k-means++", "n_init": 20},
                        labels, elapsed, False, (elapsed,)))
    return runs


def run_ward(X: np.ndarray, k_values: tuple[int, ...] | None = None) -> list[Run]:
    """Return deterministic Ward candidates over k, without reference labels."""
    ks = k_values or K_GRID
    runs = []
    for k in ks:
        if not 2 <= k < len(X):
            continue
        labels, elapsed = _timed_fit_predict(AgglomerativeClustering(n_clusters=k, linkage="ward"), X)
        runs.append(Run("ward", {"n_clusters": k, "linkage": "ward"}, labels,
                        elapsed, True, (elapsed,)))
    return runs


def run_hierarchical(X: np.ndarray, k_values: tuple[int, ...] | None = None) -> list[Run]:
    """Compatibility spelling for :func:`run_ward`."""
    return run_ward(X, k_values=k_values)


def run_kmeans_oracle(X: np.ndarray, reference_k: int, seed: int = 0) -> list[Run]:
    """Explicit supplementary track using a supplied reference category count."""
    runs = run_kmeans(X, seed=seed, k_values=(reference_k,))
    return [Run(r.method, {**r.params, "oracle": True}, r.labels, r.runtime_s,
                r.deterministic, r.runtime_samples_s) for r in runs]


def run_ward_oracle(X: np.ndarray, reference_k: int) -> list[Run]:
    """Explicit supplementary Ward track using a supplied reference k."""
    runs = run_ward(X, k_values=(reference_k,))
    return [Run(r.method, {**r.params, "oracle": True}, r.labels, r.runtime_s,
                r.deterministic, r.runtime_samples_s) for r in runs]


def run_dbscan(X: np.ndarray) -> list[Run]:
    runs = []
    for eps in DBSCAN_EPS_GRID:
        for min_samples in DBSCAN_MIN_SAMPLES_GRID:
            labels, elapsed = _timed_fit_predict(DBSCAN(eps=eps, min_samples=min_samples), X)
            runs.append(Run("dbscan", {"eps": eps, "min_samples": min_samples}, labels,
                            elapsed, True, (elapsed,)))
    return runs


def run_classix(X: np.ndarray) -> list[Run]:
    runs = []
    engine = "classix" if classix_available() else "density_connected_fallback"
    for radius in CLASSIX_RADIUS_GRID:
        for min_pts in CLASSIX_MIN_PTS_GRID:
            for merging in CLASSIX_MERGING_GRID:
                labels, elapsed = _classix_fit(X, radius, min_pts, merging)
                runs.append(Run("classix", {"radius": radius, "minPts": min_pts,
                                             "group_merging": merging, "engine": engine},
                                labels, elapsed, True, (elapsed,)))
    return runs


def retime(estimator_factory, X: np.ndarray, repeats: int = RUNTIME_REPEATS) -> tuple[float, ...]:
    """Measure independent fits; never synthesize a timing distribution."""
    if repeats < 1:
        raise ValueError("repeats must be positive")
    samples = []
    for _ in range(repeats):
        _, elapsed = _timed_fit_predict(estimator_factory(), X)
        samples.append(elapsed)
    return tuple(samples)
