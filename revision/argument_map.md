# Argument map

This map reconstructs the dissertation's central evidence chain before any prose rewriting, following the task specification's Section 3 template. Every RESULT figure below was cross-checked against `results/thesis_summary.json` and the underlying `results/retailrocket/*.csv` / `results/sensitivity/*.csv` files (see `revision/numerical_audit.md` for the row-by-row check); none is taken on trust from the manuscript text alone.

```
Raw RetailRocket events (2,756,101 rows)
    ↓ cohort rule: every visitor with >=1 transaction event
same purchaser cohort (n = 11,719), same snapshot, same order
    ↓ two feature contracts built from the same event history
compact (3 dims) vs rich (12 dims) representation
    ↓ standardisation is representation-specific -> different pairwise distances
different feature geometry
    ↓ same grids, same seeds, same deployment constraints
K Means / CLASSIX clustering (independently selected per representation)
    ↓ compare selected partitions
cluster structure comparison (ARI/NMI/VI, transition tables)
    ↓ refit on resampled 80% subsets
within-representation stability (fixed-parameter overlap-resampling)
    ↓ two independent explanation channels
explanation evidence
       |-- CLASSIX intrinsic provenance (aggregation groups, starting points)
       `-- ExKMC post-hoc fidelity/complexity (held-out tree agreement)
    ↓ documented size/coverage/distinctiveness audit
addressability
    ↓ feature deletion, PCA, perturbation, session windows, permutation
robustness / sensitivity
    ↓
