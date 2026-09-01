"""Deterministic construction of the nested RetailRocket representations.

The implementation deliberately has a small, explicit interface. Raw event
rows are normalised, category history is joined as-of the event timestamp and
all twelve named features are derived from the same purchaser cohort.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable, Mapping, Sequence

import numpy as np
import pandas as pd

COMPACT_FEATURES = (
    "purchase_recency_days",
    "purchase_occasion_count",
    "purchase_event_count",
)
RICH_FEATURES = COMPACT_FEATURES + (
    "total_events",
    "active_days",
    "cart_per_view",
    "transaction_per_view",
    "activity_span_days",
    "mean_interevent_hours",
    "session_count_30m",
    "distinct_top_categories",
    "top_category_share",
)
EVENT_COLUMNS = ("timestamp", "visitorid", "event", "itemid", "transactionid")
CATEGORY_COLUMNS = ("timestamp", "itemid", "property", "value")

FEATURE_SCHEMA = [
    {
        "feature": "purchase_recency_days",
        "block": "compact_transaction",
        "formula": "(snapshot_utc - latest transaction timestamp) / 86400 seconds",
        "input_events": "transaction",
        "observation_window": "full event snapshot",
        "unit": "days",
        "missing_strategy": "cohort guarantees one transaction",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "snapshot 2020-01-03, transaction 2020-01-01 12:00 -> 1.5",
    },
    {
        "feature": "purchase_occasion_count",
        "block": "compact_transaction",
        "formula": "number of distinct non-empty transactionid values",
        "input_events": "transaction",
        "observation_window": "full event snapshot",
        "unit": "occasions",
        "missing_strategy": "empty transactionid excluded",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "transactionid A,A,B -> 2",
    },
    {
        "feature": "purchase_event_count",
        "block": "compact_transaction",
        "formula": "count of transaction event rows",
        "input_events": "transaction",
        "observation_window": "full event snapshot",
        "unit": "events",
        "missing_strategy": "none",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "three transaction rows -> 3",
    },
    {
        "feature": "total_events",
        "block": "activity",
        "formula": "count of all event rows",
        "input_events": "all events",
        "observation_window": "full event snapshot",
        "unit": "events",
        "missing_strategy": "none",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "view, addtocart, transaction -> 3",
    },
    {
        "feature": "active_days",
        "block": "activity",
        "formula": "number of distinct UTC calendar days containing an event",
        "input_events": "all events",
        "observation_window": "full event snapshot",
        "unit": "days",
        "missing_strategy": "none",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "events on two UTC dates -> 2",
    },
    {
        "feature": "cart_per_view",
        "block": "conversion",
        "formula": "addtocart event count / view event count",
        "input_events": "addtocart and view",
        "observation_window": "full event snapshot",
        "unit": "ratio",
        "missing_strategy": "none",
        "zero_denominator_strategy": "0 when view count is 0; audited",
        "transform": "none",
        "example": "2 addtocart / 4 view -> 0.5",
    },
    {
        "feature": "transaction_per_view",
        "block": "conversion",
        "formula": "transaction event count / view event count",
        "input_events": "transaction and view",
        "observation_window": "full event snapshot",
        "unit": "ratio",
        "missing_strategy": "none",
        "zero_denominator_strategy": "0 when view count is 0; audited",
        "transform": "none",
        "example": "1 transaction / 4 view -> 0.25",
    },
    {
        "feature": "activity_span_days",
        "block": "temporal_engagement",
        "formula": "(latest event timestamp - earliest event timestamp) / 86400 seconds",
        "input_events": "all events",
        "observation_window": "full event snapshot",
        "unit": "days",
        "missing_strategy": "single event gives 0",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "events 36 hours apart -> 1.5",
    },
    {
        "feature": "mean_interevent_hours",
        "block": "temporal_engagement",
        "formula": "mean adjacent event gap after stable visitor-time-row sorting",
        "input_events": "all events",
        "observation_window": "full event snapshot",
        "unit": "hours",
        "missing_strategy": "single event gives 0",
        "zero_denominator_strategy": "0 when no adjacent pair; audited by schema",
        "transform": "log1p",
        "example": "gaps of 1 and 3 hours -> 2",
    },
    {
        "feature": "session_count_30m",
        "block": "temporal_engagement",
        "formula": "1 + count of adjacent gaps strictly greater than 30 minutes",
        "input_events": "all events",
        "observation_window": "full event snapshot",
        "unit": "sessions",
        "missing_strategy": "cohort has at least one event",
        "zero_denominator_strategy": "not applicable",
        "transform": "log1p",
        "example": "gaps 10 and 31 minutes -> 2",
    },
    {
        "feature": "distinct_top_categories",
        "block": "category_behaviour",
        "formula": "number of distinct top categories among known as-of joins",
        "input_events": "events with category property",
        "observation_window": "category known at or before event",
        "unit": "categories",
        "missing_strategy": "unknown joins excluded; flag retained",
        "zero_denominator_strategy": "0 when no known category events; audited",
        "transform": "log1p",
        "example": "known top categories 10,10,20 -> 2",
    },
    {
        "feature": "top_category_share",
        "block": "category_behaviour",
        "formula": "largest top-category event count / known top-category event count",
        "input_events": "events with category property",
        "observation_window": "category known at or before event",
        "unit": "share",
        "missing_strategy": "unknown joins excluded; flag retained",
        "zero_denominator_strategy": "0 when no known category events; audited",
        "transform": "none",
        "example": "category counts 3 and 1 -> 0.75",
    },
]


def _as_datetime(values: pd.Series) -> pd.Series:
    """Convert millisecond Unix values or datetimes to UTC timestamps."""
    if pd.api.types.is_datetime64_any_dtype(values):
        return pd.to_datetime(values, utc=True)
    return pd.to_datetime(values, unit="ms", utc=True)


def load_events(path: str | Path) -> pd.DataFrame:
    """Read and stably order the event table, adding a zero-based raw row id."""
    frame = pd.read_csv(
        path,
        usecols=list(EVENT_COLUMNS),
        dtype={
            "timestamp": "int64",
            "visitorid": "int64",
            "event": "string",
            "itemid": "int64",
            "transactionid": "string",
        },
        keep_default_na=True,
        na_values=[""],
    )
    frame["raw_row_id"] = np.arange(len(frame), dtype=np.int64)
    frame["_ts"] = _as_datetime(frame["timestamp"])
    return frame.sort_values(
        ["visitorid", "_ts", "raw_row_id"], kind="mergesort"
    ).reset_index(drop=True)


def load_category_history(
    paths: Iterable[str | Path], chunksize: int = 500_000
) -> pd.DataFrame:
    """Read only categoryid properties while retaining a deterministic row id."""
    frames: list[pd.DataFrame] = []
    offset = 0
    for path in paths:
        file_offset = 0
        for chunk in pd.read_csv(
            path,
            usecols=list(CATEGORY_COLUMNS),
            dtype={
                "timestamp": "int64",
                "itemid": "int64",
                "property": "string",
                "value": "string",
            },
            chunksize=chunksize,
            keep_default_na=True,
            na_values=[""],
        ):
            n = len(chunk)
            selected = chunk.loc[chunk["property"].eq("categoryid")].copy()
            if not selected.empty:
                selected["categoryid"] = pd.to_numeric(
                    selected["value"], errors="coerce"
                )
                selected = selected.dropna(subset=["categoryid"])
                selected["categoryid"] = selected["categoryid"].astype("int64")
                # Chunk indexes restart at zero for each source file.  Preserve
                # source-file order and original row order for equal timestamps.
                selected["raw_row_id"] = (
                    selected.index.to_numpy(dtype=np.int64)
                    - int(chunk.index.min())
                    + file_offset
                    + offset
                )
                frames.append(selected[["timestamp", "itemid", "categoryid", "raw_row_id"]])
            file_offset += n
        offset += file_offset
    if not frames:
        return pd.DataFrame(columns=["timestamp", "itemid", "categoryid", "raw_row_id"])
    history = pd.concat(frames, ignore_index=True)
    return history.sort_values(
        ["timestamp", "itemid", "raw_row_id"], kind="mergesort"
    ).reset_index(drop=True)


def top_category_map(tree: pd.DataFrame | str | Path) -> tuple[dict[int, int], int]:
    """Resolve every category tree node to its root, returning cycle count."""
    raw = (
        tree.copy()
        if isinstance(tree, pd.DataFrame)
        else pd.read_csv(tree, dtype={"categoryid": "Int64", "parentid": "Int64"})
    )
    parents = {
        int(row.categoryid): (None if pd.isna(row.parentid) else int(row.parentid))
        for row in raw.itertuples(index=False)
        if not pd.isna(row.categoryid)
    }
    resolved: dict[int, int] = {}
    cycles = 0
    for category in parents:
        current = category
        seen: set[int] = set()
        while current in parents and parents[current] is not None:
            if current in seen:
                cycles += 1
                current = min(seen)
                break
            seen.add(current)
            current = int(parents[current])
        resolved[category] = int(current)
    return resolved, cycles


def attach_categories_asof(
    events: pd.DataFrame,
    history: pd.DataFrame,
    tree: Mapping[int, int] | pd.DataFrame | str | Path,
) -> tuple[pd.DataFrame, dict[str, float | int]]:
    """Attach latest category known at event time, never using a future row."""
    frame = events.copy()
    if "_ts" not in frame:
        frame["_ts"] = _as_datetime(frame["timestamp"])
    if isinstance(tree, (str, Path)):
        top_map, cycle_count = top_category_map(pd.read_csv(tree))
    elif isinstance(tree, pd.DataFrame):
        top_map, cycle_count = top_category_map(tree)
    else:
        top_map, cycle_count = dict(tree), 0
    if history.empty:
        frame["categoryid"] = pd.Series(pd.array([pd.NA] * len(frame), dtype="Int64"))
    else:
        left = frame[["itemid", "timestamp", "raw_row_id"]].copy()
        left["_event_pos"] = np.arange(len(left), dtype=np.int64)
        right = history[["itemid", "timestamp", "categoryid", "raw_row_id"]].copy()
        # merge_asof requires the on-key to be globally sorted in pandas 2.x.
        left = left.sort_values(["timestamp", "itemid", "raw_row_id"], kind="mergesort")
        right = right.sort_values(["timestamp", "itemid", "raw_row_id"], kind="mergesort")
        joined = pd.merge_asof(
            left,
            right,
            on="timestamp",
            by="itemid",
            direction="backward",
            allow_exact_matches=True,
            suffixes=("", "_property"),
        )
        categories = joined.set_index("_event_pos")["categoryid"].reindex(
            np.arange(len(frame))
        )
        frame["categoryid"] = pd.array(categories, dtype="Int64")
    frame["top_categoryid"] = frame["categoryid"].map(top_map).astype("Int64")
    known = frame["top_categoryid"].notna()
    audit = {
        "event_rows": int(len(frame)),
        "known_category_event_rows": int(known.sum()),
        "event_category_coverage": float(known.mean()) if len(frame) else 0.0,
        "unknown_category_event_rows": int((~known).sum()),
        "category_tree_cycles": int(cycle_count),
        "category_tree_nodes": int(len(top_map)),
    }
    return frame, audit


def _cohort(events: pd.DataFrame) -> np.ndarray:
    transaction = events.loc[events["event"].eq("transaction")]
    return np.sort(transaction["visitorid"].dropna().unique())


def _empty_feature_frame(visitorids: np.ndarray, snapshot_id: str) -> pd.DataFrame:
    out = pd.DataFrame({"visitorid": visitorids.astype(np.int64)})
    out["snapshot_id"] = snapshot_id
    for feature in RICH_FEATURES:
        out[feature] = 0.0
    out["category_coverage_flag"] = 0
    return out


def build_feature_tables(
    events: pd.DataFrame,
    snapshot: pd.Timestamp | None = None,
    snapshot_id: str | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    """Build compact, nested rich, and per-visitor category audit tables."""
    df = events.copy()
    if "_ts" not in df:
        df["_ts"] = _as_datetime(df["timestamp"])
    df = df.sort_values(["visitorid", "_ts", "raw_row_id"], kind="mergesort").reset_index(drop=True)
    if snapshot is None:
        snapshot = df["_ts"].max() + pd.Timedelta(days=1)
    snapshot = pd.Timestamp(snapshot).tz_convert("UTC") if pd.Timestamp(snapshot).tzinfo else pd.Timestamp(snapshot, tz="UTC")
    if snapshot_id is None:
        snapshot_id = "snapshot_" + snapshot.strftime("%Y%m%dT%H%M%SZ")
    visitors = _cohort(df)
    if not len(visitors):
        raise ValueError("cohort is empty: at least one transaction is required")
    df = df.loc[df["visitorid"].isin(visitors)].copy()
    tx = df.loc[df["event"].eq("transaction")].copy()
    tx_nonempty = tx.loc[tx["transactionid"].notna()]
    visitor_index = pd.Index(visitors, name="visitorid")

    last_purchase = tx.groupby("visitorid")["_ts"].max().reindex(visitor_index)
    occasion = tx_nonempty.groupby("visitorid")["transactionid"].nunique().reindex(visitor_index, fill_value=0)
    purchase_rows = tx.groupby("visitorid").size().reindex(visitor_index, fill_value=0)
    total = df.groupby("visitorid").size().reindex(visitor_index, fill_value=0)
    active = df.assign(_day=df["_ts"].dt.floor("D")).groupby("visitorid")["_day"].nunique().reindex(visitor_index, fill_value=0)
    view = df["event"].eq("view").groupby(df["visitorid"]).sum().reindex(visitor_index, fill_value=0)
    cart = df["event"].eq("addtocart").groupby(df["visitorid"]).sum().reindex(visitor_index, fill_value=0)
    span = (df.groupby("visitorid")["_ts"].max() - df.groupby("visitorid")["_ts"].min()).dt.total_seconds().div(86400).reindex(visitor_index, fill_value=0)
    ordered = df.sort_values(["visitorid", "_ts", "raw_row_id"], kind="mergesort")
    delta = ordered.groupby("visitorid")["_ts"].diff().dt.total_seconds()
    mean_gap = (delta.div(3600).groupby(ordered["visitorid"]).mean().reindex(visitor_index, fill_value=0).fillna(0))
    sessions = (1 + delta.gt(1800).groupby(ordered["visitorid"]).sum()).reindex(visitor_index, fill_value=1)

    if "top_categoryid" in df:
        known = df["top_categoryid"].notna()
        known_counts = known.groupby(df["visitorid"]).sum().reindex(visitor_index, fill_value=0)
        distinct = df.loc[known].groupby("visitorid")["top_categoryid"].nunique().reindex(visitor_index, fill_value=0)
        counts = (
            df.loc[known].groupby(["visitorid", "top_categoryid"]).size()
            .groupby(level=0).max().reindex(visitor_index, fill_value=0)
        )
    else:
        known_counts = pd.Series(0, index=visitor_index, dtype="int64")
        distinct = known_counts.copy()
        counts = known_counts.copy()
    top_share = counts.div(known_counts.replace(0, np.nan)).fillna(0.0)
    coverage_flag = known_counts.gt(0).astype("int8")

    values = pd.DataFrame(index=visitor_index)
    values["purchase_recency_days"] = (snapshot - last_purchase).dt.total_seconds().div(86400)
    values["purchase_occasion_count"] = occasion.astype("int64")
    values["purchase_event_count"] = purchase_rows.astype("int64")
    values["total_events"] = total.astype("int64")
    values["active_days"] = active.astype("int64")
    values["cart_per_view"] = cart.div(view.replace(0, np.nan)).fillna(0.0)
    values["transaction_per_view"] = purchase_rows.div(view.replace(0, np.nan)).fillna(0.0)
    values["activity_span_days"] = span.astype(float)
    values["mean_interevent_hours"] = mean_gap.astype(float)
    values["session_count_30m"] = sessions.astype("int64")
    values["distinct_top_categories"] = distinct.astype("int64")
    values["top_category_share"] = top_share.astype(float)
    values = values.reset_index()
    values["snapshot_id"] = snapshot_id
    values["category_coverage_flag"] = coverage_flag.to_numpy(dtype=np.int8)
    values = values[["visitorid", *RICH_FEATURES, "snapshot_id", "category_coverage_flag"]]
    compact = values[["visitorid", *COMPACT_FEATURES, "snapshot_id"]].copy()
    audit = pd.DataFrame(
        {
            "visitorid": visitors,
            "event_rows": total.to_numpy(dtype=np.int64),
            "known_category_event_rows": known_counts.to_numpy(dtype=np.int64),
            "unknown_category_event_rows": (total - known_counts).to_numpy(dtype=np.int64),
            "category_coverage": known_counts.div(total.replace(0, np.nan)).fillna(0.0).to_numpy(),
            "category_coverage_flag": coverage_flag.to_numpy(dtype=np.int8),
            "zero_view_denominator": view.eq(0).to_numpy(dtype=np.int8),
            "zero_known_category_denominator": known_counts.eq(0).to_numpy(dtype=np.int8),
            "view_event_rows": view.to_numpy(dtype=np.int64),
            "snapshot_id": snapshot_id,
        }
    )
    metadata = {
        "cohort_size": int(len(visitors)),
        "event_rows_in_cohort": int(len(df)),
        "full_event_max_timestamp_utc": _as_datetime(events["timestamp"] if "_ts" not in events else events["_ts"]).max().isoformat(),
        "snapshot_timestamp_utc": snapshot.isoformat(),
        "snapshot_id": snapshot_id,
        "zero_view_denominator_visitors": int(view.eq(0).sum()),
        "zero_known_category_denominator_visitors": int(known_counts.eq(0).sum()),
    }
    if not np.isfinite(values[list(RICH_FEATURES)].to_numpy(float)).all():
        raise ValueError("feature table contains non-finite values")
    return compact, values, audit, metadata


def _file_info(path: Path, project_root: Path) -> dict[str, object]:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(4 * 1024 * 1024), b""):
            digest.update(chunk)
    with path.open("rb") as handle:
        rows = max(sum(1 for _ in handle) - 1, 0)
    return {
        "file": path.name,
        "relative_path": str(path.relative_to(project_root)),
        "bytes": path.stat().st_size,
        "rows": rows,
        "sha256": digest.hexdigest(),
    }


def write_input_manifests(project_root: str | Path) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Write byte hashes and raw column schema manifests."""
    root = Path(project_root)
    raw = root / "data" / "raw" / "retailrocket"
    files = [raw / n for n in ("events.csv", "item_properties_part1.csv", "item_properties_part2.csv", "category_tree.csv")]
    infos = [_file_info(p, root) for p in files]
    hashes = pd.DataFrame(infos)
    schema_rows: list[dict[str, object]] = []
    for path, info in zip(files, infos):
        header = pd.read_csv(path, nrows=0).columns.tolist()
        sample = pd.read_csv(path, nrows=100)
        for col in header:
            schema_rows.append(
                {
                    "file": path.name,
                    "column_order": int(header.index(col)),
                    "column": col,
                    "inferred_dtype": str(sample[col].dtype),
                    "nullable": bool(sample[col].isna().any()),
                    "row_count": int(info["rows"]),
                }
            )
    schema = pd.DataFrame(schema_rows)
    out = root / "data" / "manifests"
    out.mkdir(parents=True, exist_ok=True)
    hashes.to_csv(out / "input_hashes.csv", index=False)
    schema.to_csv(out / "input_schema.csv", index=False)
    return hashes, schema


