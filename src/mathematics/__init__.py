"""Auditable mathematics for the pinned CLASSIX implementation.

The functions in this package are small, dependency-light checks used by the
recorded numerical evidence.  They describe the implementation's Euclidean
aggregation and distance-merging branches; they are not a reimplementation of
the clustering library.
"""

from .classix_math import (
    StabilityMargins,
    complexity_summary,
    conditional_determinism,
    davis_kahan_direction_bound,
    local_stability_certificate,
    pca_score_perturbation_bound,
    projection_band_candidates,
    projection_pruning_check,
)

__all__ = [
    "StabilityMargins",
    "complexity_summary",
    "conditional_determinism",
    "davis_kahan_direction_bound",
    "local_stability_certificate",
    "pca_score_perturbation_bound",
    "projection_band_candidates",
    "projection_pruning_check",
]
