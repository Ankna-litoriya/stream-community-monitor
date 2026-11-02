"""
Full Batch Baseline: Modularity-Specialized Global LPA.
Recomputes community labels across the entire accumulated graph G_t = (V_t, E_t)
from scratch without retaining incremental state.

Score_u(c) = k_{u, c} - gamma * [k_u * vol(c)] / (2m)
"""

from typing import Dict, Set, List, Optional
import time
import random
from collections import defaultdict
from .base import BaseCommunityDetector
from ..models.dynamic_graph import DynamicGraph


class FullBatchLPA(BaseCommunityDetector):
    """
    Full Batch Modularity-Specialized Label Propagation Algorithm.
    Evaluates every node in the entire graph repeatedly until convergence.
    """

    def __init__(
        self,
        max_global_iterations: int = 15,
        temporal_decay_lambda: float = 0.005,
        modularity_gamma: float = 0.8,
        tie_break_seed: int = 42
    ):
        self.max_global_iterations = max_global_iterations
        self.temporal_decay_lambda = temporal_decay_lambda
        self.modularity_gamma = modularity_gamma
        self.rng = random.Random(tie_break_seed)

        self.node_to_community: Dict[str, str] = {}
        self.last_execution_time_ms: float = 0.0
        self.last_nodes_evaluated: int = 0
        self.last_label_flips: int = 0

    def fit_batch(self, graph: DynamicGraph, frontier_nodes: Set[str], batch_id: int) -> Dict[str, str]:
        """
        Runs global LPA across ALL nodes in graph.adj from scratch.
        """
        start_time = time.perf_counter()
        m2 = max(2.0 * graph.total_weight, 1.0)

        all_nodes = list(graph.adj.keys())
        # Pure batch initialization: reset each node to distinct label
        self.node_to_community = {u: f"c_{u}" for u in all_nodes}
        community_volumes: Dict[str, float] = {f"c_{u}": graph.degrees.get(u, 1.0) for u in all_nodes}

        nodes_evaluated = 0
        label_flips = 0
        current_time = time.time()

        for iteration in range(self.max_global_iterations):
            self.rng.shuffle(all_nodes)
            flips_this_round = 0

            for u in all_nodes:
                nodes_evaluated += 1
                neighbors = graph.neighbors(u)
                if not neighbors:
                    continue

                k_u = graph.degrees.get(u, 1.0)
                current_c = self.node_to_community[u]

                community_weights: Dict[str, float] = defaultdict(float)
                for v, w in neighbors.items():
                    c_v = self.node_to_community[v]
                    eff_w = graph.get_effective_weight(u, v, current_time)
                    community_weights[c_v] += eff_w

                if not community_weights:
                    continue

                best_score = -float('inf')
                best_labels: List[str] = []

                for c_label, k_uc in community_weights.items():
                    vol_c = community_volumes[c_label]
                    effective_vol = (vol_c - k_u) if c_label == current_c else vol_c
                    penalty = self.modularity_gamma * (k_u * effective_vol) / m2
                    score = k_uc - penalty

                    if score > best_score + 1e-9:
                        best_score = score
                        best_labels = [c_label]
                    elif abs(score - best_score) <= 1e-9:
                        best_labels.append(c_label)

                if current_c in best_labels:
                    selected_c = current_c
                else:
                    best_labels.sort()
                    selected_c = best_labels[0]

                if selected_c != current_c:
                    community_volumes[current_c] = max(0.0, community_volumes[current_c] - k_u)
                    community_volumes[selected_c] += k_u
                    self.node_to_community[u] = selected_c
                    flips_this_round += 1
                    label_flips += 1

            if flips_this_round == 0:
                break

        end_time = time.perf_counter()
        self.last_execution_time_ms = (end_time - start_time) * 1000.0
        self.last_nodes_evaluated = nodes_evaluated
        self.last_label_flips = label_flips

        return self.node_to_community

    def get_partition(self) -> Dict[str, str]:
        return self.node_to_community
