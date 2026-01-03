"""Convert MCP tools to LangChain tools."""

from langchain_core.tools import StructuredTool
from langchain_mcp_adapters.tools import load_mcp_tools

from src.mcp.client import McpConnection, client_manager
from src.mcp.config import load_mcp_configs
from langchain_core.tools.base import BaseTool

async def get_mcp_tools() -> list[StructuredTool]:
    """Get all tools from connected MCP servers as LangChain tools."""
    print("Loading mcp tools...")
    tools = []

    # Load configs and connect to servers
    configs = load_mcp_configs()

    await client_manager.connect_all(configs)

    # Get tools from each connection
    for connection in client_manager.get_connections():
        connection_tools = await _get_tools_from_connection(connection)
        tools.extend(connection_tools)

    return tools


async def _get_tools_from_connection(connection: McpConnection) -> list[BaseTool]:
    """Get tools from a single MCP connection and convert to LangChain tools."""
    try:
        # Load available tools from the server
        tools = await load_mcp_tools(connection.session)

        # Prefix tool names with connection name to avoid collisions
        for tool in tools:
            tool.name = f"{connection.name}_{tool.name}"

        return tools

    except Exception as e:
        print(f"Error getting tools from '{connection.name}': {e}")
        return []


async def cleanup_mcp_connections():
    """Cleanup all MCP connections."""
    await client_manager.disconnect_all()
