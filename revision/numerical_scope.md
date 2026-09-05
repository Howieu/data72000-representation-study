# Numerical scope and complementary checks

`audit_numerical.py` maps 117 retained numeric claims to explicit source selectors/aggregations and records four withdrawn baseline runtime claims. `check_consistency.py` adds 817 assertions on frozen evidence, independent partition metrics, label counts, transitions, provenance, profiles, addressability and benchmark ranks. These totals include repeated group-level invariants, not 817 independent empirical findings.

| Manuscript scope | Authoritative evidence and check | Result |
| --- | --- | --- |
| 11,719 IDs; 3/12 features; shared purchase values | Both feature tables and feature schema, IDs unique and same ordered rows | Match; metadata columns are explicitly excluded from feature counts |
| 2,756,101 events; 20,275,902 property rows; 1,669 category nodes | Raw-file manifests and four SHA256-verified original files; category tree loaded by raw audit | Match; raw files remain outside repository |
| 230,678 purchaser events; snapshot 19 September 2015 02:59:47 UTC | Raw event reconstruction and full timestamp table comparison | Match; stored timestamp includes .788 seconds, prose reports whole seconds |
| Category join 2,099,173 / 76.16%; 1,168 missing-category purchasers; 428 zero-view denominators | `raw_reproduction_check.json`; all reconstructed coverage rows compared | Match |
| Main grid 11 K Means and 186 CLASSIX candidates per space; ranges, steps, minPts, mergeScale, seeds | Frozen `analysis_protocol.json`, actual candidate grid and engine code | Match: 31 radii × 3 minimum sizes × 2 merge branches; no settings changed |
| Boundary extension 1.80–2.25 | Frozen amendment and boundary-extension result table | Supplementary boundary check retained; primary selection unchanged |
| 2–12 clusters, ≤20% noise and ≤95% largest nonnoise share | Frozen protocol and selection code; common acceptable grid intersection recomputed | Match; 41 matched CLASSIX settings |
| ARI/NMI/VI | Numeric audit plus independent contingency/entropy calculations from saved labels | Match to 1e-12; includes noise state |
| K Means migration 54.61%; CLASSIX migration 18.66% | Saved transition table and independent label recount | Match |
| Cluster/noise counts and largest shares | All eight selected configurations recounted from 93,752 saved label rows | Match, including rich 218 noise assignments |
| Silhouette/DB/CH | Explicit source-value checks for four selected partitions | Match; full all-pairs metric refitting intentionally not rerun |
| 10 pairs of 80% resamples; four mean ARIs; CLASSIX minima 0.881 / 0.941 | Frozen protocol and resampling records; exact minima 0.8809620729 / 0.9412726598 | Match; conditional configurations only |
| ExKMC five splits, four-leaf train/test means, held-out ranges, 16-leaf means and depth/conditions | Fidelity and complexity records, selected by representation and budget | Match; no test rows used for selection |
| Four effective rules, depth 3, mean 2.25 conditions at smallest budget | Both representations' five four-leaf rows | Match |
| Train-only alternative selects compact K=2 / rich K=4; compact fidelity 0.9985 | Train-selected records and leaf-budget-two mean | Match; excluded from main equal-K comparison |
| 131/559 aggregation groups, exact final labels | Native arrays, corrected trace and representative-membership invariants | Counts and labels unchanged; baseline row-order error repaired from saved arrays |
| Addressability 0 compact K Means, 0 CLASSIX in either space, 1 rich K Means | Recomputed size/share/coverage/effect gates on all 13 rows | Match; one passing rich row |
| Rich 166-customer medians 338.5 events/28 sessions/12 categories; 1,156-customer recency 127.4; 33-customer medians 869/36/14 | Explicit selected-profile row checks | Match; global medians 6/2/1 also checked |
| Other fixed deletions CLASSIX 0.927–0.967; K Means 0.855–0.991 | Excluding two category deletions: actual extrema 0.9268538744/0.9666118434 and 0.8550179402/0.9905283117 | Match; K Means activity span 0.8736384842 and interevent 0.8550179402 round to 0.874/0.855 |
| Reselected category deletions; 22 scenarios and 4,334 fits | Feature-reselection outputs and full saved grid | Match; all 22 scenarios have acceptable results for both methods; progressive endpoints retain exact primary assignments |
| Acceptable CLASSIX radii and minimum-size counts | Grid constraints independently applied | Compact: 23 radii, 0.35–1.45, minPts counts 0/23/32; rich: 20 radii, 0.30–1.25, counts 0/19/27 |
| PCA six components / 91.32%; ARIs, silhouettes and resampling | PCA rows and saved summary | Match; noise falls to 71 and use_for_rules is false |
| Gaussian perturbation exact low-level results and mean/min ARIs | All 82 rows; ten repeats at each nonzero level | Match; Gaussian standard deviation is not treated as a uniform bound |
| Session 15/30/60 minutes, ARIs, counts and noise | Six session-window rows | Match; zero change at 30, rich CLASSIX alternative noise 220/239 |
| Permuted extra dimensions K Means ARI 0.017/silhouette 0.127; CLASSIX one cluster after one added dimension | Frozen permutation rows | Match; deterministic existence control only |
| Nine benchmark dataset winners/mean ARIs and mean ranks | Selected benchmark rows, independent rank calculation | Match; four unsupported runtime literals removed, without altering recorded timing data |
| Word count and abstract limit | TeXcount `word_count.json` with explicit inclusion rules | Updated from source; abstract 204 words, below the 300-word guidance |

## Evidence boundary

No clustering grids, seeds, labels, feature definitions, model-selection results or empirical figures were changed. The sole corrected result artifact is the derived CLASSIX provenance mapping; its original native arrays, final labels and counts remain byte-value identical. Rebuilding source-data features in memory and recomputing summaries are reproducibility checks, not additional experimental conditions. The raw-data check and regression tests pass. No statistical significance or new numerical result was inferred from unmeasured evidence.
