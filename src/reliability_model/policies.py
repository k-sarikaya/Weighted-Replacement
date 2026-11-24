"""
Maintenance Policies and Cost Rate Formulations:
Policy I: Complete System / Module Replacement (Classical Baseline Extension)
Policy II: State-Dependent Component Renewal and Preventive Refreshing
Supports both instantaneous replacement (d_pm = d_cm = 0) and non-zero
preventive/corrective renewal durations (d_pm, d_cm >= 0).
"""

import numpy as np
from .ctmc_model import WeightedSystemCTMC


class PolicyI_CostModel:
    """
    Policy I: Integrated modular replacement where entire array is replaced at age t or failure.
    """
    def __init__(self, ctmc: WeightedSystemCTMC, c1: float, c2: float,
                 d_pm: float = 0.0, d_cm: float = 0.0):
        if c1 >= c2:
            raise ValueError(f"Preventive cost c1 ({c1}) must be strictly less than corrective cost c2 ({c2}).")
        if d_pm < 0.0 or d_cm < 0.0:
            raise ValueError(f"Renewal durations must be non-negative (got d_pm={d_pm}, d_cm={d_cm}).")
        self.ctmc = ctmc
        self.c1 = float(c1)
        self.c2 = float(c2)
        self.d_pm = float(d_pm)
        self.d_cm = float(d_cm)

    def expected_cost(self, t: float) -> float:
        """E[C_I(t)] = c1 * R(t) + c2 * (1 - R(t)) = c2 - (c2 - c1) * R(t)."""
        r = self.ctmc.reliability(t)
        return self.c2 - (self.c2 - self.c1) * r

    def expected_cycle_length(self, t: float) -> float:
        """E[min(T_sys, t)] + d_pm * R(t) + d_cm * (1 - R(t))."""
        P_t = self.ctmc.state_probabilities(t)
        r = float(P_t.dot(self.ctmc.e))
        es = float((P_t - self.ctmc.alpha).dot(self.ctmc.Q_inv_e))
        return es + self.d_pm * r + self.d_cm * (1.0 - r)

    def cost_rate(self, t: float) -> float:
        """BZM_I(t) = E[C_I(t)] / (E[S(t)] + d_pm * R(t) + d_cm * (1 - R(t)))."""
        if t <= 1e-6:
            return float('inf')
        P_t = self.ctmc.state_probabilities(t)
        r = float(P_t.dot(self.ctmc.e))
        es = float((P_t - self.ctmc.alpha).dot(self.ctmc.Q_inv_e))
        denom = es + self.d_pm * r + self.d_cm * (1.0 - r)
        if denom <= 1e-12:
            return float('inf')
        ec = self.c2 - (self.c2 - self.c1) * r
        return ec / denom

    def cost_rate_from_probs(self, P_mat: np.ndarray) -> np.ndarray:
        """Vectorized cost rate evaluation from precomputed state-probability rows P(t_k)."""
        r = P_mat.dot(self.ctmc.e)
        es = (P_mat - self.ctmc.alpha).dot(self.ctmc.Q_inv_e)
        denom = es + self.d_pm * r + self.d_cm * (1.0 - r)
        ec = self.c2 - (self.c2 - self.c1) * r
        with np.errstate(divide='ignore', invalid='ignore'):
            out = np.where(denom > 1e-12, ec / denom, np.inf)
        return out

    def optimality_condition(self, t: float) -> float:
        """
        Auxiliary function g(t) = h_sys(t) * int_0^t R(u) du - [1 - R(t)] - c1 / (c2 - c1)
        for instantaneous replacement (d_pm = d_cm = 0).
        """
        r = self.ctmc.reliability(t)
        h = self.ctmc.hazard_rate(t)
        integ = self.ctmc.expected_cycle_duration(t)
        return h * integ - (1.0 - r) - (self.c1 / (self.c2 - self.c1))

    def asymptotic_cost_rate(self) -> float:
        """Purely corrective (t -> inf) cost rate: c2 / (MTTF + d_cm)."""
        return self.c2 / (self.ctmc.mttf + self.d_cm)


