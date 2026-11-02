"""
Temporal Dynamic Graph Engine.
Optimized for high-throughput streaming interaction graphs (e.g. Twitter/X, Reddit).
Supports dynamic edge ingestion, degree tracking, and k-hop frontier extraction.
"""

from dataclasses import dataclass, field
from typing import Dict, Set, Tuple, List, Optional
import math
import time


@dataclass
class EdgeRecord:
    src: str
    dst: str
    weight: float = 1.0
    timestamp: float = field(default_factory=time.time)
    topic: Optional[str] = None
    interaction_type: str = "retweet"  # e.g., retweet, reply, mention, citation


class DynamicGraph:
    """
    In-memory high-performance temporal graph representation.
    Tracks adjacency, weighted degrees, total edge weight (volume),
    and boundary frontiers for incremental algorithm execution.
    """

    def __init__(self, temporal_decay_lambda: float = 0.0):
        # adj[u][v] = weight
        self.adj: Dict[str, Dict[str, float]] = {}
        # edge_timestamps[(u, v)] = last_timestamp
        self.edge_timestamps: Dict[Tuple[str, str], float] = {}
        # cached degree: sum of outgoing/undirected weights
        self.degrees: Dict[str, float] = {}
        # total weight of all edges (m = total edge weight)
        self.total_weight: float = 0.0
        self.temporal_decay_lambda = temporal_decay_lambda
        # Metadata / attributes
        self.node_metadata: Dict[str, Dict] = {}

    @property
    def num_nodes(self) -> int:
        return len(self.adj)

    @property
    def num_edges(self) -> int:
        # Undirected edge count
        return sum(len(nbrs) for nbrs in self.adj.values()) // 2

    def add_node(self, node: str, metadata: Optional[Dict] = None) -> None:
        if node not in self.adj:
            self.adj[node] = {}
            self.degrees[node] = 0.0
            self.node_metadata[node] = metadata or {}

    def add_or_update_edge(self, src: str, dst: str, weight: float = 1.0, timestamp: Optional[float] = None) -> None:
        """
        Adds or updates an undirected edge between src and dst.
        """
        if src == dst:
            return  # Ignore self-loops for community detection stability

        timestamp = timestamp or time.time()
        self.add_node(src)
        self.add_node(dst)

        # Check existing weight
        existing_weight = self.adj[src].get(dst, 0.0)
        new_weight = existing_weight + weight

        # Update adjacency
        self.adj[src][dst] = new_weight
        self.adj[dst][src] = new_weight

        # Update edge timestamp
        edge_key1 = (src, dst)
        edge_key2 = (dst, src)
        self.edge_timestamps[edge_key1] = timestamp
        self.edge_timestamps[edge_key2] = timestamp

        # Update degrees
        self.degrees[src] += weight
        self.degrees[dst] += weight

        # Update total weight (undirected m sum of w_e)
        self.total_weight += weight

    def apply_batch(self, batch_edges: List[EdgeRecord]) -> Set[str]:
        """
        Applies a streaming micro-batch of edges (e.g. 1,000 incoming interactions).
        Returns the Active Perturbation Frontier: the set of nodes directly
        affected by the arriving batch: Delta V = U_{(u,v) in Delta E} {u, v}.
        """
        frontier_nodes: Set[str] = set()

        for edge in batch_edges:
            self.add_or_update_edge(edge.src, edge.dst, edge.weight, edge.timestamp)
            frontier_nodes.add(edge.src)
            frontier_nodes.add(edge.dst)

        return frontier_nodes

    def get_k_hop_neighborhood(self, frontier: Set[str], k: int = 1) -> Set[str]:
        """
        Computes the k-hop boundary expansion around the perturbation frontier.
        V_aff = Union_{u in frontier} N^k(u).
        Nodes outside this boundary have invariant 1-hop neighbor community distributions.
        """
        visited: Set[str] = set(frontier)
        current_layer: Set[str] = set(frontier)

        for _ in range(k):
            next_layer: Set[str] = set()
            for node in current_layer:
                if node in self.adj:
                    for neighbor in self.adj[node]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            next_layer.add(neighbor)
            current_layer = next_layer
            if not current_layer:
                break

        return visited

    def neighbors(self, node: str) -> Dict[str, float]:
        """Returns dict of {neighbor: weight}."""
        return self.adj.get(node, {})

    def get_effective_weight(self, u: str, v: str, current_time: Optional[float] = None) -> float:
        """
        Calculates time-decayed edge weight if temporal decay is enabled:
        w_eff = w * exp(-lambda * (t - tau)).
        """
        w = self.adj.get(u, {}).get(v, 0.0)
        if w == 0.0 or self.temporal_decay_lambda <= 0.0 or current_time is None:
            return w

        tau = self.edge_timestamps.get((u, v), current_time)
        delta_t = max(0.0, current_time - tau)
        return w * math.exp(-self.temporal_decay_lambda * delta_t)

    def copy(self) -> 'DynamicGraph':
        """Deep copy of current graph snapshot for isolated benchmark verification."""
        new_g = DynamicGraph(self.temporal_decay_lambda)
        for u, nbrs in self.adj.items():
            new_g.adj[u] = dict(nbrs)
            new_g.degrees[u] = self.degrees[u]
            new_g.node_metadata[u] = dict(self.node_metadata.get(u, {}))
        new_g.edge_timestamps = dict(self.edge_timestamps)
        new_g.total_weight = self.total_weight
        return new_g
