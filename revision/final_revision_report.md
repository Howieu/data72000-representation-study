# Final supervisor-feedback revision report

## Changes made

Revised the dissertation for readable definitions, explicit research questions and a connected argument from representation to clustering, explanation and operational assessment. The final manuscript has 9188 words under the documented TeXcount convention; the abstract has 204 words. The compiled PDF has 42 pages.

## Supervisor feedback addressed

All 16 substantive annotations (15 highlights and one text note) were extracted from the supplied annotated PDF and visually located. All are addressed, with final page/section anchors in `supervisor_feedback_audit.md`. Popup companions are not counted as additional comments. The supplied revision plan was used to structure the broader revision; comments in the PDF were treated as feedback to assess against evidence.

## Mathematical revisions

Added the K Means objective and definitions, geometry/scaling, k-means++ and repeated initialisations. Introduced the CLASSIX preprocessing, sorting, aggregation, merging and noise decisions before advanced mathematics. Verified the version 1.5.1 source, including processed-radius units and density-branch behaviour.

Section 3.2.3 now motivates projection pruning, defines each symbol, explains Cauchy–Schwarz and its converse limitation, and separates a worst-case distance-arithmetic bound from package counters and runtime. Section 3.2.4 explains the purpose of the certificate, eigengap and Davis–Kahan bound, processed displacement and score margins, sign orientation, aggregation/merge windows and finite-decision proof. The certificate is local, conditional, sufficient only and distance-branch only. It does not certify the selected rich density-merging result or assert that saved fits satisfy every margin.

## Discussion revisions

Chapter 4 now explains why within-space repeatability can coexist with cross-space disagreement, why internal metrics disagree and why the 95% deployment cap is an operational choice. It interprets the ExKMC fidelity frontier, distinguishes provenance granularity from human comprehension, and separates grouping, geometric quality, repeatability, rules, addressability and realised value. Section 4.5 distinguishes strong, conditional and unknown conclusions. Chapter 5 introduces no new result.

## Numerical consistency checks

The numerical audit contains 121 rows: 117 retained claims match repository evidence and four unsupported historical runtime medians were withdrawn. Complementary coverage in `numerical_scope.md` includes protocol constants, feature definitions, cohort/profile counts and ranges. All retained empirical result files and data match baseline hashes except the documented provenance repair.

The consistency checker passed 817 assertions. It verifies cohort/feature identity, selected labels and cluster/noise counts, independently recomputed ARI/NMI/VI, transitions, addressability, benchmark ranks and preserved native CLASSIX arrays. Raw inputs were found outside the distribution; all four SHA256 values match the recorded inputs. Read-only reconstruction reproduces the compact/rich feature tables, coverage audit and all 230678 purchaser timestamp rows (floating tolerance 1e-12).

An actual provenance export error was found: native `groups_` uses sorted rows, while `labels_` and `groupCenters_` use input rows. Applying saved `inverse_ind` repairs exported group membership, merge membership and customer traces. The exporter and regression tests now enforce representative membership and one final label per group. No fit was run; native arrays, labels, scalers, settings and group counts 131/559 are unchanged. See `evidence_gaps.md` for the original failure counts.

## Tests/build commands executed

From the repository root unless stated otherwise:

```sh
python3 revision/audit_numerical.py
python3 revision/check_consistency.py
python3 revision/check_citations.py
python3 -m unittest discover -s tests -v
python revision/check_mathematics.py
python revision/check_raw_reproduction.py --raw-dir /Users/vendredi/Agents_outputs/claude/erp-project/retailrocket-representation-thesis/data/raw/retailrocket
 git diff --check
```

The two commands requiring numpy/pandas used `/Users/vendredi/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3`. Five provenance regression tests passed. Deterministic mathematical helper checks passed; these do not certify customer fits. All 31 active citation keys exist in both bibliography sources and no manuscript TODO/FIXME/TBD/placeholder remains. `citation_audit.md` records primary-source verification and access limits.

Build command, run three times from `dissertation/overleaf`:

```sh
/Library/TeX/texbin/xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex
```

