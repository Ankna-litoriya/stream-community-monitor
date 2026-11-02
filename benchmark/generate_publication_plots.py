"""
Publication Plot Generator.
Generates IEEE TKDE / ACM KDD standard publication figures from benchmark results.
"""

import sys
import os
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
csv_path = os.path.join(parent_dir, "benchmark_results.csv")
output_dir = os.path.join(parent_dir, "docs", "figures")
os.makedirs(output_dir, exist_ok=True)


def generate_publication_figures():
    if not os.path.exists(csv_path):
        print(f"Benchmark CSV not found at {csv_path}. Run benchmark/run_benchmarks.py first.")
        return

    df = pd.read_csv(csv_path)

    # Set publication styling (IEEE / ACM standard)
    plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
    plt.rcParams.update({
        'font.family': 'sans-serif',
        'font.size': 11,
        'axes.labelsize': 12,
        'axes.titlesize': 13,
        'xtick.labelsize': 10,
        'ytick.labelsize': 10,
        'legend.fontsize': 10,
        'figure.titlesize': 14
    })

    # -------------------------------------------------------------------------
    # Figure 1: Scaling Latency (Incremental vs Full Batch)
    # -------------------------------------------------------------------------
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5))

    ax1.plot(df["total_edges"], df["time_batch_ms"], marker='s', color='#dc2626',
             linewidth=2.5, markersize=6, label='Full Batch Recomputation (Global LPA)')
    ax1.plot(df["total_edges"], df["time_incremental_ms"], marker='o', color='#2563eb',
             linewidth=2.5, markersize=6, label='Incremental Update (i-LPA Boundary)')

    ax1.set_title('(a) Streaming Latency Scaling vs Graph Size')
    ax1.set_xlabel('Cumulative Stream Edges $|E_t|$')
    ax1.set_ylabel('Execution Time per Micro-Batch (ms)')
    ax1.legend(loc='upper left', frameon=True)
    ax1.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.0f'))
    ax1.grid(True, linestyle='--', alpha=0.6)

    # Plot 2: Speedup Factor
    bars = ax2.bar(df["batch_id"], df["speedup_factor"], color='#059669', width=0.6,
                   edgecolor='#047857', alpha=0.85)
    ax2.set_title('(b) Speedup Factor $(T_{batch} / T_{inc})$ per Micro-Batch')
    ax2.set_xlabel('Micro-Batch Sequence Index')
    ax2.set_ylabel('Empirical Speedup Multiplier')
    ax2.axhline(y=1.0, color='gray', linestyle=':', label='Parity baseline (1.0x)')
    ax2.grid(True, linestyle='--', alpha=0.6)

    # Annotate peak speedup
    max_idx = df["speedup_factor"].idxmax()
    peak_speedup = df["speedup_factor"].iloc[max_idx]
    peak_batch = df["batch_id"].iloc[max_idx]
    ax2.annotate(f'Peak: {peak_speedup:.1f}x',
                 xy=(peak_batch, peak_speedup),
                 xytext=(peak_batch - 2, peak_speedup + 1.5),
                 arrowprops=dict(facecolor='black', shrink=0.08, width=1, headwidth=6))

    plt.tight_layout()
    fig1_path = os.path.join(output_dir, "scaling_benchmark.png")
    fig.savefig(fig1_path, dpi=300)
    plt.close()
    print(f"[Publication Figure] Saved: {fig1_path}")

    # -------------------------------------------------------------------------
    # Figure 2: Quality Preservation (Modularity & NMI)
    # -------------------------------------------------------------------------
    fig2, (ax3, ax4) = plt.subplots(1, 2, figsize=(13, 5))

    ax3.plot(df["batch_id"], df["modularity_incremental"], marker='o', color='#2563eb',
             linewidth=2.2, label='Incremental i-LPA ($Q_{inc}$)')
    ax3.plot(df["batch_id"], df["modularity_batch"], marker='^', color='#f59e0b',
             linestyle='--', linewidth=2.2, label='Full Batch Global LPA ($Q_{batch}$)')
    ax3.set_title('(a) Newman-Girvan Modularity Conservation')
    ax3.set_xlabel('Micro-Batch Sequence Index')
    ax3.set_ylabel('Graph Modularity $Q$')
    ax3.legend(loc='lower right', frameon=True)
    ax3.grid(True, linestyle='--', alpha=0.6)

    ax4.plot(df["batch_id"], df["nmi_consistency"], marker='d', color='#7c3aed',
             linewidth=2.2, markersize=6, label='Normalized Mutual Info (NMI)')
    ax4.set_title('(b) Partition Fidelity vs Ground-Truth Batch Partition')
    ax4.set_xlabel('Micro-Batch Sequence Index')
    ax4.set_ylabel('NMI Agreement Score')
    ax4.set_ylim([0.0, 1.05])
    ax4.axhline(y=df["nmi_consistency"].mean(), color='#7c3aed', linestyle=':',
                label=f'Mean NMI ({df["nmi_consistency"].mean():.3f})')
    ax4.legend(loc='lower left', frameon=True)
    ax4.grid(True, linestyle='--', alpha=0.6)

    plt.tight_layout()
    fig2_path = os.path.join(output_dir, "quality_conservation.png")
    fig2.savefig(fig2_path, dpi=300)
    plt.close()
    print(f"[Publication Figure] Saved: {fig2_path}")


if __name__ == "__main__":
    generate_publication_figures()
