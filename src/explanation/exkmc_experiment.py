"""Leakage-controlled ExKMC explanation experiments.

The reference object in this module is always KMeans.  ExKMC (or its clearly
labelled compatibility fallback when the optional package is unavailable) is
fit to the *training* KMeans labels and only predicts the held-out rows.  No
test score is used for selecting k, k-prime, a scaler, or a rule.
"""

from __future__ import annotations

import json
import random
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.metrics import calinski_harabasz_score, davies_bouldin_score, silhouette_score
from sklearn.preprocessing import StandardScaler
from threadpoolctl import threadpool_limits

try:  # ExKMC is available in the pinned Python 3.10 environment.
    from ExKMC.Tree import Tree as _ExKMCTree
except Exception:  # pragma: no cover - exercised on lightweight CI images
    _ExKMCTree = None


EXKMC_SPLIT_SEEDS = (20260801, 20260802, 20260803, 20260804, 20260805)
K_GRID = tuple(range(2, 13))


def _fit_kmeans_deterministic(model: KMeans, values: np.ndarray) -> KMeans:
    """Fit KMeans with a reproducible BLAS reduction order."""

    # KMeans itself also uses matrix reductions.  Limiting only the later
    # ExKMC call would leave the reference centers vulnerable to last-bit
    # changes that can still alter ExKMC's tie-sensitive split choices.
    with threadpool_limits(limits=1, user_api="blas"):
        return model.fit(values)


@dataclass(frozen=True)
class Split:
    """A deterministic row split, represented by original row positions."""

    seed: int
    train_indices: np.ndarray
    test_indices: np.ndarray


@dataclass(frozen=True)
class ExplanationFit:
    """One train/test explanation fit and its leakage audit information."""

    representation: str
    split_seed: int
    k: int
    k_prime: int
    scaler: StandardScaler
    kmeans: KMeans
    tree: Any
    engine: str
    train_indices: np.ndarray
    test_indices: np.ndarray
    X_train_scaled: np.ndarray
    reference_train_labels: np.ndarray
    reference_test_labels: np.ndarray
    train_predictions: np.ndarray
    test_predictions: np.ndarray
    k_selection_scope: str
    k_candidate_count: int
    selected_train_silhouette: float
    selected_train_dbi: float
    selected_train_ch: float
    transformed_columns: tuple[str, ...]
    k_selection_candidates: pd.DataFrame


@dataclass(frozen=True)
class KSelection:
    """The train-only label-free selection result for one split."""

    k: int
    model: KMeans
    candidates: pd.DataFrame


def fit_fixed_k_train_only(
    X_train: np.ndarray,
    *,
    representation: str,
    split_seed: int,
    k: int,
) -> KSelection:
    """Fit a frozen primary k on training rows and record its label-free diagnostics."""

    values = np.asarray(X_train, dtype=float)
    fixed_k = int(k)
    if values.ndim != 2 or values.shape[0] < 3 or not np.isfinite(values).all():
        raise ValueError("X_train must be a finite 2-D matrix with at least three rows")
    if not 2 <= fixed_k <= 12 or fixed_k >= values.shape[0]:
        raise ValueError("fixed k is outside the frozen admissible range")
    model = KMeans(
        n_clusters=fixed_k,
        init="k-means++",
        n_init=20,
        random_state=int(split_seed),
    )
    _fit_kmeans_deterministic(model, values)
    labels = model.labels_
    table = pd.DataFrame([{
        "representation": str(representation),
        "split_seed": int(split_seed),
        "k": fixed_k,
        "train_silhouette": float(silhouette_score(values, labels)),
        "train_dbi": float(davies_bouldin_score(values, labels)),
        "train_ch": float(calinski_harabasz_score(values, labels)),
        "selection_scope": "frozen_primary_k_train_fit",
        "selected": True,
    }])
    return KSelection(fixed_k, model, table)


def deterministic_split(n_rows: int, seed: int, train_fraction: float = 0.8) -> Split:
    """Return a reproducible, disjoint split without looking at feature values."""

    n = int(n_rows)
    if n < 3:
        raise ValueError("at least three rows are required")
    if not 0.0 < float(train_fraction) < 1.0:
        raise ValueError("train_fraction must lie strictly between zero and one")
    n_train = int(round(n * float(train_fraction)))
    n_train = min(max(n_train, 2), n - 1)
    order = np.random.default_rng(int(seed)).permutation(n)
    train = np.sort(order[:n_train]).astype(int)
    test = np.sort(order[n_train:]).astype(int)
    return Split(int(seed), train, test)


