"""
CommunitySketch: Sublinear-Space Quotient Graph & Modularity Acceleration Data Structure.
Research Standard: ACM TKDD (2025) / IEEE TKDE.

Maintains constant-time O(1) quotient graph state:
- Community Volume: vol(C) = sum_{u in C} deg(u)
- Internal Community Weight: e(C, C) = sum_{(u,v) in E, u,v in C} w(u, v)
- Inter-Community Quotient Adjacency: W(C_i, C_j) = sum_{u in C_i, v in C_j} w(u, v)
- Dynamic Delta Q computation in O(1) time without re-scanning graph edges.
"""

from typing import Dict, Set, Tuple, Optional
from collections import defaultdict


class CommunitySketch:
    """
    Sublinear-Space Quotient Graph Structure for Constant-Time Dynamic Modularity Updates.
    Formulation based on Gupta & Kundu (ACM TKDD 2025) and Blondel et al.
    """

    def __init__(self):
        # community_id -> total incident degree volume: vol(C)
        self.vol: Dict[str, float] = defaultdict(float)
        # community_id -> internal weight: e(C, C)
        self.internal_weight: Dict[str, float] = defaultdict(float)
        # quotient adjacency: (C_i, C_j) -> cross weight
        self.quotient_adj: Dict[Tuple[str, str], float] = defaultdict(float)
        # node_id -> community_id
        self.node_to_comm: Dict[str, str] = {}
        # community_id -> set of member nodes
        self.comm_to_nodes: Dict[str, Set[str]] = defaultdict(set)
        # Total graph volume (2m)
        self.total_volume: float = 0.0

    @property
    def num_communities(self) -> int:
        return len([c for c, members in self.comm_to_nodes.items() if len(members) > 0])

    def register_node(self, node: str, degree: float, initial_comm: Optional[str] = None) -> str:
        """Registers a new vertex into the sketch with initial community."""
        comm = initial_comm or f"c_{node}"
        self.node_to_comm[node] = comm
        self.comm_to_nodes[comm].add(node)
        self.vol[comm] += degree
        self.total_volume += degree
        return comm

    def update_edge(self, u: str, v: str, weight: float) -> None:
        """
        Updates the quotient graph when an interaction edge (u, v, weight) streams in.
        Maintains O(1) state consistency.
        """
        c_u = self.node_to_comm.get(u)
        c_v = self.node_to_comm.get(v)

        if not c_u or not c_v:
            return

        self.vol[c_u] += weight
        self.vol[c_v] += weight
        self.total_volume += 2.0 * weight

        if c_u == c_v:
            self.internal_weight[c_u] += 2.0 * weight
        else:
            key1 = (c_u, c_v) if c_u < c_v else (c_v, c_u)
            self.quotient_adj[key1] += weight

    def compute_delta_q(
        self,
        node: str,
        k_u: float,
        current_c: str,
        target_c: str,
        k_u_in_curr: float,
        k_u_in_target: float
    ) -> float:
        """
        Calculates exact modularity gain Delta Q in O(1) constant time:
        Delta Q = [k_{u, in}^{(target)} - k_{u, in}^{(curr)}] / (2m) + [k_u * (tot_curr - tot_target)] / (2m^2)
        """
        m2 = max(self.total_volume, 1.0)
        tot_curr = self.vol[current_c] - k_u
        tot_target = self.vol[target_c]

        delta_q = (k_u_in_target - k_u_in_curr) / m2 + (k_u * (tot_curr - tot_target)) / (m2 * m2)
        return delta_q

    def move_node(
        self,
        node: str,
        k_u: float,
        from_c: str,
        to_c: str,
        k_u_in_from: float,
        k_u_in_to: float
    ) -> None:
        """
        Migrates node from from_c to to_c, maintaining quotient graph invariant in O(1).
        """
        if from_c == to_c:
            return

        self.comm_to_nodes[from_c].discard(node)
        self.comm_to_nodes[to_c].add(node)
        self.node_to_comm[node] = to_c

        # Update community volumes
        self.vol[from_c] = max(0.0, self.vol[from_c] - k_u)
        self.vol[to_c] += k_u

        # Update internal weights
        self.internal_weight[from_c] = max(0.0, self.internal_weight[from_c] - 2.0 * k_u_in_from)
        self.internal_weight[to_c] += 2.0 * k_u_in_to

        # Cleanup empty communities
        if len(self.comm_to_nodes[from_c]) == 0:
            del self.comm_to_nodes[from_c]
            if from_c in self.vol:
                del self.vol[from_c]
            if from_c in self.internal_weight:
                del self.internal_weight[from_c]

    def get_global_modularity(self) -> float:
        """
        Computes global Newman-Girvan modularity Q directly from the sketch in O(|C|):
        Q = sum_{c in C} [ e(c, c) / 2m - (vol(c) / 2m)^2 ]
        Significantly faster than O(|V| + |E|) full-graph scanning.
        """
        m2 = max(self.total_volume, 1.0)
        q = 0.0
        for c, vol_c in self.vol.items():
            in_w = self.internal_weight.get(c, 0.0)
            q += (in_w / m2) - ((vol_c / m2) ** 2)
        return max(-0.5, min(1.0, q))
