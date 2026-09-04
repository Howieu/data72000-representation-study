# Evidence gaps

Per the task specification (§2), this file records any claim in the dissertation that cannot be supported by existing repository outputs, together with why the current evidence is insufficient, the smallest possible additional analysis, and whether it is essential to the dissertation's conclusion.

## Outcome of the review

After (i) extracting and classifying all 16 supervisor annotations (`revision/supervisor_feedback_audit.md`), (ii) reconstructing the argument chain against the primary result artefacts (`revision/argument_map.md`), and (iii) numerically auditing every reported quantity in the manuscript against `results/*.csv` and `results/thesis_summary.json` (`revision/numerical_audit.md`), **no claim was found that requires new empirical evidence.**

Specifically:

- All 16 supervisor comments are resolvable by explanation, definition, motivation, or restructuring of existing text (classifications A/B/C/D in the audit table; zero comments were classified F, "potentially requires new empirical evidence").
- Every numerical claim checked against a repository artefact matched exactly (to reported precision); no reported value is unsupported, contradicted, or fabricated.
- The one claim that risks being read as stronger than the evidence supports (SF-08: cross-representation ARI without a stated ground truth) is a **framing/explanation problem, not an evidence problem** — the ARI values are correctly computed and reported; what is missing is the sentence telling the reader what a partition-agreement statistic without ground truth does and does not mean. No new experiment can supply a "ground truth" that does not exist for this dataset; the correct fix is textual (see `revision/supervisor_feedback_audit.md`, SF-08, and `revision/terminology_audit.md`, "ARI").
- The permutation control's scope limit (it is "an existence demonstration rather than a variance decomposition") is already stated explicitly in `sensitivity_limitations.tex`. The task specification (§11) separately warns against overclaiming this control as a variance decomposition; the existing text already avoids this overclaim, so no correction or new experiment is needed here either — only vigilance during editing not to accidentally strengthen the claim while improving surrounding prose.

## Table (empty by construction)

| Claim | Why current evidence is insufficient | Smallest possible additional analysis | Essential for dissertation conclusion? |
|---|---|---|---|
| — | No claim in the current manuscript was found to lack adequate existing support. | — | — |

## Explicit statement for the Section 20 decision gate

**Did any supervisor feedback genuinely require new experimental evidence? No.**

All sixteen extracted annotations concern readability, terminology, mathematical motivation, and the correct interpretation of already-computed, already-verified results. None asks for a different dataset, a different grid, a different metric, or a different reported number. The existing empirical programme (benchmark, paired clustering, resampling stability, CLASSIX provenance, ExKMC fidelity, addressability audit, and the five sensitivity/robustness analyses) is retained in full and unmodified. This is consistent with the hard freeze in task specification §2, and is the expected outcome given that the supervisor's own annotations (per `revision/supervisor_feedback_audit.md`) target exposition, not methodology.
