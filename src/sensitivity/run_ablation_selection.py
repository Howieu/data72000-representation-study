"""Rerun the frozen candidate and selection protocol for every feature ablation."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from src.clustering.engine import (
    RepresentationData,
    load_representations,
    run_candidate_grid,
    select_configurations,
)
from src.protocol import load_protocol


BLOCK_ORDER = (
    "compact_transaction",
    "activity",
    "conversion",
    "temporal_engagement",
    "category_behaviour",
)


def scenario_definitions(schema: pd.DataFrame, rich_features: tuple[str, ...]) -> list[dict[str, Any]]:
    block = schema.set_index("feature")["block"].astype(str).to_dict()
    scenarios: list[dict[str, Any]] = []
    for feature in rich_features:
        included = [name for name in rich_features if name != feature]
        scenarios.append({
            "scenario_type": "leave_one_out",
            "scenario_id": f"drop_feature_{feature}",
            "included_features": included,
            "dropped_features": [feature],
        })
    for block_name in BLOCK_ORDER:
        dropped = [name for name in rich_features if block[name] == block_name]
        included = [name for name in rich_features if name not in dropped]
        scenarios.append({
            "scenario_type": "drop_block",
            "scenario_id": f"drop_block_{block_name}",
            "included_features": included,
            "dropped_features": dropped,
        })
    included: list[str] = []
    for block_name in BLOCK_ORDER:
        included.extend(name for name in rich_features if block[name] == block_name)
        scenarios.append({
            "scenario_type": "progressive_block",
            "scenario_id": f"through_block_{block_name}",
            "included_features": list(included),
            "dropped_features": [name for name in rich_features if name not in included],
        })
    expected = len(rich_features) + 2 * len(BLOCK_ORDER)
    if len(scenarios) != expected or any(not item["included_features"] for item in scenarios):
        raise AssertionError("frozen ablation scenario contract failed")
    return scenarios


def _deployment_labels(root: Path, visitorids: np.ndarray) -> dict[tuple[str, str], np.ndarray]:
    frame = pd.read_csv(root / "results" / "retailrocket" / "selected_labels.csv")
    frame = frame[frame["selection"].eq("deployment_acceptable")]
    out: dict[tuple[str, str], np.ndarray] = {}
    for (representation, method), part in frame.groupby(["representation", "method"]):
        ordered = part.set_index("visitorid").reindex(visitorids)["label"]
        if ordered.isna().any():
            raise ValueError(f"incomplete reference labels for {representation} {method}")
        out[(str(representation), str(method))] = ordered.to_numpy(dtype=int)
    return out


def run(root: Path, output_dir: Path) -> dict[str, Any]:
    protocol_path = root / "protocol" / "analysis_protocol.json"
    protocol = load_protocol(protocol_path)
    representations = load_representations(root / "data" / "derived", protocol_path)
    rich = representations["rich"]
    schema = pd.read_csv(root / "data" / "derived" / "feature_schema.csv")
    scenarios = scenario_definitions(schema, rich.features)
    references = _deployment_labels(root, rich.visitorid)
    feature_position = {name: index for index, name in enumerate(rich.features)}

    candidate_parts: list[pd.DataFrame] = []
    selected_parts: list[pd.DataFrame] = []
    for scenario in scenarios:
        features = tuple(scenario["included_features"])
        positions = [feature_position[name] for name in features]
        data = RepresentationData(
            name=scenario["scenario_id"],
            visitorid=rich.visitorid,
            raw=rich.raw[:, positions],
            features=features,
            transformed=rich.transformed[:, positions],
            scaled=rich.scaled[:, positions],
            scaler=rich.scaler,
        )
        candidates, labels = run_candidate_grid({scenario["scenario_id"]: data}, protocol_path)
        selected = select_configurations(candidates, protocol)
        context = {
            "scenario_type": scenario["scenario_type"],
            "scenario_id": scenario["scenario_id"],
            "included_features": json.dumps(features, separators=(",", ":")),
            "dropped_features": json.dumps(scenario["dropped_features"], separators=(",", ":")),
            "n_features": len(features),
        }
        for key, value in context.items():
            candidates[key] = value
            selected[key] = value
        selected["ari_vs_compact_deployment"] = np.nan
        selected["ari_vs_rich_deployment"] = np.nan
        for index, row in selected.iterrows():
            current = labels[(scenario["scenario_id"], row["method"], row["candidate_id"])]
            selected.loc[index, "ari_vs_compact_deployment"] = adjusted_rand_score(
                references[("compact", str(row["method"]))], current
            )
            selected.loc[index, "ari_vs_rich_deployment"] = adjusted_rand_score(
                references[("rich", str(row["method"]))], current
            )
        candidate_parts.append(candidates)
        selected_parts.append(selected)

    candidates_out = pd.concat(candidate_parts, ignore_index=True)
    selected_out = pd.concat(selected_parts, ignore_index=True)
    output_dir.mkdir(parents=True, exist_ok=True)
    candidates_out.to_csv(output_dir / "feature_ablation_candidate_grid.csv", index=False)
    selected_out.to_csv(output_dir / "feature_ablation_selected.csv", index=False)
    metadata = {
        "protocol_version": protocol["protocol_version"],
        "status": "complete",
        "scenario_count": len(scenarios),
        "candidate_rows": len(candidates_out),
        "selected_rows": len(selected_out),
        "selection_per_scenario": ["unconstrained_silhouette", "deployment_acceptable"],
        "candidate_grid_per_scenario": {"kmeans": 11, "classix": 186},
        "preprocessing": "retained columns preserve frozen rich full-data transforms and standardisation",
    }
    (output_dir / "feature_ablation_selection_metadata.json").write_text(
        json.dumps(metadata, indent=2), encoding="utf-8"
    )
    return metadata


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--output-dir", type=Path, default=Path("results/sensitivity"))
    args = parser.parse_args()
    run(args.root.resolve(), args.output_dir)


if __name__ == "__main__":
    main()
