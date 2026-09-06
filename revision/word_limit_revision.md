# Word-limit revision — 7 September 2026

## Requirement and count

The author specified 7500 words for Chapters 1–5, excluding the abstract and other material. The supplied `DATA72000 Guidance for the Presentation of ERP Reports v1.1.pdf`, p. 2, defers the maximum to local regulations rather than giving 7500 explicitly. We apply the author's requested maximum. Page 4 requires the final count, including footnotes/endnotes, at the bottom of the contents page, not below the abstract. The separate abstract maximum is 300 words.

Chapters 1–5: 9193 → 7165 (2028 removed, leaving 335 words under 7500). Abstract: 204, excluded. Their combined 7369 was only an additional conservative check, not the required count. TeXcount includes body prose, headings, caption/table text and notes, excluding front matter, bibliography, appendix and mathematical expression counts. No material was moved to the appendix and no font reduction was used to meet the limit.

| Chapter | Before | After |
| --- | --- | --- |
| 1 Introduction | 692 | 411 |
| 2 Literature | 1157 | 646 |
| 3 Methodology | 3850 | 3608 |
| 4 Results/discussion | 3227 | 2340 |
| 5 Conclusion | 267 | 160 |

## Outline and paragraph roles

1. Introduction: population/geometry → explanation distinction → declarative research aims/contribution.
2. Literature: representation → validation → explanation designs/table → complexity guarantees → operational gap.
3. Methodology: feature construction → algorithms/metrics → complete projection and local-certificate arguments.
4. Results: benchmark → paired structure/mechanisms → explanation/operational hierarchy → diagnostics → strong, conditional and unknown findings.
5. Conclusion: same-cohort finding → explanation tradeoff → mathematical scope → bounded contribution.

Every retained paragraph contributes a definition, design choice, result, mechanism or limitation. Repeated background, feature-table paraphrases and repeated conclusions were merged. The complete methods_mathematics.tex, including Sections 3.2.3–3.2.4, is unchanged. All numeric claims covered by the audit remain, as do all tables, figures and 31 cited sources.

## Feedback and claim-evidence map

| Requirement / claim | Evidence | Status |
| --- | --- | --- |
| Purchaser-specific accessible framing | Introduction 1.1–1.3 and event-log definition 2.1 | Preserved |
| Separate explanation targets and guarantees | Literature 2.3–2.5 and comparison table | Preserved |
| Full mathematical motivation, notation, proof and boundaries | Unchanged methods_mathematics.tex | Preserved in full |
| Representation changes assignments despite repeatability | Paired labels and resampling, Section 4.2 | Supported |
| Fidelity frontier differs from provenance granularity | ExKMC/provenance outputs, Section 4.3 | Supported |
| Operational checks are distinct from business benefit | Addressability outputs and Sections 4.3/4.5 | Bounded |
| Diagnostics qualify the conclusion | Existing sensitivity outputs, Section 4.4 | Supported within tested scope |
| All 16 supervisor annotations remain addressed | Updated supervisor_feedback_audit.md | Rechecked |

## Repetition and attribution

Excess length primarily reflected repeated explanatory framing and limitations across chapters. Length does not establish copying. Attribution and all 31 active citations remain; standard mathematical results are cited and projection pruning is identified as a restatement. The condensed literature paraphrases previously audited concepts without adding quotations. No similarity-database or Turnitin scan was performed, so this is not a plagiarism clearance or similarity percentage. Mandatory declaration/copyright wording remains as specified in the presentation template.

## Five-dimension self-review

- Contribution: paired representation comparison explicit; no universal superiority claim.
- Clarity: concise definitions and transitions remain; no question-form research aims or bold typography.
- Experimental strength: positive and negative findings retained; no new experiments.
- Evaluation completeness: all diagnostics and 16 feedback resolutions remain; numeric/citation audits pass.
- Method soundness: preprocessing, selection, conditional resampling, distance-only certificate and missing-data limits remain explicit.

## Validation

Final three-pass XeLaTeX build and 38-page visual review passed. No bold fonts or overfull boxes. All 117 retained numeric checks, 31 citation keys and 817 consistency assertions passed. Entire mathematical source and all data/results are unchanged from the prior committed revision. Work remains on supervisor-feedback-revision; main is untouched.