def fidelity(reference: Iterable[int], predicted: Iterable[int]) -> float:
    """Exact agreement with the frozen reference partition (not a new clusterer)."""

    y = np.asarray(list(reference))
    p = np.asarray(list(predicted))
    if y.ndim != 1 or p.ndim != 1 or y.size != p.size or y.size == 0:
        raise ValueError("reference and predicted must be non-empty vectors of equal length")
    return float(np.mean(y == p))


def schema_transform(
    X: np.ndarray,
    feature_names: Iterable[str],
    *,
    schema_path: str | Path | None = None,
) -> tuple[np.ndarray, tuple[str, ...]]:
    """Apply feature-schema-declared transforms before fitting a scaler."""

    values = np.asarray(X, dtype=float)
    names = tuple(str(x) for x in feature_names)
    if values.ndim != 2 or len(names) != values.shape[1] or not np.isfinite(values).all():
        raise ValueError("X and feature_names must describe a finite 2-D matrix")
    if schema_path is None:
        schema_path = Path(__file__).resolve().parents[2] / "data" / "derived" / "feature_schema.csv"
    schema = pd.read_csv(schema_path).set_index("feature")
    unknown = sorted(set(names).difference(schema.index))
    if unknown:
        raise ValueError(f"features missing from frozen feature_schema.csv: {unknown}")
    out = values.copy()
    transformed: list[str] = []
    for j, name in enumerate(names):
        transform = str(schema.loc[name, "transform"]).strip().lower()
        if transform == "log1p":
            if np.min(out[:, j]) < 0:
                raise ValueError(f"log1p feature must be non-negative: {name}")
            out[:, j] = np.log1p(out[:, j])
            transformed.append(name)
        elif transform not in {"none", "identity", ""}:
            raise ValueError(f"unsupported feature transform in schema: {transform!r} ({name})")
    return out, tuple(transformed)


def select_k_train_only(
    X_train: np.ndarray,
    *,
    representation: str,
    split_seed: int,
    k_values: Iterable[int] = K_GRID,
) -> KSelection:
    """Select k on a training matrix using frozen label-free tie-breaks."""

    values = np.asarray(X_train, dtype=float)
    if values.ndim != 2 or values.shape[0] < 3 or not np.isfinite(values).all():
        raise ValueError("X_train must be a finite 2-D matrix with at least three rows")
    candidates: list[dict[str, Any]] = []
    models: dict[int, KMeans] = {}
    for candidate_k in sorted({int(k) for k in k_values}):
        if not 2 <= candidate_k <= 12 or candidate_k >= values.shape[0]:
            continue
        model = KMeans(n_clusters=candidate_k, init="k-means++", n_init=20,
                       random_state=int(split_seed))
        _fit_kmeans_deterministic(model, values)
        labels = model.labels_
        if np.unique(labels).size < 2:
            continue
        candidates.append({
            "representation": str(representation), "split_seed": int(split_seed),
            "k": candidate_k, "train_silhouette": float(silhouette_score(values, labels)),
            "train_dbi": float(davies_bouldin_score(values, labels)),
            "train_ch": float(calinski_harabasz_score(values, labels)),
            "selection_scope": "train_only_label_free", "selected": False,
        })
        models[candidate_k] = model
    if not candidates:
        raise ValueError("no valid k candidate on training matrix")
    table = pd.DataFrame(candidates).sort_values(
        ["train_silhouette", "train_dbi", "train_ch", "k"],
        ascending=[False, True, False, True], kind="mergesort").reset_index(drop=True)
    chosen_k = int(table.iloc[0]["k"])
    table.loc[table["k"] == chosen_k, "selected"] = True
    return KSelection(chosen_k, models[chosen_k], table)


def _tree_engine() -> str:
    return "exkmc_0.0.3" if _ExKMCTree is not None else "sklearn_threshold_compatibility_fallback"


