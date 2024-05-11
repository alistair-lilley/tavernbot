"""Poll bot
bot end of poll management
"""
from __future__ import annotations

import asyncio
import datetime
import calendar
import logging

from typing import Dict, List, TYPE_CHECKING

from botstates import CreatePoll, PickSendPoll, PickDeletePoll, InspectingPoll
from pollmgr import PollMgr

from aiogram.types.reply_keyboard_markup import ReplyKeyboardMarkup
from aiogram.types.reply_keyboard_remove import ReplyKeyboardRemove
from aiogram.types.keyboard_button import KeyboardButton

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message
    from aiogram.fsm.context import FSMContext

LOGGER = logging.getLogger(__name__)

CANCELBUTTON = KeyboardButton(text="cancel")
DONEBUTTON = KeyboardButton(text="done")
CANCELKB = ReplyKeyboardMarkup(keyboard=[[CANCELBUTTON]])
WKMNTHKB = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="weekly"), KeyboardButton(text="monthly")],
        [CANCELBUTTON],
    ]
)
DONECANCELKB = ReplyKeyboardMarkup(keyboard=[[DONEBUTTON, CANCELBUTTON]])
YESNOKB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="yes"), KeyboardButton(text="no")], [CANCELBUTTON]]
)
YESCANCELKB = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="yes")], [CANCELBUTTON]]
)
MULTIANSWERKB = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="multiple answers"),
            KeyboardButton(text="just one"),
        ],
        [
            CANCELBUTTON,
        ],
    ]
)

DAYNAMES = [
    "sunday",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
]
DOW = {dayname: dayval for dayname, dayval in zip(DAYNAMES, range(1, 8))}
WOD = {val: key for key, val in DOW.items()}

LOCK = asyncio.Lock()


def dow_left(days_used: List[str] = []):
    """Generate keyboard with days of the week left"""
    keyboardbuttons = []
    for dayofweek in DAYNAMES:
        if dayofweek not in days_used:
            keyboardbuttons.append(KeyboardButton(text=dayofweek.capitalize()))
    if len(keyboardbuttons) == len(DAYNAMES):
        return ReplyKeyboardMarkup(keyboard=[keyboardbuttons, [CANCELBUTTON]])
    else:
        return ReplyKeyboardMarkup(
            keyboard=[keyboardbuttons, [DONEBUTTON, CANCELBUTTON]]
        )


