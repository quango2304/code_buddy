"""ACP Agent implementation using the official SDK."""
import os
import uuid

import acp
from acp import Agent, Client
from acp.schema import (
    InitializeResponse,
    NewSessionResponse,
    PromptResponse,
    ClientCapabilities,
    Implementation,
    TextContentBlock,
    ImageContentBlock,
    AudioContentBlock,
    ResourceContentBlock,
    EmbeddedResourceContentBlock,
    ToolCallStart,
    ToolCallProgress,
    AgentMessageChunk,
    ContentToolCallContent,
    AgentThoughtChunk,
)
from langchain_core.messages import AIMessage

from src.acp.session import SessionManager
from src.model import create_model, load_system_prompt
from src.utils.prompt_compaction import compact_messages_if_needed
from src.tools.tool import get_all_tools, execute_tool
from src.mcp.mcp_tools import cleanup_mcp_connections
import sys
from langchain_core.messages import ToolCall


class ACPAgent(Agent):
    """
    Coding Agent implementation using the ACP SDK.
    
    This agent handles coding tasks with tool calling capabilities.
    The SDK handles all JSON-RPC transport automatically.
    """

    def __init__(self):
        self.conn: Client | None = None
        self.session_manager = SessionManager()
        self._tools = None  # Lazy-loaded tools

    def on_connect(self, conn: Client) -> None:
        """Called when client connects - store connection for sending updates."""
        self.conn = conn

    async def initialize(
            self,
            protocol_version: int,
            client_capabilities: ClientCapabilities | None = None,
            client_info: Implementation | None = None,
            **kwargs
    ) -> InitializeResponse:
        """
        Handle agent/initialize request.

        Negotiates protocol version and exchanges capability information.
        """
        return InitializeResponse(
            protocol_version=1,
            agent_capabilities=acp.schema.AgentCapabilities(
                load_session=False,  # Set to True if you implement session persistence
                prompt_capabilities=acp.schema.PromptCapabilities(
                    audio=False,
                    embedded_context=False,
                    image=False
                ),
            ),
            agent_info=Implementation(
                name="code-buddy",
                version="1.0.0",
                title="Coding Buddy Agent",
            )
        )

    async def new_session(
            self,
            cwd: str,
            mcp_servers: list = None,
            **kwargs
    ) -> NewSessionResponse:
        """
        Handle session/new request.

        Creates a new conversation session with the agent.
        """
        session_id = kwargs.get("session_id")
        session = self.session_manager.create_session(cwd=cwd,
                                                      session_id=session_id)

        # Initialize with system prompt
        session.add_system_message(load_system_prompt())
        model_id = ""
        if os.getenv("AI_PROVIDER") == "gemini":
            model_id = os.getenv("GEMINI_MODEL")
        elif os.getenv("AI_PROVIDER") == "anthropic":
            model_id = os.getenv("CLAUDE_MODEL")

        return NewSessionResponse(
            session_id=session.session_id,
            modes=acp.schema.SessionModeState(
                current_mode_id="auto",
                available_modes=[
                    acp.schema.SessionMode(
                        id="auto",
                        name="Auto",
                        description="Autonomous coding agent mode"
                    )
                ]
            ),
            models=acp.schema.SessionModelState(
                current_model_id=model_id,
                available_models=[
                    acp.schema.ModelInfo(
                        model_id=model_id,
                        name=model_id,
                    )
                ]
            )
        )

    async def cancel(self, session_id: str, **kwargs) -> None:
        """
        Handle session/cancel notification.

        Cancels ongoing operations for a session.
        """
        session = self.session_manager.get_session(session_id)
        if session is not None:
            session.cancel()

    async def prompt(
            self,
            prompt: list[
                TextContentBlock | ImageContentBlock | AudioContentBlock |
                ResourceContentBlock | EmbeddedResourceContentBlock
                ],
            session_id: str,
            **kwargs
    ) -> PromptResponse:
        """
        Handle session/prompt request.

        Receives user message and processes through the agent.
        Uses conn.session_update() to stream progress notifications.
        """
        session = self.session_manager.get_session(session_id)
        if session is None:
            raise ValueError(f"Session not found: {session_id}")

        # Reset cancellation flag for new prompt turn
        session.reset_cancellation()

        # Extract user text from prompt content
        user_text = self._extract_prompt_content(prompt)
        session.add_user_message(user_text)

        # Get tools and model
        tools = await self._get_tools()
        model = create_model().bind_tools(tools)

        # Agent loop - may include multiple tool calls
        while True:
            # Check for cancellation before making LLM request
            if session.is_cancelled():
                return PromptResponse(stop_reason="cancelled")

            response: AIMessage = await model.ainvoke(session.messages)
            session.add_ai_message(response)

            # Check if we need to compact messages based on input token usage
            input_tokens = response.usage_metadata.get("input_tokens", 0) if response.usage_metadata else 0
            session.messages = await compact_messages_if_needed(
                messages=session.messages,
                current_input_tokens=input_tokens
            )
            # Check for cancellation after LLM response
            if session.is_cancelled():
                return PromptResponse(stop_reason="cancelled")

            if response.tool_calls:
                print(
                    f"Tool calls detected!, list of tool call is {response.tool_calls}",
                    file=sys.stderr)
                # Stream reasoning/text blocks if present
                await self._stream_content_blocks(session_id, response)

                # Process tool calls
                for tool_call in response.tool_calls:
                    await self._process_tool_call(session_id,
                                                  session,
                                                  tools,
                                                  tool_call)
            else:
                # No more tool calls - stream agent message and end turn
                await self._stream_content_blocks(session_id, response)
                break

        return PromptResponse(stop_reason="end_turn")

    async def _get_tools(self):
        """Lazy load tools."""
        if self._tools is None:
            self._tools = await get_all_tools()
        return self._tools

    async def _stream_content_blocks(self, session_id: str,
                                     response: AIMessage) -> None:
        """
        Stream content blocks from an AI response to the client.
        
        Handles reasoning blocks as thought chunks and text blocks as message chunks.
        
        Args:
            session_id: The session ID for the client connection
            response: The AIMessage response from the model
        """
        if not hasattr(response,
                       'content_blocks') or not response.content_blocks:
            return

        for block in response.content_blocks:
            if isinstance(block, dict) and block.get("type") == "reasoning":
                await self.conn.session_update(
                    session_id,
                    AgentThoughtChunk(
                        session_update="agent_thought_chunk",
                        content=TextContentBlock(type="text",
                                                 text=block['reasoning'])
                    )
                )
            elif isinstance(block, dict) and block.get("type") == "text":
                await self.conn.session_update(
                    session_id,
                    AgentMessageChunk(
                        session_update="agent_message_chunk",
                        content=TextContentBlock(type="text",
                                                 text=block['text'])
                    )
                )


    async def _process_tool_call(self, session_id: str, session, tools: list,
                                 tool_call: ToolCall):
        """
        Process a single tool call.

        Args:
            session_id: The session ID
            session: The session object
            tools: List of available tools
            tool_call: The tool call dictionary
            
        Returns:
            PromptResponse if cancellation occurs, None otherwise
        """
        tool_call_id = tool_call["id"]  # LLM's original ID for conversation history
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        # Generate a unique ID for ACP client reporting
        acp_tool_call_id = f"tool_{uuid.uuid4().hex[:16]}"

        # Notify client about tool call initiation
        await self.conn.session_update(
            session_id,
            ToolCallStart(
                session_update="tool_call",
                tool_call_id=acp_tool_call_id,
                title=f"Calling {tool_name}",
                kind="other",
                status="pending",
                raw_input=tool_args
            )
        )

        # Notify client that tool execution is starting
        await self.conn.session_update(
            session_id,
            ToolCallProgress(
                session_update="tool_call_update",
                tool_call_id=acp_tool_call_id,
                status="in_progress"
            )
        )

        # Execute tool
        result = await execute_tool(tools, tool_call)
        session.add_tool_message(result, tool_call_id)

        # Truncate long results
        truncated_result = result[:1000] if len(result) > 1000 else result

        # Notify client about tool completion
        await self.conn.session_update(
            session_id,
            ToolCallProgress(
                session_update="tool_call_update",
                tool_call_id=acp_tool_call_id,
                status="completed",
                content=[ContentToolCallContent(
                    type="content",
                    content=TextContentBlock(type="text", text=truncated_result)
                )]
            )
        )

    def _extract_prompt_content(self, prompt_content: list) -> str:
        """
        Extract and combine user text and attached files from prompt content.
        
        Args:
            prompt_content: List of content blocks from the prompt
            
        Returns:
            Combined user text with attached file contents appended
        """
        user_text_parts = []
        attached_files = []

        for block in prompt_content:
            # Handle both Pydantic models and dicts
            if hasattr(block, 'model_dump'):
                block = block.model_dump(by_alias=True)

            block_type = block.get("type")

            if block_type == "text":
                user_text_parts.append(block.get("text", ""))

            elif block_type == "resource_link":
                file_uri = block.get("uri", "")
                file_name = block.get("name") or file_uri.split("/")[-1]
                mime_type = block.get("mimeType", "")

                if file_uri.startswith("file://"):
                    file_path = file_uri[7:]  # Remove "file://" prefix
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        attached_files.append({
                            "name": file_name,
                            "uri": file_uri,
                            "content": file_content,
                            "mimeType": mime_type
                        })
                    except Exception:
                        pass  # Skip unreadable files

        user_text = "\n".join(user_text_parts)

        if attached_files:
            file_context = "\n\n--- Attached Files ---\n"
            for file_info in attached_files:
                file_context += f"\n### {file_info['name']}\n"
                file_context += f"```\n{file_info['content']}\n```\n"
            user_text = user_text + file_context

        return user_text


async def run_acp_agent():
    """Entry point to run the coding agent using ACP SDK."""

    agent = ACPAgent()
    print("ACP Server starting...", file=sys.stderr)

    try:
        await acp.run_agent(agent, use_unstable_protocol=True)
    finally:
        await cleanup_mcp_connections()
        print("ACP Server stopped.", file=sys.stderr)
