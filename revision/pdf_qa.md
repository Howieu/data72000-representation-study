# Final PDF visual QA

- Final artifact: `dissertation/overleaf/build/main.pdf`.
- SHA256: `beed6d57f8186333bd19f7852318b8c6d8a1823bc07d459ced29495ceb332564`.
- 42 pages; manuscript word count 9193 (method in word_count.json), abstract 204 words.
- All 42 rendered pages inspected in seven contact sheets, with additional full-page inspection of the mathematical certificate. Earlier page-by-page inspection identified two short orphan pages; both were removed and the final 42-page build re-inspected.
- Contents pp. 2–3, lists pp. 4–5, running page numbers and chapter starts agree.
- Table 3.1 pp. 18–19 continues with a repeated header; Tables 4.1–4.2 p. 29 are within margins.
- Section 3.2.3 p. 24 and continuation p. 25; Section 3.2.4 pp. 25–27: norms, Greek symbols, subscripts, inequalities and proof endings render without clipping.
- Figures 4.1, 4.2 and 4.3 on pp. 30, 32 and 34 are readable, correctly numbered and inside margins.
- References pp. 39–41 render author names, URLs and DOI text; no unresolved citation or reference markers.
- Conclusion fits p. 38; Appendix A is p. 42. No accidental blank or two-line continuation page remains.
- Final XeLaTeX log has no fatal errors, undefined references/citations, LaTeX warnings or overfull boxes. 65 underfull box messages remain from short/ragged lines and narrow table cells; rendered inspection found no clipping or malformed content.
- Original supervisor annotations were inspected on annotated-PDF pages 6, 10–14, 21, 22 and 24; all 16 comments map to final revisions in supervisor_feedback_audit.md.

Temporary raster previews are ignored by Git. The compiled PDF is tracked under the repository's existing convention.

## Declarative phrasing follow-up (6 September 2026)

Replaced the three introductory research-question sentences and the three Section 4.5 question headings with declarative formulations. Recompiled in three passes and visually rechecked final pages 11, 36 and 37. No clipping or new build warnings; empirical results unchanged.

## Normal-weight typography follow-up (6 September 2026)

Removed bold weight throughout the dissertation, including class-generated chapter/section/paragraph and theorem headings, contents entries, cover title and caption labels. Three XeLaTeX passes succeeded. Font inspection across all 42 PDF pages found no bold fonts; regular/italic text and mathematical fonts remain. Cover and Section 4.5 were visually rechecked. Text, word count and empirical results are unchanged.
