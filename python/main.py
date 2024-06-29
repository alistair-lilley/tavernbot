"""Main
main file with main function, also defines all command accepting functions"""
from __future__ import annotations

import os
import asyncio
import logging

from typing import Callable
from dotenv import dotenv_values

from aiogram import Bot, Router, Dispatcher
from aiogram import F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.types.error_event import ErrorEvent

from botstates import (
    PurgeAdmins,
    CreatePoll,
    PickSendPoll,
    PickDeletePoll,
    InspectingPoll,
)
from adminbot import AdminBot
from pollbot import PollBot

config = dotenv_values(".env")

TOKEN = config["TOKEN"]
MEEEEEEEE = config["ME"]

ADMINFILE = os.path.join(os.path.dirname(__file__), "data", "admins.json")
POLLSFILE = os.path.join(os.path.dirname(__file__), "data", "polls.json")

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s::%(levelname)s::%(module)s.%(funcName)s::%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

LOGGER = logging.getLogger(__name__)

tgbot = Bot(TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
router = Router()
dispatcher = Dispatcher()
dispatcher.include_router(router)

adminbot = AdminBot(ADMINFILE, MEEEEEEEE)
pollbot = PollBot(POLLSFILE, tgbot)

ADMINIDS = lambda: [adminid for adminid in adminbot.admin_ids]
STARTING_COMMAND = lambda: pollbot.users_starting_commands

ALL_STATES = [
    PurgeAdmins.areyousure,
    CreatePoll.set_name,
    CreatePoll.add_answer,
    CreatePoll.set_anon,
    CreatePoll.pick_days,
    CreatePoll.set_q,
    CreatePoll.set_wk_mnth,
    CreatePoll.set_multiresp,
]

DEBUGGING = True

# Command meta-checks


def _check_update_admin(message: Message) -> None:
    """Decorator over each function to update admin IDs and @s as necessary"""
    adminbot.update_admin_info(message.from_user.id, message.from_user.username)


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


if not DEBUGGING:

    @router.error(F.update.message.as_("message"))
    async def error_user_didnt_start_bot(event: ErrorEvent, message: Message) -> None:
        """Tells a user in group to start private messages if they're not started"""
        LOGGER.critical(
            "User %s (%s) tried to use me but an error was caught. I'm assuming they didn't "
            "initiate me privately, but this could be a wrong assumption.",
            message.from_user.username,
            message.from_user.id,
        )
        LOGGER.critical("error was this: %s", event.exception)
        await message.reply(
            "Oop you gotta message me directly before you can ask me anything in a group!! Send me "
            "<code>/start</code> in private messages please. (If you <em>have</em> started me and "
            "something's still going wrong, go poke Ali for debugging!)"
        )


@router.message(
    (~(F.from_user.id.in_(ADMINIDS())))
    & ((F.chat.type == "private") | (F.text.startswith("/")))
)
async def nonadmin_command(message: Message):
    """Validate that a user is an admin if the user is either sending a slash command or talking to
    the bot in private messages

    this MUST be the first router call defined in this file"""
    LOGGER.info(
        "User %s (%s) tried to use me, but is not an admin.",
        message.from_user.username,
        message.from_user.id,
    )


@router.message(~(F.from_user.id.in_(ADMINIDS())))
async def nonadmin_all(message: Message):
    """Ignore any other messages not from admins"""

# State-based operations


@router.message(F.text == "cancel", F.chat.type == "private")
@pre_command_check_stateful
async def cancel_command(message: Message, state: FSMContext):
    """Cancels a multi-step command"""
    pollbot.no_longer_doing_stuff(message.from_user.id)
    await state.clear()
    await message.answer("Command cancelled!", reply_markup=ReplyKeyboardRemove())


@router.message(CreatePoll.set_q, F.chat.type == "private")
@pre_command_check_stateful
async def set_poll_q_query_wk_mnth(message: Message, state: FSMContext):
    await pollbot.set_poll_q_query_wk_mnth(message, state)


@router.message(CreatePoll.set_wk_mnth, F.chat.type == "private")
@pre_command_check_stateful
async def set_wk_mnth_query_pick_days(message: Message, state: FSMContext):
    await pollbot.set_wk_mnth_query_pick_days(message, state)


@router.message(CreatePoll.pick_days, F.chat.type == "private", F.text != "done")
@pre_command_check_stateful
async def set_pick_days_query_pick_days(message: Message, state: FSMContext):
    await pollbot.set_pick_days_query_pick_days(message, state)


@router.message(CreatePoll.pick_days, F.chat.type == "private", F.text == "done")
@pre_command_check_stateful
async def set_pick_days_query_add_answer(message: Message, state: FSMContext):
    await pollbot.set_pick_days_query_add_answer(message, state)


@router.message(CreatePoll.add_answer, F.chat.type == "private", F.text != "done")
@pre_command_check_stateful
async def add_answer_query_add_answer(message: Message, state: FSMContext):
    await pollbot.add_answer_query_add_answer(message, state)


@router.message(CreatePoll.add_answer, F.chat.type == "private", F.text == "done")
@pre_command_check_stateful
async def add_answer_query_anon(message: Message, state: FSMContext):
    await pollbot.add_answer_query_anon(message, state)


@router.message(CreatePoll.set_anon, F.chat.type == "private")
@pre_command_check_stateful
async def set_anon_query_multiresp(message: Message, state: FSMContext):
    await pollbot.set_anon_query_multiresp(message, state)


@router.message(CreatePoll.set_multiresp, F.chat.type == "private")
@pre_command_check_stateful
async def set_multiresp_create_quiz_say_done(message: Message, state: FSMContext):
    await pollbot.set_multiresp_create_quiz_say_done(message, state)


@router.message(PurgeAdmins.areyousure, F.text == "Yes, I'm sure.")
@pre_command_check_stateful
async def confirm_purge_admin(message: Message, state: FSMContext):
    await adminbot.confirm_purge_admin(message, state)


@router.message(PurgeAdmins.areyousure, F.text != "Yes, I'm sure.")
@pre_command_check_stateful
async def decline_purge_admin(message: Message, state: FSMContext):
    await adminbot.decline_purge_admin(message, state)


@router.message(PickDeletePoll.verifying, F.chat.type == "private")
@pre_command_check_stateful
async def delete_poll(message: Message, state: FSMContext):
    await pollbot.delete_poll(message, state)


@router.message(InspectingPoll.inspecting, F.chat.type == "private")
@pre_command_check_stateful
async def show_inspect_poll(message: Message, state: FSMContext):
    await pollbot.show_inspect_poll(message, state)


@router.message(
    F.from_user.func(lambda from_user: pollbot.user_creating_poll(from_user.id))
    & (F.chat.type == "private")
)
@pre_command_check_stateful
async def set_poll_name_query_q(message: Message, state: FSMContext):
    await pollbot.set_poll_name_query_q(message, state)


@router.message(
    F.from_user.func(lambda from_user: pollbot.user_sending_poll(from_user.id))
    & F.chat.type
    == "private"
)
@pre_command_check_stateless
async def send_poll_now(message: Message):
    await pollbot.send_poll_now(message)


@router.message(
    F.from_user.func(lambda from_user: pollbot.user_deleting_poll(from_user.id))
    & F.chat.type
    == "private"
)
@pre_command_check_stateful
async def verify_delete_poll(message: Message, state: FSMContext):
    await pollbot.verify_delete_poll(message, state)


# Commands

@router.message(F.text.startswith("/start"), F.chat.type == "private")
@pre_command_check_stateless
async def start(message: Message):
    """Get a user initiaed with th ebot"""
    LOGGER.info("User %s started with me", message.from_user.username)
    await message.answer(
        "Hi! Thanks for talking to me! If you're an admin, go ahead and give me commands."
    )


@router.message(F.text.startswith("/help"))
@pre_command_check_stateless
async def help(message: Message):
    """post hlep"""
    await message.answer(
        "This bot is designed to help manage the Short Rest Tavern chat!\nHere are the things you "
        "can do with this bot:\n"
        "/addadmin [admin @] - Add an admin to the list of approved admins\n"
        "/deladmin [admin @] - Remove an admin from the list of approved admins\n"
        "/purgeadmin - Remove ALL ADMINS leaving @TheLegendOfZegend in charge!!!\n"
        "/addpoll - Start the process of making a new recurring poll (NOTE: you HAVE to start this "
        "in the group!)\n"
        "/sendpoll - Send an existing poll <i>now!</i>\n"
        "/delpoll - Delete an existing poll\n"
        "/listpolls - List all of the polls available\n"
        "/inspectpoll - Select a poll and see what's in it\n"
        "<b>Note: you can only use these commands in private chat, except for addpoll, sendpoll, and delpoll, "
        "which you can only use in a group chat</b>"
    )


@router.message(F.text.startswith("/addadmin"), F.chat.type == "private")
@pre_command_check_stateless
async def add_admin(message: Message):
    await adminbot.add_admin(message)


@router.message(F.text.startswith("/deladmin"), F.chat.type == "private")
@pre_command_check_stateless
async def remove_admin(message: Message):
    await adminbot.remove_admin(message)


@router.message(F.text.startswith("/purgeadmin"), F.chat.type == "private")
@pre_command_check_stateful
async def purge_admin(message: Message, state: FSMContext):
    await adminbot.purge_admin(message, state)


@router.message(F.text.startswith("/listpolls"), F.chat.type == "private")
@pre_command_check_stateless
async def list_polls(message: Message):
    await pollbot.list_polls(message)


@router.message(F.text.startswith("/inspectpoll"), F.chat.type == "private")
@pre_command_check_stateful
async def select_inspect_poll(message: Message, state: FSMContext):
    await pollbot.select_inspect_poll(message, state)


@router.message(F.text.startswith("/addpoll"))
@pre_command_check_stateless
async def initiate_poll_creation(message: Message):
    await pollbot.initiate_poll_creation(message)


@router.message(F.text.startswith("/sendpoll"))
@pre_command_check_stateless
async def select_send_poll(message: Message):
    await pollbot.select_send_poll(message)


@router.message(F.text.startswith("/delpoll"))
@pre_command_check_stateless
async def select_delete_poll(message: Message):
    await pollbot.select_delete_poll(message)


@router.message()
@pre_command_check_stateless
async def catchall(message: Message):
    """Catches all other messages for the pre-command checks"""
    LOGGER.info("Ignored message (%s) (%s)", message.text, message.chat.id)


# doesnt work ;w;
@router.message()
@pre_command_check_stateful
async def catchallstates(message: Message, state: FSMContext):
    """Catches all other messages for the pre-command checks"""
    LOGGER.info("Ignored message (%s) and state (%s)", message.text, state)


if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    loop.create_task(dispatcher.start_polling(tgbot))
    loop.create_task(pollbot.loop_and_send_polls())
    loop.run_forever()
