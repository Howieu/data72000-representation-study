"""Command-line entry point for the frozen RetailRocket clustering stage."""

from __future__ import annotations

import argparse
import json
import platform
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from ..protocol import classix_radii, load_protocol
from .engine import (
    DEFAULT_DERIVED,
    DEFAULT_PROTOCOL,
    _classix_fit,
    _stable_json,
    cluster_profiles,
    load_representations,
    paired_comparisons,
    run_candidate_grid,
    select_configurations,
    selected_labels_frame,
    transition_matrix,
)
from .metrics import cluster_sizes, evaluate_partition
from .schema import SCHEMAS, validate_schema, write_schema_files
from .stability import resampling_stability


def _classix_sensitivity(candidates: pd.DataFrame) -> pd.DataFrame:
    """Summarise marginal CLASSIX sensitivity without duplicating the grid."""
    rows: list[dict[str, Any]] = []
    sub = candidates[candidates["method"] == "classix"].copy()
    parsed = sub["parameters"].map(json.loads)
    sub["radius"] = parsed.map(lambda value: float(value["radius"]))
    sub["minPts"] = parsed.map(lambda value: int(value["minPts"]))
    sub["group_merging"] = parsed.map(lambda value: str(value["group_merging"]))

    def append_summary(
        representation: str,
        summary_level: str,
        group: pd.DataFrame,
        *,
        radius: float | None = None,
        min_pts: int | None = None,
        merging: str | None = None,
    ) -> None:
        deployment = (
            group["internal_valid"].fillna(False)
            & group["n_clusters"].between(2, 12)
            & (group["noise_fraction"] <= 0.2)
            & (group["largest_non_noise_cluster_share"] <= 0.95)
        )
        rows.append({
            "representation": representation, "summary_level": summary_level,
            "radius": radius, "minPts": min_pts, "group_merging": merging,
            "n_candidates": len(group),
            "valid_internal_count": int(group["internal_valid"].sum()),
            "deployment_acceptable_count": int(deployment.sum()),
            "mean_silhouette": float(group["silhouette"].mean()),
            "max_silhouette": float(group["silhouette"].max()),
            "noise_fraction_min": float(group["noise_fraction"].min()),
            "noise_fraction_max": float(group["noise_fraction"].max()),
        })

    for representation, rep in sub.groupby("representation", sort=True):
        for radius, group in rep.groupby("radius", sort=True):
            append_summary(str(representation), "radius_marginal", group, radius=float(radius))
        for min_pts, group in rep.groupby("minPts", sort=True):
            append_summary(str(representation), "minPts_marginal", group, min_pts=int(min_pts))
        for merging, group in rep.groupby("group_merging", sort=True):
            append_summary(str(representation), "merging_marginal", group, merging=str(merging))
    frame = pd.DataFrame(rows)
    validate_schema(frame, "classix_parameter_sensitivity.csv")
    return frame


def _grid_boundary_diagnostic(candidates: pd.DataFrame, protocol: dict[str, Any]) -> dict[str, Any]:
    radii = [float(x) for x in classix_radii(protocol)]
    classix = candidates[candidates["method"] == "classix"].copy()
    classix["radius"] = classix["parameters"].map(lambda value: float(json.loads(value)["radius"]))
    by_representation: dict[str, Any] = {}
    trigger = False
    for representation, rep in classix.groupby("representation", sort=True):
        edges = rep[rep["radius"].isin({min(radii), max(radii)})]
        valid = rep[rep["internal_valid"].fillna(False)].sort_values(
            ["silhouette", "davies_bouldin", "calinski_harabasz", "parameters"],
            ascending=[False, True, False, True],
        )
        best = valid.head(20)
        best_radius = float(valid.iloc[0]["radius"]) if not valid.empty else None
        best_at_boundary = bool(best_radius in {min(radii), max(radii)}) if best_radius is not None else False
        trigger = trigger or best_at_boundary
        boundary_best_count = int(best["radius"].isin({min(radii), max(radii)}).sum()) if not best.empty else 0
        by_representation[str(representation)] = {
            "candidate_count": int(len(rep)),
            "boundary_candidate_count": int(len(edges)),
            "boundary_candidate_fraction": float(len(edges) / len(rep)) if len(rep) else 0.0,
            "best_internal_radius": best_radius,
            "best_internal_at_boundary": best_at_boundary,
            "top20_internal_boundary_count": boundary_best_count,
            "top20_internal_boundary_fraction": float(boundary_best_count / len(best)) if len(best) else 0.0,
        }
    return {
        "diagnostic_only": True,
        "grid_radius_start": min(radii), "grid_radius_stop": max(radii),
        "grid_radius_step": float(protocol["classix"]["radius_step"]),
        "candidate_count": int(len(classix)),
        "boundary_radii": [min(radii), max(radii)],
        "by_representation": by_representation,
        "boundary_extension_triggered": trigger,
        "extension_scope": "upper radius extension applied to both representations" if trigger else "none",
        "recommendation": "retain the frozen main grid and report any extension as supplementary sensitivity",
    }


