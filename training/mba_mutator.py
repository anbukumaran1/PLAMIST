# Intermediate Representation (IR) tree-based recursive MBA mutator with reversible ledger.
import ast
import random
import sys
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

# Raise recursion limit for deep AST operations.
sys.setrecursionlimit(10000)

# Import node counter from local zero-trust AST slicer.
try:
    from ast_slicer import count_nodes
except ImportError:
    from training.ast_slicer import count_nodes

# Strict AST node ceiling to prevent context window explosion and solver timeout.
MAX_AST_NODES = 160

# 64-bit BitVec mask.
MASK_64 = 0xFFFFFFFFFFFFFFFF

# Positive constant generator ensuring zero-trust AST compliance without USub nodes.
def get_masked_const() -> int:
    # 31-bit positive random integer avoids Python AST unary minus ambiguity.
    return random.randint(1, 0x7FFFFFFF) & MASK_64

# Canonical seed expressions covering bitwise logic, arithmetic, shifts, and registers.
SEEDS = [
    # Canonical variables (x, y, z).
    "x + y",
    "x - y",
    "x ^ y",
    "x & y",
    "x | y",
    "(x + y) ^ z",
    "(x & y) + (x | y)",
    "(2 * x) - y",
    "(x << 1) + y",
    "~x ^ y",
    "(x ^ y) - z",
    "(x + y) - (x & y)",
    "(x | y) ^ (x & y)",
    "(x << 2) + (y >> 1)",
    "~x + ~y",
    "(x & y) ^ z",
    "(x | y) - z",
    "(x + z) & (y + z)",
    "(x ^ y) + (x & y)",
    "~((x & y) | z)",
    # X86-64 register variables.
    "rax + rbx",
    "rax - rbx",
    "rax ^ rbx",
    "rax & rbx",
    "rax | rbx",
    "(rax + rbx) ^ rcx",
    "(rax & rbx) + (rax | rbx)",
    "(rax << 1) + rbx",
    "(rax ^ rbx) - rcx",
    "(rax & rbx) ^ rdx",
    "(rsi + rdi) - r8",
    "(r8 ^ r9) + rax",
    "(rsi & rdi) | (r8 & r9)",
    "(2 * rax) + (rbx << 2)",
    "~rax ^ rbx",
    "(rax | rbx) - (rax & rbx)",
    "(rcx + rdx) ^ (rsi - rdi)",
]

# Base class for Intermediate Representation (IR) AST nodes.
@dataclass
class Node:
    # Render IR node into a clean parenthesized string representation.
    def to_string(self) -> str:
        raise NotImplementedError

# Binary operation IR node.
@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node

    # Parenthesize binary operation to preserve order of operations.
    def to_string(self) -> str:
        return f"({self.left.to_string()} {self.op} {self.right.to_string()})"

# Unary operation IR node.
@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

    # Parenthesize unary operation and its operand.
    def to_string(self) -> str:
        return f"({self.op}({self.operand.to_string()}))"

# Variable identifier IR node.
@dataclass
class Var(Node):
    name: str

    # Render variable name as bare identifier.
    def to_string(self) -> str:
        return self.name

# Constant integer literal IR node.
@dataclass
class Const(Node):
    val: int

    # Render constant value, displaying 64-bit values in hex notation.
    def to_string(self) -> str:
        if self.val > 255:
            return hex(self.val)
        return str(self.val)

# Helper constructor functions for clean rewrite rule authoring.
def Add(a: Node, b: Node) -> BinOp:
    return BinOp("+", a, b)

def Sub(a: Node, b: Node) -> BinOp:
    return BinOp("-", a, b)

def Mult(a: Node, b: Node) -> BinOp:
    return BinOp("*", a, b)

def Xor(a: Node, b: Node) -> BinOp:
    return BinOp("^", a, b)

def And(a: Node, b: Node) -> BinOp:
    return BinOp("&", a, b)

def Or(a: Node, b: Node) -> BinOp:
    return BinOp("|", a, b)

def Not(a: Node) -> UnaryOp:
    return UnaryOp("~", a)

