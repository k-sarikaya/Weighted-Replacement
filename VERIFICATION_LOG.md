# Primary-Source Verification Log

Verification Date: 2026-11-21

---

## 1.1 GE Vernova GER-3620 Rev P (2021)

- **Document:** D. Beagle, B. Moran, M. McDufford, M. Merine, *Heavy-Duty Gas Turbine Operating and Maintenance Considerations*, GER-3620 Rev P (01/21), Released Date: 2021/03/15, GE Vernova, Atlanta, GA (60 pages).
- **Primary URL:** `https://www.gevernova.com/content/dam/gepower-new/global/en_US/downloads/gas-new-site/resources/reference/GER-3620-P.pdf`
- **Access Method:** Direct PDF full-text extraction from primary URL (all 60 pages inspected).

| Item | Requirement | Status | Verified Value / Formula | Document Location |
|---|---|---|---|---|
| 1.1(a) | Factored-hours formula and definition of load factor $A_p$ | **DOĞRULANDI** | **Hours-Based HGP Inspection:** $\text{Factored Hours} = \sum_{i=1}^{n} (S_i \cdot A_{fi} \cdot A_{pi} \cdot t_i)$, $\text{Actual Hours} = \sum_{i=1}^{n} t_i$, $\text{MF} = \text{Factored Hours} / \text{Actual Hours}$, $\text{Maintenance Interval} = \text{Baseline HGPI} / \text{MF}$. $A_{pi}$ is the load severity factor for operating mode $i$: $A_p = 1.0$ up to base load; for peak load, $A_p = \exp(0.018 \, T_f)$ (B/E-class) and $A_p = \exp(0.023 \, T_f)$ (F-class), where $T_f$ is the peak firing temperature adder in $^{\circ}\text{F}$. (Hours-Based Combustion Inspection uses $\sum (K_i \cdot A_{fi} \cdot A_{pi} \cdot t_i)$ with the same $A_p$.) | Figure 10 (doc p. 7), Figure 39 (doc p. 33), Figure 41 (doc p. 34), Appendix A.1 (doc p. 39) |
| 1.1(b) | 100% peak-load rotor maintenance factor | **DOĞRULANDI** | **Hours-Based Rotor Inspection:** $\text{MF} = (H + 2P)/(H + P)$ (F-class / general) and $\text{MF} = (H + 2P + 2\text{TG})/(H + P)$ (B/E-class; turning-gear term $\text{TG}$ may be omitted if dovetails show no distress, footnote 2), where $H$ = non-peak operating hours and $P$ = peak operating hours. At 100% peak-load operation ($H = 0, P > 0$, omitting $\text{TG}$), $\text{MF}_{\text{rotor}} = 2P/P = \mathbf{2.0}$. | Figure 44 (doc p. 35 / PDF p. 40) |
| 1.1(c) | Peak firing temperature HGP maintenance factor | **DOĞRULANDI** | Figure 10 gives $A_p = \exp(0.018 \, T_f)$ (B/E-class) and $A_p = \exp(0.023 \, T_f)$ (F-class). In Appendix A.1 Example 1 (7E.03, B/E-class) at peak load with $+100^{\circ}\text{F}$ firing temperature adder ($T_f = 100^{\circ}\text{F}$), $A_p = e^{0.018 \times 100} = e^{1.8} \approx 6.05$, explicitly evaluated and rounded in the example table as **$A_p = 6$**. (For F-class at the same $T_f = 100^{\circ}\text{F}$, the Figure 10 formula yields $e^{2.3} \approx 9.97$, though no worked numerical example is printed for F-class in Appendix A.1.) | Figure 10 (doc p. 7), Appendix A.1 Example 1 (doc p. 39) |
| 1.1(d) | Below-base (part-load) maintenance factor | **DOĞRULANDI** (saat-bazlı ve start-bazlı ayrımı ile) | **Starts-based HGP criterion:** Part-load start/stop cycles ($<60\%$ load, $N_A$) have a weighting factor of **$0.5$** (i.e., $\text{MF} = \mathbf{0.5} < 1$ for pure $<60\%$ part-load starts: *"two operating cycles to maximum load levels of less than 60% would equate to one start to a load greater than 60% or, stated another way, would have a maintenance factor of 0.5"*). **Hours-based HGP/CI criteria:** $A_p = \mathbf{1.0}$ up to base load (Appendix A.1 Modes 1 & 2 list *"base or part load"* with $A_p = 1$); doc p. 7 states the Figure 10 exponential equation *"should not be used for decreases in firing temperature"*. **Rotor starts-based criterion:** Hot/warm individual start factors can be $<1$ ($0.5, 0.9$), but overall rotor MF is floored at $1.0$ (*"calculated maintenance factors less than one are not considered"*). | Section *Firing Temperatures* (doc p. 7), *Hot Gas Path Parts* & Figure 20 (doc p. 10), Figure 21 (doc p. 12 / PDF p. 18), Figures 39, 41, 42 (doc pp. 33–34), *Rotor Inspection Interval* (doc p. 35), Appendix A.1 (doc p. 39) |
| 1.1(e) | **CRITICAL:** Power output difference (MW or %) between peak rating and base rating | **DOĞRULANAMADI** | **Not explicitly stated in GER-3620 Rev P.** Full-document search confirms zero occurrences of `"MW"`, `"megawatt"`, `"peak rating"`, or `"base rating"`. Peak load is defined only via firing temperature adder ($+100^{\circ}\text{F}$ in Appendix A.1) or qualitatively as `>100% Load` (Figure 42). Figure 11 displays a schematic `% Load` axis up to `120` without numeric peak output values; Figure 12 cites `Load Ratio = 1.08 / 1.10` solely for 3% steam-injection power augmentation, not dry peak firing. **Action taken:** $\rho$ is NOT invented; $\gamma$ is parameterized across $\rho \in [1.03, 1.15]$ and $\text{MF} \in [2.0, 6.0]$ (with F-class $e^{2.3} \approx 9.97$ noted as an upper reference). | Full-text search across all 60 pages of GER-3620 Rev P |