class PolicyII_CostModel:
    """
    Policy II: Component-level selective replacement of failed units, refreshing of surviving units,
    with intervention setup cost c0 and unscheduled failure penalty c_pen.
    """
    def __init__(self, ctmc: WeightedSystemCTMC,
                 c0: float = 0.5, c_pen: float = 3.0,
                 c_rep1: float = 0.15, c_rep2: float = 1.05,
                 c_ref1: float = 0.02, c_ref2: float = 0.08,
                 d_pm: float = 0.0, d_cm: float = 0.0):
        if d_pm < 0.0 or d_cm < 0.0:
            raise ValueError(f"Renewal durations must be non-negative (got d_pm={d_pm}, d_cm={d_cm}).")
        self.ctmc = ctmc
        self.c0 = float(c0)
        self.c_pen = float(c_pen)
        self.c_rep1 = float(c_rep1)
        self.c_rep2 = float(c_rep2)
        self.c_ref1 = float(c_ref1)
        self.c_ref2 = float(c_ref2)
        self.d_pm = float(d_pm)
        self.d_cm = float(d_cm)

        self._build_cost_vectors()

    def _build_cost_vectors(self):
        """Constructs c_pm vector and c_abs (corrective absorption cost rate) vector."""
        M = self.ctmc.M
        m = self.ctmc.m
        n = self.ctmc.n

        self.c_pm = np.zeros(M, dtype=float)
        self.c_abs = np.zeros(M, dtype=float)

        for idx, (i, j) in enumerate(self.ctmc.states):
            # PM cost in working state (i, j): failed units replaced, working units refreshed
            self.c_pm[idx] = (self.c0 +
                              (m - i) * self.c_rep1 +
                              (n - m - j) * self.c_rep2 +
                              i * self.c_ref1 +
                              j * self.c_ref2)

            # Use exact fatal transition rates already built by CTMC (consistent overflow guard)
            rate1 = self.ctmc.fatal_rate1[idx]
            if rate1 > 0.0:
                c_cm1 = (self.c0 + self.c_pen +
                         (m - (i - 1)) * self.c_rep1 +
                         (n - m - j) * self.c_rep2 +
                         (i - 1) * self.c_ref1 +
                         j * self.c_ref2)
                self.c_abs[idx] += rate1 * c_cm1

            rate2 = self.ctmc.fatal_rate2[idx]
            if rate2 > 0.0:
                c_cm2 = (self.c0 + self.c_pen +
                         (m - i) * self.c_rep1 +
                         (n - m - (j - 1)) * self.c_rep2 +
                         i * self.c_ref1 +
                         (j - 1) * self.c_ref2)
                self.c_abs[idx] += rate2 * c_cm2

        self.Q_inv_cabs = self.ctmc.Q_inv.dot(self.c_abs)

    def expected_cost(self, t: float) -> float:
        """E[C_II(t)] = P(t) * c_pm + int_0^t P(u) du * c_abs."""
        P_t = self.ctmc.state_probabilities(t)
        return float(P_t.dot(self.c_pm) + (P_t - self.ctmc.alpha).dot(self.Q_inv_cabs))

    def cost_rate(self, t: float) -> float:
        """BZM_II(t) = E[C_II(t)] / (E[S(t)] + d_pm * R(t) + d_cm * (1 - R(t)))."""
        if t <= 1e-6:
            return float('inf')
        P_t = self.ctmc.state_probabilities(t)
        r = float(P_t.dot(self.ctmc.e))
        es = float((P_t - self.ctmc.alpha).dot(self.ctmc.Q_inv_e))
        denom = es + self.d_pm * r + self.d_cm * (1.0 - r)
        if denom <= 1e-12:
            return float('inf')
        ec = float(P_t.dot(self.c_pm) + (P_t - self.ctmc.alpha).dot(self.Q_inv_cabs))
        return ec / denom

    def cost_rate_from_probs(self, P_mat: np.ndarray) -> np.ndarray:
        """Vectorized cost rate evaluation from precomputed state-probability rows P(t_k)."""
        r = P_mat.dot(self.ctmc.e)
        diff = P_mat - self.ctmc.alpha
        es = diff.dot(self.ctmc.Q_inv_e)
        denom = es + self.d_pm * r + self.d_cm * (1.0 - r)
        ec = P_mat.dot(self.c_pm) + diff.dot(self.Q_inv_cabs)
        with np.errstate(divide='ignore', invalid='ignore'):
            out = np.where(denom > 1e-12, ec / denom, np.inf)
        return out

    def asymptotic_cost_rate(self) -> float:
        """Purely corrective (t -> inf) cost rate: (-alpha * Q_W^{-1} * c_abs) / (MTTF + d_cm)."""
        return float(-self.ctmc.alpha.dot(self.Q_inv_cabs)) / (self.ctmc.mttf + self.d_cm)
