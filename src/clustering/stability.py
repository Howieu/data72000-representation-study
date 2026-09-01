"""Fixed-parameter resampling stability for the selected configurations."""

from __future__ import annotations

import json
from typing import Any

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from .engine import RepresentationData, _classix_fit
from .metrics import paired_partition_metrics
from .schema import validate_schema


def _fit_subset(data: RepresentationData, method: str, params: dict[str, Any], indices: np.ndarray,
                seed: int) -> np.ndarray:
    # The scaler is fitted independently inside each resample, as required by
    # the frozen protocol.  Transform rules are inferred from the table's
    # already transformed/raw pair by checking whether values differ.
    transformed = data.transformed[indices]
    scaler = StandardScaler().fit(transformed)
    X = scaler.transform(transformed)
    if method == "kmeans":
        return KMeans(n_clusters=int(params["n_clusters"]), init="k-means++", n_init=20,
                      random_state=seed).fit_predict(X).astype(int)
    labels, _ = _classix_fit(X, params)
    return labels


def resampling_stability(
    representations: dict[str, RepresentationData], selected: pd.DataFrame,
    protocol: dict[str, Any],
) -> pd.DataFrame:
    """Compute ten deterministic 80% without-replacement overlap ARIs."""
    fraction = float(protocol["resampling_fraction"])
    pairs = int(protocol["resampling_pairs"])
    primary = int(protocol["primary_seed"])
    records = []
    for _, config in selected.iterrows():
        if str(config["selection"]) == "deployment_acceptable" and not bool(config["deployment_acceptable"]):
            # Keep the selected configuration failure visible, but do not
            # compute a stability statistic for a non-deployable fallback.
            continue
        data = representations[str(config["representation"])]
        params = json.loads(str(config["parameters"]))
        for pair_id in range(pairs):
            seed_left, seed_right = primary + 2 * pair_id, primary + 2 * pair_id + 1
            n_draw = int(np.floor(fraction * len(data.visitorid)))
            idx_left = np.random.default_rng(seed_left).choice(len(data.visitorid), n_draw, replace=False)
            idx_right = np.random.default_rng(seed_right).choice(len(data.visitorid), n_draw, replace=False)
            left_ids, right_ids = data.visitorid[idx_left], data.visitorid[idx_right]
            left_labels = _fit_subset(data, str(config["method"]), params, idx_left, seed_left)
            right_labels = _fit_subset(data, str(config["method"]), params, idx_right, seed_right)
            left_pos = {int(visitor): i for i, visitor in enumerate(left_ids)}
            right_pos = {int(visitor): i for i, visitor in enumerate(right_ids)}
            common = sorted(set(left_pos).intersection(right_pos))
            valid = len(common) >= 100
            ari = None
            if valid:
                ari = paired_partition_metrics(
                    np.asarray([left_labels[left_pos[v]] for v in common]),
                    np.asarray([right_labels[right_pos[v]] for v in common]),
                )["ari"]
            records.append({
                "representation": config["representation"], "method": config["method"],
                "selection": config["selection"], "candidate_id": config["candidate_id"],
                "pair_id": pair_id + 1, "seed_left": seed_left, "seed_right": seed_right,
                "sample_fraction": fraction, "n_left": len(idx_left), "n_right": len(idx_right),
                "n_overlap": len(common), "valid_overlap": valid, "ari_overlap": ari,
            })
    frame = pd.DataFrame(records)
    validate_schema(frame, "resampling_stability.csv")
    return frame
