"""Mathematical checks for CLASSIX 1.5.1.

The implementation under audit sorts scalar projections and uses
``searchsorted(..., side='right')`` as a necessary-condition filter before
computing Euclidean distances.  This module makes that filter executable and
states only conditional stability claims.  In particular, a Davis--Kahan
bound is used only for the principal direction; it is not treated as a bound
on the complete clustering output.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable, Mapping

import numpy as np


def _as_2d_float(points: np.ndarray | Iterable[Iterable[float]]) -> np.ndarray:
    values = np.asarray(points, dtype=float)
    if values.ndim != 2 or values.shape[0] == 0:
        raise ValueError("points must be a non-empty two-dimensional array")
    if not np.isfinite(values).all():
        raise ValueError("points must be finite")
    return values


def projection_band_candidates(
    sorted_scores: np.ndarray | Iterable[float],
    start_position: int,
    radius: float,
) -> np.ndarray:
    """Return the later sorted positions retained by CLASSIX's band filter.

    For a unit direction ``u``, ``|u.T(x-c)| <= ||x-c||_2``.  Consequently a
    point with score larger than ``score(c)+radius`` cannot be within the
    Euclidean aggregation radius.  The implementation uses a right-inclusive
    boundary, matching ``np.searchsorted(..., side='right')`` in the 1.5.1
    Euclidean aggregation code.  The returned positions exclude the starting
    point itself, as does the inner loop in ``lm_aggregate``.
    """

    scores = np.asarray(sorted_scores, dtype=float)
    if scores.ndim != 1 or not np.isfinite(scores).all():
        raise ValueError("sorted_scores must be a finite one-dimensional array")
    if not 0 <= int(start_position) < scores.size:
        raise IndexError("start_position is outside sorted_scores")
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and non-negative")
    i = int(start_position)
    last = int(np.searchsorted(scores, scores[i] + radius, side="right"))
    return np.arange(i + 1, last, dtype=int)


def projection_pruning_check(
    points: np.ndarray | Iterable[Iterable[float]],
    direction: np.ndarray | Iterable[float],
    radius: float,
    *,
    order: np.ndarray | None = None,
    centers: Iterable[int] | None = None,
) -> dict[str, Any]:
    """Check that projection-band pruning has no false negatives.

    ``direction`` is normalized internally.  ``order`` is a permutation that
    puts the points in nondecreasing score order; if omitted a stable
    lexicographic order (score, original index) is used.  For each listed
    center, the check compares all later points within the complete distance
    ball against the points retained by the projection band.  This is the
    exact claim needed by the aggregation inner loop.  It does not claim that
    the greedy first-start assignment is invariant to changing the order.
    """

    x = _as_2d_float(points)
    u = np.asarray(direction, dtype=float).reshape(-1)
    if u.size != x.shape[1] or not np.isfinite(u).all() or np.linalg.norm(u) == 0:
        raise ValueError("direction must be a non-zero finite vector")
    if not np.isfinite(radius) or radius < 0:
        raise ValueError("radius must be finite and non-negative")
    u = u / np.linalg.norm(u)
    scores = x @ u
    if order is None:
        order = np.lexsort((np.arange(x.shape[0]), scores))
    else:
        order = np.asarray(order, dtype=int)
        if order.shape != (x.shape[0],) or not np.array_equal(np.sort(order), np.arange(x.shape[0])):
            raise ValueError("order must be a permutation of point indices")
    sorted_scores = scores[order]
    if np.any(np.diff(sorted_scores) < -1e-12):
        raise ValueError("order must be nondecreasing in projection score")
    center_positions = range(x.shape[0]) if centers is None else [int(c) for c in centers]
    false_negatives: list[tuple[int, int]] = []
    false_positives: list[tuple[int, int]] = []
    checked = 0
    retained = 0
    for i in center_positions:
        if not 0 <= i < x.shape[0]:
            raise IndexError("center position is outside the sorted order")
        c = x[order[i]]
        later = np.arange(i + 1, x.shape[0], dtype=int)
        exact = later[np.linalg.norm(x[order[later]] - c, axis=1) <= radius]
        candidate = projection_band_candidates(sorted_scores, i, radius)
        exact_set = set(exact.tolist())
        candidate_set = set(candidate.tolist())
        false_negatives.extend((i, j) for j in sorted(exact_set - candidate_set))
        false_positives.extend((i, j) for j in sorted(candidate_set - exact_set))
        checked += len(later)
        retained += len(candidate)
    return {
        "exact": not false_negatives,
        "false_negative_count": len(false_negatives),
        "false_positive_count": len(false_positives),
        "false_negatives": false_negatives,
        "false_positives": false_positives,
        "pairs_checked_without_band": checked,
        "pairs_retained_by_band": retained,
        "order": order.tolist(),
        "radius": float(radius),
    }


def complexity_summary(
    n_samples: int,
    n_features: int,
    n_groups: int,
    aggregation_distance_count: int,
    *,
    merge_distance_count: int = 0,
    sorting: str = "pca",
    pca_solver_branch: str | None = None,
) -> dict[str, Any]:
    """Summarize observed arithmetic counts and honest worst-case bounds.

    The scalar-band implementation can retain all later pairs, so its worst
    case is quadratic; the bound is not replaced by an empirical speed claim.
    Dot products in retained comparisons cost ``n_features`` arithmetic
    units.  PCA preprocessing is reported separately: the small-dimensional
    ``eigh`` Gram branch is ``O(n d^2 + d^3)``, while the larger-dimensional
    ``svds(k=1)`` branch is solver-dependent and is not assigned a fake exact
    constant.
    """

    n, d, q = int(n_samples), int(n_features), int(n_groups)
    agg = int(aggregation_distance_count)
    merge = int(merge_distance_count)
    if min(n, d, q, agg, merge) < 0 or q > n:
        raise ValueError("counts must be non-negative and n_groups <= n_samples")
    pair_bound = n * (n - 1) // 2
    merge_pair_bound = q * (q - 1) // 2
    branch = pca_solver_branch
    if sorting == "pca" and branch is None:
        branch = "eigh_gram_d_le_3" if d <= 3 else "svds_k_1_d_gt_3"
    return {
        "n_samples": n,
        "n_features": d,
        "n_groups": q,
        "sorting": sorting,
        "pca_solver_branch": branch,
        "aggregation_distance_count": agg,
        "aggregation_pair_bound": pair_bound,
        "aggregation_retained_fraction": agg / pair_bound if pair_bound else 0.0,
        "merge_distance_count": merge,
        "merge_pair_bound": merge_pair_bound,
        "total_distance_count": agg + merge,
        "distance_arithmetic_units": (agg + merge) * d,
        "worst_case_distance_arithmetic_units": (pair_bound + merge_pair_bound) * d,
        "complexity_statement": "O(n*d + d^3 + (n^2 + q^2)*d) worst case for projection and distance merging; minPts/post-allocation can add a q^2 nearest-centre pass",
    }


@dataclass(frozen=True)
class StabilityMargins:
    """Margins for the finite comparisons made by aggregation and merging."""

    eigengap: float
    projection_sort_gap: float
    projection_window_gap: float
    radius_judgement_gap: float
    merge_judgement_gap: float
    orientation_anchor_gap: float = 0.0


def conditional_determinism(
    scores: np.ndarray | Iterable[float],
    *,
    tie_policy: str = "stable_original_index",
    pca_eigengap: float | None = None,
) -> dict[str, Any]:
    """Report the conditions under which the sorted traversal is deterministic.

    A fixed score vector plus a fully specified tie policy gives a fixed
    permutation.  With the package's default ``np.argsort`` call, ties are not
    a documented semantic order, so deterministic labels additionally require
    no relevant score ties (or an order-invariance proof).  PCA itself needs a
    simple leading eigenvalue for a unique direction; a sign convention alone
    does not resolve a repeated eigenspace.
    """

    s = np.asarray(scores, dtype=float).reshape(-1)
    if s.size == 0 or not np.isfinite(s).all():
        raise ValueError("scores must be a non-empty finite vector")
    tie_policy = str(tie_policy)
    if tie_policy not in {"stable_original_index", "explicit_permutation", "package_argsort"}:
        raise ValueError("unknown tie policy")
    sorted_s = np.sort(s, kind="stable")
    tied_adjacent = np.flatnonzero(np.isclose(np.diff(sorted_s), 0.0, rtol=0.0, atol=0.0))
    no_ties = tied_adjacent.size == 0
    eigengap_ok = pca_eigengap is None or float(pca_eigengap) > 0.0
    deterministic = tie_policy in {"stable_original_index", "explicit_permutation"} and eigengap_ok
    if tie_policy == "package_argsort":
        deterministic = no_ties and eigengap_ok
    return {
        "deterministic_under_conditions": bool(deterministic),
        "tie_policy": tie_policy,
        "has_exact_score_ties": not no_ties,
        "tie_block_count": int(tied_adjacent.size),
        "pca_unique_direction_required": pca_eigengap is not None,
        "pca_eigengap_positive": bool(eigengap_ok),
        "condition": "fixed scores; positive eigengap when PCA is used; stable tie order or no relevant ties",
    }


def local_stability_certificate(
    margins: StabilityMargins | Mapping[str, float],
    *,
    score_perturbation_bound: float,
    distance_perturbation_bound: float,
    merge_distance_perturbation_bound: float | None = None,
    pca_direction_bound: float | None = None,
) -> dict[str, Any]:
    """Evaluate a sufficient, local finite-comparison stability certificate.

    If every strict comparison has margin larger than its perturbation bound,
    the corresponding branch decisions remain unchanged, provided the same
    candidate set and group representatives are being compared.  Thus this is
    a local sufficient condition, not a global continuity theorem for labels.
    ``pca_direction_bound`` records the Davis--Kahan principal-direction bound
    separately; it must be converted into ``score_perturbation_bound`` by the
    caller using a data-radius bound.
    """

    if not isinstance(margins, StabilityMargins):
        margins = StabilityMargins(
            eigengap=float(margins["eigengap"]),
            projection_sort_gap=float(margins["projection_sort_gap"]),
            projection_window_gap=float(margins["projection_window_gap"]),
            radius_judgement_gap=float(margins["radius_judgement_gap"]),
            merge_judgement_gap=float(margins["merge_judgement_gap"]),
            orientation_anchor_gap=float(margins.get("orientation_anchor_gap", 0.0)),
        )
    sb = float(score_perturbation_bound)
    db = float(distance_perturbation_bound)
    mb = db if merge_distance_perturbation_bound is None else float(merge_distance_perturbation_bound)
    if min(sb, db, mb) < 0:
        raise ValueError("perturbation bounds must be non-negative")
    checks = {
        "eigengap": margins.eigengap > 0.0,
        "projection_order": margins.projection_sort_gap > 2.0 * sb,
        "projection_window_membership": margins.projection_window_gap > 2.0 * sb,
        "orientation_sign": margins.orientation_anchor_gap > sb,
        "radius_decisions": margins.radius_judgement_gap > db,
        "merge_decisions": margins.merge_judgement_gap > mb,
    }
    return {
        "stable_under_conditions": bool(all(checks.values())),
        "checks": checks,
        "margins": asdict(margins),
        "bounds": {
            "score_perturbation_bound": sb,
            "distance_perturbation_bound": db,
            "merge_distance_perturbation_bound": mb,
            "davis_kahan_direction_bound": None if pca_direction_bound is None else float(pca_direction_bound),
        },
        "scope": "fixed branch, fixed tie policy, fixed orientation sign, fixed projection-window membership, fixed group representatives, and strict comparisons only",
        "global_label_stability_claim": False,
    }


def davis_kahan_direction_bound(operator_perturbation: float, eigengap: float) -> float:
    """A conservative sin(theta) bound for the leading PCA direction."""

    delta, gap = float(operator_perturbation), float(eigengap)
    if delta < 0 or gap <= 0:
        raise ValueError("operator_perturbation >= 0 and eigengap > 0 are required")
    return min(1.0, 2.0 * delta / gap)


def pca_score_perturbation_bound(
    max_point_norm: float,
    point_perturbation: float,
    operator_perturbation: float,
    eigengap: float,
) -> float:
    """Convert a direction-only Davis--Kahan bound into a score bound.

    This conservative conversion is for already-processed coordinates.  After
    sign alignment, ``||u_hat-u|| <= sqrt(2) sin(theta)`` for the acute angle
    between one-dimensional subspaces.  The returned bound is therefore
    ``epsilon_x + sqrt(2) B sin(theta)`` for a point norm bound ``B``.  Any perturbation
    of CLASSIX's centering or median/std scaling must be included in
    ``point_perturbation`` by the caller.
    """

    B, eps = float(max_point_norm), float(point_perturbation)
    if B < 0 or eps < 0:
        raise ValueError("max_point_norm and point_perturbation must be non-negative")
    return eps + np.sqrt(2.0) * B * davis_kahan_direction_bound(operator_perturbation, eigengap)
