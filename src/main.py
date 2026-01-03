import argparse
import asyncio

from dotenv import load_dotenv

from src.acp.acp_agent import run_acp_agent
from src.cli_agent.cli_agent import run_cli_agent


def main():
    # Load environment variables
    load_dotenv(override=True)

    # Check if should run in ACP mode
    parser = argparse.ArgumentParser(description="Coding Agent")
    parser.add_argument(
        "--acp",
        action="store_true",
        help="Run in ACP (Agent Client Protocol) mode instead of CLI mode"
    )
    args = parser.parse_args()

    if args.acp:
        asyncio.run(run_acp_agent())
    else:
        asyncio.run(run_cli_agent())

if __name__ == "__main__":
    main()
