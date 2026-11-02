"""
Incremental Label Propagation Algorithm (i-LPA) with Modularity-Specialized Regularization.
Journal Standard: IEEE TKDE / ACM SIGKDD.

Theoretical Principle:
Given a streaming graph G_t and incoming micro-batch Delta E_t (e.g. 1,000 edges),
only nodes in the Active Perturbation Frontier Delta V_t and their k-hop boundary
neighborhood N^k(Delta V_t) can experience a shift in their neighborhood label distribution.
Nodes outside this frontier remain topologically stationary.

Prevents the classic "monster community" collapse via Newman-Girvan modularity gradient:
Score_u(c) = k_{u, c} - gamma * [k_u * vol(c)] / (2m)
where:
  k_{u, c} = sum_{v in N(u), C(v)=c} w_eff(u, v)
  vol(c)   = sum of degrees of vertices in community c
  2m       = total graph volume

Time Complexity:
O(|Delta E_t| * d_bar^k * I_local) << O(|V_t| + |E_t|)
"""

from typing import Dict, Set, List, Tuple, Optional
import time
import random
from collections import deque, defaultdict
from .base import BaseCommunityDetector
from ..models.dynamic_graph import DynamicGraph


class IncrementalLPA(BaseCommunityDetector):
    """
    Incremental Modularity-Guided Label Propagation with Dynamic Boundary Queue.
    """

    def __init__(
        self,
        max_hops: int = 2,
        max_local_iterations: int = 15,
        temporal_decay_lambda: float = 0.005,
        modularity_gamma: float = 0.8,
        tie_break_seed: int = 42
    ):
        self.max_hops = max_hops
        self.max_local_iterations = max_local_iterations
        self.temporal_decay_lambda = temporal_decay_lambda
        self.modularity_gamma = modularity_gamma
        self.rng = random.Random(tie_break_seed)

        # Persistent state: node_id -> community_id
        self.node_to_community: Dict[str, str] = {}
        # Track community degrees (volumes): community_id -> vol(c)
        self.community_volumes: Dict[str, float] = defaultdict(float)

        # Diagnostic telemetry
        self.last_execution_time_ms: float = 0.0
        self.last_nodes_evaluated: int = 0
        self.last_label_flips: int = 0

    def fit_batch(self, graph: DynamicGraph, frontier_nodes: Set[str], batch_id: int) -> Dict[str, str]:
        """
        Incrementally updates community labels for nodes affected by the incoming micro-batch.
        Only traverses the affected neighborhood rather than the global graph.
        """
        start_time = time.perf_counter()
        m2 = max(2.0 * graph.total_weight, 1.0)

        # Step 1: Initialize newly observed nodes that have no prior label
        for u in frontier_nodes:
            if u not in self.node_to_community:
                c_u = f"c_{u}"
                self.node_to_community[u] = c_u
                self.community_volumes[c_u] += graph.degrees.get(u, 1.0)

        # Step 2: Form the initial active candidate set via k-hop boundary expansion
        active_candidates = graph.get_k_hop_neighborhood(frontier_nodes, k=self.max_hops)
        candidate_queue = deque(list(active_candidates))
        in_queue: Set[str] = set(candidate_queue)

        nodes_evaluated = 0
        label_flips = 0
        iteration = 0
        current_time = time.time()

        # Step 3: Asynchronous Boundary-Restricted Propagation
        while candidate_queue and iteration < self.max_local_iterations:
            iteration += 1
            num_nodes_this_round = len(candidate_queue)

            for _ in range(num_nodes_this_round):
                u = candidate_queue.popleft()
                in_queue.discard(u)
                nodes_evaluated += 1

                neighbors = graph.neighbors(u)
                if not neighbors:
                    continue

                k_u = graph.degrees.get(u, 1.0)
                current_c = self.node_to_community.get(u)

                # Accumulate label weights: k_{u, c} = sum_{v in N(u), C(v)=c} w_eff(u, v)
                community_weights: Dict[str, float] = defaultdict(float)
                for v, w in neighbors.items():
                    c_v = self.node_to_community.get(v)
                    if c_v is None:
                        c_v = f"c_{v}"
                        self.node_to_community[v] = c_v
                        self.community_volumes[c_v] += graph.degrees.get(v, 1.0)

                    eff_w = graph.get_effective_weight(u, v, current_time)
                    community_weights[c_v] += eff_w

                if not community_weights:
                    continue

                # Compute Modularity-Regularized Score for each candidate community
                # Score_u(c) = k_{u, c} - gamma * [k_u * vol(c)] / (2m)
                best_score = -float('inf')
                best_labels: List[str] = []

                for c_label, k_uc in community_weights.items():
                    vol_c = self.community_volumes[c_label]
                    # If u is already in c_label, discount u's own degree from vol_c
                    effective_vol = (vol_c - k_u) if c_label == current_c else vol_c
                    penalty = self.modularity_gamma * (k_u * effective_vol) / m2
                    score = k_uc - penalty

                    if score > best_score + 1e-9:
                        best_score = score
                        best_labels = [c_label]
                    elif abs(score - best_score) <= 1e-9:
                        best_labels.append(c_label)

                # Selection with hysteresis
                if current_c in best_labels:
                    selected_c = current_c
                else:
                    best_labels.sort()
                    selected_c = best_labels[0]

                # If label flipped, adjust volume and push neighbor frontier
                if selected_c != current_c:
                    # Update community volumes
                    self.community_volumes[current_c] = max(0.0, self.community_volumes[current_c] - k_u)
                    self.community_volumes[selected_c] += k_u
                    self.node_to_community[u] = selected_c
                    label_flips += 1

                    # Re-enqueue neighbors if not already in queue
                    for v in neighbors:
                        if v not in in_queue:
                            candidate_queue.append(v)
                            in_queue.add(v)

        end_time = time.perf_counter()
        self.last_execution_time_ms = (end_time - start_time) * 1000.0
        self.last_nodes_evaluated = nodes_evaluated
        self.last_label_flips = label_flips

        return self.node_to_community

    def get_partition(self) -> Dict[str, str]:
        return self.node_to_community
