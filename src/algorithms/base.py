"""
Base Interface for Community Detection Algorithms.
"""

from abc import ABC, abstractmethod
from typing import Dict, Set, Tuple
from ..models.dynamic_graph import DynamicGraph


class BaseCommunityDetector(ABC):
    """
    Abstract Base Class for graph community detection.
    """

    @abstractmethod
    def fit_batch(self, graph: DynamicGraph, frontier_nodes: Set[str], batch_id: int) -> Dict[str, str]:
        """
        Executes community detection.
        Returns mapping: {node_id: community_id}.
        """
        pass

    @abstractmethod
    def get_partition(self) -> Dict[str, str]:
        """
        Returns the current node -> community mapping.
        """
        pass
