from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.filters import Command, CommandObject
from aiogram.types import Message, ReplyParameters

from .. import texts
from ..db import Database
from ..filters import IsAdmin
from ..utils import ack

router = Router(name="admin")
router.message.filter(F.chat.type == "private", IsAdmin())


@router.message(Command("start", "help"))
async def start(message: Message) -> None:
    await message.answer(texts.START_ADMIN)


@router.message(Command("ban"))
async def ban(message: Message, command: CommandObject, db: Database) -> None:
    user_id = _target(message, command, db)
    if user_id is None:
        await message.answer(texts.BAN_USAGE)
        return
    db.set_banned(user_id, True)
    await message.answer(texts.BANNED.format(id=user_id))


@router.message(Command("unban"))
async def unban(message: Message, command: CommandObject, db: Database) -> None:
    user_id = _target(message, command, db)
    if user_id is None:
        await message.answer(texts.UNBAN_USAGE)
        return
    db.set_banned(user_id, False)
    await message.answer(texts.UNBANNED.format(id=user_id))


@router.message(F.reply_to_message)
async def reply(message: Message, bot: Bot, db: Database) -> None:
    link = db.lookup(message.reply_to_message.message_id)
    if link is None:
        await message.answer(texts.NO_TARGET)
        return
    user_id, user_msg_id = link

    try:
        copied = await bot.copy_message(
            user_id,
            message.chat.id,
            message.message_id,
            reply_parameters=ReplyParameters(
                message_id=user_msg_id, allow_sending_without_reply=True
            ),
        )
    except TelegramForbiddenError:
        await message.answer(texts.USER_BLOCKED_BOT)
        return
    except TelegramBadRequest:
        await message.answer(texts.SEND_FAILED)
        return

    # Replying to this answer later should reach the same user.
    db.link(message.message_id, user_id, copied.message_id)
    await ack(message)


@router.message()
async def other(message: Message) -> None:
    await message.answer(texts.NOT_REPLY)


def _target(message: Message, command: CommandObject, db: Database) -> int | None:
    """User id from the command argument or from the replied-to message."""
    args = (command.args or "").strip()
    if args.isdigit():
        return int(args)
    if message.reply_to_message is not None:
        link = db.lookup(message.reply_to_message.message_id)
        if link is not None:
            return link[0]
    return None
