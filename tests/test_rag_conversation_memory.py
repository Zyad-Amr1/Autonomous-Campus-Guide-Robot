"""Tests for in-memory chatbot conversation memory."""

from controllers.rag.conversation_memory import ConversationMemory


def test_stores_recent_messages() -> None:
    memory = ConversationMemory()

    memory.add_user_message("Tell me about Engineering")
    memory.add_assistant_message("Engineering information")

    assert memory.get_recent_messages() == [
        {"role": "user", "content": "Tell me about Engineering"},
        {"role": "assistant", "content": "Engineering information"},
    ]


def test_returns_limited_recent_messages() -> None:
    memory = ConversationMemory(max_messages=10)
    for index in range(5):
        memory.add_user_message(f"Question {index}")

    assert memory.get_recent_messages(limit=2) == [
        {"role": "user", "content": "Question 3"},
        {"role": "user", "content": "Question 4"},
    ]


def test_clear_removes_messages() -> None:
    memory = ConversationMemory()
    memory.add_user_message("Where is the cafeteria?")

    memory.clear()

    assert memory.get_recent_messages() == []
