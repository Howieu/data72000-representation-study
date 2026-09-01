"""Raw-event reconstruction for session-window sensitivity."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from typing import Any

import numpy as np
import pandas as pd

from .core import FitPredict, _fit_predict, _numeric_matrix, evaluate_labels


def reconstruct_session_counts(
    events: pd.DataFrame,
    windows_minutes: Sequence[int] = (15, 30, 60),
    *,
    visitor_column: str = "visitorid",
    timestamp_column: str = "timestamp",
) -> pd.DataFrame:
    """Rebuild per-visitor session counts from the original event rows.

    Timestamps may be UTC-aware datetimes, naive datetimes (interpreted as
    UTC), or Unix milliseconds.  A new session starts only when an adjacent
    within-visitor gap is strictly greater than the requested window.
    """
    if visitor_column not in events or timestamp_column not in events:
        raise ValueError("events must contain visitor and timestamp columns")
    windows = [int(window) for window in windows_minutes]
    if not windows or any(window <= 0 for window in windows):
        raise ValueError("windows_minutes must contain positive values")
    frame = events[[visitor_column, timestamp_column]].copy()
    raw = frame[timestamp_column]
    if pd.api.types.is_numeric_dtype(raw):
        frame["_timestamp"] = pd.to_datetime(raw, unit="ms", utc=True)
    else:
        frame["_timestamp"] = pd.to_datetime(raw, utc=True)
    frame["_row_order"] = np.arange(len(frame), dtype=np.int64)
    frame = frame.sort_values([visitor_column, "_timestamp", "_row_order"], kind="mergesort")
    gaps_minutes = frame.groupby(visitor_column, sort=False)["_timestamp"].diff().dt.total_seconds().div(60.0)
    result = pd.DataFrame({visitor_column: frame[visitor_column].drop_duplicates().sort_values().to_numpy()})
    for window in windows:
        # ``Series.gt`` turns NaN into False before ``fillna``; explicitly
        # mark each visitor's first event as a session start.
        starts = gaps_minutes.isna() | gaps_minutes.gt(window)
        counts = starts.groupby(frame[visitor_column], sort=False).sum().astype("int64")
        result = result.merge(counts.rename(f"session_count_{window}m"), on=visitor_column, how="left", validate="one_to_one")
    return result.sort_values(visitor_column).reset_index(drop=True)


def replace_session_feature(
    rich: pd.DataFrame,
    session_counts: pd.DataFrame,
    window_minutes: int,
    *,
    visitor_column: str = "visitorid",
    canonical_column: str = "session_count_30m",
) -> tuple[pd.DataFrame, str]:
    """Return rich features with only the canonical session dimension replaced."""
    source_column = f"session_count_{int(window_minutes)}m"
    if visitor_column not in rich or visitor_column not in session_counts or source_column not in session_counts:
        raise ValueError("rich and session_counts lack required columns")
    out = rich.copy()
    if canonical_column not in out:
        raise ValueError(f"rich table lacks {canonical_column}")
    replacement = session_counts[[visitor_column, source_column]].rename(columns={source_column: canonical_column})
    out = out.drop(columns=[canonical_column]).merge(replacement, on=visitor_column, how="left", validate="one_to_one")
    if out[canonical_column].isna().any():
        raise ValueError("session reconstruction did not cover every rich visitor")
    return out.sort_values(visitor_column).reset_index(drop=True), f"{canonical_column} <- {source_column} reconstructed from raw events"


def session_window_sensitivity(
    rich: pd.DataFrame,
    events: pd.DataFrame,
    feature_names: Sequence[str],
    fit_predict: FitPredict,
    *,
    windows_minutes: Sequence[int] = (15, 30, 60),
    baseline_labels: Iterable[int] | None = None,
    algorithm: str | None = None,
    visitor_column: str = "visitorid",
) -> pd.DataFrame:
    """Evaluate selected clustering with sessions reconstructed per window."""
    sessions = reconstruct_session_counts(events, windows_minutes, visitor_column=visitor_column)
    baseline = None if baseline_labels is None else np.asarray(list(baseline_labels), dtype=int)
    rows: list[dict[str, Any]] = []
    for window in windows_minutes:
        altered, affected = replace_session_feature(rich, sessions, int(window), visitor_column=visitor_column)
        matrix = _numeric_matrix(altered[list(feature_names)])
        labels = _fit_predict(fit_predict, matrix)
        row: dict[str, Any] = {
            "window_minutes": int(window),
            "affected_dimension": affected,
            "n_features": int(matrix.shape[1]),
            **evaluate_labels(matrix, labels, baseline),
        }
        if algorithm is not None:
            row["algorithm"] = algorithm
        rows.append(row)
    return pd.DataFrame(rows)
