"""
Execution Script: Replicates and Validates All Numerical Benchmark Experiments
and the IEEE RTS-GMLC Industrial Case Study for the Heterogeneous Weighted
k-out-of-n:G Load-Sharing System.

Generates:
Synthetic Analytical Verification (Tables S1-S4 in supplementary):
- Table 2: Baseline Benchmark Validation (gamma1 = gamma2 = 0)
- Table 3: Optimal Replacement Age & Penalty of Neglecting Load-Sharing (n=15, k=15)
- Table 4: Structural Component-Mix Optimization Under Policy II (n=15, k=15)
- Table 5: Sensitivity Analysis Across Stress Exponents gamma1 and gamma2

IEEE RTS-GMLC Industrial Case Study (saved to results/*.csv):
- Gamma Calibration Band (GER-3620 Rev P over rho in [1.03, 1.15])
- E1: Three CT arrays x 5 k/W0 thresholds x 4 cost ratios at gamma = 0
- E2: Same grid across calibrated gamma levels + naive schedule penalty, plus asymmetric (gamma1 != gamma2) cross-branch sensitivity
- E3: Geometric gamma sweep (0..1000) for turning point and 1% CM-only transition
- E4: Component-mix consistency mapping m*(gamma, c_pen/c2_c1, om_ratio, k/W0)
      over the 4D parameter box (no Sav% or suboptimality claims)
- E5: Reverse-order Coal steam array (Area 1, lambda2 > lambda1) & rate-swapped counterfactual vs CT arrays
- E6: Non-zero replacement/repair duration sensitivity (RTS-GMLC MTTRs, continuous & peaking duty factors)
"""

import os
import sys
import csv
import json
import math
import numpy as np

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, 'src'))

from reliability_model.ctmc_model import WeightedSystemCTMC
from reliability_model.policies import PolicyI_CostModel, PolicyII_CostModel
from reliability_model.optimizer import SystemOptimizer

RESULTS_DIR = os.path.join(BASE_DIR, 'results')
DATA_DIR = os.path.join(BASE_DIR, 'data')


