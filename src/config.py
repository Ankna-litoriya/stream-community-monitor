"""
System Configuration & Hyperparameters for Stream-Based Community Monitor.
Publication & Production Standard: IEEE TKDE / ACM KDD / FAANG MLOps.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class StreamingConfig:
    batch_size: int = 1000  # Micro-batch window size (incoming edges per batch)
    temporal_decay_lambda: float = 0.005  # Temporal edge weight decay parameter
    burst_zscore_threshold: float = 2.0  # Statistical significance for burst surge
    velocity_ema_alpha: float = 0.3  # Exponential moving average smoothing for velocity
    max_propagation_hops: int = 2  # Boundary neighborhood expansion limit
    convergence_tol: float = 1e-4  # Delta modularity / label change tolerance
    max_local_iterations: int = 15  # Max localized LPA iterations per micro-batch
    max_global_iterations: int = 30  # Max batch LPA iterations for full recomputation


@dataclass
class MongoConfig:
    uri: str = "mongodb://localhost:27017/"
    database_name: str = "stream_community_db"
    communities_collection: str = "communities"
    node_index_collection: str = "node_index"
    metrics_collection: str = "stream_metrics"
    use_mock_fallback: bool = True  # Gracefully fall back to persistent in-memory engine if MongoDB is offline


@dataclass
class SimulationConfig:
    num_initial_nodes: int = 500
    num_initial_edges: int = 2000
    num_stream_batches: int = 15  # 15 batches x 1000 edges = 15,000 dynamic stream edges
    burst_probability: float = 0.25  # Probability of synthetic burst in a trending community
    topics: List[str] = field(default_factory=lambda: [
        "#AI_Research", "#QuantumComputing", "#DistributedSystems",
        "#DeepLearning", "#AutonomousAgents", "#DataEngineering",
        "#OpenSource", "#CyberSecurity", "#GraphTheory", "#CloudNative"
    ])


@dataclass
class AppConfig:
    streaming: StreamingConfig = field(default_factory=StreamingConfig)
    mongo: MongoConfig = field(default_factory=MongoConfig)
    simulation: SimulationConfig = field(default_factory=SimulationConfig)


# Global default configuration instance
DEFAULT_CONFIG = AppConfig()