class PollBot:
    """Object that manages poll bot interactions"""

    def __init__(self: PollBot, polls_file: str, tgbot: Bot):
        self._poll_mgr = PollMgr(polls_file)
        self._tgbot: Bot = tgbot
        self._starting_command: Dict = {}
        self._command_coming_from: Dict = {}  # user: groupchat

    async def initiate_poll_creation(self: PollBot, message: Message):
        """Starts poll creation process"""
        if message.chat.type == "private":
            await message.reply("Start this in the chat you want the poll for!")
            return
        await message.reply("Let's make a poll!!! I've sent you a private message")
        await self._tgbot.send_message(
            message.from_user.id,
            "What name do you want to give this poll? This will be used for tracking polls, "
            "but won't be visible in the poll.",
        )
        self._command_coming_from[message.from_user.id] = message.chat.id
        self._starting_command[message.from_user.id] = "create"

    async def set_poll_name_query_q(self: PollBot, message: Message, state: FSMContext):
        """Set poll name and query for the poll question"""
        await state.update_data(chatid=self._command_coming_from[message.from_user.id])
        await state.update_data(name=message.text)
        await message.answer(
            "Awesome! Now send me the query -- this is what will be shown when the poll is posted",
            reply_markup=CANCELKB,
        )
        await state.set_state(CreatePoll.set_q)

    async def set_poll_q_query_wk_mnth(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Set poll q and query weekly or monthly"""
        await state.update_data(question=message.text)
        await message.answer(
            'Cool! Now, we gotta set poll frequency. Select "week" or "month" and then pick any '
            "number of days of the week or days of the month.",
            reply_markup=WKMNTHKB,
        )
        await state.set_state(CreatePoll.set_wk_mnth)

    async def set_wk_mnth_query_pick_days(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Set weekly or monthly and query which days"""
        if message.text not in ["weekly", "monthly"]:
            await message.answer("Please select weekly or monthly!")
            return
        await state.update_data(wk_mnth=message.text)
        responsequery = (
            f"Sweet! Now we gotta pick which days of the {message.text[:-2]} the poll will "
            "land on."
        )
        if message.text == "monthly":
            responsequery += (
                " <b>Note: if you pick 29, 30, or 31 as a date, on months with fewer "
                "than that many days the poll will by default land on the last day of "
                "the month.</b>"
            )
            await message.answer(responsequery, reply_markup=CANCELKB)
        elif message.text == "weekly":
            await message.answer(responsequery, reply_markup=dow_left())
        await state.set_state(CreatePoll.pick_days)

    async def set_pick_days_query_pick_days(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Set a day and query either more days or done"""
        wk_mnth = (await state.get_data())["wk_mnth"]
        if (wk_mnth == "monthly" and not (1 <= int(message.text) <= 31)) or (
            wk_mnth == "weekly" and message.text.lower() not in DOW.keys()
        ):
            await message.answer("That's not a valid option!!! Try again pls")
            return "Failed"
        if wk_mnth == "monthly":
            await state.update_data(
                days=(await state.get_data()).get("days", []) + [int(message.text)]
            )
        else:
            await state.update_data(
                days=(await state.get_data()).get("days", [])
                + [DOW[message.text.lower()]]
            )
        responsequery = (
            'Awesome! Go ahead and pick another day or click the "done" button!'
        )
        if wk_mnth == "monthly":
            responsequery += (
                " <b>Note: if you pick 29, 30, or 31 as a date, on months with fewer "
                "than that many days the poll will by default land on the last day of "
                "the month.</b>"
            )
            await message.answer(responsequery, reply_markup=DONECANCELKB)
        elif wk_mnth == "weekly":
            await message.answer(
                responsequery,
                reply_markup=dow_left(
                    [WOD[daynum] for daynum in (await state.get_data())["days"]]
                ),
            )

    async def set_pick_days_query_add_answer(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Set final day to pick and query for an answer to the poll"""
        await message.answer(
            "Cool! Now give me an answer for the poll.", reply_markup=CANCELKB
        )
        await state.set_state(CreatePoll.add_answer)

    async def add_answer_query_add_answer(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Add an answer and query for more answers"""
        await state.update_data(
            replyopts=(await state.get_data()).get("replyopts", []) + [message.text]
        )
        await message.answer(
            'Awesome! Add another question or click "done"!', reply_markup=DONECANCELKB
        )

    async def add_answer_query_anon(self: PollBot, message: Message, state: FSMContext):
        """Add an answer and query anon mode or not"""
        await state.update_data(
            replyopts=((await state.get_data())["replyopts"]) + [message.text]
        )
        await message.answer(
            "Sweet! Questions added. Now, do you want this poll to be anonymous?",
            reply_markup=YESNOKB,
        )
        await state.set_state(CreatePoll.set_anon)

    async def set_anon_query_multiresp(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Set anon and query multiresponse or not"""
        anonymous = True if message.text == "yes" else False
        await state.update_data(anon=anonymous)
        await message.answer(
            "Cool! Final question! Do you want people to be able to choose multiple answers or "
            "just one?",
            reply_markup=MULTIANSWERKB,
        )
        await state.set_state(CreatePoll.set_multiresp)

    async def set_multiresp_create_quiz_say_done(
        self: PollBot, message: Message, state: FSMContext
    ):
        """Set multiresponse setting, create quiz, and say done"""
        multiresponse = True if message.text == "multiple answers" else False
        await state.update_data(multiresp=multiresponse)
        await message.answer(
            "WOOOOO you've made a quiz!!! It'll be posted on the schedule you "
            "specified, and if you want to post one on command you can tell me to!",
            reply_markup=ReplyKeyboardRemove(),
        )
        self._poll_mgr.create_save_poll((await state.get_data()))
        await state.clear()
        self.no_longer_doing_stuff(message.from_user.id)

    async def list_polls(self: PollBot, message: Message):
        """sends a list of polls by name"""
        allpolls = "\n".join([self._poll_mgr.poll_names])
        await message.answer(f"Here are the polls available:\n{allpolls}")

    async def select_inspect_poll(self: PollBot, message: Message, state: FSMContext):
        """shows inspectable polls"""
        allpolls = self._poll_mgr.poll_names
        if len(allpolls) % 2 == 0:
            buttons = [
                [KeyboardButton(text=poll1), KeyboardButton(text=poll2)]
                for poll1, poll2 in zip(allpolls[::2], allpolls[1::2])
            ]
            buttons.append([CANCELBUTTON])
        elif len(allpolls) % 2 != 0:
            allpolls, lastpoll = allpolls[:-1], allpolls[-1]
            if allpolls:
                buttons = [
                    [KeyboardButton(text=poll1), KeyboardButton(text=poll2)]
                    for poll1, poll2 in zip(allpolls[::2], allpolls[1::2])
                ]
            else:
                buttons = []
            buttons.append([KeyboardButton(text=lastpoll), CANCELBUTTON])
        await message.answer(
            "Pick one of the following polls to see more about it!",
            reply_markup=ReplyKeyboardMarkup(keyboard=buttons),
        )
        await state.set_state(InspectingPoll.inspecting)

    async def show_inspect_poll(self: PollBot, message: Message, state: FSMContext):
        """displays a poll to be inspected"""
        if message.text not in self._poll_mgr.poll_names:
            await message.answer(
                "That's not a poll!! Pick one of the polls you do have!!!"
            )
            return
        await message.answer(
            self._poll_mgr.printable_poll(message.text),
            reply_markup=ReplyKeyboardRemove(),
        )
        await state.clear()

    async def select_send_poll(self: PollBot, message: Message):
        """list all available polls to send and send one"""
        if message.chat.type == "private":
            await message.answer("Run this command in a group first!")
            return
        await message.reply("I'm sending you a dm!")
        allpolls = [
            poll.name
            for poll in self._poll_mgr.polls.values()
            if poll.chatid == message.chat.id
        ]
        if len(allpolls) % 2 == 0:
            buttons = [
                [KeyboardButton(text=poll1), KeyboardButton(text=poll2)]
                for poll1, poll2 in zip(allpolls[::2], allpolls[1::2])
            ]
            buttons.append([CANCELBUTTON])
        elif len(allpolls) % 2 != 0:
            allpolls, lastpoll = allpolls[:-1], allpolls[-1]
            if allpolls:
                buttons = [
                    [KeyboardButton(text=poll1), KeyboardButton(text=poll2)]
                    for poll1, poll2 in zip(allpolls[::2], allpolls[1::2])
                ]
            else:
                buttons = []
            buttons.append([KeyboardButton(text=lastpoll), CANCELBUTTON])
        await self._tgbot.send_message(
            message.from_user.id,
            "Pick one of these polls to send and i'll send it!!",
            reply_markup=ReplyKeyboardMarkup(keyboard=buttons),
        )
        self._starting_command[message.from_user.id] = "send"
        self._command_coming_from[message.from_user.id] = message.chat.id

    async def send_poll_now(self: PollBot, message: Message):
        """Sends a selected poll"""
        chat_id = self._command_coming_from[message.from_user.id]
        allpolls = [
            name
            for name, poll in self._poll_mgr.polls.items()
            if poll.chatid == chat_id
        ]
        if message.text not in allpolls:
            await message.answer('That wasn\'t an option!!! Try again or say "cancel"')
            return
        await message.answer(
            "cool!! Sending poll now!", reply_markup=ReplyKeyboardRemove()
        )
        poll = self._poll_mgr.polls[message.text]
        await self._tgbot.send_poll(
            chat_id=poll.chatid,
            question=poll.question,
            options=poll.replyopts,
            is_anonymous=poll.anon,
            allows_multiple_answers=poll.multiresp,
        )
        self.no_longer_doing_stuff(message.from_user.id)

    async def select_delete_poll(self: PollBot, message: Message):
        """lists polls to delete"""
        if message.chat.type == "private":
            message.answer("Run this command in a group first!")
            return
        message.reply("I'm sending you a dm!")
        polls = "\n".join(
            [
                name
                for name, poll in self._poll_mgr.polls.items()
                if poll.chatid == message.chat.id
            ]
        )
        keyboard = [KeyboardButton(text=pollname) for pollname in polls] + [
            CANCELBUTTON
        ]
        await self._tgbot.send_message(
            message.from_user.id,
            "Pick one of these polls to delete and i'll delete it!!",
            reply_markup=keyboard,
        )
        await state.set_state(PickDeletePoll.picking)

    async def verify_delete_poll(self: PollBot, message: Message, state: FSMContext):
        """checks you're sure you wanna delete poll"""
        await state.update_data(poll=message.text)
        await message.answer(
            f"Are you sure you want to delete this poll {message.text}?",
            reply_markup=YESCANCELKB,
        )
        await state.set_state(PickDeletePoll.verifying)
        self.no_longer_doing_stuff(message.from_user.id)

    async def delete_poll(self: PollBot, message: Message, state: FSMContext):
        """deletes poll"""
        self._poll_mgr.delete_poll((await state.get_data())["poll"])
        await message.answer("Poll deleted!")
        await state.clear()

    def _poll_on_today(self: PollBot, weekly_monthly: str, days: List[int]):
        day_of_week = datetime.datetime.now().isoweekday() + 1
        day_of_month = datetime.datetime.now().day
        year = datetime.datetime.now().year
        last_day_of_month = calendar.monthrange(year, day_of_month)[-1]
        if weekly_monthly == "weekly":
            return day_of_week in [WOD[dayval] for dayval in days]
        elif weekly_monthly == "monthly":
            if day_of_month == last_day_of_month:
                # If the poll is requested to start on a day later than the last day of the month,
                # we want to post it on the last day of the month
                return max(days) > last_day_of_month
            return day_of_month in days

    async def _send_polls(self: PollBot):
        async with LOCK:
            for pollname, poll in self._poll_mgr.polls.items():
                if self._poll_on_today(poll.wk_mnth, poll.days):
                    await self._tgbot.send_poll(
                        chat_id=poll.chatid,
                        question=poll.question,
                        options=poll.replyopts,
                        is_anonymous=poll.anon,
                        allows_multiple_answers=poll.multiresp,
                    )
                    LOGGER.info("Sent poll %s to group %s", pollname, poll.chatid)

    async def loop_and_send_polls(self: PollBot):
        """Loop through polls at 7am each day and send any polls set to send on that day"""
        while True:
            await asyncio.sleep(0)
            now = datetime.datetime.now()
            if (now.hour, now.minute) != (7, 0):
                continue
            self._send_polls()
            await asyncio.sleep(60)

    def user_creating_poll(self: PollBot, userid: int):
        return self.users_starting_commands.get(userid, "") == "create"

    def user_sending_poll(self: PollBot, userid: int):
        return self.users_starting_commands.get(userid, "") == "send"

    def no_longer_doing_stuff(self: PollBot, userid: int):
        if userid in self.users_starting_commands:
            del self.users_starting_commands[userid]
        if userid in self._command_coming_from.keys():
            del self._command_coming_from[userid]

    @property
    def users_starting_commands(self: PollBot):
        return self._starting_command