def write_csv(filename: str, rows: list):
    """Writes a list of dicts to results/<filename>."""
    os.makedirs(RESULTS_DIR, exist_ok=True)
    path = os.path.join(RESULTS_DIR, filename)
    if not rows:
        return path
    fieldnames = list(rows[0].keys())
    with open(path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


# ==============================================================================
# PART A: SYNTHETIC ANALYTICAL BENCHMARK (TABLES 2-5 — PRESERVED UNCHANGED)
# ==============================================================================

def _exact_binomial_reliability(
    n: int, k: int, m: int, w1: int, w2: int, lam1: float, lam2: float, t: float
) -> float:
    """Closed-form independent weighted k-out-of-n:G reliability Eq. (R_ind)."""
    p1 = math.exp(-lam1 * t)
    p2 = math.exp(-lam2 * t)
    total = 0.0
    for i in range(m + 1):
        c1_term = math.comb(m, i) * (p1 ** i) * ((1.0 - p1) ** (m - i))
        for j in range(n - m + 1):
            if i * w1 + j * w2 >= k:
                c2_term = math.comb(n - m, j) * (p2 ** j) * ((1.0 - p2) ** (n - m - j))
                total += c1_term * c2_term
    return total


def run_table_2_baseline():
    """Runs the 16 classical independent-component weighted benchmark scenarios."""
    print("\n" + "="*80)
    print("RUNNING TABLE 2: BASELINE BENCHMARK VALIDATION (gamma1 = gamma2 = 0.0)")
    print("="*80)

    w1, w2 = 1, 2
    lambda1_0, lambda2_0 = 0.2, 0.1
    c1, c2 = 1.0, 5.0

    scenarios = [
        ('S1', 10, 10, 8),
        ('S2', 10, 12, 6),
        ('S3', 10, 15, 3),
        ('S4', 15, 15, 3),
        ('S5', 15, 15, 5),
        ('S6', 15, 15, 7),
        ('S7', 15, 15, 12),
        ('S8', 15, 15, 13),
        ('S9', 15, 10, 15),
        ('S10', 15, 15, 14),
        ('S11', 15, 20, 7),
        ('S12', 15, 8, 5),
        ('S13', 15, 10, 5),
        ('S14', 15, 13, 5),
        ('S15', 15, 17, 5),
        ('S16', 15, 20, 5),
    ]

    t_grid = np.linspace(0.1, 10.0, 50)
    results = []
    for sid, n, k, m in scenarios:
        ctmc = WeightedSystemCTMC(n=n, m=m, k=k, w1=w1, w2=w2,
                                  lambda1_0=lambda1_0, lambda2_0=lambda2_0,
                                  gamma1=0.0, gamma2=0.0)
        t_opt, bzm_opt = SystemOptimizer.optimize_t_policy_I(ctmc, c1=c1, c2=c2)
        max_rel_err = max(
            abs(ctmc.reliability(float(t)) - r_ind) / r_ind
            for t in t_grid
            for r_ind in (_exact_binomial_reliability(n, k, m, w1, w2, lambda1_0, lambda2_0, float(t)),)
        )
        margin = ctmc.W0 - k
        results.append({
            'scenario': sid, 'n': n, 'k': k, 'm': m, 'n_minus_m': n - m,
            'W0': ctmc.W0, 'margin': margin, 't_star': round(t_opt, 3), 'bzm_star': round(bzm_opt, 3),
            'max_rel_err': f"{max_rel_err:.3e}",
        })
    write_csv('synthetic_table2_baseline.csv', results)
    return results


def run_table_3_load_sharing():
    """Runs Table 3: 4 mixes x 4 regimes with Delta BZM% calculation."""
    print("\n" + "="*80)
    print("RUNNING TABLE 3: IMPACT OF ASYMMETRIC LOAD-SHARING AND COST PENALTY (n=15, k=15)")
    print("="*80)

    w1, w2 = 1, 2
    lambda1_0, lambda2_0 = 0.2, 0.1
    c1, c2 = 1.0, 5.0
    n, k = 15, 15

    mixes = [3, 5, 7, 12]
    regimes = [
        ('Regime 0', 0.0, 0.0),
        ('Regime 1', 0.8, 0.8),
        ('Regime 2', 1.5, 0.5),
        ('Regime 3', 1.5, 1.5),
    ]

    t_ind = {}
    for m in mixes:
        ctmc_base = WeightedSystemCTMC(n=n, m=m, k=k, w1=w1, w2=w2,
                                       lambda1_0=lambda1_0, lambda2_0=lambda2_0,
                                       gamma1=0.0, gamma2=0.0)
        t_opt, _ = SystemOptimizer.optimize_t_policy_I(ctmc_base, c1, c2)
        t_ind[m] = t_opt

    results = []
    for m in mixes:
        for reg_name, g1, g2 in regimes:
            ctmc = WeightedSystemCTMC(n=n, m=m, k=k, w1=w1, w2=w2,
                                      lambda1_0=lambda1_0, lambda2_0=lambda2_0,
                                      gamma1=g1, gamma2=g2)
            t_ls_opt, bzm_ls_opt = SystemOptimizer.optimize_t_policy_I(ctmc, c1, c2)
            cost_model = PolicyI_CostModel(ctmc, c1, c2)
            cost_naive = cost_model.cost_rate(t_ind[m])
            delta_pct = ((cost_naive - bzm_ls_opt) / bzm_ls_opt) * 100.0
            results.append({
                'mix_m': m, 'regime': reg_name, 'gamma1': g1, 'gamma2': g2,
                't_ls_star': round(t_ls_opt, 3), 'bzm_ls_star': round(bzm_ls_opt, 3),
                'bzm_naive': round(cost_naive, 3), 'delta_pct': round(delta_pct, 2)
            })
    write_csv('synthetic_table3_loadsharing.csv', results)
    return results


def run_table_4_policy_II():
    """Runs Table 4: Policy II structural mix optimization across m in 0..15."""
    print("\n" + "="*80)
    print("RUNNING TABLE 4: POLICY II COMPONENT-MIX OPTIMIZATION (n=15, k=15, gamma1=1.5, gamma2=0.5)")
    print("="*80)

    w1, w2 = 1, 2
    lambda1_0, lambda2_0 = 0.2, 0.1
    n, k = 15, 15
    g1, g2 = 1.5, 0.5

    cost_params = {
        'c0': 0.5, 'c_pen': 3.0,
        'c_rep1': 0.15, 'c_rep2': 1.05,
        'c_ref1': 0.02, 'c_ref2': 0.08
    }

    res = SystemOptimizer.co_optimize_mix_and_age_policy_II(n, k, w1, w2, lambda1_0, lambda2_0, g1, g2, cost_params)
    csv_rows = []
    for row in res['all_evaluations']:
        t_opt = row['t_star']
        if np.isinf(t_opt):
            row['t_star'] = 'inf'
        csv_rows.append({
            'm': row['m'], 'n_minus_m': n - row['m'], 'W0': row['W0'],
            'margin': row['capacity_margin'], 'mttf': round(row['mttf'], 2),
            't_star': 'inf' if row['t_star'] == 'inf' else round(row['t_star'], 3),
            'bzm_star': round(row['bzm_star'], 6),
        })
    write_csv('synthetic_table4_policyII.csv', csv_rows)
    return res


def run_table_5_sensitivity():
    """Runs Table 5: Sensitivity sweep over gamma1, gamma2 for m=5, n=15, k=15."""
    print("\n" + "="*80)
    print("RUNNING TABLE 5: SENSITIVITY OVER STRESS EXPONENTS gamma1 & gamma2 (n=15, k=15, m=5)")
    print("="*80)

    w1, w2 = 1, 2
    lambda1_0, lambda2_0 = 0.2, 0.1
    c1, c2 = 1.0, 5.0
    n, k, m = 15, 15, 5

    sweep = [
        (0.0, 0.0), (0.5, 0.5), (1.0, 1.0), (1.5, 0.5), (0.5, 1.5),
        (1.5, 1.5), (2.0, 2.0), (3.0, 3.0), (3.5, 3.5),
    ]

    results = []
    for g1, g2 in sweep:
        ctmc = WeightedSystemCTMC(n=n, m=m, k=k, w1=w1, w2=w2,
                                  lambda1_0=lambda1_0, lambda2_0=lambda2_0,
                                  gamma1=g1, gamma2=g2)
        t_opt, bzm_opt = SystemOptimizer.optimize_t_policy_I(ctmc, c1, c2)
        results.append({
            'gamma1': g1, 'gamma2': g2, 'mttf': round(ctmc.mttf, 2),
            't_star': round(t_opt, 3), 'bzm_star': round(bzm_opt, 3)
        })
    write_csv('synthetic_table5_sensitivity.csv', results)
    return results


# ==============================================================================
# PART B: IEEE RTS-GMLC INDUSTRIAL CASE STUDY (E1 - E6)
# ==============================================================================

K_FRACTIONS = [0.50, 0.60, 0.70, 0.80, 0.90]
COST_RATIOS = [3.0, 5.0, 10.0, 20.0]

# Primary GER-3620 Rev P damage-mechanism branches parameterized over overload ratio rho = P_peak / P_base:
#   Rotor branch (Fig. 44, p. 35): MF_rotor = 2.00 at 100% peak load
#   HGP B/E-class branch (Fig. 10, p. 7 & App. A.1, p. 39): MF_HGP = exp(0.018 * 100) ~ 6.05
#   HGP F-class reference (Fig. 10, p. 7): exp(0.023 * 100) ~ 9.97
MF_ROTOR = 2.00
MF_HGP = 6.05
MF_HGP_F = math.exp(2.3)

RHO_CALIB_GRID = [1.03, 1.05, 1.08, 1.10, 1.12, 1.15]
RHO_EXP_GRID = [1.15, 1.10, 1.05, 1.03]
RHO_CORE_GRID = [1.15, 1.10, 1.03]


def gamma_from_mf_rho(mf: float, rho: float) -> float:
    """Computes power-law TFR sensitivity exponent gamma = ln(MF) / ln(rho)."""
    return math.log(mf) / math.log(rho)


ROTOR_MIN = gamma_from_mf_rho(MF_ROTOR, 1.15)   # 4.9595
ROTOR_MAX = gamma_from_mf_rho(MF_ROTOR, 1.03)   # 23.4498
HGP_MIN = gamma_from_mf_rho(MF_HGP, 1.15)       # 12.8806
HGP_MAX = gamma_from_mf_rho(MF_HGP, 1.03)       # 60.9022

EIA_FOM_AERO = 9.99
EIA_VOM_AERO = 5.97
EIA_FOM_FRAME = 7.18
EIA_VOM_FRAME = 4.17
PEAKING_CF_REF = 0.10
EIA_OM_UNIT_RATIO = (
    (55.0 * (EIA_FOM_FRAME + EIA_VOM_FRAME * 8.76 * PEAKING_CF_REF)) /
    (20.0 * (EIA_FOM_AERO + EIA_VOM_AERO * 8.76 * PEAKING_CF_REF))
)


def load_and_verify_rts_gmlc():
    """
    Loads data/gen.csv and data/REAL_TIME_regional_Load.csv, asserts internal
    consistency FOR == MTTR / (MTTF + MTTR) for all relevant unit groups, and
    constructs area-based array definitions (no fleet-wide pooling).
    """
    gen_path = os.path.join(DATA_DIR, 'gen.csv')
    load_path = os.path.join(DATA_DIR, 'REAL_TIME_regional_Load.csv')
    assert os.path.exists(gen_path), f"Missing primary data file: {gen_path}"
    assert os.path.exists(load_path), f"Missing primary data file: {load_path}"

    target_groups = {'U20', 'U55', 'U76', 'U155', 'U12'}
    group_records = {g: [] for g in target_groups}

    with open(gen_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            ug = row['Unit Group']
            if ug in target_groups:
                bus_id = str(row['Bus ID']).strip()
                area = int(bus_id[0])
                pmax = float(row['PMax MW'])
                mttf = float(row['MTTF Hr'])
                mttr = float(row['MTTR Hr'])
                for_val = float(row['FOR'])
                calc_for = mttr / (mttf + mttr)
                assert abs(for_val - calc_for) < 1e-6, (
                    f"FOR consistency failed for {ug}: FOR={for_val}, calc={calc_for}"
                )
                group_records[ug].append({
                    'area': area, 'pmax': int(round(pmax)),
                    'mttf': mttf, 'mttr': mttr, 'for': for_val
                })

    unit_params = {}
    for ug in sorted(target_groups):
        recs = group_records[ug]
        assert len(recs) > 0, f"No units found for {ug}"
        p0 = recs[0]
        for r in recs[1:]:
            assert r['pmax'] == p0['pmax'] and r['mttf'] == p0['mttf'] and r['mttr'] == p0['mttr']
        counts_by_area = {a: sum(1 for r in recs if r['area'] == a) for a in (1, 2, 3)}
        unit_params[ug] = {
            'pmax': p0['pmax'], 'mttf': p0['mttf'], 'mttr': p0['mttr'],
            'for': p0['for'], 'lambda': 1.0 / p0['mttf'], 'counts': counts_by_area
        }

    area_max_load = {1: 0.0, 2: 0.0, 3: 0.0}
    with open(load_path, 'r', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            for a in (1, 2, 3):
                val = float(row[str(a)])
                if val > area_max_load[a]:
                    area_max_load[a] = val

    arrays = {}
    for area in (1, 2, 3):
        m_u20 = unit_params['U20']['counts'][area]
        n_u55 = unit_params['U55']['counts'][area]
        n_tot = m_u20 + n_u55
        W0 = m_u20 * unit_params['U20']['pmax'] + n_u55 * unit_params['U55']['pmax']
        arrays[f'CT_Area{area}'] = {
            'name': f'CT_Area{area}',
            'area': area,
            'type1': 'U20', 'type2': 'U55',
            'n': n_tot, 'm': m_u20, 'n_minus_m': n_u55,
            'w1': unit_params['U20']['pmax'], 'w2': unit_params['U55']['pmax'],
            'W0': W0,
            'lam1': unit_params['U20']['lambda'], 'lam2': unit_params['U55']['lambda'],
            'mttf1': unit_params['U20']['mttf'], 'mttf2': unit_params['U55']['mttf'],
            'mttr1': unit_params['U20']['mttr'], 'mttr2': unit_params['U55']['mttr'],
            'area_peak_load_mw': area_max_load[area],
        }

    m_u76 = unit_params['U76']['counts'][1]
    n_u155 = unit_params['U155']['counts'][1]
    W0_coal = m_u76 * unit_params['U76']['pmax'] + n_u155 * unit_params['U155']['pmax']
    arrays['Coal_Area1'] = {
        'name': 'Coal_Area1',
        'area': 1,
        'type1': 'U76', 'type2': 'U155',
        'n': m_u76 + n_u155, 'm': m_u76, 'n_minus_m': n_u155,
        'w1': unit_params['U76']['pmax'], 'w2': unit_params['U155']['pmax'],
        'W0': W0_coal,
        'lam1': unit_params['U76']['lambda'], 'lam2': unit_params['U155']['lambda'],
        'mttf1': unit_params['U76']['mttf'], 'mttf2': unit_params['U155']['mttf'],
        'mttr1': unit_params['U76']['mttr'], 'mttr2': unit_params['U155']['mttr'],
        'area_peak_load_mw': area_max_load[1],
    }

    assert arrays['CT_Area1']['n'] == 11 and arrays['CT_Area1']['m'] == 4 and arrays['CT_Area1']['W0'] == 465
    assert arrays['CT_Area2']['n'] == 13 and arrays['CT_Area2']['m'] == 4 and arrays['CT_Area2']['W0'] == 575
    assert arrays['CT_Area3']['n'] == 15 and arrays['CT_Area3']['m'] == 4 and arrays['CT_Area3']['W0'] == 685
    assert arrays['Coal_Area1']['n'] == 7 and arrays['Coal_Area1']['m'] == 4 and arrays['Coal_Area1']['W0'] == 769
    assert abs(area_max_load[1] - 2850.0) < 1e-6

    return unit_params, arrays, area_max_load


def run_gamma_calibration_table():
    """Generates the parametric gamma = ln(MF)/ln(rho) mechanism-curve calibration table."""
    mf_specs = [
        ('Rotor_Branch_MF2.00', MF_ROTOR, 'GER-3620 Fig. 44 (p. 35)'),
        ('HGP_BE_Branch_MF6.05', MF_HGP, 'GER-3620 Fig. 10 & App. A.1 (p. 7, 39)'),
        ('HGP_F_Ref_MF9.97', MF_HGP_F, 'GER-3620 Fig. 10 formula (p. 7, reference)'),
    ]
    rows = []
    for label, mf, src in mf_specs:
        row = {'mechanism': label, 'MF': round(mf, 4), 'source': src}
        for rho in RHO_CALIB_GRID:
            row[f'rho_{rho:.2f}'] = round(gamma_from_mf_rho(mf, rho), 2)
        rows.append(row)
    write_csv('gamma_calibration_band.csv', rows)
    return rows


def run_case_E1_independent(arrays: dict):
    """E1: Three CT arrays x 5 k/W0 values x 4 cost ratios at gamma = 0."""
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E1: CT ARRAYS AT GAMMA = 0 (INDEPENDENT BASELINE)")
    print("="*80)
    rows = []
    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = arrays[name]
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], 0.0, 0.0)
            grid, P_mat = SystemOptimizer.precompute_grid_probs(
                ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(2000.0, 6.0 * ctmc.mttf), n_grid=300
            )
            for c2 in COST_RATIOS:
                model = PolicyI_CostModel(ctmc, 1.0, c2)
                t_opt, bzm_opt = SystemOptimizer.optimize_t_from_precomputed(model, grid, P_mat)
                bzm_inf = c2 / ctmc.mttf
                cm_gap_pct = (bzm_inf - bzm_opt) / bzm_inf * 100.0
                rows.append({
                    'array': name, 'n': a['n'], 'm': a['m'], 'W0': a['W0'],
                    'k_frac': kf, 'k': k, 'M': ctmc.M, 'c2_c1': int(c2),
                    'gamma': 0.0, 'mttf_h': round(ctmc.mttf, 2),
                    't_star_h': 'inf' if np.isinf(t_opt) else round(t_opt, 2),
                    'bzm_star': round(bzm_opt, 6), 'bzm_inf': round(bzm_inf, 6),
                    'cm_gap_pct': round(cm_gap_pct, 2),
                })
    write_csv('case_E1_independent.csv', rows)
    return rows


def _compute_ct_independent_optima(arrays: dict) -> dict:
    """Computes independent (gamma=0) optimal replacement ages for CT_Area1..3."""
    t_ind_map = {}
    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = arrays[name]
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            ctmc0 = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], 0.0, 0.0)
            grid0, P0 = SystemOptimizer.precompute_grid_probs(
                ctmc0, t_lb=max(0.5, 1e-3 * ctmc0.mttf), t_ub=max(2000.0, 6.0 * ctmc0.mttf), n_grid=300
            )
            for c2 in COST_RATIOS:
                t0, _ = SystemOptimizer.optimize_t_from_precomputed(PolicyI_CostModel(ctmc0, 1.0, c2), grid0, P0)
                t_ind_map[(name, kf, c2)] = t0
    return t_ind_map


