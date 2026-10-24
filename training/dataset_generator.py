# Multi-core ShareGPT / ChatML dataset generator for MBA deobfuscation.
import argparse
import concurrent.futures
import json
import multiprocessing
import os
import random
from typing import Any, Dict, List, Optional

# Import local modules with directory fallback.
try:
    from ast_slicer import count_nodes
    from mba_mutator import MBAMutator, parse_to_ir, SEEDS
    from z3_verifier import verify_equivalence
except ImportError:
    from training.ast_slicer import count_nodes
    from training.mba_mutator import MBAMutator, parse_to_ir, SEEDS
    from training.z3_verifier import verify_equivalence

# Mapping of operators to syntactically valid alternative operators for near-miss injection.
OP_SWAPS = [
    ("+", "^"),
    ("-", "+"),
    ("^", "|"),
    ("&", "^"),
    ("|", "&"),
    ("<<", ">>"),
    ("*", "+"),
]

# Generate a single-token hallucination near-miss expression for CEGIS loop simulation.
def generate_near_miss(seed: str) -> str:
    # Handle unary inversion near-miss by stripping bitwise not.
    if "~" in seed:
        return seed.replace("~", "")

    # Attempt operator substitution from supported binary swaps.
    for op, rep in OP_SWAPS:
        if op in seed:
            idx = seed.find(op)
            return seed[:idx] + rep + seed[idx + len(op):]

    # Fallback near-miss mutation.
    return f"({seed}) ^ 1"

# Generate a single verified dataset row (worker function executed in parallel).
def generate_row(row_idx: int) -> Dict[str, Any]:
    # Seed worker's random generator uniquely using process and row identifiers.
    random.seed(os.getpid() + row_idx * 1009 + random.randint(1, 1000000))

    # Determine trace type based on 70% SFT / 30% CEGIS distribution.
    trace_type = "SFT" if random.random() < 0.7 else "CEGIS"

    # Retry loop to guarantee generation of provably verified MBA obfuscation.
    while True:
        # Pick a canonical seed expression.
        target_seed = random.choice(SEEDS)
        target_nodes = count_nodes(target_seed)

        # Mutate IR tree to depth 1 or 2.
        mut_seed = random.randint(1, 2**31 - 1)
        mutator = MBAMutator(seed=mut_seed)
        depth = random.choice([1, 2])
        seed_ir = parse_to_ir(target_seed)
        mutated_ir = mutator.mutate_tree(seed_ir, current_depth=0, max_depth=depth)

        # Inject opaque zeros with 64-bit constants.
        obf_ir = mutator.inject_opaque_zeros(mutated_ir)
        expr_obf = obf_ir.to_string()
        obf_nodes = count_nodes(expr_obf)

        # Ensure nontrivial obfuscation expansion.
        if obf_nodes <= target_nodes:
            continue

        # Verify equivalence using Z3 Miter circuit.
        verif_res = verify_equivalence(target_seed, expr_obf)
        if verif_res.get("status") != "QF_BV_UNSAT_64BIT_VERIFIED":
            continue

        z3_latency = verif_res.get("latency_ms", 0.0)
        eta_ast = round(1.0 - (target_nodes / obf_nodes), 4)

        # Build SFT conversational trace.
        if trace_type == "SFT":
            conversations = [
                {
                    "from": "user",
                    "value": f"De-obfuscate this 64-bit MBA expression:\n{expr_obf}",
                },
                {
                    "from": "assistant",
                    "value": f"<think>\nAST Node Count: {obf_nodes}. Analyzing data-flow...\n</think>\n{target_seed}",
                },
            ]
            return {
                "conversations": conversations,
                "type": "SFT",
                "eta_ast": eta_ast,
                "z3_latency_ms": z3_latency,
                "target_nodes": target_nodes,
                "obf_nodes": obf_nodes,
            }

        # Build Multi-Hop CEGIS conversational trace.
        near_miss = generate_near_miss(target_seed)
        cegis_verif = verify_equivalence(target_seed, near_miss)
        if cegis_verif.get("status") != "SAT":
            continue

        witness = cegis_verif.get("witness", {})
        expected = cegis_verif.get("expected", 0)
        actual = cegis_verif.get("actual", 0)

        conversations = [
            {
                "from": "user",
                "value": f"De-obfuscate this 64-bit MBA expression:\n{expr_obf}",
            },
            {
                "from": "assistant",
                "value": f"<think>\nAttempting reduction...\n</think>\n{near_miss}",
            },
            {
                "from": "tool",
                "value": f"Z3_VERIFICATION_FAILED: SAT\nCounterexample Witness: {witness}\nExpected: {expected}, Actual: {actual}",
            },
            {
                "from": "assistant",
                "value": f"<think>\nWitness {witness} evaluated to {actual}, but expected {expected}. Correcting operator...\n</think>\n{target_seed}",
            },
        ]
        return {
            "conversations": conversations,
            "type": "CEGIS",
            "eta_ast": eta_ast,
            "z3_latency_ms": z3_latency,
            "target_nodes": target_nodes,
            "obf_nodes": obf_nodes,
        }

