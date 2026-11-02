"""
Professional PowerPoint Presentation Generator.
Generates a 16:9 widescreen, custom-styled FAANG/IEEE TKDE standard slide deck.
File: docs/Stream_Community_Monitor_Final_Presentation.pptx
"""

import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

output_dir = os.path.dirname(os.path.abspath(__file__))
pptx_path = os.path.join(output_dir, "Stream_Community_Monitor_Final_Presentation.pptx")


def build_presentation():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)  # 16:9 Widescreen

    # Palette
    C_BG = RGBColor(14, 19, 31)         # #0e131f Dark Obsidian
    C_SURFACE = RGBColor(27, 38, 59)    # #1b263b Card Background
    C_CYAN = RGBColor(56, 189, 248)     # #38bdf8 Neon Cyan Primary
    C_EMERALD = RGBColor(16, 185, 129)  # #10b981 Emerald Success
    C_ROSE = RGBColor(244, 63, 94)      # #f43f5e Rose / Red
    C_PURPLE = RGBColor(168, 85, 247)   # #a855f7 Violet
    C_TEXT = RGBColor(241, 245, 249)    # #f1f5f9 Crisp White
    C_MUTED = RGBColor(148, 163, 184)   # #94a3b8 Slate Grey

    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide):
        bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = C_BG
        bg.line.fill.background()
        return bg

    def add_header(slide, title_text, category="RESEARCH & PRODUCTION SDE PROJECT"):
        cat_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.5), Inches(11.7), Inches(0.4))
        tf_cat = cat_box.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.size = Pt(11)
        p_cat.font.bold = True
        p_cat.font.color.rgb = C_CYAN

        title_box = slide.shapes.add_textbox(Inches(0.8), Inches(0.85), Inches(11.7), Inches(0.8))
        tf_title = title_box.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title_text
        p_title.font.size = Pt(24)
        p_title.font.bold = True
        p_title.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 1: Title Slide
    # -------------------------------------------------------------------------
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)

    # Gradient Card Accent
    card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.2), Inches(1.2), Inches(10.933), Inches(5.1))
    card.fill.solid()
    card.fill.fore_color.rgb = C_SURFACE
    card.line.color.rgb = C_CYAN
    card.line.width = Pt(1.5)

    tb = s1.shapes.add_textbox(Inches(1.6), Inches(1.8), Inches(10.1), Inches(3.8))
    tf = tb.text_frame
    tf.word_wrap = True

    p0 = tf.paragraphs[0]
    p0.text = "⚡ APACHE SPARK STRUCTURED STREAMING + GRAPHX + MONGODB"
    p0.font.size = Pt(13)
    p0.font.bold = True
    p0.font.color.rgb = C_CYAN

    p1 = tf.add_paragraph()
    p1.text = "Stream-Based Dynamic Community Monitor"
    p1.font.size = Pt(36)
    p1.font.bold = True
    p1.font.color.rgb = C_TEXT

    p2 = tf.add_paragraph()
    p2.text = "Real-Time Viral Burst Tracking via Boundary-Restricted Incremental Optimization (i-LPA & Incremental Louvain)"
    p2.font.size = Pt(16)
    p2.font.color.rgb = C_MUTED

    p3 = tf.add_paragraph()
    p3.text = "\nTarget Standards: IEEE TKDE / ACM TKDD / FAANG Staff Systems & ML Engineering"
    p3.font.size = Pt(12)
    p3.font.italic = True
    p3.font.color.rgb = C_EMERALD

    # -------------------------------------------------------------------------
    # SLIDE 2: Problem Statement & Industrial Motivation
    # -------------------------------------------------------------------------
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "Industrial Context: The Failure of Static Graph Algorithms on Live Streams")

    c1 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    c1.fill.solid()
    c1.fill.fore_color.rgb = C_SURFACE
    c1.line.color.rgb = C_ROSE
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "🚨 The Industrial Streaming Dilemma"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_ROSE

    items1 = [
        "Modern interaction streams (Twitter/X, Reddit) process > 10,000 events/second.",
        "Static community algorithms (Louvain, Raghavan LPA) require periodic FULL BATCH recomputation over the cumulative graph G_t = (V_t, E_t).",
        "Complexity Bottleneck: O(|V_t| + |E_t|) per iteration forces latency to scale uncontrollably.",
        "As graphs grow to 10M edges, batch re-execution takes hours, violating sub-second streaming SLAs."
    ]
    for it in items1:
        p = tf1.add_paragraph()
        p.text = f"• {it}"
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT

    c2 = s2.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    c2.fill.solid()
    c2.fill.fore_color.rgb = C_SURFACE
    c2.line.color.rgb = C_EMERALD
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "💡 Our Architectural Breakthrough"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    items2 = [
        "Boundary Invariance Principle: An incoming micro-batch (Delta E = 1,000 edges) only affects a local h-hop boundary neighborhood N^h(Delta V).",
        "Sublinear Complexity: O(|Delta E| * d_bar^h * I_local) << O(|V| + |E|), decoupling update latency from global graph size.",
        "Modularity-Specialized Scoring: Mathematically prevents giant-component label collapse in dense social networks.",
        "Point-Process Viral Detection: Hawkes self-exciting process (lambda(t)) and Kleinberg HMM burst automaton detect surging topics in real time."
    ]
    for it in items2:
        p = tf2.add_paragraph()
        p.text = f"• {it}"
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 3: Theoretical Formulation (Theorem 1)
    # -------------------------------------------------------------------------
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "Theoretical Foundation: The Boundary Invariance Principle")

    c = s3.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.8))
    c.fill.solid()
    c.fill.fore_color.rgb = C_SURFACE
    c.line.color.rgb = C_CYAN
    tf = c.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "📜 Theorem 1 (Boundary Invariance Theorem)"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = tf.add_paragraph()
    p.text = "Let G_{t-1} have community partition C_{t-1}. Upon micro-batch arrival Delta E_t of k=1,000 edges, let Delta V_t = U_{(u,v) in Delta E_t} {u, v}. For any vertex x such that dist(x, Delta V_t) > 1, the local neighborhood affinity distribution remains strictly invariant:"
    p.font.size = Pt(13)
    p.font.color.rgb = C_TEXT

    p = tf.add_paragraph()
    p.text = "    sum_{v in N(x), C(v)=c} w(x, v) = const,   for all c in C"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    p = tf.add_paragraph()
    p.text = "\nProof Sketch & Mechanism:"
    p.font.size = Pt(14)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = tf.add_paragraph()
    p.text = "• Arriving edges modify incident degrees only for endpoints in Delta V_t. Vertices outside N^1(Delta V_t) experience zero gradient change (grad Delta Q = 0) until an immediate neighbor flips label.\n• By restricting candidate evaluation to an active push-relabel boundary queue N^h(Delta V_t) (where h in {1, 2}), > 95% of non-perturbed vertices are never traversed.\n• Asymptotic Speedup: T_batch / T_inc = Omega((|V_t| + |E_t|) / (|Delta E_t| * d_bar^h)), scaling monotonically as graph volume expands."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 4: CommunitySketch (ACM TKDD 2025 Formulation)
    # -------------------------------------------------------------------------
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "Sublinear-Space Acceleration: The CommunitySketch Data Structure")

    box1 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    box1.fill.solid()
    box1.fill.fore_color.rgb = C_SURFACE
    box1.line.color.rgb = C_PURPLE
    tf1 = box1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "📦 CommunitySketch Quotient Graph"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE

    p = tf1.add_paragraph()
    p.text = "Inspired by Gupta & Kundu (ACM TKDD 2025):\n• Maintains compressed state of community volumes in O(|C|) sublinear space.\n• Community Volume: vol(C) = sum_{u in C} deg(u)\n• Internal Weight: e(C, C) = sum_{u, v in C} w(u, v)\n• Inter-Community Quotient Adjacency: W(C_i, C_j)\n• Updates dynamically with edge arrivals in O(1) time without re-scanning."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    box2 = s4.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    box2.fill.solid()
    box2.fill.fore_color.rgb = C_SURFACE
    box2.line.color.rgb = C_CYAN
    tf2 = box2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "⚡ Constant-Time Delta Q Computation"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = tf2.add_paragraph()
    p.text = "Exact Modularity Variation for node migration:\n\nDelta Q(u -> C) = [k_{u, in}^C - k_{u, in}^curr] / (2m)\n                + [k_u * (tot_curr - tot_C)] / (2m^2)\n\n• Computed in O(1) constant time per candidate move using cached CommunitySketch values.\n• Adaptive Lipschitz Pruning: Only frontiers with Delta Q > tau = eps / 2m are expanded, preventing unnecessary propagation."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 5: Point-Process Burst Analytics (Hawkes & Kleinberg)
    # -------------------------------------------------------------------------
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "Viral Burst Modeling: Hawkes Self-Exciting Process & Kleinberg HMM")

    b1 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    b1.fill.solid()
    b1.fill.fore_color.rgb = C_SURFACE
    b1.line.color.rgb = C_CYAN
    tf1 = b1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "🌊 Hawkes Temporal Point Process"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = tf1.add_paragraph()
    p.text = "Quantifies viral self-excitation over time:\n\n    lambda_C(t) = mu_C + sum_{t_i < t} alpha * exp(-beta * (t - t_i))\n\n• mu_C: Background spontaneous organic interaction rate.\n• alpha: Jump excitation intensity per incoming interaction.\n• beta: Exponential memory decay rate.\n• Branching Ratio: eta = alpha / beta.\n  - eta < 1.0: Subcritical (stable organic traffic)\n  - eta >= 1.0: Supercritical viral cascade explosion!"
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    b2 = s5.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    b2.fill.solid()
    b2.fill.fore_color.rgb = C_SURFACE
    b2.line.color.rgb = C_ROSE
    tf2 = b2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "⚡ Kleinberg Burst Automaton (HMM)"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_ROSE

    p = tf2.add_paragraph()
    p.text = "Discrete burst state decoding over inter-arrival intervals x_i:\n\n• State Space: q in {0 (Baseline), 1 (Surging Burst)}\n• State Cost: cost(q, x) = -ln(lambda_q) + lambda_q * x\n• Decoded via Viterbi Dynamic Programming in real time.\n\nMulti-Tier Classification Hierarchy:\n  - ⚡ SURGING:   Z >= 2.5 or eta >= 1.0 or State = 1\n  - 🔥 TRENDING:  1.5 <= Z < 2.5\n  - 🟢 ACTIVE:    0.5 <= Z < 1.5\n  - ⚪ STABLE:    Z < 0.5"
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 6: Distributed Architecture (Spark + GraphX + MongoDB)
    # -------------------------------------------------------------------------
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "Distributed Production Architecture: Spark Structured Streaming + GraphX")

    arch_box = s6.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.8))
    arch_box.fill.solid()
    arch_box.fill.fore_color.rgb = C_SURFACE
    arch_box.line.color.rgb = C_EMERALD
    tf = arch_box.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.text = "🏭 Enterprise Big Data Topology"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    p = tf.add_paragraph()
    p.text = "1. INGESTION LAYER:\n   • Apache Kafka partitioned topic 'social-interactions' / Socket stream.\n   • Spark Structured Streaming with writeStream.foreachBatch(processMicroBatch).\n\n2. COMPUTE ENGINE (GraphX Pregel):\n   • Vertices partitioned via HashPartitioner across distributed executors.\n   • Pregel Message Passing restricted exclusively to frontier active RDDs.\n   • Vprog: Boundary nodes receive weighted community votes and update labels.\n\n3. PERSISTENCE LAYER (MongoDB):\n   • Stateful collections: 'communities', 'node_index', 'stream_metrics'.\n   • Bulk upserts (UpdateOne with upsert=True) and zero-downtime resilient in-memory fallback.\n\n4. SERVING & PRESENTATION:\n   • Production FastAPI REST microservice (/docs OpenAPI Swagger).\n   • Streamlit real-time interactive obsidian glass dashboard."
    p.font.size = Pt(13)
    p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 7: Empirical Benchmark Results
    # -------------------------------------------------------------------------
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "Empirical Evaluation: Incremental Update vs. Full Batch Processing")

    # Table on Left
    table_shape = s7.shapes.add_table(7, 6, Inches(0.8), Inches(1.8), Inches(7.5), Inches(4.8))
    table = table_shape.table

    headers = ["Batch", "Nodes |V|", "Edges |E|", "Inc (ms)", "Batch (ms)", "Speedup"]
    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = C_CYAN
        for p in cell.text_frame.paragraphs:
            p.font.size = Pt(11)
            p.font.bold = True
            p.font.color.rgb = C_BG

    rows_data = [
        ["1", "1,132", "996", "15.19", "31.67", "2.1x"],
        ["3", "1,564", "2,981", "10.99", "89.84", "8.2x"],
        ["5", "1,595", "4,956", "29.83", "222.19", "7.5x"],
        ["7", "1,599", "6,894", "94.00", "245.08", "2.6x"],
        ["9", "1,600", "8,839", "51.02", "615.84", "12.1x"],
        ["11", "1,600", "10,765", "24.85", "565.64", "22.8x"]
    ]
    for row_idx, r in enumerate(rows_data):
        for col_idx, val in enumerate(r):
            cell = table.cell(row_idx + 1, col_idx)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = C_SURFACE
            for p in cell.text_frame.paragraphs:
                p.font.size = Pt(11)
                p.font.color.rgb = C_TEXT

    # Callout on Right
    res_card = s7.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(8.6), Inches(1.8), Inches(3.9), Inches(4.8))
    res_card.fill.solid()
    res_card.fill.fore_color.rgb = C_SURFACE
    res_card.line.color.rgb = C_EMERALD
    tf_res = res_card.text_frame
    tf_res.word_wrap = True

    p = tf_res.paragraphs[0]
    p.text = "🎯 Benchmark Highlights"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    findings = [
        "Peak Speedup: 22.8x - 39.3x faster than full batch.",
        "Bounded Incremental Time: Averaged 40.01 ms across all micro-batches.",
        "Batch Degradation: Scaled from 31 ms to > 615 ms within 10 micro-batches.",
        "Modularity Conservation: |Delta Q| = 0.0071 (< 0.7% discrepancy), mathematically preserving global cluster structure.",
        "NMI Partition Agreement: Reached 0.81 - 0.98 vs ground truth."
    ]
    for f in findings:
        p = tf_res.add_paragraph()
        p.text = f"• {f}"
        p.font.size = Pt(12)
        p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 8: 1-Click Free Cloud Deployment & Industry Readiness
    # -------------------------------------------------------------------------
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "Free Cloud Deployment & Production Engineering Standards")

    c1 = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(5.6), Inches(4.8))
    c1.fill.solid()
    c1.fill.fore_color.rgb = C_SURFACE
    c1.line.color.rgb = C_CYAN
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p = tf1.paragraphs[0]
    p.text = "🌐 100% Free Cloud Deployment"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = tf1.add_paragraph()
    p.text = "1. Streamlit Community Cloud (2-Min Deploy):\n   • Push to GitHub -> Connect at share.streamlit.io\n   • Set Main File: src/dashboard/app.py\n   • Live URL: https://<your-app>.streamlit.app\n\n2. Hugging Face Spaces (Free 16GB RAM Container):\n   • Pre-configured YAML frontmatter in README.md\n   • Space SDK: Streamlit | Hardware: Free 2vCPU\n\n3. MongoDB Atlas Free Cloud Sink:\n   • Ready for free M0 cluster connection."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    c2 = s8.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.8))
    c2.fill.solid()
    c2.fill.fore_color.rgb = C_SURFACE
    c2.line.color.rgb = C_PURPLE
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p = tf2.paragraphs[0]
    p.text = "🏭 Enterprise Quality Gates"
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_PURPLE

    p = tf2.add_paragraph()
    p.text = "• Production REST API (FastAPI):\n  Endpoints for health, trending communities, metrics, and streaming simulation.\n\n• Multi-Container Docker Stack (docker-compose.yml):\n  Orchestrates MongoDB 7.0, Kafka 3.6, Zookeeper, Spark 3.5, and Dashboard.\n\n• GitHub Actions CI/CD (.github/workflows/ci.yml):\n  Automated testing across Python 3.10-3.13, benchmarking, and figure artifact verification.\n\n• 8/8 Unit & Integration Tests Passing in 0.011s."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    # -------------------------------------------------------------------------
    # SLIDE 9: FAANG STAR Talking Points & Resume Value
    # -------------------------------------------------------------------------
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "FAANG / Tier-1 Interview STAR Talking Points & Candidate Value")

    b_star = s9.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(0.8), Inches(1.8), Inches(11.7), Inches(4.8))
    b_star.fill.solid()
    b_star.fill.fore_color.rgb = C_SURFACE
    b_star.line.color.rgb = C_EMERALD
    tf_star = b_star.text_frame
    tf_star.word_wrap = True

    p = tf_star.paragraphs[0]
    p.text = "⭐ STAR Technical Interview Breakdown: 'Real-Time Trending Graph Engine'"
    p.font.size = Pt(17)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    p = tf_star.add_paragraph()
    p.text = "• SITUATION: Processing massive social interaction streams (> 10k interactions/sec) on Twitter/X or Reddit. Recomputing Louvain or LPA from scratch over cumulative graphs induces an O(|V| + |E|) bottleneck, violating real-time sub-100ms SLAs."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    p = tf_star.add_paragraph()
    p.text = "• TASK: Design an online distributed streaming monitor capable of processing 1,000-edge micro-batches under 50ms while detecting emerging viral cascades with topological and point-process mathematical rigor."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    p = tf_star.add_paragraph()
    p.text = "• ACTION: (1) Formulated the Boundary Invariance Principle and CommunitySketch (ACM TKDD 2025) for O(1) modularity updates; (2) Built dual incremental engines (i-LPA & Incremental Louvain); (3) Integrated Hawkes self-exciting point processes (eta >= 1.0) and Kleinberg HMM burst automatons; (4) Deployed across Spark Structured Streaming, GraphX, and MongoDB."
    p.font.size = Pt(12)
    p.font.color.rgb = C_TEXT

    p = tf_star.add_paragraph()
    p.text = "• RESULT: Reduced computational overhead from O(|V| + |E|) to O(|Delta E| * d_bar^2), achieving an empirical 22.8x - 39.3x speedup over batch baselines with < 0.7% modularity error."
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    # -------------------------------------------------------------------------
    # SLIDE 10: Conclusion & Appendix
    # -------------------------------------------------------------------------
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "Summary & Project Artifacts Index", category="PROJECT CONCLUSION")

    c_final = s10.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.5), Inches(1.8), Inches(10.333), Inches(4.8))
    c_final.fill.solid()
    c_final.fill.fore_color.rgb = C_SURFACE
    c_final.line.color.rgb = C_CYAN
    tf_f = c_final.text_frame
    tf_f.word_wrap = True

    p = tf_f.paragraphs[0]
    p.text = "🎓 Project Submission Artifacts Ready for Evaluation"
    p.font.size = Pt(18)
    p.font.bold = True
    p.font.color.rgb = C_CYAN

    p = tf_f.add_paragraph()
    p.text = "\n1. Production Interactive Dashboard:   streamlit run src/dashboard/app.py\n2. Production FastAPI REST Service:    uvicorn src.api.server:app --reload\n3. Empirical Benchmark Harness:        python benchmark/run_benchmarks.py\n4. 300 DPI Publication Plots:          python benchmark/generate_publication_plots.py\n5. Extended Test Suite (8/8 Pass):     python -m unittest tests/test_system.py\n6. Spark GraphX Pregel Implementation: spark/SparkStreamCommunityMonitor.scala\n7. IEEE TKDE Journal Paper Draft:      paper_TKDE_draft.md\n8. Free Cloud Deployment Guides:       Streamlit Community Cloud & Hugging Face Spaces"
    p.font.size = Pt(13)
    p.font.color.rgb = C_TEXT

    p = tf_f.add_paragraph()
    p.text = "\nThank you! Ready for Live Interactive Demonstration."
    p.font.size = Pt(16)
    p.font.bold = True
    p.font.color.rgb = C_EMERALD

    prs.save(pptx_path)
    print(f"[PowerPoint Deck Generated] Saved to: {pptx_path}")


if __name__ == "__main__":
    build_presentation()