def run_case_E2_mechanism_branches(arrays: dict):
    """
    E2: Three CT arrays x 5 k/W0 x 4 cost ratios evaluated along the two
    GER-3620 mechanism branches (Rotor MF=2.00 and HGP B/E-class MF=6.05) over rho in [1.03, 1.15].
    """
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E2: CT ARRAYS ALONG ROTOR & HGP MECHANISM BRANCHES")
    print("="*80)
    branch_points = []
    for branch_name, mf_val in (('Rotor', MF_ROTOR), ('HGP', MF_HGP)):
        for rho in RHO_EXP_GRID:
            branch_points.append((branch_name, mf_val, rho, gamma_from_mf_rho(mf_val, rho)))

    t_ind_map = _compute_ct_independent_optima(arrays)

    rows = []
    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = arrays[name]
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            for branch_name, mf_val, rho, g_val in branch_points:
                ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], g_val, g_val)
                grid, P_mat = SystemOptimizer.precompute_grid_probs(
                    ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(1000.0, 6.0 * ctmc.mttf), n_grid=300
                )
                for c2 in COST_RATIOS:
                    model = PolicyI_CostModel(ctmc, 1.0, c2)
                    t_opt, bzm_opt = SystemOptimizer.optimize_t_from_precomputed(model, grid, P_mat)
                    bzm_inf = c2 / ctmc.mttf
                    cm_gap_pct = (bzm_inf - bzm_opt) / bzm_inf * 100.0
                    t_naive = t_ind_map[(name, kf, c2)]
                    bzm_naive = bzm_inf if np.isinf(t_naive) else model.cost_rate(t_naive)
                    penalty_pct = (bzm_naive - bzm_opt) / bzm_opt * 100.0
                    rows.append({
                        'array': name, 'n': a['n'], 'm': a['m'], 'W0': a['W0'],
                        'k_frac': kf, 'k': k, 'c2_c1': int(c2),
                        'mechanism': branch_name, 'MF': round(mf_val, 2), 'rho': round(rho, 2),
                        'gamma': round(g_val, 2),
                        'mttf_h': round(ctmc.mttf, 2),
                        't_star_h': 'inf' if np.isinf(t_opt) else round(t_opt, 2),
                        'bzm_star': round(bzm_opt, 6), 'bzm_inf': round(bzm_inf, 6),
                        'cm_gap_pct': round(cm_gap_pct, 2),
                        'bzm_naive': round(bzm_naive, 6),
                        'naive_penalty_pct': round(penalty_pct, 2),
                    })
    write_csv('case_E2_mechanism_branches.csv', rows)
    return rows


def run_case_E2_asymmetric(arrays: dict):
    """
    E2b: Evaluates heterogeneous cross-branch exponent combinations (gamma1 != gamma2)
    where U20 (Type I) and U55 (Type II) sit on independent Rotor or HGP branches
    at overload ratio rho in {1.15, 1.10, 1.03}.
    """
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E2b: ASYMMETRIC CROSS-BRANCH SENSITIVITY (gamma1 != gamma2)")
    print("="*80)
    t_ind_map = _compute_ct_independent_optima(arrays)
    branch_map = {'Rotor': MF_ROTOR, 'HGP': MF_HGP}
    pair_specs = [
        ('Rotor_Rotor', 'Rotor', 'Rotor'),
        ('HGP_Rotor', 'HGP', 'Rotor'),
        ('Rotor_HGP', 'Rotor', 'HGP'),
        ('HGP_HGP', 'HGP', 'HGP'),
    ]

    rows = []
    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = arrays[name]
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            for rho in RHO_CORE_GRID:
                for pair_label, b1, b2 in pair_specs:
                    g1 = gamma_from_mf_rho(branch_map[b1], rho)
                    g2 = gamma_from_mf_rho(branch_map[b2], rho)
                    ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], g1, g2)
                    grid, P_mat = SystemOptimizer.precompute_grid_probs(
                        ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(1000.0, 6.0 * ctmc.mttf), n_grid=300
                    )
                    for c2 in COST_RATIOS:
                        model = PolicyI_CostModel(ctmc, 1.0, c2)
                        t_opt, bzm_opt = SystemOptimizer.optimize_t_from_precomputed(model, grid, P_mat)
                        bzm_inf = c2 / ctmc.mttf
                        cm_gap_pct = (bzm_inf - bzm_opt) / bzm_inf * 100.0
                        t_naive = t_ind_map[(name, kf, c2)]
                        bzm_naive = bzm_inf if np.isinf(t_naive) else model.cost_rate(t_naive)
                        penalty_pct = (bzm_naive - bzm_opt) / bzm_opt * 100.0
                        rows.append({
                            'array': name, 'n': a['n'], 'm': a['m'], 'W0': a['W0'],
                            'k_frac': kf, 'k': k, 'c2_c1': int(c2),
                            'rho': round(rho, 2), 'branch_pair': pair_label,
                            'gamma1': round(g1, 2), 'gamma2': round(g2, 2),
                            'mttf_h': round(ctmc.mttf, 2),
                            't_star_h': 'inf' if np.isinf(t_opt) else round(t_opt, 2),
                            'bzm_star': round(bzm_opt, 6), 'bzm_inf': round(bzm_inf, 6),
                            'cm_gap_pct': round(cm_gap_pct, 2),
                            'naive_penalty_pct': round(penalty_pct, 2),
                        })
    write_csv('case_E2_asymmetric_gamma.csv', rows)
    return rows


def _evaluate_gamma_sweep(a: dict, k: int, c2: float, gamma_grid: list):
    """Sweeps symmetric gamma and extracts turning point (gamma_tp, t_min) and gamma_CM,1%."""
    series = []
    gamma_cm_1pct = None
    for g in gamma_grid:
        ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], g, g)
        t_opt, bzm_opt = SystemOptimizer.optimize_t_policy_I(
            ctmc, 1.0, c2, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(1000.0, 6.0 * ctmc.mttf), n_grid=300
        )
        bzm_inf = c2 / ctmc.mttf
        gap = (bzm_inf - bzm_opt) / bzm_inf
        series.append((g, ctmc.mttf, t_opt, bzm_opt, bzm_inf, gap))
        if gap < 0.01:
            gamma_cm_1pct = g
            break

    t0 = series[0][2]
    gap0 = series[0][5]
    finite_pts = [(g, t) for g, _, t, _, _, _ in series if np.isfinite(t)]
    if gap0 < 0.01:
        tp_found, gamma_tp, t_min = False, 0.0, t0
    elif finite_pts:
        gamma_tp, t_min = min(finite_pts, key=lambda x: x[1])
        tp_found = (gamma_tp > 0.0) and (t_min < t0 * 0.999)
    else:
        tp_found, gamma_tp, t_min = False, float('nan'), float('inf')

    return series, t0, tp_found, gamma_tp, t_min, gamma_cm_1pct


def run_case_E3_turning_point(arrays: dict):
    """E3: Geometric gamma sweep (0..1000) for turning point and <1% CM-only transition."""
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E3: GAMMA TURNING-POINT & CM-ONLY TRANSITION SWEEP")
    print("="*80)
    gamma_grid = [0.0] + list(np.geomspace(0.5, 1000.0, 90))

    summary_rows = []
    curve_rows = []

    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3', 'Coal_Area1'):
        a = arrays[name]
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            for c2 in COST_RATIOS:
                series, t0, tp_found, gamma_tp, t_min, gamma_cm_1pct = _evaluate_gamma_sweep(a, k, c2, gamma_grid)
                if kf in (0.50, 0.70) and int(c2) in (5, 10):
                    for g, mttf_val, t_opt, bzm_opt, bzm_inf, gap in series:
                        curve_rows.append({
                            'array': name, 'k_frac': kf, 'k': k, 'c2_c1': int(c2),
                            'gamma': round(g, 4), 'mttf_h': round(mttf_val, 3),
                            't_star_h': 'inf' if np.isinf(t_opt) else round(t_opt, 3),
                            'bzm_star': round(bzm_opt, 6), 'bzm_inf': round(bzm_inf, 6),
                            'cm_gap_pct': round(gap * 100.0, 4),
                        })

                tp_in_rotor = tp_found and (ROTOR_MIN <= gamma_tp <= ROTOR_MAX)
                tp_in_hgp = tp_found and (HGP_MIN <= gamma_tp <= HGP_MAX)
                tp_in_env = tp_found and (ROTOR_MIN <= gamma_tp <= HGP_MAX)
                cm_in_rotor = (gamma_cm_1pct is not None) and (ROTOR_MIN <= gamma_cm_1pct <= ROTOR_MAX)
                cm_in_hgp = (gamma_cm_1pct is not None) and (HGP_MIN <= gamma_cm_1pct <= HGP_MAX)
                cm_in_env = (gamma_cm_1pct is not None) and (ROTOR_MIN <= gamma_cm_1pct <= HGP_MAX)
                summary_rows.append({
                    'array': name, 'k_frac': kf, 'k': k, 'c2_c1': int(c2),
                    't_at_g0_h': 'inf' if np.isinf(t0) else round(t0, 2),
                    'turning_point_found': tp_found,
                    'gamma_tp': '' if (not tp_found) else round(gamma_tp, 2),
                    't_min_h': 'inf' if np.isinf(t_min) else round(t_min, 2),
                    'gamma_cm_1pct': '' if gamma_cm_1pct is None else round(gamma_cm_1pct, 2),
                    'tp_in_rotor_branch': tp_in_rotor,
                    'tp_in_hgp_branch': tp_in_hgp,
                    'tp_in_envelope': tp_in_env,
                    'cm_in_rotor_branch': cm_in_rotor,
                    'cm_in_hgp_branch': cm_in_hgp,
                    'cm_in_envelope': cm_in_env,
                })

    write_csv('case_E3_turning_point_summary.csv', summary_rows)
    write_csv('case_E3_turning_point_curves.csv', curve_rows)
    return summary_rows, curve_rows


