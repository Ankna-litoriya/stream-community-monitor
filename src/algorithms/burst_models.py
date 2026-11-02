"""
Advanced Streaming Burst & Viral Surge Detection Models.
Publication & Journal Standard: IEEE TKDE / ACM SIGKDD / NeurIPS Graph Learning.

Implements:
1. Hawkes Self-Exciting Temporal Point Process:
   Models viral cascade dynamics where each interaction excites future interactions:
   lambda_C(t) = mu_C + sum_{t_i < t} alpha * exp(-beta * (t - t_i))
   Branching ratio: eta = alpha / beta (eta >= 1.0 denotes supercritical viral explosion).

2. Kleinberg 2-State / Multi-State Burst Automaton:
   Hidden Markov Model with state space {s_0 (baseline), s_1 (burst)}
   Decodes state sequence via Viterbi dynamic programming over inter-arrival times.
"""

from typing import List, Dict, Tuple, Optional
import math
import time
from collections import deque


class HawkesProcessModel:
    """
    Self-Exciting Hawkes Process for modeling social interaction cascades.
    Quantifies exogenous (baseline organic) vs. endogenous (viral self-excitation) dynamics.
    """

    def __init__(self, mu: float = 1.0, alpha: float = 0.6, beta: float = 0.8, memory_window: int = 100):
        self.mu = mu          # Baseline spontaneous interaction intensity
        self.alpha = alpha    # Excitation jump size per interaction
        self.beta = beta      # Exponential decay rate of excitation
        self.memory_window = memory_window
        # Timestamp history of recent interactions for this community
        self.timestamps: deque = deque(maxlen=memory_window)

    @property
    def branching_ratio(self) -> float:
        """
        The criticality metric eta = alpha / beta.
        If eta < 1.0: Subcritical (stable, decays to baseline).
        If eta >= 1.0: Supercritical (explosive viral burst).
        """
        return self.alpha / max(self.beta, 1e-6)

    def record_events(self, count: int, current_time: Optional[float] = None) -> None:
        """Records multiple interaction events arriving at current time."""
        t = current_time or time.time()
        for _ in range(count):
            self.timestamps.append(t)

    def compute_intensity(self, current_time: Optional[float] = None) -> float:
        """
        Computes current Hawkes conditional intensity lambda(t):
        lambda(t) = mu + sum_{t_i < t} alpha * exp(-beta * (t - t_i))
        """
        t = current_time or time.time()
        intensity = self.mu

        for t_i in self.timestamps:
            delta_t = t - t_i
            if delta_t >= 0:
                intensity += self.alpha * math.exp(-self.beta * delta_t)

        return intensity

    def get_surge_diagnostics(self, current_time: Optional[float] = None) -> Dict[str, float]:
        """Returns comprehensive point-process diagnostic metrics."""
        intensity = self.compute_intensity(current_time)
        return {
            "conditional_intensity": round(intensity, 3),
            "branching_ratio": round(self.branching_ratio, 3),
            "endogenous_fraction": round(min(1.0, (intensity - self.mu) / max(intensity, 1e-6)), 3),
            "is_supercritical": bool(self.branching_ratio >= 1.0 or intensity > 5.0 * self.mu)
        }


class KleinbergBurstAutomaton:
    """
    Kleinberg Multi-State Burst Detection Automaton.
    Models interaction bursts as transitions between discrete activity states
    in an infinite-state or 2-state Hidden Markov Model.
    """

    def __init__(self, s: float = 2.0, gamma: float = 1.0):
        """
        s: State scaling multiplier (lambda_1 = s * lambda_0)
        gamma: State transition cost penalty
        """
        self.s = s
        self.gamma = gamma
        self.inter_arrival_times: deque = deque(maxlen=60)

    def add_observation(self, interval: float) -> None:
        if interval > 0:
            self.inter_arrival_times.append(interval)

    def detect_burst_state(self) -> Tuple[int, float]:
        """
        Performs Viterbi state estimation over observed inter-arrival times.
        Returns: (state [0=baseline, 1=burst], burst_weight).
        """
        if len(self.inter_arrival_times) < 3:
            return 0, 0.0

        # Mean inter-arrival time
        intervals = list(self.inter_arrival_times)
        n = len(intervals)
        t_total = sum(intervals)
        lambda_0 = n / max(t_total, 1e-6)  # Baseline rate
        lambda_1 = lambda_0 * self.s       # Burst rate

        # Cost matrix for 2-state HMM
        # C_j(x) = -ln(lambda_j * exp(-lambda_j * x)) = -ln(lambda_j) + lambda_j * x
        def cost(state, x):
            rate = lambda_1 if state == 1 else lambda_0
            return -math.log(rate) + rate * x

        # Viterbi DP
        # dp[t][state] = min cost to reach state at time t
        dp_0 = cost(0, intervals[0])
        dp_1 = cost(1, intervals[0])

        for x in intervals[1:]:
            # Transition costs: tau(0 -> 1) = gamma * ln(s), tau(1 -> 0) = 0
            trans_cost_0_to_1 = self.gamma * math.log(self.s)

            new_dp_0 = cost(0, x) + min(dp_0, dp_1)
            new_dp_1 = cost(1, x) + min(dp_0 + trans_cost_0_to_1, dp_1)

            dp_0, dp_1 = new_dp_0, new_dp_1

        # Current estimated state
        current_state = 1 if dp_1 < dp_0 else 0
        burst_weight = max(0.0, dp_0 - dp_1) if current_state == 1 else 0.0

        return current_state, burst_weight
