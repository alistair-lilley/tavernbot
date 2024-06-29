"""test for admin manager"""
from __future__ import annotations

import os
import unittest

from dotenv import dotenv_values

from adminmgr import AdminMgr

config = dotenv_values(".env")

MEEEEEEEE = int(config["ME"])

class AdminMgrTestCase(unittest.TestCase):

    def setUp(self: AdminMgrTestCase):
        self.adminmgr = AdminMgr("/home/ali/Programs/src/tavernbot/data/admins.json", MEEEEEEEE)

    def test___init__(self: AdminMgrTestCase):
        self.assertIn("default", self.adminmgr.admin_names)
        self.assertIn(MEEEEEEEE, self.adminmgr.admin_ids)
        self.assertEqual(len(self.adminmgr.admin_names), 1)
        self.assertEqual(len(self.adminmgr.admin_ids), 1)
    
    def test_add_admin(self: AdminMgrTestCase):
        self.adminmgr.add_admin(("StimkyFerret").lower())
        self.assertIn(("StimkyFerret").lower(), self.adminmgr.admin_names)
        self.assertIsNone(self.adminmgr.admins[("StimkyFerret").lower()])
        self.adminmgr.add_admin(("StankyTig").lower())
        self.assertIn(("StankyTig").lower(), self.adminmgr.admin_names)
        self.assertIsNone(self.adminmgr.admins[("StankyTig").lower()])
    
    def test_remove_admin(self: AdminMgrTestCase):
        self.adminmgr.remove_admin("default")
        self.assertEqual(len(self.adminmgr.admins), 2) # should still have stimkyferret and staynkytig
    
    def test_update_admin_info(self: AdminMgrTestCase):
        self.adminmgr.add_admin(("StimkyFerret").lower())
        self.adminmgr.update_admin_info(10101, ("StimkyFerret").lower())
        self.adminmgr.update_admin_info(MEEEEEEEE, ("TheLegendOfZegend").lower())
        self.assertIn(10101, self.adminmgr.admin_ids)
        self.assertIn(("StimkyFerret").lower(), self.adminmgr.admin_names)
        self.assertIn(MEEEEEEEE, self.adminmgr.admin_ids)
        self.assertIn(("TheLegendOfZegend").lower(), self.adminmgr.admin_names)
    
    def test_purge_admins(self: AdminMgrTestCase):
        self.adminmgr.purge_admins()
        self.assertIn("default", self.adminmgr.admin_names)
        self.assertIn(MEEEEEEEE, self.adminmgr.admin_ids)
        self.assertEqual(len(self.adminmgr.admin_names), 1)
        self.assertEqual(len(self.adminmgr.admin_ids), 1)


def compile_suite():
    suite = unittest.TestSuite()
    tests = [test for test in AdminMgrTestCase.__dict__.keys() if test.startswith("test_")]
    for test in tests:
        suite.addTest(AdminMgrTestCase(test))
    return suite