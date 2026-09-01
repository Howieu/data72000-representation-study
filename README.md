# DATA72000 RetailRocket representation study

This repository contains the data, code and recorded outputs for a comparison of compact transaction features and richer behavioural features within the same cohort of 11,719 RetailRocket purchasers. The analysis covers clustering structure, resampling stability, CLASSIX provenance, ExKMC fidelity, explanation complexity and technical addressability.

## Repository contents

- `data/derived` contains the compact and rich customer feature tables and the purchaser timestamps used for session sensitivity.
- `data/raw/benchmarks` contains nine labelled benchmark datasets and their upstream licence notice.
- `data/manifests` records source provenance, schemas, sizes and SHA256 values.
- `src` contains feature construction, clustering, explanation, sensitivity, reporting and reproduction code.
- `results` contains the benchmark, customer and sensitivity outputs used by the report.
- `protocol` records the fixed grids, seeds, selection rules and deployment constraints.
- `dissertation/overleaf` contains the report source, figures, references and compiled PDF.
- `REPOSITORY_MANIFEST.json` records the size and SHA256 value of each distributed content file.

## Environment

The recorded environment uses Python 3.10.20, NumPy 1.26.4, pandas 2.3.3, SciPy 1.15.3, scikit-learn 1.7.2, CLASSIX 1.5.1, ExKMC 0.0.3 and Matplotlib 3.10.9. The complete dependency definition is stored in `environment.yml`.

```bash
conda env create -f environment.yml
conda activate retailrocket-representation-thesis
```

## Reproduction

The distributed data support the complete result and figure reproduction entry point.

```bash
python -m src.reproduce
```

The report can also be compiled when XeLaTeX is available.

```bash
python -m src.reproduce --compile-pdf
```

The four original RetailRocket files are only required when the distributed feature tables are reconstructed from the source event logs.

```bash
python -m src.reproduce --rebuild-features
```

The default sequence regenerates the benchmark, customer clustering, explanation, sensitivity, summary and figure outputs. Random seeds and numerical thread settings are fixed by the protocol and reproduction entry point.

## Data

The distributed compact representation contains purchase recency, purchase occasion count and purchase event count. The rich representation contains the same three columns in the same customer order plus nine activity, conversion, temporal and category features. The purchaser timestamp table contains only purchaser identifiers and event timestamps and supports the 15, 30 and 60 minute session-window analysis.

The four large RetailRocket source files are not redistributed. They originate from the [Retailrocket recommender system dataset](https://www.kaggle.com/datasets/retailrocket/ecommerce-dataset) and are resolved under `data/raw/retailrocket` during optional feature reconstruction.

| File | Rows | Bytes | SHA256 |
| --- | ---: | ---: | --- |
| `events.csv` | 2,756,101 | 94,237,913 | `3745aa83238b1e6d44d8fda209807899f420084398f94ddf745f3cbcfecbf9e7` |
| `item_properties_part1.csv` | 10,999,999 | 484,315,749 | `30aad5aeca58b2dc27dcc73e1708565f5818e45adb3eb57401f91e87355b0b81` |
| `item_properties_part2.csv` | 9,275,903 | 408,929,907 | `d5e7d1a91dc40f522aeb596b267e6c87d8aed689a7192d12369cfb165eb987e5` |
| `category_tree.csv` | 1,669 | 14,454 | `94e865eb0a3d48cbbfe3b79079018dd92509315c88f5fd8d00d0b4b5af434f5b` |

The study snapshot is the maximum event timestamp plus twenty four hours. The cohort contains every visitor with at least one transaction event. The nine labelled benchmark files are stored in `data/raw/benchmarks`. Reference labels are excluded from parameter selection.

## Analysis protocol

`protocol/analysis_protocol.json` records the cohort, snapshot rule, random seeds, K Means grid, CLASSIX grid, deployment constraints, perturbation levels, resampling design and ExKMC split seeds. Candidate selection maximises silhouette subject to two to twelve clusters, noise no greater than 0.20 and largest nonnoise cluster share no greater than 0.95. The unconstrained optimum is retained separately.

K Means uses twenty initialisations. Benchmark K Means structures use five seeds and are aggregated before selection. Customer stability uses ten pairs of independent 80 per cent samples. ExKMC uses five fixed 80 per cent training and 20 per cent test splits. The main explanation comparison fixes K at four and fits transformations, K Means and ExKMC on training rows only. Nonzero perturbation levels use ten fixed seeds.

## Output map

- `results/benchmark` contains every benchmark fit, seed aggregation, label-free selection and supplementary oracle diagnostic.
- `results/retailrocket` contains candidate grids, selected configurations, labels, partition comparisons, transitions, profiles, resampling records, CLASSIX provenance, ExKMC fidelity, exported rules, explanation complexity and addressability results.
- `results/sensitivity` contains feature deletion and reselection, PCA, CLASSIX perturbation, session-window, permutation and empirical distance results.
- `results/thesis_summary.json` links the result tables to the numerical values reported in the dissertation.

## Interpretation boundaries

ExKMC is a post hoc explanation of K Means labels rather than a clustering algorithm. PCA is a structural diagnostic and is not used for rules. CLASSIX provenance explains its own fitted partition. Addressability measures size, data coverage and named-feature distinctiveness. These measures do not establish commercial return, treatment response or human comprehension.

## Licence record

The RetailRocket data card identifies the source licence as [Creative Commons Attribution NonCommercial ShareAlike 4.0 International](https://creativecommons.org/licenses/by-nc-sa/4.0/). The distributed customer tables and purchaser timestamp table are derived from the source event logs under those conditions.

The benchmark files were obtained from the [CLASSIX repository](https://github.com/nla-group/CLASSIX/tree/6749f00e7e57a26b5dd93632e50f17ccc1d5ff8b/exps/data) at revision `6749f00e7e57a26b5dd93632e50f17ccc1d5ff8b` and retain the upstream MIT notice in `data/raw/benchmarks/LICENSE`.

No blanket licence is granted for the dissertation source code. Third-party packages retain their respective licences. Further licence details are recorded in `LICENSE`.
