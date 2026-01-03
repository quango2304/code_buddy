# Code Buddy

A minimal, production-ready coding agent built with LangChain for learning purposes.

## Tools

The agent has access to the following tools:

**File Operations:**
- `read_file` - Read the content of a file
- `write_file` - Write content to a file (create or overwrite)
- `copy_file` - Copy a file to a new location
- `move_file` - Move a file to a new location
- `file_delete` - Delete a file
- `list_directory` - List files and subdirectories in a directory
- `file_search` - Recursively search for files matching a pattern
- `replace_file_content` - Replace a single contiguous block of content in a file

**Command Execution:**
- `run_command` - Execute shell commands (supports foreground and background modes)
- `read_command_output` - Read output from a background command using its process ID
- `send_command_input` - Send input to a running background command or terminate it

**Search:**
- `grep_search` - Search for patterns in files using grep

## Quick Start

1. **Setup environment**
   ```bash
   cp .env.example .env
   # Add your config based on AI_PROVIDER setting
   ```

2. **Run the agent**
   ```bash
   uv sync
   uv run python -m src.main
   ```
   
## Install the CLI
Follow below steps to install the agent in editable mode and add an alias to your shell config, so you can run it from anywhere using `code-buddy` commnad
```bash
# Install in editable mode
uv pip install -e .

# Add alias to your shell config (~/.zshrc or ~/.bashrc)
alias coding-buddy='<project_absolute_path>/.venv/bin/code-buddy'
```

## MCP (Model Context Protocol) Support

Code Buddy supports [MCP](http://modelcontextprotocol.io) servers to extend the agent's capabilities with additional tools.

### Configuration Locations

MCP servers are loaded from two locations (in order):

1. **Default servers**: `src/mcp/default_mcp_servers.json` (bundled with the package)
2. **Project-specific servers**: `.code-buddy/mcp_servers.json` (in your current working directory)

### Configuration Format

Create a `mcp_servers.json` file with the following structure:

#### Stdio Server (Local)

```json
{
    "mcpServers": {
        "my-local-server": {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/dir"],
            "env": {
                "OPTIONAL_ENV_VAR": "value"
            }
        }
    }
}
```

#### Remote Server (HTTP)

```json
{
    "mcpServers": {
        "my-remote-server": {
            "url": "https://mcp.example.com/sse",
            "headers": {
                "Authorization": "Bearer your-api-key"
            }
        }
    }
}
```

### Default MCP Servers

The following MCP servers are included by default:

```json
{
    "mcpServers": {
        "auggie": {
            "command": "auggie",
            "args": ["--mcp"]
        }
    }
}
```

> **Note:** For the Auggie MCP server to work, you need to install and authenticate first:
> ```bash
> npm install -g auggie
> auggie login
> ```

### Adding Project-Specific Servers

1. Create the config directory:
   ```bash
   mkdir -p .code-buddy
   ```

2. Create `.code-buddy/mcp_servers.json`:
   ```json
   {
       "mcpServers": {
           "your-server": {
               "command": "your-command",
               "args": ["--your-args"]
           }
       }
   }
   ```

3. Restart the agent to load the new configuration.

## Roadmap

1. Simple agent CLI loop – ✅ done
2. Tools (file operations, command execution, search) – ✅ done
3. MCP support with configurable settings – ✅ done
4. ACP support for IDE integration (http://agentclientprotocol.com)
5. Prompt compression for long-running contexts 
6. Memory, rules, and task management