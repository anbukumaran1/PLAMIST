# LangGraph CEGIS neurosymbolic orchestrator integrating Ollama with Z3 Miter verifier.
import json
import re
import requests
from typing import List, TypedDict
from langgraph.graph import END, START, StateGraph

# Import zero-trust formal verification engine.
try:
    from z3_verifier import verify_equivalence
except ImportError:
    from training.z3_verifier import verify_equivalence

# Define CEGIS state schema tracking candidate expressions and formal counterexamples.
class CEGISState(TypedDict):
    original_expr: str
    current_expr: str
    iterations: int
    status: str
    messages: List[str]

# Propose candidate de-obfuscated expression using local fine-tuned Qwen 3B via Ollama.
def llm_proposer_node(state: CEGISState) -> CEGISState:
    # Print current iteration header.
    print(f"\n--- [Iteration {state['iterations'] + 1}] LLM Proposer Node ---")

    # Formulate prompt depending on whether initial proposal or counterexample refinement.
    if state["iterations"] == 0:
        prompt = f"De-obfuscate this 64-bit MBA expression:\n{state['original_expr']}"
    else:
        witness_info = state["messages"][-1]
        prompt = (
            f"De-obfuscate this 64-bit MBA expression:\n{state['original_expr']}\n"
            f"Attempting reduction...\n{state['current_expr']}\n"
            f"{witness_info}\n"
            f"Correct the logic and output the simplified canonical expression:"
        )

    # Query local Ollama instance hosting palimpsest_qwen.
    payload = {
        "model": "palimpsest_qwen",
        "prompt": prompt,
        "stream": False,
    }
    response = requests.post("http://localhost:11434/api/generate", json=payload, timeout=120)
    raw_output = response.json().get("response", "")

    # Strip reasoning think blocks and formatting fences to extract pure mathematical expression.
    clean_expr = re.sub(r"<think>[\s\S]*?</think>", "", raw_output).strip()
    clean_expr = re.sub(r"```[a-zA-Z]*\n?|```", "", clean_expr).strip()
    lines = [line.strip() for line in clean_expr.splitlines() if line.strip()]
    candidate_expr = lines[-1] if lines else raw_output.strip()

    # Update state fields.
    state["current_expr"] = candidate_expr
    state["iterations"] += 1
    state["messages"].append(raw_output)

    # Log proposal trace.
    print(f"Proposed Candidate: {candidate_expr}")
    return state

# Formally verify proposed candidate against obfuscated ground truth via Z3 Miter circuit.
def z3_verifier_node(state: CEGISState) -> CEGISState:
    # Print verification status header.
    print(f"\n--- [Iteration {state['iterations']}] Z3 Verifier Node ---")

    # Execute formal equivalence verification.
    try:
        verif_result = verify_equivalence(state["original_expr"], state["current_expr"])
        verif_status = verif_result.get("status")
    except Exception as e:
        verif_status = "ERROR"
        verif_result = {"status": "ERROR", "error": str(e)}

    # Process solver outcome.
    if verif_status == "QF_BV_UNSAT_64BIT_VERIFIED":
        state["status"] = "VERIFIED"
        latency = verif_result.get("latency_ms", 0.0)
        print(f"Formal Proof Result: VERIFIED (Latency: {latency} ms)")
    elif verif_status == "SAT":
        state["status"] = "FAILED"
        witness = verif_result.get("witness", {})
        expected = verif_result.get("expected")
        actual = verif_result.get("actual")
        witness_msg = (
            f"Z3_VERIFICATION_FAILED: SAT\n"
            f"Counterexample Witness: {witness}\n"
            f"Expected: {expected}, Actual: {actual}"
        )
        state["messages"].append(witness_msg)
        print(f"Formal Proof Result: FAILED (Counterexample Witness: {witness})")
    else:
        state["status"] = "FAILED"
        state["messages"].append(f"Z3_VERIFICATION_FAILED: {verif_status}")
        print(f"Formal Proof Result: FAILED ({verif_status})")

    return state

# Conditional routing logic directing graph execution based on verification outcome.
def route_after_verifier(state: CEGISState) -> str:
    # Terminate if proven equivalent or if iteration budget exhausted.
    if state["status"] == "VERIFIED" or state["iterations"] >= 3:
        return END
    # Reroute back to LLM proposer with counterexample witness.
    return "llm_proposer_node"

# Construct and compile LangGraph CEGIS state machine.
workflow = StateGraph(CEGISState)
workflow.add_node("llm_proposer_node", llm_proposer_node)
workflow.add_node("z3_verifier_node", z3_verifier_node)

workflow.add_edge(START, "llm_proposer_node")
workflow.add_edge("llm_proposer_node", "z3_verifier_node")
workflow.add_conditional_edges(
    "z3_verifier_node",
    route_after_verifier,
    {
        END: END,
        "llm_proposer_node": "llm_proposer_node",
    },
)

# Export compiled runnable graph.
app = workflow.compile()

if __name__ == "__main__":
    # Test expression: heavily obfuscated expression known to trigger SAT evaluation.
    test_obfuscated_expr = (
        "((((x) ^ (y))) + (((((2) * (((x) & (y))))) + "
        "(((0xca70da7a7e57ed13) * (((((((x) | (x))) - (((x) ^ (x))))) - (((x) & (x))))))))))"
    )

    # Initialize state payload.
    initial_state: CEGISState = {
        "original_expr": test_obfuscated_expr,
        "current_expr": "",
        "iterations": 0,
        "status": "INITIALIZING",
        "messages": [],
    }

    # Print launch header.
    print("=" * 60)
    print("PALIMPSEST: Air-Gapped Neurosymbolic CEGIS Loop")
    print(f"Input Obfuscated MBA:\n{test_obfuscated_expr}")
    print("=" * 60)

    # Execute StateGraph workflow.
    final_state = app.invoke(initial_state)

    # Print final execution summary.
    print("\n" + "=" * 60)
    print("CEGIS Workflow Completed")
    print(f"Total Iterations: {final_state['iterations']}")
    print(f"Final Verification Status: {final_state['status']}")
    print(f"Final Canonical Expression: {final_state['current_expr']}")
    print("=" * 60)
