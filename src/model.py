"""Shared model and prompt utilities."""
import os
from pathlib import Path

from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.language_models.chat_models import BaseChatModel


def create_model() -> BaseChatModel:
    """Create and return the LangChain chat model based on AI_PROVIDER env."""
    provider = os.getenv("AI_PROVIDER", "anthropic").lower()

    if provider == "gemini":
        return ChatGoogleGenerativeAI(
            model=os.getenv("GEMINI_MODEL"),
            api_key=os.getenv("GOOGLE_API_KEY"),
            client_options={"api_endpoint": os.getenv("GEMINI_BASE_URL")} if os.getenv("GEMINI_BASE_URL") else None,
            thinking_budget=5000
        )
    elif provider == "anthropic":
        return ChatAnthropic(
            model_name=os.getenv("CLAUDE_MODEL"),
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            base_url=os.getenv("ANTHROPIC_BASE_URL"),
            max_tokens_to_sample=16000,
            thinking={
                "type": "enabled",
                "budget_tokens": 5000
            }
        )
    raise ValueError(f"Unsupported AI provider: {provider}")


def load_system_prompt() -> str:
    """Load system prompt from markdown file."""
    prompt_path = Path(__file__).parent / "prompt" / "system_prompt.md"
    return prompt_path.read_text()
