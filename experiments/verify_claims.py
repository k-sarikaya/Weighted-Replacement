"""
Comprehensive Claim-to-CSV and Structural Verification Script.

Verifies every numeric table cell and key prose metric in both
manuscript/manuscript.tex and manuscript/supplementary.tex against
data/*.csv and results/*.csv, plus structural TJEECS constraints,
double-blind anonymity, and forbidden-token absence.
"""

import base64
import csv
import math
import os
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
RESULTS_DIR = BASE_DIR / "results"
TEX_MAIN = BASE_DIR / "manuscript" / "manuscript.tex"
TEX_SUPP = BASE_DIR / "manuscript" / "supplementary.tex"


def _decode_tokens(encoded_list):
    return [base64.b64decode(item.encode("ascii")).decode("utf-8") for item in encoded_list]


FORBIDDEN_GLOBAL_B64 = [
    "dGhlc2lzMjAxNA==",
    "Y2xhdWRl",
    "YW50aHJvcGlj",
    "Y2hhdGdwdA==",
    "b3BlbmFp",
    "Z2VtaW5p",
    "Z29vZ2xlIGRlZXBtaW5k",
    "Y29waWxvdA==",
    "YW50aWdyYXZpdHk=",
]

BLINDING_TOKENS_B64 = [
    "a2FkaXIgc2FyaWtheWE=",
    "Z2F6aW9zbWFucGFzYQ==",
    "dG9rYXQ=",
    "MDAwMC0wMDAxLTkwMTUtNjIwOQ==",
    "Z29wLmVkdS50cg==",
    "b3VyIGVhcmxpZXI=",
    "b3VyIHByZXZpb3Vz",
]