def _boundary_extension(
    representations: dict[str, Any],
    protocol: dict[str, Any],
    diagnostic: dict[str, Any],
    amendment_path: Path,
) -> pd.DataFrame:
    """Run the conditional, symmetric supplementary radius extension."""
    columns = SCHEMAS["classix_boundary_extension.csv"]
    if not bool(diagnostic["boundary_extension_triggered"]):
        return pd.DataFrame(columns=columns)
    amendment = json.loads(amendment_path.read_text(encoding="utf-8"))
    start = float(amendment["radius_start"])
    stop = float(amendment["radius_stop"])
    step = float(amendment["radius_step"])
    count = int(round((stop - start) / step)) + 1
    radii = [round(start + i * step, 12) for i in range(count)]
    rows: list[dict[str, Any]] = []
    for representation, data in representations.items():
        for radius in radii:
            for min_pts in protocol["classix"]["minPts"]:
                for merging in protocol["classix"]["group_merging"]:
                    params = {
                        "sorting": "pca", "metric": "euclidean", "radius": radius,
                        "minPts": int(min_pts), "group_merging": str(merging),
                        "mergeScale": float(protocol["classix"]["mergeScale"]),
                        "mergeTinyGroups": True, "post_alloc": False,
                    }
                    labels, runtime = _classix_fit(data.scaled, params)
                    diagnostics = evaluate_partition(data.scaled, labels)
                    rows.append({
                        "amendment_id": amendment["amendment_id"],
                        "grid_scope": "supplementary_upper_radius_extension",
                        "representation": representation,
                        "method": "classix",
                        "candidate_id": f"classix_ext_r{radius:.2f}_m{int(min_pts)}_{merging}",
                        "parameters": _stable_json(params),
                        "n_samples": int(len(labels)),
                        **diagnostics,
                        "runtime_seconds": float(runtime),
                        "cluster_sizes": _stable_json(cluster_sizes(labels)),
                    })
    frame = pd.DataFrame(rows)
    frame["n_clusters_excluding_noise"] = frame["n_clusters"]
    validate_schema(frame, "classix_boundary_extension.csv")
    return frame


def run(output_dir: Path, protocol_path: Path = DEFAULT_PROTOCOL, derived_dir: Path = DEFAULT_DERIVED) -> dict[str, Any]:
    started = datetime.now(timezone.utc).isoformat()
    begin = time.perf_counter()
    protocol = load_protocol(protocol_path)
    representations = load_representations(derived_dir, protocol_path)
    candidates, labels = run_candidate_grid(representations, protocol_path)
    selected = select_configurations(candidates, protocol)
    labels_frame = selected_labels_frame(representations, selected, labels)
    paired = paired_comparisons(representations, labels, selected)
    transitions = transition_matrix(representations, labels, selected)
    stability = resampling_stability(representations, selected, protocol)
    profiles = cluster_profiles(representations, labels, selected)
    sensitivity = _classix_sensitivity(candidates)
    boundary = _grid_boundary_diagnostic(candidates, protocol)
    extension = _boundary_extension(
        representations, protocol, boundary,
        Path(protocol_path).parent / "amendment_boundary_extension.json",
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    artifacts = {
        "candidate_grid.csv": candidates,
        "selected_configurations.csv": selected,
        "selected_labels.csv": labels_frame,
        "paired_partition_comparison.csv": paired,
        "cluster_transition_matrix.csv": transitions,
        "resampling_stability.csv": stability,
        "classix_parameter_sensitivity.csv": sensitivity,
        "cluster_profiles.csv": profiles,
        "classix_boundary_extension.csv": extension,
    }
    for filename, frame in artifacts.items():
        frame.to_csv(output_dir / filename, index=False)
    (output_dir / "grid_boundary_diagnostic.json").write_text(
        json.dumps(boundary, indent=2, sort_keys=True), encoding="utf-8"
    )
    write_schema_files(output_dir)
    metadata = {
        "started_at_utc": started,
        "elapsed_seconds": time.perf_counter() - begin,
        "protocol_path": "protocol/analysis_protocol.json",
        "derived_tables": ["data/derived/compact_features.csv", "data/derived/rich_features.csv"],
        "n_visitors": int(len(next(iter(representations.values())).visitorid)),
        "candidate_rows": int(len(candidates)),
        "boundary_extension_rows": int(len(extension)),
        "classix_engine": "classixclustering==1.5.1",
        "python": sys.version, "platform": platform.platform(),
    }
    (output_dir / "run_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    return {"metadata": metadata, "boundary": boundary, "candidate_grid": candidates,
            "selected": selected, "paired": paired, "stability": stability}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("results/retailrocket"))
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--derived-dir", type=Path, default=DEFAULT_DERIVED)
    args = parser.parse_args()
    result = run(args.output_dir, args.protocol, args.derived_dir)
    print(f"wrote {result['candidate_grid'].shape[0]} candidate rows to {args.output_dir}")


if __name__ == "__main__":
    main()