---

## 1.2 U.S. EIA AEO 2026 Electricity Market Module Assumptions

- **Document:** U.S. Energy Information Administration (EIA), *Assumptions to the Annual Energy Outlook 2026: Electricity Market Module*, April 2026 (39 pages).
- **Primary URL:** `https://www.eia.gov/outlooks/aeo/assumptions/pdf/EMM_Assumptions.pdf`
- **Location:** **Table 3** (*Cost and performance characteristics of new central station electricity generating technologies*), document page 6 (PDF page 12); monetary units in **2025 dollars** (underlying engineering source: Sargent & Lundy, January 2024).
- **Status:** **DOĞRULANDI**

| Technology (EIA Table 3) | Size (MW) | Fixed O&M ($/kW-yr, 2025$) | Variable O&M ($/MWh, 2025$) | Base/Total Overnight Cost ($/kW, 2025$) *(noted only; NOT used for $c_1/c_2$)* | Heat Rate (Btu/kWh) |
|---|---|---|---|---|---|
| Combustion turbine — aeroderivative | 211 | **9.99** | **5.97** | 2,275 *(not used)* | 9,447 |
| Combustion turbine — industrial frame | 419 | **7.18** | **4.17** | 1,158 *(not used)* | 9,142 |

---

## 1.3 Barrows et al. (2020) — IEEE RTS-GMLC Primary Reference

- **Query:** Crossref REST API `https://api.crossref.org/works?query.title=The+IEEE+Reliability+Test+System+A+Proposed+2019+Update` and direct DOI resolution `https://api.crossref.org/works/10.1109/TPWRS.2019.2925557`.
- **Status:** **DOĞRULANDI**
- **Verified Metadata:**
  - **Authors:** Clayton Barrows, Eugene Preston, Andrea Staid, Gord Stephen, Jean-Paul Watson, Aaron Bloom, Ali Ehlen, Jussi Ikaheimo, Jennie Jorgenson, Dheepak Krishnamurthy, Jessica Lau, Brendan McBennett, Matthew O'Connell
  - **Title:** The IEEE Reliability Test System: A Proposed 2019 Update
  - **Journal:** *IEEE Transactions on Power Systems*
  - **Volume / Issue / Pages / Year:** Vol. 35, No. 1, pp. 119–127, Jan. 2020
  - **DOI:** `10.1109/TPWRS.2019.2925557`

---

## 1.4 Rushdi & Alturki (2018) — Threshold Reliability System Reference