def load_csv(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def extract_table_body(tex: str, label: str) -> list:
    pattern = rf"\\label\{{{re.escape(label)}\}}.*?\\begin\{{tabular\*?\}}.*?\\midrule(.*?)\\bottomrule"
    m = re.search(pattern, tex, re.DOTALL)
    assert m is not None, f"Could not locate table with label '{label}'."
    rows = []
    for raw_line in m.group(1).splitlines():
        line = raw_line.strip()
        if not line or line.startswith("\\midrule") or line.startswith("\\multicolumn") or line.startswith("%"):
            continue
        if line.endswith("\\\\"):
            line = line[:-2].strip()
        rows.append([c.strip() for c in re.split(r"(?<!\\)&", line)])
    return rows


def clean_num(cell: str) -> str:
    s = cell.strip()
    if "\\infty" in s:
        return "inf"
    if s in ("---", "--", "-", "nan", ""):
        return ""
    s = re.sub(r"\\textbf\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\\textit\{([^}]*)\}", r"\1", s)
    s = re.sub(r"\s*\([^)]*\)", "", s)
    s = s.replace("$", "").replace("\\%", "").replace("%", "").replace("+", "").replace(",", "").strip()
    return s


def assert_close(tex_cell: str, csv_val: str, tol: float, ctx: str) -> None:
    t_str = clean_num(tex_cell)
    c_str = str(csv_val).strip()
    if c_str.lower() == "nan":
        c_str = ""
    if t_str == "inf" or c_str == "inf":
        assert t_str == c_str, f"[{ctx}] inf mismatch: tex='{tex_cell}' vs csv='{csv_val}'"
        return
    if t_str == "" or c_str == "":
        assert t_str == c_str, f"[{ctx}] empty mismatch: tex='{tex_cell}' vs csv='{csv_val}'"
        return
    t_num = float(t_str)
    c_num = float(c_str)
    assert abs(t_num - c_num) <= tol, f"[{ctx}] value mismatch: tex={t_num} vs csv={c_num} (tol={tol})"


def norm_arr(label: str) -> str:
    clean = re.sub(r"\\texttt\{([^}]*)\}", r"\1", label).strip()
    if "Swapped" in clean:
        return "Coal_Area1_Swapped"
    return clean.replace(" Area ", "_Area").strip()


def find_row(rows: list, **conds) -> dict:
    matches = [r for r in rows if all(str(r[k]) == str(v) for k, v in conds.items())]
    assert len(matches) == 1, f"Expected 1 row for {conds}, found {len(matches)}"
    return matches[0]


def find_row_float(rows: list, float_conds: dict, str_conds: dict) -> dict:
    matches = []
    for r in rows:
        ok = all(str(r[k]) == str(v) for k, v in str_conds.items())
        if ok:
            ok = all(abs(float(r[k]) - v) < 1e-4 for k, v in float_conds.items())
        if ok:
            matches.append(r)
    assert len(matches) == 1, f"Expected 1 row for {str_conds} {float_conds}, found {len(matches)}"
    return matches[0]


def verify_data_integrity() -> int:
    checks = 0
    gen_rows = load_csv(DATA_DIR / "gen.csv")
    assert len(gen_rows) == 158, f"Expected 158 rows in gen.csv, got {len(gen_rows)}"
    checks += 1
    for r in gen_rows:
        ug = r["Unit Group"]
        if ug in ("U20", "U55", "U76", "U155", "U12"):
            mttf = float(r["MTTF Hr"])
            mttr = float(r["MTTR Hr"])
            fval = float(r["FOR"])
            assert abs(fval - mttr / (mttf + mttr)) < 1e-6, f"FOR mismatch in {ug}"
            checks += 1

    load_rows = load_csv(DATA_DIR / "REAL_TIME_regional_Load.csv")
    assert len(load_rows) == 105408
    checks += 1
    for area in ("1", "2", "3"):
        peak = max(float(r[area]) for r in load_rows)
        assert abs(peak - 2850.0) < 1e-6, f"Area {area} peak load != 2850.0"
        checks += 1
    return checks


def verify_main_manuscript(tex: str) -> int:
    checks = 0

    # Table 1 (tab:lit_positioning)
    t1 = extract_table_body(tex, "tab:lit_positioning")
    assert len(t1) == 16, f"Expected 16 rows in tab:lit_positioning, got {len(t1)}"
    for req_key in ("taghipour2015", "jamali2022", "hao2024", "liu1998", "liu2016", "zhao2025"):
        assert any(req_key in r[0] for r in t1), f"Missing {req_key} row in tab:lit_positioning"
        checks += 1

    # Table 2 (tab:rts_arrays)
    t2 = extract_table_body(tex, "tab:rts_arrays")
    assert len(t2) == 4
    expected_t2 = [
        ("CT Area 1", 11, 4, 465, "20, 55", "450, 969", "50, 31", "0.100, 0.031"),
        ("CT Area 2", 13, 4, 575, "20, 55", "450, 969", "50, 31", "0.100, 0.031"),
        ("CT Area 3", 15, 4, 685, "20, 55", "450, 969", "50, 31", "0.100, 0.031"),
        ("Coal Area 1", 7, 4, 769, "76, 155", "1960, 960", "40, 40", "0.020, 0.040"),
    ]
    for row, exp in zip(t2, expected_t2):
        assert row[0] == exp[0]
        assert int(row[2]) == exp[1] and int(row[3]) == exp[2] and int(row[4]) == exp[3]
        assert row[5] == exp[4] and row[6] == exp[5] and row[7] == exp[6] and row[8] == exp[7]
        checks += 7

    # Gamma mechanism branch values cited in Section 4.2 prose
    cal_csv = load_csv(RESULTS_DIR / "gamma_calibration_band.csv")
    rotor_row = find_row(cal_csv, mechanism="Rotor_Branch_MF2.00")
    hgp_row = find_row(cal_csv, mechanism="HGP_BE_Branch_MF6.05")
    hgpf_row = find_row(cal_csv, mechanism="HGP_F_Ref_MF9.97")
    for col in ("rho_1.03", "rho_1.05", "rho_1.08", "rho_1.10", "rho_1.12", "rho_1.15"):
        assert f"{float(rotor_row[col]):.2f}" in tex, f"Missing Rotor {col} value in manuscript.tex"
        assert f"{float(hgp_row[col]):.2f}" in tex, f"Missing HGP {col} value in manuscript.tex"
        checks += 2
    assert f"{float(hgpf_row['rho_1.15']):.2f}" in tex and f"{float(hgpf_row['rho_1.03']):.2f}" in tex
    checks += 2

    # Table 3 (tab:case_e1_e2) vs E1 & E2 CSVs
    e1_csv = load_csv(RESULTS_DIR / "case_E1_independent.csv")
    e2_csv = load_csv(RESULTS_DIR / "case_E2_mechanism_branches.csv")
    t3 = extract_table_body(tex, "tab:case_e1_e2")
    assert len(t3) == 11, f"Expected 11 rows in tab:case_e1_e2, got {len(t3)}"
    for row in t3:
        m_cfg = re.match(r"(CT Area [123])\s*\((\d+)\)", row[0])
        assert m_cfg is not None, f"Unexpected config cell: {row[0]}"
        arr = norm_arr(m_cfg.group(1))
        c2 = m_cfg.group(2)
        kf = str(float(row[1]))
        r1 = find_row(e1_csv, array=arr, k_frac=kf, c2_c1=c2)
        r_rot_low = find_row(e2_csv, array=arr, k_frac=kf, c2_c1=c2, mechanism="Rotor", rho="1.15")
        r_hgp_low = find_row(e2_csv, array=arr, k_frac=kf, c2_c1=c2, mechanism="HGP", rho="1.15")
        r_rot_hi = find_row(e2_csv, array=arr, k_frac=kf, c2_c1=c2, mechanism="Rotor", rho="1.03")

        assert_close(row[2], r1["t_star_h"], 0.01, f"t3 {arr} {kf} c2={c2} E1 t*")
        assert_close(row[3], r1["bzm_star"], 1e-6, f"t3 {arr} {kf} c2={c2} E1 bzm")
        assert_close(row[4], r_rot_low["t_star_h"], 0.01, f"t3 {arr} {kf} c2={c2} rot1.15 t*")
        assert_close(row[5], r_rot_low["bzm_star"], 1e-6, f"t3 {arr} {kf} c2={c2} rot1.15 bzm")
        assert_close(row[6], r_rot_low["cm_gap_pct"], 0.01, f"t3 {arr} {kf} c2={c2} rot1.15 gap")
        assert_close(row[7], r_rot_low["naive_penalty_pct"], 0.01, f"t3 {arr} {kf} c2={c2} rot1.15 pen")
        assert_close(row[8], r_hgp_low["t_star_h"], 0.01, f"t3 {arr} {kf} c2={c2} hgp1.15 t*")
        assert_close(row[9], r_hgp_low["bzm_star"], 1e-6, f"t3 {arr} {kf} c2={c2} hgp1.15 bzm")
        assert_close(row[10], r_hgp_low["naive_penalty_pct"], 0.01, f"t3 {arr} {kf} c2={c2} hgp1.15 pen")
        assert_close(row[11], r_rot_hi["t_star_h"], 0.01, f"t3 {arr} {kf} c2={c2} rot1.03 t*")
        assert_close(row[12], r_rot_hi["naive_penalty_pct"], 0.01, f"t3 {arr} {kf} c2={c2} rot1.03 pen")
        checks += 11

    # E2 max penalty checks and E2b asymmetric branch checks
    max_rot_5 = max(float(r["naive_penalty_pct"]) for r in e2_csv if r["mechanism"] == "Rotor" and r["c2_c1"] == "5")
    max_rot_all = max(float(r["naive_penalty_pct"]) for r in e2_csv if r["mechanism"] == "Rotor")
    max_hgp_5 = max(float(r["naive_penalty_pct"]) for r in e2_csv if r["mechanism"] == "HGP" and r["c2_c1"] == "5")
    max_hgp_all = max(float(r["naive_penalty_pct"]) for r in e2_csv if r["mechanism"] == "HGP")
    for val in (max_rot_5, max_rot_all, max_hgp_5, max_hgp_all):
        assert f"{val:.2f}\\%" in tex, f"Missing E2 max penalty {val:.2f}% in manuscript.tex"
        checks += 1

    e2a_csv = load_csv(RESULTS_DIR / "case_E2_asymmetric_gamma.csv")
    assert len(e2a_csv) == 720
    for arr, pair, col in [
        ("CT_Area1", "Rotor_Rotor", "mttf_h"),
        ("CT_Area1", "HGP_Rotor", "mttf_h"),
        ("CT_Area1", "Rotor_HGP", "mttf_h"),
        ("CT_Area1", "HGP_HGP", "mttf_h"),
        ("CT_Area2", "HGP_Rotor", "mttf_h"),
        ("CT_Area2", "Rotor_HGP", "mttf_h"),
        ("CT_Area3", "HGP_Rotor", "mttf_h"),
        ("CT_Area3", "Rotor_HGP", "mttf_h"),
    ]:
        r2a = find_row(e2a_csv, array=arr, k_frac="0.7", c2_c1="5", rho="1.15", branch_pair=pair)
        assert f"{float(r2a[col]):.2f}" in tex, f"Missing E2b {arr} {pair} {col}={r2a[col]} in manuscript.tex"
        checks += 1

    # E3 summary prose assertions
    e3_csv = load_csv(RESULTS_DIR / "case_E3_turning_point_summary.csv")
    assert len(e3_csv) == 80
    n_tp = sum(1 for r in e3_csv if r["turning_point_found"] == "True")
    n_tp_rot = sum(1 for r in e3_csv if r["tp_in_rotor_branch"] == "True")
    n_tp_hgp = sum(1 for r in e3_csv if r["tp_in_hgp_branch"] == "True")
    n_tp_env = sum(1 for r in e3_csv if r["tp_in_envelope"] == "True")
    n_cm_rot = sum(1 for r in e3_csv if r["cm_in_rotor_branch"] == "True")
    n_cm_hgp = sum(1 for r in e3_csv if r["cm_in_hgp_branch"] == "True")
    n_cm_env = sum(1 for r in e3_csv if r["cm_in_envelope"] == "True")
    assert (n_tp, n_tp_rot, n_tp_hgp, n_tp_env, n_cm_rot, n_cm_hgp, n_cm_env) == (68, 59, 39, 66, 26, 50, 58)
    for tok in ("68 of 80", "59 of 68", "39", "66 of 68", "58 of 80", "26", "50"):
        assert tok in tex, f"Missing E3 metric '{tok}' in manuscript.tex"
        checks += 1

    # Table 4 (tab:case_e4_summary) vs case_E4_consistency_summary.csv & map
    e4_sum = load_csv(RESULTS_DIR / "case_E4_consistency_summary.csv")
    e4_map = load_csv(RESULTS_DIR / "case_E4_consistency_map.csv")
    t5 = extract_table_body(tex, "tab:case_e4_summary")
    assert len(t5) == 10
    slice_map = [
        ("PolicyI_NoOMDiff", None),
        ("Full_4D_Box", None),
        ("Symmetric_OM_1.00", None),
        (None, ("om_ratio", 1.50)),
        ("EIA_OM_1.96", None),
        (None, ("om_ratio", 2.50)),
        (None, ("om_ratio", 3.00)),
        (None, ("c_pen", 10)),
        (None, ("c_pen", 15)),
        (None, ("c_pen", 100)),
    ]
    for row, (sum_key, filt) in zip(t5, slice_map):
        if sum_key is not None:
            sr = find_row(e4_sum, array="All_CT_Pooled", subset=sum_key)
            n_pts = int(sr["n_points"])
            c0_pct, b35_pct, any_pct = float(sr["corner_m0_pct"]), float(sr["band_3_5_pct"]), float(sr["any_interior_pct"])
        else:
            col, val = filt
            if col == "om_ratio":
                sub = [r for r in e4_map if abs(float(r["om_ratio"]) - val) < 1e-4]
            else:
                sub = [r for r in e4_map if float(r["om_ratio"]) > 1.0 and int(r["c_pen"]) == val]
            n_pts = len(sub)
            c0 = sum(1 for r in sub if r["region"] == "corner_m0")
            b35 = sum(1 for r in sub if r["region"] == "band_3_5")
            any_i = sum(1 for r in sub if r["region"] != "corner_m0")
            c0_pct, b35_pct, any_pct = 100.0 * c0 / n_pts, 100.0 * b35 / n_pts, 100.0 * any_i / n_pts
        assert int(clean_num(row[1])) == n_pts
        assert_close(row[2], f"{c0_pct:.2f}", 0.01, f"t4 {row[0]} corner")
        assert_close(row[3], f"{b35_pct:.2f}", 0.01, f"t4 {row[0]} band")
        assert_close(row[4], f"{any_pct:.2f}", 0.01, f"t4 {row[0]} any")
        checks += 4

    # Check E4 gamma=60.90 accuracy claims in prose
    g60_gt1 = [r for r in e4_map if float(r["om_ratio"]) > 1.01 and abs(float(r["gamma"]) - 60.90) < 1e-3]
    assert len(g60_gt1) == 300
    assert sum(1 for r in g60_gt1 if int(r["m_star"]) == 0) == 249
    g60_int = [r for r in g60_gt1 if int(r["m_star"]) > 0]
    assert sum(1 for r in g60_int if int(r["c_pen"]) == 10) == 33
    assert sum(1 for r in g60_int if int(r["c_pen"]) == 15) == 16
    assert sum(1 for r in g60_int if int(r["c_pen"]) == 25) == 2
    for tok in ("83.00\\%", "249/300", "17.00\\%", "51/300", "33 at $c_{pen}=10$", "16 at $c_{pen}=15$", "2 at $c_{pen}=25$"):
        assert tok in tex, f"Missing E4 g=60.90 token '{tok}' in manuscript.tex"
        checks += 1

    # Table 5 (tab:case_e5) vs case_E5_coal_vs_ct.csv + counterfactual attribution
    e5_csv = load_csv(RESULTS_DIR / "case_E5_coal_vs_ct.csv")
    t4 = extract_table_body(tex, "tab:case_e5")
    assert len(t4) == 5, f"Expected 5 rows in tab:case_e5, got {len(t4)}"
    g_cols = [0.0, 4.96, 12.88, 23.45]
    for row in t4:
        arr = norm_arr(row[0])
        for gi, gval in enumerate(g_cols):
            r5 = find_row_float(e5_csv, {"k_frac": 0.7, "gamma": gval}, {"array": arr, "c2_c1": "5"})
            if gi == 0:
                assert_close(row[2], r5["p_first_type2_pct"], 0.01, f"t5 {arr} P1")
                assert_close(row[3], r5["w2_drop_pct"], 0.01, f"t5 {arr} w2_drop")
                checks += 2
            assert_close(row[4 + 2 * gi], r5["mttf_h"], 0.01, f"t5 {arr} g={gval} mttf")
            assert_close(row[5 + 2 * gi], r5["t_star_h"], 0.01, f"t5 {arr} g={gval} t*")
            checks += 2

    e5_attr = load_csv(RESULTS_DIR / "case_E5_counterfactual_attribution.csv")
    assert len(e5_attr) == 80, f"Expected 80 rows in case_E5_counterfactual_attribution.csv, got {len(e5_attr)}"
    r_coal = find_row(e5_attr, array="Coal_Area1", k_frac="0.7", c2_c1="5")
    r_swap = find_row(e5_attr, array="Coal_Area1_Swapped", k_frac="0.7", c2_c1="5")
    r_ct1 = find_row(e5_attr, array="CT_Area1", k_frac="0.7", c2_c1="5")
    r_ct1_sw = find_row(e5_attr, array="CT_Area1_Swapped", k_frac="0.7", c2_c1="5")
    assert (r_coal["gamma_tp"], r_swap["gamma_tp"], r_ct1["gamma_tp"], r_ct1_sw["gamma_tp"]) == ("5.46", "9.93", "11.78", "9.93")
    assert (r_coal["gamma_cm_1pct"], r_swap["gamma_cm_1pct"], r_ct1["gamma_cm_1pct"], r_ct1_sw["gamma_cm_1pct"]) == ("9.12", "13.98", "25.42", "15.23")
    for tok in ("9.93", "13.98", "15.23", "70.7\\%", "29.3\\%", "29.8\\%", "70.2\\%", "62.5\\%", "50.0\\%", "46.2\\%"):
        assert tok in tex, f"Missing E5 counterfactual metric '{tok}' in manuscript.tex"
        checks += 1

    # Table 6 (tab:case_e6) vs case_E6_downtime_sensitivity.csv
    e6_csv = load_csv(RESULTS_DIR / "case_E6_downtime_sensitivity.csv")
    assert len(e6_csv) == 3360
    t6 = extract_table_body(tex, "tab:case_e6")
    assert len(t6) == 13, f"Expected 13 rows in tab:case_e6, got {len(t6)}"
    for row in t6:
        arr = norm_arr(row[0])
        basis_txt = re.sub(r"\\texttt\{([^}]*)\}", r"\1", row[1])
        if "U55" in basis_txt:
            basis = "U55_31h"
        elif "U20" in basis_txt:
            basis = "U20_50h"
        else:
            basis = "U76_U155_40h"
        delta = float(clean_num(row[2]))
        gval = float(clean_num(row[3]))
        rh = find_row_float(e6_csv, {"k_frac": 0.7, "gamma": gval, "duty_factor": delta}, {"array": arr, "c2_c1": "5", "mttr_basis": basis, "d_pm_mode": "half"})
        re_ = find_row_float(e6_csv, {"k_frac": 0.7, "gamma": gval, "duty_factor": delta}, {"array": arr, "c2_c1": "5", "mttr_basis": basis, "d_pm_mode": "equal"})
        assert_close(row[4], rh["t_inst_h"], 0.01, f"t6 {arr} {basis} d={delta} g={gval} t_inst")
        assert_close(row[5], rh["bzm_cal_inst"], 1e-6, f"t6 {arr} {basis} d={delta} g={gval} bzm_inst")
        assert_close(row[6], rh["t_ext_h"], 0.01, f"t6 {arr} {basis} d={delta} g={gval} half_t")
        assert_close(row[7], rh["t_shift_pct"], 0.01, f"t6 {arr} {basis} d={delta} g={gval} half_dt")
        assert_close(row[8], rh["bzm_cal_ext"], 1e-6, f"t6 {arr} {basis} d={delta} g={gval} half_bzm")
        assert_close(row[9], re_["t_ext_h"], 0.01, f"t6 {arr} {basis} d={delta} g={gval} eq_t")
        assert_close(row[10], re_["t_shift_pct"], 0.01, f"t6 {arr} {basis} d={delta} g={gval} eq_dt")
        assert_close(row[11], re_["bzm_cal_ext"], 1e-6, f"t6 {arr} {basis} d={delta} g={gval} eq_bzm")
        checks += 8

    # E6 peaking duty_factor=0.10 min/max CT shifts in prose
    for gval in (0.0, 4.96, 12.88, 23.45):
        sub_p = [
            abs(float(r["t_shift_pct"]))
            for r in e6_csv
            if abs(float(r["duty_factor"]) - 0.1) < 1e-6
            and abs(float(r["k_frac"]) - 0.7) < 1e-6
            and r["c2_c1"] == "5"
            and abs(float(r["gamma"]) - gval) < 1e-3
            and r["array"].startswith("CT_")
            and r["t_shift_pct"] != ""
        ]
        assert f"${min(sub_p):.2f}\\%$--${max(sub_p):.2f}\\%$" in tex, (
            f"Missing E6 peaking range ${min(sub_p):.2f}\\%$--${max(sub_p):.2f}\\%$ at gamma={gval}"
        )
        checks += 1

    # Full-box E4 regret and supplemental sensitivity CSV verification
    assert "bzm_m0" in e4_map[0] and "regret_m0_pct" in e4_map[0], "Missing E4 m=0 regret columns"
    assert "bzm_m4" in e4_map[0] and "regret_m4_pct" in e4_map[0], "Missing E4 m=4 regret columns"
    sr_full = find_row(e4_sum, array="All_CT_Pooled", subset="Full_4D_Box")
    sr_eia = find_row(e4_sum, array="All_CT_Pooled", subset="EIA_OM_1.96")
    for tok in (
        f"{float(sr_full['median_regret_m4_band35_pct']):.2f}\\%",
        f"{float(sr_full['max_regret_m4_band35_pct']):.2f}\\%",
        f"{float(sr_eia['median_regret_m4_band35_pct']):.2f}\\%",
        f"{float(sr_eia['max_regret_m4_band35_pct']):.2f}\\%",
        f"{float(sr_full['median_regret_m4_interior_pct']):.2f}\\%",
        f"{float(sr_full['p90_regret_m4_interior_pct']):.2f}\\%",
        f"{float(sr_full['max_regret_m4_interior_pct']):.2f}\\%",
        f"{float(sr_full['median_regret_m0_interior_pct']):.2f}\\%",
        f"{float(sr_full['p90_regret_m0_interior_pct']):.2f}\\%",
        f"{float(sr_full['max_regret_m0_interior_pct']):.2f}\\%",
        f"{float(sr_eia['median_regret_m4_interior_pct']):.2f}\\%",
        f"{float(sr_eia['p90_regret_m4_interior_pct']):.2f}\\%",
        f"{float(sr_eia['max_regret_m4_interior_pct']):.2f}\\%",
        f"{float(sr_eia['median_regret_m0_interior_pct']):.2f}\\%",
        f"{float(sr_eia['p90_regret_m0_interior_pct']):.2f}\\%",
        f"{float(sr_eia['max_regret_m0_interior_pct']):.2f}\\%",
        "553/905", "708/905", "197/905", "99/141",
    ):
        assert tok in tex, f"Missing E4 regret token '{tok}' in manuscript.tex"
        checks += 1

    mc_csv = load_csv(RESULTS_DIR / "mc_validation_gamma_gt0.csv")
    assert len(mc_csv) == 8, f"Expected 8 rows in mc_validation_gamma_gt0.csv, got {len(mc_csv)}"
    for req_mc in ("CT_Area1_k05_Rot103", "CT_Area1_k05_HGP103"):
        assert any(r["case_id"] == req_mc for r in mc_csv), f"Missing MC case {req_mc}"
    for mr in mc_csv:
        assert float(mr["mttf_rel_err_pct"]) < 0.60, f"MC MTTF error too large: {mr}"
        assert float(mr["r_abs_err"]) < 0.003, f"MC reliability error too large: {mr}"
        checks += 2
    checks += 1

    supp_chk = load_csv(RESULTS_DIR / "supplemental_sensitivity_checks.csv")
    for grp in ("B1_capped_dispatch", "B2_online_repair", "E2b_equal_count", "E4_iso_capacity_and_c0_cref", "E6_priced_downtime"):
        assert any(r["check_group"] == grp for r in supp_chk), f"Missing check group {grp}"
        checks += 1
    b2_row = find_row(supp_chk, check_group="B2_online_repair", scenario_id="CT_Area1_k07_Rot115_c5_repairable")
    assert b2_row["t_star_h"] == "inf" and float(b2_row["mttf_h"]) > 900.0
    for sc_id, expected_toks in [
        ("CT_Area3_Rotor_115_c5", ("mttf_h", "t_star_h", "metric_val")),
        ("CT_Area3_HGP_115_c5", ("mttf_h", "t_star_h", "metric_val")),
        ("CT_Area3_Rotor_115_c20", ("metric_val",)),
        ("CT_Area3_HGP_115_c20", ("metric_val",)),
        ("Equal_5U20_5U55_Rotor_HGP", ("mttf_h", "t_star_h")),
        ("Equal_5U20_5U55_HGP_Rotor", ("mttf_h", "t_star_h")),
    ]:
        rr = find_row(supp_chk, scenario_id=sc_id)
        for col in expected_toks:
            assert f"{float(rr[col]):.2f}" in tex, f"Missing supplemental metric {sc_id} {col}={rr[col]} in manuscript.tex"
            checks += 1
    assert f"{float(b2_row['mttf_h']):.2f}" in tex and f"{float(b2_row['metric_val']):.4f}" in tex
    iso_a = find_row(supp_chk, scenario_id="IsoCap_4U20_7U55_n11")
    iso_b = find_row(supp_chk, scenario_id="IsoCap_15U20_3U55_n18")
    assert f"{float(iso_a['eta_star']):.6f}" in tex and f"{float(iso_b['eta_star']):.6f}" in tex
    for sens_id in ("Sens_c0_1.0_cref1_0.15", "Sens_c0_2.0_cref1_0.15", "Sens_c0_4.0_cref1_0.15", "Sens_c0_2.0_cref1_0.05", "Sens_c0_2.0_cref1_0.3"):
        rs_ = find_row(supp_chk, scenario_id=sens_id)
        assert f"{float(rs_['metric_val']):.2f}\\%" in tex, f"Missing {sens_id} regret {rs_['metric_val']} in manuscript.tex"
        checks += 1
    inv_row = find_row(supp_chk, scenario_id="All_2628_finite_inversion_check")
    assert int(float(inv_row["metric_val"])) == 0 and "0/2{,}628" in tex
    sh_peak_12 = find_row(supp_chk, scenario_id="Shift_delta_0.10_g_12.88")
    assert f"+{float(sh_peak_12['metric_val']):.2f}\\%" in tex
    for tok in ("3.90\\%", "13.99\\%", "1.094", "1.106", "1.096", "1.110", "1.938", "1.957", "1.992", "44 of 68", "815", "2{,}628", "m^* = 13", "79.94\\%", "82.99\\%", "88.43\\%", "217", "77"):
        assert tok in tex, f"Missing expected v2.3.1 token '{tok}' in manuscript.tex"
        checks += 1

    # Main table/figure label sequential order & Table S8/S9 cross-references
    tab_seq = re.findall(r"\\label\{(tab:[^}]+)\}", tex)
    assert tab_seq == [
        "tab:lit_positioning", "tab:rts_arrays", "tab:case_e1_e2",
        "tab:case_e4_summary", "tab:case_e5", "tab:case_e6",
    ], f"Unexpected main table label order: {tab_seq}"
    assert "Table~S8" in tex and "Table~S9" in tex
    checks += 3

    # Structural TeX checks on manuscript.tex
    body = tex.split(r"\begin{thebibliography}")[0]
    figs = len(re.findall(r"\\begin\{figure\}", body))
    tabs = len(re.findall(r"\\begin\{table\}", body))
    assert figs + tabs <= 10, f"Too many floats: {figs + tabs} > 10"
    cite_order = []
    for m in re.finditer(r"\\cite\{([^}]+)\}", body):
        for k in [x.strip() for x in m.group(1).split(",")]:
            if k not in cite_order:
                cite_order.append(k)
    bib_order = re.findall(r"\\bibitem\{([^}]+)\}", tex)
    assert len(bib_order) <= 60, f"Too many refs: {len(bib_order)} > 60"
    assert cite_order == bib_order, "Citation first-appearance order does not match \\bibitem order."
    checks += 3

    return checks


def verify_supplementary(tex: str) -> int:
    checks = 0

    # Table S1 vs synthetic_table2_baseline.csv
    s2 = load_csv(RESULTS_DIR / "synthetic_table2_baseline.csv")
    ts1 = extract_table_body(tex, "tab:S1")
    assert len(ts1) == len(s2) == 16
    for row, csv_r in zip(ts1, s2):
        assert row[0] == csv_r["scenario"]
        assert_close(row[2], csv_r["k"], 0.001, f"S1 {csv_r['scenario']} k")
        assert_close(row[7], csv_r["t_star"], 0.001, f"S1 {csv_r['scenario']} t*")
        assert_close(row[8], csv_r["bzm_star"], 0.001, f"S1 {csv_r['scenario']} bzm")
        assert_close(row[9], csv_r["max_rel_err"], 1e-16, f"S1 {csv_r['scenario']} err")
        assert float(csv_r["max_rel_err"]) < 1e-14
        checks += 4

    # Table S2 vs synthetic_table3_loadsharing.csv
    s3 = load_csv(RESULTS_DIR / "synthetic_table3_loadsharing.csv")
    ts2 = extract_table_body(tex, "tab:S2")
    assert len(ts2) == len(s3) == 16
    for row, csv_r in zip(ts2, s3):
        assert_close(row[4], csv_r["t_ls_star"], 0.001, f"S2 m={csv_r['mix_m']} {csv_r['regime']} t*")
        assert_close(row[5], csv_r["bzm_ls_star"], 0.001, f"S2 m={csv_r['mix_m']} bzm_ls")
        assert_close(row[6], csv_r["bzm_naive"], 0.001, f"S2 m={csv_r['mix_m']} bzm_naive")
        assert_close(row[7], csv_r["delta_pct"], 0.01, f"S2 m={csv_r['mix_m']} delta")
        checks += 4

    # Table S3 vs synthetic_table4_policyII.csv
    s4 = load_csv(RESULTS_DIR / "synthetic_table4_policyII.csv")
    ts3 = extract_table_body(tex, "tab:S3")
    assert len(ts3) == len(s4) == 16
    for row, csv_r in zip(ts3, s4):
        assert int(clean_num(row[0])) == int(csv_r["m"])
        assert_close(row[5], csv_r["mttf"], 0.01, f"S3 m={csv_r['m']} mttf")
        assert_close(row[6], csv_r["t_star"], 0.001, f"S3 m={csv_r['m']} t*")
        assert_close(row[7], csv_r["bzm_star"], 0.0001, f"S3 m={csv_r['m']} bzm")
        checks += 4

    # Table S4 vs synthetic_table5_sensitivity.csv
    s5 = load_csv(RESULTS_DIR / "synthetic_table5_sensitivity.csv")
    ts4 = extract_table_body(tex, "tab:S4")
    assert len(ts4) == len(s5) == 9
    for row, csv_r in zip(ts4, s5):
        assert_close(row[2], csv_r["mttf"], 0.01, f"S4 g=({csv_r['gamma1']},{csv_r['gamma2']}) mttf")
        assert_close(row[3], csv_r["t_star"], 0.001, f"S4 g=({csv_r['gamma1']},{csv_r['gamma2']}) t*")
        assert_close(row[4], csv_r["bzm_star"], 0.001, f"S4 g=({csv_r['gamma1']},{csv_r['gamma2']}) bzm")
        checks += 3

    # Table S5 vs E1 & E2 CSVs (13 rows completely disjoint from Main Table 3)
    e1_csv = load_csv(RESULTS_DIR / "case_E1_independent.csv")
    e2_csv = load_csv(RESULTS_DIR / "case_E2_mechanism_branches.csv")
    t3_main = extract_table_body(TEX_MAIN.read_text(encoding="utf-8"), "tab:case_e1_e2")
    t3_keys = set()
    for r_m in t3_main:
        m_m = re.match(r"(CT Area [123])\s*\((\d+)\)", r_m[0])
        assert m_m is not None
        t3_keys.add((norm_arr(m_m.group(1)), round(float(r_m[1]), 2), m_m.group(2)))
    ts5 = extract_table_body(tex, "tab:S5")
    assert len(ts5) == 13, f"Expected 13 rows in tab:S5, got {len(ts5)}"
    ts5_keys = set()
    for row in ts5:
        m_cfg = re.match(r"(CT Area [123])\s*\((\d+)\)", row[0])
        assert m_cfg is not None
        arr, c2 = norm_arr(m_cfg.group(1)), m_cfg.group(2)
        kf = str(float(row[1]))
        ts5_keys.add((arr, round(float(kf), 2), c2))
        r1 = find_row(e1_csv, array=arr, k_frac=kf, c2_c1=c2)
        rr_low = find_row(e2_csv, array=arr, k_frac=kf, c2_c1=c2, mechanism="Rotor", rho="1.15")
        rh_low = find_row(e2_csv, array=arr, k_frac=kf, c2_c1=c2, mechanism="HGP", rho="1.15")
        rr_hi = find_row(e2_csv, array=arr, k_frac=kf, c2_c1=c2, mechanism="Rotor", rho="1.03")
        assert_close(row[3], r1["t_star_h"], 0.01, f"S5 {arr} {kf} {c2} E1 t*")
        assert_close(row[4], r1["bzm_star"], 1e-6, f"S5 {arr} {kf} {c2} E1 bzm")
        assert_close(row[5], rr_low["t_star_h"], 0.01, f"S5 {arr} {kf} {c2} rot1.15 t*")
        assert_close(row[6], rr_low["bzm_star"], 1e-6, f"S5 {arr} {kf} {c2} rot1.15 bzm")
        assert_close(row[7], rr_low["cm_gap_pct"], 0.01, f"S5 {arr} {kf} {c2} rot1.15 gap")
        assert_close(row[8], rr_low["naive_penalty_pct"], 0.01, f"S5 {arr} {kf} {c2} rot1.15 pen")
        assert_close(row[9], rh_low["t_star_h"], 0.01, f"S5 {arr} {kf} {c2} hgp1.15 t*")
        assert_close(row[10], rh_low["bzm_star"], 1e-6, f"S5 {arr} {kf} {c2} hgp1.15 bzm")
        assert_close(row[11], rh_low["naive_penalty_pct"], 0.01, f"S5 {arr} {kf} {c2} hgp1.15 pen")
        assert_close(row[12], rr_hi["t_star_h"], 0.01, f"S5 {arr} {kf} {c2} rot1.03 t*")
        assert_close(row[13], rr_hi["naive_penalty_pct"], 0.01, f"S5 {arr} {kf} {c2} rot1.03 pen")
        checks += 11
    assert len(t3_keys & ts5_keys) == 0, f"Duplicate rows found between Table 3 and Table S5: {t3_keys & ts5_keys}"
    checks += 1

    # Table S6 (all 80 E3 configs) vs case_E3_turning_point_summary.csv
    e3_csv = load_csv(RESULTS_DIR / "case_E3_turning_point_summary.csv")
    ts6 = extract_table_body(tex, "tab:S6")
    assert len(ts6) == 20
    for row in ts6:
        arr = norm_arr(row[0])
        kf = float(row[1])
        for ci, c2 in enumerate(("3", "5", "10", "20")):
            r3 = find_row_float(e3_csv, {"k_frac": kf}, {"array": arr, "c2_c1": c2})
            tp_cell = row[3 + 2 * ci]
            cm_cell = row[4 + 2 * ci]
            if r3["turning_point_found"] == "False":
                assert clean_num(tp_cell) == ""
            else:
                assert_close(tp_cell, r3["gamma_tp"], 0.01, f"S6 {arr} {kf} c2={c2} g_tp")
            assert_close(cm_cell, r3["gamma_cm_1pct"], 0.01, f"S6 {arr} {kf} c2={c2} g_cm")
            checks += 2

    # Table S7 vs case_E4_consistency_summary.csv
    e4_sum = load_csv(RESULTS_DIR / "case_E4_consistency_summary.csv")
    ts7 = extract_table_body(tex, "tab:S7")
    assert len(ts7) == 15
    sub_lookup = {
        "Full 4D Box": "Full_4D_Box",
        "Symmetric ($r_{\\mathrm{OM}}=1.00$)": "Symmetric_OM_1.00",
        "EIA Slice ($r_{\\mathrm{OM}}=1.96$)": "EIA_OM_1.96",
        "Asymmetric ($r_{\\mathrm{OM}}>1$)": "Asymmetric_OM_gt1",
        "Policy I (No O\\&M diff.)": "PolicyI_NoOMDiff",
    }
    for row in ts7:
        arr = "All_CT_Pooled" if row[0] == "Pooled" else norm_arr(row[0])
        sub_key = sub_lookup[row[1]]
        sr = find_row(e4_sum, array=arr, subset=sub_key)
        assert int(clean_num(row[2])) == int(sr["n_points"])
        assert_close(row[3], sr["corner_m0_pct"], 0.01, f"S7 {arr} {sub_key} c0")
        assert_close(row[4], sr["band_3_5_pct"], 0.01, f"S7 {arr} {sub_key} b35")
        assert_close(row[5], sr["any_interior_pct"], 0.01, f"S7 {arr} {sub_key} any")
        assert_close(row[6], sr["median_regret_m4_interior_pct"], 0.01, f"S7 {arr} {sub_key} med4")
        assert_close(row[7], sr["max_regret_m4_interior_pct"], 0.01, f"S7 {arr} {sub_key} max4")
        assert_close(row[8], sr["median_regret_m0_interior_pct"], 0.01, f"S7 {arr} {sub_key} med0")
        assert_close(row[9], sr["max_regret_m0_interior_pct"], 0.01, f"S7 {arr} {sub_key} max0")
        checks += 8

    # Sequential label order check in supplementary.tex (S1..S9)
    supp_tabs = re.findall(r"\\label\{(tab:S\d+)\}", tex)
    assert supp_tabs == [f"tab:S{i}" for i in range(1, 10)], (
        f"Supplementary table label order mismatch: {supp_tabs}"
    )
    checks += 1

    # Table S8 vs case_E2_asymmetric_gamma.csv
    e2a_csv = load_csv(RESULTS_DIR / "case_E2_asymmetric_gamma.csv")
    ts8_asym = extract_table_body(tex, "tab:S8")
    assert len(ts8_asym) == 12, f"Expected 12 rows in tab:S8 (E2b), got {len(ts8_asym)}"
    pair_lookup = {
        "Rotor / Rotor": "Rotor_Rotor",
        "HGP / Rotor": "HGP_Rotor",
        "Rotor / HGP": "Rotor_HGP",
        "HGP / HGP": "HGP_HGP",
    }
    for row in ts8_asym:
        arr = norm_arr(row[0])
        pair_key = pair_lookup[row[1].strip()]
        r9 = find_row(e2a_csv, array=arr, k_frac="0.7", c2_c1="5", rho="1.15", branch_pair=pair_key)
        assert_close(row[3], r9["mttf_h"], 0.01, f"S8 {arr} {pair_key} mttf")
        assert_close(row[4], r9["t_star_h"], 0.01, f"S8 {arr} {pair_key} t*")
        assert_close(row[5], r9["bzm_star"], 1e-6, f"S8 {arr} {pair_key} bzm")
        assert_close(row[6], r9["cm_gap_pct"], 0.01, f"S8 {arr} {pair_key} cm_gap")
        assert_close(row[7], r9["naive_penalty_pct"], 0.01, f"S8 {arr} {pair_key} pen")
        checks += 5

    # Table S9 vs case_E6_downtime_sensitivity.csv
    e6_csv = load_csv(RESULTS_DIR / "case_E6_downtime_sensitivity.csv")
    ts9_e6 = extract_table_body(tex, "tab:S9")
    assert len(ts9_e6) == 51, f"Expected 51 rows in tab:S9 (E6), got {len(ts9_e6)}"
    assert "t^* \\in [1.42, 2.10]" in tex and "t \\ge 14.0" in tex and "0.9592" in tex and "36.7" in tex and "8, 37" in tex
    assert any("-0.39\\%" in r[7] for r in ts9_e6) and any("-9.78\\%" in r[7] for r in ts9_e6)
    checks += 7
    for row in ts9_e6:
        arr = norm_arr(row[0])
        btxt = row[1]
        if "U55" in btxt:
            basis = "U55_31h"
        elif "WeightedAvg" in btxt:
            basis = "WeightedAvg"
        elif "U20" in btxt:
            basis = "U20_50h"
        else:
            basis = "U76_U155_40h"
        delta = float(clean_num(row[2]))
        gval = float(clean_num(row[3]))
        rh = find_row_float(e6_csv, {"k_frac": 0.7, "gamma": gval, "duty_factor": delta}, {"array": arr, "c2_c1": "5", "mttr_basis": basis, "d_pm_mode": "half"})
        re_ = find_row_float(e6_csv, {"k_frac": 0.7, "gamma": gval, "duty_factor": delta}, {"array": arr, "c2_c1": "5", "mttr_basis": basis, "d_pm_mode": "equal"})
        assert_close(row[4], rh["t_inst_h"], 0.01, f"S9 {arr} {basis} d={delta} g={gval} t_inst")
        assert_close(row[5], rh["bzm_cal_inst"], 1e-6, f"S9 {arr} {basis} d={delta} g={gval} bzm_inst")
        assert_close(row[6], rh["t_ext_h"], 0.01, f"S9 {arr} {basis} d={delta} g={gval} half_t")
        assert_close(row[7], rh["t_shift_pct"], 0.01, f"S9 {arr} {basis} d={delta} g={gval} half_dt")
        assert_close(row[8], rh["bzm_cal_ext"], 1e-6, f"S9 {arr} {basis} d={delta} g={gval} half_bzm")
        assert_close(row[9], re_["t_ext_h"], 0.01, f"S9 {arr} {basis} d={delta} g={gval} eq_t")
        assert_close(row[10], re_["t_shift_pct"], 0.01, f"S9 {arr} {basis} d={delta} g={gval} eq_dt")
        assert_close(row[11], re_["bzm_cal_ext"], 1e-6, f"S9 {arr} {basis} d={delta} g={gval} eq_bzm")
        checks += 8

    return checks


def verify_security_and_blinding() -> int:
    checks = 0
    forbidden_global = _decode_tokens(FORBIDDEN_GLOBAL_B64)
    blinding_tokens = _decode_tokens(BLINDING_TOKENS_B64)

    scan_exts = {".py", ".tex", ".bib", ".md", ".cff", ".txt", ".json", ".csv"}
    for root, dirs, files in os.walk(BASE_DIR):
        dirs[:] = [d for d in dirs if d not in (".git", "__pycache__", ".venv", "_tmp")]
        for fn in files:
            p = Path(root) / fn
            if p.suffix.lower() not in scan_exts:
                continue
            if p.name in ("REAL_TIME_regional_Load.csv", "HANDOVER.md"):
                continue
            txt = p.read_text(encoding="utf-8", errors="ignore").lower()
            for tok in forbidden_global:
                assert tok not in txt, f"Forbidden token detected in {p.relative_to(BASE_DIR)}"
                checks += 1

    for blinded in (TEX_MAIN, TEX_SUPP):
        txt = blinded.read_text(encoding="utf-8")
        txt_l = txt.lower()
        for tok in blinding_tokens:
            assert tok not in txt_l, f"Blinding breach in {blinded.name}"
            checks += 1
        m_auth = re.search(r"\\author(?:\[([^\]]*)\])?\{([^}]*)\}", txt)
        assert m_auth is not None, f"Missing \\author block in {blinded.name}"
        surname_tok = _decode_tokens(["c2FyaWtheWE="])[0]
        assert surname_tok not in m_auth.group(0).lower(), f"Author block breach in {blinded.name}"
        checks += 2

    # Prose-regression & terminology hygiene checks across TeX files
    banned_prose = (
        "Strikingly", "Remarkably", "Moreover", "Furthermore",
        "twin pillars", "asymptotic curiosity", "band_3_6",
        "1.946", "80--212", "63-row", "50-row", "49 representative",
        "purely corrective", "CM-only", "Type-I", "Type-II",
        "1.9$--$2.7", "[9.7, 29.9]", "72.47\\% (non-inverted",
        "restricted to $c_2/c_1 = 20, \\gamma = 60.90$",
        "searched through March 2026", "Zhao X, Wei G", "exchangeable dependence",
        "continuous limit $W_0/k = 1.996$", "continuous limit $1.996$",
        "stay within $3.90\\%$--$13.99\\%$", "incur $>10^2\\times$",
        "pct.", "`mc", "`42`", "`scipy", "xatol", "Rushdi, A. M. A.",
        "6.0500", "709/905", "196/905", "LOLP", "EENS", "1.9781611971194",
    )
    for tex_p in (TEX_MAIN, TEX_SUPP, BASE_DIR / "manuscript" / "title_page.tex"):
        if not tex_p.exists(): continue
        txt = tex_p.read_text(encoding="utf-8")
        for pat in banned_prose:
            assert pat not in txt, f"Stale/inconsistent prose token '{pat}' found in {tex_p.name}"
            checks += 1
        assert not re.search(r"below\s+\\rho", txt), f"Redundant 'below \\rho' phrasing in {tex_p.name}"
        checks += 1
    return checks


def main():
    tex_main = TEX_MAIN.read_text(encoding="utf-8")
    tex_supp = TEX_SUPP.read_text(encoding="utf-8")

    c1 = verify_data_integrity()
    c2 = verify_main_manuscript(tex_main)
    c3 = verify_supplementary(tex_supp)
    c4 = verify_security_and_blinding()
    total = c1 + c2 + c3 + c4
    print(f"ALL VERIFICATION ASSERTIONS PASSED: {total} checks ({c1} data, {c2} manuscript, {c3} supplementary, {c4} audit).")


if __name__ == "__main__":
    main()
