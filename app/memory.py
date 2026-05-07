from collections import defaultdict, deque
from typing import Deque, Dict, List, TypedDict


class Message(TypedDict):
    role: str
    content: str


class SessionMemory:
    def __init__(self, max_messages: int = 12) -> None:
        self._store: Dict[str, Deque[Message]] = defaultdict(
            lambda: deque(maxlen=max_messages)
        )

    def add(self, session_id: str, role: str, content: str) -> None:
        self._store[session_id].append({"role": role, "content": content})

    def history(self, session_id: str) -> List[Message]:
        return list(self._store[session_id])


memory = SessionMemory()
