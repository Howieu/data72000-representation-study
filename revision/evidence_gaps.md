# Evidence gaps

Final evidence audit. No unresolved gap prevents the bounded dissertation conclusion. The scope limitations below remain explicit; they are not treated as results.

| Claim / requirement | Why current evidence is insufficient | Smallest possible addition | Essential for conclusion? |
| --- | --- | --- | --- |
| Every supervisor annotation has been addressed | All 16 substantive annotations extracted, revised and visually verified | Completed: supervisor_feedback_audit.md and pdf_qa.md | Essential for feedback completion and push gate, not a new experiment |
| Proposition 3.2 certifies selected rich CLASSIX stability | Rich selection uses density merging; proposition addresses distance merging and no measured margins are established | Explicitly exclude this claim and distinguish empirical perturbation evidence | No new experiment needed for bounded conclusion |
| More aggregation groups imply harder human comprehension | No human evaluation in existing design | Remove implication; describe provenance granularity only | No |
| Addressability establishes realised business value | No intervention/outcome data | State that value and campaign effectiveness remain unknown | No |

The stated feedback concerns exposition and mathematical scope. The completed audit finds that none of the 16 comments requires new experimental evidence; they request explanation and clarification rather than a new experimental programme. No new experiment has been performed.

## Resolved unsupported runtime claims

The original benchmark paragraph claimed median selected runtimes of 0.011/0.064/0.003/0.004 seconds (CLASSIX/K Means/DBSCAN/Ward). Direct medians of `runtime_seconds_mean` in `results/benchmark/selected_label_free.csv` disagree (see numerical audit). These four claims were removed, without replacing results or rerunning timings. The smallest possible analysis is the read-only aggregation already performed. Runtime is not part of selection or the dissertation conclusion; no new experimental evidence is essential.

## Historical testing claim

The original prose asserted unit tests on hand-checked raw event histories, but no such tests are distributed in this repository. The revision instead identifies the documented feature contract and the limits of independently reconstructing raw joins. Existing paired-table values and IDs are checked directly. The original raw files were subsequently located and their hashes, reconstructed feature tables, category joins and purchaser timestamps independently checked in memory (raw_reproduction_check.json). No historical test execution is invented. This does not require an additional empirical experiment.

## Corrected reproducibility error: CLASSIX provenance row order

Version 1.5.1 `groups_` uses sorted rows, while `labels_` and `groupCenters_` refer to original input rows. The baseline exporter did not apply `inverse_ind`. Consequently 130/131 compact and 559/559 rich representative-to-group membership checks failed; 49 compact and 229 rich purported groups mixed final labels. The selected labels themselves remained correct.

The smallest correction maps saved group IDs through `inverse_ind`, reconstructs exported membership/trace/merge-membership records, and validates representative membership and label consistency. This has been done without fitting a model. Native arrays, scalers, settings, final labels and counts (131/559) remain identical to baseline. `src/provenance_alignment.py`, the exporter and five regression tests prevent recurrence. This is a reproducibility repair, not a new experiment.

## Final experiment decision

**No supervisor feedback genuinely required new experimental evidence.** The existing empirical programme, data, features, candidate grids, seeds, constraints, selection rules and model labels were retained. Read-only numerical reconstruction and deterministic mathematical/regression checks validate existing evidence; they do not produce a new customer experiment. The row-order correction above repairs only derived provenance records.