def _fit_tree(X_train: np.ndarray, reference: KMeans, k_prime: int, seed: int) -> tuple[Any, str]:
    k = int(reference.n_clusters)
    if not k <= int(k_prime) <= 4 * k:
        raise ValueError("k_prime must lie in the frozen k..4k grid")
    if _ExKMCTree is not None:
        tree = _ExKMCTree(k=k, max_leaves=int(k_prime), verbose=0, light=True,
                          base_tree="IMM", n_jobs=1, random_state=int(seed))
        numpy_state = np.random.get_state()
        python_state = random.getstate()
        np.random.seed(int(seed))
        random.seed(int(seed))
        try:
            # ExKMC 0.0.3 computes expansion costs with np.dot.  Its result
            # can vary in the last bits when OpenBLAS reduces a dot product
            # across threads; those tiny differences can change a tied
            # best-split decision and hence the exported tree.  Keep the
            # pinned ExKMC algorithm and its Cython splitters, but make the
            # numeric reduction order reproducible at this boundary.
            with threadpool_limits(limits=1, user_api="blas"):
                tree.fit(X_train, kmeans=reference)
        finally:
            np.random.set_state(numpy_state)
            random.setstate(python_state)
        return tree, "exkmc_0.0.3"

    # This branch is a test/portability aid only.  It is deliberately named so
    # a result cannot be mistaken for a run made by the pinned ExKMC package.
    from sklearn.tree import DecisionTreeClassifier

    tree = DecisionTreeClassifier(max_leaf_nodes=int(k_prime), random_state=int(seed))
    tree.fit(X_train, reference.labels_)
    return tree, "sklearn_threshold_compatibility_fallback"


def fit_exkmc_split(
    X: np.ndarray,
    *,
    representation: str,
    split_seed: int,
    k: int | None = None,
    k_prime: int | None = None,
    feature_names: Iterable[str] | None = None,
    schema_path: str | Path | None = None,
    selection: KSelection | None = None,
    train_fraction: float = 0.8,
) -> ExplanationFit:
    """Fit scaler, KMeans reference, and ExKMC using training rows only."""

    values = np.asarray(X, dtype=float)
    if values.ndim != 2 or values.shape[0] < 3 or values.shape[1] < 1:
        raise ValueError("X must be a non-empty 2-D feature matrix")
    if not np.isfinite(values).all():
        raise ValueError("X must contain only finite values")
    split = deterministic_split(values.shape[0], split_seed, train_fraction)
    if feature_names is None:
        feature_names = tuple(f"feature_{i}" for i in range(values.shape[1]))
        transformed_values, transformed_columns = values, tuple()
    else:
        transformed_values, transformed_columns = schema_transform(values, feature_names, schema_path=schema_path)
    X_train_raw = transformed_values[split.train_indices]
    X_test_raw = transformed_values[split.test_indices]
    scaler = StandardScaler().fit(X_train_raw)
    X_train = scaler.transform(X_train_raw).astype(float, copy=False)
    X_test = scaler.transform(X_test_raw).astype(float, copy=False)
    if selection is None:
        if k is None:
            selection = select_k_train_only(
                X_train, representation=representation, split_seed=split_seed
            )
        else:
            selection = fit_fixed_k_train_only(
                X_train, representation=representation, split_seed=split_seed, k=int(k)
            )
    if k is not None and int(k) != selection.k:
        raise ValueError(f"explicit k={k} disagrees with train-only selection k={selection.k}")
    k = selection.k
    if k_prime is None:
        k_prime = int(k)
    reference = selection.model
    tree, engine = _fit_tree(X_train, reference, int(k_prime), int(split_seed))
    train_ref = reference.predict(X_train).astype(int, copy=False)
    test_ref = reference.predict(X_test).astype(int, copy=False)
    train_pred = np.asarray(tree.predict(X_train), dtype=int)
    test_pred = np.asarray(tree.predict(X_test), dtype=int)
    return ExplanationFit(
        representation=str(representation), split_seed=int(split_seed), k=int(k),
        k_prime=int(k_prime), scaler=scaler, kmeans=reference, tree=tree,
        engine=engine, train_indices=split.train_indices,
        test_indices=split.test_indices, X_train_scaled=X_train,
        reference_train_labels=train_ref,
        reference_test_labels=test_ref, train_predictions=train_pred,
        test_predictions=test_pred,
        k_selection_scope=str(selection.candidates.iloc[0]["selection_scope"]),
        k_candidate_count=int(len(selection.candidates)),
        selected_train_silhouette=float(selection.candidates.iloc[0]["train_silhouette"]),
        selected_train_dbi=float(selection.candidates.iloc[0]["train_dbi"]),
        selected_train_ch=float(selection.candidates.iloc[0]["train_ch"]),
        transformed_columns=transformed_columns,
        k_selection_candidates=selection.candidates.copy(),
    )


