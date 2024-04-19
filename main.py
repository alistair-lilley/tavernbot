"""Main
main file with main function, also defines all command accepting functions"""
from __future__ import annotations

import os
import asyncio
import logging
import json

from aiogram import Bot, Router, Dispatcher
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.types.keyboard_button import KeyboardButton

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

tgbot = Bot(TOKEN, parse_mode=ParseMode.HTML)
router = Router()
dispatcher = Dispatcher()
dispatcher.include_router(router)

tavernbot = TavernBot(ADMINFILE, POLLSFILE, MEEEEEEEE)

adminids = [int(adminid) for adminid in tavernbot.admin_ids]

@router.message(F.text.startswith("/start"))
async def start(message):
    LOGGER.info("User %s started with me", message.from_user.username)
    await message.answer("Hi! Thanks for talking to me! If you're an admin, go ahead and give me commands.")

@router.message((~(F.from_user.id.in_(adminids)))&((F.chat.type == "private")|(F.text.startswith("/"))))
async def nonadmin(message):
    LOGGER.info("User %s (%s) tried to use me, but is not an admin.", message.from_user.username, message.from_user.id)
    await message.answer("You are not an admin of this chat. You may not run bot commands.")


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(dispatcher.start_polling(tgbot))
    loop.run_forever()
