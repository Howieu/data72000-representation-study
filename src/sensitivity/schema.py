"""Schemas for sensitivity result artefacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SCHEMAS: dict[str, tuple[str, ...]] = {
    "feature_ablation.csv": ("algorithm", "representation", "selection", "candidate_id", "parameters", "dropped_feature", "n_features", "n_clusters", "largest_non_noise_cluster_share", "silhouette", "davies_bouldin", "calinski_harabasz", "ari", "stability_ari", "n_noise", "noise_fraction"),
    "pca_sensitivity.csv": ("representation", "space", "algorithm", "selection", "candidate_id", "parameters", "variance_threshold", "n_features", "n_components", "cumulative_explained_variance", "standardized", "use_for_rules", "n_clusters", "largest_non_noise_cluster_share", "silhouette", "davies_bouldin", "calinski_harabasz", "n_noise", "noise_fraction", "reference_ari", "resampling_ari_mean", "resampling_ari_std", "resampling_pairs"),
    "classix_perturbation_stability.csv": ("algorithm", "representation", "selection", "candidate_id", "parameters", "sigma", "seed", "n_clusters", "largest_non_noise_cluster_share", "silhouette", "davies_bouldin", "calinski_harabasz", "ari", "stability_ari", "n_noise", "noise_fraction"),
    "session_window_sensitivity.csv": ("algorithm", "representation", "selection", "candidate_id", "parameters", "window_minutes", "affected_dimension", "n_features", "n_clusters", "largest_non_noise_cluster_share", "silhouette", "davies_bouldin", "calinski_harabasz", "ari", "stability_ari", "n_noise", "noise_fraction"),
    "permutation_dimension_control.csv": ("algorithm", "representation", "selection", "candidate_id", "parameters", "n_features", "added_permuted_features", "permuted_feature_names", "compact_columns_unchanged", "rich_joint_structure_preserved", "n_clusters", "largest_non_noise_cluster_share", "silhouette", "davies_bouldin", "calinski_harabasz", "ari", "stability_ari", "n_noise", "noise_fraction"),
}


def write_schemas(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for filename, columns in SCHEMAS.items():
        pd.DataFrame({"column": columns, "position": range(len(columns))}).to_csv(output_dir / f"{filename}.schema.csv", index=False)