def _node_is_leaf(node: Any) -> bool:
    if hasattr(node, "is_leaf"):
        return bool(node.is_leaf())
    return getattr(node, "children_left", -1) == -1


def _iter_rules(tree: Any) -> list[dict[str, Any]]:
    """Extract every leaf path, retaining a row for leaves with no condition."""

    if _ExKMCTree is not None and isinstance(tree, _ExKMCTree):
        leaf_counter = [0]
        def walk(node: Any, conditions: list[dict[str, Any]], path: str):
            if node.is_leaf():
                leaf_id = leaf_counter[0]
                leaf_counter[0] += 1
                yield {"leaf_id": leaf_id, "cluster_id": int(node.value),
                       "path": path or "TRUE", "conditions": list(conditions),
                       "samples": int(node.samples or 0)}
                return
            f, t = int(node.feature), float(node.value)
            yield from walk(node.left, conditions + [{"feature_index": f, "threshold": t,
                                                        "direction": "<="}],
                            f"{path} AND x[{f}] <= {t:.17g}" if path else f"x[{f}] <= {t:.17g}")
            yield from walk(node.right, conditions + [{"feature_index": f, "threshold": t,
                                                         "direction": ">"}],
                            f"{path} AND x[{f}] > {t:.17g}" if path else f"x[{f}] > {t:.17g}")
        return list(walk(tree.tree, [], ""))

    # sklearn compatibility tree; its children and thresholds are arrays.
    def walk_sklearn(node_id: int, conditions: list[dict[str, Any]], path: str):
        children_left = tree.tree_.children_left
        children_right = tree.tree_.children_right
        if children_left[node_id] == -1:
            values = tree.tree_.value[node_id][0]
            cluster = int(np.argmax(values))
            yield {"leaf_id": int(node_id), "cluster_id": cluster,
                   "path": path or "TRUE", "conditions": list(conditions),
                   "samples": int(tree.tree_.n_node_samples[node_id])}
            return
        f, t = int(tree.tree_.feature[node_id]), float(tree.tree_.threshold[node_id])
        yield from walk_sklearn(int(children_left[node_id]),
                                conditions + [{"feature_index": f, "threshold": t, "direction": "<="}],
                                f"{path} AND x[{f}] <= {t:.17g}" if path else f"x[{f}] <= {t:.17g}")
        yield from walk_sklearn(int(children_right[node_id]),
                                conditions + [{"feature_index": f, "threshold": t, "direction": ">"}],
                                f"{path} AND x[{f}] > {t:.17g}" if path else f"x[{f}] > {t:.17g}")
    return list(walk_sklearn(0, [], ""))


def tree_complexity(fit: ExplanationFit) -> dict[str, float | int]:
    """Report effective non-empty rules, depth and per-rule conditions."""

    rules = _iter_rules(fit.tree)
    # Effective means a leaf reached by at least one training observation.  It
    # is computed from predictions, never from held-out rows.
    counts = {int(r["leaf_id"]): 0 for r in rules}
    if _ExKMCTree is not None and isinstance(fit.tree, _ExKMCTree):
        leaf_counter = [0]
        def assign(node: Any, x: np.ndarray) -> None:
            if node.is_leaf():
                leaf_id = leaf_counter[0]
                leaf_counter[0] += 1
                counts[leaf_id] += int(x.shape[0])
                return
            mask = x[:, int(node.feature)] <= float(node.value)
            assign(node.left, x[mask]); assign(node.right, x[~mask])
        assign(fit.tree.tree, fit.X_train_scaled)
    else:
        for node_id, value in zip(fit.tree.apply(fit.X_train_scaled), fit.train_predictions):
            counts[int(node_id)] = counts.get(int(node_id), 0) + 1
    effective = [r for r in rules if counts.get(int(r["leaf_id"]), 0) > 0]
    lengths = [len(r["conditions"]) for r in effective]
    max_depth = max(lengths, default=0)
    return {
        "leaves": int(len(rules)), "leaf_count": int(len(rules)),
        "effective_rules": int(len(effective)), "effective_rule_count": int(len(effective)),
        "max_depth": int(max_depth), "depth": int(max_depth),
        "mean_conditions_per_rule": float(np.mean(lengths)) if lengths else 0.0,
        "conditions_per_rule_mean": float(np.mean(lengths)) if lengths else 0.0,
        "max_conditions_per_rule": int(max_depth),
    }


