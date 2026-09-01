"""Command-line entry point for the two RetailRocket explanation tracks."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any


_DETERMINISTIC_PROCESS_ENV = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def _reexec_with_deterministic_environment() -> None:
    """Restart the CLI before numerical libraries load when controls differ."""

    if __name__ != "__main__":
        return
    if all(os.environ.get(key) == value for key, value in _DETERMINISTIC_PROCESS_ENV.items()):
        return
    environment = dict(os.environ)
    environment.update(_DETERMINISTIC_PROCESS_ENV)
    completed = subprocess.run(
        [sys.executable, "-m", "src.explanation.run_retailrocket", *sys.argv[1:]],
        env=environment,
        check=False,
    )
    raise SystemExit(completed.returncode)


_reexec_with_deterministic_environment()

import numpy as np
import pandas as pd
from sklearn.metrics import adjusted_rand_score

from .addressability import audit_addressability, write_addressability_metadata
from .classix_provenance import fit_classix_provenance, write_classix_provenance
from .exkmc_experiment import EXKMC_SPLIT_SEEDS, run_exkmc_experiment, write_exkmc_results


def _read_classix_configs(path: Path) -> dict[str, dict[str, Any]]:
    frame = pd.read_json(path) if path.suffix.lower() == ".json" else pd.read_csv(path)
    required = {"representation", "method"}
    if not required.issubset(frame.columns):
        raise ValueError(f"selected configuration missing columns: {sorted(required - set(frame.columns))}")
    scope_col = next((c for c in ("selection_scope", "selection", "selection_rule") if c in frame.columns), None)
    if scope_col is None:
        raise ValueError("selected configuration must declare selection_scope/selection_rule")
    out = {}
    for _, row in frame.iterrows():
        if str(row["method"]).lower() != "classix":
            continue
        if "selection" in frame.columns and str(row["selection"]) != "deployment_acceptable":
            continue
        if "deployment_acceptable" in frame.columns:
            acceptable = row["deployment_acceptable"]
            if isinstance(acceptable, str):
                acceptable = acceptable.strip().lower() in {"true", "1", "yes"}
            if not bool(acceptable):
                continue
        scope = str(row[scope_col]).lower()
        if any(token in scope for token in ("test", "oos", "oracle")):
            raise ValueError(f"test-derived CLASSIX selection is forbidden: {scope}")
        rep = str(row["representation"])
        params: dict[str, Any] = {}
        parameter_column = next(
            (name for name in ("parameters", "params") if name in frame.columns),
            None,
        )
        if parameter_column is not None and pd.notna(row[parameter_column]):
            raw = row[parameter_column]
            params.update(json.loads(raw) if isinstance(raw, str) else dict(raw))
        for name in ("radius", "minPts", "group_merging", "mergeScale", "mergeTinyGroups", "post_alloc", "sorting", "metric"):
            if name in frame.columns and pd.notna(row[name]):
                params[name] = row[name]
        if "radius" not in params:
            raise ValueError(f"CLASSIX configuration for {rep} has no radius")
        out[rep] = params
    if not out:
        raise ValueError("no deployment-acceptable CLASSIX configurations found")
    return out


def run_from_files(project_root: str | Path, selected_config: str | Path, results_dir: str | Path) -> None:
    root = Path(project_root); out = Path(results_dir); out.mkdir(parents=True, exist_ok=True)
    compact = pd.read_csv(root / "data/derived/compact_features.csv")
    rich = pd.read_csv(root / "data/derived/rich_features.csv")
    if not compact["visitorid"].equals(rich["visitorid"]):
        raise ValueError("compact and rich rows must use the same purchaser cohort order")
    compact_names = ["purchase_recency_days", "purchase_occasion_count", "purchase_event_count"]
    rich_names = [c for c in rich.columns if c not in {"visitorid", "snapshot_id", "category_coverage_flag"}]
    supplementary_summary, supplementary_rules, supplementary_selection = run_exkmc_experiment(
        {"compact": compact[compact_names].to_numpy(), "rich": rich[rich_names].to_numpy()},
        split_seeds=EXKMC_SPLIT_SEEDS,
        feature_names={"compact": compact_names, "rich": rich_names},
        return_selection=True)
    selected_frame = pd.read_csv(selected_config)
    selected_kmeans = selected_frame[
        selected_frame["selection"].eq("deployment_acceptable")
        & selected_frame["method"].eq("kmeans")
    ]
    fixed_k = {
        str(row.representation): int(json.loads(row.parameters)["n_clusters"])
        for row in selected_kmeans.itertuples(index=False)
    }
    if set(fixed_k) != {"compact", "rich"}:
        raise ValueError("deployment K Means selections are required for both representations")
    summary, rules, k_selection = run_exkmc_experiment(
        {"compact": compact[compact_names].to_numpy(), "rich": rich[rich_names].to_numpy()},
        split_seeds=EXKMC_SPLIT_SEEDS,
        feature_names={"compact": compact_names, "rich": rich_names},
        return_selection=True,
        fixed_k=fixed_k,
    )
    if not summary.empty and set(summary["engine"]) != {"exkmc_0.0.3"}:
        raise RuntimeError("formal results require pinned ExKMC==0.0.3; compatibility tree is test-only")
    write_exkmc_results(summary, rules, out, k_selection)
    supplementary_summary.to_csv(
        out / "exkmc_train_selected_oos_fidelity.csv", index=False
    )
    supplementary_rules.to_csv(out / "exkmc_train_selected_rules.csv", index=False)
    supplementary_selection.to_csv(
        out / "exkmc_train_selected_k_selection.csv", index=False
    )

    configs = _read_classix_configs(Path(selected_config))
    selected_labels = pd.read_csv(root / "results/retailrocket/selected_labels.csv")
    selected_labels = selected_labels[
        selected_labels["selection"].eq("deployment_acceptable")
    ].copy()
    provenance = {}
    audits = []
    provenance_audits = []
    for rep, frame, names in (("compact", compact, compact_names), ("rich", rich, rich_names)):
        if rep not in configs:
            raise ValueError(f"selected configurations missing CLASSIX row for {rep}")
        payload = fit_classix_provenance(frame[names].to_numpy(), frame["visitorid"].tolist(),
                                         representation=rep, config=configs[rep],
                                         feature_names=tuple(names))
        provenance[rep] = payload
        expected = (
            selected_labels[
                selected_labels["representation"].eq(rep)
                & selected_labels["method"].eq("classix")
            ]
            .set_index("visitorid")
            .reindex(frame["visitorid"])["label"]
        )
        if expected.isna().any():
            raise ValueError(f"selected CLASSIX labels do not cover every {rep} customer")
        observed = np.asarray(payload["native_public_attributes"]["labels_"], dtype=int)
        expected_array = expected.to_numpy(dtype=int)
        exact = bool(np.array_equal(expected_array, observed))
        ari = float(adjusted_rand_score(expected_array, observed))
        provenance_audits.append({
            "representation": rep,
            "n_customers": int(len(observed)),
            "exact_label_match": exact,
            "partition_ari": ari,
            "selected_label_source": "results/retailrocket/selected_labels.csv",
        })
        if not exact or ari != 1.0:
            raise RuntimeError(f"CLASSIX provenance does not reproduce selected {rep} labels")
        audits.append(audit_addressability(frame, payload["native_public_attributes"]["labels_"],
                                           representation=rep, split_or_config="selected_classix",
                                           key_features=names))
        kmeans_expected = (
            selected_labels[
                selected_labels["representation"].eq(rep)
                & selected_labels["method"].eq("kmeans")
            ]
            .set_index("visitorid")
            .reindex(frame["visitorid"])["label"]
        )
        if kmeans_expected.isna().any():
            raise ValueError(f"selected K Means labels do not cover every {rep} customer")
        audits.append(
            audit_addressability(
                frame,
                kmeans_expected.to_numpy(dtype=int),
                representation=rep,
                split_or_config="selected_kmeans",
                key_features=names,
            )
        )
    write_classix_provenance(provenance, out / "classix_provenance.json")
    pd.DataFrame(provenance_audits).to_csv(
        out / "classix_provenance_selection_audit.csv", index=False
    )
    pd.concat(audits, ignore_index=True).to_csv(out / "addressability_audit.csv", index=False)
    write_addressability_metadata(out / "addressability_audit_metadata.json")
    metadata = {
        "schema_version": "1.0.0", "representations": {"compact": compact_names, "rich": rich_names},
        "split_seeds": list(EXKMC_SPLIT_SEEDS), "train_fraction": 0.8,
        "k_selection_source": "frozen_primary_k_with_split_local_training_fits", "test_rows_used_for_selection": 0,
        "exkmc_leaf_grid": "k..4k inclusive", "exkmc_reference": "KMeans fit on each training partition",
        "supplementary_k_selection": "split_local_training_rows_only",
        "python_hash_seed": 0,
        "numerical_library_threads": 1,
        "deterministic_process_environment": _DETERMINISTIC_PROCESS_ENV,
        "classix_provenance_note": "native public assignments are retained; merge relations are explicitly reconstructed where no documented edge API exists",
    }
    (out / "explanation_metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", default=".")
    parser.add_argument("--selected-config", required=True)
    parser.add_argument("--results-dir", default="results/retailrocket")
    args = parser.parse_args()
    run_from_files(args.project_root, args.selected_config, args.results_dir)


if __name__ == "__main__":
    main()