if __name__ == "__main__":
    # Parse command line arguments.
    parser = argparse.ArgumentParser(description="Multi-core ShareGPT dataset generator for MBA deobfuscation")
    parser.add_argument("--rows", type=int, default=100, help="Number of dataset rows to generate")
    parser.add_argument("--output", type=str, default="training/dataset.jsonl", help="Output file path")
    args = parser.parse_args()

    # Determine CPU worker count.
    num_cpus = multiprocessing.cpu_count()
    print(f"Starting multi-core generation: {args.rows} rows using {num_cpus} workers...")

    results: List[Dict[str, Any]] = []

    # Map generation function across process pool.
    with concurrent.futures.ProcessPoolExecutor(max_workers=num_cpus) as executor:
        futures = [executor.submit(generate_row, i) for i in range(args.rows)]
        completed_count = 0
        for future in concurrent.futures.as_completed(futures):
            row_data = future.result()
            results.append(row_data)
            completed_count += 1
            if completed_count % 10 == 0 or completed_count == args.rows:
                pct = (completed_count / args.rows) * 100.0
                print(f"[Progress] {completed_count}/{args.rows} rows generated ({pct:.1f}%)")

    # Ensure parent output directory exists.
    output_dir = os.path.dirname(args.output)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)

    # Write generated rows to JSONL destination.
    with open(args.output, "w", encoding="utf-8") as f:
        for r in results:
            # Strip temporary metric counters before saving.
            output_obj = {
                "conversations": r["conversations"],
                "type": r["type"],
                "eta_ast": r["eta_ast"],
                "z3_latency_ms": r["z3_latency_ms"],
            }
            f.write(json.dumps(output_obj) + "\n")

    # Compute dataset summary statistics.
    sft_count = sum(1 for r in results if r["type"] == "SFT")
    cegis_count = sum(1 for r in results if r["type"] == "CEGIS")
    avg_obf_nodes = sum(r["obf_nodes"] for r in results) / len(results)
    avg_eta_ast = (sum(r["eta_ast"] for r in results) / len(results)) * 100.0

    # Print generation statistics.
    print("\n" + "=" * 50)
    print("Dataset Generation Complete:")
    print(f"  Total Rows: {len(results)}")
    print(f"  SFT Ratio: {(sft_count / len(results)) * 100.0:.1f}% ({sft_count} rows)")
    print(f"  CEGIS Ratio: {(cegis_count / len(results)) * 100.0:.1f}% ({cegis_count} rows)")
    print(f"  Avg Obfuscated AST Nodes: {avg_obf_nodes:.1f}")
    print(f"  Avg AST Compression Ratio: {avg_eta_ast:.2f}%")
    print(f"  Saved to: {args.output}")
    print("=" * 50)
