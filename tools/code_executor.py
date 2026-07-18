import subprocess
import sys
import textwrap
from agents import function_tool

# Timeout for code execution (seconds)
_TIMEOUT = 15

# Maximum output characters
_MAX_OUTPUT = 3000

# Restricted imports available in the sandbox
_ALLOWED_IMPORTS = [
    "math", "json", "random", "datetime", "collections",
    "itertools", "statistics", "string", "re",
]


def _build_sandbox_code(user_code: str) -> str:
    """Wrap user code in a sandbox with restricted imports and globals."""
    allowed_imports_str = ", ".join(repr(m) for m in _ALLOWED_IMPORTS)

    wrapper = textwrap.dedent(f"""
import builtins

# Restrict dangerous builtins
_safe_builtins = {{}}
for _name in ("print", "len", "range", "int", "float", "str", "bool",
              "list", "dict", "tuple", "set", "type", "True", "False",
              "None", "abs", "min", "max", "sum", "round", "sorted",
              "reversed", "enumerate", "zip", "map", "filter", "any", "all",
              "isinstance", "hasattr", "getattr", "setattr", "repr", "format",
              "Exception", "ValueError", "TypeError", "KeyError",
              "IndexError", "RuntimeError", "StopIteration", "ZeroDivisionError",
              "ArithmeticError", "OverflowError"):
    _safe_builtins[_name] = getattr(builtins, _name, None)

# Whitelisted modules
_allowed_modules = [{allowed_imports_str}]
for _mod_name in _allowed_modules:
    try:
        _safe_builtins[_mod_name] = __import__(_mod_name)
    except ImportError:
        pass

# Allow specific imports
_import_safe_modules = {allowed_imports_str}

_globals = {{"_builtins": _safe_builtins, "__builtins__": _safe_builtins}}
_locals = {{}}

# Execute the user code
exec(compile({repr(user_code)}, "<user_code>", "exec"), _globals, _locals)
""")

    return wrapper


@function_tool
def execute_code(code: str) -> str:
    """
    Execute Python code in a sandboxed environment and return the output.

    The sandbox provides access to these modules: math, json, random, datetime,
    collections, itertools, statistics, string, re. Standard print() captures
    output. Code is limited to 15 seconds execution time.

    Args:
        code: Python code to execute as a string.

    Returns:
        Captured stdout/stderr output, or an error message.
    """
    sandbox_code = _build_sandbox_code(code)

    try:
        # Use isolated env — preserve only essential paths for stdlib access
        safe_env = {
            "PYTHONPATH": "",
            "PYTHONHASHSEED": "0",
        }
        result = subprocess.run(
            [sys.executable, "-I", "-c", sandbox_code],
            capture_output=True,
            text=True,
            timeout=_TIMEOUT,
            env=safe_env,
        )

        output_parts = []

        if result.stdout:
            output_parts.append(result.stdout.rstrip())
        if result.stderr:
            output_parts.append(f"Stderr:\n{result.stderr.rstrip()}")

        combined = "\n".join(output_parts)

        if not combined.strip():
            combined = "(Code executed successfully with no output.)"

        if len(combined) > _MAX_OUTPUT:
            combined = combined[:_MAX_OUTPUT] + (
                f"\n... (truncated, {len(combined)} total chars)"
            )

        return combined

    except subprocess.TimeoutExpired:
        return (
            f"Error: Code execution timed out after {_TIMEOUT} seconds. "
            f"The sandbox environment may be too restrictive."
        )
    except Exception as e:
        return f"Error executing code: {str(e)}"
