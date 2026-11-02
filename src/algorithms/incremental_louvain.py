"""
Boundary-Restricted Incremental Louvain Algorithm.
Dynamic Modularity Maximization for Streaming Graphs.

Journal Reference: Blondel et al. (Louvain) adapted for Dynamic/Streaming Networks.
Only assesses community migration for nodes affected by the incoming micro-batch (Delta E_t).
"""

from typing import Dict, Set, List, Optional
import time
from collections import defaultdict
from .base import BaseCommunityDetector
from ..models.dynamic_graph import DynamicGraph


class IncrementalLouvain(BaseCommunityDetector):
    """
    Incremental Louvain Community Detector.
    Evaluates modularity gain Delta Q strictly over the affected frontier.
    """

    def __init__(self, max_local_passes: int = 5):
        self.max_local_passes = max_local_passes
        self.node_to_community: Dict[str, str] = {}
        self.community_degrees: Dict[str, float] = defaultdict(float)

        self.last_execution_time_ms: float = 0.0
        self.last_nodes_evaluated: int = 0
        self.last_label_flips: int = 0

    def fit_batch(self, graph: DynamicGraph, frontier_nodes: Set[str], batch_id: int) -> Dict[str, str]:
        """
        Incrementally updates community assignments based on modularity gain Delta Q.
        """
        start_time = time.perf_counter()
        m2 = 2.0 * max(graph.total_weight, 1.0)

        # 1. Initialize new frontier nodes
        for u in frontier_nodes:
            if u not in self.node_to_community:
                c_u = f"c_{u}"
                self.node_to_community[u] = c_u
                self.community_degrees[c_u] += graph.degrees[u]

        # 2. Evaluate delta Q for affected frontier nodes
        nodes_evaluated = 0
        moves = 0
        active_set = set(frontier_nodes)

        for _ in range(self.max_local_passes):
            moves_this_pass = 0
            next_active: Set[str] = set()

            for u in active_set:
                nodes_evaluated += 1
                current_c = self.node_to_community[u]
                k_u = graph.degrees[u]
                neighbors = graph.neighbors(u)

                # Tally weights to each neighbor community
                weights_to_c: Dict[str, float] = defaultdict(float)
                for v, w in neighbors.items():
                    c_v = self.node_to_community.get(v, f"c_{v}")
                    weights_to_c[c_v] += w

                # Best modularity gain
                best_gain = 0.0
                best_c = current_c

                # Weight to current community
                k_u_in_curr = weights_to_c.get(current_c, 0.0)
                tot_curr = self.community_degrees[current_c] - k_u

                for target_c, k_u_in_target in weights_to_c.items():
                    if target_c == current_c:
                        continue

                    tot_target = self.community_degrees[target_c]
                    # Delta Q of moving u from current_c to target_c
                    # Delta Q = [k_u_in_target - k_u_in_curr]/m2 + [k_u * (tot_curr - tot_target)] / (m2^2 / 2)
                    delta_q = (k_u_in_target - k_u_in_curr) / m2 + (k_u * (tot_curr - tot_target)) / (m2 * m2)

                    if delta_q > best_gain:
                        best_gain = delta_q
                        best_c = target_c

                # If positive gain found, migrate node
                if best_c != current_c and best_gain > 1e-6:
                    self.node_to_community[u] = best_c
                    self.community_degrees[current_c] -= k_u
                    self.community_degrees[best_c] += k_u
                    moves += 1
                    moves_this_pass += 1

                    # Re-enqueue neighbors
                    for v in neighbors:
                        next_active.add(v)

            active_set = next_active
            if moves_this_pass == 0 or not active_set:
                break

        end_time = time.perf_counter()
        self.last_execution_time_ms = (end_time - start_time) * 1000.0
        self.last_nodes_evaluated = nodes_evaluated
        self.last_label_flips = moves

        return self.node_to_community

    def get_partition(self) -> Dict[str, str]:
        return self.node_to_community
