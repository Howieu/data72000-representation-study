"""Auditable CLASSIX provenance for the selected configuration."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

from .exkmc_experiment import schema_transform
from ..provenance_alignment import align_groups

try:
    from classix import CLASSIX
except Exception:  # pragma: no cover
    CLASSIX = None


def _jsonable(value: Any) -> Any:
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _as_bool(value: Any) -> bool:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"false", "0", "no", "off"}:
            return False
        if lowered in {"true", "1", "yes", "on"}:
            return True
    return bool(value)


def fit_classix_provenance(
    X: np.ndarray,
    customer_ids: list[Any] | np.ndarray,
    *,
    representation: str,
    config: Mapping[str, Any],
    feature_names: list[str] | tuple[str, ...] | None = None,
    schema_path: str | Path | None = None,
) -> dict[str, Any]:
    """Fit selected CLASSIX and export native arrays plus explicit reconstruction.

    CLASSIX exposes aggregation groups, group representatives and final labels,
    but not a documented complete merge-edge list.  ``merge_relations`` below
    is therefore marked reconstructed from these public assignments rather
    than presented as an undocumented native graph.
    """

    if CLASSIX is None:
        raise RuntimeError("classix 1.5.1 is required for native provenance export")
    values = np.asarray(X, dtype=float)
    ids = np.asarray(customer_ids)
    if values.ndim != 2 or values.shape[0] != ids.size or values.shape[0] < 1:
        raise ValueError("X and customer_ids have incompatible shapes")
    if not np.isfinite(values).all():
        raise ValueError("X must be finite")
    if feature_names is None:
        transformed = values
        transformed_columns: tuple[str, ...] = tuple()
    else:
        transformed, transformed_columns = schema_transform(
            values, feature_names, schema_path=schema_path
        )
    scaler = StandardScaler().fit(transformed)
    scaled = scaler.transform(transformed).astype(float, copy=False)
    params = {
        "sorting": str(config.get("sorting", "pca")),
        "metric": str(config.get("metric", "euclidean")),
        "radius": float(config["radius"]),
        "minPts": int(config.get("minPts", config.get("min_pts", 1))),
        "group_merging": str(config.get("group_merging", "distance")),
        "mergeScale": float(config.get("mergeScale", 1.5)),
        "mergeTinyGroups": _as_bool(config.get("mergeTinyGroups", True)),
        "post_alloc": _as_bool(config.get("post_alloc", False)),
        "verbose": 0,
    }
    if params["post_alloc"]:
        raise ValueError("post_alloc must be false for the frozen CLASSIX configuration")
    model = CLASSIX(**params).fit(scaled)
    groups_native = np.asarray(model.groups_, dtype=int)
    labels = np.asarray(model.labels_, dtype=int)
    reps = np.asarray(model.groupCenters_, dtype=int)
    groups = np.asarray(align_groups(groups_native.tolist(), np.asarray(model.inverse_ind, dtype=int).tolist(), reps.tolist(), labels.tolist()), dtype=int)
    if groups.size != values.shape[0] or labels.size != values.shape[0]:
        raise ValueError("CLASSIX returned invalid assignment lengths")
    group_ids = sorted(int(x) for x in np.unique(groups))
    cluster_sizes = {int(c): int(np.sum(labels == c)) for c in np.unique(labels)}
    groups_out = []
    for gid in group_ids:
        members = np.flatnonzero(groups == gid).astype(int)
        rep = int(reps[gid]) if 0 <= gid < reps.size else int(members[0])
        groups_out.append({
            "aggregation_group": gid,
            "representative_row_index": rep,
            "representative_customer_id": _jsonable(ids[rep]),
            "member_row_indices": members.tolist(),
            "member_customer_ids": _jsonable(ids[members]),
            "group_size": int(members.size),
            "final_cluster": int(labels[members[0]]) if members.size else -1,
            "final_cluster_size": cluster_sizes.get(int(labels[members[0]]), 0) if members.size else 0,
        })
    merge_relations = []
    for cluster, size in sorted(cluster_sizes.items()):
        gids = sorted(int(x) for x in np.unique(groups[labels == cluster]))
        merge_relations.append({"final_cluster": cluster, "aggregation_groups": gids,
                                "cluster_size": size,
                                "relation_status": "reconstructed_from_public_assignments"})
    customer_trace = [{
        "row_index": int(i), "customer_id": _jsonable(ids[i]),
        "aggregation_group": int(groups[i]), "representative_row_index": int(reps[groups[i]]) if 0 <= groups[i] < reps.size else None,
        "final_cluster": int(labels[i]), "final_cluster_size": cluster_sizes[int(labels[i])],
    } for i in range(values.shape[0])]
    native = {
        "groups_": groups_native.tolist(), "labels_": labels.tolist(),
        "groupCenters_": reps.tolist(), "splist_": _jsonable(getattr(model, "splist_", None)),
        "ind": _jsonable(getattr(model, "ind", None)),
        "inverse_ind": _jsonable(getattr(model, "inverse_ind", None)),
        "clusterSizes_": _jsonable(getattr(model, "clusterSizes_", None)),
    }
    return {
        "schema_version": "1.0.1",
        "representation": str(representation),
        "n_samples": int(values.shape[0]), "n_features": int(values.shape[1]),
        "engine": "classix_1.5.1",
        "config": params,
        "scaler": {"fit_scope": "all_rows_for_selected_full_data_CLASSIX",
                   "mean": scaler.mean_.tolist(), "scale": scaler.scale_.tolist(),
                   "schema_transformed_columns": list(transformed_columns)},
        "native_public_attributes": native,
        "groups": groups_out,
        "merge_relations": merge_relations,
        "customer_trace": customer_trace,
        "provenance_limits": {
            "native_assignments": ["groups_", "labels_", "groupCenters_", "splist_", "ind", "inverse_ind", "clusterSizes_"],
            "reconstructed": ["merge_relations", "final_cluster_size", "customer_trace"],
            "group_row_order": "native groups_ uses sorted rows; exported groups and customer_trace use inverse_ind to restore input order",
            "note": "CLASSIX 1.5.1 does not expose a documented complete merge-edge graph; relations are reconstructed from public group/final assignments.",
        },
    }


def write_classix_provenance(payloads: Mapping[str, Mapping[str, Any]], output: str | Path) -> None:
    path = Path(output); path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_jsonable(dict(payloads)), indent=2, ensure_ascii=False), encoding="utf-8")


__all__ = ["fit_classix_provenance", "write_classix_provenance"]
