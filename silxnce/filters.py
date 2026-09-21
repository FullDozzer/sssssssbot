from aiogram.filters import BaseFilter
from aiogram.types import Message

from .config import Config


class IsAdmin(BaseFilter):
    async def __call__(self, message: Message, config: Config) -> bool:
        return message.from_user is not None and message.from_user.id == config.admin_id
