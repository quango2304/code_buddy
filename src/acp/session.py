"""Session management for ACP."""
import uuid
from dataclasses import dataclass, field
from typing import Optional
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage, SystemMessage, BaseMessage

@dataclass
class Session:
    """Represents an ACP session with conversation history."""
    session_id: str
    cwd: str
    messages: list[BaseMessage] = field(default_factory=list)
    cancelled: bool = False  # Cancellation flag

    def add_system_message(self, content: str):
        self.messages.append(SystemMessage(content=content))

    def add_user_message(self, content: str):
        self.messages.append(HumanMessage(content=content))

    def add_ai_message(self, message: AIMessage):
        self.messages.append(message)

    def add_tool_message(self, content: str, tool_call_id: str):
        self.messages.append(
            ToolMessage(content=content, tool_call_id=tool_call_id))

    def cancel(self):
        """Mark this session as cancelled."""
        self.cancelled = True

    def is_cancelled(self) -> bool:
        """Check if this session is cancelled."""
        return self.cancelled

    def reset_cancellation(self):
        """Reset the cancellation flag for a new prompt turn."""
        self.cancelled = False


class SessionManager:
    """Manages multiple ACP sessions."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create_session(self, cwd: str,
                       session_id: Optional[str] = None) -> Session:
        """Create a new session."""
        if session_id is None:
            session_id = f"sess_{uuid.uuid4().hex[:12]}"

        session = Session(session_id=session_id, cwd=cwd)
        self._sessions[session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