def run_case_E4_consistency_map(arrays: dict):
    """
    E4 (REFRAMED): Component-mix consistency mapping m* = f(gamma, c2/c1_eff, om_ratio, k/W0).
    Evaluates Policy I (no unit O&M differentiation) and Policy II across the 4D parameter box:
      - gamma in {0.0, 4.96, 7.27, 9.01, 12.88, 14.21, 18.88, 23.45, 36.89, 60.90}
        (spanning independence, the rotor branch [4.96, 23.45], and the HGP branch [12.88, 60.90])
      - om_ratio (c_rep2/c_rep1 = c_ref2/c_ref1) in {1.00, 1.50, 1.96, 2.50, 3.00}
      - c_pen in {10, 15, 25, 40, 100} (mapping to effective c2/c1 across [~3, ~20])
      - k_frac in {0.50, 0.60, 0.70, 0.80, 0.90}
    Reports volume fractions of the corner region (m* = 0), symmetric +/-1 band
    (m* in {3, 4, 5}), and other interior regions. No suboptimality or Sav% claims.
    """
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E4: 4D COMPONENT-MIX CONSISTENCY MAPPING")
    print("="*80)

    gamma_box = [
        0.0,
        round(math.log(2.00) / math.log(1.15), 4),   # 4.9595 (rotor rho=1.15)
        round(math.log(2.00) / math.log(1.10), 4),   # 7.2725 (rotor rho=1.10)
        round(math.log(2.00) / math.log(1.08), 4),   # 9.0065 (rotor rho=1.08)
        round(math.log(6.05) / math.log(1.15), 4),   # 12.8806 (HGP rho=1.15)
        round(math.log(2.00) / math.log(1.05), 4),   # 14.2067 (rotor rho=1.05)
        round(math.log(6.05) / math.log(1.10), 4),   # 18.8878 (HGP rho=1.10)
        round(math.log(2.00) / math.log(1.03), 4),   # 23.4498 (rotor rho=1.03)
        round(math.log(6.05) / math.log(1.05), 4),   # 36.8965 (HGP rho=1.05)
        round(math.log(6.05) / math.log(1.03), 4),   # 60.9022 (HGP rho=1.03)
    ]
    om_ratios = [1.00, 1.50, round(EIA_OM_UNIT_RATIO, 4), 2.50, 3.00]
    pen_levels = [10.0, 15.0, 25.0, 40.0, 100.0]
    c0 = 2.0
    c_rep1 = 1.0
    c_ref1 = 0.15

    # 1. Verify Policy I (no unit O&M differentiation) over (gamma_box x COST_RATIOS x K_FRACTIONS)
    p1_total = 0
    p1_m0_count = 0
    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = arrays[name]
        n = a['n']
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            for g_val in gamma_box:
                ctmcs = {}
                precomp = {}
                for m in range(0, n + 1):
                    W0 = m * a['w1'] + (n - m) * a['w2']
                    if W0 >= k:
                        ctmc = WeightedSystemCTMC(n, m, k, a['w1'], a['w2'], a['lam1'], a['lam2'], g_val, g_val)
                        ctmcs[m] = ctmc
                        precomp[m] = SystemOptimizer.precompute_grid_probs(
                            ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(1500.0, 6.0 * ctmc.mttf), n_grid=150
                        )
                for c2 in COST_RATIOS:
                    best_m, best_bzm = -1, float('inf')
                    for m, ctmc in ctmcs.items():
                        model = PolicyI_CostModel(ctmc, 1.0, c2)
                        grid, P_mat = precomp[m]
                        _, bzm_opt = SystemOptimizer.optimize_t_from_precomputed(model, grid, P_mat)
                        if bzm_opt < best_bzm:
                            best_bzm = bzm_opt
                            best_m = m
                    p1_total += 1
                    if best_m == 0:
                        p1_m0_count += 1
    assert p1_m0_count == p1_total, f"Policy I expected 100% m*=0, got {p1_m0_count}/{p1_total}"

    # 2. Evaluate Policy II 4D consistency box
    box_rows = []
    summary_rows = []

    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = arrays[name]
        n = a['n']
        arr_rows = []
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            for g_val in gamma_box:
                # Cache CTMCs and uniform probability grids across all 25 (om_ratio, c_pen) cells
                ctmcs = {}
                precomp = {}
                for m in range(0, n + 1):
                    W0 = m * a['w1'] + (n - m) * a['w2']
                    if W0 >= k:
                        ctmc = WeightedSystemCTMC(n, m, k, a['w1'], a['w2'], a['lam1'], a['lam2'], g_val, g_val)
                        ctmcs[m] = ctmc
                        precomp[m] = SystemOptimizer.precompute_grid_probs(
                            ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(1500.0, 6.0 * ctmc.mttf), n_grid=150
                        )

                for om_r in om_ratios:
                    c_rep2 = om_r * c_rep1
                    c_ref2 = om_r * c_ref1
                    c_pm_ref = c0 + 4 * c_ref1 + (n - 4) * c_ref2
                    for c_pen in pen_levels:
                        c2_c1_eff = (c_pm_ref + c_pen) / c_pm_ref
                        best_m, best_t, best_bzm = -1, float('inf'), float('inf')
                        bzm_m0 = float('inf')
                        bzm_m4 = float('inf')
                        for m, ctmc in ctmcs.items():
                            model = PolicyII_CostModel(
                                ctmc, c0=c0, c_pen=c_pen,
                                c_rep1=c_rep1, c_rep2=c_rep2,
                                c_ref1=c_ref1, c_ref2=c_ref2
                            )
                            grid, P_mat = precomp[m]
                            t_opt, bzm_opt = SystemOptimizer.optimize_t_from_precomputed(model, grid, P_mat)
                            if m == 0:
                                bzm_m0 = bzm_opt
                            if m == 4:
                                bzm_m4 = bzm_opt
                            if bzm_opt < best_bzm:
                                best_bzm = bzm_opt
                                best_m = m
                                best_t = t_opt

                        assert np.isfinite(bzm_m0) and np.isfinite(bzm_m4), f"m=0,4 must be feasible for {name}, k={k}"
                        regret_m0_pct = round((bzm_m0 - best_bzm) / best_bzm * 100.0, 2)
                        regret_m4_pct = round((bzm_m4 - best_bzm) / best_bzm * 100.0, 2)
                        region = (
                            'corner_m0' if best_m == 0 else
                            ('band_3_5' if best_m in (3, 4, 5) else 'other_interior')
                        )
                        rec = {
                            'array': name, 'n': n, 'k_frac': kf, 'k': k,
                            'gamma': round(g_val, 2), 'om_ratio': round(om_r, 4),
                            'c_pen': int(c_pen), 'c2_c1_eff': round(c2_c1_eff, 2),
                            'm_star': best_m,
                            't_star_h': 'inf' if np.isinf(best_t) else round(best_t, 2),
                            'bzm_star': round(best_bzm, 6),
                            'bzm_m0': round(bzm_m0, 6),
                            'regret_m0_pct': regret_m0_pct,
                            'bzm_m4': round(bzm_m4, 6),
                            'regret_m4_pct': regret_m4_pct,
                            'region': region,
                        }
                        box_rows.append(rec)
                        arr_rows.append(rec)

        # Compute box volume fractions for this array (overall, om_ratio=1.0, om_ratio=1.96, om_ratio>1.0)
        for subset_label, subset in [
            ('Full_4D_Box', arr_rows),
            ('Symmetric_OM_1.00', [r for r in arr_rows if abs(r['om_ratio'] - 1.0) < 1e-3]),
            ('EIA_OM_1.96', [r for r in arr_rows if abs(r['om_ratio'] - EIA_OM_UNIT_RATIO) < 1e-3]),
            ('Asymmetric_OM_gt1', [r for r in arr_rows if r['om_ratio'] > 1.01]),
        ]:
            tot = len(subset)
            n_m0 = sum(1 for r in subset if r['m_star'] == 0)
            n_35 = sum(1 for r in subset if r['m_star'] in (3, 4, 5))
            n_int = sum(1 for r in subset if r['m_star'] > 0)
            n_oth = tot - n_m0 - n_35
            reg_35 = [r['regret_m4_pct'] for r in subset if r['region'] == 'band_3_5']
            reg4_int = [r['regret_m4_pct'] for r in subset if r['m_star'] > 0]
            reg0_int = [r['regret_m0_pct'] for r in subset if r['m_star'] > 0]
            summary_rows.append({
                'array': name, 'subset': subset_label, 'n_points': tot,
                'corner_m0_count': n_m0, 'corner_m0_pct': round(100.0 * n_m0 / tot, 2),
                'band_3_5_count': n_35, 'band_3_5_pct': round(100.0 * n_35 / tot, 2),
                'other_interior_count': n_oth, 'other_interior_pct': round(100.0 * n_oth / tot, 2),
                'any_interior_pct': round(100.0 * n_int / tot, 2),
                'median_regret_m4_band35_pct': round(float(np.median(reg_35)), 2) if reg_35 else '',
                'max_regret_m4_band35_pct': round(float(np.max(reg_35)), 2) if reg_35 else '',
                'median_regret_m4_interior_pct': round(float(np.median(reg4_int)), 2) if reg4_int else '',
                'p90_regret_m4_interior_pct': round(float(np.percentile(reg4_int, 90)), 2) if reg4_int else '',
                'max_regret_m4_interior_pct': round(float(np.max(reg4_int)), 2) if reg4_int else '',
                'count_regret_m4_gt1_interior': sum(1 for x in reg4_int if x > 1.0) if reg4_int else 0,
                'median_regret_m0_interior_pct': round(float(np.median(reg0_int)), 2) if reg0_int else '',
                'p90_regret_m0_interior_pct': round(float(np.percentile(reg0_int, 90)), 2) if reg0_int else '',
                'max_regret_m0_interior_pct': round(float(np.max(reg0_int)), 2) if reg0_int else '',
                'count_regret_m0_gt1_interior': sum(1 for x in reg0_int if x > 1.0) if reg0_int else 0,
            })

    # Add pooled summary across all 3 CT arrays + Policy I summary row
    for subset_label, subset in [
        ('Full_4D_Box', box_rows),
        ('Symmetric_OM_1.00', [r for r in box_rows if abs(r['om_ratio'] - 1.0) < 1e-3]),
        ('EIA_OM_1.96', [r for r in box_rows if abs(r['om_ratio'] - EIA_OM_UNIT_RATIO) < 1e-3]),
        ('Asymmetric_OM_gt1', [r for r in box_rows if r['om_ratio'] > 1.01]),
    ]:
        tot = len(subset)
        n_m0 = sum(1 for r in subset if r['m_star'] == 0)
        n_35 = sum(1 for r in subset if r['m_star'] in (3, 4, 5))
        n_int = sum(1 for r in subset if r['m_star'] > 0)
        n_oth = tot - n_m0 - n_35
        reg_35 = [r['regret_m4_pct'] for r in subset if r['region'] == 'band_3_5']
        reg4_int = [r['regret_m4_pct'] for r in subset if r['m_star'] > 0]
        reg0_int = [r['regret_m0_pct'] for r in subset if r['m_star'] > 0]
        summary_rows.append({
            'array': 'All_CT_Pooled', 'subset': subset_label, 'n_points': tot,
            'corner_m0_count': n_m0, 'corner_m0_pct': round(100.0 * n_m0 / tot, 2),
            'band_3_5_count': n_35, 'band_3_5_pct': round(100.0 * n_35 / tot, 2),
            'other_interior_count': n_oth, 'other_interior_pct': round(100.0 * n_oth / tot, 2),
            'any_interior_pct': round(100.0 * n_int / tot, 2),
            'median_regret_m4_band35_pct': round(float(np.median(reg_35)), 2) if reg_35 else '',
            'max_regret_m4_band35_pct': round(float(np.max(reg_35)), 2) if reg_35 else '',
            'median_regret_m4_interior_pct': round(float(np.median(reg4_int)), 2) if reg4_int else '',
            'p90_regret_m4_interior_pct': round(float(np.percentile(reg4_int, 90)), 2) if reg4_int else '',
            'max_regret_m4_interior_pct': round(float(np.max(reg4_int)), 2) if reg4_int else '',
            'count_regret_m4_gt1_interior': sum(1 for x in reg4_int if x > 1.0) if reg4_int else 0,
            'median_regret_m0_interior_pct': round(float(np.median(reg0_int)), 2) if reg0_int else '',
            'p90_regret_m0_interior_pct': round(float(np.percentile(reg0_int, 90)), 2) if reg0_int else '',
            'max_regret_m0_interior_pct': round(float(np.max(reg0_int)), 2) if reg0_int else '',
            'count_regret_m0_gt1_interior': sum(1 for x in reg0_int if x > 1.0) if reg0_int else 0,
        })

    summary_rows.append({
        'array': 'All_CT_Pooled', 'subset': 'PolicyI_NoOMDiff', 'n_points': p1_total,
        'corner_m0_count': p1_m0_count, 'corner_m0_pct': round(100.0 * p1_m0_count / p1_total, 2),
        'band_3_5_count': 0, 'band_3_5_pct': 0.0,
        'other_interior_count': 0, 'other_interior_pct': 0.0,
        'any_interior_pct': 0.0,
        'median_regret_m4_band35_pct': '',
        'max_regret_m4_band35_pct': '',
        'median_regret_m4_interior_pct': '',
        'p90_regret_m4_interior_pct': '',
        'max_regret_m4_interior_pct': '',
        'count_regret_m4_gt1_interior': 0,
        'median_regret_m0_interior_pct': '',
        'p90_regret_m0_interior_pct': '',
        'max_regret_m0_interior_pct': '',
        'count_regret_m0_gt1_interior': 0,
    })

    write_csv('case_E4_consistency_map.csv', box_rows)
    write_csv('case_E4_consistency_summary.csv', summary_rows)
    print(f"E4 consistency mapping completed: {len(box_rows)} 4D Policy II points + {p1_total} Policy I points.")
    for r in summary_rows:
        if r['array'] == 'All_CT_Pooled' or r['subset'] == 'Full_4D_Box':
            print(f"  {r['array']:13s} | {r['subset']:18s} | N={r['n_points']:4d} | m*=0: {r['corner_m0_pct']:6.2f}% | m* in {{3..5}}: {r['band_3_5_pct']:6.2f}% | any int: {r['any_interior_pct']:6.2f}%")
    return box_rows, summary_rows


