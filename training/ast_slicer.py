# Zero-trust AST slicer and node counter for MBA expressions.
import ast

# Zero-trust AST visitor enforcing strict node whitelisting.
class ZeroTrustAST(ast.NodeVisitor):
    # Allowed operator AST node types.
    ALLOWED_OPERATORS = (
        ast.Add,
        ast.Sub,
        ast.Mult,
        ast.BitAnd,
        ast.BitOr,
        ast.BitXor,
        ast.Invert,
        ast.LShift,
        ast.RShift,
    )
    # Complete whitelist of allowed AST node types.
    ALLOWED_NODES = (
        ast.BinOp,
        ast.UnaryOp,
        *ALLOWED_OPERATORS,
        ast.Name,
        ast.Constant,
    )
    # Explicitly forbidden AST node types that trigger immediate rejection.
    DISALLOWED_NODES = (
        ast.Call,
        ast.Attribute,
        ast.Import,
        ast.ImportFrom,
    )

    # Initialize node counter.
    def __init__(self) -> None:
        self.node_count = 0

    # Generic visitor fallback for validating and counting nodes.
    def generic_visit(self, node: ast.AST) -> None:
        # Pass through root module or expr containers without counting them.
        if isinstance(node, (ast.Module, ast.Expr, ast.Expression)):
            super().generic_visit(node)
            return
        # Explicit rejection for forbidden node types.
        if isinstance(node, self.DISALLOWED_NODES):
            raise ValueError(f"Explicitly rejected node type: {type(node).__name__}")
        # Enforce whitelist on all expression nodes.
        if not isinstance(node, self.ALLOWED_NODES):
            raise ValueError(f"Disallowed AST node: {type(node).__name__}")
        # Increment baseline AST node count for allowed nodes.
        self.node_count += 1
        super().generic_visit(node)

    # Explicitly reject Call nodes.
    def visit_Call(self, node: ast.Call) -> None:
        raise ValueError("Explicitly rejected node type: Call")

    # Explicitly reject Attribute nodes.
    def visit_Attribute(self, node: ast.Attribute) -> None:
        raise ValueError("Explicitly rejected node type: Attribute")

    # Explicitly reject Import nodes.
    def visit_Import(self, node: ast.Import) -> None:
        raise ValueError("Explicitly rejected node type: Import")

    # Explicitly reject ImportFrom nodes.
    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        raise ValueError("Explicitly rejected node type: ImportFrom")

    # Visit and validate Name nodes for dangerous identifiers.
    def visit_Name(self, node: ast.Name) -> None:
        # Check for builtins or dunder identifiers.
        if node.id == "__builtins__" or "__builtins__" in node.id:
            raise ValueError("Explicitly rejected identifier: __builtins__")
        # Increment node count without traversing ctx.
        self.node_count += 1

    # Visit Constant literal nodes.
    def visit_Constant(self, node: ast.Constant) -> None:
        # Increment node count for constant literals.
        self.node_count += 1

# Parse string expression, validate zero-trust whitelist, and return node count.
def count_nodes(expr: str) -> int:
    # Parse source string into AST.
    tree = ast.parse(expr)
    # Instantiate zero-trust visitor.
    visitor = ZeroTrustAST()
    # Walk and validate all nodes in AST.
    visitor.visit(tree)
    # Return total baseline AST node count.
    return visitor.node_count

if __name__ == "__main__":
    # Test 1: Valid Mixed Boolean-Arithmetic (MBA) expression.
    valid_expr = "(x ^ y) + 2 * (x & y)"
    valid_count = count_nodes(valid_expr)
    print(f"Valid expression node count: {valid_count}")

    # Test 2: Malicious code injection expression.
    malicious_expr = "__import__('os').system('ls')"
    try:
        count_nodes(malicious_expr)
        print("Error: Malicious expression was not rejected")
    except ValueError:
        print("Rejected as expected")
