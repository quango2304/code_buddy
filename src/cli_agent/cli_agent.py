from src.mcp.mcp_tools import cleanup_mcp_connections
from src.model import create_model, load_system_prompt
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, \
    SystemMessage, BaseMessage
from langchain_core.tools.base import BaseTool

from src.tools.tool import execute_tool, get_all_tools


async def run_cli_agent():
    """Run the main agent loop."""
    system_prompt = load_system_prompt()
    # Initialize the model and tools
    tools: list[BaseTool] = await get_all_tools()
    model = create_model().bind_tools(tools)

    # Add system prompt as the first message
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

    print("Agent ready. Type 'quit' to exit.")

    try:
        while True:
            # Get user input
            print(f"{"---" * 20}")
            user_input = input("[You]: ").strip()

            # Check for exit condition
            if user_input.lower() == "quit":
                print("Goodbye!")
                break

            if not user_input:
                continue

            # Append the user message to history
            messages.append(HumanMessage(content=user_input))

            while True:
                response: AIMessage = await model.ainvoke(messages)
                messages.append(response)
                # Check if there are tool calls to handle
                if response.tool_calls:
                    # print the thinking blocks
                    _print_agent_text_output(response)
                    # Execute each tool call
                    for tool_call in response.tool_calls:
                        result = await execute_tool(tools, tool_call)
                        tool_message = ToolMessage(
                            content=result,
                            tool_call_id=tool_call["id"],
                        )
                        messages.append(tool_message)
                else:
                    # No more tool calls - print the text response and break
                    _print_agent_text_output(response)
                    break
    finally:
        await cleanup_mcp_connections()


def _print_agent_text_output(response: AIMessage):
    """Print reasoning blocks from extended thinking if present."""
    print(f"{"---" * 20}")
    if hasattr(response, 'content_blocks'):
        for block in response.content_blocks:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                print(f"[Thinking]: {block['reasoning']}")
            if isinstance(block, dict) and block.get("type") == "text":
                print(f"[Agent]: {block['text']}\n")
    else:
        print(f"Empty response")