def run_case_E5_coal_comparison(arrays: dict):
    """
    E5: Reverse-order Coal steam array (Area 1, lambda2 > lambda1), rate-swapped Coal
    counterfactual (fixed geometry, lambda1 > lambda2), and CT arrays, plus E3-style
    gamma threshold attribution split.
    """
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E5: REVERSE-ORDER COAL ARRAY, SWAPPED COUNTERFACTUAL & CT")
    print("="*80)
    specs = [('Independent', None, 0.0)]
    for branch_name, mf_val in (('Rotor', MF_ROTOR), ('HGP', MF_HGP)):
        for rho in RHO_CORE_GRID:
            specs.append((branch_name, rho, gamma_from_mf_rho(mf_val, rho)))

    coal_swapped = dict(
        arrays['Coal_Area1'],
        name='Coal_Area1_Swapped',
        lam1=arrays['Coal_Area1']['lam2'],
        lam2=arrays['Coal_Area1']['lam1'],
        mttf1=arrays['Coal_Area1']['mttf2'],
        mttf2=arrays['Coal_Area1']['mttf1'],
    )
    ct_area1_swapped = dict(
        arrays['CT_Area1'],
        name='CT_Area1_Swapped',
        lam1=arrays['Coal_Area1']['lam1'],
        lam2=arrays['Coal_Area1']['lam2'],
        mttf1=arrays['Coal_Area1']['mttf1'],
        mttf2=arrays['Coal_Area1']['mttf2'],
    )
    eval_arrays = {
        'Coal_Area1': arrays['Coal_Area1'],
        'Coal_Area1_Swapped': coal_swapped,
        'CT_Area1': arrays['CT_Area1'],
        'CT_Area1_Swapped': ct_area1_swapped,
        'CT_Area2': arrays['CT_Area2'],
        'CT_Area3': arrays['CT_Area3'],
    }

    rows = []
    for name in ('Coal_Area1', 'Coal_Area1_Swapped', 'CT_Area1', 'CT_Area2', 'CT_Area3'):
        a = eval_arrays[name]
        r1_init = a['m'] * a['lam1']
        r2_init = a['n_minus_m'] * a['lam2']
        p_first_type2 = r2_init / (r1_init + r2_init)
        w2_drop_pct = a['w2'] / a['W0'] * 100.0
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            ctmc0 = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], 0.0, 0.0)
            mttf0 = ctmc0.mttf
            for mech_label, rho_val, g_val in specs:
                ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], g_val, g_val)
                grid, P_mat = SystemOptimizer.precompute_grid_probs(
                    ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(2000.0, 6.0 * ctmc.mttf), n_grid=300
                )
                mttf_ratio = ctmc.mttf / mttf0
                for c2 in COST_RATIOS:
                    model = PolicyI_CostModel(ctmc, 1.0, c2)
                    t_opt, bzm_opt = SystemOptimizer.optimize_t_from_precomputed(model, grid, P_mat)
                    bzm_inf = c2 / ctmc.mttf
                    cm_gap_pct = (bzm_inf - bzm_opt) / bzm_inf * 100.0
                    rows.append({
                        'array': name, 'ordering': 'lambda2>lambda1' if a['lam2'] > a['lam1'] else 'lambda1>lambda2',
                        'n': a['n'], 'm': a['m'], 'W0': a['W0'], 'k_frac': kf, 'k': k, 'M': ctmc.M,
                        'p_first_type2_pct': round(p_first_type2 * 100.0, 2),
                        'w2_drop_pct': round(w2_drop_pct, 2),
                        'c2_c1': int(c2),
                        'mechanism': mech_label,
                        'rho': '' if rho_val is None else round(rho_val, 2),
                        'gamma': round(g_val, 2),
                        'mttf_h': round(ctmc.mttf, 2), 'mttf_retention_pct': round(mttf_ratio * 100.0, 2),
                        't_star_h': 'inf' if np.isinf(t_opt) else round(t_opt, 2),
                        'bzm_star': round(bzm_opt, 6), 'cm_gap_pct': round(cm_gap_pct, 2),
                    })
    write_csv('case_E5_coal_vs_ct.csv', rows)

    gamma_grid = [0.0] + list(np.geomspace(0.5, 1000.0, 90))
    attr_rows = []
    for name in ('Coal_Area1', 'Coal_Area1_Swapped', 'CT_Area1', 'CT_Area1_Swapped'):
        a = eval_arrays[name]
        r1_init = a['m'] * a['lam1']
        r2_init = a['n_minus_m'] * a['lam2']
        p_first_type2 = r2_init / (r1_init + r2_init)
        w2_drop_pct = a['w2'] / a['W0'] * 100.0
        for kf in K_FRACTIONS:
            k = math.ceil(kf * a['W0'])
            for c2 in COST_RATIOS:
                _, t0, tp_found, gamma_tp, t_min, gamma_cm_1pct = _evaluate_gamma_sweep(a, k, c2, gamma_grid)
                attr_rows.append({
                    'array': name, 'ordering': 'lambda2>lambda1' if a['lam2'] > a['lam1'] else 'lambda1>lambda2',
                    'k_frac': kf, 'k': k, 'c2_c1': int(c2),
                    'p_first_type2_pct': round(p_first_type2 * 100.0, 2),
                    'w2_drop_pct': round(w2_drop_pct, 2),
                    't_at_g0_h': 'inf' if np.isinf(t0) else round(t0, 2),
                    'turning_point_found': tp_found,
                    'gamma_tp': '' if (not tp_found) else round(gamma_tp, 2),
                    't_min_h': 'inf' if np.isinf(t_min) else round(t_min, 2),
                    'gamma_cm_1pct': '' if gamma_cm_1pct is None else round(gamma_cm_1pct, 2),
                })
    write_csv('case_E5_counterfactual_attribution.csv', attr_rows)
    return rows


def run_case_E6_downtime_sensitivity(arrays: dict):
    """
    E6: Non-zero replacement/repair duration sensitivity using RTS-GMLC MTTRs
    under both continuous duty (duty_factor=1.00) and peaking duty (duty_factor=0.10).
    """
    print("\n" + "="*80)
    print("RUNNING CASE STUDY E6: NON-ZERO REPLACEMENT DURATION SENSITIVITY (MTTR)")
    print("="*80)
    specs = [
        ('Independent', None, 0.0),
        ('Rotor', 1.15, gamma_from_mf_rho(MF_ROTOR, 1.15)),
        ('Rotor', 1.10, gamma_from_mf_rho(MF_ROTOR, 1.10)),
        ('Rotor', 1.03, gamma_from_mf_rho(MF_ROTOR, 1.03)),
        ('HGP', 1.15, gamma_from_mf_rho(MF_HGP, 1.15)),
        ('HGP', 1.10, gamma_from_mf_rho(MF_HGP, 1.10)),
        ('HGP', 1.03, gamma_from_mf_rho(MF_HGP, 1.03)),
    ]
    duty_factors = [1.00, PEAKING_CF_REF]
    rows = []
    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3', 'Coal_Area1'):
        a = arrays[name]
        mttr_avg = (a['m'] * a['mttr1'] + a['n_minus_m'] * a['mttr2']) / a['n']
        if name == 'Coal_Area1':
            d_cm_cases = [('U76_U155_40h', a['mttr1'])]
        else:
            d_cm_cases = [('U55_31h', a['mttr2']), ('WeightedAvg', round(mttr_avg, 2)), ('U20_50h', a['mttr1'])]

        for kf in (0.50, 0.70, 0.90):
            k = math.ceil(kf * a['W0'])
            assert k <= a['W0']
            for mech_label, rho_val, g_val in specs:
                ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], g_val, g_val)
                grid, P_mat = SystemOptimizer.precompute_grid_probs(
                    ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(2000.0, 6.0 * ctmc.mttf), n_grid=300
                )
                for c2 in COST_RATIOS:
                    t_inst, bzm_inst = SystemOptimizer.optimize_t_from_precomputed(
                        PolicyI_CostModel(ctmc, 1.0, c2, d_pm=0.0, d_cm=0.0), grid, P_mat
                    )
                    for delta in duty_factors:
                        bzm_cal_inst = delta * bzm_inst
                        for dcm_label, d_cm in d_cm_cases:
                            for dpm_mode, d_pm in (('half', 0.5 * d_cm), ('equal', d_cm)):
                                d_pm_eff = delta * d_pm
                                d_cm_eff = delta * d_cm
                                t_ext, bzm_ext = SystemOptimizer.optimize_t_from_precomputed(
                                    PolicyI_CostModel(ctmc, 1.0, c2, d_pm=d_pm_eff, d_cm=d_cm_eff), grid, P_mat
                                )
                                bzm_cal_ext = delta * bzm_ext
                                bzm_diff_pct = (bzm_ext - bzm_inst) / bzm_inst * 100.0
                                t_diff_pct = round((t_ext - t_inst) / t_inst * 100.0, 2) if (np.isfinite(t_inst) and np.isfinite(t_ext)) else ''
                                rows.append({
                                    'array': name, 'k_frac': kf, 'k': k, 'c2_c1': int(c2),
                                    'mechanism': mech_label,
                                    'rho': '' if rho_val is None else round(rho_val, 2),
                                    'gamma': round(g_val, 2),
                                    'mttf_h': round(ctmc.mttf, 2),
                                    'duty_factor': delta,
                                    'mttr_basis': dcm_label, 'd_cm_h': d_cm,
                                    'd_pm_mode': dpm_mode, 'd_pm_h': round(d_pm, 2),
                                    't_inst_h': 'inf' if np.isinf(t_inst) else round(t_inst, 2),
                                    'bzm_inst': round(bzm_inst, 6),
                                    'bzm_cal_inst': round(bzm_cal_inst, 6),
                                    't_ext_h': 'inf' if np.isinf(t_ext) else round(t_ext, 2),
                                    'bzm_ext': round(bzm_ext, 6),
                                    'bzm_cal_ext': round(bzm_cal_ext, 6),
                                    't_shift_pct': t_diff_pct,
                                    'bzm_shift_pct': round(bzm_diff_pct, 2),
                                })
    write_csv('case_E6_downtime_sensitivity.csv', rows)
    return rows


