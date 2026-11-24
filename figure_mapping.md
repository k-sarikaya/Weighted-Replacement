# Figure and Table Mapping (v2.3.1)

This document maps every figure and table across `manuscript/manuscript.tex` and `manuscript/supplementary.tex` to its generating code, source data, and legacy `v1` counterpart.

## Main Manuscript Figures (TJEECS Limit: $\le 10$ Floats Total; Currently $3 + 6 = 9$)

| Main Label | Output Files | Description | Generator & Data Source | Change vs. v1 |
|---|---|---|---|---|
| `fig:mechanism_curves` (Figure 1) | `figures/fig1_mechanism_curves.{pdf,png}` | (a) $\gamma(\rho)$ mechanism calibration curves (Rotor $\mathrm{MF}=2.00$, HGP B/E $\mathrm{MF}=6.05$, HGP F ref.); (b) optimal age $t^*(\rho)$ and (c) naive penalty $\Delta\eta\%(\rho)$ across CT Areas 1--3 ($k/W_0=0.70, c_2/c_1=5$) | `experiments/generate_figures.py` (`generate_fig1_mechanism_curves`) | Uses $\Delta\eta\%$ notation (v2.1.2) |
| `fig:turning_point` (Figure 2) | `figures/fig2_gamma_turning_point.{pdf,png}` | E3 turning-point trajectory $t^*(\gamma)$ and $<1\%$ corrective-only gap across all four RTS-GMLC arrays inside Rotor $[4.96, 23.45]$ and HGP $[12.88, 60.90]$ envelopes | `experiments/generate_figures.py` from `results/case_E3_turning_point_curves.csv`, `case_E3_turning_point_summary.csv` | Replaces v1 `fig5_gamma_turning_point` |
| `fig:e4_heatmap` (Figure 3) | `figures/fig3_e4_consistency_heatmap.{pdf,png}` | E4 4D Policy II parameter-box heatmaps ($m^*$ over $\gamma$ vs. $c_{pen}$ at $r_{\mathrm{OM}} \in \{1.00, 1.96, 2.50\}$, $k/W_0=0.70$) for CT Areas 1 and 3 with bold symmetric neighborhood $3 \le m^* \le 5$ | `experiments/generate_figures.py` from `results/case_E4_consistency_map.csv` | Replaces v1 `fig6_e4_component_mix` (`Sav%` removed; symmetric $\pm 1$ band in v2.1) |

## Main Manuscript Tables (Ordered E1/E2 $\to$ E3 $\to$ E4 $\to$ E5 $\to$ E6)

| Main Label | Description | Data Source / Generator | Change vs. v1 / v2.0 |
|---|---|---|---|
| `tab:lit_positioning` (Table 1) | Methodological positioning relative to 15 reliability and power-system maintenance studies (adding `liu1998`, `liu2016`, `zhao2025` alongside `taghipour2015`, `jamali2022`, `hao2024`, `eryilmaz2014two`, and TJEECS studies, with aging and pre-renewal repair columns) | Curated primary literature | Expanded to 15 rows in v2.3.0 covering load-sharing PM literature |
| `tab:rts_arrays` (Table 2) | Verified IEEE RTS-GMLC CT Areas 1--3 and Coal Area 1 reliability parameters | `data/gen.csv` via `run_experiments.py` | Unchanged data values (`v1` Table 6) |
| `tab:case_e1_e2` (Table 3) | Selected E1/E2 Policy I endpoints ($k/W_0 \in \{0.50, 0.90\}$ at $c_2/c_1=5$; CT Area 1 $c_2/c_1$ sweep at $k/W_0=0.70$; plus CM savings gap column under Rotor $\rho=1.15$) | `results/case_E1_independent.csv`, `case_E2_mechanism_branches.csv` | Added `CM Gap` column (`43.11%`) in v2.3.0; completely disjoint from Table S5 |
| `tab:case_e4_summary` (Table 4) | E4 4D parameter-box consistency summary under symmetric band $3 \le m^* \le 5$ across Policy I, Policy II full box, $r_{\mathrm{OM}}$, and $c_{pen}$ slices | `results/case_E4_consistency_summary.csv`, `case_E4_consistency_map.csv` | Reordered into Section 5.3 with symmetric `3..5` band |
| `tab:case_e5` (Table 5) | Reverse-order Coal Area 1 ($\lambda_2 > \lambda_1$), rate-swapped Coal counterfactual ($\lambda_1 > \lambda_2$), and CT Areas 1--3 across $\gamma$ regimes | `results/case_E5_coal_vs_ct.csv`, `case_E5_counterfactual_attribution.csv` | Added `Coal Area 1 (Swapped)` counterfactual row |
| `tab:case_e6` (Table 6) | Representative E6 instantaneous vs. non-zero MTTR replacement duration sensitivity across continuous ($\delta=1.00$) and peaking ($\delta=0.10$) duty ($k/W_0=0.70, c_2/c_1=5$) | `results/case_E6_downtime_sensitivity.csv` | Added $\delta \in \{1.00, 0.10\}$ duty-factor reconciliation |

