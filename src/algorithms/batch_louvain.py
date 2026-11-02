"""
Full Batch Baseline: Global Louvain Algorithm.
Recomputes communities from scratch across the entire graph G_t = (V_t, E_t).

Evaluates all nodes in V_t iteratively for modularity maximization:
Delta Q = [k_{u, in}^{(C)} - k_{u, in}^{(curr)}] / (2m) + [k_u * (tot_curr - tot_C)] / (2m^2)
"""

from typing import Dict, Set, List
import time
import random
from collections import defaultdict
from .base import BaseCommunityDetector
from ..models.dynamic_graph import DynamicGraph


class FullBatchLouvain(BaseCommunityDetector):
    """
    Standard Full Batch Louvain Algorithm (Blondel et al.).
    Evaluates every node in the entire graph repeatedly until modularity convergence.
    """

    def __init__(self, max_passes: int = 15, tie_break_seed: int = 42):
        self.max_passes = max_passes
        self.rng = random.Random(tie_break_seed)

        self.node_to_community: Dict[str, str] = {}
        self.last_execution_time_ms: float = 0.0
        self.last_nodes_evaluated: int = 0
        self.last_label_flips: int = 0

    def fit_batch(self, graph: DynamicGraph, frontier_nodes: Set[str], batch_id: int) -> Dict[str, str]:
        start_time = time.perf_counter()
        m2 = max(2.0 * graph.total_weight, 1.0)

        all_nodes = list(graph.adj.keys())
        # Reset: each node in its own community
        self.node_to_community = {u: f"c_{u}" for u in all_nodes}
        community_degrees: Dict[str, float] = {f"c_{u}": graph.degrees[u] for u in all_nodes}

        nodes_evaluated = 0
        moves = 0

        for _ in range(self.max_passes):
            self.rng.shuffle(all_nodes)
            moves_this_round = 0

            for u in all_nodes:
                nodes_evaluated += 1
                current_c = self.node_to_community[u]
                k_u = graph.degrees[u]
                neighbors = graph.neighbors(u)
                if not neighbors:
                    continue

                weights_to_c: Dict[str, float] = defaultdict(float)
                for v, w in neighbors.items():
                    c_v = self.node_to_community[v]
                    weights_to_c[c_v] += w

                best_gain = 0.0
                best_c = current_c

                k_u_in_curr = weights_to_c.get(current_c, 0.0)
                tot_curr = community_degrees[current_c] - k_u

                for target_c, k_u_in_target in weights_to_c.items():
                    if target_c == current_c:
                        continue

                    tot_target = community_degrees[target_c]
                    delta_q = (k_u_in_target - k_u_in_curr) / m2 + (k_u * (tot_curr - tot_target)) / (m2 * m2)

                    if delta_q > best_gain:
                        best_gain = delta_q
                        best_c = target_c

                if best_c != current_c and best_gain > 1e-6:
                    self.node_to_community[u] = best_c
                    community_degrees[current_c] -= k_u
                    community_degrees[best_c] += k_u
                    moves += 1
                    moves_this_round += 1

            if moves_this_round == 0:
                break

        end_time = time.perf_counter()
        self.last_execution_time_ms = (end_time - start_time) * 1000.0
        self.last_nodes_evaluated = nodes_evaluated
        self.last_label_flips = moves

        return self.node_to_community

    def get_partition(self) -> Dict[str, str]:
        return self.node_to_community
