"""Sensitivity analyses for the frozen dual-representation experiment.

The functions in this package are deliberately independent of configuration
selection.  A selected clustering fit is supplied as a small ``fit_predict``
callable, so sensitivity calculations cannot silently select a new model.
"""

from .core import (
    METRIC_COLUMNS,
    evaluate_labels,
    feature_ablation,
    pca_variance_diagnostic,
    perturbation_stability,
    permutation_dimension_control,
)
from .sessions import (
    reconstruct_session_counts,
    session_window_sensitivity,
    replace_session_feature,
)

__all__ = [
    "METRIC_COLUMNS",
    "evaluate_labels",
    "feature_ablation",
    "pca_variance_diagnostic",
    "perturbation_stability",
    "permutation_dimension_control",
    "reconstruct_session_counts",
    "replace_session_feature",
    "session_window_sensitivity",
]
