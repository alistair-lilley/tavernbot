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
from aiogram.fsm.context import FSMContext
from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.types.keyboard_button import KeyboardButton
from aiogram.types.error_event import ErrorEvent

from dotenv import dotenv_values

from botstates import PurgeAdmins

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


def pre_command_check_stateless(command: Callable):
    """Wrap each command with this to do pre-command checks -- without state"""

    async def wrap_command(message: Message):
        _check_update_admin(message)
        await command(message)

    return wrap_command


def pre_command_check_stateful(command: Callable):
    """Wrap each command with this to do pre-command checks -- with state"""

    async def wrap_command(message: Message, state: FSMContext):
        _check_update_admin(message)
        await command(message, state)

    return wrap_command


@router.error(F.update.message.as_("message"))
async def error_user_didnt_start_bot(event: ErrorEvent, message: Message) -> None:
    """Tells a user in group to start private messages if they're not started"""
    LOGGER.critical(
        "User %s (%s) tried to use me but an error was caught. I'm assuming they didn't initiate "
        "me privately, but this could be a wrong assumption."
    )
    await message.reply(
        "Oop you gotta message me directly before you can ask me anything in a group!! Send me "
        "<code>/start</code> in private messages please. (If you <em>have</em> started me and "
        "something's still going wrong, go poke Ali for debugging!)"
    )


@router.message(
    (~(F.from_user.id.in_(ADMINIDS)))
    & ((F.chat.type == "private") | (F.text.startswith("/")))
)
async def nonadmin(message: Message):
    """Validate that a user is an admin if the user is either sending a slash command or talking
    to the bot in private messages

    this MUST be the first router call defined in this file"""
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
@pre_command_check_stateless
async def start(message: Message):
    """Get a user initiaed with th ebot"""
    LOGGER.info("User %s started with me", message.from_user.username)
    await message.answer(
        "Hi! Thanks for talking to me! If you're an admin, go ahead and give me commands."
    )


@router.message(F.text.startswith("/addadmin"))
@pre_command_check_stateless
async def add_admin(message: Message):
    """Add one or more new admins by @"""
    newadmins = message.text.split(" ")[1:]
    if not newadmins:
        await message.reply("You gotta give me admins to add!")
    else:
        newadmins = [admin.strip("@") for admin in newadmins]
        for admin in newadmins:
            tavernbot.add_admin(admin)
        await message.reply("Admin(s) added!")


@router.message(F.text.startswith("/deladmin"))
@pre_command_check_stateless
async def remove_admin(message: Message):
    """Remove one or more admins by @"""
    rmadmins = message.text.split(" ")[:]
    if not rmadmins:
        await message.reply("You gotta give me admins to remove!")
    else:
        rmadmins = [admin.strip("@") for admin in rmadmins]
        for admin in rmadmins:
            tavernbot.remove_admin(admin)
        await message.reply("Admin(s) removed!")


@router.message(F.text.startswith("/purgeadmin"))
@pre_command_check_stateful
async def purge_admin(message: Message, state: FSMContext):
    """Start purging admins"""
    await state.set_state(PurgeAdmins.areyousure)
    await message.reply(
        'Are you sure you want to purge all admins? The result of this action will leave '
        '@TheLegendOfZegend as the only admin. (Say "Yes, I\'m sure." exactly to confirm)'
    )


@router.message(PurgeAdmins.areyousure, F.text == "Yes, I'm sure.")
@pre_command_check_stateful
async def confirm_purge_admin(message: Message, state: FSMContext):
    """Confirm purge of admins"""
    tavernbot.purge_admins()
    await message.answer(
        "Alright, purging all admins... You'll have to talk to Ali to get things up again."
    )
    await state.clear()


@router.message(PurgeAdmins.areyousure, F.text != "Yes, I'm sure.")
@pre_command_check_stateful
async def decline_purge_admin(message: Message, state: FSMContext):
    """Decline purge of admins"""
    await message.answer("Good good no purge will happen")
    await state.clear()


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(dispatcher.start_polling(tgbot))
    loop.run_forever()
