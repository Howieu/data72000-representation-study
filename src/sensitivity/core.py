"""Pure, configuration-independent sensitivity calculations.

All functions operate on numeric matrices and a caller-supplied clustering
function.  They do not tune, select, or replace a clustering configuration.
The caller owns preprocessing and must pass the same preprocessing used by
the selected main run (``standardize=True`` is only a convenience for the
standalone diagnostics and is explicit in the output metadata).
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd
from sklearn.decomposition import PCA
from sklearn.metrics import (
    adjusted_rand_score,
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import StandardScaler


FitPredict = Callable[..., Iterable[int]]
METRIC_COLUMNS = (
    "n_clusters",
    "largest_non_noise_cluster_share",
    "silhouette",
    "davies_bouldin",
    "calinski_harabasz",
    "ari",
    "stability_ari",
    "n_noise",
    "noise_fraction",
)


def _numeric_matrix(values: Any) -> np.ndarray:
    """Convert a matrix/data frame to a finite two-dimensional float array."""
    matrix = values.to_numpy(dtype=float, copy=True) if isinstance(values, pd.DataFrame) else np.asarray(values, dtype=float)
    if matrix.ndim != 2 or matrix.shape[0] == 0 or matrix.shape[1] == 0:
        raise ValueError("X must be a non-empty two-dimensional matrix")
    if not np.isfinite(matrix).all():
        raise ValueError("X must contain only finite values")
    return matrix


def _fit_predict(fit_predict: FitPredict, X: np.ndarray, seed: int | None = None) -> np.ndarray:
    """Call a fit function while tolerating functions without a seed keyword."""
    try:
        labels = fit_predict(X, seed=seed)
    except TypeError as error:
        if "seed" not in str(error):
            raise
        labels = fit_predict(X)
    values = np.asarray(labels, dtype=int)
    if values.ndim != 1 or len(values) != len(X):
        raise ValueError("fit_predict must return one label per row")
    return values


def _internal_scores(X: np.ndarray, labels: np.ndarray) -> tuple[float | None, float | None, float | None]:
    keep = labels != -1
    Xv, yv = X[keep], labels[keep]
    if len(Xv) < 3 or np.unique(yv).size < 2:
        return None, None, None
    return (
        float(silhouette_score(Xv, yv)),
        float(davies_bouldin_score(Xv, yv)),
        float(calinski_harabasz_score(Xv, yv)),
    )


def evaluate_labels(
    X: Any,
    labels: Iterable[int],
    reference_labels: Iterable[int] | None = None,
) -> dict[str, float | int | None]:
    """Compute the frozen structural and internal metrics for one partition.

    Internal scores exclude ``-1`` noise.  ARI is against ``reference_labels``
    when supplied, while ``stability_ari`` is an explicit alias for the same
    comparison in sensitivity output.  No label renaming is needed for ARI.
    """
    matrix = _numeric_matrix(X)
    values = np.asarray(list(labels), dtype=int)
    if values.ndim != 1 or len(values) != len(matrix):
        raise ValueError("labels must be a one-dimensional vector matching X")
    non_noise = values[values != -1]
    counts = pd.Series(non_noise).value_counts().to_numpy(dtype=float) if len(non_noise) else np.array([], dtype=float)
    n_clusters = int(np.unique(non_noise).size)
    n_noise = int(np.sum(values == -1))
    largest = float(counts.max() / len(non_noise)) if len(non_noise) else 0.0
    silhouette, dbi, ch = _internal_scores(matrix, values)
    ari = None
    if reference_labels is not None:
        reference = np.asarray(list(reference_labels), dtype=int)
        if reference.shape != values.shape:
            raise ValueError("reference_labels must match labels")
        ari = float(adjusted_rand_score(reference, values))
    return {
        "n_clusters": n_clusters,
        "largest_non_noise_cluster_share": largest,
        "silhouette": silhouette,
        "davies_bouldin": dbi,
        "calinski_harabasz": ch,
        "ari": ari,
        "stability_ari": ari,
        "n_noise": n_noise,
        "noise_fraction": float(n_noise / len(values)),
    }


def _with_context(row: dict[str, Any], algorithm: str | None, representation: str | None) -> dict[str, Any]:
    if algorithm is not None:
        row["algorithm"] = algorithm
    if representation is not None:
        row["representation"] = representation
    return row


def feature_ablation(
    X: Any,
    feature_names: Sequence[str],
    fit_predict: FitPredict,
    *,
    reference_labels: Iterable[int] | None = None,
    algorithm: str | None = None,
    representation: str = "rich",
    standardize: bool = False,
) -> pd.DataFrame:
    """Run leave-one-feature-out ablation without changing model selection."""
    matrix = _numeric_matrix(X)
    names = list(feature_names)
    if len(names) != matrix.shape[1] or len(set(names)) != len(names):
        raise ValueError("feature_names must uniquely name every column")
    source = StandardScaler().fit_transform(matrix) if standardize else matrix
    reference = None if reference_labels is None else np.asarray(list(reference_labels), dtype=int)
    rows: list[dict[str, Any]] = []
    for index, name in enumerate(names):
        reduced = np.delete(source, index, axis=1)
        labels = _fit_predict(fit_predict, reduced)
        row: dict[str, Any] = {
            "dropped_feature": name,
            "n_features": int(reduced.shape[1]),
            **evaluate_labels(reduced, labels, reference),
        }
        rows.append(_with_context(row, algorithm, representation))
    return pd.DataFrame(rows)


def pca_variance_diagnostic(
    X: Any,
    *,
    feature_names: Sequence[str] | None = None,
    variance_threshold: float = 0.90,
    standardize: bool = True,
) -> dict[str, Any]:
    """Return the minimum PCA dimension reaching a variance threshold.

    This is a diagnostic only; it never supplies PCA features to a rule or
    clustering selection path.
    """
    if not 0 < variance_threshold <= 1:
        raise ValueError("variance_threshold must be in (0, 1]")
    matrix = _numeric_matrix(X)
    transformed = StandardScaler().fit_transform(matrix) if standardize else matrix
    model = PCA().fit(transformed)
    ratios = np.asarray(model.explained_variance_ratio_, dtype=float)
    cumulative = np.cumsum(ratios)
    n_components = int(np.searchsorted(cumulative, variance_threshold, side="left") + 1)
    names = None if feature_names is None else list(feature_names)
    if names is not None and len(names) != matrix.shape[1]:
        raise ValueError("feature_names must match X columns")
    return {
        "variance_threshold": float(variance_threshold),
        "n_features": int(matrix.shape[1]),
        "n_components": n_components,
        "explained_variance_ratio": ratios.tolist(),
        "cumulative_explained_variance": cumulative.tolist(),
        "threshold_reached": bool(cumulative[n_components - 1] >= variance_threshold),
        "standardized": bool(standardize),
        "feature_names": names,
        "use_for_rules": False,
    }


def perturbation_stability(
    X: Any,
    fit_predict: FitPredict,
    *,
    sigmas: Sequence[float] = (0.0, 1e-6, 1e-4, 1e-3, 1e-2),
    seeds: Sequence[int] = tuple(range(10)),
    baseline_labels: Iterable[int] | None = None,
    algorithm: str = "CLASSIX",
    representation: str = "rich",
) -> pd.DataFrame:
    """Measure label ARI after Gaussian feature perturbations.

    Sigma zero is handled as an exact deterministic rerun against the supplied
    baseline labels.  It must reproduce ARI=1 rather than receiving that value
    by construction.
    Non-zero levels use exactly one independent Gaussian draw per seed.
    """
    matrix = _numeric_matrix(X)
    sigma_values = [float(sigma) for sigma in sigmas]
    if any(sigma < 0 for sigma in sigma_values):
        raise ValueError("sigmas must be non-negative")
    seed_values = [int(seed) for seed in seeds]
    baseline = _fit_predict(fit_predict, matrix, seed=seed_values[0] if seed_values else None) if baseline_labels is None else np.asarray(list(baseline_labels), dtype=int)
    if baseline.shape != (len(matrix),):
        raise ValueError("baseline_labels must match X")
    rows: list[dict[str, Any]] = []
    for sigma in sigma_values:
        use_seeds = [seed_values[0]] if sigma == 0 and seed_values else seed_values
        for seed in use_seeds:
            if sigma == 0:
                evaluated = matrix
            else:
                rng = np.random.default_rng(seed)
                evaluated = matrix + rng.normal(0.0, sigma, size=matrix.shape)
            labels = _fit_predict(fit_predict, evaluated, seed=seed)
            row = {
                "sigma": sigma,
                "seed": seed,
                **evaluate_labels(evaluated, labels, baseline),
            }
            rows.append(_with_context(row, algorithm, representation))
    return pd.DataFrame(rows)


def permutation_dimension_control(
    compact: Any,
    rich: Any,
    compact_features: Sequence[str],
    non_shared_features: Sequence[str],
    fit_predict: FitPredict,
    *,
    baseline_labels: Iterable[int] | None = None,
    seed: int = 20260801,
    algorithm: str | None = None,
    representation: str = "compact_plus_permuted_non_shared",
) -> pd.DataFrame:
    """Add independently permuted rich-only columns to an unchanged compact X.

    Each non-shared column is permuted independently across visitors.  Thus
    the control retains the compact marginal columns but removes the rich
    cross-feature and row-level joint structure.  The function records a
    compact hash-like equality audit in the returned rows via
    ``compact_columns_unchanged``.
    """
    compact_frame = compact.copy() if isinstance(compact, pd.DataFrame) else pd.DataFrame(_numeric_matrix(compact), columns=list(compact_features))
    rich_frame = rich.copy() if isinstance(rich, pd.DataFrame) else pd.DataFrame(_numeric_matrix(rich), columns=[*compact_features, *non_shared_features])
    missing = [name for name in [*compact_features, *non_shared_features] if name not in rich_frame.columns]
    if missing or any(name not in compact_frame.columns for name in compact_features):
        raise ValueError(f"missing control feature columns: {missing}")
    if len(compact_frame) != len(rich_frame):
        raise ValueError("compact and rich tables must have equal row counts")
    compact_values = compact_frame[list(compact_features)].to_numpy(dtype=float, copy=True)
    rich_shared = rich_frame[list(compact_features)].to_numpy(dtype=float, copy=True)
    if not np.array_equal(compact_values, rich_shared, equal_nan=True):
        raise ValueError("compact columns must equal the rich shared columns")
    baseline = None if baseline_labels is None else np.asarray(list(baseline_labels), dtype=int)
    if baseline is not None and baseline.shape != (len(compact_frame),):
        raise ValueError("baseline_labels must match compact rows")
    rows: list[dict[str, Any]] = []
    permuted: dict[str, np.ndarray] = {}
    for added in range(len(non_shared_features) + 1):
        columns = list(compact_features)
        for index, feature in enumerate(non_shared_features[:added]):
            if feature not in permuted:
                rng = np.random.default_rng(seed + index)
                permuted[feature] = rng.permutation(rich_frame[feature].to_numpy(dtype=float))
            columns.append(feature)
        matrix = np.column_stack([compact_values, *[permuted[f] for f in non_shared_features[:added]]])
        labels = _fit_predict(fit_predict, matrix, seed=seed)
        row: dict[str, Any] = {
            "n_features": int(matrix.shape[1]),
            "added_permuted_features": int(added),
            "permuted_feature_names": "|".join(non_shared_features[:added]),
            "compact_columns_unchanged": bool(np.array_equal(compact_values, compact_frame[list(compact_features)].to_numpy(dtype=float), equal_nan=True)),
            "rich_joint_structure_preserved": False,
            **evaluate_labels(matrix, labels, baseline),
        }
        rows.append(_with_context(row, algorithm, representation))
    return pd.DataFrame(rows)
