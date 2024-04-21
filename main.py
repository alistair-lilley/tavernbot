"""Main
main file with main function, also defines all command accepting functions"""
from __future__ import annotations

import os
import asyncio
import logging
import json

from typing import Callable

from aiogram import Bot, Router, Dispatcher
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.error_event import ErrorEvent

from dotenv import dotenv_values

import botstates

from tavernbot import TavernBot

config = dotenv_values(".env")

TOKEN = config["TOKEN"]
MEEEEEEEE = config["ME"]

ADMINFILE = os.path.join(os.path.dirname(__file__), "data", "admins.json")
POLLSFILE = os.path.join(os.path.dirname(__file__), "data", "polls.json")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s::%(levelname)s::%(module)s.%(funcName)s:: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

LOGGER = logging.getLogger(__name__)

tgbot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
router = Router()
dispatcher = Dispatcher()
dispatcher.include_router(router)

tavernbot = TavernBot(ADMINFILE, POLLSFILE, MEEEEEEEE)

ADMINIDS = [int(adminid) for adminid in tavernbot.admin_ids]

# Command meta-checks

def _check_update_admin(message: Message) -> None:
    """Decorator over each function to update admin IDs and @s as necessary"""
    tavernbot.update_admin_info(str(message.from_user.id), message.from_user.username)

def pre_command_check(command: Callable):
    """Wrap each command with this to do pre-command checks"""
    async def wrap_command(message: Message):
        _check_update_admin(message)
        await command(message)
    return wrap_command

@router.error(F.update.message.as_("message"))
async def error_user_didnt_start_bot(event: ErrorEvent, message: Message) -> None:
    """Tells a user in group to start private messages if they're not started"""
    LOGGER.critical("User %s (%s) tried to use me in a group before they initiated me privately")
    await message.reply("Oop you gotta message me directly before you can ask me anything in a group!! Send me <code>/start</code> in private messages please. (If you <em>have</em> started me and something's still going wrong, go poke Ali for debugging!)")

@router.message(
    (~(F.from_user.id.in_(ADMINIDS)))
    & ((F.chat.type == "private") | (F.text.startswith("/")))
)
async def nonadmin(message: Message):
    """Validate that a user is an admin if the user is either sending a slash command or talking
    to the bot in private messages"""
    LOGGER.info(
        "User %s (%s) tried to use me, but is not an admin.",
        message.from_user.username,
        message.from_user.id,
    )
    # Not sure this is even necessary tbh
    # await message.answer(
    #     "You are not an admin of this chat. You may not run bot commands."
    # )

# Commands

@router.message(F.text.startswith("/start"))
@pre_command_check
async def start(message: Message):
    """Get a user initiaed with th ebot"""
    LOGGER.info("User %s started with me", message.from_user.username)
    await message.answer(
        "Hi! Thanks for talking to me! If you're an admin, go ahead and give me commands."
    )


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(dispatcher.start_polling(tgbot))
    loop.run_forever()
