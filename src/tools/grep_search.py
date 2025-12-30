import subprocess
from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

# Root directory for file operations (where python command is executed)
ROOT_DIR = Path.cwd()


@tool
def grep_search(
    pattern: Annotated[str, "The regex pattern to search for"],
    path: Annotated[str, "The file or directory path to search in (relative to project root)"] = ".",
    case_insensitive: Annotated[bool, "If True, perform case-insensitive search"] = False,
) -> str:
    """Search for a pattern in files using grep.

    Returns:
        Matching lines with file names and line numbers.
    """
    search_path = ROOT_DIR / path

    if not search_path.exists():
        return f"Error: Path '{path}' does not exist"

    cmd = ["grep", "-rn"]
    if case_insensitive:
        cmd.append("-i")
    cmd.extend([pattern, str(search_path)])

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return result.stdout or "No matches found"
        elif result.returncode == 1:
            return "No matches found"
        else:
            return f"Error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Error: Search timed out"
    except Exception as e:
        return f"Error: {str(e)}"