Final build passed without fatal errors, undefined references/citations or overfull boxes. Underfull messages were reviewed visually and accepted. All 42 final rendered pages were inspected; equations, tables, figures, contents, bibliography and page breaks passed (see `pdf_qa.md`). The complete manuscript diff and the exporter/helper changes were reviewed. The large provenance JSON was reviewed semantically against preserved native arrays.

The full `src.reproduce` experimental pipeline was deliberately not invoked: its compile flag would also rerun the empirical programme. The only result repair was reconstructed from saved arrays.

## Remaining limitations

One purchaser event log; no ground-truth customer types, prospective business outcomes or human-comprehension assessment. Resampling is conditional on selected parameters, operational cutoffs are study choices, and the single permutation is not a causal variance decomposition. The stability proposition excludes density merging and requires unmeasured positive margins. Historical papers with inaccessible full text are explicitly distinguished from full-text/implementation checks in the citation audit; conventional metric definitions are supported by official documentation.

## Any unresolved evidence gaps

No unresolved essential gap prevents the bounded conclusion. **No supervisor feedback genuinely required new experimental evidence.** The empirical programme, features, grids, seeds, constraints, selection and fitted labels were retained. Read-only reconstruction, source inspection and deterministic regression checks were sufficient. No redesigned or additional customer experiment was performed.

## Files changed

- `REPOSITORY_MANIFEST.json`
- `dissertation/overleaf/build/main.pdf`
- `dissertation/overleaf/main.tex`
- `dissertation/overleaf/references.bib`
- `dissertation/overleaf/references_harvard.tex`
- `dissertation/overleaf/sections/abstract.tex`
- `dissertation/overleaf/sections/benchmark_results.tex`
- `dissertation/overleaf/sections/conclusion.tex`
- `dissertation/overleaf/sections/data_representation.tex`
- `dissertation/overleaf/sections/explanation_results.tex`
- `dissertation/overleaf/sections/introduction.tex`
- `dissertation/overleaf/sections/literature_review.tex`
- `dissertation/overleaf/sections/methods_mathematics.tex`
- `dissertation/overleaf/sections/paired_results.tex`
- `dissertation/overleaf/sections/sensitivity_limitations.tex`
- `dissertation/overleaf/sections/technical_appendix.tex`
- `results/retailrocket/classix_provenance.json`
- `revision/.gitignore`
- `revision/argument_map.md`
- `revision/audit_numerical.py`
- `revision/baseline_audit.md`
- `revision/check_citations.py`
- `revision/check_consistency.py`
- `revision/check_mathematics.py`
- `revision/check_raw_reproduction.py`
- `revision/citation_audit.md`
- `revision/citation_key_check.json`
- `revision/classix_source_record.json`
- `revision/consistency_check.json`
- `revision/evidence_gaps.md`
- `revision/final_revision_report.md`
- `revision/mathematical_check.json`
- `revision/numerical_audit.md`
- `revision/numerical_scope.md`
- `revision/pdf_qa.md`
- `revision/raw_reproduction_check.json`
- `revision/repair_provenance.py`
- `revision/supervisor_annotations.json`
- `revision/supervisor_feedback_audit.md`
- `revision/terminology_audit.md`
- `revision/word_count.json`
- `src/explanation/classix_provenance.py`
- `src/provenance_alignment.py`
- `tests/test_provenance_alignment.py`

The tracked PDF follows the existing repository convention. Raw data, credentials and temporary raster/build previews are excluded. The distribution manifest is refreshed to the final tracked deliverables.

## Final PDF path

`dissertation/overleaf/build/main.pdf`

Local absolute path: `/Users/vendredi/Agents_outputs/claude/erp-project/retailrocket-representation-thesis/submission/data72000-representation-study/dissertation/overleaf/build/main.pdf`.

## Git commit hash

The validated source revision is committed on `supervisor-feedback-revision`; its immutable SHA is recorded in this section by the subsequent audit-record commit. The manuscript and PDF do not change during that metadata step.

Baseline/main: `6be20f7bdf9b001c765a99090439176e857ba150`.
Remote: `https://github.com/Howieu/data72000-representation-study.git`.
Only the revision branch is pushed; main is preserved.
