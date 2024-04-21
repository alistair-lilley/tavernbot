"""Bot
Contains... bot stuff??? Idunno, i dont know if this is needed yet (or ever)"""
from __future__ import annotations

import os
import json
import logging

from typing import Dict

from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass
class PollObject:
    """Object containing information for a poll"""

    def __init__(self: PollObject, fields: Dict = None):
        self.name = ""
        self.query = ""
        self.replyopts = []
        self.schedule = None
        if fields:
            self.deserialize(fields)

    def serialize(self: PollObject):
        """Returns object as dictionary"""
        return {
            "name": self.name,
            "query": self.query,
            "replylopts": self.replyopts,
            "schedule": self.schedule,
        }

    def deserialize(self: PollObject, fields: Dict):
        """Takes dictionary and constructs object"""
        try:
            self.name = fields["name"]
            self.query = fields["query"]
            self.replyopts = fields["replyopts"]
            self.schedule = fields["schedule"]
        except Exception as e:
            LOGGER.critical(
                f"Loading poll object failed, likely due to missing field; returned error <{e}>"
            )


class TavernBot:
    """Tavern bot
    manages the database parts of the bot
    the admin dict takes the form of
    admins = {
        adminat: adminid,
        ...
    }
    """

    def __init__(self: TavernBot, admin_file: str, polls_file: str, myid: str):
        self._admin_file = admin_file
        self._polls_file = polls_file
        self._polls: Dict = None
        self._admins: Dict = None
        self._default_admins = {"default": myid}
        self._safe_load_objects()

    def _load_objects(self: TavernBot):
        try:
            with open(self._admin_file) as af:
                self._admins = json.load(af)
        except Exception as e:
            LOGGER.critical(f"Failed to load admins due to error <{e}>")
        try:
            with open(self._polls_file) as pf:
                rawpolls = json.load(pf)
            self._polls = {
                poll["name"]: PollObject(polldata)
                for poll, polldata in rawpolls.items()
            }
        except Exception as e:
            LOGGER.critical(f"Failed to load polls due to error <{e}>")

    def _validate_file_existence(self: TavernBot):
        if not os.path.exists(self._admin_file):
            try:
                with open(self._admin_file, "w") as af:
                    json.dump(self._default_admins, af)
            except Exception as e:
                LOGGER.critical(f"Failed to create admins due to error <{e}>")
        if not os.path.exists(self._polls_file):
            try:
                with open(self._polls_file, "w") as pf:
                    json.dump(self._default_admins, pf)
            except Exception as e:
                LOGGER.critical(f"Failed to create polls due to error <{e}>")
    
    def _validate_has_admins(self: TavernBot):
        if not self._admins:
            self._admins = self._default_admins.copy()

    def _safe_load_objects(self: TavernBot):
        self._validate_file_existence()
        self._load_objects()
        self._validate_has_admins()

    def serialize(self: TavernBot):
        """Dumps admin and polls data to files"""
        try:
            with open(self._admin_file, "w") as af:
                json.dump(self._admins, af)
        except Exception as e:
            LOGGER.critical(f"Failed to dump admins due to error <{e}>")
        try:
            polldict = {pollname: poll.serialize() for pollname, poll in self._polls}
            with open(self._polls_file, "w") as pf:
                json.dump(polldict, pf)
        except Exception as e:
            LOGGER.critical(f"Failed to dump polls due to error <{e}>")

    def add_admin(self: TavernBot, adminat: str = None):
        """Add an admin to the dict by @"""
        self._admins[adminat] = None
        self.serialize()

    def remove_admin(self: TavernBot, admin: str):
        """Removes an admin from the admin dict by @ *or* ID"""
        if admin in self._admins.keys():
            del self._admins[admin]
        elif admin in self._admins.values():
            # wow this is janky
            # basically this finds an admin's @ by searching the values for their id
            adminat = list(self._admins.keys())[
                list(self._admins.values()).index(admin)
            ]
            del self._admins[adminat]
        self.serialize()

    def update_admin_info(self: TavernBot, adminid: str, adminat: str):
        """Update the at:id pairing for admin entries
        Runs each time an admin messages gets caught, just to be sure that the values are up to date
        in case an admin changes their @"""
        try:
            # yeah i know its janky its fine its fine
            self.remove_admin(adminid)
            self.remove_admin(adminat)
            self._admins[adminat] = adminid
            LOGGER.debug("Updated admin %s (%s)", adminat, adminid)
        except Exception as e:
            LOGGER.critical("Failed to update admin %s (%s)!", adminat, adminid)
        self.serialize()

    def purge_admins(self: TavernBot):
        self._admins = {}
        self.serialize()

    @property
    def admins(self: TavernBot):
        return self._admins

    @property
    def admin_ids(self: TavernBot):
        return self._admins.values()

    @property
    def poll_names(self: TavernBot):
        return self._polls.keys()
