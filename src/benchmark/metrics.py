"""External and internal clustering metrics with explicit noise handling."""

from __future__ import annotations

import numpy as np
from sklearn.metrics import (adjusted_rand_score, calinski_harabasz_score,
                             davies_bouldin_score, normalized_mutual_info_score,
                             silhouette_score)


def count_clusters(labels: np.ndarray) -> int:
    values = np.asarray(labels)
    return int(np.unique(values[values != -1]).size)


def noise_count(labels: np.ndarray) -> int:
    return int(np.sum(np.asarray(labels) == -1))


def _non_noise(X: np.ndarray, labels: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    labels = np.asarray(labels)
    keep = labels != -1
    return np.asarray(X)[keep], labels[keep]


def _internal_metrics_valid(labels: np.ndarray) -> bool:
    labels = np.asarray(labels)
    non_noise = labels[labels != -1]
    return 1 < np.unique(non_noise).size < len(non_noise)


def evaluate(X: np.ndarray, y_true: np.ndarray | None, labels: np.ndarray) -> dict[str, float | int | None]:
    """Return the metric bundle; noise is excluded from internal indices.

    ``y_true`` is optional to make it possible to run the label-free selection
    path without even carrying reference labels into the selector.
    """
    labels = np.asarray(labels, dtype=int)
    if labels.ndim != 1 or len(labels) != len(X):
        raise ValueError("labels must be a one-dimensional vector matching X")
    out: dict[str, float | int | None] = {
        "n_clusters": count_clusters(labels),
        "n_clusters_excluding_noise": count_clusters(labels),
        "n_noise": noise_count(labels),
        "ari": None if y_true is None else float(adjusted_rand_score(y_true, labels)),
        "nmi": None if y_true is None else float(normalized_mutual_info_score(y_true, labels)),
        "silhouette": None,
        "davies_bouldin": None,
        "calinski_harabasz": None,
    }
    if _internal_metrics_valid(labels):
        X_valid, y_valid = _non_noise(X, labels)
        out["silhouette"] = float(silhouette_score(X_valid, y_valid))
        out["davies_bouldin"] = float(davies_bouldin_score(X_valid, y_valid))
        out["calinski_harabasz"] = float(calinski_harabasz_score(X_valid, y_valid))
    return out


def selection_score(metrics: dict[str, float | int | None]) -> float | None:
    """Label-free score used by the main track (higher silhouette is better)."""
    value = metrics.get("silhouette")
    clusters = int(metrics.get("n_clusters_excluding_noise", 0) or 0)
    return float(value) if value is not None and clusters >= 2 else None

