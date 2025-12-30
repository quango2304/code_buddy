from pathlib import Path
from typing import Annotated

from langchain_core.tools import tool

# Root directory for file operations
ROOT_DIR = Path.cwd()


@tool
def replace_file_content(
        target_file: Annotated[str, "Relative path to the file to edit"],
        start_line: Annotated[
            int, "Starting line number (1-indexed) to search within"],
        end_line: Annotated[
            int, "Ending line number (1-indexed, inclusive) to search within"],
        target_content: Annotated[
            str, "Exact text to replace (must match exactly, including whitespace)"],
        replacement_content: Annotated[
            str, "New content to replace the target with"],
        allow_multiple: Annotated[
            bool, "If True, replace all occurrences; if False, error on multiple matches"] = False,
) -> str:
    """Replace a single contiguous block of content in a file.

    Use this tool when making ONE contiguous block of edits to a file.
    For multiple non-adjacent edits, use multi_replace_file_content instead.

    Returns:
        Success message or error description.
    """
    file_path = ROOT_DIR / target_file

    if not file_path.exists():
        return f"Error: File '{target_file}' does not exist"

    if not file_path.is_file():
        return f"Error: '{target_file}' is not a file"

    # Validate line numbers
    if start_line < 1:
        return f"Error: start_line must be >= 1, got {start_line}"

    if end_line < start_line:
        return f"Error: end_line ({end_line}) must be >= start_line ({start_line})"

    try:
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines(keepends=True)
        total_lines = len(lines)

        if start_line > total_lines:
            return f"Error: start_line ({start_line}) exceeds file length ({total_lines} lines)"

        if end_line > total_lines:
            return f"Error: end_line ({end_line}) exceeds file length ({total_lines} lines)"

        # Extract the search region (convert to 0-indexed)
        search_region = "".join(lines[start_line - 1: end_line])

        # Count occurrences in the search region
        occurrences = search_region.count(target_content)

        if occurrences == 0:
            return f"Error: Target content not found in lines {start_line}-{end_line}"

        if occurrences > 1 and not allow_multiple:
            return (
                f"Error: Found {occurrences} occurrences of target content. "
                f"Set allow_multiple=True to replace all, or narrow the search range."
            )

        # Perform replacement in the search region
        new_region = search_region.replace(target_content, replacement_content)

        # Reconstruct the file
        before = "".join(lines[: start_line - 1])
        after = "".join(lines[end_line:])
        new_content = before + new_region + after

        # Write back
        file_path.write_text(new_content, encoding="utf-8")

        replaced_count = occurrences if allow_multiple else 1
        return f"Successfully replaced {replaced_count} occurrence(s) in '{target_file}'"

    except Exception as e:
        return f"Error: {str(e)}"
