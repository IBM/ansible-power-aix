# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import re
import copy

from ansible_collections.ibm.power_aix.plugins.modules import inittab

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir
)


class TestCreateInittab(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["name"] = "uprintfd"
        params["runlevel"] = "1234567"
        params["action"] = "respawn"
        params["command"] = "/usr/sbin/uprintfd"
        params["insertafter"] = "perfstat"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_success_create_entry(self):
        msg = inittab.create_entry(self.module)
        testMsg = "\nEntry is created in inittab file SUCCESSFULLY: %s" %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_fail_create_entry(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = inittab.create_entry(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_remove_entry(self):
        msg = inittab.remove_entry(self.module)
        testMsg = "Entry is REMOVED SUCCESSFULLY from inittab file: %s" %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_fail_remove_entry(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = inittab.remove_entry(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_modify_entry(self):
        msg = inittab.modify_entry(self.module)
        testMsg = "\nEntry for: %s is changed SUCCESSFULLY in inittab file" %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_fail_modify_entry(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = inittab.modify_entry(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])
