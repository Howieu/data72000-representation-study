"""Out-of-sample explanations for the RetailRocket representations.

The package keeps ExKMC as an explanation of a frozen KMeans reference
partition.  It does not expose the explanation tree as a clustering method.
"""

from .exkmc_experiment import (
    EXKMC_SPLIT_SEEDS,
    deterministic_split,
    fidelity,
    fit_exkmc_split,
    run_exkmc_experiment,
    tree_complexity,
)

__all__ = [
    "EXKMC_SPLIT_SEEDS",
    "deterministic_split",
    "fidelity",
    "fit_exkmc_split",
    "run_exkmc_experiment",
    "tree_complexity",
]
