"""test for poll manager"""
from __future__ import annotations

import os
import unittest

from dotenv import dotenv_values

from pollmgr import PollMgr

config = dotenv_values(".env")


class PollMgrTestCase(unittest.TestCase):

    def setUp(self: PollMgrTestCase):
        self.pollmgr = PollMgr("/home/ali/Programs/src/tavernbot/data/polls.json")
    
    def test___init__(self: PollMgrTestCase):
        self.assertEqual(len(self.pollmgr.poll_names), 0)
    
    def test_create_save_poll(self: PollMgrTestCase):
        sample_poll = {
            "name": "thingy",
            "question": "thingy",
            "replyopts": ["thee", "thou"],
            "wk_mnth": "weekly",
            "days": [1, 2, 3],
            "anon": False,
            "multiresp": True,
        }
        self.pollmgr.create_save_poll(sample_poll)


def compile_suite():
    suite = unittest.TestSuite()
    tests = [test for test in PollMgrTestCase.__dict__.keys() if test.startswith("test_")]
    for test in tests:
        suite.addTest(PollMgrTestCase(test))
    return suite