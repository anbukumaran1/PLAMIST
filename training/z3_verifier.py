# Zero-trust AST-to-Z3 compiler and QF_BV Miter circuit equivalence verifier.
import ast
import random
import time
from typing import Any, Dict

import z3

# Import zero-trust AST slicer components.
try:
    from ast_slicer import ZeroTrustAST, count_nodes
except ImportError:
    from training.ast_slicer import ZeroTrustAST, count_nodes

# Import IR mutator and parser.
try:
    from mba_mutator import MBAMutator, parse_to_ir
except ImportError:
    from training.mba_mutator import MBAMutator, parse_to_ir

# Native AST-to-Z3 compiler translating Python AST to 64-bit BitVec expressions.
class Z3Compiler(ast.NodeVisitor):
    # Initialize compiler with 64-bit BitVec variable mapping.
    def __init__(self, z3_vars: Dict[str, z3.BitVecRef]) -> None:
        self.z3_vars = z3_vars

    # Compile AST node into native Z3 expression.
    def compile(self, node: ast.AST) -> z3.BitVecRef:
        return self.visit(node)

    # Unwrap root module container.
    def visit_Module(self, node: ast.Module) -> z3.BitVecRef:
        return self.visit(node.body[0])

    # Unwrap statement expression container.
    def visit_Expr(self, node: ast.Expr) -> z3.BitVecRef:
        return self.visit(node.value)

    # Unwrap eval expression container.
    def visit_Expression(self, node: ast.Expression) -> z3.BitVecRef:
        return self.visit(node.body)

    # Compile binary operation AST node to Z3 BitVec operator.
    def visit_BinOp(self, node: ast.BinOp) -> z3.BitVecRef:
        left = self.visit(node.left)
        right = self.visit(node.right)
        op_type = type(node.op)
        if op_type is ast.Add:
            return left + right
        elif op_type is ast.Sub:
            return left - right
        elif op_type is ast.Mult:
            return left * right
        elif op_type is ast.BitAnd:
            return left & right
        elif op_type is ast.BitOr:
            return left | right
        elif op_type is ast.BitXor:
            return left ^ right
        elif op_type is ast.LShift:
            return left << right
        elif op_type is ast.RShift:
            return left >> right
        raise ValueError(f"Unsupported binary operator: {op_type.__name__}")

    # Compile unary operation AST node to Z3 BitVec operator.
    def visit_UnaryOp(self, node: ast.UnaryOp) -> z3.BitVecRef:
        operand = self.visit(node.operand)
        op_type = type(node.op)
        if op_type is ast.Invert:
            return ~operand
        elif op_type is ast.USub:
            return -operand
        raise ValueError(f"Unsupported unary operator: {op_type.__name__}")

    # Compile variable identifier to corresponding Z3 64-bit BitVec.
    def visit_Name(self, node: ast.Name) -> z3.BitVecRef:
        if node.id not in self.z3_vars:
            raise ValueError(f"Unknown variable: {node.id}")
        return self.z3_vars[node.id]

    # Compile integer constant to 64-bit Z3 BitVec literal.
    def visit_Constant(self, node: ast.Constant) -> z3.BitVecRef:
        return z3.BitVecVal(node.value, 64)

# Verify semantic equivalence of two expressions using zero-trust QF_BV Miter circuit.
def verify_equivalence(expr_seed: str, expr_obf: str) -> Dict[str, Any]:
    # Parse both expressions into abstract syntax trees.
    tree_seed = ast.parse(expr_seed)
    tree_obf = ast.parse(expr_obf)

    # Enforce zero-trust AST whitelist verification on both expressions.
    ZeroTrustAST().visit(tree_seed)
    ZeroTrustAST().visit(tree_obf)

    # Extract unique variable names across both AST trees.
    unique_vars = sorted(list(
        {n.id for n in ast.walk(tree_seed) if isinstance(n, ast.Name)} |
        {n.id for n in ast.walk(tree_obf) if isinstance(n, ast.Name)}
    ))

    # Map each variable to a 64-bit Z3 BitVec.
    z3_vars = {v: z3.BitVec(v, 64) for v in unique_vars}

    # Compile both AST trees into native Z3 BitVec expressions.
    compiler = Z3Compiler(z3_vars)
    z3_seed = compiler.compile(tree_seed)
    z3_obf = compiler.compile(tree_obf)

    # Initialize Miter circuit solver with 3000 ms timeout.
    solver = z3.Solver()
    solver.set("timeout", 3000)

    # Add negated equivalence assertion to detect discrepancies.
    solver.add(z3_seed != z3_obf)

    # Benchmark solver execution latency.
    start_ns = time.perf_counter_ns()
    result = solver.check()
    end_ns = time.perf_counter_ns()
    latency = round((end_ns - start_ns) / 1_000_000, 3)

    # Return verified unsat payload if expressions are provably equivalent.
    if result == z3.unsat:
        return {
            "status": "QF_BV_UNSAT_64BIT_VERIFIED",
            "latency_ms": latency,
        }

    # Return sat counterexample payload if a discrepancy is discovered.
    if result == z3.sat:
        model = solver.model()
        witness_dict = {
            v: model.eval(z3_vars[v], model_completion=True).as_long()
            for v in unique_vars
        }
        val_seed = model.eval(z3_seed, model_completion=True).as_long()
        val_obf = model.eval(z3_obf, model_completion=True).as_long()
        return {
            "status": "SAT",
            "witness": witness_dict,
            "expected": val_seed,
            "actual": val_obf,
            "latency_ms": latency,
        }

    # Return timeout or inconclusive solver status.
    return {
        "status": "UNKNOWN_OR_TIMEOUT",
        "latency_ms": latency,
    }

if __name__ == "__main__":
    # Initialize mutator with deterministic seed for reproducible verification.
    mutator = MBAMutator(seed=4)

    # Parse canonical seed expression into IR tree.
    canonical_seed = "x + y"
    seed_ir = parse_to_ir(canonical_seed)

    # Mutate tree and inject opaque zeros with random 64-bit constants.
    mutated_tree = mutator.mutate_tree(seed_ir, current_depth=0, max_depth=2)
    obfuscated_tree = mutator.inject_opaque_zeros(mutated_tree)

    # Render final obfuscated string representation.
    obfuscated_str = obfuscated_tree.to_string()
    obfuscated_nodes = count_nodes(obfuscated_str)

    # Output obfuscated MBA expression and total AST node count.
    print(f"Obfuscated MBA String:\n{obfuscated_str}")
    print(f"AST Node Count: {obfuscated_nodes}")

    # Solve Miter circuit and display verification payload.
    verification_payload = verify_equivalence(canonical_seed, obfuscated_str)
    print(f"Verification Result:\n{verification_payload}")
