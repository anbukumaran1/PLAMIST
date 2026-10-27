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
st.set_page_config(layout="wide", page_title="PALIMPSEST", page_icon="🛡️")

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

# Render main header and de-obfuscation subheader.
st.title("🛡️ PALIMPSEST: VEX-MORPH")
st.subheader("Air-Gapped Neurosymbolic Binary De-obfuscation")
st.caption("Powered by Local Qwen-2.5-Coder-3B QLoRA, Z3 QF_BV Miter Verification & LangGraph")

# Default complex MBA test expression.
DEFAULT_OBFUSCATED_MBA = (
    "((((x) ^ (y))) + (((((2) * (((x) & (y))))) + "
    "(((0xca70da7a7e57ed13) * (((((((x) | (x))) - (((x) ^ (x))))) - (((x) & (x))))))))))"
)

# Text area for user input expression.
user_input = st.text_area(
    "Paste 64-bit Obfuscated MBA Expression:",
    value=DEFAULT_OBFUSCATED_MBA,
    height=150,
)

# Action button to trigger the CEGIS workflow.
if st.button("Initialize CEGIS Loop", use_container_width=True):
    if not user_input.strip():
        st.warning("Please provide a valid mathematical expression.")
    else:
        # Execute CEGIS state graph with interactive spinner.
        with st.spinner("Initializing Local Qwen-3B & Z3 Miter Circuit..."):
            initial_state: CEGISState = {
                "original_expr": user_input.strip(),
                "current_expr": "",
                "iterations": 0,
                "status": "PENDING",
                "messages": [],
            }
            final_state = cegis_graph.invoke(initial_state)

        # Calculate AST baseline node counts.
        try:
            original_nodes = len(list(ast.walk(ast.parse(user_input.strip()))))
        except Exception:
            original_nodes = 1

        try:
            final_nodes = len(list(ast.walk(ast.parse(final_state["current_expr"]))))
        except Exception:
            final_nodes = 1

        # Calculate AST compression percentage.
        compression_ratio = (1.0 - (final_nodes / original_nodes)) * 100.0

        # Render metric counters in 3 responsive columns.
        col1, col2, col3 = st.columns(3)
        col1.metric("AST Compression (%)", f"{compression_ratio:.2f}%")
        col2.metric("Total CEGIS Hops", final_state["iterations"])
        col3.metric("Verification Status", final_state["status"])

        # Display verification status alert.
        if final_state["status"] == "VERIFIED":
            st.success("✅ QF_BV_UNSAT: MATHEMATICALLY PROVEN")
        else:
            st.error(f"❌ Verification Status: {final_state['status']}")

        # Display final simplified canonical expression.
        st.markdown("### Simplified Canonical Expression:")
        st.code(final_state["current_expr"], language="python")

        # Display hop-by-hop neurosymbolic execution trace.
        with st.expander("Neurosymbolic Execution Trace", expanded=True):
            st.markdown("#### Hop-by-Hop History:")
            for idx, msg in enumerate(final_state["messages"]):
                if "Z3_VERIFICATION_FAILED" in msg:
                    st.warning(f"**Hop Verification Feedback:**\n```\n{msg}\n```")
                else:
                    st.info(f"**LLM Proposal Iteration {idx + 1}:**\n```\n{msg}\n```")
