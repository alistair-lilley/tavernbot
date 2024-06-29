"""test for admin bot"""
from __future__ import annotations

import os
import asyncio
import unittest

from unittest.mock import MagicMock
from dotenv import dotenv_values

from adminbot import AdminBot

config = dotenv_values(".env")

MEEEEEEEE = config["ME"]

POLLSFILE = "/home/ali/Programs/src/tavernbot/data/polls.json"

# mock methods for message

class mockmessage:

    def __init__(self):
        self.text = ""

    async def reply(self, *args, **kwargs):
        return "this is a reply"

    async def answer(self, *args, **kwargs):
        return "this is an answer"

# mock methods for state

class mockstate:

    def __init__(self):
        pass

    async def clear():
        return "cleared"
    
    async def set_state(self, *args, **kwargs):
        return None


class AdminBotTestCase(unittest.TestCase):

    def setUp(self: AdminBotTestCase):
        self.adminbot = AdminBot(POLLSFILE, MEEEEEEEE)
        self.loop = asyncio.new_event_loop()
        self.pseudo_message = mockmessage()
        self.pseudo_state = mockstate
        
    def test_add_admin(self: AdminBotTestCase):
        self.pseudo_message.text = "stimkyferret @stankytig"
        self.loop.run_until_complete(self.adminbot.add_admin(self.pseudo_message))
        self.assertIn("stimkyferret", self.adminbot.admin_names)
        self.assertIn("stankytig", self.adminbot.admin_names)

    def test_remove_admin(self: AdminBotTestCase):
        self.pseudo_message.text = "stankytig stimkyferret"
        self.loop.run_until_complete(self.adminbot.remove_admin(self.pseudo_message))
        self.assertEqual(len(self.adminbot.admin_ids), 2)

    def test_purge_admin(self: AdminBotTestCase):
        self.loop.run_until_complete(self.adminbot.purge_admin(self.pseudo_message, self.pseudo_state))

    def test_confirm_purge_admin(self: AdminBotTestCase):
        self.loop.run_until_complete(self.adminbot.confirm_purge_admin(self.pseudo_message, self.pseudo_state))
        self.assertEqual(len(self.adminbot.admin_ids), 1)

    def test_decline_purge_admin(self: AdminBotTestCase):
        self.loop.run_until_complete(self.adminbot.decline_purge_admin(self.pseudo_message, self.pseudo_state))
        self.assertIn("default", self.adminbot.admin_names)

    def test_update_admin_info(self: AdminBotTestCase):
        self.pseudo_message.text = "stimkyferret"
        self.loop.run_until_complete(self.adminbot.add_admin(self.pseudo_message))
        self.adminbot.update_admin_info(10101, "stimkyferret")
        self.adminbot.update_admin_info(MEEEEEEEE, "thelegendofzegend")
        self.assertIn(10101, self.adminbot.admin_ids)
        self.assertIn("stimkyferret", self.adminbot.admin_names)
        self.assertIn(1061576853, self.adminbot.admin_ids)
        self.assertIn("thelegendofzegend", self.adminbot.admin_names)

    
def compile_suite():
    suite = unittest.TestSuite()
    tests = [test for test in AdminBotTestCase.__dict__.keys() if test.startswith("test_")]
    for test in tests:
        suite.addTest(AdminBotTestCase(test))
    return suite