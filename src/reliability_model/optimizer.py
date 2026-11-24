"""
Optimization Engine for Preventive Replacement Age (t*) and Component-Mix Design (m*).
Implements Algorithm 1 for Mixed-Integer Nonlinear Programming (MINLP) using a
two-stage grid-bracketed global-to-local search with asymptotic purely-corrective fallback
and mandatory global-grid optimality assertions on every call.
"""

from typing import Tuple, Dict, Any, Optional
import numpy as np
from scipy.optimize import minimize_scalar
from .ctmc_model import WeightedSystemCTMC
from .policies import PolicyI_CostModel, PolicyII_CostModel


class SystemOptimizer:
    """
    Solves age-replacement and structural mix optimization problems.
    """

    @staticmethod
    def precompute_grid_probs(ctmc: WeightedSystemCTMC,
                              t_lb: float, t_ub: float,
                              n_grid: int = 300) -> Tuple[np.ndarray, np.ndarray]:
        """
        Precomputes the dense two-segment uniform time grid over [t_lb, max(t_ub, 6 * MTTF)]
        and exact transient state probability rows P(t_k) = alpha * exp(Q_W * t_k).
        Reusing (grid, P_mat) across multiple cost parameterizations avoids repeated expm() calls.
        """
        t_max = max(float(t_ub), 6.0 * ctmc.mttf)
        t_split = min(t_max, 3.0 * ctmc.mttf)

        if t_split <= t_lb:
            grid = np.linspace(t_lb, t_max, n_grid)
            dt = float(grid[1] - grid[0]) if n_grid > 1 else 0.0
            P_mat = ctmc.state_probs_on_uniform_grid(float(grid[0]), dt, n_grid)
        else:
            n1 = max(2, int(0.75 * n_grid))
            n2 = max(2, n_grid - n1)
            g1 = np.linspace(t_lb, t_split, n1, endpoint=False)
            g2 = np.linspace(t_split, t_max, n2)
            dt1 = float(g1[1] - g1[0])
            dt2 = float(g2[1] - g2[0])
            P1 = ctmc.state_probs_on_uniform_grid(float(g1[0]), dt1, n1)
            P2 = ctmc.state_probs_on_uniform_grid(float(g2[0]), dt2, n2)
            grid = np.concatenate([g1, g2])
            P_mat = np.vstack([P1, P2])

        return grid, P_mat

    @staticmethod
    def optimize_t_from_precomputed(model,
                                    grid: np.ndarray,
                                    P_mat: np.ndarray) -> Tuple[float, float]:
        """
        Global-to-local minimizer operating directly on precomputed (grid, P_mat).
        Enforces global grid optimality assertions against both the grid minimum and BZM(inf).
        """
        ctmc = model.ctmc
        mttf = ctmc.mttf
        M = ctmc.M
        t_lb = float(grid[0])

        bzm_inf = float(model.asymptotic_cost_rate())
        if M == 1 and getattr(model, 'd_pm', 0.0) == 0.0 and getattr(model, 'd_cm', 0.0) == 0.0:
            t_probe = max(t_lb, 0.5 * mttf)
            if model.cost_rate(t_probe) > bzm_inf:
                return float('inf'), bzm_inf

        vals = model.cost_rate_from_probs(P_mat)
        assert len(grid) == len(vals) and len(grid) >= 4, "Global grid construction failed."
        assert np.all(np.isfinite(vals)), "Non-finite cost rate encountered on global grid."

        idx_min = int(np.argmin(vals))
        grid_best_t = float(grid[idx_min])
        grid_best_val = float(vals[idx_min])

        if grid_best_val >= bzm_inf - 1e-12:
            assert bzm_inf <= grid_best_val + 1e-12, "Asymptotic CM fallback violated grid bound."
            return float('inf'), bzm_inf

        if idx_min == len(grid) - 1:
            t_max = float(grid[-1])
            t_ext = max(t_max * 3.0, 20.0 * mttf)
            n_ext = max(60, len(grid) // 2)
            g_ext = np.linspace(t_max, t_ext, n_ext)
            dt_ext = float(g_ext[1] - g_ext[0])
            P_ext = ctmc.state_probs_on_uniform_grid(float(g_ext[0]), dt_ext, n_ext)
            v_ext = model.cost_rate_from_probs(P_ext)
            grid = np.concatenate([grid, g_ext[1:]])
            vals = np.concatenate([vals, v_ext[1:]])
            idx_min = int(np.argmin(vals))
            grid_best_t = float(grid[idx_min])
            grid_best_val = float(vals[idx_min])
            if idx_min == len(grid) - 1 or grid_best_val >= bzm_inf - 1e-12:
                return float('inf'), bzm_inf

        lo = float(grid[max(0, idx_min - 1)])
        hi = float(grid[min(len(grid) - 1, idx_min + 1)])
        res = minimize_scalar(model.cost_rate, bounds=(lo, hi), method='bounded',
                              options={'xatol': 1e-9})

        cand_t = float(res.x)
        cand_val = float(res.fun)

        # Guarantee local refinement never worsens the global grid minimum
        if grid_best_val < cand_val:
            cand_t = grid_best_t
            cand_val = grid_best_val

        if cand_val >= bzm_inf - 1e-12:
            assert bzm_inf <= grid_best_val + 1e-12, "Asymptotic CM fallback violated grid bound."
            return float('inf'), bzm_inf

        assert cand_val <= grid_best_val + 1e-11, (
            f"Refined optimum ({cand_val}) exceeded global grid minimum ({grid_best_val})."
        )
        assert cand_val <= bzm_inf + 1e-12, (
            f"Refined optimum ({cand_val}) exceeded purely corrective asymptote ({bzm_inf})."
        )
        return cand_t, cand_val

    @classmethod
    def _bracketed_minimize(cls, model, mttf: float, M: int,
                            t_lb: float, t_ub: float,
                            n_grid: int = 300) -> Tuple[float, float]:
        """
        Two-stage global-to-local minimizer avoiding flat-tail failures of Brent's bounded search.
        Returns (float('inf'), bzm_inf) when purely corrective maintenance is optimal.
        """
        if M == 1 and getattr(model, 'd_pm', 0.0) == 0.0 and getattr(model, 'd_cm', 0.0) == 0.0:
            bzm_inf = float(model.asymptotic_cost_rate())
            t_probe = max(t_lb, 0.5 * mttf)
            if model.cost_rate(t_probe) > bzm_inf:
                return float('inf'), bzm_inf

        grid, P_mat = cls.precompute_grid_probs(model.ctmc, t_lb, t_ub, n_grid=n_grid)
        return cls.optimize_t_from_precomputed(model, grid, P_mat)

    @classmethod
    def optimize_t_policy_I(cls, ctmc: WeightedSystemCTMC, c1: float, c2: float,
                            t_lb: float = 0.01, t_ub: float = 20.0,
                            n_grid: int = 300,
                            d_pm: float = 0.0, d_cm: float = 0.0) -> Tuple[float, float]:
        """
        Finds optimal replacement age t* minimizing Policy I cost rate BZM_I(t).
        Returns (t*, BZM_I*).
        """
        model = PolicyI_CostModel(ctmc, c1, c2, d_pm=d_pm, d_cm=d_cm)
        return cls._bracketed_minimize(model, ctmc.mttf, ctmc.M, t_lb, t_ub, n_grid=n_grid)

    @classmethod
    def optimize_t_policy_II(cls, ctmc: WeightedSystemCTMC,
                             c0: float = 0.5, c_pen: float = 3.0,
                             c_rep1: float = 0.15, c_rep2: float = 1.05,
                             c_ref1: float = 0.02, c_ref2: float = 0.08,
                             t_lb: float = 0.05, t_ub: float = 15.0,
                             n_grid: int = 300,
                             d_pm: float = 0.0, d_cm: float = 0.0) -> Tuple[float, float]:
        """
        Finds optimal replacement age t* minimizing Policy II cost rate BZM_II(t).
        Returns (t*, BZM_II*).
        """
        model = PolicyII_CostModel(ctmc, c0, c_pen, c_rep1, c_rep2, c_ref1, c_ref2,
                                   d_pm=d_pm, d_cm=d_cm)
        return cls._bracketed_minimize(model, ctmc.mttf, ctmc.M, t_lb, t_ub, n_grid=n_grid)

    @classmethod
    def co_optimize_mix_and_age_policy_II(cls, n: int, k: int, w1: int, w2: int,
                                          lambda1_0: float, lambda2_0: float,
                                          gamma1: float, gamma2: float,
                                          cost_params: Optional[Dict[str, float]] = None,
                                          t_lb: float = 0.05, t_ub: float = 15.0,
                                          n_grid: int = 300,
                                          d_pm: float = 0.0, d_cm: float = 0.0) -> Dict[str, Any]:
        """
        MINLP optimization: solves for optimal component mix m* and replacement age t* under Policy II.
        """
        if cost_params is None:
            cost_params = {
                'c0': 0.5, 'c_pen': 3.0,
                'c_rep1': 0.15, 'c_rep2': 1.05,
                'c_ref1': 0.02, 'c_ref2': 0.08
            }

        best_result = {
            'm_star': -1,
            't_star': -1.0,
            'bzm_star': float('inf'),
            'mttf': -1.0,
            'all_evaluations': []
        }

        for m in range(0, n + 1):
            W0 = m * w1 + (n - m) * w2
            if W0 < k:
                continue

            ctmc = WeightedSystemCTMC(n=n, m=m, k=k, w1=w1, w2=w2,
                                      lambda1_0=lambda1_0, lambda2_0=lambda2_0,
                                      gamma1=gamma1, gamma2=gamma2)

            t_opt, bzm_opt = cls.optimize_t_policy_II(
                ctmc, t_lb=t_lb, t_ub=t_ub, n_grid=n_grid,
                d_pm=d_pm, d_cm=d_cm, **cost_params
            )

            evaluation = {
                'm': m,
                'W0': W0,
                'capacity_margin': W0 - k,
                'mttf': ctmc.mttf,
                't_star': t_opt,
                'bzm_star': bzm_opt
            }
            best_result['all_evaluations'].append(evaluation)

            if bzm_opt < best_result['bzm_star']:
                best_result['bzm_star'] = bzm_opt
                best_result['m_star'] = m
                best_result['t_star'] = t_opt
                best_result['mttf'] = ctmc.mttf

        return best_result
