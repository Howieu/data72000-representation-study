# Final revision report

This report summarises the revision performed on `dissertation/overleaf/` in response to supervisor feedback, states what was and was not changed, and gives the compilation evidence that the manuscript builds cleanly after the edits. It should be read together with the four upstream audit files in this directory:

- `supervisor_feedback_audit.md` — extraction and classification of all 16 annotations found in the supervisor-annotated PDF (`14199981_DATA72000_anno_7fc4.pdf`).
- `argument_map.md` — the reconstructed claim → method → result → interpretation → limitation chain, cross-checked against `results/`.
- `terminology_audit.md` — audit of 21 technical terms for definition-before-use.
- `numerical_audit.md` — line-by-line comparison of every reported number against its source artefact.
- `evidence_gaps.md` — explicit statement that no supervisor comment requires new empirical evidence.

## 1. Scope and constraint

The task specification required that the empirical programme be **frozen**: no re-running of experiments, no new datasets, grids, metrics, or reported values, unless a reproducibility error was found. `numerical_audit.md` confirms every number in the manuscript matches its artefact in `results/`, and `evidence_gaps.md` confirms all 16 supervisor comments are resolvable through explanation, definition, motivation, and restructuring rather than new evidence. Accordingly, **no experiment was re-run and no reported value was changed.** All edits are to prose, structure, definitions, and cross-referencing.

## 2. What changed, by supervisor comment

| Comment ID | Issue | Section(s) edited | Resolution |
|---|---|---|---|
| SF-01 | "Provenance" unglossed in abstract | `abstract.tex` | Added plain-language gloss at first use. |
| SF-02 | Abstract too detailed/technical | `abstract.tex` | Removed grid-level detail (ARI ranges, "41 CLASSIX settings"); kept one headline number per finding. |
| SF-03 | Unscoped claim about "customers" | `introduction.tex` §1.1 | Scoped opening claim explicitly to the purchaser cohort. |
| SF-04 | "Provenance" unglossed (2nd instance) | `introduction.tex` §1.1 | Added precise definition at first technical use. |
| SF-05 | Ambiguous "installed" | `introduction.tex` §1.2 | Reworded to "the CLASSIX 1.5.1 implementation used in this study". |
| SF-06 | Ch.1 hard to follow | `introduction.tex` §1.2 | Rewritten with short declarative sentences and explicit signposting. |
| SF-07 | DBSCAN/Ward unexplained at first mention | `introduction.tex` §1.3 | Added one-clause parenthetical definitions; clarified these are benchmark-only methods. |
| SF-08 | ARI 0.014/0.068 read as "accuracy against ground truth" | `introduction.tex` §1.3, `methods_mathematics.tex` §3.2.3 | Added explicit statement that ARI is a partition-to-partition agreement statistic with no external ground truth for this cohort; numbers retained unchanged. |
| SF-09 | "Event logs" undefined | `literature_review.tex` | Added definition at first use. |
| SF-10 | "Neutral input" undefined | `literature_review.tex` | Added one-sentence definition of the assumption being challenged. |
| SF-11 | Table 2.1 "Timing" column unexplained | `literature_review.tex` | Added caption clause defining the column and its values. |
| SF-12 | Table 2.1 "Tuning settings" vague | `literature_review.tex` | Replaced with a specific, sourced description. |
| SF-13 | Dense paragraph on theory/software maturity | `literature_review.tex` | Rewritten in short sentences; jargon defined or replaced. |
| SF-14 | §3.2.4 (stability certificate) unmotivated | `methods_mathematics.tex` §3.2.6 | Added motivating paragraph before notation; plain-English interpretation after the proposition; explicit link to §4.4.2 and its scope limits. |
| SF-15 | "CLASSIX perturbation" undefined | `methods_mathematics.tex` §3.2.7 | Added one-sentence procedural definition before the standard-deviation grid. |
| SF-16 | Table 4.2 "Noise" undefined | `methods_mathematics.tex` §3.2.3, `paired_results.tex` Table 4.2 | Defined at first use in Ch.3; added table note in Ch.4. |

## 3. Structural and cross-cutting changes beyond the 16 comments

The task specification also asked for improvements not tied to a single highlighted comment:

