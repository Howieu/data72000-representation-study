"""Frozen, local loaders for the nine public benchmark datasets.

The raw files are vendored snapshots under ``data/raw/benchmarks``.  Loading
is deliberately strict: a changed file is reported before it can enter a run.
Reference labels are carried for external evaluation only; no loader function
uses them to choose a clustering configuration.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_ROOT = PROJECT_ROOT / "data" / "raw" / "benchmarks"
MANIFEST_PATH = DATA_ROOT / "manifest.json"


@dataclass(frozen=True)
class Dataset:
    """A complete feature matrix and held-out reference labels."""

    name: str
    kind: str
    X: np.ndarray
    y: np.ndarray
    source: str
    license: str
    sha256: str
    path: Path

    @property
    def n_samples(self) -> int:
        return int(self.X.shape[0])

    @property
    def n_features(self) -> int:
        return int(self.X.shape[1])

    @property
    def n_classes(self) -> int:
        return int(np.unique(self.y).size)


with MANIFEST_PATH.open(encoding="utf-8") as _manifest_file:
    MANIFEST = json.load(_manifest_file)


def _verify(path: Path, expected: str) -> None:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected:
        raise ValueError(f"frozen benchmark file changed: {path.name} ({actual} != {expected})")


def _finish(name: str, kind: str, X: np.ndarray, y: np.ndarray) -> Dataset:
    spec = MANIFEST["datasets"][name]
    path = DATA_ROOT / spec["file"]
    _verify(path, spec["sha256"])
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=int)
    if X.ndim != 2 or y.ndim != 1 or len(X) != len(y) or len(X) < 3:
        raise ValueError(f"invalid shape for {name}: X={X.shape}, y={y.shape}")
    if not np.isfinite(X).all() or not np.isfinite(y).all():
        raise ValueError(f"non-finite value in frozen dataset {name}")
    return Dataset(name, kind, X, y, MANIFEST["source_repository"],
                   MANIFEST["source_license"], spec["sha256"], path)


def _shape(name: str) -> Dataset:
    path = DATA_ROOT / f"{name}.txt"
    frame = pd.read_csv(path, sep=r"\s+", header=None, engine="python")
    return _finish(name, "shape", frame.iloc[:, :-1].to_numpy(), frame.iloc[:, -1].to_numpy())


def _iris() -> Dataset:
    frame = pd.read_csv(DATA_ROOT / "iris.csv")
    species = frame["Species"].astype(str)
    codes = pd.Categorical(species, categories=sorted(species.unique())).codes
    return _finish("iris", "real", frame[["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]].to_numpy(), codes)


def _numeric_last(name: str) -> Dataset:
    # Both files use a numeric-looking first row as their column header.
    # Reading with header=None would silently turn that schema row into a
    # spurious all-numeric observation and an extra reference class.
    frame = pd.read_csv(DATA_ROOT / f"{name}.csv", header=0)
    values = frame.to_numpy(dtype=float)
    return _finish(name, "real", values[:, :-1], values[:, -1])


REGISTRY: dict[str, Callable[[], Dataset]] = {
    "aggregation": lambda: _shape("aggregation"),
    "compound": lambda: _shape("compound"),
    "jain": lambda: _shape("jain"),
    "pathbased": lambda: _shape("pathbased"),
    "r15": lambda: _shape("r15"),
    "spiral": lambda: _shape("spiral"),
    "iris": _iris,
    "wine": lambda: _numeric_last("wine"),
    "seeds": lambda: _numeric_last("seeds"),
}


def load(name: str) -> Dataset:
    """Load one frozen dataset by its canonical lower-case name."""
    try:
        return REGISTRY[name]()
    except KeyError as exc:
        raise KeyError(f"unknown benchmark dataset {name!r}; expected {sorted(REGISTRY)}") from exc


def load_all() -> list[Dataset]:
    return [load(name) for name in REGISTRY]


def standardize(dataset: Dataset) -> np.ndarray:
    """Fit a scaler on this complete matrix and return float64 features."""
    return StandardScaler().fit_transform(dataset.X).astype(float, copy=False)


def frozen_inventory() -> list[dict[str, object]]:
    """Return a serialisable source/hash inventory for run metadata."""
    return [{"name": d.name, "kind": d.kind, "n_samples": d.n_samples,
             "n_features": d.n_features, "n_classes": d.n_classes,
             "file": d.path.name, "sha256": d.sha256,
             "source_url": MANIFEST["datasets"][d.name]["url"]} for d in load_all()]
