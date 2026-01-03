"""MCP client connection management."""
from dataclasses import dataclass
from typing import Optional

import httpx
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.client.streamable_http import streamable_http_client
from contextlib import AsyncExitStack
from src.mcp.config import McpServerConfig


@dataclass
class McpConnection:
    """Active MCP server connection."""
    name: str
    session: ClientSession


class McpClientManager:
    """Manages connections to multiple MCP servers."""

    def __init__(self):
        self._connections: list[McpConnection] = []
        self._exit_stacks: list = []

    async def _connect(self, config: McpServerConfig) -> Optional[
        McpConnection]:
        """Connect to a single MCP server."""
        try:
            if config.server_type == "stdio":
                return await self._connect_stdio(config)
            elif config.server_type == "remote":
                return await self._connect_remote(config)
            else:
                print(f"Unknown server type: {config.server_type}")
                return None
        except Exception as e:
            print(f"Failed to connect to MCP server '{config.name}': {e}")
            return None

    async def _connect_stdio(self, config: McpServerConfig) -> McpConnection:
        """Connect to a stdio-based MCP server."""
        server_params = StdioServerParameters(
            command=config.command,
            args=config.args or [],
            env=config.env,
        )

        # AsyncExitStack - we need to keep connections alive beyond this
        # function's scope (for the agent's lifetime), so we manually enter
        # the context and store the stack for later cleanup in disconnect_all().
        stack = AsyncExitStack()
        await stack.__aenter__()
        self._exit_stacks.append(stack)

        read, write = await stack.enter_async_context(
            stdio_client(server_params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        connection = McpConnection(name=config.name, session=session)
        self._connections.append(connection)

        print(f"Connected to MCP server: {config.name}")
        return connection

    async def _connect_remote(self, config: McpServerConfig) -> McpConnection:
        """Connect to a remote MCP server via HTTP."""

        # AsyncExitStack - we need to keep connections alive beyond this
        # function's scope (for the agent's lifetime), so we manually enter
        # the context and store the stack for later cleanup in disconnect_all().
        stack = AsyncExitStack()
        await stack.__aenter__()
        self._exit_stacks.append(stack)

        # Create httpx client with your custom headers/auth
        client = httpx.AsyncClient(
            headers=config.headers,
            timeout=httpx.Timeout(30.0, read=300.0),
        )
        read, write, _ = await stack.enter_async_context(
            streamable_http_client(config.url, http_client=client)
        )
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()

        connection = McpConnection(name=config.name, session=session)
        self._connections.append(connection)

        print(f"Connected to remote MCP server: {config.name}")
        return connection

    async def connect_all(self, configs: list[McpServerConfig]) -> list[
        McpConnection]:
        """Connect to all configured MCP servers."""
        connections = []
        for config in configs:
            connection = await self._connect(config)
            if connection:
                connections.append(connection)
        return connections

    def get_connections(self) -> list[McpConnection]:
        """Get all active connections."""
        return self._connections

    async def disconnect_all(self):
        """Disconnect from all MCP servers."""
        for stack in reversed(self._exit_stacks):
            try:
                await stack.__aexit__(None, None, None)
            except Exception as e:
                print(f"Error disconnecting: {e}")

        self._connections.clear()
        self._exit_stacks.clear()


# Global client manager instance
client_manager = McpClientManager()