- **Query:** Crossref REST API direct DOI lookup `https://api.crossref.org/works/10.3906/elk-1612-92`.
- **Status:** **DOĞRULANDI**
- **Verified Metadata:**
  - **Authors:** Ali Muhammad Rushdi, Alaa Mohammad Alturki
  - **Title:** Novel representations for a coherent threshold reliability system: a tale of eight signal flow graphs
  - **Journal:** *Turkish Journal of Electrical Engineering & Computer Sciences*
  - **Volume / Pages / Year:** Vol. 26, pp. 257–269, 2018
  - **DOI:** `10.3906/elk-1612-92`

---

## 1.5 RTS-GMLC `gen.csv` Internal Consistency & Regional Load Context

- **Repository:** `https://github.com/GridMod/RTS-GMLC` (branch `master`, commit `3ece0d3725c844056132393ee252b3083dd4eab4`, commit date `2025-10-23T02:33:26Z`, downloaded `2026-11-21`).
- **Local Files:** `data/gen.csv` (158 generating units) and `data/REAL_TIME_regional_Load.csv` (105,408 five-minute rows across Areas 1, 2, 3).
- **Status:** **DOĞRULANDI** (`assert abs(FOR - MTTR/(MTTF + MTTR)) < 1e-6` holds identically with zero discrepancy for all five unit groups).

| Unit Group | Area Counts (A1 / A2 / A3) | Total | PMax (MW) | MTTF (h) | MTTR (h) | Reported FOR | Computed `MTTR/(MTTF+MTTR)` | Abs. Diff |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| `U20` (Oil CT) | 4 / 4 / 4 | 12 | 20.0 | 450.0 | 50.0 | 0.100 | 0.100000 | 0.000000 |
| `U55` (NG CT) | 7 / 9 / 11 | 27 | 55.0 | 969.0 | 31.0 | 0.031 | 0.031000 | 0.000000 |
| `U76` (Coal Steam) | 4 / 3 / 0 | 7 | 76.0 | 1960.0 | 40.0 | 0.020 | 0.020000 | 0.000000 |
| `U155` (Coal Steam) | 3 / 3 / 1 | 7 | 155.0 | 960.0 | 40.0 | 0.040 | 0.040000 | 0.000000 |
| `U12` (Oil Steam) | 2 / 0 / 5 | 7 | 12.0 | 2940.0 | 60.0 | 0.020 | 0.020000 | 0.000000 |

- **Regional Peak Load (`data/REAL_TIME_regional_Load.csv`):** Area 1 max = `2850.0 MW` (min `621.30 MW`), Area 2 max = `2850.0 MW` (min `793.43 MW`), Area 3 max = `2850.0 MW` (min `911.30 MW`). Used exclusively to establish peaking/reserve-layer context (installed CT array capacity $W_0 \in \{465, 575, 685\}\text{ MW}$ represents $16.3\%\text{--}24.0\%$ of regional peak load).

---

## Summary of Unverified Items

- **Only one item could not be verified from primary sources:** **Item 1.1(e)** (explicit MW or % electrical power output difference between peak rating and base rating in GE Vernova GER-3620 Rev P). Accordingly, no point value for $\rho$ is assumed or invented; all $\gamma$ calibrations are reported parametrically along the rotor and HGP mechanism branches over $\rho \in [1.03, 1.15]$.

---

## v1 `verify_claims.py` Audit (Section 1.3 Inspection)

An inspection of the v1 `verify_claims.py` debugging sequence found:
1. **Failure 1 (Script Parser Bug):** `norm_arr` had not yet been written; `row[0].replace(' ', '_')` converted `'CT Area 1'` into `'CT_Area_1'` whereas `case_E1_independent.csv` used `'CT_Area1'`. Fixed cleanly in the parser without altering any assertion or tolerance.
2. **Failure 2 (Genuine Manuscript Data Mismatch — Caught & Fixed in Manuscript):** Comparing v1 Table 8 (`c2/c1` sensitivity for `CT_Area1`, `k/W0=0.70`) at strict tolerance `1e-6` detected four hand-typed discrepancies against `results/case_E2_calibrated_gamma.csv`:
   - `c2/c1=3, low`: manuscript had `0.014474` vs. CSV `0.015` (now `0.015000`);
   - `c2/c1=3, mid`: manuscript had `0.032204` vs. CSV `0.032207`;
   - `c2/c1=20, low`: manuscript had `0.036518` vs. CSV `0.036457`;
   - `c2/c1=20, mid`: manuscript had `0.130445` vs. CSV `0.130298`.
   **Resolution:** Zero tolerances were relaxed (`0.01` for 2-decimal hours/percentages and `1e-6` for 6-decimal cost rates remained strictly enforced); `manuscript.tex` was updated to match the exact CSV outputs, after which 605/605 assertions passed.

