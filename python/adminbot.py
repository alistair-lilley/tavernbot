"""Admin bot
does bot stuff for admin stuff"""
from __future__ import annotations

import logging

from typing import Dict, TYPE_CHECKING

from botstates import PurgeAdmins
from adminmgr import AdminMgr

LOGGER = logging.getLogger(__name__)

if TYPE_CHECKING:
    from aiogram.types import Message
    from aiogram.fsm.context import FSMContext


class AdminBot:
    """does bot stuff for admin regulation"""

    def __init__(self: AdminBot, admin_file: str, myid: str):
        self._admin_mgr = AdminMgr(admin_file, myid)
        self._starting_command: Dict = {}

    async def add_admin(self: AdminBot, message: Message):
        """Add one or more new admins by @"""
        newadmins = message.text.split(" ")[1:]
        if not newadmins:
            await message.reply("You gotta give me admins to add!")
        else:
            newadmins = [admin.strip("@") for admin in newadmins]
            for admin in newadmins:
                self._admin_mgr.add_admin(admin)
            await message.reply("Admin(s) added!")

    async def remove_admin(self: AdminBot, message: Message):
        """Remove one or more admins by @"""
        rmadmins = message.text.split(" ")[:]
        if not rmadmins:
            await message.reply("You gotta give me admins to remove!")
        else:
            rmadmins = [admin.strip("@") for admin in rmadmins]
            for admin in rmadmins:
                self._admin_mgr.remove_admin(admin)
            await message.reply("Admin(s) removed!")

    async def purge_admin(self: AdminBot, message: Message, state: FSMContext):
        """Start purging admins"""
        await state.set_state(PurgeAdmins.areyousure)
        await message.reply(
            "Are you sure you want to purge all admins? The result of this action will leave "
            '@TheLegendOfZegend as the only admin. (Say "Yes, I\'m sure." exactly to confirm)'
        )

    async def confirm_purge_admin(self: AdminBot, message: Message, state: FSMContext):
        """Confirm purge of admins"""
        self._admin_mgr.purge_admins()
        await message.answer(
            "Alright, purging all admins... You'll have to talk to Ali to get things up again."
        )
        await state.clear()

    async def decline_purge_admin(self: AdminBot, message: Message, state: FSMContext):
        """Decline purge of admins"""
        await message.answer("Good good no purge will happen")
        await state.clear()

    def update_admin_info(self: AdminBot, userid: int, username: str):
        """Update admin info automatically"""
        self._admin_mgr.update_admin_info(userid, username)

    @property
    def admin_ids(self: AdminBot):
        return self._admin_mgr.admin_ids

    @property
    def admin_names(self: AdminBot):
        return self._admin_mgr.admin_names
