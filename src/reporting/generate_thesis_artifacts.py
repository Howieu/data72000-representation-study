"""Generate dissertation-facing summaries strictly from frozen result files."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

plt.rcParams.update({"font.size": 12})


ROOT = Path(__file__).resolve().parents[2]


def _json_value(value: Any) -> float | int | bool | str | None:
    if pd.isna(value):
        return None
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, str):
        return value
    return float(value)


def _deployment(selected: pd.DataFrame) -> pd.DataFrame:
    out = selected[selected["selection"].eq("deployment_acceptable")].copy()
    if len(out) != 4 or not out["deployment_acceptable"].astype(bool).all():
        raise ValueError("four deployment-acceptable customer configurations are required")
    return out.sort_values(["method", "representation"]).reset_index(drop=True)


def _selected_summary(frame: pd.DataFrame, stability: pd.DataFrame) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in _deployment(frame).itertuples(index=False):
        values = stability[
            stability["representation"].eq(row.representation)
            & stability["method"].eq(row.method)
            & stability["selection"].eq("deployment_acceptable")
        ]["ari_overlap"].dropna()
        rows.append({
            "representation": row.representation,
            "method": row.method,
            "candidate_id": row.candidate_id,
            "parameters": json.loads(row.parameters),
            "n_clusters": int(row.n_clusters),
            "n_noise": int(row.n_noise),
            "noise_fraction": float(row.noise_fraction),
            "largest_non_noise_cluster_share": float(row.largest_non_noise_cluster_share),
            "silhouette": float(row.silhouette),
            "davies_bouldin": float(row.davies_bouldin),
            "calinski_harabasz": float(row.calinski_harabasz),
            "stability_ari_mean": float(values.mean()),
            "stability_ari_std": float(values.std(ddof=0)),
            "stability_pairs": int(values.size),
        })
    return rows


def _paired_summary(frame: pd.DataFrame, transitions: pd.DataFrame) -> list[dict[str, Any]]:
    selected = frame[frame["comparison"].eq("independent_deployment_selection")]
    rows = []
    for row in selected.itertuples(index=False):
        current = transitions[transitions["method"].eq(row.method)]
        rows.append({
            "method": row.method,
            "ari": float(row.ari),
            "nmi": float(row.nmi),
            "variation_of_information": float(row.vi),
            "matched_migration_share": float(
                current.loc[current["migration_flag"].astype(bool), "share_of_customers"].sum()
            ),
        })
    return rows


def _explanation_summary(oos: pd.DataFrame) -> list[dict[str, Any]]:
    main = oos[oos["k_prime"].eq(oos["k"])]
    rows = []
    for representation, part in main.groupby("representation", sort=True):
        rows.append({
            "representation": representation,
            "splits": int(len(part)),
            "selected_k_values": sorted(int(x) for x in part["k"].unique()),
            "train_fidelity_mean": float(part["train_fidelity"].mean()),
            "test_fidelity_mean": float(part["test_fidelity"].mean()),
            "test_fidelity_std": float(part["test_fidelity"].std(ddof=0)),
            "effective_rules_mean": float(part["effective_rules"].mean()),
            "max_depth_mean": float(part["max_depth"].mean()),
            "conditions_per_rule_mean": float(part["mean_conditions_per_rule"].mean()),
        })
    return rows


def _figure_structure(selected: pd.DataFrame, stability: pd.DataFrame, path: Path) -> None:
    data = _deployment(selected).copy()
    method_name = {"classix": "CLASSIX", "kmeans": "K Means"}
    data["key"] = data.apply(
        lambda row: f"{str(row['representation']).title()} {method_name[str(row['method'])]}",
        axis=1,
    )
    stability_mean = stability[stability["selection"].eq("deployment_acceptable")].groupby(
        ["representation", "method"], as_index=False
    )["ari_overlap"].mean().rename(columns={"ari_overlap": "stability"})
    data = data.merge(stability_mean, on=["representation", "method"], validate="one_to_one")
    fig, axes = plt.subplots(1, 3, figsize=(8.2, 3.0))
    colors = ["#4C78A8", "#72B7B2", "#F58518", "#E45756"]
    for axis, column, label in zip(
        axes,
        ("silhouette", "largest_non_noise_cluster_share", "stability"),
        ("Silhouette", "Largest cluster share", "Resampling ARI"),
    ):
        axis.bar(data["key"], data[column], color=colors)
        axis.set_ylabel(label)
        axis.tick_params(axis="x", rotation=38)
        axis.spines[["top", "right"]].set_visible(False)
        axis.grid(axis="y", alpha=0.22)
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def _figure_exkmc(oos: pd.DataFrame, path: Path) -> None:
    frame = oos.copy()
    frame["leaf_ratio"] = frame["k_prime"] / frame["k"]
    fig, axis = plt.subplots(figsize=(6.7, 3.8))
    colors = {"compact": "#4C78A8", "rich": "#E45756"}
    for representation, part in frame.groupby("representation", sort=True):
        summary = part.groupby("leaf_ratio")["test_fidelity"].agg(["mean", "std"]).reset_index()
        axis.plot(summary["leaf_ratio"], summary["mean"], marker="o",
                  label=representation.title(), color=colors[representation])
        axis.fill_between(summary["leaf_ratio"], summary["mean"] - summary["std"],
                          summary["mean"] + summary["std"], color=colors[representation], alpha=0.14)
    axis.set_xlabel("Leaf budget relative to K")
    axis.set_ylabel("Held out fidelity")
    axis.set_ylim(0, 1.02)
    axis.spines[["top", "right"]].set_visible(False)
    axis.grid(alpha=0.22)
    axis.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def _figure_sensitivity(ablation_selected: pd.DataFrame, pca: pd.DataFrame, path: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(8.2, 4.4))
    deletion = ablation_selected[
        ablation_selected["selection"].eq("deployment_acceptable")
        & ablation_selected["scenario_type"].eq("leave_one_out")
    ].copy()
    deletion["dropped_feature"] = deletion["scenario_id"].str.replace(
        "drop_feature_", "", regex=False
    )
    ab = deletion.pivot(
        index="dropped_feature", columns="method", values="ari_vs_rich_deployment"
    )
    ab = ab.assign(order=ab.mean(axis=1)).sort_values("order").drop(columns="order")
    y = np.arange(len(ab.index))
    height = 0.38
    axes[0].barh(y - height / 2, ab["classix"], height, label="CLASSIX", color="#4C78A8")
    axes[0].barh(y + height / 2, ab["kmeans"], height, label="K Means", color="#72B7B2")
    axes[0].set_yticks(y, [str(name).replace("_", " ") for name in ab.index])
    axes[0].set_xlabel("ARI against full rich partition")
    axes[0].set_xlim(0, 1.02)
    axes[0].spines[["top", "right"]].set_visible(False)
    axes[0].legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.12), ncol=2)
    pc = pca.pivot(index="algorithm", columns="space", values="reference_ari")
    x = np.arange(len(pc.index))
    width = 0.34
    axes[1].bar(x - width / 2, pc["rich_named"], width, label="Named", color="#4C78A8")
    axes[1].bar(x + width / 2, pc["pca_90"], width, label="PCA", color="#F58518")
    method_name = {"classix": "CLASSIX", "kmeans": "K Means"}
    axes[1].set_xticks(x, [method_name[str(v)] for v in pc.index])
    axes[1].set_ylabel("ARI against named space")
    axes[1].set_ylim(0, 1.02)
    axes[1].spines[["top", "right"]].set_visible(False)
    axes[1].legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(path, dpi=240, bbox_inches="tight")
    plt.close(fig)


def generate(root: Path = ROOT) -> dict[str, Any]:
    result_root = root / "results"
    retail = result_root / "retailrocket"
    sensitivity_root = result_root / "sensitivity"
    selected = pd.read_csv(retail / "selected_configurations.csv")
    stability = pd.read_csv(retail / "resampling_stability.csv")
    paired = pd.read_csv(retail / "paired_partition_comparison.csv")
    transitions = pd.read_csv(retail / "cluster_transition_matrix.csv")
    oos = pd.read_csv(retail / "exkmc_oos_fidelity.csv")
    ablation = pd.read_csv(sensitivity_root / "feature_ablation.csv")
    ablation_selected = pd.read_csv(sensitivity_root / "feature_ablation_selected.csv")
    pca = pd.read_csv(sensitivity_root / "pca_sensitivity.csv")
    distance = pd.read_csv(sensitivity_root / "distance_complexity_classix.csv")
    benchmark = pd.read_csv(result_root / "benchmark" / "selected_label_free.csv")

    summary = {
        "cohort_size": 11719,
        "representations": {"compact_dimensions": 3, "rich_dimensions": 12},
        "deployment_results": _selected_summary(selected, stability),
        "paired_results": _paired_summary(paired, transitions),
        "explanation_results": _explanation_summary(oos),
        "pca": [
            {key: _json_value(value) for key, value in row.items()}
            for row in pca.to_dict(orient="records")
        ],
        "feature_reselection": [
            {key: _json_value(value) for key, value in row.items()}
            for row in ablation_selected[
                ablation_selected["selection"].eq("deployment_acceptable")
            ].to_dict(orient="records")
        ],
        "benchmark": {
            "datasets": int(benchmark["dataset"].nunique()),
            "methods": sorted(str(x) for x in benchmark["method"].unique()),
            "selected_rows": int(len(benchmark)),
        },
        "distance_complexity": [
            {key: _json_value(value) for key, value in row.items()}
            for row in distance.to_dict(orient="records")
        ],
    }
    (result_root / "thesis_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    figures = root / "dissertation" / "overleaf" / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    _figure_structure(selected, stability, figures / "customer_structure.png")
    _figure_exkmc(oos, figures / "exkmc_tradeoff.png")
    _figure_sensitivity(ablation_selected, pca, figures / "sensitivity_summary.png")
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    args = parser.parse_args()
    generate(args.root.resolve())


if __name__ == "__main__":
    main()
