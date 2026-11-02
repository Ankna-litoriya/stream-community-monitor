"""
Community State & Telemetry Data Models.
Tracks dynamic community properties: member count, velocity, burst score,
modularity contribution, and trending classification.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional
import time


@dataclass
class CommunityTelemetry:
    """
    Time-series tracking of community expansion & interaction velocity.
    """
    history_sizes: List[int] = field(default_factory=list)
    history_velocities: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)

    def record(self, size: int, velocity: float, t: Optional[float] = None) -> None:
        self.history_sizes.append(size)
        self.history_velocities.append(velocity)
        self.timestamps.append(t or time.time())
        # Retain recent 50 checkpoints
        if len(self.history_sizes) > 50:
            self.history_sizes.pop(0)
            self.history_velocities.pop(0)
            self.timestamps.pop(0)


@dataclass
class CommunityState:
    """
    Persisted state of a detected community.
    Compatible with MongoDB document model.
    """
    community_id: str
    members: Set[str] = field(default_factory=set)
    total_internal_weight: float = 0.0
    total_degree: float = 0.0
    current_velocity: float = 0.0  # Interactions per second / per micro-batch
    velocity_ema: float = 0.0      # Exponential moving average of velocity
    burst_zscore: float = 0.0      # Kleinberg / Statistical Z-score
    hawkes_intensity: float = 0.0  # Hawkes Point Process conditional intensity
    branching_ratio: float = 0.0   # Hawkes criticality metric alpha / beta
    kleinberg_burst_state: int = 0 # 0=baseline, 1=burst
    status: str = "STABLE"         # "SURGING", "TRENDING", "ACTIVE", "STABLE"
    top_topics: Dict[str, int] = field(default_factory=dict)
    last_updated_batch: int = 0
    last_updated_time: float = field(default_factory=time.time)

    @property
    def size(self) -> int:
        return len(self.members)

    def to_dict(self) -> Dict:
        """Serializes to MongoDB document."""
        return {
            "community_id": self.community_id,
            "size": self.size,
            "members": list(self.members)[:500],  # cap serialized members for high-scale storage
            "total_internal_weight": self.total_internal_weight,
            "total_degree": self.total_degree,
            "current_velocity": round(self.current_velocity, 3),
            "velocity_ema": round(self.velocity_ema, 3),
            "burst_zscore": round(self.burst_zscore, 3),
            "hawkes_intensity": round(self.hawkes_intensity, 3),
            "branching_ratio": round(self.branching_ratio, 3),
            "kleinberg_burst_state": self.kleinberg_burst_state,
            "status": self.status,
            "top_topics": self.top_topics,
            "last_updated_batch": self.last_updated_batch,
            "last_updated_time": self.last_updated_time
        }