def run_monte_carlo_validation_gamma_gt0(n_paths: int = 100000, seed: int = 42):
    """Independent Monte Carlo CTMC jump cross-validation at gamma > 0."""
    print("\n" + "="*80)
    print("RUNNING MONTE CARLO VALIDATION AT GAMMA > 0 (N = 100,000 PATHS)")
    print("="*80)
    rng = np.random.default_rng(seed)
    cases = [
        ('Synth_Reg1', 15, 5, 15, 1, 2, 0.2, 0.1, 0.8, 0.8, 1.5),
        ('Synth_Reg2', 15, 5, 15, 1, 2, 0.2, 0.1, 1.5, 0.5, 1.5),
        ('Synth_Reg3', 15, 5, 15, 1, 2, 0.2, 0.1, 1.5, 1.5, 1.5),
        ('CT_Area1_Rot115', 11, 4, 326, 20, 55, 1.0 / 450.0, 1.0 / 969.0, 4.96, 4.96, 150.0),
        ('CT_Area1_HGP115', 11, 4, 326, 20, 55, 1.0 / 450.0, 1.0 / 969.0, 12.88, 12.88, 100.0),
        ('CT_Area1_Asym', 11, 4, 326, 20, 55, 1.0 / 450.0, 1.0 / 969.0, 4.96, 12.88, 100.0),
        ('CT_Area1_k05_Rot103', 11, 4, 233, 20, 55, 1.0 / 450.0, 1.0 / 969.0, 23.45, 23.45, 80.0),
        ('CT_Area1_k05_HGP103', 11, 4, 233, 20, 55, 1.0 / 450.0, 1.0 / 969.0, 60.90, 60.90, 60.0),
    ]
    rows = []
    for case_id, n, m, k, w1, w2, l1, l2, g1, g2, t_probe in cases:
        ctmc = WeightedSystemCTMC(n, m, k, w1, w2, l1, l2, g1, g2)
        mttf_exact = float(ctmc.mttf)
        r_exact = float(ctmc.reliability(t_probe))

        i_cur = np.full(n_paths, m, dtype=np.int32)
        j_cur = np.full(n_paths, n - m, dtype=np.int32)
        t_acc = np.zeros(n_paths, dtype=np.float64)
        W0 = float(m * w1 + (n - m) * w2)
        for _ in range(n + 1):
            W_ij = i_cur * w1 + j_cur * w2
            alive = W_ij >= k
            if not np.any(alive):
                break
            idx = np.where(alive)[0]
            ic = i_cur[idx]
            jc = j_cur[idx]
            rho = W0 / W_ij[idx].astype(np.float64)
            log_rho = np.where(rho > 1.0, np.log(rho), 0.0)
            scale1 = np.exp(np.minimum(g1 * log_rho, 650.0))
            scale2 = np.exp(np.minimum(g2 * log_rho, 650.0))
            r1_rate = ic * l1 * scale1
            r2_rate = jc * l2 * scale2
            tot = r1_rate + r2_rate
            t_acc[idx] += rng.exponential(1.0 / tot)
            choose1 = rng.random(len(idx)) < (r1_rate / tot)
            i_cur[idx] -= choose1.astype(np.int32)
            j_cur[idx] -= (~choose1).astype(np.int32)

        mttf_mc = float(np.mean(t_acc))
        r_mc = float(np.mean(t_acc > t_probe))
        rel_err_pct = abs(mttf_mc - mttf_exact) / mttf_exact * 100.0
        abs_err_r = abs(r_mc - r_exact)
        rows.append({
            'case_id': case_id, 'n': n, 'm': m, 'k': k,
            'gamma1': g1, 'gamma2': g2, 't_probe': t_probe,
            'mttf_exact': round(mttf_exact, 4), 'mttf_mc': round(mttf_mc, 4),
            'mttf_rel_err_pct': round(rel_err_pct, 4),
            'r_exact': round(r_exact, 4), 'r_mc': round(r_mc, 4),
            'r_abs_err': round(abs_err_r, 4),
        })
    write_csv('mc_validation_gamma_gt0.csv', rows)
    return rows


class _CappedWeightedSystemCTMC(WeightedSystemCTMC):
    """WeightedSystemCTMC with per-unit overload ratio capped at rho_max."""
    def __init__(self, n: int, m: int, k: int, w1: int, w2: int,
                 lambda1_0: float, lambda2_0: float,
                 gamma1: float, gamma2: float, rho_max: float = 1.15):
        self.rho_max = float(rho_max)
        super().__init__(n, m, k, w1, w2, lambda1_0, lambda2_0, gamma1, gamma2)

    def _build_generator_matrix(self):
        self.Q_W = np.zeros((self.M, self.M), dtype=float)
        self.q_F = np.zeros(self.M, dtype=float)
        self.fatal_rate1 = np.zeros(self.M, dtype=float)
        self.fatal_rate2 = np.zeros(self.M, dtype=float)
        for idx, (i, j) in enumerate(self.states):
            Wij = i * self.w1 + j * self.w2
            ratio = min(self.rho_max, self.W0 / Wij)
            log_ratio = np.log(ratio) if ratio > 1.0 else 0.0
            scale1 = np.exp(min(self.gamma1 * log_ratio, 650.0)) if log_ratio > 0.0 else 1.0
            scale2 = np.exp(min(self.gamma2 * log_ratio, 650.0)) if log_ratio > 0.0 else 1.0
            rate1 = i * self.lambda1_0 * scale1
            rate2 = j * self.lambda2_0 * scale2
            if i > 0:
                ns1 = (i - 1, j)
                if ns1 in self.state_to_idx:
                    self.Q_W[idx, self.state_to_idx[ns1]] += rate1
                else:
                    self.q_F[idx] += rate1
                    self.fatal_rate1[idx] += rate1
            if j > 0:
                ns2 = (i, j - 1)
                if ns2 in self.state_to_idx:
                    self.Q_W[idx, self.state_to_idx[ns2]] += rate2
                else:
                    self.q_F[idx] += rate2
                    self.fatal_rate2[idx] += rate2
            self.Q_W[idx, idx] = -(rate1 + rate2)
        self.Q_inv = np.linalg.inv(self.Q_W)
        self.Q_inv_e = self.Q_inv.dot(self.e)
        self.mttf = -float(self.alpha.dot(self.Q_inv_e))


class _RepairableWeightedSystemCTMC(WeightedSystemCTMC):
    """WeightedSystemCTMC extended with online unit repair transitions inside W."""
    def __init__(self, n: int, m: int, k: int, w1: int, w2: int,
                 lambda1_0: float, lambda2_0: float,
                 gamma1: float, gamma2: float, mu1: float, mu2: float):
        self.mu1 = float(mu1)
        self.mu2 = float(mu2)
        super().__init__(n, m, k, w1, w2, lambda1_0, lambda2_0, gamma1, gamma2)

    def _build_generator_matrix(self):
        self.Q_W = np.zeros((self.M, self.M), dtype=float)
        self.q_F = np.zeros(self.M, dtype=float)
        self.fatal_rate1 = np.zeros(self.M, dtype=float)
        self.fatal_rate2 = np.zeros(self.M, dtype=float)
        for idx, (i, j) in enumerate(self.states):
            Wij = i * self.w1 + j * self.w2
            ratio = self.W0 / Wij
            log_ratio = np.log(ratio) if ratio > 1.0 else 0.0
            scale1 = np.exp(min(self.gamma1 * log_ratio, 650.0)) if log_ratio > 0.0 else 1.0
            scale2 = np.exp(min(self.gamma2 * log_ratio, 650.0)) if log_ratio > 0.0 else 1.0
            rate1 = i * self.lambda1_0 * scale1
            rate2 = j * self.lambda2_0 * scale2
            rep1 = (self.m - i) * self.mu1
            rep2 = (self.n - self.m - j) * self.mu2
            if i > 0:
                ns1 = (i - 1, j)
                if ns1 in self.state_to_idx:
                    self.Q_W[idx, self.state_to_idx[ns1]] += rate1
                else:
                    self.q_F[idx] += rate1
                    self.fatal_rate1[idx] += rate1
            if j > 0:
                ns2 = (i, j - 1)
                if ns2 in self.state_to_idx:
                    self.Q_W[idx, self.state_to_idx[ns2]] += rate2
                else:
                    self.q_F[idx] += rate2
                    self.fatal_rate2[idx] += rate2
            if rep1 > 0.0 and (i + 1, j) in self.state_to_idx:
                self.Q_W[idx, self.state_to_idx[(i + 1, j)]] += rep1
            if rep2 > 0.0 and (i, j + 1) in self.state_to_idx:
                self.Q_W[idx, self.state_to_idx[(i, j + 1)]] += rep2
            self.Q_W[idx, idx] = -(rate1 + rate2 + rep1 + rep2)
        self.Q_inv = np.linalg.inv(self.Q_W)
        self.Q_inv_e = self.Q_inv.dot(self.e)
        self.mttf = -float(self.alpha.dot(self.Q_inv_e))


