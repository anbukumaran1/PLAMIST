# Intermediate Representation (IR) tree-based recursive MBA mutator.
import ast
import random
from dataclasses import dataclass
from typing import Optional

# Import node counter from local zero-trust AST slicer.
try:
    from ast_slicer import count_nodes
except ImportError:
    from training.ast_slicer import count_nodes

# Stage 1: Canonical seed expressions for MBA dataset generation.
SEEDS = [
    "x + y",
    "x - y",
    "2 * x + y",
    "(x + y) - z",
    "x ^ y",
    "x & y",
    "x | y",
    "~x",
    "(x + y) ^ z",
    "(x & y) + z",
    "(x << 1) | y",
    "(x ^ y) - z",
]

# Base class for Intermediate Representation (IR) AST nodes.
@dataclass
class Node:
    # Render IR node into a heavily parenthesized string representation.
    def to_string(self) -> str:
        raise NotImplementedError

# Binary operation IR node.
@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node

    # Heavily parenthesize every binary operation to preserve order of operations.
    def to_string(self) -> str:
        return f"(({self.left.to_string()}) {self.op} ({self.right.to_string()}))"

# Unary operation IR node.
@dataclass
class UnaryOp(Node):
    op: str
    operand: Node

    # Heavily parenthesize unary operation and its operand.
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

    # Render constant value as string.
    def to_string(self) -> str:
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

# MBAMutator class applying weighted stochastic rewrite rules.
class MBAMutator:
    # Initialize mutator with an optional deterministic seed.
    def __init__(self, seed: Optional[int] = None) -> None:
        if seed is not None:
            random.seed(seed)

    # Recursively mutate an IR tree up to max_depth.
    def mutate_tree(self, node: Node, current_depth: int = 0, max_depth: int = 4) -> Node:
        # Halt recursion when maximum depth limit is reached.
        if current_depth >= max_depth:
            return node

        # Binary operator mutation with 80% probability.
        if isinstance(node, BinOp):
            if node.op in ("+", "-", "^", "&", "|") and random.random() < 0.8:
                a = node.left
                b = node.right
                # Rewrite 1: Add(a, b) -> Add(Xor(a, b), Mult(Const(2), And(a, b))) OR Add(Or(a, b), And(a, b))
                if node.op == "+":
                    mutated = random.choice([
                        Add(Xor(a, b), Mult(Const(2), And(a, b))),
                        Add(Or(a, b), And(a, b)),
                    ])
                # Rewrite 2: Xor(a, b) -> Sub(Or(a, b), And(a, b))
                elif node.op == "^":
                    mutated = Sub(Or(a, b), And(a, b))
                # Rewrite 3: And(a, b) -> Sub(Add(a, b), Or(a, b))
                elif node.op == "&":
                    mutated = Sub(Add(a, b), Or(a, b))
                # Rewrite 4: Sub(a, b) -> Sub(Xor(a, b), Mult(Const(2), And(Not(a), b)))
                elif node.op == "-":
                    mutated = Sub(Xor(a, b), Mult(Const(2), And(Not(a), b)))
                # Rewrite 6: Or(a, b) -> Not(And(Not(a), Not(b)))
                elif node.op == "|":
                    mutated = Not(And(Not(a), Not(b)))
                else:
                    mutated = node
                # Continue mutating transformed subtree with incremented depth.
                return self.mutate_tree(mutated, current_depth + 1, max_depth)
            else:
                # Recurse down children without mutating current binary node.
                new_left = self.mutate_tree(node.left, current_depth + 1, max_depth)
                new_right = self.mutate_tree(node.right, current_depth + 1, max_depth)
                return BinOp(node.op, new_left, new_right)

        # Unary operator mutation: recurse on operand.
        if isinstance(node, UnaryOp):
            new_operand = self.mutate_tree(node.operand, current_depth + 1, max_depth)
            return UnaryOp(node.op, new_operand)

        # Variable node mutation with 10% probability to prevent unary explosion.
        if isinstance(node, Var):
            # Rewrite 5: Var(a) -> Not(Not(a))
            if random.random() < 0.1:
                mutated = Not(Not(node))
                return self.mutate_tree(mutated, current_depth + 1, max_depth)
            return node

        # Base case for Const or unmodified nodes.
        return node

if __name__ == "__main__":
    # Initialize mutator with fixed seed for deterministic reproducibility.
    fixed_seed = 42
    mutator = MBAMutator(seed=fixed_seed)

    # Parse canonical seed expression into IR tree.
    canonical_seed = "x + y"
    ir_tree = parse_to_ir(canonical_seed)
    orig_string = ir_tree.to_string()
    orig_node_count = count_nodes(canonical_seed)

    # Mutate IR tree recursively to max_depth=4.
    mutated_tree = mutator.mutate_tree(ir_tree, current_depth=0, max_depth=4)
    mutated_string = mutated_tree.to_string()
    mutated_node_count = count_nodes(mutated_string)

    # Output original and mutated representations with AST node counts.
    print(f"Original Seed: {canonical_seed}")
    print(f"Original IR String: {orig_string}")
    print(f"Original AST Node Count: {orig_node_count}")
    print(f"Mutated MBA String: {mutated_string}")
    print(f"Mutated AST Node Count: {mutated_node_count}")
