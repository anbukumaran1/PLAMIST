# Reactive hacker-aesthetic Streamlit demo UI for PALIMPSEST neurosymbolic CEGIS loop.
import ast
import os
import sys
import streamlit as st

# Append training directory to system path for clean imports.
sys.path.append(os.path.join(os.path.dirname(__file__), "training"))

# Import compiled LangGraph CEGIS state machine and state definition.
from langgraph_orchestrator import CEGISState, app as cegis_graph

# Configure wide layout with cybersecurity-themed title and icon.
st.set_page_config(layout="wide", page_title="PALIMPSEST | VEX-MORPH", page_icon="🛡️")

# Custom CSS injecting terminal hacker aesthetic.
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'JetBrains Mono', 'Courier New', monospace;
    }
    h1, h2, h3 {
        color: #58a6ff !important;
        font-family: 'JetBrains Mono', monospace;
    }
    .stTextArea textarea {
        background-color: #161b22;
        color: #39d353;
        font-family: 'JetBrains Mono', monospace;
        border: 1px solid #30363d;
        font-size: 0.95rem;
    }
    .stButton>button {
        background-color: #238636;
        color: #ffffff;
        font-weight: bold;
        border: none;
        border-radius: 6px;
        padding: 0.5rem 1.5rem;
    }
    .stButton>button:hover {
        background-color: #2ea043;
        color: #ffffff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# Preset library of representative scrambled MBA expressions.
PRESETS = {
    "Linear MBA + Opaque Zero (x + y)": (
        "((((x) ^ (y))) + (((((2) * (((x) & (y))))) + "
        "(((0xca70da7a) * (((((((x) | (x))) - (((x) ^ (x))))) - (((x) & (x))))))))))"
    ),
    "x86-64 Register MBA (rax - rbx)": (
        "(((rax ^ rbx) - (2 * ((~rax) & rbx))) + (0x41cfde29 * ((rax & (~rax)) * rax)))"
    ),
    "Tier 3 Shift & Logic MBA ((rax << 1) + rbx)": (
        "((((rax << 1) ^ rbx) + (2 * ((rax << 1) & rbx))) + "
        "(16 * (((rax | rax) - (rax ^ rax)) - (rax & rax))))"
    ),
    "Constant-Heavy Immediate Folding (rsi | 0x1234)": (
        "(rsi | ((((0x1234 ^ 0x55aa) + (2 * (0x1234 & 0x55aa))) + "
        "(16 * (((rsi | rsi) - (rsi ^ rsi)) - (rsi & rsi)))) - 0x55aa))"
    ),
}

# Sidebar configuration and engine diagnostics.
with st.sidebar:
    st.header("⚙️ CEGIS Engine Config")
    max_hops = st.slider("Max CEGIS Iterations", min_value=1, max_value=20, value=10, step=1)
    st.markdown("---")
    st.subheader("📡 System Architecture")
    st.markdown("- **Model**: `palimpsest_qwen` (Qwen-2.5-Coder-3B QLoRA)")
    st.markdown("- **Prover**: Z3 QF_BV Miter Circuit (64-bit BitVec)")
    st.markdown("- **Framework**: LangGraph Multi-Hop CEGIS Loop")
    st.markdown("---")
    st.subheader("🧪 Scrambled MBA Presets")
    for label, expr in PRESETS.items():
        if st.button(label, use_container_width=True):
            st.session_state["user_input_expr"] = expr

# Initialize session state for text input if not already present.
if "user_input_expr" not in st.session_state:
    st.session_state["user_input_expr"] = PRESETS["Linear MBA + Opaque Zero (x + y)"]

# Render main page title and header.
st.title("🛡️ PALIMPSEST: VEX-MORPH")
st.subheader("Air-Gapped Neurosymbolic Binary De-obfuscation Engine")
st.caption("Coupling Quantized Local Reasoning (Qwen-2.5-Coder-3B) with Formal Zero-Trust Theorem Proving (Z3)")

# Text area for user input expression.
user_input = st.text_area(
    "Paste 64-bit Obfuscated MBA Expression:",
    value=st.session_state["user_input_expr"],
    height=140,
    key="text_area_input",
)

# Trigger button for CEGIS de-obfuscation.
if st.button("🚀 De-obfuscate with Neurosymbolic CEGIS", use_container_width=True):
    active_expr = user_input.strip()
    if not active_expr:
        st.warning("Please provide a valid mathematical expression.")
    else:
        # Execute CEGIS state graph with interactive spinner.
        with st.spinner(f"Executing Multi-Hop CEGIS Loop (Max {max_hops} Iterations)..."):
            initial_state: CEGISState = {
                "original_expr": active_expr,
                "current_expr": "",
                "iterations": 0,
                "status": "PENDING",
                "messages": [],
                "max_iterations": max_hops,
            }
            final_state = cegis_graph.invoke(initial_state)

        # Calculate AST node counts before and after de-obfuscation.
        try:
            original_nodes = len(list(ast.walk(ast.parse(active_expr))))
        except Exception:
            original_nodes = 1

        try:
            final_nodes = len(list(ast.walk(ast.parse(final_state["current_expr"]))))
        except Exception:
            final_nodes = 1

        # Calculate AST compression percentage.
        compression_ratio = max(0.0, (1.0 - (final_nodes / original_nodes)) * 100.0)
        latency = final_state.get("verification_latency_ms", 0.0)

        # Render metric counters in 4 responsive columns.
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("AST Compression", f"{compression_ratio:.1f}%")
        c2.metric("AST Nodes", f"{original_nodes} → {final_nodes}")
        c3.metric("CEGIS Hops", f"{final_state['iterations']} / {max_hops}")
        c4.metric("Z3 Latency", f"{latency:.2f} ms")

        # Display formal verification proof banner.
        if final_state["status"] == "VERIFIED":
            st.success("✅ FORMALLY VERIFIED: QF_BV_UNSAT (Provably Equivalent 64-Bit BitVec Expression)")
        else:
            st.error(f"❌ Verification Status: {final_state['status']} (Iteration budget reached)")

        # Display simplified canonical result.
        st.markdown("### 🎯 Simplified Canonical Expression:")
        st.code(final_state["current_expr"], language="python")

        # Display hop-by-hop neurosymbolic execution trace.
        with st.expander("🔍 Neurosymbolic Execution Trace & Reasoning", expanded=True):
            st.markdown("#### Iteration Trace:")
            for idx, msg in enumerate(final_state["messages"]):
                if "Z3_VERIFICATION_FAILED" in msg:
                    st.warning(f"**⚡ Hop {idx + 1} Z3 Counterexample Feedback:**\n```\n{msg}\n```")
                else:
                    st.info(f"**🧠 Hop {idx + 1} LLM Proposer Reasoning & Hypothesis:**\n```\n{msg}\n```")