def run_supplemental_sensitivity_checks(arrays: dict):
    """
    Runs all supplemental sensitivity, structural-premise, equal-count,
    Shapley attribution, and priced-downtime checks into
    results/supplemental_sensitivity_checks.csv.
    """
    print("\n" + "="*80)
    print("RUNNING SUPPLEMENTAL SENSITIVITY & STRUCTURAL CHECKS")
    print("="*80)
    rows = []

    # 1. B1: Nameplate-capped dispatch (CT_Area3, k/W0=0.50) & k/W0=0.90 max attained overload
    t_ind_map = _compute_ct_independent_optima(arrays)
    a3 = arrays['CT_Area3']
    k_a3_05 = math.ceil(0.50 * a3['W0'])
    for mech_label, g_val in (('Rotor_115', gamma_from_mf_rho(MF_ROTOR, 1.15)),
                              ('HGP_115', gamma_from_mf_rho(MF_HGP, 1.15))):
        ctmc_cap = _CappedWeightedSystemCTMC(
            a3['n'], a3['m'], k_a3_05, a3['w1'], a3['w2'],
            a3['lam1'], a3['lam2'], g_val, g_val, rho_max=1.15
        )
        grid, P_mat = SystemOptimizer.precompute_grid_probs(
            ctmc_cap, t_lb=max(0.5, 1e-3 * ctmc_cap.mttf), t_ub=max(1000.0, 6.0 * ctmc_cap.mttf), n_grid=300
        )
        for c2 in (5.0, 20.0):
            mod = PolicyI_CostModel(ctmc_cap, 1.0, c2)
            t_opt, eta_opt = SystemOptimizer.optimize_t_from_precomputed(mod, grid, P_mat)
            t_naive = t_ind_map[('CT_Area3', 0.50, c2)]
            eta_naive = (c2 / ctmc_cap.mttf) if np.isinf(t_naive) else mod.cost_rate(t_naive)
            pen_pct = (eta_naive - eta_opt) / eta_opt * 100.0
            rows.append({
                'check_group': 'B1_capped_dispatch',
                'scenario_id': f'CT_Area3_{mech_label}_c{int(c2)}',
                'array': 'CT_Area3', 'k_frac': 0.50, 'k_mw': k_a3_05,
                'gamma_1': round(g_val, 4), 'gamma_2': round(g_val, 4),
                'param_a': f'c2_c1={int(c2)}', 'param_b': 'rho_max=1.15',
                'mttf_h': round(ctmc_cap.mttf, 2),
                't_star_h': 'inf' if np.isinf(t_opt) else round(t_opt, 2),
                'eta_star': round(eta_opt, 6),
                'metric_val': round(pen_pct, 2),
                'notes': f'naive_t_h={round(t_naive, 2)};naive_penalty_pct',
            })

    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3', 'Coal_Area1'):
        a = arrays[name]
        k90 = math.ceil(0.90 * a['W0'])
        ctmc90 = WeightedSystemCTMC(a['n'], a['m'], k90, a['w1'], a['w2'], a['lam1'], a['lam2'], 0.0, 0.0)
        rho_max_att = max(ctmc90.W0 / (i * ctmc90.w1 + j * ctmc90.w2) for i, j in ctmc90.states)
        rows.append({
            'check_group': 'B1_capped_dispatch',
            'scenario_id': f'{name}_k09_max_rho',
            'array': name, 'k_frac': 0.90, 'k_mw': k90,
            'gamma_1': 0.0, 'gamma_2': 0.0,
            'param_a': f'W0={ctmc90.W0}', 'param_b': f'k={k90}',
            'mttf_h': round(ctmc90.mttf, 2),
            't_star_h': '', 'eta_star': '',
            'metric_val': round(rho_max_att, 3),
            'notes': 'max_attained_overload_ratio_W0_over_Wij',
        })

    # 2. B2: Online unit repair CTMC check (CT_Area1, k/W0=0.70, Rotor rho=1.15, c2/c1=5)
    a1 = arrays['CT_Area1']
    k_a1_07 = math.ceil(0.70 * a1['W0'])
    g_rot115 = gamma_from_mf_rho(MF_ROTOR, 1.15)
    ctmc_rep = _RepairableWeightedSystemCTMC(
        a1['n'], a1['m'], k_a1_07, a1['w1'], a1['w2'],
        a1['lam1'], a1['lam2'], g_rot115, g_rot115,
        mu1=1.0 / a1['mttr1'], mu2=1.0 / a1['mttr2']
    )
    t_rep, eta_rep = SystemOptimizer.optimize_t_policy_I(
        ctmc_rep, 1.0, 5.0,
        t_lb=max(0.5, 1e-3 * ctmc_rep.mttf),
        t_ub=max(2000.0, 6.0 * ctmc_rep.mttf), n_grid=300
    )
    h_inf = float(-np.max(np.real(np.linalg.eigvals(ctmc_rep.Q_W))))
    h_inf_mttf = h_inf * ctmc_rep.mttf
    assert np.isinf(t_rep) and h_inf_mttf < 1.25
    rows.append({
        'check_group': 'B2_online_repair',
        'scenario_id': 'CT_Area1_k07_Rot115_c5_repairable',
        'array': 'CT_Area1', 'k_frac': 0.70, 'k_mw': k_a1_07,
        'gamma_1': round(g_rot115, 4), 'gamma_2': round(g_rot115, 4),
        'param_a': f'mu1=1/{int(a1["mttr1"])}', 'param_b': f'mu2=1/{int(a1["mttr2"])}',
        'mttf_h': round(ctmc_rep.mttf, 2),
        't_star_h': 'inf' if np.isinf(t_rep) else round(t_rep, 2),
        'eta_star': round(eta_rep, 6),
        'metric_val': round(h_inf_mttf, 4),
        'notes': f'h_inf={h_inf:.6e};ratio_h_inf_MTTF_lt_1.25',
    })

    # 3. E2b: Equal-count control (5xU20 + 5xU55, W0=375 MW, k/W0=0.70 -> 263 MW, rho=1.15, c2/c1=5)
    k_eq = math.ceil(0.70 * 375)
    for pair_label, b1, b2 in (
        ('Rotor_Rotor', MF_ROTOR, MF_ROTOR),
        ('HGP_Rotor', MF_HGP, MF_ROTOR),
        ('Rotor_HGP', MF_ROTOR, MF_HGP),
        ('HGP_HGP', MF_HGP, MF_HGP),
    ):
        g1 = gamma_from_mf_rho(b1, 1.15)
        g2 = gamma_from_mf_rho(b2, 1.15)
        ctmc_eq = WeightedSystemCTMC(10, 5, k_eq, 20, 55, a1['lam1'], a1['lam2'], g1, g2)
        t_eq, eta_eq = SystemOptimizer.optimize_t_policy_I(
            ctmc_eq, 1.0, 5.0,
            t_lb=max(0.5, 1e-3 * ctmc_eq.mttf),
            t_ub=max(1000.0, 6.0 * ctmc_eq.mttf), n_grid=300
        )
        rows.append({
            'check_group': 'E2b_equal_count',
            'scenario_id': f'Equal_5U20_5U55_{pair_label}',
            'array': 'Equal_5U20_5U55', 'k_frac': 0.70, 'k_mw': k_eq,
            'gamma_1': round(g1, 2), 'gamma_2': round(g2, 2),
            'param_a': 'rho=1.15', 'param_b': 'c2_c1=5',
            'mttf_h': round(ctmc_eq.mttf, 2),
            't_star_h': 'inf' if np.isinf(t_eq) else round(t_eq, 2),
            'eta_star': round(eta_eq, 6),
            'metric_val': round(eta_eq, 6),
            'notes': 'equal_count_control_W0_375MW',
        })

    # 4a. E4 Iso-capacity comparison (W0=465 MW, k=326 MW, Rotor 1.15, r_OM=1.9574, c_pen=15)
    c_rep1, c_rep2 = 1.0, EIA_OM_UNIT_RATIO
    c_ref1_base, c_ref2_base = 0.15, 0.15 * EIA_OM_UNIT_RATIO
    for iso_id, n_iso, m_iso in (('4U20_7U55_n11', 11, 4), ('15U20_3U55_n18', 18, 15)):
        ctmc_iso = WeightedSystemCTMC(
            n_iso, m_iso, k_a1_07, 20, 55, a1['lam1'], a1['lam2'], g_rot115, g_rot115
        )
        t_iso, eta_iso = SystemOptimizer.optimize_t_policy_II(
            ctmc_iso, c0=2.0, c_pen=15.0,
            c_rep1=c_rep1, c_rep2=c_rep2, c_ref1=c_ref1_base, c_ref2=c_ref2_base,
            t_lb=max(0.5, 1e-3 * ctmc_iso.mttf), t_ub=max(1500.0, 6.0 * ctmc_iso.mttf), n_grid=150
        )
        rows.append({
            'check_group': 'E4_iso_capacity_and_c0_cref',
            'scenario_id': f'IsoCap_{iso_id}',
            'array': 'CT_Area1_IsoCap', 'k_frac': 0.70, 'k_mw': k_a1_07,
            'gamma_1': round(g_rot115, 4), 'gamma_2': round(g_rot115, 4),
            'param_a': f'm={m_iso}', 'param_b': f'n={n_iso}',
            'mttf_h': round(ctmc_iso.mttf, 2),
            't_star_h': 'inf' if np.isinf(t_iso) else round(t_iso, 2),
            'eta_star': round(eta_iso, 6),
            'metric_val': round(eta_iso, 6),
            'notes': 'W0=465_k=326_rOM=1.9574_cpen=15',
        })

    # 4b. E4 (c0, c_ref1) sensitivity on CT_Area1 (k/W0=0.70, HGP 1.15, r_OM=1.9574, c_pen=15)
    g_hgp115 = gamma_from_mf_rho(MF_HGP, 1.15)
    ctmcs_s = {}
    pre_s = {}
    for m_s in range(0, a1['n'] + 1):
        if m_s * a1['w1'] + (a1['n'] - m_s) * a1['w2'] >= k_a1_07:
            c_s = WeightedSystemCTMC(a1['n'], m_s, k_a1_07, a1['w1'], a1['w2'], a1['lam1'], a1['lam2'], g_hgp115, g_hgp115)
            ctmcs_s[m_s] = c_s
            pre_s[m_s] = SystemOptimizer.precompute_grid_probs(
                c_s, t_lb=max(0.5, 1e-3 * c_s.mttf), t_ub=max(1500.0, 6.0 * c_s.mttf), n_grid=150
            )
    for c0_v, cref1_v in ((1.0, 0.15), (2.0, 0.15), (4.0, 0.15), (2.0, 0.05), (2.0, 0.30)):
        om_r_e4 = round(EIA_OM_UNIT_RATIO, 4)
        cref2_v = om_r_e4 * cref1_v
        best_m_s, best_t_s, best_eta_s = -1, float('inf'), float('inf')
        eta_m4_s = float('inf')
        for m_s, c_s in ctmcs_s.items():
            mod_s = PolicyII_CostModel(
                c_s, c0=c0_v, c_pen=15.0,
                c_rep1=1.0, c_rep2=om_r_e4, c_ref1=cref1_v, c_ref2=cref2_v
            )
            g_s, P_s = pre_s[m_s]
            t_s, eta_s = SystemOptimizer.optimize_t_from_precomputed(mod_s, g_s, P_s)
            if m_s == 4:
                eta_m4_s = eta_s
            if eta_s < best_eta_s:
                best_eta_s, best_m_s, best_t_s = eta_s, m_s, t_s
        reg_m4_s = (eta_m4_s - best_eta_s) / best_eta_s * 100.0
        rows.append({
            'check_group': 'E4_iso_capacity_and_c0_cref',
            'scenario_id': f'Sens_c0_{c0_v}_cref1_{cref1_v}',
            'array': 'CT_Area1', 'k_frac': 0.70, 'k_mw': k_a1_07,
            'gamma_1': round(g_hgp115, 4), 'gamma_2': round(g_hgp115, 4),
            'param_a': f'c0={c0_v};m*={best_m_s}', 'param_b': f'cref1={cref1_v}',
            'mttf_h': round(ctmcs_s[best_m_s].mttf, 2),
            't_star_h': 'inf' if np.isinf(best_t_s) else round(best_t_s, 2),
            'eta_star': round(best_eta_s, 6),
            'metric_val': round(reg_m4_s, 2),
            'notes': f'm_star={best_m_s};regret_m4_pct',
        })

    # 4c. E5 Reverse counterfactual Shapley attribution at k/W0=0.70, c2/c1=5
    attr_path = os.path.join(RESULTS_DIR, 'case_E5_counterfactual_attribution.csv')
    with open(attr_path, 'r', encoding='utf-8') as f_attr:
        attr_map = {
            r['array']: r for r in csv.DictReader(f_attr)
            if abs(float(r['k_frac']) - 0.70) < 1e-6 and int(r['c2_c1']) == 5
        }
    g_tp_coal = float(attr_map['Coal_Area1']['gamma_tp'])
    g_tp_coal_sw = float(attr_map['Coal_Area1_Swapped']['gamma_tp'])
    g_tp_ct = float(attr_map['CT_Area1']['gamma_tp'])
    g_tp_ct_sw = float(attr_map['CT_Area1_Swapped']['gamma_tp'])
    dir_tp = (g_tp_coal_sw - g_tp_coal) / (g_tp_ct - g_tp_coal) * 100.0
    rev_tp = (g_tp_ct - g_tp_ct_sw) / (g_tp_ct - g_tp_coal) * 100.0
    shap_tp = 0.5 * (dir_tp + rev_tp)

    g_cm_coal = float(attr_map['Coal_Area1']['gamma_cm_1pct'])
    g_cm_coal_sw = float(attr_map['Coal_Area1_Swapped']['gamma_cm_1pct'])
    g_cm_ct = float(attr_map['CT_Area1']['gamma_cm_1pct'])
    g_cm_ct_sw = float(attr_map['CT_Area1_Swapped']['gamma_cm_1pct'])
    dir_cm = (g_cm_coal_sw - g_cm_coal) / (g_cm_ct - g_cm_coal) * 100.0
    rev_cm = (g_cm_ct - g_cm_ct_sw) / (g_cm_ct - g_cm_coal) * 100.0
    shap_cm = 0.5 * (dir_cm + rev_cm)

    for metric_lbl, ct_sw_v, dir_v, rev_v, shap_v in (
        ('gamma_tp', g_tp_ct_sw, dir_tp, rev_tp, shap_tp),
        ('gamma_cm_1pct', g_cm_ct_sw, dir_cm, rev_cm, shap_cm),
    ):
        rows.append({
            'check_group': 'E4_iso_capacity_and_c0_cref',
            'scenario_id': f'E5_Shapley_{metric_lbl}',
            'array': 'CT_Area1_Swapped', 'k_frac': 0.70, 'k_mw': k_a1_07,
            'gamma_1': round(ct_sw_v, 2), 'gamma_2': round(ct_sw_v, 2),
            'param_a': f'dir={dir_v:.1f}%', 'param_b': f'rev={rev_v:.1f}%',
            'mttf_h': '', 't_star_h': '', 'eta_star': '',
            'metric_val': round(shap_v, 1),
            'notes': f'shapley_rate_ordering_pct_{metric_lbl}',
        })

    # 5. E6 Opportunity-cost-priced downtime (c_d = delta * c2 / MTTF) across all 2,628 finite rows
    e6_specs = [
        ('Independent', 0.0),
        ('Rotor', gamma_from_mf_rho(MF_ROTOR, 1.15)),
        ('Rotor', gamma_from_mf_rho(MF_ROTOR, 1.10)),
        ('Rotor', gamma_from_mf_rho(MF_ROTOR, 1.03)),
        ('HGP', gamma_from_mf_rho(MF_HGP, 1.15)),
        ('HGP', gamma_from_mf_rho(MF_HGP, 1.10)),
        ('HGP', gamma_from_mf_rho(MF_HGP, 1.03)),
    ]
    n_finite = 0
    n_inv_unpriced = 0
    n_inv_priced = 0
    shifts_k07_c5 = {(delta, round(g_val, 2)): [] for delta in (1.00, PEAKING_CF_REF) for _, g_val in e6_specs}

    for name in ('CT_Area1', 'CT_Area2', 'CT_Area3', 'Coal_Area1'):
        a = arrays[name]
        mttr_avg = (a['m'] * a['mttr1'] + a['n_minus_m'] * a['mttr2']) / a['n']
        if name == 'Coal_Area1':
            d_cm_cases = [('U76_U155_40h', a['mttr1'])]
        else:
            d_cm_cases = [('U55_31h', a['mttr2']), ('WeightedAvg', round(mttr_avg, 2)), ('U20_50h', a['mttr1'])]
        for kf in (0.50, 0.70, 0.90):
            k = math.ceil(kf * a['W0'])
            for _, g_val in e6_specs:
                ctmc = WeightedSystemCTMC(a['n'], a['m'], k, a['w1'], a['w2'], a['lam1'], a['lam2'], g_val, g_val)
                grid, P_mat = SystemOptimizer.precompute_grid_probs(
                    ctmc, t_lb=max(0.5, 1e-3 * ctmc.mttf), t_ub=max(2000.0, 6.0 * ctmc.mttf), n_grid=300
                )
                for c2 in COST_RATIOS:
                    t_inst, _ = SystemOptimizer.optimize_t_from_precomputed(
                        PolicyI_CostModel(ctmc, 1.0, c2, d_pm=0.0, d_cm=0.0), grid, P_mat
                    )
                    if not np.isfinite(t_inst):
                        continue
                    for delta in (1.00, PEAKING_CF_REF):
                        for _, d_cm in d_cm_cases:
                            for d_pm in (0.5 * d_cm, d_cm):
                                n_finite += 1
                                d_pm_eff = delta * d_pm
                                d_cm_eff = delta * d_cm
                                if (1.0 / d_pm_eff) < (c2 / (ctmc.mttf + d_cm_eff)):
                                    n_inv_unpriced += 1
                                c_d_op = (c2 / ctmc.mttf) * delta
                                c1_eff = 1.0 + c_d_op * d_pm
                                c2_eff = c2 + c_d_op * d_cm
                                if (c1_eff / d_pm_eff) < (c2_eff / (ctmc.mttf + d_cm_eff)):
                                    n_inv_priced += 1
                                t_pr, _ = SystemOptimizer.optimize_t_from_precomputed(
                                    PolicyI_CostModel(ctmc, c1_eff, c2_eff, d_pm=d_pm_eff, d_cm=d_cm_eff),
                                    grid, P_mat
                                )
                                if (name != 'Coal_Area1') and (abs(kf - 0.70) < 1e-6) and (int(c2) == 5):
                                    sh_pct = (t_pr - t_inst) / t_inst * 100.0
                                    key = (delta, round(g_val, 2))
                                    if key in shifts_k07_c5:
                                        shifts_k07_c5[key].append(sh_pct)

    assert n_finite == 2628, f"Expected 2628 finite E6 rows, got {n_finite}"
    assert n_inv_unpriced == 815, f"Expected 815 unpriced inversions, got {n_inv_unpriced}"
    assert n_inv_priced == 0, f"Expected 0 priced inversions, got {n_inv_priced}"

    rows.append({
        'check_group': 'E6_priced_downtime',
        'scenario_id': 'All_2628_finite_inversion_check',
        'array': 'All_4_Arrays', 'k_frac': '', 'k_mw': '',
        'gamma_1': '', 'gamma_2': '',
        'param_a': f'n_finite={n_finite}', 'param_b': f'inv_cd0={n_inv_unpriced}',
        'mttf_h': '', 't_star_h': '', 'eta_star': '',
        'metric_val': n_inv_priced,
        'notes': 'zero_inversions_under_priced_downtime_cd_delta_c2_over_MTTF',
    })
    for delta in (1.00, PEAKING_CF_REF):
        for g_r in (0.0, 4.96, 12.88, 23.45):
            vals = shifts_k07_c5[(delta, g_r)]
            mn, mx = min(vals), max(vals)
            rows.append({
                'check_group': 'E6_priced_downtime',
                'scenario_id': f'Shift_delta_{delta:.2f}_g_{g_r:.2f}',
                'array': 'CT_Areas_1_2_3', 'k_frac': 0.70, 'k_mw': '',
                'gamma_1': g_r, 'gamma_2': g_r,
                'param_a': f'delta={delta:.2f}', 'param_b': f'min_shift_pct={mn:.2f}',
                'mttf_h': '', 't_star_h': '', 'eta_star': '',
                'metric_val': round(mx, 2),
                'notes': f'max_t_star_shift_pct_k07_c5_under_priced_downtime',
            })

    write_csv('supplemental_sensitivity_checks.csv', rows)
    print(f"Supplemental sensitivity checks completed: {len(rows)} rows written.")
    return rows


