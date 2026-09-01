"""Recorded, computable business-addressability audit."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


ADDRESSABILITY_RULE = {
    "min_cluster_share": 0.01,
    "min_non_noise_size": 50,
    "min_category_coverage": 0.80,
    "effect_threshold_iqr": 0.50,
    "max_distinguishable_conditions": 4,
    "min_distinguishable_conditions": 2,
    "noise_label": -1,
    "effect_definition": "abs(cluster median - global median) / global IQR; zero-IQR features do not count",
    "addressable_definition": "non-noise cluster passes size/share/coverage gates, has 2..4 named feature effects, and uses numeric cluster_id only",
}


def audit_addressability(
    frame: pd.DataFrame,
    labels: Iterable[int],
    *,
    representation: str,
    split_or_config: str,
    key_features: Iterable[str] | None = None,
    category_coverage_column: str = "category_coverage_flag",
) -> pd.DataFrame:
    """Audit clusters without subjective labels or test-dependent thresholds."""

    labels_arr = np.asarray(list(labels), dtype=int)
    if len(frame) != labels_arr.size:
        raise ValueError("frame and labels have different lengths")
    features = list(key_features) if key_features is not None else [
        c for c in frame.columns if c not in {"visitorid", "snapshot_id", category_coverage_column}
        and pd.api.types.is_numeric_dtype(frame[c])
    ]
    missing = sorted(set(features).difference(frame.columns))
    if missing:
        raise KeyError(f"unknown key features: {missing}")
    numeric = frame[features].apply(pd.to_numeric, errors="coerce")
    global_median = numeric.median(numeric_only=True)
    q25, q75 = numeric.quantile(0.25), numeric.quantile(0.75)
    iqr = q75 - q25
    out = []
    non_noise = labels_arr != ADDRESSABILITY_RULE["noise_label"]
    total = int(non_noise.sum())
    coverage = pd.to_numeric(frame.get(category_coverage_column, pd.Series(1, index=frame.index)), errors="coerce").fillna(0)
    for cluster in sorted(int(x) for x in np.unique(labels_arr) if x != ADDRESSABILITY_RULE["noise_label"]):
        mask = labels_arr == cluster
        size = int(mask.sum()); share = size / total if total else 0.0
        effects = {}
        for feature in features:
            denom = float(iqr[feature])
            effects[feature] = float(abs(numeric.loc[mask, feature].median() - global_median[feature]) / denom) if denom > 0 else 0.0
        distinguishable = sorted([f for f, effect in effects.items() if effect >= ADDRESSABILITY_RULE["effect_threshold_iqr"]])
        cluster_coverage = float(coverage.loc[mask].mean())
        size_gate = size >= ADDRESSABILITY_RULE["min_non_noise_size"]
        share_gate = share >= ADDRESSABILITY_RULE["min_cluster_share"]
        coverage_gate = cluster_coverage >= ADDRESSABILITY_RULE["min_category_coverage"]
        count = len(distinguishable)
        addressable = bool(size_gate and share_gate and coverage_gate and
                           ADDRESSABILITY_RULE["min_distinguishable_conditions"] <= count <= ADDRESSABILITY_RULE["max_distinguishable_conditions"])
        out.append({
            "representation": str(representation), "split_or_config": str(split_or_config),
            "cluster_id": cluster, "non_noise_cluster_size": size,
            "non_noise_cluster_share": share, "category_coverage_rate": cluster_coverage,
            "size_gate": size_gate, "share_gate": share_gate, "coverage_gate": coverage_gate,
            "distinguishable_condition_count": count,
            "distinguishable_features": json.dumps(distinguishable, separators=(",", ":")),
            "feature_effects_iqr": json.dumps(effects, sort_keys=True, separators=(",", ":")),
            "addressable": addressable,
            "rule_version": "addressability_v1",
        })
    return pd.DataFrame(out)


def write_addressability_metadata(output: str | Path) -> None:
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(ADDRESSABILITY_RULE, indent=2), encoding="utf-8")


__all__ = ["ADDRESSABILITY_RULE", "audit_addressability", "write_addressability_metadata"]