1. **Mathematical scope (formerly §3.2.3–3.2.4, now §3.2.5–3.2.6).** Two new subsections were added *before* the existing hyperparameter-grid material: "What K Means computes" and "What CLASSIX computes". These give a conceptual, pre-notation account of each algorithm's objective and mechanism, so that by the time the reader reaches the projection-filtering complexity result and the local stability certificate, they already know what quantity is being filtered/certified and why it matters. This directly answers the supervisor's general complaint of "limited discussion of the mathematical workings of the algorithms".
2. **Chapter 4 restructuring.** Every results subsection (`benchmark_results.tex`, `paired_results.tex`, `explanation_results.tex`, `sensitivity_limitations.tex`) was reframed under an explicit **RESULT → MECHANISM → INTERPRETATION → LIMITATION** structure, and each subsection now opens by naming which research question(s) it answers. A new subsection, "Addressability: a stricter, distinct criterion" (`sec:addressability-hierarchy`), was added to `explanation_results.tex` to formalise a distinction that was previously implicit.
3. **Research questions made explicit.** `introduction.tex` §1.3 now states five numbered research questions (RQ1–RQ5); every Chapter 4 section and the conclusion refer back to these by number, closing the loop between motivation, method, and answer that the supervisor's "hard to follow" comments (SF-06, SF-13) implicitly diagnosed as missing.
4. **Cross-referencing.** All hardcoded references to sections, chapters, tables, and figures (e.g. "§3.2.3", "Chapter 4", "Table 4.2") were converted to LaTeX `\label`/`\ref` pairs across every `.tex` file in `sections/`. This was necessary because the new subsections shifted the numbering of everything after §3.2.2 (old §3.2.3/§3.2.4 became §3.2.5/§3.2.6), and hardcoded numbers would otherwise now be wrong throughout the document. A repository-wide check (see §4 below) confirms every `\ref` resolves and no label is multiply defined.
5. **Terminology.** Fifteen of the 21 terms flagged in `terminology_audit.md` as undefined-before-use now carry an explicit definition at first use (the remaining six were already adequately defined and required no change).

## 4. Compilation verification

The manuscript was compiled from a clean `build/` directory with `xelatex` (three sequential passes, matching this document's manual `thebibliography` bibliography style, which needs no separate `bibtex`/`biber` step):

```
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex   # pass 1
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex   # pass 2
xelatex -interaction=nonstopmode -halt-on-error -output-directory=build main.tex   # pass 3
```

Results:

- **Exit code:** `0` on all three passes.
- **Final page count:** 54 pages.
- **Warnings/errors in the final pass log:** none (`grep -n "Warning\|Error" build/pass3.log` returns no matches).
- **Unresolved cross-references:** none (`??` count across extracted PDF text is 0).
- **Duplicate labels:** none found.
- **Hardcoded section/chapter references remaining in `sections/*.tex`:** none (`\S[0-9]`, `Chapter [0-9]`, `§[0-9]` all converted to `\ref`).

One compilation defect was found and fixed during this pass: `methods_mathematics.tex` had `\citep{macqueen1967kmeans}` placed inside a display-math (`\[ ... \]`) environment for the K-Means objective, which raised `! LaTeX Error: Command \bfseries invalid in math mode.` because natbib's citation formatting is not valid inside math mode. The citation was moved to a sentence immediately following the display equation ("This is the objective originally proposed by \citet{macqueen1967kmeans}."), which is both syntactically valid and, arguably, clearer attribution than an inline citation glued to the end of an equation.

Visual spot checks (rendered at 150 dpi from the compiled PDF) confirmed: the K-Means and CLASSIX mathematics render correctly with no garbled symbols; the local stability certificate motivation paragraph (SF-14 fix) appears before any notation; Table 4.2's noise definition note (SF-16 fix) appears under the table; and the RESULT/MECHANISM/INTERPRETATION/LIMITATION labels render as intended bold run-in headings with correctly resolved `§`-references throughout Chapter 4.

## 5. What was deliberately not changed

Per the task's hard freeze on empirical results:

- No dataset, feature engineering step, clustering run, hyperparameter grid, or evaluation metric was altered or re-executed.
- No numerical value reported in the manuscript (ARI, NMI, VI, silhouette, Davies–Bouldin, Calinski–Harabasz, fidelity, cluster counts, noise counts, runtime, or perturbation results) was changed.
- The permutation control's existing, already-correct scope statement ("an existence demonstration rather than a variance decomposition") was left untouched rather than risk strengthening it during unrelated prose edits.
- Figures and tables retain their original data; only captions/notes were extended where a supervisor comment required a definition (Table 2.1, Table 4.2).

## 6. Residual risk / recommended follow-up (non-blocking)

- The dissertation's manual `thebibliography` (in `references_harvard.tex`) was not converted to `biblatex`/`biber`; this was out of scope for this revision and the existing natbib setup compiles cleanly with no missing keys, so no action is required unless the supervisor separately requests a bibliography-tooling change.
- `revision/*.md` files are process/audit artefacts for this revision cycle and are not part of the submitted dissertation; they should be excluded from the final PDF/Overleaf export if the department requires only the dissertation itself to be submitted.

## 7. Summary

All 16 extracted supervisor comments are addressed (see §2), the requested structural improvements (explicit RQs, RESULT→MECHANISM→INTERPRETATION→LIMITATION framing, pre-notation mathematical motivation) are implemented, cross-referencing is fully automated via `\label`/`\ref`, the manuscript compiles cleanly to a 54-page PDF with zero warnings or errors, and every reported empirical value is unchanged and re-verified against its source artefact. No new experiments were run, consistent with the task's constraint to freeze the empirical results.
