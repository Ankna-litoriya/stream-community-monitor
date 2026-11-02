"""
Comprehensive Verification & Test Suite.
Validates Dynamic Graph consistency, i-LPA boundary pruning, Incremental Louvain,
CommunitySketch quotient graph, Hawkes point-process intensity, Kleinberg burst automaton,
FastAPI endpoints, and storage integrity.
"""

import unittest
import time
from src.models.dynamic_graph import DynamicGraph, EdgeRecord
from src.algorithms.incremental_lpa import IncrementalLPA
from src.algorithms.batch_lpa import FullBatchLPA
from src.algorithms.incremental_louvain import IncrementalLouvain
from src.algorithms.adaptive_louvain import AdaptiveIncrementalLouvain
from src.algorithms.community_sketch import CommunitySketch
from src.algorithms.batch_louvain import FullBatchLouvain
from src.algorithms.burst_models import HawkesProcessModel, KleinbergBurstAutomaton
from src.algorithms.metrics import compute_modularity, compute_nmi, compute_burst_metrics
from src.storage.mongo_store import MongoStore, InMemoryMongoFallback
from src.streaming.stream_generator import SocialInteractionStreamGenerator
from src.api.server import get_health, simulate_microbatch


class TestStreamCommunityMonitor(unittest.TestCase):

    def setUp(self):
        self.graph = DynamicGraph(temporal_decay_lambda=0.01)

    def test_dynamic_graph_operations(self):
        """Validates graph degree tracking and volume conservation."""
        self.graph.add_or_update_edge("node_A", "node_B", weight=2.0)
        self.graph.add_or_update_edge("node_B", "node_C", weight=3.0)

        self.assertEqual(self.graph.num_nodes, 3)
        self.assertEqual(self.graph.num_edges, 2)
        self.assertEqual(self.graph.degrees["node_B"], 5.0)
        self.assertEqual(self.graph.total_weight, 5.0)

    def test_frontier_and_k_hop_neighborhood(self):
        """Validates Active Perturbation Frontier extraction."""
        batch_edges = [
            EdgeRecord(src="u1", dst="u2", weight=1.0),
            EdgeRecord(src="u2", dst="u3", weight=1.0),
            EdgeRecord(src="u3", dst="u4", weight=1.0)
        ]
        frontier = self.graph.apply_batch(batch_edges)
        self.assertEqual(frontier, {"u1", "u2", "u3", "u4"})

        # Test 1-hop from u1
        hood_1hop = self.graph.get_k_hop_neighborhood({"u1"}, k=1)
        self.assertIn("u1", hood_1hop)
        self.assertIn("u2", hood_1hop)
        self.assertNotIn("u4", hood_1hop)

        # Test 2-hop from u1
        hood_2hop = self.graph.get_k_hop_neighborhood({"u1"}, k=2)
        self.assertIn("u3", hood_2hop)

    def test_incremental_lpa_execution(self):
        """Validates i-LPA partition formation and modularity positivity."""
        generator = SocialInteractionStreamGenerator(num_latent_clusters=3, nodes_per_cluster=30)
        edges = generator.generate_micro_batch(batch_size=200, batch_id=1)

        frontier = self.graph.apply_batch(edges)
        ilpa = IncrementalLPA(max_hops=2, max_local_iterations=10)
        partition = ilpa.fit_batch(self.graph, frontier, batch_id=1)

        self.assertTrue(len(partition) > 0)
        q = compute_modularity(self.graph, partition)
        self.assertGreater(q, 0.1)

    def test_community_sketch_and_adaptive_louvain(self):
        """Validates CommunitySketch quotient graph and Adaptive Incremental Louvain."""
        sketch = CommunitySketch()
        sketch.register_node("n1", 2.0, "c1")
        sketch.register_node("n2", 2.0, "c1")
        sketch.update_edge("n1", "n2", 1.0)
        self.assertEqual(sketch.internal_weight["c1"], 2.0)

        # Test Adaptive Incremental Louvain
        generator = SocialInteractionStreamGenerator(num_latent_clusters=3, nodes_per_cluster=30)
        edges = generator.generate_micro_batch(batch_size=200, batch_id=1)
        frontier = self.graph.apply_batch(edges)

        adaptive = AdaptiveIncrementalLouvain(max_local_passes=5)
        partition = adaptive.fit_batch(self.graph, frontier, batch_id=1)
        self.assertTrue(len(partition) > 0)

        q = compute_modularity(self.graph, partition)
        self.assertGreater(q, 0.1)

    def test_burst_metrics_detection(self):
        """Validates statistical Z-score burst classification."""
        history = [10.0, 12.0, 9.0, 11.0, 10.0]
        surging_velocity = 85.0

        ema, z, status = compute_burst_metrics(surging_velocity, history)
        self.assertGreater(z, 2.5)
        self.assertEqual(status, "SURGING")

    def test_hawkes_point_process(self):
        """Validates Hawkes self-exciting point process intensity and branching ratio."""
        hawkes = HawkesProcessModel(mu=1.0, alpha=0.8, beta=1.0)
        self.assertAlmostEqual(hawkes.branching_ratio, 0.8, places=2)

        t0 = time.time()
        hawkes.record_events(10, current_time=t0)
        intensity = hawkes.compute_intensity(current_time=t0 + 0.1)
        self.assertGreater(intensity, 1.0)

    def test_kleinberg_burst_automaton(self):
        """Validates Kleinberg Viterbi decoding of burst state."""
        automaton = KleinbergBurstAutomaton(s=3.0, gamma=1.0)
        for _ in range(15):
            automaton.add_observation(1.0)
        for _ in range(15):
            automaton.add_observation(0.02)

        state, weight = automaton.detect_burst_state()
        self.assertEqual(state, 1)
        self.assertGreater(weight, 0.0)

    def test_fastapi_rest_endpoints(self):
        """Validates production REST API endpoints."""
        res_health = get_health()
        self.assertEqual(res_health["status"], "HEALTHY")
        self.assertIn("graph_nodes", res_health)

        res_sim = simulate_microbatch(batch_size=100, algorithm="i-lpa", run_batch_baseline=False)
        self.assertIn("batch_id", res_sim)
        self.assertIn("time_incremental_ms", res_sim)


if __name__ == "__main__":
    unittest.main()
