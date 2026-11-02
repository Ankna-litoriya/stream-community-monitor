"""
Graph Quality & Streaming Telemetry Metrics.
Implements:
- Newman-Girvan Modularity (Q)
- Partition Consistency / Normalized Mutual Information (NMI)
- Community Velocity & Kleinberg-style Statistical Burst Z-Score
"""

from typing import Dict, Set, List, Tuple, Optional
import math
from collections import defaultdict
from ..models.dynamic_graph import DynamicGraph


def compute_modularity(graph: DynamicGraph, partition: Dict[str, str]) -> float:
    """
    Computes standard Newman-Girvan Modularity Q for the given partition:
    Q = sum_c [ (Sigma_in(c) / 2m) - (Sigma_tot(c) / 2m)^2 ]
    Where 2m = total graph degree volume.
    """
    m2 = 2.0 * graph.total_weight
    if m2 <= 0.0:
        return 0.0

    community_internal_weight: Dict[str, float] = defaultdict(float)
    community_total_degree: Dict[str, float] = defaultdict(float)

    for u, deg in graph.degrees.items():
        c_u = partition.get(u)
        if c_u is None:
            continue
        community_total_degree[c_u] += deg

        for v, w in graph.adj.get(u, {}).items():
            c_v = partition.get(v)
            if c_u == c_v:
                # Undirected edge counted from both u and v, so internal weight is sum(w)
                community_internal_weight[c_u] += w

    q = 0.0
    for c, deg_c in community_total_degree.items():
        in_w = community_internal_weight[c]
        # in_w / m2 - (deg_c / m2)^2
        q += (in_w / m2) - ((deg_c / m2) ** 2)

    return max(-0.5, min(1.0, q))


def compute_nmi(partition_a: Dict[str, str], partition_b: Dict[str, str]) -> float:
    """
    Computes Normalized Mutual Information (NMI) between two community partitions.
    Used to mathematically verify that the Incremental Update preserves structural
    fidelity with the Full Batch partition.
    """
    common_nodes = list(set(partition_a.keys()).intersection(set(partition_b.keys())))
    n = len(common_nodes)
    if n == 0:
        return 1.0

    labels_a = [partition_a[u] for u in common_nodes]
    labels_b = [partition_b[u] for u in common_nodes]

    # Map labels to integers
    map_a: Dict[str, int] = {}
    map_b: Dict[str, int] = {}
    for l in labels_a:
        if l not in map_a:
            map_a[l] = len(map_a)
    for l in labels_b:
        if l not in map_b:
            map_b[l] = len(map_b)

    # Contingency matrix
    ka = len(map_a)
    kb = len(map_b)
    if ka <= 1 and kb <= 1:
        return 1.0

    contingency = defaultdict(int)
    count_a = defaultdict(int)
    count_b = defaultdict(int)

    for la, lb in zip(labels_a, labels_b):
        ia = map_a[la]
        ib = map_b[lb]
        contingency[(ia, ib)] += 1
        count_a[ia] += 1
        count_b[ib] += 1

    # Mutual Information
    mi = 0.0
    for (ia, ib), n_ij in contingency.items():
        p_ij = n_ij / n
        p_i = count_a[ia] / n
        p_j = count_b[ib] / n
        if p_ij > 0 and p_i > 0 and p_j > 0:
            mi += p_ij * math.log(p_ij / (p_i * p_j))

    # Entropies H(A) and H(B)
    ha = -sum((cnt / n) * math.log(cnt / n) for cnt in count_a.values() if cnt > 0)
    hb = -sum((cnt / n) * math.log(cnt / n) for cnt in count_b.values() if cnt > 0)

    denominator = math.sqrt(ha * hb)
    if denominator <= 1e-12:
        return 1.0

    return max(0.0, min(1.0, mi / denominator))


def compute_burst_metrics(
    current_velocity: float,
    velocity_history: List[float],
    alpha: float = 0.3
) -> Tuple[float, float, str]:
    """
    Computes Exponential Moving Average (EMA) and Statistical Z-Score for burst detection:
    Z = (v_t - mu) / (sigma + eps).
    Returns (velocity_ema, burst_zscore, status_str).
    """
    if not velocity_history:
        return current_velocity, 0.0, "STABLE"

    # Compute mean and standard deviation over historical window
    n = len(velocity_history)
    mu = sum(velocity_history) / n
    variance = sum((x - mu) ** 2 for x in velocity_history) / n
    sigma = math.sqrt(variance)

    # Z-score with Laplace smoothing epsilon
    z = (current_velocity - mu) / (sigma + 1.0)

    # Classification
    if z >= 2.5:
        status = "SURGING"
    elif z >= 1.5:
        status = "TRENDING"
    elif z >= 0.5:
        status = "ACTIVE"
    else:
        status = "STABLE"

    # Exponential moving average
    prev_ema = velocity_history[-1]
    new_ema = (alpha * current_velocity) + ((1.0 - alpha) * prev_ema)

    return new_ema, z, status
