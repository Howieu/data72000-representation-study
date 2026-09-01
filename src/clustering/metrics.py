"""Metrics and partition-alignment helpers for the clustering experiment.

Internal indices intentionally exclude CLASSIX's ``-1`` labels.  Pairwise
partition metrics retain every visitor, including noise, because a noise
assignment is itself part of the deployed partition.
"""

from __future__ import annotations

from collections import Counter
from typing import Iterable

import numpy as np
from scipy.optimize import linear_sum_assignment
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    normalized_mutual_info_score,
    silhouette_score,
    mutual_info_score,
)


def cluster_count(labels: Iterable[int], include_noise: bool = False) -> int:
    values = np.asarray(list(labels) if not isinstance(labels, np.ndarray) else labels)
    unique = np.unique(values)
    if not include_noise:
        unique = unique[unique != -1]
    return int(unique.size)


def cluster_sizes(labels: Iterable[int], include_noise: bool = True) -> dict[int, int]:
    values = np.asarray(list(labels) if not isinstance(labels, np.ndarray) else labels, dtype=int)
    counts = Counter(int(value) for value in values)
    if not include_noise:
        counts.pop(-1, None)
    return dict(sorted(counts.items()))


def _valid_internal(labels: np.ndarray) -> np.ndarray | None:
    labels = np.asarray(labels, dtype=int)
    keep = labels != -1
    non_noise = labels[keep]
    # A singleton-only partition, an empty partition, and a one-cluster
    # partition all make the three indices undefined.
    if non_noise.size < 3 or np.unique(non_noise).size < 2:
        return None
    return keep


def evaluate_partition(X: np.ndarray, labels: np.ndarray) -> dict[str, float | int | bool | None]:
    """Return complete size/noise/internal-index diagnostics for one candidate."""
    values = np.asarray(labels, dtype=int)
    if values.ndim != 1 or len(values) != len(X):
        raise ValueError("labels must be a one-dimensional vector matching X")
    sizes = cluster_sizes(values, include_noise=True)
    non_noise_count = int(np.sum(values != -1))
    noise_count = int(np.sum(values == -1))
    non_noise_sizes = [size for key, size in sizes.items() if key != -1]
    largest_share = (
        float(max(non_noise_sizes) / non_noise_count)
        if non_noise_count else 0.0
    )
    out: dict[str, float | int | bool | None] = {
        "n_samples": int(len(values)),
        "n_clusters": cluster_count(values),
        "n_clusters_including_noise": cluster_count(values, include_noise=True),
        "n_noise": noise_count,
        "noise_fraction": float(noise_count / len(values)) if len(values) else 0.0,
        "largest_non_noise_cluster_share": largest_share,
        "internal_valid": False,
        "silhouette": None,
        "davies_bouldin": None,
        "calinski_harabasz": None,
    }
    keep = _valid_internal(values)
    if keep is not None:
        Xv, yv = np.asarray(X)[keep], values[keep]
        scores = (
            float(silhouette_score(Xv, yv)),
            float(davies_bouldin_score(Xv, yv)),
            float(calinski_harabasz_score(Xv, yv)),
        )
        if np.isfinite(scores).all():
            out["internal_valid"] = True
            out["silhouette"], out["davies_bouldin"], out["calinski_harabasz"] = scores
    return out


def _entropy(labels: np.ndarray) -> float:
    counts = np.asarray(list(Counter(np.asarray(labels, dtype=int)).values()), dtype=float)
    probs = counts / counts.sum()
    return float(-np.sum(probs * np.log(probs)))


def variation_of_information(left: Iterable[int], right: Iterable[int]) -> float:
    """Variation of information in nats, including all labels."""
    a, b = np.asarray(list(left), dtype=int), np.asarray(list(right), dtype=int)
    if a.shape != b.shape:
        raise ValueError("partitions must have equal length")
    return float(_entropy(a) + _entropy(b) - 2.0 * mutual_info_score(a, b))


def adjusted_mutual_information(left: Iterable[int], right: Iterable[int]) -> float:
    """Name-stable wrapper used by result schemas (AMI, not label accuracy)."""
    return float(adjusted_mutual_info_score(np.asarray(left), np.asarray(right)))


def paired_partition_metrics(left: Iterable[int], right: Iterable[int]) -> dict[str, float]:
    """Return ARI, NMI and VI for two complete visitor partitions."""
    a, b = np.asarray(list(left), dtype=int), np.asarray(list(right), dtype=int)
    if a.shape != b.shape:
        raise ValueError("partitions must have equal length")
    return {
        "ari": float(adjusted_rand_score(a, b)),
        "nmi": float(normalized_mutual_info_score(a, b, average_method="arithmetic")),
        "vi": variation_of_information(a, b),
    }


def hungarian_alignment(source: Iterable[int], target: Iterable[int]) -> dict[int, int]:
    """Map target non-noise labels onto source labels by maximum overlap.

    Noise is kept as ``-1``.  Any unmatched target cluster receives a fresh
    negative ID, so the mapping remains injective and never collides with a
    real source cluster.  The pinned SciPy solver is repeatable for a fixed
    table, but no portable secondary objective is claimed for tied optima.
    """
    a, b = np.asarray(list(source), dtype=int), np.asarray(list(target), dtype=int)
    if a.shape != b.shape:
        raise ValueError("partitions must have equal length")
    source_ids = sorted(int(x) for x in np.unique(a) if x != -1)
    target_ids = sorted(int(x) for x in np.unique(b) if x != -1)
    mapping: dict[int, int] = {-1: -1}
    if source_ids and target_ids:
        table = np.zeros((len(source_ids), len(target_ids)), dtype=np.int64)
        source_pos = {value: i for i, value in enumerate(source_ids)}
        target_pos = {value: j for j, value in enumerate(target_ids)}
        for x, y in zip(a, b):
            if x != -1 and y != -1:
                table[source_pos[int(x)], target_pos[int(y)]] += 1
        # linear_sum_assignment minimizes, therefore negate overlap.  Tied
        # optima inherit the pinned solver's ordering and have equal total
        # matched counts, so the aggregate migration share is unchanged.
        row_ind, col_ind = linear_sum_assignment(-table)
        for i, j in zip(row_ind, col_ind):
            mapping[target_ids[int(j)]] = source_ids[int(i)]
    used = set(mapping.values()) | set(source_ids)
    next_id = -2
    for target_id in target_ids:
        if target_id not in mapping:
            while next_id in used:
                next_id -= 1
            mapping[target_id] = next_id
            used.add(next_id)
            next_id -= 1
    return mapping


# Kept local to avoid depending on a version-specific sklearn import layout.
def adjusted_mutual_info_score(left: np.ndarray, right: np.ndarray) -> float:
    from sklearn.metrics import adjusted_mutual_info_score as _ami

    return float(_ami(left, right))
