"""
Empirical Benchmark Suite: Incremental Update vs. Full Batch Processing.
Publication & Journal Standard: IEEE TKDE / ACM SIGKDD.

Evaluates:
1. Latency Scaling: Execution time (ms) as graph size |V| and |E| grow monotonically.
2. Speedup Factor: T_batch / T_incremental.
3. Modularity Quality: Q_incremental vs Q_batch.
4. Partition Fidelity: Normalized Mutual Information (NMI).
5. Visited Nodes Ratio: Evaluates theoretical boundary pruning O(|Delta E| * d^k) << O(|V| + |E|).
"""

import sys
import os
import time
import json
import csv

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add workspace to path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.streaming.stream_engine import StreamCommunityEngine
from src.streaming.stream_generator import SocialInteractionStreamGenerator
from src.config import AppConfig, StreamingConfig, SimulationConfig


def run_scaling_benchmark(num_batches: int = 12, batch_size: int = 1000):
    """
    Executes benchmark over consecutive streaming micro-batches of 1,000 edges.
    """
    print("=" * 88)
    print(" STREAM-BASED COMMUNITY MONITOR: INCREMENTAL vs FULL BATCH BENCHMARK")
    print(f" Micro-Batch Window Size: {batch_size} incoming edges | Batches: {num_batches}")
    print("=" * 88)

    config = AppConfig()
    config.streaming.batch_size = batch_size
    engine = StreamCommunityEngine(config)
    generator = SocialInteractionStreamGenerator(num_latent_clusters=8, nodes_per_cluster=200, burst_probability=0.35)

    results = []

    header = (
        f"{'Batch':^6} | {'Nodes |V|':^10} | {'Edges |E|':^10} | "
        f"{'Inc (ms)':^10} | {'Batch (ms)':^10} | {'Speedup':^9} | "
        f"{'Q_inc':^8} | {'Q_batch':^8} | {'NMI':^6} | {'Status':^12}"
    )
    print(header)
    print("-" * len(header))

    for b in range(1, num_batches + 1):
        # Generate micro-batch of 1,000 streaming edges
        edges = generator.generate_micro_batch(batch_size=batch_size, batch_id=b)

        # Process batch through streaming orchestrator
        metrics = engine.process_micro_batch(edges, run_batch_baseline=True)

        # Determine trending status of highest burst community
        top_communities = engine.get_top_trending(limit=1)
        top_status = top_communities[0]["status"] if top_communities else "STABLE"

        row = (
            f"{metrics['batch_id']:^6d} | "
            f"{metrics['total_nodes']:^10d} | "
            f"{metrics['total_edges']:^10d} | "
            f"{metrics['time_incremental_ms']:^10.2f} | "
            f"{metrics['time_batch_ms']:^10.2f} | "
            f"{metrics['speedup_factor']:^8.1f}x | "
            f"{metrics['modularity_incremental']:^8.4f} | "
            f"{metrics['modularity_batch']:^8.4f} | "
            f"{metrics['nmi_consistency']:^6.3f} | "
            f"{top_status:^12}"
        )
        print(row)

        results.append(metrics)

    print("-" * len(header))
    print("BENCHMARK SUMMARY & EMPIRICAL FINDINGS:")

    avg_inc = sum(r['time_incremental_ms'] for r in results) / len(results)
    avg_batch = sum(r['time_batch_ms'] for r in results) / len(results)
    max_speedup = max(r['speedup_factor'] for r in results)
    final_nodes = results[-1]['total_nodes']
    final_edges = results[-1]['total_edges']

    print(f" * Accumulated Graph Scale:   {final_nodes:,} vertices, {final_edges:,} interaction edges")
    print(f" * Average Incremental Time:  {avg_inc:.2f} ms per micro-batch")
    print(f" * Average Full Batch Time:   {avg_batch:.2f} ms per micro-batch")
    print(f" * Peak Empirical Speedup:    {max_speedup:.1f}x faster")
    print(f" * Average NMI Agreement:     {sum(r['nmi_consistency'] for r in results)/len(results):.4f}")
    print(f" * Average Modularity Delta:  {abs(sum(r['modularity_incremental']-r['modularity_batch'] for r in results)/len(results)):.4f}")
    print("=" * 88)

    # Save to CSV
    csv_file = os.path.join(parent_dir, "benchmark_results.csv")
    with open(csv_file, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"\n[Artifact] Benchmark CSV saved successfully to: {csv_file}")
    return results


if __name__ == "__main__":
    run_scaling_benchmark(num_batches=12, batch_size=1000)
