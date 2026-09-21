from aiogram import Bot, F, Router
from aiogram.enums import ContentType
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import Command
from aiogram.types import Message, ReplyParameters

from .. import texts
from ..config import Config
from ..db import Database
from ..utils import Limiter, ack, header

router = Router(name="user")
router.message.filter(F.chat.type == "private")

limiter = Limiter()

TEXT_LIMIT = 4096
CAPTION_LIMIT = 1024
CAPTIONABLE = {
    ContentType.PHOTO,
    ContentType.VIDEO,
    ContentType.ANIMATION,
    ContentType.AUDIO,
    ContentType.DOCUMENT,
    ContentType.VOICE,
}


class Unsupported(Exception):
    """Message cannot be copied to the admin."""


@router.message(Command("start", "help"))
async def start(message: Message) -> None:
    await message.answer(texts.START)


@router.message()
async def relay(message: Message, bot: Bot, config: Config, db: Database) -> None:
    user = message.from_user
    if user is None or db.is_banned(user.id):
        return

    state = limiter.check(user.id)
    if state != "ok":
        if state == "warn":
            await message.answer(texts.FLOOD)
        return

    db.add_user(user.id)
    try:
        admin_msg_ids = await deliver(message, bot, config.admin_id)
    except Unsupported:
        await message.answer(texts.UNSUPPORTED)
        return

    for msg_id in admin_msg_ids:
        db.link(msg_id, user.id, message.message_id)
    await ack(message)


async def deliver(message: Message, bot: Bot, admin_id: int) -> list[int]:
    """Send the user's message to the admin. Returns ids of the messages created in the admin chat."""
    head = header(message)
    # Rough plain-text length of the header, to stay within Telegram limits.
    head_len = len(message.from_user.full_name) + len(message.from_user.username or "") + 40

    # Compact form: header and content in a single message.
    if message.text is not None and len(message.text) + head_len <= TEXT_LIMIT:
        try:
            sent = await bot.send_message(admin_id, f"{head}\n\n{message.html_text}")
            return [sent.message_id]
        except TelegramBadRequest:
            pass
    elif (
        message.content_type in CAPTIONABLE
        and len(message.caption or "") + head_len <= CAPTION_LIMIT
    ):
        caption = head + (f"\n\n{message.html_text}" if message.caption else "")
        try:
            copied = await bot.copy_message(
                admin_id, message.chat.id, message.message_id, caption=caption
            )
            return [copied.message_id]
        except TelegramBadRequest:
            pass

    # Fallback: header as a separate message, original copied as a reply to it.
    sent = await bot.send_message(admin_id, head)
    try:
        copied = await bot.copy_message(
            admin_id,
            message.chat.id,
            message.message_id,
            reply_parameters=ReplyParameters(message_id=sent.message_id),
        )
    except TelegramBadRequest as e:
        await bot.delete_message(admin_id, sent.message_id)
        raise Unsupported from e
    return [sent.message_id, copied.message_id]
