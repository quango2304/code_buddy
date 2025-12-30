from langchain_core.messages import ToolCall
from langchain_core.tools.base import BaseTool

from src.tools.command_tools import run_command, \
    read_command_output, send_command_input
from src.tools.grep_search import grep_search
from src.tools.langchain_tools import get_langchain_tools
from src.tools.replace_file_content import replace_file_content


async def get_all_tools() -> list[BaseTool]:
    """Get all available tools from all sources."""
    tools: list[BaseTool] = [
        run_command,
        read_command_output,
        send_command_input,
        replace_file_content,
        grep_search,
        *get_langchain_tools(),
    ]
    return tools

async def execute_tool(tools: list[BaseTool], tool_call: ToolCall) -> str:
    """Execute a tool call and return the result."""
    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    truncated_args = _truncate_args_for_print(tool_args)
    print(f"Executing tool: {tool_name}, tool_args: {truncated_args}")

    # Find the tool by name
    tool = next((t for t in tools if t.name == tool_name), None)

    if tool is None:
        return f"Error: Unknown tool '{tool_name}'"

    # Execute the tool and return the result
    try:
        result = await tool.ainvoke(tool_args)
        print(f"\n📦 Tool result:\n{result[:100]}...")
        return str(result)
    except Exception as e:
        print(f"Error executing tool '{tool_name}': {str(e)}")
        return f"Error: {str(e)}"


def _truncate_args_for_print(args: dict, max_length: int = 100) -> dict:
    """Truncate long string values in args for printing purposes."""
    truncated = {}
    for key, value in args.items():
        if isinstance(value, str) and len(value) > max_length:
            truncated[key] = value[:max_length] + "..."
        elif isinstance(value, list):
            truncated[key] = [
                (v[:max_length] + "..." if isinstance(v, str) and len(
                    v) > max_length else v)
                for v in value
            ]
        elif isinstance(value, dict):
            truncated[key] = _truncate_args_for_print(value, max_length)
        else:
            truncated[key] = value
    return truncated
