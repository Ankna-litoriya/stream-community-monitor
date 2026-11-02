"""
Storage Layer: MongoDB Community State Store with Resilient Document Store Fallback.
Provides persistence for:
1. Dynamic Community States (members, size, velocity, burst score, topics)
2. Inverted Node Index (node -> community, degree, active batch)
3. Streaming Telemetry & Benchmark Metrics (execution time, modularity, speedup)
"""

from typing import Dict, List, Any, Optional
import time
import json
import os
from ..models.community import CommunityState


class InMemoryMongoFallback:
    """
    In-memory document store matching the PyMongo collection interface.
    Ensures zero-downtime execution in standalone or offline environments.
    """

    def __init__(self, name: str):
        self.name = name
        self.documents: Dict[str, Dict[str, Any]] = {}

    def insert_one(self, doc: Dict[str, Any]) -> None:
        doc_id = str(doc.get("_id", doc.get("community_id", doc.get("batch_id", time.time()))))
        self.documents[doc_id] = dict(doc)

    def update_one(self, filter_query: Dict[str, Any], update_ops: Dict[str, Any], upsert: bool = False) -> None:
        key = None
        for k, v in filter_query.items():
            key = str(v)
            break

        doc = self.documents.get(key, {}) if key else {}
        if not doc and not upsert:
            return

        if "$set" in update_ops:
            doc.update(update_ops["$set"])
        else:
            doc.update(update_ops)

        if key:
            self.documents[key] = doc

    def find(self, filter_query: Optional[Dict[str, Any]] = None, sort: Optional[List] = None, limit: int = 0) -> List[Dict[str, Any]]:
        results = list(self.documents.values())
        if filter_query:
            filtered = []
            for d in results:
                match = True
                for k, v in filter_query.items():
                    if d.get(k) != v:
                        match = False
                        break
                if match:
                    filtered.append(d)
            results = filtered

        if sort:
            sort_key, direction = sort[0]
            reverse = (direction == -1 or direction == "desc")
            results.sort(key=lambda x: x.get(sort_key, 0), reverse=reverse)

        if limit > 0:
            results = results[:limit]

        return results

    def count_documents(self, filter_query: Optional[Dict] = None) -> int:
        return len(self.find(filter_query))

    def clear(self) -> None:
        self.documents.clear()


class MongoStore:
    """
    Production MongoDB interface with automatic connection discovery and failover.
    """

    def __init__(self, uri: str = "mongodb://localhost:27017/", db_name: str = "stream_community_db"):
        self.uri = uri
        self.db_name = db_name
        self.is_live_mongo = False
        self.client = None
        self.db = None

        # Collections (live or fallback)
        self.communities = None
        self.node_index = None
        self.metrics = None

        self._init_connection()

    def _init_connection(self) -> None:
        """Attempts connection to live MongoDB; falls back gracefully if offline."""
        try:
            import pymongo
            self.client = pymongo.MongoClient(self.uri, serverSelectionTimeoutMS=1000)
            # Ping database to verify active server
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            self.communities = self.db["communities"]
            self.node_index = self.db["node_index"]
            self.metrics = self.db["stream_metrics"]
            self.is_live_mongo = True
            print(f"[MongoStore] Connected to live MongoDB at {self.uri}")
        except Exception:
            self.is_live_mongo = False
            self.communities = InMemoryMongoFallback("communities")
            self.node_index = InMemoryMongoFallback("node_index")
            self.metrics = InMemoryMongoFallback("stream_metrics")
            print("[MongoStore] Live MongoDB not detected. Initialized high-performance In-Memory Document Store.")

    def save_community_states(self, community_states: Dict[str, CommunityState], batch_id: int) -> None:
        """
        Persists community states (upsert pattern).
        """
        for cid, state in community_states.items():
            doc = state.to_dict()
            doc["batch_id"] = batch_id
            self.communities.update_one(
                {"community_id": cid},
                {"$set": doc},
                upsert=True
            )

    def save_stream_metric(
        self,
        batch_id: int,
        batch_size: int,
        total_nodes: int,
        total_edges: int,
        inc_time_ms: float,
        batch_time_ms: float,
        speedup: float,
        modularity_inc: float,
        modularity_batch: float,
        nmi: float
    ) -> None:
        """
        Saves telemetry comparison between Incremental vs Full Batch.
        """
        metric_doc = {
            "batch_id": batch_id,
            "timestamp": time.time(),
            "batch_size": batch_size,
            "total_nodes": total_nodes,
            "total_edges": total_edges,
            "time_incremental_ms": round(inc_time_ms, 2),
            "time_batch_ms": round(batch_time_ms, 2),
            "speedup_factor": round(speedup, 2),
            "modularity_incremental": round(modularity_inc, 4),
            "modularity_batch": round(modularity_batch, 4),
            "nmi_consistency": round(nmi, 4)
        }
        self.metrics.insert_one(metric_doc)

    def get_trending_communities(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves top trending communities ranked by burst Z-score and velocity.
        """
        return self.communities.find(
            filter_query=None,
            sort=[("burst_zscore", -1)],
            limit=limit
        )

    def get_all_metrics(self) -> List[Dict[str, Any]]:
        """
        Retrieves history of stream performance benchmarks.
        """
        return self.metrics.find(sort=[("batch_id", 1)])
