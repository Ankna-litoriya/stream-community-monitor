"""
Stream-Based Community Monitor Engine.
Micro-Batch Orchestrator processing incoming edge windows (e.g. 1,000 edges).
Integrates:
- Incremental LPA (Modularity-Specialized) & Incremental Louvain
- Full Batch Baselines (Global LPA & Global Louvain)
- Hawkes Self-Exciting Temporal Point Process & Kleinberg Multi-State Burst Automaton
- MongoDB Resilient State Persistence & Comprehensive Diagnostic Telemetry
"""

from typing import Dict, List, Set, Any, Optional
import time
from collections import defaultdict

from ..models.dynamic_graph import DynamicGraph, EdgeRecord
from ..models.community import CommunityState, CommunityTelemetry
from ..algorithms.incremental_lpa import IncrementalLPA
from ..algorithms.batch_lpa import FullBatchLPA
from ..algorithms.incremental_louvain import IncrementalLouvain
from ..algorithms.batch_louvain import FullBatchLouvain
from ..algorithms.burst_models import HawkesProcessModel, KleinbergBurstAutomaton
from ..algorithms.metrics import compute_modularity, compute_nmi, compute_burst_metrics
from ..storage.mongo_store import MongoStore
from ..config import DEFAULT_CONFIG, AppConfig


