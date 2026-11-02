"""
Production FastAPI REST Microservice.
Provides real-time API endpoints for streaming community detection and telemetry.
OpenAPI Swagger docs available at /docs.
"""

from typing import List, Dict, Any, Optional
import time
import os
import sys

# Ensure parent directory in path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(current_dir))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from src.streaming.stream_engine import StreamCommunityEngine
from src.streaming.stream_generator import SocialInteractionStreamGenerator
from src.models.dynamic_graph import EdgeRecord
from src.config import AppConfig

app = FastAPI(
    title="Stream-Based Dynamic Community Monitor API",
    description="Production REST API for High-Velocity Online Community Detection & Burst Tracking",
    version="2.0.0"
)

# Initialize singleton streaming engine
engine = StreamCommunityEngine(AppConfig())
generator = SocialInteractionStreamGenerator(num_latent_clusters=8, nodes_per_cluster=180)


# -----------------------------------------------------------------------------
# Pydantic Schemas
# -----------------------------------------------------------------------------
class EdgePayload(BaseModel):
    src: str = Field(..., example="usr_102")
    dst: str = Field(..., example="usr_304")
    weight: float = Field(default=1.0, example=1.0)
    topic: Optional[str] = Field(default="#AI_Research", example="#AI_Research")
    interaction_type: str = Field(default="retweet", example="retweet")


class MicroBatchRequest(BaseModel):
    edges: List[EdgePayload]
    algorithm: str = Field(default="i-lpa", example="i-lpa")
    run_batch_baseline: bool = Field(default=False)


# -----------------------------------------------------------------------------
# REST Endpoints
# -----------------------------------------------------------------------------
@app.get("/api/v1/health", tags=["System"])
def get_health() -> Dict[str, Any]:
    """Returns engine health status, active nodes, total edges, and storage sink status."""
    return {
        "status": "HEALTHY",
        "timestamp": time.time(),
        "graph_nodes": engine.graph.num_nodes,
        "graph_edges": engine.graph.num_edges,
        "total_communities": len(engine.community_states),
        "storage_mode": "Live MongoDB" if engine.store.is_live_mongo else "Resilient In-Memory Store"
    }


@app.get("/api/v1/communities/trending", tags=["Communities"])
def get_trending_communities(limit: int = Query(default=10, ge=1, le=50)) -> List[Dict[str, Any]]:
    """Retrieves top trending communities ranked by Kleinberg Burstiness Z-score and Hawkes Intensity."""
    return engine.get_top_trending(limit=limit)


@app.get("/api/v1/metrics", tags=["Benchmarks"])
def get_metrics() -> List[Dict[str, Any]]:
    """Returns historical latency scaling benchmarks (Incremental vs Full Batch)."""
    return engine.recent_metrics


@app.post("/api/v1/stream/microbatch", tags=["Streaming"])
def ingest_microbatch(request: MicroBatchRequest) -> Dict[str, Any]:
    """Ingests a streaming micro-batch of interaction edges (e.g. 1,000 edges) and executes incremental update."""
    if not request.edges:
        raise HTTPException(status_code=400, detail="Micro-batch edges list cannot be empty.")

    edge_records = [
        EdgeRecord(
            src=e.src,
            dst=e.dst,
            weight=e.weight,
            topic=e.topic,
            interaction_type=e.interaction_type
        )
        for e in request.edges
    ]

    metrics = engine.process_micro_batch(
        edge_records,
        algorithm=request.algorithm,
        run_batch_baseline=request.run_batch_baseline
    )
    return metrics


@app.post("/api/v1/stream/simulate", tags=["Streaming"])
def simulate_microbatch(
    batch_size: int = Query(default=1000, ge=100, le=5000),
    algorithm: str = Query(default="i-lpa", pattern="^(i-lpa|i-louvain)$"),
    run_batch_baseline: bool = Query(default=True)
) -> Dict[str, Any]:
    """Generates and processes a synthetic micro-batch of social interactions with dynamic burst injection."""
    b_id = engine.batch_counter + 1
    edges = generator.generate_micro_batch(batch_size=batch_size, batch_id=b_id)
    metrics = engine.process_micro_batch(
        edges,
        algorithm=algorithm,
        run_batch_baseline=run_batch_baseline
    )
    return metrics
