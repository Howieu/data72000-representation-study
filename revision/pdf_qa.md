# Final PDF visual QA

Latest inspection: 7 September 2026, after word-limit condensation.

- Artifact: `dissertation/overleaf/build/main.pdf`.
- SHA256: `b34ec4aa40f7d6685f421b957fe5ba3a69c8447f4c228f8ac83abab8463a5d42`.
- 38 pages; Chapters 1–5 total 7165 words; abstract 204 (excluded). Count scope is recorded in word_count.json and word_limit_revision.md.
- All 38 rendered pages inspected in seven contact sheets; the final table-layout correction was additionally checked on pages 13–14. Cover, contents pp. 2–3, lists pp. 4–5 and page numbers agree.
- Final word count appears at the bottom of the contents on p. 3, as required by the supplied presentation guide p. 4. The guide does not require it below the abstract.
- Table 2.1 p. 13 and Table 3.1 p. 16 fit within margins. Tables 4.1–4.2 p. 27 are readable.
- Sections 3.2.3–3.2.4 pp. 21–24 retain all mathematical text from the validated prior revision. No clipped equation or missing symbol is visible.
- Figures 4.1–4.3 pp. 27/29/31 retain original graphics and numbering.
- Section 4.5 pp. 32–33 keeps declarative headings; conclusion p. 34 fits one page. References pp. 35–37 and appendix p. 38 render correctly.
- Full-document font inspection finds no bold fonts; regular/italic text and mathematical fonts remain.
- Three final XeLaTeX passes succeeded without undefined citations/references, LaTeX warnings, fatal errors or overfull boxes. 68 underfull messages were checked against rendered pages; no malformed content found.
- All 16 annotations were rechecked against final section/page anchors in supervisor_feedback_audit.md.

Temporary raster previews are ignored by Git; the compiled PDF follows the repository's existing tracked convention.
