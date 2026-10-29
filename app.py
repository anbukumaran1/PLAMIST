# Reactive hacker-aesthetic Streamlit demo UI for PALIMPSEST neurosymbolic CEGIS loop.
import ast
import os
import random
import sys
import streamlit as st

# Append training directory to system path for clean imports.
sys.path.append(os.path.join(os.path.dirname(__file__), "training"))

# Import zero-trust AST slicer and compiled LangGraph CEGIS state machine.
from ast_slicer import count_nodes
from langgraph_orchestrator import CEGISState, app as cegis_graph
from mba_mutator import MBAMutator, parse_to_ir, SEEDS
from z3_verifier import verify_equivalence

# Configure wide layout with cybersecurity-themed title and icon.
st.set_page_config(layout="wide", page_title="PALIMPSEST | VEX-MORPH Workstation", page_icon="🛡️")

# Custom CSS injecting polished cybersecurity reverse-engineering aesthetic.
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600;700;800&display=swap');

    .stApp {
        background-color: #05080f;
        color: #e2e8f0;
        font-family: 'JetBrains Mono', monospace;
        background-image: radial-gradient(rgba(14, 165, 233, 0.04) 1px, transparent 1px);
        background-size: 24px 24px;
    }
    h1, h2, h3, h4, h5 {
        color: #38bdf8 !important;
        font-family: 'JetBrains Mono', monospace;
        letter-spacing: -0.5px;
    }
    .metric-card {
        background: #090e17;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        transition: border-color 0.2s ease-in-out;
    }
    .metric-card:hover {
        border-color: #38bdf8;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #94a3b8;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        margin-bottom: 6px;
    }
    .metric-value {
        font-size: 1.65rem;
        font-weight: 800;
        color: #38bdf8;
    }
    .stTextArea textarea {
        background-color: #080d1a !important;
        color: #38bdf8 !important;
        font-family: 'JetBrains Mono', monospace !important;
        border: 1px solid #1e293b !important;
        border-radius: 8px !important;
        font-size: 0.92rem !important;
        line-height: 1.5 !important;
    }
    .stTextArea textarea:focus {
        border-color: #0ea5e9 !important;
        box-shadow: 0 0 15px rgba(14, 165, 233, 0.25) !important;
    }
    .generator-btn>button {
        background-color: #0c1322 !important;
        color: #38bdf8 !important;
        border: 1px solid #1e293b !important;
        border-radius: 6px !important;
        font-family: 'JetBrains Mono', monospace !important;
        font-size: 0.8rem !important;
        font-weight: 600 !important;
        padding: 0.45rem 0.6rem !important;
        transition: all 0.2s ease-in-out !important;
    }
    .generator-btn>button:hover {
        background-color: #111d33 !important;
        border-color: #38bdf8 !important;
        color: #ffffff !important;
        box-shadow: 0 0 12px rgba(56, 189, 248, 0.3) !important;
        transform: translateY(-1px) !important;
    }
    .execute-btn>button {
        background: linear-gradient(135deg, #0284c7 0%, #059669 100%) !important;
        color: #ffffff !important;
        font-weight: 800 !important;
        font-size: 1.05rem !important;
        letter-spacing: 0.6px !important;
        border: none !important;
        border-radius: 8px !important;
        padding: 0.75rem 1.5rem !important;
        box-shadow: 0 4px 18px rgba(2, 132, 199, 0.45) !important;
        transition: all 0.2s ease-in-out !important;
    }
    .execute-btn>button:hover {
        background: linear-gradient(135deg, #0369a1 0%, #047857 100%) !important;
        box-shadow: 0 6px 24px rgba(2, 132, 199, 0.65) !important;
        transform: translateY(-1px) !important;
    }
    .status-badge {
        display: inline-block;
        padding: 4px 10px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 700;
        letter-spacing: 0.08em;
        text-transform: uppercase;
    }
    .badge-verified {
        background: rgba(16, 185, 129, 0.15);
        color: #34d399;
        border: 1px solid #059669;
    }
    .badge-sat {
        background: rgba(239, 68, 68, 0.15);
        color: #f87171;
        border: 1px solid #dc2626;
    }
    .badge-info {
        background: rgba(56, 189, 248, 0.15);
        color: #38bdf8;
        border: 1px solid #0284c7;
    }
    .badge-gold {
        background: rgba(245, 158, 11, 0.15);
        color: #fbbf24;
        border: 1px solid #d97706;
    }
    .cyber-panel {
        background: #090e17;
        border: 1px solid #1e293b;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 20px;
    }
    .reasoning-box {
        background: #060911;
        border-left: 3px solid #38bdf8;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        color: #94a3b8;
        font-size: 0.82rem;
        line-height: 1.5;
        margin-top: 8px;
        margin-bottom: 8px;
    }
    .feedback-box-sat {
        background: #130a0d;
        border-left: 3px solid #ef4444;
        padding: 10px 14px;
        border-radius: 0 6px 6px 0;
        color: #fca5a5;
        font-size: 0.82rem;
        line-height: 1.5;
        margin-top: 8px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Default complex MBA test expression.
DEFAULT_OBFUSCATED_MBA = (
    "((((x) ^ (y))) + (((((2) * (((x) & (y))))) + "
    "(((0xca70da7a) * (((((((x) | (x))) - (((x) ^ (x))))) - (((x) & (x))))))))))"
)

# Initialize session state variables.
if "mba_code_input" not in st.session_state:
    st.session_state["mba_code_input"] = DEFAULT_OBFUSCATED_MBA
if "target_seed" not in st.session_state:
    st.session_state["target_seed"] = "x + y"
if "gen_banner" not in st.session_state:
    st.session_state["gen_banner"] = ""

# Callback function to dynamically generate and inject random scrambled MBA expressions.
def generate_and_set_code(tier: int, register_only: bool = False, constant_heavy: bool = False, clear: bool = False):
    if clear:
        st.session_state["mba_code_input"] = ""
        st.session_state["target_seed"] = ""
        st.session_state["gen_banner"] = "Input buffer cleared."
        return

    mutator = MBAMutator()
    if constant_heavy:
        seed = random.choice([
            "rax + 0x1000",
            "rbx - 0x20",
            "rcx ^ 0x5555",
            "rdx & 0x7fff",
            "rsi | 0x1234",
            "(rax + 0x100) ^ 0x20",
        ])
        ir = parse_to_ir(seed)
        unfolded = mutator.unfold_constants(ir)
        obf = mutator.inject_opaque_zeros(unfolded)
        obf_str = obf.to_string()
        st.session_state["mba_code_input"] = obf_str
        st.session_state["target_seed"] = seed
        nodes = count_nodes(obf_str)
        st.session_state["gen_banner"] = f"⚡ Synthesized Constant-Heavy Expression (Target: '{seed}', {nodes} AST Nodes)"
    elif register_only:
        reg_seeds = [s for s in SEEDS if any(r in s for r in ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9"])]
        seed = random.choice(reg_seeds)
        res = mutator.mutate(seed=seed, tier=tier)
        obf_str = res["obfuscated_expr"]
        st.session_state["mba_code_input"] = obf_str
        st.session_state["target_seed"] = seed
        nodes = count_nodes(obf_str)
        st.session_state["gen_banner"] = f"⚡ Synthesized x86-64 Register MBA (Target: '{seed}', Tier {tier}, {nodes} AST Nodes)"
    else:
        res = mutator.mutate(tier=tier)
        obf_str = res["obfuscated_expr"]
        seed = res["canonical_seed"]
        st.session_state["mba_code_input"] = obf_str
        st.session_state["target_seed"] = seed
        nodes = count_nodes(obf_str)
        st.session_state["gen_banner"] = f"⚡ Synthesized Tier {tier} Expression (Target: '{seed}', {nodes} AST Nodes)"

# Sidebar configuration and engine diagnostics.
with st.sidebar:
    st.markdown("### ⚙️ Engine Settings")
    max_hops = st.slider("Max CEGIS Iterations", min_value=1, max_value=20, value=10, step=1)
    st.markdown("---")
    st.markdown("### 📡 System Diagnostics")
    st.markdown(
        """
        <div style="font-size: 0.85rem; line-height: 1.9;">
            <div>🟢 <strong>Model:</strong> <code>palimpsest_qwen</code></div>
            <div>🟢 <strong>Prover:</strong> <code>Z3 QF_BV Miter (64-Bit)</code></div>
            <div>🟢 <strong>Orchestration:</strong> <code>LangGraph CEGIS</code></div>
            <div>🟢 <strong>Quantization:</strong> <code>Q4_K_M GGUF</code></div>
            <div>🟢 <strong>Differential Fuzz:</strong> <code>64-Bit Random Invariance</code></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("---")
    st.markdown("### 🛡️ About PALIMPSEST")
    st.markdown(
        """
        <div style="font-size: 0.8rem; color: #94a3b8; line-height: 1.6;">
        PALIMPSEST couples local generative reasoning (fine-tuned Qwen-2.5-Coder-3B) with zero-trust formal methods (Z3 Theorem Prover).
        Every candidate expression is evaluated in a 64-bit BitVec Miter circuit. If an algebraic discrepancy exists, Z3 returns a concrete counterexample witness, guiding the model to convergence.
        </div>
        """,
        unsafe_allow_html=True,
    )

# Render main header with cybersecurity badge pills.
st.title("🛡️ PALIMPSEST: VEX-MORPH")
st.markdown(
    """
    <div style="margin-bottom: 22px;">
        <span class="status-badge badge-info">Qwen-2.5-Coder-3B QLoRA</span>
        <span class="status-badge badge-verified">Formal Z3 QF_BV Prover</span>
        <span class="status-badge badge-gold">Neurosymbolic CEGIS Loop</span>
        <span class="status-badge badge-verified">Air-Gapped & Local</span>
    </div>
    """,
    unsafe_allow_html=True,
)

# Section 1: Random Scrambled MBA Code Generator Toolbar.
st.markdown("#### ⚡ Random Scrambled MBA Code Generator")
st.caption("Click any button below to dynamically synthesize fresh, mathematically verified 64-bit scrambled MBA expressions on demand:")

# Render generator action buttons across columns.
g_col1, g_col2, g_col3, g_col4, g_col5, g_col6 = st.columns([1.1, 1.1, 1.1, 1.3, 1.3, 0.7])

with g_col1:
    st.markdown('<div class="generator-btn">', unsafe_allow_html=True)
    st.button("🎲 Tier 1 (Linear)", on_click=generate_and_set_code, args=(1,), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with g_col2:
    st.markdown('<div class="generator-btn">', unsafe_allow_html=True)
    st.button("🎲 Tier 2 (Multi-Hop)", on_click=generate_and_set_code, args=(2,), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with g_col3:
    st.markdown('<div class="generator-btn">', unsafe_allow_html=True)
    st.button("🎲 Tier 3 (Deep Logic)", on_click=generate_and_set_code, args=(3,), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with g_col4:
    st.markdown('<div class="generator-btn">', unsafe_allow_html=True)
    st.button("🎲 x86-64 Register MBA", on_click=generate_and_set_code, args=(2, True), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with g_col5:
    st.markdown('<div class="generator-btn">', unsafe_allow_html=True)
    st.button("🎲 Constant Unfolding", on_click=generate_and_set_code, args=(2, False, True), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

with g_col6:
    st.markdown('<div class="generator-btn">', unsafe_allow_html=True)
    st.button("🧹 Clear", on_click=generate_and_set_code, args=(0, False, False, True), use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

# Display generator feedback message if present.
if st.session_state.get("gen_banner"):
    st.markdown(
        f"""
        <div style="background: rgba(14, 165, 233, 0.08); border: 1px solid #0284c7; border-radius: 6px; padding: 6px 12px; margin-top: 10px; font-size: 0.82rem; color: #7dd3fc;">
            {st.session_state['gen_banner']}
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

# Section 2: Input Expression and Live AST Slicer Diagnostics.
input_val = st.session_state.get("mba_code_input", "")

# Compute live AST node count and validation status.
detected_nodes = 0
syntax_valid = False
syntax_msg = ""
try:
    if input_val.strip():
        detected_nodes = count_nodes(input_val.strip())
        syntax_valid = True
        syntax_msg = f"{detected_nodes} AST Nodes (Valid ZeroTrustAST Whitelist)"
    else:
        syntax_msg = "Awaiting input expression..."
except Exception as e:
    syntax_msg = f"Syntax or Whitelist Discrepancy: {str(e)}"

# Live AST status indicator bar above text area.
ast_col1, ast_col2 = st.columns([2, 1])
with ast_col1:
    st.markdown("##### 📝 64-Bit Scrambled MBA Expression Input:")
with ast_col2:
    if syntax_valid:
        st.markdown(f"<div style='text-align: right;'><span class='status-badge badge-verified'>✓ {syntax_msg}</span></div>", unsafe_allow_html=True)
    elif input_val.strip():
        st.markdown(f"<div style='text-align: right;'><span class='status-badge badge-sat'>⚠ {syntax_msg}</span></div>", unsafe_allow_html=True)

# Text area for user input expression.
user_input = st.text_area(
    "Scrambled MBA Input Area",
    key="mba_code_input",
    height=140,
    label_visibility="collapsed",
)

# Execute CEGIS button.
st.markdown('<div class="execute-btn">', unsafe_allow_html=True)
execute_clicked = st.button("🚀 DE-OBFUSCATE & FORMALLY VERIFY (NEUROSYMBOLIC CEGIS)", use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# Process execution when button is clicked.
if execute_clicked:
    active_expr = user_input.strip()
    if not active_expr:
        st.warning("Please provide a valid mathematical expression.")
    else:
        # Execute CEGIS state graph with interactive spinner.
        with st.spinner(f"⚡ Proving Equivalence via Qwen-2.5-Coder-3B & Z3 Miter Circuit (Max {max_hops} Hops)..."):
            initial_state: CEGISState = {
                "original_expr": active_expr,
                "current_expr": "",
                "iterations": 0,
                "status": "PENDING",
                "messages": [],
                "max_iterations": max_hops,
            }
            final_state = cegis_graph.invoke(initial_state)

        # Calculate AST node metrics.
        try:
            original_nodes = count_nodes(active_expr)
        except Exception:
            original_nodes = 1

        try:
            final_nodes = count_nodes(final_state["current_expr"])
        except Exception:
            final_nodes = 1

        # Calculate compression ratio.
        compression_ratio = max(0.0, (1.0 - (final_nodes / original_nodes)) * 100.0) if original_nodes > 0 else 0.0
        latency = final_state.get("verification_latency_ms", 0.0)

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # Verification status banner.
        if final_state["status"] == "VERIFIED":
            st.markdown(
                """
                <div style="background: rgba(16, 185, 129, 0.12); border: 1px solid #10b981; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <div style="color: #34d399; font-weight: 700; font-size: 1.15rem;">
                        ✅ FORMALLY VERIFIED: EQUIVALENCE CERTIFIED
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.88rem; margin-top: 4px;">
                        The candidate expression is <strong>mathematically proven identical</strong> to the obfuscated input across all 64-bit bit-vector evaluations.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f"""
                <div style="background: rgba(239, 68, 68, 0.12); border: 1px solid #ef4444; border-radius: 8px; padding: 16px; margin-bottom: 20px;">
                    <div style="color: #f87171; font-weight: 700; font-size: 1.15rem;">
                        ❌ VERIFICATION INCONCLUSIVE / EXHAUSTED ({final_state['status']})
                    </div>
                    <div style="color: #cbd5e1; font-size: 0.88rem; margin-top: 4px;">
                        CEGIS loop reached maximum iteration budget ({max_hops} hops) without complete UNSAT convergence.
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Render 4 metrics cards.
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        with m_col1:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">AST Compression</div>
                    <div class="metric-value" style="color: #34d399;">{compression_ratio:.1f}%</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col2:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Node Reduction</div>
                    <div class="metric-value">{original_nodes} → {final_nodes}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col3:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">CEGIS Hops</div>
                    <div class="metric-value">{final_state['iterations']} / {max_hops}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        with m_col4:
            st.markdown(
                f"""
                <div class="metric-card">
                    <div class="metric-label">Z3 Proof Latency</div>
                    <div class="metric-value" style="color: #38bdf8;">{latency:.2f} ms</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='margin-top: 25px;'></div>", unsafe_allow_html=True)

        # Target comparison card if generated from known seed.
        target_seed = st.session_state.get("target_seed")
        if target_seed and final_state["status"] == "VERIFIED":
            seed_match = target_seed.replace(" ", "") == final_state["current_expr"].replace(" ", "")
            match_badge = "✅ 100% CANONICAL MATCH" if seed_match else "✓ FORMALLY EQUIVALENT"
            badge_class = "badge-verified" if seed_match else "badge-info"
            st.markdown(
                f"""
                <div class="cyber-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <span style="font-size: 0.85rem; color: #94a3b8; font-weight: 700;">GROUND TRUTH TARGET VERIFICATION</span>
                        <span class="status-badge {badge_class}">{match_badge}</span>
                    </div>
                    <div style="font-size: 0.88rem; color: #cbd5e1;">
                        Target Canonical Seed: <code style="color: #38bdf8; font-size: 0.95rem;">{target_seed}</code>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        # Simplified canonical expression card.
        st.markdown("### 🎯 De-obfuscated Canonical Expression:")
        st.code(final_state["current_expr"], language="python")

        # Hop-by-Hop Neurosymbolic Execution Trace Expander.
        with st.expander("🔬 Neurosymbolic CEGIS Hop-by-Hop Proof Trace", expanded=True):
            st.markdown("#### Execution Timeline:")
            messages = final_state.get("messages", [])
            hop_counter = 1
            for idx, msg in enumerate(messages):
                if "Z3_VERIFICATION_FAILED" in msg:
                    st.markdown(
                        f"""
                        <div style="background: #15090d; border: 1px solid #7f1d1d; border-radius: 6px; padding: 14px; margin-bottom: 14px;">
                            <span class="status-badge badge-sat">Hop {hop_counter} Formal Feedback: Counterexample Witness</span>
                            <div class="feedback-box-sat">{msg}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    hop_counter += 1
                else:
                    # Clean message and isolate think block if present.
                    clean_display = msg
                    think_block = ""
                    import re
                    think_match = re.search(r"<think>([\s\S]*?)</think>", msg)
                    if think_match:
                        think_block = think_match.group(1).strip()
                        clean_display = re.sub(r"<think>[\s\S]*?</think>", "", msg).strip()

                    st.markdown(
                        f"""
                        <div style="background: #090e17; border: 1px solid #1e293b; border-radius: 6px; padding: 14px; margin-bottom: 14px;">
                            <span class="status-badge badge-info">Hop {hop_counter} LLM Hypothesis & Reasoning</span>
                            {f'<div class="reasoning-box"><strong>CoT Reasoning:</strong><br>{think_block}</div>' if think_block else ''}
                            <div style="color: #38bdf8; margin-top: 8px; font-weight: 600;">Proposed Candidate: <code>{clean_display}</code></div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

            if final_state["status"] == "VERIFIED":
                st.markdown(
                    f"""
                    <div style="background: #051912; border: 1px solid #059669; border-radius: 6px; padding: 14px; margin-top: 10px;">
                        <span class="status-badge badge-verified">Formal Theorem Proof Complete: UNSAT</span>
                        <div style="color: #6ee7b7; margin-top: 8px; font-size: 0.9rem;">
                            Prover verified negation circuit (seed != candidate) is UNSAT in {latency:.3f} ms. 64-bit mathematical equivalence certified.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