def rule_rows(fit: ExplanationFit, feature_names: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Return rule rows with both model-space and original-unit thresholds."""

    names = list(feature_names) if feature_names is not None else []
    rows = []
    for rid, rule in enumerate(_iter_rules(fit.tree)):
        conds = rule["conditions"]
        if not conds:
            conds = [{"feature_index": "", "feature": "", "threshold": "",
                      "direction": "TRUE"}]
        for ci, condition in enumerate(conds):
            fidx = condition.get("feature_index", "")
            feature = names[int(fidx)] if names and fidx != "" else condition.get("feature", "")
            threshold_scaled = condition.get("threshold", "")
            threshold_original: float | str = ""
            transform = ""
            if fidx != "" and threshold_scaled != "":
                transformed_threshold = (
                    float(threshold_scaled) * float(fit.scaler.scale_[int(fidx)])
                    + float(fit.scaler.mean_[int(fidx)])
                )
                if feature in fit.transformed_columns:
                    threshold_original = float(np.expm1(transformed_threshold))
                    transform = "log1p_then_standardize"
                else:
                    threshold_original = float(transformed_threshold)
                    transform = "standardize"
            rows.append({
                "representation": fit.representation, "split_seed": fit.split_seed,
                "k": fit.k, "k_prime": fit.k_prime, "rule_id": rid,
                "leaf_id": rule["leaf_id"], "cluster_id": rule["cluster_id"],
                "condition_index": ci, "feature_index": fidx,
                "feature": feature,
                "threshold": threshold_original,
                "threshold_original": threshold_original,
                "threshold_scaled": threshold_scaled,
                "feature_transform": transform,
                "direction": condition.get("direction", "TRUE"),
                "path": rule["path"], "condition_count": len(rule["conditions"]),
                "leaf_training_samples": rule.get("samples", ""),
                "engine": fit.engine,
            })
    return rows


def _summary_row(fit: ExplanationFit) -> dict[str, Any]:
    complexity = tree_complexity(fit)
    return {
        "representation": fit.representation, "split_seed": fit.split_seed,
        "k": fit.k, "k_prime": fit.k_prime, "engine": fit.engine,
        "train_fidelity": fidelity(fit.reference_train_labels, fit.train_predictions),
        "test_fidelity": fidelity(fit.reference_test_labels, fit.test_predictions),
        # Fixed seed, frozen scaler, KMeans and tree construction are all
        # deterministic.  This is a reproducibility stability indicator, not
        # a claim that the partition is stable under data perturbation.
        "stability": 1.0,
        "stability_definition": "fixed_seed_reproducibility",
        "k_selection_scope": fit.k_selection_scope,
        "k_candidate_count": fit.k_candidate_count,
        "selected_train_silhouette": fit.selected_train_silhouette,
        "selected_train_dbi": fit.selected_train_dbi,
        "selected_train_ch": fit.selected_train_ch,
        "transformed_columns": json.dumps(list(fit.transformed_columns), separators=(",", ":")),
        **complexity,
        "test_rows_used_for_selection": 0,
        "scaler_fit_rows": int(fit.train_indices.size),
        "reference_fit_rows": int(fit.train_indices.size),
    }


def run_exkmc_experiment(
    representations: Mapping[str, np.ndarray],
    *,
    split_seeds: Iterable[int] = EXKMC_SPLIT_SEEDS,
    train_fraction: float = 0.8,
    feature_names: Mapping[str, Iterable[str]] | None = None,
    schema_path: str | Path | None = None,
    return_selection: bool = False,
    fixed_k: Mapping[str, int] | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame] | tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Run train-only K Means and ExKMC fits across the frozen leaf grids."""

    summary: list[dict[str, Any]] = []
    rules: list[dict[str, Any]] = []
    selections: list[pd.DataFrame] = []
    for name, matrix in representations.items():
        for seed in tuple(int(s) for s in split_seeds):
            names = feature_names.get(name) if feature_names is not None else None
            # First fit performs split-local selection.  Subsequent k-prime
            # fits reuse only that train-derived KMeans/scaler decision.
            requested_k = int(fixed_k[name]) if fixed_k is not None else None
            first = fit_exkmc_split(matrix, representation=name, k=requested_k, k_prime=None,
                                    split_seed=seed, feature_names=names,
                                    schema_path=schema_path, train_fraction=train_fraction)
            selected = KSelection(first.k, first.kmeans, first.k_selection_candidates)
            selections.append(selected.candidates)
            for k_prime in range(first.k, 4 * first.k + 1):
                fit = first if k_prime == first.k else fit_exkmc_split(
                    matrix, representation=name, k=first.k, k_prime=k_prime,
                    split_seed=seed, feature_names=names, schema_path=schema_path,
                    train_fraction=train_fraction, selection=selected)
                summary.append(_summary_row(fit))
                rules.extend(rule_rows(fit, names))
    result = (pd.DataFrame(summary), pd.DataFrame(rules))
    if return_selection:
        return result + (pd.concat(selections, ignore_index=True),)
    return result


def load_selected_k(path: str | Path) -> dict[str, int]:
    """Read frozen k selections; reject files that do not declare train-only selection."""

    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"selected configuration file is required: {p}")
    frame = pd.read_json(p) if p.suffix.lower() == ".json" else pd.read_csv(p)
    required = {"representation", "k"}
    if not required.issubset(frame.columns):
        raise ValueError(f"selected configuration missing columns: {sorted(required - set(frame.columns))}")
    scope_col = next((c for c in ("selection_scope", "selection", "selection_rule") if c in frame.columns), None)
    if scope_col is None:
        raise ValueError("selected configuration must declare selection_scope/selection_rule")
    forbidden = {"test", "oos", "oracle", "all_data"}
    values = {}
    for _, row in frame.iterrows():
        scope = str(row[scope_col]).lower()
        if any(token in scope for token in forbidden):
            raise ValueError(f"test-derived selection is forbidden: {scope}")
        rep, k = str(row["representation"]), int(row["k"])
        if rep in values and values[rep] != k:
            raise ValueError(f"duplicate conflicting k for {rep}")
        if not 2 <= k <= 12:
            raise ValueError(f"k outside frozen grid for {rep}: {k}")
        values[rep] = k
    return values


