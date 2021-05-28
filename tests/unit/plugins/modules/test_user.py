# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import re
import copy

from ansible_collections.ibm.power_aix.plugins.modules import user

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir
)


class Testcreate_user(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json

    def _setup_module_params(self):
        self.module.run_command.return_value = (0, None, None)
        params = dict()
        params["name"] = "test123"
        params["attributes"] = None
        params["remove_homedir"] = True
        params["change_passwd_on_login"] = True
        params["password"] = "pass1234"
        self.module.params = params

    def test_success_create_user_without_password(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params["password"] = None
        msg = user.create_user(self.module)
        testMsg = 'Username is created SUCCESSFULLY: %s' %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_create_user_with_password(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        msg = user.create_user(self.module)
        testMsg = 'Username is created SUCCESSFULLY: %s' %self.module.params["name"]
        passMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        testMsg += passMsg
        self.assertEqual(msg, testMsg)

    def test_success_create_user_with_password_with_attributes(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params["attributes"] = {"home" : "/test/home/test123", "data" : "1272"}
        msg = user.create_user(self.module)
        testMsg = 'Username is created SUCCESSFULLY: %s' %self.module.params["name"]
        attrMsg = '\nAll provided attributes for the user: %s is set SUCCESSFULLY' %self.module.params["name"]
        testMsg += attrMsg
        passMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        testMsg += passMsg
        self.assertEqual(msg, testMsg)

    def test_fail_create_user(self):
        self._setup_module_params()
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = user.create_user(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_user_modify_without_password(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params["password"] = None
        self.module.params["attributes"] = {"home" : "/test/home/test123", "data" : "1272"}
        msg = user.modify_user(self.module)
        testMsg = '\nAll provided attributes for the user: %s is set SUCCESSFULLY' %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_user_modify_with_password_with_attribute(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params["attributes"] = {"home" : "/test/home/test123", "data" : "1272"}
        msg = user.modify_user(self.module)
        testMsg = '\nAll provided attributes for the user: %s is set SUCCESSFULLY' % self.module.params['name']
        passMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        testMsg += passMsg
        self.assertEqual(msg, testMsg)

    def test_success_user_modify_with_password_without_attribute(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        msg = user.modify_user(self.module)
        testMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        self.assertEqual(msg, testMsg)


    def test_fail_user_modify(self):
        self._setup_module_params()
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = user.modify_user(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_user_remove(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        msg = user.remove_user(self.module)
        testMsg = "User name is REMOVED SUCCESSFULLY: %s" % self.module.params["name"]
        self.assertEqual(msg, testMsg)


    def test_fail_user_remove(self):
        self._setup_module_params()
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = user.remove_user(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_change_password(self):
        self._setup_module_params()
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        msg = user.change_password(self.module)
        testMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        self.assertEqual(msg, testMsg)

    def test_fail_change_password(self):
        self._setup_module_params()
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = user.change_password(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])
