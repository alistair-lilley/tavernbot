"""test for poll bot"""
from __future__ import annotations

import os
import asyncio
import unittest

from unittest.mock import MagicMock
from dotenv import dotenv_values

from pollbot import PollBot

config = dotenv_values(".env")

MEEEEEEEE = config["ME"]

POLLSFILE = "/home/ali/Programs/src/tavernbot/data/polls.json"

# mock methods for message

class chatobj:

    def __init__(self):
        self.type = None
        self.id = 123213

class userobj:

    def __init__(self):
        self.id = 1111

class mockmessage:

    def __init__(self):
        self.text = None
        self.chat = chatobj()
        self.from_user = userobj()

    async def reply(self, messeg, **kwargs):
        return messeg

    async def answer(self, messeg, **kwargs):
        print(messeg)

# mock methods for state

class dataobj:

    def __init__(self):
        self.stuff = {}

    def get(self, key, default):
        if key in self.stuff:
            return self.stuff[key]
        return default

    def __setitem__(self, key, val):
        self.stuff[key] = val

    def __getitem__(self, key):
        return self.stuff.get(key, "randomval")


class mockstate:

    def __init__(self):
        self.data = dataobj()

    async def clear(self):
        return None

    async def set_state(self, *args, **kwargs):
        return None

    async def set_data(self, *args, **kwargs):
        return "set data"

    async def update_data(self, *args, **kwargs):
        return "update data"
    
    async def get_data(self):
        return self.data

# mock methods for bot

class mockbot:

    def __init__(self, *args, **kwargs):
        pass


    async def send_message(*args, **kwargs):
        return "You sent a message"


    async def send_poll(*args, **kwargs):
        return "You sent a poll"

class PollBotTestCase(unittest.TestCase):

    def setUp(self: PollBotTestCase):
        self.loop = asyncio.new_event_loop()
        botmock = mockbot()
        self.message = mockmessage()
        self.message.text = "text"
        self.state = mockstate()
        self.pollbot = PollBot(POLLSFILE, botmock)
    
    def test_initiate_poll_creation_private(self: PollBotTestCase):
        self.message.chat.type = "private"
        (self.loop.run_until_complete(self.pollbot.initiate_poll_creation(self.message, None)))
        self.assertTrue(True)
    
    def test_initiate_poll_creation_notprivate(self: PollBotTestCase):
        self.message.chat.type = "notprivate"
        (self.loop.run_until_complete(self.pollbot.initiate_poll_creation(self.message, self.state)))
        self.assertTrue(True)
    
    def test_set_poll_name_query_q(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.set_poll_name_query_q(self.message, self.state)))
        self.assertTrue(True)
    
    def test_set_poll_q_query_wk_mnth(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.set_poll_q_query_wk_mnth(self.message, self.state)))
        self.assertTrue(True)

    def test_set_wk_mnth_query_pick_days(self: PollBotTestCase):
        self.message.text = "monthly"
        (self.loop.run_until_complete(self.pollbot.set_wk_mnth_query_pick_days(self.message, self.state)))
        self.assertTrue(True)
        self.message.text = "weekly"
        (self.loop.run_until_complete(self.pollbot.set_wk_mnth_query_pick_days(self.message, self.state)))
        self.assertTrue(True)
    
    def test_pick_days_query_pick_days_failed(self: PollBotTestCase):
        dataobj = self.loop.run_until_complete(self.state.get_data())
        dataobj["wk_mnth"] = "monthly"
        self.message.text = "0"
        self.assertEqual((self.loop.run_until_complete(self.pollbot.set_pick_days_query_pick_days(self.message, self.state))), "Failed")
        self.message.text = "32"
        self.assertEqual((self.loop.run_until_complete(self.pollbot.set_pick_days_query_pick_days(self.message, self.state))), "Failed")
        dataobj["wk_mnth"] = "weekly"
        self.message.text = "ljf"
        self.assertEqual((self.loop.run_until_complete(self.pollbot.set_pick_days_query_pick_days(self.message, self.state))), "Failed")
        
    def test_pick_days_query_pick_days_success(self: PollBotTestCase):
        dataobj = self.loop.run_until_complete(self.state.get_data())
        dataobj["wk_mnth"] = "monthly"
        self.message.text = "4"
        (self.loop.run_until_complete(self.pollbot.set_pick_days_query_pick_days(self.message, self.state)))
        self.assertTrue(True)
        dataobj["wk_mnth"] = "weekly"
        self.message.text = "Monday"
        (self.loop.run_until_complete(self.pollbot.set_pick_days_query_pick_days(self.message, self.state)))
        self.assertTrue(True)
    
    def test_pick_days_query_add_answer(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.set_pick_days_query_add_answer(self.message, self.state)))
        self.assertTrue(True)

    def test_add_answer_query_add_answer(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.set_pick_days_query_add_answer(self.message, self.state)))
        self.assertTrue(True)

    def test_add_answer_query_anon(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.add_answer_query_add_answer(self.message, self.state)))
        self.assertTrue(True)

    def test_set_anon_query_multiresp(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.set_anon_query_multiresp(self.message, self.state)))
        self.assertTrue(True)

    def test_set_multiresp_create_quiz_say_done(self: PollBotTestCase):
        (self.loop.run_until_complete(self.pollbot.set_multiresp_create_quiz_say_done(self.message, self.state)))
        self.assertTrue(True)


    
def compile_suite():
    suite = unittest.TestSuite()
    tests = [test for test in PollBotTestCase.__dict__.keys() if test.startswith("test_")]
    for test in tests:
        suite.addTest(PollBotTestCase(test))
    return suite