if __name__ == '__main__':
    res_t2 = run_table_2_baseline()
    res_t3 = run_table_3_load_sharing()
    res_t4 = run_table_4_policy_II()
    res_t5 = run_table_5_sensitivity()
    res_mc = run_monte_carlo_validation_gamma_gt0()

    unit_params, arrays, area_max_load = load_and_verify_rts_gmlc()
    cal_band = run_gamma_calibration_table()
    res_e1 = run_case_E1_independent(arrays)
    res_e2 = run_case_E2_mechanism_branches(arrays)
    res_e2_asym = run_case_E2_asymmetric(arrays)
    res_e3_sum, res_e3_curv = run_case_E3_turning_point(arrays)
    res_e4_box, res_e4_sum = run_case_E4_consistency_map(arrays)
    res_e5 = run_case_E5_coal_comparison(arrays)
    res_e6 = run_case_E6_downtime_sensitivity(arrays)
    res_supp = run_supplemental_sensitivity_checks(arrays)

    output_data = {
        'Table2_Baseline': res_t2,
        'Table3_LoadSharing': res_t3,
        'Table4_PolicyII': res_t4['all_evaluations'],
        'Table4_Optimum': {
            'm_star': res_t4['m_star'],
            't_star': res_t4['t_star'],
            'bzm_star': res_t4['bzm_star']
        },
        'Table5_Sensitivity': res_t5,
        'CaseStudy_Meta': {
            'rotor_branch': {'MF': MF_ROTOR, 'rho_range': [1.03, 1.15],
                             'gamma_range': [round(ROTOR_MIN, 4), round(ROTOR_MAX, 4)]},
            'hgp_branch': {'MF': MF_HGP, 'rho_range': [1.03, 1.15],
                           'gamma_range': [round(HGP_MIN, 4), round(HGP_MAX, 4)]},
            'eia_om_unit_ratio': round(EIA_OM_UNIT_RATIO, 4),
            'area_peak_load_mw': area_max_load,
            'arrays': arrays,
        },
        'CaseStudy_GammaCalibrationBand': cal_band,
        'CaseStudy_E4_ConsistencySummary': res_e4_sum,
    }

    with open(os.path.join(RESULTS_DIR, 'simulation_results.json'), 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=4)

    print("\nAll synthetic benchmark and RTS-GMLC case-study experiments completed successfully.")
