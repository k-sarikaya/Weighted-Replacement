"""
Continuous-Time Markov Chain (CTMC) Phase-Type Lifetime Model for Heterogeneous
Weighted k-out-of-n:G Systems under Capacity-Proportional Asymmetric Load-Sharing.
"""

import numpy as np
from scipy.linalg import expm, inv


class WeightedSystemCTMC:
    """
    Represents an acyclic bivariate CTMC over the operational state space W = {(i, j): i*w1 + j*w2 >= k}.
    """
    def __init__(self, n: int, m: int, k: int, w1: int, w2: int,
                 lambda1_0: float, lambda2_0: float,
                 gamma1: float = 0.0, gamma2: float = 0.0):
        self.n = n
        self.m = m
        self.k = k
        self.w1 = w1
        self.w2 = w2
        self.lambda1_0 = lambda1_0
        self.lambda2_0 = lambda2_0
        self.gamma1 = gamma1
        self.gamma2 = gamma2
        
        self.W0 = m * w1 + (n - m) * w2
        if self.W0 < k:
            raise ValueError(f"Initial capacity W0={self.W0} is strictly less than threshold k={k}.")
            
        self._build_state_space()
        self._build_generator_matrix()
        
    def _build_state_space(self):
        """Constructs ordered operational state space W."""
        self.states = []
        for i in range(self.m, -1, -1):
            for j in range(self.n - self.m, -1, -1):
                if i * self.w1 + j * self.w2 >= self.k:
                    self.states.append((i, j))
                    
        self.state_to_idx = {state: idx for idx, state in enumerate(self.states)}
        self.M = len(self.states)
        self.alpha = np.zeros(self.M)
        self.alpha[0] = 1.0  # Initial state is (m, n - m)
        self.e = np.ones(self.M)
        
    def _build_generator_matrix(self):
        """Builds upper-triangular generator submatrix Q_W and absorption vector q_F."""
        self.Q_W = np.zeros((self.M, self.M), dtype=float)
        self.q_F = np.zeros(self.M, dtype=float)
        
        # Track transitions specifically for component renewal (Policy II)
        self.fatal_rate1 = np.zeros(self.M, dtype=float)
        self.fatal_rate2 = np.zeros(self.M, dtype=float)
        
        for idx, (i, j) in enumerate(self.states):
            Wij = i * self.w1 + j * self.w2
            ratio = self.W0 / Wij

            # Tampered Failure Rate (TFR) power-law relation (overflow-guarded)
            log_ratio = np.log(ratio) if ratio > 1.0 else 0.0
            scale1 = np.exp(min(self.gamma1 * log_ratio, 650.0)) if log_ratio > 0.0 else 1.0
            scale2 = np.exp(min(self.gamma2 * log_ratio, 650.0)) if log_ratio > 0.0 else 1.0
            lam1 = self.lambda1_0 * scale1
            lam2 = self.lambda2_0 * scale2

            rate1 = i * lam1
            rate2 = j * lam2

            # Transition upon Type I failure: (i - 1, j)
            if i > 0:
                next_state1 = (i - 1, j)
                if next_state1 in self.state_to_idx:
                    self.Q_W[idx, self.state_to_idx[next_state1]] += rate1
                else:
                    self.q_F[idx] += rate1
                    self.fatal_rate1[idx] += rate1

            # Transition upon Type II failure: (i, j - 1)
            if j > 0:
                next_state2 = (i, j - 1)
                if next_state2 in self.state_to_idx:
                    self.Q_W[idx, self.state_to_idx[next_state2]] += rate2
                else:
                    self.q_F[idx] += rate2
                    self.fatal_rate2[idx] += rate2

            self.Q_W[idx, idx] = -(rate1 + rate2)

        self.Q_inv = inv(self.Q_W)
        self.Q_inv_e = self.Q_inv.dot(self.e)
        self.mttf = -float(self.alpha.dot(self.Q_inv_e))
        
    def reliability(self, t: float) -> float:
        """Exact Phase-Type system reliability: R_sys(t) = alpha * exp(Q_W * t) * e."""
        if t <= 0.0:
            return 1.0
        exp_Qt = expm(self.Q_W * t)
        return float(self.alpha.dot(exp_Qt).dot(self.e))
        
    def failure_density(self, t: float) -> float:
        """Exact failure density: f_sys(t) = alpha * exp(Q_W * t) * q_F."""
        if t <= 0.0:
            return 0.0
        exp_Qt = expm(self.Q_W * t)
        return float(self.alpha.dot(exp_Qt).dot(self.q_F))
        
    def hazard_rate(self, t: float) -> float:
        """System hazard rate: h_sys(t) = f_sys(t) / R_sys(t)."""
        r = self.reliability(t)
        if r <= 1e-15:
            return float('inf')
        return self.failure_density(t) / r
        
    def expected_cycle_duration(self, t: float) -> float:
        """
        Exact expected renewal cycle duration: E[min(T_sys, t)] = integral_0^t R_sys(u) du
        = alpha * Q_W^{-1} * (exp(Q_W * t) - I_M) * e
        """
        if t <= 0.0:
            return 0.0
        exp_Qt = expm(self.Q_W * t)
        v_int = self.alpha.dot(self.Q_inv).dot(exp_Qt - np.eye(self.M))
        return float(v_int.dot(self.e))
        
    def state_probabilities(self, t: float) -> np.ndarray:
        """Vector of transient state probabilities at time t: P(t) = alpha * exp(Q_W * t)."""
        if t <= 0.0:
            return self.alpha.copy()
        return self.alpha.dot(expm(self.Q_W * t))
        
    def state_probability_integrals(self, t: float) -> np.ndarray:
        """Vector of integrated transient probabilities: integral_0^t P(u) du."""
        if t <= 0.0:
            return np.zeros(self.M)
        exp_Qt = expm(self.Q_W * t)
        return self.alpha.dot(self.Q_inv).dot(exp_Qt - np.eye(self.M))

    def state_probs_on_uniform_grid(self, t_start: float, dt: float, count: int) -> np.ndarray:
        """
        Evaluates transient state probability vectors P(t_k) = alpha * exp(Q_W * t_k)
        on a uniform grid t_k = t_start + k * dt (k = 0, ..., count - 1) using
        iterative matrix-exponential stepping P(t_{k+1}) = P(t_k) * exp(Q_W * dt).
        Requires only two expm() calls per uniform segment instead of `count` calls.
        """
        P_mat = np.empty((count, self.M), dtype=float)
        if count <= 0:
            return P_mat
        p_curr = self.alpha.copy() if t_start <= 0.0 else self.alpha.dot(expm(self.Q_W * t_start))
        P_mat[0] = p_curr
        if count > 1:
            E_step = expm(self.Q_W * dt)
            for k in range(1, count):
                p_curr = p_curr.dot(E_step)
                P_mat[k] = p_curr
        return P_mat