class StreamCommunityEngine:
    """
    Real-Time Dynamic Community Stream Processing Engine.
    Processes continuous micro-batches of edges and tracks surging communities.
    """

    def __init__(self, config: Optional[AppConfig] = None):
        self.config = config or DEFAULT_CONFIG
        self.graph = DynamicGraph(temporal_decay_lambda=self.config.streaming.temporal_decay_lambda)

        # Community Detection Algorithms
        self.inc_lpa = IncrementalLPA(
            max_hops=self.config.streaming.max_propagation_hops,
            max_local_iterations=self.config.streaming.max_local_iterations,
            temporal_decay_lambda=self.config.streaming.temporal_decay_lambda
        )
        self.inc_louvain = IncrementalLouvain(max_local_passes=5)

        self.batch_lpa = FullBatchLPA(
            max_global_iterations=self.config.streaming.max_global_iterations,
            temporal_decay_lambda=self.config.streaming.temporal_decay_lambda
        )
        self.batch_louvain = FullBatchLouvain(max_passes=10)

        # Storage layer (MongoDB with in-memory fallback)
        self.store = MongoStore(
            uri=self.config.mongo.uri,
            db_name=self.config.mongo.database_name
        )

        # Community States & Point-Process Models
        self.community_states: Dict[str, CommunityState] = {}
        self.community_telemetry: Dict[str, CommunityTelemetry] = defaultdict(CommunityTelemetry)
        self.hawkes_models: Dict[str, HawkesProcessModel] = defaultdict(lambda: HawkesProcessModel(mu=1.0, alpha=0.6, beta=0.8))
        self.kleinberg_models: Dict[str, KleinbergBurstAutomaton] = defaultdict(lambda: KleinbergBurstAutomaton(s=2.5, gamma=1.0))

        self.batch_counter: int = 0
        self.recent_metrics: List[Dict[str, Any]] = []

    def process_micro_batch(
        self,
        edges: List[EdgeRecord],
        algorithm: str = "i-lpa",
        run_batch_baseline: bool = True
    ) -> Dict[str, Any]:
        """
        Executes end-to-end processing of an incoming micro-batch of edges (e.g. 1,000 edges).
        Returns comprehensive performance diagnostic payload.
        """
        self.batch_counter += 1
        batch_id = self.batch_counter
        batch_size = len(edges)

        # 1. Update dynamic graph with micro-batch & extract Active Perturbation Frontier
        t_ingest_start = time.perf_counter()
        frontier_nodes = self.graph.apply_batch(edges)
        t_ingest_ms = (time.perf_counter() - t_ingest_start) * 1000.0

        # 2. Incremental algorithm execution on affected neighborhood
        if algorithm == "i-louvain":
            inc_partition = self.inc_louvain.fit_batch(self.graph, frontier_nodes, batch_id)
            inc_time_ms = self.inc_louvain.last_execution_time_ms
            inc_nodes_evaluated = self.inc_louvain.last_nodes_evaluated
            inc_flips = self.inc_louvain.last_label_flips
        else:
            inc_partition = self.inc_lpa.fit_batch(self.graph, frontier_nodes, batch_id)
            inc_time_ms = self.inc_lpa.last_execution_time_ms
            inc_nodes_evaluated = self.inc_lpa.last_nodes_evaluated
            inc_flips = self.inc_lpa.last_label_flips

        # 3. Optional Full Batch baseline execution across all accumulated nodes/edges
        batch_time_ms = 0.0
        batch_nodes_evaluated = 0
        modularity_batch = 0.0
        nmi_score = 1.0

        if run_batch_baseline:
            if algorithm == "i-louvain":
                batch_partition = self.batch_louvain.fit_batch(self.graph, frontier_nodes, batch_id)
                batch_time_ms = self.batch_louvain.last_execution_time_ms
                batch_nodes_evaluated = self.batch_louvain.last_nodes_evaluated
            else:
                batch_partition = self.batch_lpa.fit_batch(self.graph, frontier_nodes, batch_id)
                batch_time_ms = self.batch_lpa.last_execution_time_ms
                batch_nodes_evaluated = self.batch_lpa.last_nodes_evaluated

            modularity_batch = compute_modularity(self.graph, batch_partition)
            nmi_score = compute_nmi(inc_partition, batch_partition)

        # 4. Modularity of Incremental Partition
        modularity_inc = compute_modularity(self.graph, inc_partition)

        # Speedup ratio
        speedup = (batch_time_ms / max(inc_time_ms, 0.001)) if run_batch_baseline else 1.0

        # 5. Community-Level Telemetry & Advanced Burst Modeling
        community_incoming_edges: Dict[str, int] = defaultdict(int)
        community_topics: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))

        now = time.time()
        for e in edges:
            c_src = inc_partition.get(e.src)
            c_dst = inc_partition.get(e.dst)
            if c_src:
                community_incoming_edges[c_src] += 1
                if e.topic:
                    community_topics[c_src][e.topic] += 1
            if c_dst and c_dst != c_src:
                community_incoming_edges[c_dst] += 1
                if e.topic:
                    community_topics[c_dst][e.topic] += 1

        # Inverted index: community_id -> set of member nodes
        community_members: Dict[str, Set[str]] = defaultdict(set)
        for u, c in inc_partition.items():
            community_members[c].add(u)

        # Update CommunityState with Hawkes & Kleinberg metrics
        for cid, members in community_members.items():
            if cid not in self.community_states:
                self.community_states[cid] = CommunityState(community_id=cid)

            c_state = self.community_states[cid]
            c_state.members = members

            # Velocity in current batch
            vel = float(community_incoming_edges.get(cid, 0))
            c_state.current_velocity = vel

            # Historical telemetry
            telemetry = self.community_telemetry[cid]
            telemetry.record(size=len(members), velocity=vel, t=now)

            # Statistical Z-score & EMA
            ema, zscore, status = compute_burst_metrics(
                current_velocity=vel,
                velocity_history=telemetry.history_velocities,
                alpha=self.config.streaming.velocity_ema_alpha
            )
            c_state.velocity_ema = ema
            c_state.burst_zscore = zscore
            c_state.status = status

            # Hawkes Process Point Intensity
            hawkes = self.hawkes_models[cid]
            if vel > 0:
                hawkes.record_events(count=int(min(vel, 50)), current_time=now)
            c_state.hawkes_intensity = hawkes.compute_intensity(current_time=now)
            c_state.branching_ratio = hawkes.branching_ratio

            # Kleinberg Burst Automaton
            kleinberg = self.kleinberg_models[cid]
            if len(telemetry.timestamps) >= 2:
                dt = max(telemetry.timestamps[-1] - telemetry.timestamps[-2], 0.001)
                effective_interval = dt / max(vel, 1.0)
                kleinberg.add_observation(effective_interval)
            k_state, _ = kleinberg.detect_burst_state()
            c_state.kleinberg_burst_state = k_state

            # Override status to SURGING if Hawkes is supercritical or Kleinberg burst active
            if k_state == 1 or hawkes.branching_ratio >= 1.0 or zscore >= 2.5:
                c_state.status = "SURGING"
            elif zscore >= 1.5:
                c_state.status = "TRENDING"
            elif zscore >= 0.5:
                c_state.status = "ACTIVE"
            else:
                c_state.status = "STABLE"

            # Merge topics
            if cid in community_topics:
                for top, count in community_topics[cid].items():
                    c_state.top_topics[top] = c_state.top_topics.get(top, 0) + count

            c_state.last_updated_batch = batch_id
            c_state.last_updated_time = now

        # 6. MongoDB State Persistence
        self.store.save_community_states(self.community_states, batch_id)
        self.store.save_stream_metric(
            batch_id=batch_id,
            batch_size=batch_size,
            total_nodes=self.graph.num_nodes,
            total_edges=self.graph.num_edges,
            inc_time_ms=inc_time_ms,
            batch_time_ms=batch_time_ms,
            speedup=speedup,
            modularity_inc=modularity_inc,
            modularity_batch=modularity_batch,
            nmi=nmi_score
        )

        # 7. Diagnostic snapshot payload
        metrics_payload = {
            "batch_id": batch_id,
            "algorithm": algorithm,
            "batch_size": batch_size,
            "total_nodes": self.graph.num_nodes,
            "total_edges": self.graph.num_edges,
            "frontier_nodes_count": len(frontier_nodes),
            "time_ingest_ms": round(t_ingest_ms, 2),
            "time_incremental_ms": round(inc_time_ms, 2),
            "time_batch_ms": round(batch_time_ms, 2),
            "speedup_factor": round(speedup, 2),
            "nodes_evaluated_inc": inc_nodes_evaluated,
            "nodes_evaluated_batch": batch_nodes_evaluated,
            "label_flips_inc": inc_flips,
            "modularity_incremental": round(modularity_inc, 4),
            "modularity_batch": round(modularity_batch, 4) if run_batch_baseline else None,
            "nmi_consistency": round(nmi_score, 4) if run_batch_baseline else None,
            "num_communities": len(self.community_states)
        }

        self.recent_metrics.append(metrics_payload)
        return metrics_payload

    def get_top_trending(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Returns top trending communities ranked by burst Z-score and velocity."""
        return self.store.get_trending_communities(limit=limit)
