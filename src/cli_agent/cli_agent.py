from src.model import create_model, load_system_prompt
import asyncio

from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage, BaseMessage


async def run_agent_loop():
    """Run the main agent loop."""
    system_prompt = load_system_prompt()
    model = create_model()
    messages: list[BaseMessage] = [SystemMessage(content=system_prompt)]

    print("Agent ready.\n")

    while True:
        # 1. Get user input
        user_input = input("[You]: ").strip()
        # 2. Append user message to history
        messages.append(HumanMessage(content=user_input))
        # 3. Send entire history to LLM and get response
        response: AIMessage = await model.ainvoke(messages)
        # 4. Append LLM response to history (this is how context is maintained!)
        messages.append(response)
        # 5. Display the response
        _print_agent_text_output(response)


def _print_agent_text_output(response: AIMessage):
    """Print reasoning blocks from extended thinking if present."""
    if hasattr(response, 'content_blocks'):
        for block in response.content_blocks:
            print(f"\n{"---"*10}")
            if isinstance(block, dict) and block.get("type") == "reasoning":
                print(f"\n[Thinking]: {block['reasoning']}")
            if isinstance(block, dict) and block.get("type") == "text":
                print(f"\n[Agent]: {block['text']}\n")
        print(f"{"---" * 10}")
