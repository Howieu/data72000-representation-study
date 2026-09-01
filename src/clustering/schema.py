"""Column contracts for the clustering result artefacts."""

from __future__ import annotations

from pathlib import Path

import pandas as pd


SCHEMAS: dict[str, tuple[str, ...]] = {
    "candidate_grid.csv": (
        "representation", "method", "candidate_id", "parameters", "seed",
        "n_samples", "n_clusters", "n_clusters_excluding_noise", "n_noise", "noise_fraction",
        "largest_non_noise_cluster_share", "internal_valid", "silhouette",
        "davies_bouldin", "calinski_harabasz", "runtime_seconds",
        "cluster_sizes",
    ),
    "selected_configurations.csv": (
        "representation", "method", "selection", "candidate_id", "parameters",
        "n_clusters", "n_clusters_excluding_noise", "n_noise", "noise_fraction",
        "largest_non_noise_cluster_share", "silhouette", "davies_bouldin",
        "calinski_harabasz", "deployment_acceptable",
    ),
    "selected_labels.csv": (
        "visitorid", "representation", "method", "selection", "candidate_id", "label",
    ),
    "paired_partition_comparison.csv": (
        "comparison", "method", "parameter_key", "parameter_value", "k",
        "left_representation", "right_representation", "n_samples", "ari", "nmi", "vi",
        "availability",
    ),
    "cluster_transition_matrix.csv": (
        "method", "comparison", "parameter_key", "parameter_value", "source_representation",
        "target_representation", "source_cluster", "target_cluster_original",
        "target_cluster_matched", "n_customers", "share_of_customers", "migration_flag",
    ),
    "resampling_stability.csv": (
        "representation", "method", "selection", "candidate_id", "pair_id", "seed_left",
        "seed_right", "sample_fraction", "n_left", "n_right", "n_overlap", "valid_overlap",
        "ari_overlap",
    ),
    "classix_parameter_sensitivity.csv": (
        "representation", "summary_level", "radius", "minPts", "group_merging", "n_candidates",
        "valid_internal_count", "deployment_acceptable_count", "mean_silhouette",
        "max_silhouette", "noise_fraction_min", "noise_fraction_max",
    ),
    "classix_boundary_extension.csv": (
        "amendment_id", "grid_scope", "representation", "method", "candidate_id",
        "parameters", "n_samples", "n_clusters", "n_clusters_excluding_noise",
        "n_noise", "noise_fraction", "largest_non_noise_cluster_share",
        "internal_valid", "silhouette", "davies_bouldin", "calinski_harabasz",
        "runtime_seconds", "cluster_sizes",
    ),
    "cluster_profiles.csv": (
        "representation", "method", "selection", "candidate_id", "cluster", "cluster_is_noise",
        "feature", "n_customers", "share_of_all_customers", "share_of_non_noise_customers",
        "median", "q25", "q75", "global_median", "iqr_effect",
    ),
}


def validate_schema(frame: pd.DataFrame, artifact_name: str) -> None:
    expected = SCHEMAS.get(artifact_name)
    if expected is None:
        raise KeyError(f"unknown clustering artifact: {artifact_name}")
    missing = [column for column in expected if column not in frame.columns]
    if missing:
        raise ValueError(f"{artifact_name} missing columns: {missing}")


def write_schema_files(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    for name, columns in SCHEMAS.items():
        pd.DataFrame({"column": columns, "position": range(len(columns))}).to_csv(
            output_dir / f"{name}.schema.csv", index=False
        )
