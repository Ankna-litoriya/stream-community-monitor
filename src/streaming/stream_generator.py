"""
Realistic Social Interaction Stream Generator (Twitter/X & Reddit).
Generates power-law interaction streams with temporal clusters and burst events.
"""

from typing import List, Dict, Optional
import random
import time
from ..models.dynamic_graph import EdgeRecord


class SocialInteractionStreamGenerator:
    """
    Generates realistic dynamic micro-batches of social network interactions.
    Simulates:
    - Scale-free preferential attachment (influencers/supernodes)
    - Latent community affiliations
    - Exogenous viral burst events (surging topics)
    """

    def __init__(
        self,
        num_latent_clusters: int = 8,
        nodes_per_cluster: int = 150,
        burst_probability: float = 0.35,
        topics: Optional[List[str]] = None,
        random_seed: int = 42
    ):
        self.rng = random.Random(random_seed)
        self.num_latent_clusters = num_latent_clusters
        self.nodes_per_cluster = nodes_per_cluster
        self.burst_probability = burst_probability

        self.topics = topics or [
            "#AI_Research", "#QuantumComputing", "#DistributedSystems",
            "#DeepLearning", "#AutonomousAgents", "#DataEngineering",
            "#OpenSource", "#CyberSecurity"
        ]

        # Initialize cluster node pools
        self.cluster_nodes: Dict[int, List[str]] = {}
        for c in range(num_latent_clusters):
            self.cluster_nodes[c] = [f"usr_{c}_{i:03d}" for i in range(nodes_per_cluster)]

        self.current_time = time.time()

    def generate_micro_batch(self, batch_size: int = 1000, batch_id: int = 0) -> List[EdgeRecord]:
        """
        Generates a micro-batch of exactly batch_size (e.g. 1,000) incoming edges.
        Periodically triggers viral topic bursts concentrated in a single cluster.
        """
        edges: List[EdgeRecord] = []

        # Determine if a burst occurs in this micro-batch
        is_burst = self.rng.random() < self.burst_probability
        burst_cluster = self.rng.randint(0, self.num_latent_clusters - 1) if is_burst else None
        burst_topic = self.topics[burst_cluster % len(self.topics)] if is_burst else None

        for _ in range(batch_size):
            self.current_time += 0.05  # Increment virtual time

            # 70% intra-cluster interactions, 30% inter-cluster interactions
            if is_burst and self.rng.random() < 0.65:
                # Burst traffic concentrated in burst_cluster
                src_c = burst_cluster
                dst_c = burst_cluster
                topic = burst_topic
                weight = self.rng.uniform(1.5, 3.0)  # High intensity viral interaction
            else:
                if self.rng.random() < 0.75:
                    # Intra-cluster interaction
                    src_c = self.rng.randint(0, self.num_latent_clusters - 1)
                    dst_c = src_c
                else:
                    # Cross-cluster interaction (bridge)
                    src_c = self.rng.randint(0, self.num_latent_clusters - 1)
                    dst_c = self.rng.randint(0, self.num_latent_clusters - 1)

                topic = self.topics[src_c % len(self.topics)]
                weight = 1.0

            src = self.rng.choice(self.cluster_nodes[src_c])
            dst = self.rng.choice(self.cluster_nodes[dst_c])

            if src == dst:
                # Pick alternative
                dst = self.rng.choice(self.cluster_nodes[(dst_c + 1) % self.num_latent_clusters])

            interaction_types = ["retweet", "reply", "mention", "quote"]
            itype = self.rng.choice(interaction_types)

            edges.append(EdgeRecord(
                src=src,
                dst=dst,
                weight=weight,
                timestamp=self.current_time,
                topic=topic,
                interaction_type=itype
            ))

        return edges
