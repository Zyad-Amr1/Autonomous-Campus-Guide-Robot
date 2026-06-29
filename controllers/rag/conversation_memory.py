"""In-memory conversation memory for short public chatbot sessions."""

from __future__ import annotations


class ConversationMemory:
    """Store recent chat turns without persisting sensitive history."""

    def __init__(self, max_messages: int = 20) -> None:
        self.max_messages = max(2, int(max_messages))
        self._messages: list[dict[str, str]] = []

    def add_user_message(self, text: str) -> None:
        """Add a user message to memory."""
        self._add_message("user", text)

    def add_assistant_message(self, text: str) -> None:
        """Add an assistant message to memory."""
        self._add_message("assistant", text)

    def get_recent_messages(self, limit: int = 6) -> list[dict[str, str]]:
        """Return the most recent messages, capped by the requested limit."""
        safe_limit = max(0, int(limit))
        if safe_limit == 0:
            return []
        return [dict(message) for message in self._messages[-safe_limit:]]

    def clear(self) -> None:
        """Clear all in-memory messages."""
        self._messages.clear()

    def _add_message(self, role: str, text: str) -> None:
        cleaned_text = text.strip()
        if not cleaned_text:
            return
        self._messages.append({"role": role, "content": cleaned_text})
        if len(self._messages) > self.max_messages:
            self._messages = self._messages[-self.max_messages :]
