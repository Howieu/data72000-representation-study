"""Reproduce the reported experimental results from the distributed data."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DETERMINISTIC_ENVIRONMENT = {
    "PYTHONHASHSEED": "0",
    "OMP_NUM_THREADS": "1",
    "OPENBLAS_NUM_THREADS": "1",
    "MKL_NUM_THREADS": "1",
    "VECLIB_MAXIMUM_THREADS": "1",
    "NUMEXPR_NUM_THREADS": "1",
}


def _run(command: list[str], cwd: Path = ROOT) -> None:
    environment = dict(os.environ)
    environment.update(DETERMINISTIC_ENVIRONMENT)
    print("Running", " ".join(command), flush=True)
    subprocess.run(command, cwd=cwd, env=environment, check=True)


def reproduce(*, rebuild_features: bool = False, compile_pdf: bool = False) -> None:
    stages: list[list[str]] = []
    if rebuild_features:
        stages.append([sys.executable, "-m", "src.representation.build_features"])
    stages.extend(
        [
            [sys.executable, "-m", "src.benchmark.run_benchmark", "--output-dir", "results/benchmark"],
            [sys.executable, "-m", "src.mathematics.complexity_run"],
            [sys.executable, "-m", "src.clustering.run_experiment", "--output-dir", "results/retailrocket"],
            [
                sys.executable,
                "-m",
                "src.explanation.run_retailrocket",
                "--project-root",
                ".",
                "--selected-config",
                "results/retailrocket/selected_configurations.csv",
                "--results-dir",
                "results/retailrocket",
            ],
            [
                sys.executable,
                "-m",
                "src.sensitivity.run_ablation_selection",
                "--root",
                ".",
                "--output-dir",
                "results/sensitivity",
            ],
            [
                sys.executable,
                "-m",
                "src.sensitivity.run_sensitivity",
                "--project-root",
                ".",
                "--output-dir",
                "results/sensitivity",
            ],
            [sys.executable, "-m", "src.reporting.generate_thesis_artifacts", "--root", "."],
        ]
    )
    for stage in stages:
        _run(stage)

    if compile_pdf:
        xelatex = shutil.which("xelatex")
        if xelatex is None:
            raise RuntimeError("XeLaTeX is unavailable")
        tex_root = ROOT / "dissertation" / "overleaf"
        (tex_root / "build").mkdir(parents=True, exist_ok=True)
        command = [
            xelatex,
            "-interaction=nonstopmode",
            "-halt-on-error",
            "-output-directory=build",
            "main.tex",
        ]
        for _ in range(3):
            _run(command, tex_root)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--rebuild-features",
        action="store_true",
        help="rebuild derived feature tables from separately obtained RetailRocket source files",
    )
    parser.add_argument(
        "--compile-pdf",
        action="store_true",
        help="compile the report after regenerating results and figures",
    )
    args = parser.parse_args()
    reproduce(rebuild_features=args.rebuild_features, compile_pdf=args.compile_pdf)


if __name__ == "__main__":
    main()
