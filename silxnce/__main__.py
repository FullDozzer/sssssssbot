import asyncio
import logging
from contextlib import suppress

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError
from aiogram.types import BotCommand, BotCommandScopeChat, ErrorEvent

from . import texts
from .config import Config, load_config
from .db import Database
from .handlers import admin, user

log = logging.getLogger("silxnce")


async def on_error(event: ErrorEvent) -> None:
    log.exception("Unhandled error", exc_info=event.exception)
    message = event.update.message
    if message is not None:
        with suppress(TelegramAPIError):
            await message.answer(texts.ERROR)


async def set_admin_commands(bot: Bot, config: Config) -> None:
    with suppress(TelegramAPIError):
        await bot.set_my_commands(
            [
                BotCommand(command="ban", description="Заблокировать"),
                BotCommand(command="unban", description="Разблокировать"),
            ],
            scope=BotCommandScopeChat(chat_id=config.admin_id),
        )


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )
    config = load_config()
    db = Database(config.db_path)
    bot = Bot(config.token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

    dp = Dispatcher(config=config, db=db)
    dp.include_routers(admin.router, user.router)
    dp.errors.register(on_error)

    try:
        me = await bot.get_me()
        log.info("Started as @%s, admin id %s", me.username, config.admin_id)
        await set_admin_commands(bot, config)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        db.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
