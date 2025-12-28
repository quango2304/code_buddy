# Code Buddy

A minimal, production-ready coding agent built with LangChain for learning purposes.

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

1. Simple agent CLI loop - done
2. Tools (file operations, command execution, search)
3. MCP support with configurable settings (http://modelcontextprotocol.io)
4. ACP support for IDE integration (http://agentclientprotocol.com)
5. Prompt compression for long-running contexts 
6. Memory, rules, and task management