import html
import time
from collections import deque

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, ReactionTypeEmoji

from . import texts


def header(message: Message) -> str:
    """One line about the sender: name · @username · id."""
    user = message.from_user
    parts = [f'<a href="tg://user?id={user.id}">{html.escape(user.full_name)}</a>']
    if user.username:
        parts.append(f"@{user.username}")
    parts.append(f"<code>{user.id}</code>")
    if message.forward_origin is not None:
        parts.append(texts.FORWARDED)
    return " · ".join(parts)


async def ack(message: Message) -> None:
    """Mark a message as delivered: reaction, or a short text if reactions are unavailable."""
    try:
        await message.react([ReactionTypeEmoji(emoji="👍")])
    except TelegramBadRequest:
        await message.answer(texts.SENT)


class Limiter:
    """Sliding window: at most `limit` messages per `window` seconds per user."""

    def __init__(self, limit: int = 20, window: float = 60.0) -> None:
        self.limit = limit
        self.window = window
        self._hits: dict[int, deque[float]] = {}
        self._warned: set[int] = set()

    def check(self, user_id: int) -> str:
        """Returns "ok", "warn" (first rejected message) or "drop" (silently ignore)."""
        now = time.monotonic()
        hits = self._hits.setdefault(user_id, deque())
        while hits and now - hits[0] > self.window:
            hits.popleft()
        if len(hits) < self.limit:
            hits.append(now)
            self._warned.discard(user_id)
            return "ok"
        if user_id in self._warned:
            return "drop"
        self._warned.add(user_id)
        return "warn"