bounded conclusion: representation is not a neutral preprocessing choice
```

## CLAIM → METHOD → RESULT → INTERPRETATION → LIMITATION

### C1. The two representations describe the same customers but different geometry

- **METHOD.** Both feature tables are built from the same 11,719-purchaser cohort, same snapshot rule, same row order; unit tests verify identical purchase-summary columns across both tables (`data_representation.tex`, verified against `data/manifests`).
- **RESULT.** Compact = 3 standardised dimensions; rich = 12 (`thesis_summary.json: representations.compact_dimensions=3, rich_dimensions=12`).
- **INTERPRETATION.** Any downstream difference in clustering cannot be attributed to a different population or a different purchase definition — only to the nine added behavioural dimensions.
- **LIMITATION.** This isolates *an* effect of adding these nine specific variables; it does not generalise to arbitrary representation choices or other domains.

### C2. Independently selected K Means partitions strongly disagree across representations, despite both giving 4 clusters

- **METHOD.** K Means (k-means++, 20 inits, seed 20260801, k in [2,12]) selected independently per representation under the deployment rule (silhouette-maximising subject to noise/imbalance guards); partitions compared by ARI/NMI/VI with Hungarian-matched transition tables.
- **RESULT.** Both select k=4. Cross-representation ARI = 0.014, NMI = 0.089, VI = 1.691 nats, 54.61% of customers relabelled under matched correspondence (verified in `results/retailrocket/paired_partition_comparison.csv` and `selected_configurations.csv`).
- **INTERPRETATION.** Low ARI here means the two 4-cluster *partitions* barely agree with **each other**; there is no external ground-truth label being compared against (this is the point of supervisor comment SF-08 — see `revision/supervisor_feedback_audit.md`). Because standardisation gives the nine added behavioural dimensions comparable weight to the three purchase dimensions, they can dominate the pairwise distances that drive centroid placement, so the geometry — and hence the Voronoi partition — changes substantially even for unchanged customers.
- **LIMITATION.** Matching cluster counts (both k=4) does not imply matching cluster content; the comparison does not indicate which representation is "more correct" since no external criterion exists.

### C3. CLASSIX shows the same qualitative pattern with a different structural signature

- **METHOD.** CLASSIX candidates (radius 0.25–1.75 step 0.05, minPts in {1,5,10}, distance/density merging) selected independently per representation under the same deployment rule.
- **RESULT.** Compact selects 2 nonnoise clusters, 0 noise; rich selects 3 nonnoise clusters plus 218 noise assignments (1.86% noise fraction). Cross-representation ARI = 0.068 (verified in `results/thesis_summary.json: deployment_results`).
- **INTERPRETATION.** CLASSIX's principal sorting direction and aggregation radius are also sensitive to the added dimensions' geometry; the rich fit both changes cluster count and introduces noise (points the aggregation process could not place in any adequately sized/merged group).
- **LIMITATION.** The compact result (2 clusters, silhouette 0.595) and rich result (3 clusters + noise, silhouette 0.291) are not nested or directly comparable configurations; the comparison is between independently optimal choices, not a controlled ablation.

### C4. High within-representation stability coexists with low cross-representation agreement — these are not contradictory

- **METHOD.** Ten pairs of independent 80% resamples, refit per pair, ARI computed on the customers common to both samples.
- **RESULT.** Compact/rich K Means stability ≈ 0.988 / 0.995; compact/rich CLASSIX stability ≈ 0.985 / 0.965 (verified in `results/retailrocket/resampling_stability.csv`).
- **INTERPRETATION.** Stability measures sensitivity to *which customers* are sampled, holding the representation and selected parameters fixed. Cross-representation ARI measures agreement between *two different geometries* applied to the *same* customers. These are different questions; a configuration can be highly reproducible within its own representation while two representations still disagree with each other.
- **LIMITATION.** Stability does not certify that the selected configuration is the uniquely correct one, nor that model *selection itself* (as opposed to model *refitting*) would be reproducible under resampling.

### C5. CLASSIX intrinsic provenance and ExKMC post-hoc fidelity answer different questions and diverge structurally

- **METHOD.** CLASSIX exports its own aggregation-group trace (groups → merges → final labels) for its selected fit. ExKMC (K fixed at 4, five 80/20 splits, leaf budget K to 4K) approximates the *K Means* predictor's labels with a decision tree fitted on training rows only, evaluated on held-out rows.
- **RESULT.** Compact CLASSIX: 131 aggregation groups → 2 clusters. Rich CLASSIX: 559 groups → 3 clusters + noise (verified in `results/retailrocket/classix_provenance.json` / `explanation_complexity.csv`). ExKMC at 4 leaves: compact held-out fidelity 0.9448, rich 0.9650; at 16 leaves: compact 0.9924, rich 0.9747 (verified in `results/retailrocket/exkmc_oos_fidelity.csv`).
- **INTERPRETATION.** These are two independent explanation channels applied to two independent objects (CLASSIX explains its own partition; ExKMC explains K Means's partition). The crossover pattern — rich starts higher at 4 leaves but compact overtakes by 16 leaves — shows that representation changes not only *what* is clustered but the *complexity/fidelity relationship* of a post-hoc explanation of it. Rich CLASSIX needing >4x the aggregation groups reflects finer local geometric structure being traced, not a claim about human interpretability.
- **LIMITATION.** CLASSIX group count and ExKMC fidelity/leaves must never be combined into one "explainability score" — they are not commensurable (this is an explicit requirement from the task specification, Section 5, and is directly supported by the dissertation's own framing in `literature_review.tex` and `explanation_results.tex`).

### C6. Addressability is a stricter, distinct criterion from existence, separation, or explainability

- **METHOD.** Documented audit: nonnoise cluster with >=50 customers and >=1% of nonnoise customers, >=80% category coverage, and >=0.5 IQR distinctiveness on 2–4 named features.
- **RESULT.** Zero of five nonnoise CLASSIX clusters (compact or rich) pass. Zero of four compact K Means clusters pass. One of four rich K Means clusters passes (verified in `results/retailrocket/addressability_audit.csv`).
- **INTERPRETATION.** A cluster can exist, be well separated internally (high silhouette), and be reproducible under resampling, and still fail addressability because it is too small, lacks category coverage, or lacks distinctive named-feature contrasts. This motivates the conceptual hierarchy used in the strengthened §4.5/§4.7 discussion: existence ≠ separation ≠ stability ≠ rule-expressibility ≠ addressability ≠ realised business value.
- **LIMITATION.** Passing the audit is a technical/operational property (queryability, coverage, distinctiveness), not evidence of commercial value, causal effect, or human comprehension.

### C7. Robustness checks rule out specific alternative explanations without claiming a full variance decomposition

- **METHOD/RESULT** (each verified against `results/sensitivity/*.csv`):
  - Feature deletion: removing category features (`distinct top categories`, `top category share`) is the single largest driver of rich-partition change (ARI drops to 0.189–0.238 for CLASSIX, 0.516–0.517 for K Means vs. 0.855–0.991 for other single-feature deletions).
  - PCA (6 components, 91.32% variance): reduced-space K Means/CLASSIX agree with the named-space result at ARI 0.995/0.920 — most fitted structure survives dimensionality reduction, but PCA is never used for rule explanations because components lack direct business meaning.
  - Gaussian perturbation: compact CLASSIX exact through SD 0.001 (mean ARI 0.999 at SD 0.01); rich CLASSIX exact through SD 0.0001, degrading to mean ARI 0.985 at SD 0.01 — more sensitive but not wholesale reassignment.
  - Session windows (15/30/60 min): both partitions persist qualitatively; CLASSIX noise count shifts from 218 to 220/239.
  - Permutation control: adding permuted (marginal-preserving, jointly-meaningless) dimensions to the compact space still collapses structure (compact CLASSIX → single cluster, ARI 0; compact K Means → ARI 0.017 against its own unpermuted partition).
- **INTERPRETATION.** Each diagnostic rules out one specific alternative explanation: feature deletion rules out "it's not really the category features"; PCA rules out "the rich effect is only redundant dimensions"; perturbation rules out "the assignments are numerically fragile noise"; session windows rule out "the 30-minute convention alone drives the conclusion"; permutation demonstrates *that* dimensionality/standardisation alone can move geometry, as an existence proof.
- **LIMITATION.** The permutation control is a single deterministic existence demonstration, not a variance decomposition — it does **not** quantify what fraction of the compact-to-rich effect is "caused by dimensionality" versus "caused by the specific behavioural content" of the nine added variables. This distinction must be stated explicitly and is one of the points most at risk of being overclaimed (task specification Section 11).

### Bounded conclusion

Representation is part of the empirical clustering model, not a neutral preprocessing choice, **for this cohort, this feature contract, and these two algorithms**. Richer behavioural information changes observed geometry, assignments, explanation complexity/fidelity, and addressability — but does not automatically imply better clustering, simpler explanations, deployment-ready segments, or realised business value. No claim in this map exceeds what the cited result files support.