## Baseline Reference Update

Per author instruction, the prior unpublished thesis baseline placeholder was removed; the independent two-type baseline model and age-replacement theory are grounded in the peer-reviewed journal article Eryilmaz & Sarikaya (*Proc. IMechE Part O: J. Risk and Reliability*, 2014; DOI `10.1177/1748006X13515647`) alongside Nakagawa (*Maintenance Theory of Reliability*, Springer-Verlag, London, 2005), Wu & Chen (*IEEE Trans. Reliability*, 1994), and Eryilmaz (*Reliability Engineering & System Safety*, 2018).

---

## 1.6 Expanded Bibliography & TJEECS Bridge Verification (Crossref REST API)

All 42 references in `manuscript/refs.bib` were queried against the Crossref REST API (`https://api.crossref.org/works/`) on `2026-11-21`. Unverified issue numbers on 2013--2018 TJEECS `10.3906/elk-*` records (empty in both Crossref and OpenAlex) are omitted rather than invented:

- `eryilmaz2014two`: Eryilmaz S, Sarikaya K, *Proceedings of the Institution of Mechanical Engineers, Part O: Journal of Risk and Reliability* 2014; 228 (3): 265-271 (`10.1177/1748006X13515647`; published online Dec 31, 2013; print June 2014) — **DOĞRULANDI**.

- `fotuhi2014`: Fotuhi-Firuzabad M, Aminifar F, Shahzadeh A, *Turkish J. Electrical Engineering & Computer Sciences* 2014; 22: 1147-1158 (`10.3906/elk-1208-79`) — **DOĞRULANDI** (issue omitted as empty in Crossref/OpenAlex).
- `almuhaini2017`: Almuhaini M, Al-Sakkaf A, *Turkish J. Electrical Engineering & Computer Sciences* 2017; 25: 4657-4672 (`10.3906/elk-1609-137`) — **DOĞRULANDI** (issue omitted as empty in Crossref/OpenAlex).
- `golmohamadi2014` (`10.3906/elk-1207-69`), `heidari2016` (`10.3906/elk-1310-218`), `hashemi2013` (`10.3906/elk-1203-34`), `kumari2026` (`10.55730/1300-0632.4162`) — **DOĞRULANDI**.
- Power-system & RTS classics: `barrows2020` (`10.1109/tpwrs.2019.2925557`), `grigg1999` (`10.1109/59.780914`), `rts1979` (`10.1109/tpas.1979.319398`), `billinton1996` (`10.1007/978-1-4899-1860-4`), `billinton1994` (`10.1007/978-1-4899-1346-3`), `lisnianski2012` (`10.1016/j.ress.2011.10.008`), `ding2009` (`10.1016/j.epsr.2009.04.014`) — **DOĞRULANDI**.
- Reliability & load-sharing journal DOIs (`wu1994`, `li2008`, `eryilmaz2015mttf`, `eryilmaz2015`, `eryilmaz2018`, `eryilmaz2021`, `hamdan2021`, `hamdan2024`, `qi2024`, `qi2026`, `daniels1945`, `amari2008`, `taghipour2015`, `sharifi2023`, `che2020`, `huang2023`, `jamali2022`, `hao2024`, `ghnimi2025`, `mannai2026`, `nakagawa1985`, `nakagawa2005`, `wang2006`, `barlow1965`, `liu1998`, `liu2016`, `zhao2025`) — **DOĞRULANDI** (`kuo2003` ISBN book metadata without DOI; `zhao2025` verified against `https://api.crossref.org/works/10.1016/j.ress.2025.110855` as Zhao S, Wei Y, Cheng Y, Li Y).
- **Template binary asset note:** `journals.tubitak.gov.tr` direct HTTPS download failed TLS certificate date validation against local system clock (`2026-11-21`). `elektr.cls`, `elk-template.tex`, `elk-titlepage-template.tex`, and `elksty.tex` were obtained from the verbatim TÜBİTAK publisher mirror, and the footer badge `elk-creative.pdf` was generated locally as a vector CC BY 4.0 placeholder matching `elektr.cls` `\includegraphics[height=3.5ex]{elk-creative}`.


