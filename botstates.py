"""bot states
this file defines all the finite state machine states for the bot"""
from __future__ import annotations

from aiogram.fsm.state import StatesGroup, State


class PurgeAdmins(StatesGroup):
    areyousure = State()


class CreatePoll(StatesGroup):
    set_name = State()
    set_q = State()
    set_wk_mnth = State()
    pick_days = State()
    add_answer = State()
    set_anon = State()
    set_multiresp = State()


class PickSendPoll(StatesGroup):
    picking = State()


class PickDeletePoll(StatesGroup):
    picking = State()
    verifying = State()


class InspectingPoll(StatesGroup):
    inspecting = State()
