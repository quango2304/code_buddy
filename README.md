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
alias coding-agent='<project_absolute_path>/.venv/bin/code-buddy'
```

## Roadmap

1. Simple agent CLI loop – ✅ done
2. Tools (file operations, command execution, search) – ✅ done
3. MCP support with configurable settings (http://modelcontextprotocol.io)
4. ACP support for IDE integration (http://agentclientprotocol.com)
5. Prompt compression for long-running contexts 
6. Memory, rules, and task management