# Mapping of Python AST binary operators to IR operator strings.
OP_MAP = {
    ast.Add: "+",
    ast.Sub: "-",
    ast.Mult: "*",
    ast.BitXor: "^",
    ast.BitAnd: "&",
    ast.BitOr: "|",
    ast.LShift: "<<",
    ast.RShift: ">>",
}

# Mapping of Python AST unary operators to IR operator strings.
UNARY_OP_MAP = {
    ast.Invert: "~",
}

# Extract all variable identifiers present within an IR subtree.
def extract_variables(node: Node) -> Set[str]:
    vars_found: Set[str] = set()
    def visit(n: Node) -> None:
        if isinstance(n, Var):
            vars_found.add(n.name)
        elif isinstance(n, BinOp):
            visit(n.left)
            visit(n.right)
        elif isinstance(n, UnaryOp):
            visit(n.operand)
    visit(node)
    return vars_found

# Check whether an IR subtree contains bitwise shift operators.
def has_shift(node: Node) -> bool:
    if isinstance(node, BinOp):
        if node.op in ("<<", ">>"):
            return True
        return has_shift(node.left) or has_shift(node.right)
    if isinstance(node, UnaryOp):
        return has_shift(node.operand)
    return False

# Collect all nodes matching a predicate in an IR tree.
def collect_nodes(root: Node, predicate: Callable[[Node], bool]) -> List[Node]:
    found: List[Node] = []
    def walk(n: Node) -> None:
        if predicate(n):
            found.append(n)
        if isinstance(n, BinOp):
            walk(n.left)
            walk(n.right)
        elif isinstance(n, UnaryOp):
            walk(n.operand)
    walk(root)
    return found

# Replace a specific target node within an IR tree by reference identity.
def replace_node(root: Node, target: Node, replacement: Node) -> Node:
    if root is target:
        return replacement
    if isinstance(root, BinOp):
        return BinOp(
            root.op,
            replace_node(root.left, target, replacement),
            replace_node(root.right, target, replacement),
        )
    if isinstance(root, UnaryOp):
        return UnaryOp(root.op, replace_node(root.operand, target, replacement))
    return root

# Parse Python expression string into Intermediate Representation (IR) tree.
def parse_to_ir(expr: str) -> Node:
    tree = ast.parse(expr, mode="eval")

    # Recursive converter from Python AST node to IR node.
    def convert(n: ast.AST) -> Node:
        if isinstance(n, ast.BinOp):
            op_cls = type(n.op)
            if op_cls not in OP_MAP:
                raise ValueError(f"Unsupported binary operator: {op_cls.__name__}")
            return BinOp(OP_MAP[op_cls], convert(n.left), convert(n.right))
        if isinstance(n, ast.UnaryOp):
            op_cls = type(n.op)
            if op_cls not in UNARY_OP_MAP:
                raise ValueError(f"Unsupported unary operator: {op_cls.__name__}")
            return UnaryOp(UNARY_OP_MAP[op_cls], convert(n.operand))
        if isinstance(n, ast.Name):
            return Var(n.id)
        if isinstance(n, ast.Constant):
            return Const(n.value)
        raise ValueError(f"Unsupported AST node type: {type(n).__name__}")

    return convert(tree.body)

# Custom return structure supporting dict indexing and tuple unpacking.
class MutationResult(dict):
    # Enable tuple unpacking for (obfuscated_expr, canonical_seed, mutation_ledger, tier).
    def __iter__(self):
        yield self["obfuscated_expr"]
        yield self["canonical_seed"]
        yield self["mutation_ledger"]
        yield self["tier"]

