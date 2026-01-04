"""Prompt compaction utility for managing context window limits.

When the conversation history approaches the context window limit,
this module compacts older messages into a summary while preserving
the system prompt and recent messages.
"""
from pathlib import Path
from typing import Optional
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import (
    BaseMessage,
    SystemMessage,
    HumanMessage,
)

from src.model import create_model

# Threshold at which to trigger compaction (80% of context window)
COMPACTION_THRESHOLD = 0.8

# Number of recent messages to preserve (excluding system message)
RECENT_MESSAGES_TO_KEEP = 10


async def _generate_summary(
    messages_to_summarize: list[BaseMessage], 
) -> str:
    """Generate a summary of the given messages.
    
    The summary captures:
    - Key decisions made
    - Important context established
    - Files/resources discussed
    - Actions taken

    Returns:
        A summary string of the conversation.
    """
    if not messages_to_summarize:
        return ""
    
    # Create a summarization prompt
    conversation_text = "\n\n".join(
        f"[{msg.__class__.__name__}]: {msg.content}" 
        for msg in messages_to_summarize
    )
    
    # Load prompt template from file
    prompt_path = Path(__file__).parent.parent / "prompt" / "compaction_prompt.md"
    prompt_template = prompt_path.read_text()
    summary_prompt = prompt_template.replace("{conversation_text}", conversation_text)

    # Use the same model to generate the summary
    model = create_model()
    
    try:
        response = await model.ainvoke([HumanMessage(content=summary_prompt)])
        return str(response.content)
    except Exception as e:
        # If summarization fails, create a basic summary
        return f"[Previous conversation with {len(messages_to_summarize)} messages - summarization failed: {e}]"


async def compact_messages_if_needed(
    messages: list[BaseMessage],
    current_input_tokens: int,
    threshold: float = COMPACTION_THRESHOLD,
    recent_count: int = RECENT_MESSAGES_TO_KEEP,
) -> list[BaseMessage]:
    """Compact messages if approaching the context window limit.
    Returns:
        compacted_messages: The (potentially) compacted list of messages
    """
    # For simple, we set claude model max token is 200_000, and gemini to 1_000_000
    model = create_model()
    max_token = 200_000
    if isinstance(model, ChatGoogleGenerativeAI):
        max_token = 1_000_000
    if isinstance(model, ChatAnthropic):
        max_token = 200_000
    
    if len(messages) <= recent_count + 1:
        # Not enough messages to compact
        return messages
    
    # Calculate the threshold (80% of 200k = 160k tokens)
    token_limit = int(max_token * threshold)
    
    if current_input_tokens < token_limit:
        # Still under the limit, no compaction needed
        return messages
    
    # Compaction is needed
    # Extract system message (should be first)
    system_message: Optional[SystemMessage] = None
    remaining_messages = messages
    
    if messages and isinstance(messages[0], SystemMessage):
        system_message = messages[0]
        remaining_messages = messages[1:]
    
    if len(remaining_messages) <= recent_count:
        # Not enough non-system messages to compact
        return messages
    
    # Split into messages to summarize and recent messages to keep
    messages_to_summarize = remaining_messages[:-recent_count]
    recent_messages = remaining_messages[-recent_count:]
    
    # Generate summary
    summary = await _generate_summary(messages_to_summarize)
    
    # Create the summary message as a SystemMessage with context
    summary_message = SystemMessage(
        content=f"[CONVERSATION SUMMARY - Previous {len(messages_to_summarize)} messages]\n\n{summary}"
    )
    
    # Reconstruct the message list
    compacted_messages: list[BaseMessage] = []
    
    if system_message:
        compacted_messages.append(system_message)
    
    compacted_messages.append(summary_message)
    compacted_messages.extend(recent_messages)
    
    print("Prompt compaction: Compacted messages")
    return compacted_messages
