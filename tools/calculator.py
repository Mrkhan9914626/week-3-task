import ast
import math
import operator
from agents import function_tool


# Whitelist of safe operators
_SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


# Whitelist of allowed functions (math module)
_SAFE_FUNCTIONS = {
    "abs": abs,
    "round": round,
    "min": min,
    "max": max,
    "sum": sum,
    "int": int,
    "float": float,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "pi": math.pi,
    "e": math.e,
    "degrees": math.degrees,
    "radians": math.radians,
}


def _safe_eval(expr: str) -> str:
    """Safely evaluate a mathematical expression using AST parsing."""
    # Replace common math notation
    expr = expr.strip()

    try:
        tree = ast.parse(expr, mode="eval")
    except SyntaxError:
        raise ValueError("Invalid mathematical expression")

    return _eval_node(tree.body)


def _eval_node(node) -> float:
    """Recursively evaluate an AST node with only safe operations allowed."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Unsupported constant: {type(node.value).__name__}")

    elif isinstance(node, ast.UnaryOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.operand))

    elif isinstance(node, ast.BinOp):
        op = _SAFE_OPERATORS.get(type(node.op))
        if op is None:
            raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
        return op(_eval_node(node.left), _eval_node(node.right))

    elif isinstance(node, ast.Call):
        func_name = _get_func_name(node.func)
        if func_name is None:
            raise ValueError(f"Unsupported function call syntax")
        func = _SAFE_FUNCTIONS.get(func_name)
        if func is None:
            raise ValueError(f"Unsupported function: {func_name}")
        args = [_eval_node(arg) for arg in node.args]
        try:
            return func(*args)
        except Exception as e:
            raise ValueError(f"Error calling {func_name}: {str(e)}")

    elif isinstance(node, ast.Name):
        # Allow constants like pi, e
        constant = _SAFE_FUNCTIONS.get(node.id)
        if isinstance(constant, (int, float)):
            return constant
        raise ValueError(f"Unknown variable or constant: {node.id}")

    else:
        raise ValueError(f"Unsupported expression type: {type(node).__name__}")


def _get_func_name(node) -> str | None:
    """Extract the function name from a Call node."""
    if isinstance(node, ast.Name):
        return node.id
    return None


@function_tool
def calculator(expression: str) -> str:
    """
    Evaluate a mathematical expression safely.

    Supports: +, -, *, /, //, %, **, and functions like sqrt(),
    sin(), cos(), tan(), log(), log10(), exp(), abs(), round(), min(), max().
    Also supports the constants pi and e.

    Args:
        expression: The math expression to evaluate, e.g. "2 + 3 * 4" or
                    "sqrt(144)" or "sin(pi / 2)".

    Returns:
        The calculated result as a string, or an error message.
    """
    try:
        result = _safe_eval(expression)
        # Format cleanly: int if whole number, else reasonable precision
        if isinstance(result, float):
            if result == int(result):
                result_formatted = str(int(result))
            else:
                result_formatted = f"{result:.10g}"
        else:
            result_formatted = str(result)

        return f"{expression} = {result_formatted}"
    except (ValueError, ZeroDivisionError) as e:
        return f"Error: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"