## Supplementary Material Figures & Tables (`manuscript/supplementary.tex`)

| Supplementary Label | Output / Source | Description | Origin / v2.1 Update |
|---|---|---|---|
| `fig:S1` (`Figure S1`) | `figures/figS1_reliability_hazard.{pdf,png}` | 3-panel synthetic benchmark ($n=15, k=15$): (a) $R_{sys}(t)$ ($m=5$), (b) early $h_{sys}(t)$ ($m=5$), and (c) late-time Regime 2 tail $h_{sys}(t)$ ($t \in [8, 37]$, $m \in \{5,6,7,8\}$) | Extended in v2.3.0 to $t \in [8, 37]$ covering full $t \in [9.7, 36.7]$ span |
| `fig:S2` (`Figure S2`) | `figures/figS2_cost_convexity.{pdf,png}` | Synthetic Policy I cost rate curves $\eta_I(t)$ | Uses $\eta_I(t)$ notation (v2.1.2) |
| `fig:S3` (`Figure S3`) | `figures/figS3_policy2_minlp.{pdf,png}` | Synthetic Policy II component-mix optimization pinned cleanly at $m^*=4$ ($\eta^* = 1.8082$) | Fixed precision tie and $\eta^*$ notation |
| `fig:S4` (`Figure S4`) | `figures/figS4_contour_sensitivity.{pdf,png}` | Synthetic 2D sensitivity contour over $(\gamma_1, \gamma_2)$ | Moved from `v1` Figure 4 |
| `tab:S1`--`tab:S4` | `results/synthetic_table2..5*.csv` | Synthetic validation Tables S1 (`S15 k=17` + `Max Rel. Err.`), S2, S3 (4-dec $\eta_{II}^*$), S4, and Algorithm S1 | Updated S1, S3, and $\eta$ notation |
| `tab:S5`--`tab:S7` | `results/case_E1..E4*.csv` | Disjoint 13-row E1/E2 grid (`S5`, with `CM Gap`), full 80-config E3 turning points (`S6`), per-area E4 box breakdown with `3..5` band (`S7`) | Table S5 made 100% disjoint from Table 3 (13 rows) in v2.3.0 |
| `tab:S8` (`Table S8`) | `results/case_E2_asymmetric_gamma.csv` | E2b asymmetric cross-branch $(\gamma_1 \neq \gamma_2)$ CT archive at $k/W_0=0.70, c_2/c_1=5, \rho=1.15$ | Assigned sequential `Table S8` in v2.1.1 |
| `tab:S9` (`Table S9`) | `results/case_E6_downtime_sensitivity.csv` | 51-row E6 MTTR downtime sensitivity ($c_d=0$) across CT Areas 1--3 ($\delta \in \{1.00, 0.10\}$, incl.\ peaking `U55` lower bounds) and Coal Area 1 ($\delta=1.00$) | Expanded to 51 rows in v2.3.0 (plus `supplemental_sensitivity_checks.csv` for priced downtime $c_d = \delta c_2 / MTTF$) |
