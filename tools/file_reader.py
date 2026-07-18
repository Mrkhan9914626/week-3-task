import os
from agents import function_tool

# Maximum lines to read from a file
_MAX_LINES = 5000

# Allowed directory — restrict file access for safety
_ALLOWED_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def _is_path_safe(file_path: str) -> bool:
    """Check if the file path is within the allowed directory."""
    resolved = os.path.abspath(os.path.normpath(file_path))
    return resolved.startswith(_ALLOWED_DIR) and os.path.isfile(resolved)


@function_tool
def read_file(
    file_path: str,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    """
    Read the contents of a file from the project directory.

    Args:
        file_path: Path to the file (relative or absolute within the project).
        start_line: Optional line number to start reading from (1-indexed).
        end_line: Optional line number to stop reading at (1-indexed, inclusive).

    Returns:
        The file contents as a string, or an error message.
    """
    if not file_path:
        return "Error: No file path provided."

    # Resolve path
    abs_path = os.path.abspath(
        os.path.join(_ALLOWED_DIR, file_path)
        if not os.path.isabs(file_path)
        else file_path
    )

    if not _is_path_safe(abs_path):
        return (
            f"Error: Access denied. File must be within the project directory "
            f"({_ALLOWED_DIR})."
        )

    try:
        with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Apply line range
        if start_line is not None or end_line is not None:
            s = max(0, (start_line or 1) - 1)
            e = min(total_lines, end_line or total_lines)
            lines = lines[s:e]
            label = f" (lines {s + 1}-{e} of {total_lines})"
        else:
            label = f" ({total_lines} lines total)"

        # Truncate if too many lines
        if len(lines) > _MAX_LINES:
            lines = lines[:_MAX_LINES]
            label += f" — truncated to first {_MAX_LINES} lines"

        content = "".join(lines)
        return f"File: {os.path.relpath(abs_path, _ALLOWED_DIR)}{label}\n\n```\n{content}```"

    except FileNotFoundError:
        return f"Error: File not found at '{file_path}'."
    except PermissionError:
        return f"Error: Permission denied reading '{file_path}'."
    except IsADirectoryError:
        return f"Error: '{file_path}' is a directory, not a file."
    except Exception as e:
        return f"Error reading file: {str(e)}"
