# Heterogeneous Weighted $k$-out-of-$n$:G Age Replacement Under Load Sharing

Reproducible computational package and TJEECS submission bundle for **Optimal age replacement and component-mix design for heterogeneous weighted k-out-of-n:G systems under asymmetric capacity-proportional load sharing**.

## Directory Structure

```text
.
├── data/
│   ├── gen.csv                           # IEEE RTS-GMLC generating unit parameters (158 units)
│   ├── REAL_TIME_regional_Load.csv       # Regional 5-minute load time series (105,408 rows)
│   └── SOURCES.md                        # Primary URLs, commit hash, and verified SHA256 checksums
├── src/reliability_model/                # Core analytical CTMC, policy, and global-to-local optimizer modules
├── experiments/
│   ├── run_experiments.py                # Deterministic numerical experiments (synthetic + E1-E6)
│   ├── generate_figures.py               # Publication figures (vector PDF + 310 dpi PNG, Times New Roman)
│   └── verify_claims.py                  # Claim-to-CSV numeric, citation-order, and blinding audit
├── results/                              # Machine-readable CSV outputs and simulation_results.json
├── figures/                              # Generated main (fig1-3) and supplementary (figS1-S4) graphics
├── manuscript/
│   ├── tjeecs-template/                  # Official TJEECS class (elektr.cls) and style macros
│   ├── manuscript.tex / .pdf             # Blinded main manuscript (<= 15 pages, <= 10 floats)
│   ├── supplementary.tex / .pdf          # Blinded Supplementary Material (Sections S1-S4, Tables S1-S9)
│   └── refs.bib                          # Crossref-verified BibTeX database (45 entries)
├── run_all.py                            # Single-command end-to-end reproduction & checklist audit
├── SUBMISSION_CHECKLIST.md               # Auto-generated TJEECS compliance & verification report
├── VERIFICATION_LOG.md                   # Primary-source audit (GER-3620 Rev P, EIA AEO 2026, Crossref)
├── figure_mapping.md                     # Figure and table traceability across code and CSVs
├── CHANGELOG.md                          # v1 -> v2.3.1 scientific and formatting release notes
├── LICENSE                               # MIT License
└── requirements.txt                      # Exact Python dependency versions
```

## Reproduction

Tested deterministically on `Python 3.12.5` (`numpy==2.1.1`, `scipy==1.14.1`, `matplotlib==3.9.2`, `PyMuPDF==1.26.7`) with `MiKTeX-pdfTeX` (`pdflatex`):

```bash
pip install -r requirements.txt
python run_all.py
```

`run_all.py` verifies primary dataset SHA256 checksums, regenerates all experimental CSVs in `results/` (including `mc_validation_gamma_gt0.csv`, `case_E2_asymmetric_gamma.csv`, `case_E5_counterfactual_attribution.csv`, and `supplemental_sensitivity_checks.csv`), renders all figures in `figures/`, executes automated claim-to-CSV, prose-hygiene, disjoint-table, and blinding assertions via `experiments/verify_claims.py`, compiles `title_page.pdf`, `manuscript.pdf`, and `supplementary.pdf`, strips PDF metadata, and writes `SUBMISSION_CHECKLIST.md`. Because the CTMC matrix-exponential and two-stage grid-bracketed optimizer (`Algorithm S1`) are purely deterministic without pseudo-random sampling, repeated runs reproduce identical outputs byte for byte.

## License

Code and documentation are released under the MIT License (see `LICENSE`).
