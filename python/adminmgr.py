"""Admin manager
contains admin management stuff"""
from __future__ import annotations

import os
import json
import logging

from typing import Dict

LOGGER = logging.getLogger(__name__)


class AdminMgr:
    """admin mgr
    manages the admin parts of the bot
    the admin dict takes the form of
    admins = {
        adminat: adminid,
        ...
    }
    """

    def __init__(self: AdminMgr, admin_file: str, myid: str):
        self._admin_file = admin_file
        self._admins: Dict = None
        self._default_admins = {"default": int(myid)}
        self._safe_load_admins()

    def _load_admins(self: AdminMgr):
        try:
            with open(self._admin_file) as af:
                self._admins = json.load(af)
        except Exception as e:
            LOGGER.critical(f"Failed to load admins due to error <{e}>")

    def _validate_file_existence(self: AdminMgr):
        if not os.path.exists(self._admin_file):
            try:
                with open(self._admin_file, "w") as af:
                    json.dump(self._default_admins, af)
            except Exception as e:
                LOGGER.critical(f"Failed to create admins due to error <{e}>")

    def _validate_has_admins(self: AdminMgr):
        if not self._admins:
            self._admins = self._default_admins.copy()

    def _safe_load_admins(self: AdminMgr):
        self._validate_file_existence()
        self._load_admins()
        self._validate_has_admins()

    def serialize(self: AdminMgr):
        """Dumps admin and polls data to files"""
        try:
            with open(self._admin_file, "w") as af:
                json.dump(self._admins, af)
        except Exception as e:
            LOGGER.critical(f"Failed to dump admins due to error <{e}>")

    def add_admin(self: AdminMgr, adminat: str = None):
        """Add an admin to the dict by @"""
        self._admins[adminat.lower()] = None
        self.serialize()

    def remove_admin(self: AdminMgr, admin: str):
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

    def update_admin_info(self: AdminMgr, adminid: int, adminat: str):
        """Update the at:id pairing for admin entries
        Runs each time an admin messages gets caught, just to be sure that the values are up to date
        in case an admin changes their @"""
        try:
            # yeah i know its janky its fine its fine
            self.remove_admin(adminid)
            self.remove_admin(adminat.lower())
            self._admins[adminat.lower()] = adminid
            LOGGER.debug("Updated admin %s (%s)", adminat.lower(), adminid)
        except Exception as e:
            LOGGER.critical("Failed to update admin %s (%s)!", adminat.lower(), adminid)
        self.serialize()

    def purge_admins(self: AdminMgr):
        """Remove all admins but me"""
        self._admins = self._default_admins.copy()
        self.serialize()

    @property
    def admins(self: AdminMgr):
        return self._admins

    @property
    def admin_ids(self: AdminMgr):
        return self._admins.values()

    @property
    def admin_names(self: AdminMgr):
        return self._admins.keys()
