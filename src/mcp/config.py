"""MCP server configuration loading."""
import json
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Optional


@dataclass
class McpServerConfig:
    """Configuration for a single MCP server."""
    name: str
    server_type: str  # "stdio" or "remote"
    command: Optional[str] = None
    args: Optional[list[str]] = None
    env: Optional[dict[str, str]] = None
    url: Optional[str] = None  # For remote servers
    headers: Optional[dict[str, str]] = None  # For remote servers


def load_mcp_configs() -> list[McpServerConfig]:
    """Load MCP server configs from both package and project locations."""
    configs = []

    # Load from package mcp folder
    package_config_path = Path(__file__).parent / "default_mcp_servers.json"
    configs.extend(_load_and_parse_config_file(package_config_path))

    # Load from .coding-agent folder in current working directory
    project_config_path = Path(
        os.getcwd()) / ".code-buddy" / "mcp_servers.json"
    configs.extend(_load_and_parse_config_file(project_config_path))

    return configs


def _load_and_parse_config_file(config_path: Path) -> list[McpServerConfig]:
    """Load configs from a single config file."""
    configs = []

    if not config_path.exists():
        return configs

    with open(config_path, "r") as f:
        data = json.load(f)

    mcp_servers = data.get("mcpServers", {})

    for name, server_config in mcp_servers.items():
        config = _parse_server_config(name, server_config)
        if config:
            configs.append(config)

    return configs


def _parse_server_config(name: str, server_config: dict) -> Optional[
    McpServerConfig]:
    """Parse a single server configuration."""
    # Check if remote server (has url)
    if "url" in server_config:
        return McpServerConfig(
            name=name,
            server_type="remote",
            url=server_config["url"],
            env=server_config.get("env"),
            headers=server_config.get("headers"),
        )

    # Check if stdio server (has command)
    if "command" in server_config:
        return McpServerConfig(
            name=name,
            server_type="stdio",
            command=server_config["command"],
            args=server_config.get("args", []),
            env=server_config.get("env"),
        )

    print(
        f"Warning: Invalid MCP server config for '{name}': missing 'command' or 'url'")
    return None