def write_feature_schema(path: str | Path) -> pd.DataFrame:
    schema = pd.DataFrame(FEATURE_SCHEMA)
    schema.to_csv(path, index=False)
    return schema


def generate_artifacts(project_root: str | Path | None = None) -> dict[str, object]:
    """Generate all data and audit artefacts for the frozen raw snapshot."""
    root = Path(project_root) if project_root is not None else Path(__file__).resolve().parents[2]
    raw = root / "data" / "raw" / "retailrocket"
    derived = root / "data" / "derived"
    derived.mkdir(parents=True, exist_ok=True)
    hashes, schema = write_input_manifests(root)
    write_feature_schema(derived / "feature_schema.csv")
    events = load_events(raw / "events.csv")
    history = load_category_history([raw / "item_properties_part1.csv", raw / "item_properties_part2.csv"])
    enriched, join_audit = attach_categories_asof(events, history, raw / "category_tree.csv")
    snapshot = enriched["_ts"].max() + pd.Timedelta(days=1)
    compact, rich, audit, metadata = build_feature_tables(enriched, snapshot=snapshot)
    compact.to_csv(derived / "compact_features.csv", index=False)
    rich.to_csv(derived / "rich_features.csv", index=False)
    audit.to_csv(derived / "category_coverage_audit.csv", index=False)
    purchaser_events = events.loc[
        events["visitorid"].isin(rich["visitorid"]),
        ["visitorid", "timestamp", "raw_row_id"],
    ].sort_values(["visitorid", "timestamp", "raw_row_id"], kind="mergesort")
    purchaser_events[["visitorid", "timestamp"]].to_csv(
        derived / "purchaser_event_timestamps.csv", index=False
    )
    metadata["purchaser_event_rows"] = int(len(purchaser_events))
    metadata.update({"input_hashes": hashes.to_dict(orient="records"), "input_schema_columns": int(len(schema)), "category_join": join_audit})
    (derived / "feature_generation_metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True), encoding="utf-8"
    )
    return metadata


if __name__ == "__main__":
    result = generate_artifacts()
    print(json.dumps(result, indent=2, sort_keys=True))