# MBAMutator class orchestrating the 4-stage rewrite arsenal with reversible ledger.
class MBAMutator:
    # Initialize mutator with an optional deterministic seed.
    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)

    # Stage 1: Apply linear MBA identities to a selected binary operator.
    def apply_linear_mba(self, root: Node, ledger: Optional[List[str]] = None) -> Node:
        eligible = collect_nodes(root, lambda n: isinstance(n, BinOp) and n.op in ("+", "-", "^", "|") and count_nodes(n.to_string()) <= 40)
        if not eligible:
            eligible = collect_nodes(root, lambda n: isinstance(n, BinOp) and n.op in ("+", "-", "^", "|"))
        if not eligible:
            return root
        target = random.choice(eligible)
        assert isinstance(target, BinOp)

        if target.op == "+":
            # A + B -> (A ^ B) + (2 * (A & B)) OR (A | B) + (A & B)
            if random.random() < 0.5:
                expanded = Add(Xor(target.left, target.right), Mult(Const(2), And(target.left, target.right)))
                rule = "Linear MBA: (A + B) -> (A ^ B) + (2 * (A & B))"
            else:
                expanded = Add(Or(target.left, target.right), And(target.left, target.right))
                rule = "Linear MBA: (A + B) -> (A | B) + (A & B)"
        elif target.op == "-":
            # A - B -> (A ^ B) - (2 * ((~A) & B)) OR A + ((~B) + 1)
            if random.random() < 0.5:
                expanded = Sub(Xor(target.left, target.right), Mult(Const(2), And(Not(target.left), target.right)))
                rule = "Linear MBA: (A - B) -> (A ^ B) - (2 * ((~A) & B))"
            else:
                expanded = Add(target.left, Add(Not(target.right), Const(1)))
                rule = "Linear MBA: (A - B) -> A + ((~B) + 1)"
        elif target.op == "^":
            # A ^ B -> (A | B) - (A & B) OR (A + B) - (2 * (A & B))
            if random.random() < 0.5:
                expanded = Sub(Or(target.left, target.right), And(target.left, target.right))
                rule = "Linear MBA: (A ^ B) -> (A | B) - (A & B)"
            else:
                expanded = Sub(Add(target.left, target.right), Mult(Const(2), And(target.left, target.right)))
                rule = "Linear MBA: (A ^ B) -> (A + B) - (2 * (A & B))"
        elif target.op == "|":
            # A | B -> (A ^ B) + (A & B)
            expanded = Add(Xor(target.left, target.right), And(target.left, target.right))
            rule = "Linear MBA: (A | B) -> (A ^ B) + (A & B)"
        else:
            return root

        candidate = replace_node(root, target, expanded)
        try:
            if count_nodes(candidate.to_string()) <= MAX_AST_NODES:
                if ledger is not None:
                    ledger.append(rule)
                return candidate
        except Exception:
            pass
        return root

    # Stage 2: Inject opaque zeros (Omega_0 == 0) wrapping a selected subtree.
    def inject_opaque_zeros(self, root: Node, ledger: Optional[List[str]] = None) -> Node:
        eligible = collect_nodes(root, lambda n: isinstance(n, BinOp) and n.op in ("+", "-", "^", "&", "|"))
        if not eligible:
            eligible = collect_nodes(root, lambda n: isinstance(n, BinOp) or n is root)
        if not eligible:
            return root
        target = random.choice(eligible)

        var_list = sorted(list(extract_variables(root)))
        if not var_list:
            var_list = ["x"]

        # Select random variable operands from active tree scope.
        a = Var(random.choice(var_list))
        b = Var(random.choice(var_list))
        c = Var(random.choice(var_list))
        pred_choice = random.choice(["0b", "0d", "0b", "0d", "0a", "0c"])

        if pred_choice == "0a":
            # Omega_0a: ((a | b) - (a ^ b)) - (a & b)
            omega = Sub(Sub(Or(a, b), Xor(a, b)), And(a, b))
            rule = f"Opaque Zero: + (((({a.name} | {b.name}) - ({a.name} ^ {b.name})) - ({a.name} & {b.name}))) == 0"
            wrapped = Add(target, omega)
        elif pred_choice == "0b":
            # Omega_0b: (a & (~a)) * c
            hex_const = get_masked_const()
            omega = Mult(And(a, Not(a)), c)
            rule = f"Opaque Zero: + ({hex(hex_const)} * (({a.name} & (~{a.name})) * {c.name})) == 0"
            wrapped = Add(target, Mult(Const(hex_const), omega))
        elif pred_choice == "0c":
            # Omega_0c: ((a ^ b) + ((a & b) << 1)) - (a + b)
            omega = Sub(Add(Xor(a, b), BinOp("<<", And(a, b), Const(1))), Add(a, b))
            rule = f"Opaque Zero: + (((({a.name} ^ {b.name}) + (({a.name} & {b.name}) << 1)) - ({a.name} + {b.name}))) == 0"
            wrapped = Add(target, omega)
        else:
            # Omega_0d: ((~a) | (~b)) ^ (~(a & b))
            hex_const = get_masked_const()
            omega = Xor(Or(Not(a), Not(b)), Not(And(a, b)))
            rule = f"Opaque Zero: + ({hex(hex_const)} * (((~{a.name}) | (~{b.name})) ^ (~({a.name} & {b.name})))) == 0"
            wrapped = Add(target, Mult(Const(hex_const), omega))
        candidate = replace_node(root, target, wrapped)
        try:
            if count_nodes(candidate.to_string()) <= MAX_AST_NODES:
                if ledger is not None:
                    ledger.append(rule)
                return candidate
        except Exception:
            pass
        return root

    # Stage 3: Inject opaque ones (Omega_1 == 1) wrapping a selected subtree in Mult(node, Omega_1).
    def inject_opaque_ones(self, root: Node, ledger: Optional[List[str]] = None) -> Node:
        # Avoid non-linear multiplication in expressions containing bitwise shifts to prevent solver timeouts.
        if has_shift(root):
            return root
        eligible = collect_nodes(root, lambda n: isinstance(n, (Var, Const)) and not has_shift(n))
        if not eligible:
            return root
        target = random.choice(eligible)

        var_list = sorted(list(extract_variables(root)))
        if not var_list:
            var_list = ["x"]

        a = Var(random.choice(var_list))
        pred_choice = random.choice(["1a", "1b"])
        if pred_choice == "1a":
            # Omega_1a: (0 - (a | (~a))) == 1 in two's complement without USub.
            omega = Sub(Const(0), Or(a, Not(a)))
            rule = f"Opaque One: * (0 - ({a.name} | (~{a.name}))) == 1"
        else:
            # Omega_1b: ((a ^ (~a)) + (2 * (a & (~a)))) + 2 == 1
            omega = Add(Add(Xor(a, Not(a)), Mult(Const(2), And(a, Not(a)))), Const(2))
            rule = f"Opaque One: * ((({a.name} ^ (~{a.name})) + (2 * ({a.name} & (~{a.name})))) + 2) == 1"

        wrapped = Mult(target, omega)
        candidate = replace_node(root, target, wrapped)
        try:
            if count_nodes(candidate.to_string()) <= MAX_AST_NODES:
                if ledger is not None:
                    ledger.append(rule)
                return candidate
        except Exception:
            pass
        return root

    # Stage 4: Constant unfolding: C -> ((C ^ R) + (2 * (C & R))) - R.
    def unfold_constants(self, root: Node, ledger: Optional[List[str]] = None) -> Node:
        eligible = collect_nodes(root, lambda n: isinstance(n, Const))
        if not eligible:
            return root
        target = random.choice(eligible)
        assert isinstance(target, Const)

        c_val = target.val
        r_val = get_masked_const()
        unfolded = Sub(
            Add(
                Xor(Const(c_val), Const(r_val)),
                Mult(Const(2), And(Const(c_val), Const(r_val))),
            ),
            Const(r_val),
        )

        candidate = replace_node(root, target, unfolded)
        try:
            if count_nodes(candidate.to_string()) <= MAX_AST_NODES:
                if ledger is not None:
                    c_str = hex(c_val) if c_val > 255 else str(c_val)
                    r_str = hex(r_val)
                    ledger.append(f"Constant Unfolded: {c_str} -> (({c_str} ^ {r_str}) + (2 * ({c_str} & {r_str}))) - {r_str}")
                return candidate
        except Exception:
            pass
        return root

    # Backward compatible recursive tree mutation method for z3_verifier.py.
    def mutate_tree(self, node: Node, current_depth: int = 0, max_depth: int = 4) -> Node:
        if current_depth >= max_depth:
            return node

        if isinstance(node, BinOp):
            if node.op in ("+", "-", "^", "&", "|") and random.random() < 0.8:
                a = node.left
                b = node.right
                if node.op == "+":
                    mutated = random.choice([
                        Add(Xor(a, b), Mult(Const(2), And(a, b))),
                        Add(Or(a, b), And(a, b)),
                    ])
                elif node.op == "^":
                    mutated = Sub(Or(a, b), And(a, b))
                elif node.op == "&":
                    mutated = Sub(Add(a, b), Or(a, b))
                elif node.op == "-":
                    mutated = Sub(Xor(a, b), Mult(Const(2), And(Not(a), b)))
                elif node.op == "|":
                    mutated = Add(Xor(a, b), And(a, b))
                else:
                    mutated = node
                return self.mutate_tree(mutated, current_depth + 1, max_depth)
            else:
                new_left = self.mutate_tree(node.left, current_depth + 1, max_depth)
                new_right = self.mutate_tree(node.right, current_depth + 1, max_depth)
                return BinOp(node.op, new_left, new_right)

        if isinstance(node, UnaryOp):
            new_operand = self.mutate_tree(node.operand, current_depth + 1, max_depth)
            return UnaryOp(node.op, new_operand)

        return node

    # Curriculum-stratified mutation method returning verifiable obfuscation with reversible ledger.
    def mutate(self, seed: Optional[str] = None, tier: int = 1) -> MutationResult:
        canonical_seed = seed if seed is not None else random.choice(SEEDS)
        ir_tree = parse_to_ir(canonical_seed)
        seed_nodes = count_nodes(canonical_seed)

        # Map tier to mutation step bounds.
        if tier == 1:
            step_count = random.randint(1, 2)
        elif tier == 2:
            step_count = random.randint(3, 4)
        else:
            step_count = random.randint(5, 6)

        ledger: List[str] = []
        current_tree = ir_tree

        # Apply progressive mutations respecting the MAX_AST_NODES ceiling.
        for _ in range(step_count * 2):
            if len(ledger) >= step_count:
                break
            if count_nodes(current_tree.to_string()) >= MAX_AST_NODES:
                break

            # Action selection weighted by tier.
            weights = [0.5, 0.5, 0.0, 0.0] if tier == 1 else ([0.4, 0.35, 0.25, 0.0] if tier == 2 else [0.35, 0.3, 0.2, 0.15])
            action = random.choices(["linear", "zero", "one", "unfold"], weights=weights, k=1)[0]

            prev_len = len(ledger)
            if action == "linear":
                current_tree = self.apply_linear_mba(current_tree, ledger)
            elif action == "zero":
                current_tree = self.inject_opaque_zeros(current_tree, ledger)
            elif action == "one":
                current_tree = self.inject_opaque_ones(current_tree, ledger)
            elif action == "unfold":
                current_tree = self.unfold_constants(current_tree, ledger)

            # If action did not add a rule, try linear MBA as fallback.
            if len(ledger) == prev_len:
                current_tree = self.apply_linear_mba(current_tree, ledger)

        # Fallback guarantee: ensure at least one verifiable expansion exists.
        if not ledger or count_nodes(current_tree.to_string()) <= seed_nodes:
            current_tree = self.apply_linear_mba(ir_tree, ledger)
            if not ledger:
                current_tree = self.inject_opaque_zeros(ir_tree, ledger)

        obf_expr = current_tree.to_string()
        return MutationResult({
            "obfuscated_expr": obf_expr,
            "canonical_seed": canonical_seed,
            "mutation_ledger": ledger,
            "tier": tier,
        })

if __name__ == "__main__":
    # Test all 3 tiers with deterministic seed.
    mutator = MBAMutator(seed=42)
    for t in [1, 2, 3]:
        res = mutator.mutate(tier=t)
        print(f"\n--- Tier {t} Mutation Test ---")
        print(f"Seed: {res['canonical_seed']}")
        print(f"Obfuscated: {res['obfuscated_expr']}")
        print(f"AST Node Count: {count_nodes(res['obfuscated_expr'])}")
        print(f"Ledger Steps ({len(res['mutation_ledger'])}):")
        for step in res["mutation_ledger"]:
            print(f"  + {step}")
