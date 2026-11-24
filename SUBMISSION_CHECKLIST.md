# TJEECS Submission & Reproducibility Verification Checklist

Python runtime: `3.12.5`

| Check | Status | Measured Value / Evidence |
|---|---|---|
| Primary dataset SHA256 integrity | **[OK]** | gen.csv=988466f29132..., load=462888ae3572... |
| LaTeX compilation logs clean (0 errors / 0 undefined refs) | **[OK]** | issues=0 |
| Main manuscript page limit (<= 15 pages) | **[OK]** | 15 pages (title_page=0, supplementary=12) |
| Zero unresolved '??' in compiled PDFs | **[OK]** | checked main, title_page, supplementary |
| Main manuscript float limit (<= 10) | **[OK]** | 9 floats (3 figures + 6 tables) |
| Reference count (<= 60) & sequential citation order | **[OK]** | 45 references; order_match=True |
| Abstract (<= 300 words, 0 formulas, 0 citations, verbatim match) | **[OK]** | 284 words; verbatim_match=True |
| Keywords (3-6, first-word cap only, no acronyms, no period) | **[OK]** | 6 keywords |
| Title sentence case and formula-free | **[OK]** | Optimal age replacement and component-mix design for heterogeneou... |
| Double-blind anonymity (manuscript & supplementary .tex/.pdf) | **[OK]** | 0 author/affiliation/ORCID or header/title-block identity leaks |
| Public double-blind release (title page omitted) | **[OK]** | title_page omitted for peer review |
| Figures TJEECS geometry, >=118 px/cm resolution & vector PDF | **[OK]** | 7/7 validated |
| Empty PDF Author/Creator/Producer metadata on all PDFs | **[OK]** | checked all manuscript & figure PDFs |
| Zero forbidden attribution/legacy tokens in repo & git history | **[OK]** | files_clean=True, git_log_clean=True |

### Figure Geometry Summary
- `fig1_mechanism_curves:15.2x5.2cm@122px/cm`
- `fig2_gamma_turning_point:15.1x5.8cm@122px/cm`
- `fig3_e4_consistency_heatmap:15.1x8.7cm@122px/cm`
- `figS1_reliability_hazard:15.1x5.0cm@122px/cm`
- `figS2_cost_convexity:11.1x6.4cm@122px/cm`
- `figS3_policy2_minlp:12.1x6.4cm@122px/cm`
- `figS4_contour_sensitivity:11.0x7.2cm@122px/cm`