def write_exkmc_results(summary: pd.DataFrame, rules: pd.DataFrame, output_dir: str | Path,
                        k_selection: pd.DataFrame | None = None) -> None:
    """Write the two requested CSVs without filtering on test performance."""

    out = Path(output_dir); out.mkdir(parents=True, exist_ok=True)
    summary.to_csv(out / "exkmc_oos_fidelity.csv", index=False)
    complexity_cols = [c for c in (
        "representation", "split_seed", "k", "k_prime", "engine", "leaves", "leaf_count",
        "effective_rules", "effective_rule_count", "max_depth", "depth",
        "mean_conditions_per_rule", "conditions_per_rule_mean", "max_conditions_per_rule",
        "stability", "stability_definition",
    ) if c in summary.columns]
    summary[complexity_cols].to_csv(out / "explanation_complexity.csv", index=False)
    rules.to_csv(out / "exkmc_rules.csv", index=False)
    if k_selection is not None:
        k_selection.to_csv(out / "exkmc_train_k_selection.csv", index=False)


__all__ = [
    "EXKMC_SPLIT_SEEDS", "ExplanationFit", "deterministic_split", "fidelity",
    "fit_exkmc_split", "fit_fixed_k_train_only", "load_selected_k", "rule_rows", "run_exkmc_experiment",
    "tree_complexity", "write_exkmc_results",
]
