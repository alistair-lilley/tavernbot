"""Poll manager
contains poll management stuff"""
from __future__ import annotations

import os
import json
import logging

from typing import Dict, List
from dataclasses import dataclass

LOGGER = logging.getLogger(__name__)


@dataclass
class PollObject:
    """Object containing information for a poll

    the polls dict takes the form of
    polls = {
        pollname: pollobj,
        ...
    }"""

    def __init__(self: PollObject, fields: Dict = None):
        self.chatid: int = None
        self.name: str = None
        self.question: str = None
        self.replyopts: List[str] = None
        self.wk_mnth: str = None  # "weekly" or "monthly"
        self.days: List[int | str] = None
        self.anon: bool = None
        self.multiresp: bool = None
        if fields:
            self._deserialize(fields)

    def __repr__(self: PollObject):
        fields = self.serialize()
        return f"PollObject({fields})"

    def serialize(self: PollObject):
        """Returns object as dictionary"""
        return {
            "chatid": self.chatid,
            "name": self.name,
            "question": self.question,
            "replyopts": self.replyopts,
            "wk_mnth": self.wk_mnth,
            "days": self.days,
            "anon": self.anon,
            "multiresp": self.multiresp,
        }

    def _deserialize(self: PollObject, fields: Dict):
        """Takes dictionary and constructs object"""
        try:
            self.chatid = fields["chatid"]
            self.name = fields["name"]
            self.question = fields["question"]
            self.replyopts = fields["replyopts"]
            self.wk_mnth = fields["wk_mnth"]
            self.days = fields["days"]
            self.anon = fields["anon"]
            self.multiresp = fields["multiresp"]
        except Exception as e:
            LOGGER.critical(
                f"Loading poll object failed, likely due to missing field; returned error <{e}>"
            )
            raise (e)

    def printable(self: PollObject):
        """Returns data in a pretty format (HTML formatting)"""
        answers = "- " + "\n       - ".join(self.replyopts)
        days = ", ".join([str(ddd) for ddd in self.days])
        anon = "yes" if self.anon else "no"
        multiresp = "yes" if self.multiresp else "no"
        return (
            f"<b>Poll name:</b> {self.name}\n"
            f"<b>Question</b>: {self.question}\n"
            f"<b>Answers</b>: {answers}\n"
            f"<b>Weekly or Monthly</b>: {self.wk_mnth}\n"
            f"<b>Days to post</b>: {days}\n"
            f"<b>Anonymous?</b>: {anon}\n"
            f"<b>Multiple responses?</b>: {multiresp}"
        )


class PollMgr:
    """Object that manages polls"""

    def __init__(self: PollMgr, polls_file: str):
        self._polls_file = polls_file
        self._polls: Dict[str, PollObject] = {}
        self._safe_load_polls()

    def _load_polls(self: PollMgr):
        try:
            with open(self._polls_file) as pf:
                rawpolls = json.load(pf)
            self._polls = {
                polldata["name"]: PollObject(polldata) for polldata in rawpolls.values()
            }
        except Exception as e:
            LOGGER.critical(f"Failed to load polls due to error <{e}>")

    def _validate_file_existence(self: PollMgr):
        if not os.path.exists(self._polls_file):
            try:
                with open(self._polls_file, "w") as pf:
                    json.dump({}, pf)
            except Exception as e:
                LOGGER.critical(f"Failed to create polls file due to error <{e}>")

    def _safe_load_polls(self: PollMgr):
        self._validate_file_existence()
        self._load_polls()

    def _serialize(self: PollMgr):
        try:
            polldict = {
                pollname: poll.serialize() for pollname, poll in self._polls.items()
            }
            with open(self._polls_file, "w") as pf:
                json.dump(polldict, pf)
        except Exception as e:
            LOGGER.critical(f"Failed to dump polls due to error <{e}>")

    def create_save_poll(self: PollMgr, poll_info: Dict):
        new_poll = PollObject(fields=poll_info)
        self._polls[poll_info["name"]] = new_poll
        self._serialize()

    def delete_poll(self: PollMgr, del_poll: str):
        del self._polls[del_poll]
        self._serialize()

    def printable_poll(self: PollMgr, inspect_poll: str):
        return self._polls[inspect_poll].printable()

    @property
    def polls(self: PollMgr):
        return self._polls

    @property
    def poll_names(self: PollMgr):
        return list(self._polls.keys())
