import asyncio

from dotenv import load_dotenv

from src.cli_agent.cli_agent import run_agent_loop


def main():
    # Load environment variables
    load_dotenv(override=True)
    # Run the agent
    asyncio.run(run_agent_loop())

if __name__ == "__main__":
    main()
