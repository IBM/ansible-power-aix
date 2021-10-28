# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.ibm.power_aix.plugins.modules import user

from .common.utils import (
    AnsibleFailJson, fail_json
)


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["name"] = "test123"
        params["attributes"] = None
        params["remove_homedir"] = True
        params["change_passwd_on_login"] = True
        params["password"] = "pass1234"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_success_create_user_without_password(self):
        self.module.params["password"] = None
        msg = user.create_user(self.module)
        testMsg = 'Username is created SUCCESSFULLY: %s' % self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_create_user_with_password(self):
        msg = user.create_user(self.module)
        testMsg = 'Username is created SUCCESSFULLY: %s' % self.module.params["name"]
        passMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        testMsg += passMsg
        self.assertEqual(msg, testMsg)

    def test_success_create_user_with_password_with_attributes(self):
        self.module.params["attributes"] = {"home": "/test/home/test123", "data": "1272"}
        msg = user.create_user(self.module)
        testMsg = 'Username is created SUCCESSFULLY: %s' % self.module.params["name"]
        attrMsg = '\nAll provided attributes for the user: %s are set SUCCESSFULLY' % self.module.params["name"]
        testMsg += attrMsg
        passMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        testMsg += passMsg
        self.assertEqual(msg, testMsg)

    def test_fail_create_user(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            user.create_user(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_user_modify_without_password(self):
        self.module.params["password"] = None
        self.module.params["attributes"] = {"home": "/test/home/test123", "data": "1272"}
        msg = user.modify_user(self.module)
        testMsg = '\nAll provided attributes for the user: %s are set SUCCESSFULLY' % self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_user_modify_with_password_with_attribute(self):
        self.module.params["attributes"] = {"home": "/test/home/test123", "data": "1272"}
        msg = user.modify_user(self.module)
        testMsg = '\nAll provided attributes for the user: %s are set SUCCESSFULLY' % self.module.params['name']
        passMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        testMsg += passMsg
        self.assertEqual(msg, testMsg)

    def test_success_user_modify_with_password_without_attribute(self):
        msg = user.modify_user(self.module)
        testMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        self.assertEqual(msg, testMsg)

    def test_fail_user_modify(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            user.modify_user(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_user_remove(self):
        msg = user.remove_user(self.module)
        testMsg = "User name is REMOVED SUCCESSFULLY: %s" % self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_fail_user_remove(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            user.remove_user(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_change_password(self):
        msg = user.change_password(self.module)
        testMsg = "\nPassword is set successfully for the user: %s" % self.module.params['name']
        self.assertEqual(msg, testMsg)

    def test_fail_change_password(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            user.change_password(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_change_account_locked_true_bool(self):
        # Note: The following cases get interpreted as a boolean true:
        # a lower case true without quotations
        # a lower case yes without quotations
        # an upper case true without quotations
        # an upper case yes without quotations
        self.module.params["attributes"] = {"account_locked": True}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"true\"  test123")

    def test_change_account_locked_true_quotes(self):
        self.module.params["attributes"] = {"account_locked": "true"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"true\"  test123")

    def test_change_account_locked_True_quotes(self):
        self.module.params["attributes"] = {"account_locked": "True"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"true\"  test123")

    def test_change_account_locked_yes_quotes(self):
        self.module.params["attributes"] = {"account_locked": "yes"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"yes\"  test123")

    def test_change_account_locked_Yes_quotes(self):
        self.module.params["attributes"] = {"account_locked": "Yes"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"yes\"  test123")

    def test_change_account_locked_always(self):
        # both always and "always" get interpreted as strings
        self.module.params["attributes"] = {"account_locked": "always"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"always\"  test123")

    def test_change_account_locked_Always(self):
        # both Always and "Always" get interpreted as strings
        self.module.params["attributes"] = {"account_locked": "Always"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"always\"  test123")

    def test_change_account_locked_false_bool(self):
        # Note: The following cases get interpreted as a boolean false:
        # a lower case false without quotations
        # a lower case no without quotations
        # an upper case false without quotations
        # an upper case no without quotations
        self.module.params["attributes"] = {"account_locked": False}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"false\"  test123")

    def test_change_account_locked_false_quotes(self):
        self.module.params["attributes"] = {"account_locked": "false"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"false\"  test123")

    def test_change_account_locked_False_quotes(self):
        self.module.params["attributes"] = {"account_locked": "False"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"false\"  test123")

    def test_change_account_locked_no_quotes(self):
        self.module.params["attributes"] = {"account_locked": "no"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"no\"  test123")

    def test_change_account_locked_No_quotes(self):
        self.module.params["attributes"] = {"account_locked": "No"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"no\"  test123")

    def test_change_account_locked_never(self):
        # both never and "never" get interpreted as strings
        self.module.params["attributes"] = {"account_locked": "never"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"never\"  test123")

    def test_change_account_locked_Never(self):
        # both Never and "Never" get interpreted as strings
        self.module.params["attributes"] = {"account_locked": "Never"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"never\"  test123")

    def test_modify_user_account_locked_capabilities(self):
        # test the modifying of two attributes: account_locked and capabilities
        self.module.params["attributes"] = {"account_locked": "Yes", "capabilities": "CAP_AACCT"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"yes\" capabilities=\"CAP_AACCT\"  test123")

    def test_modify_user_account_locked_mixed_case(self):
        # test modifying account_locked with mixed case
        self.module.params["attributes"] = {"account_locked": "TrUe"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"true\"  test123")

    def test_modify_user_account_locked_mixed_case_capabilities(self):
        # test the modifying of two attributes: account_locked and capabilities
        self.module.params["attributes"] = {"account_locked": "fAlSe", "capabilities": "CAP_AACCT"}
        self.module.params["password"] = None
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"

        self.module.run_command.return_value = (rc, stdout, stderr)

        user.modify_user(self.module)
        self.module.run_command.assert_called_once_with("chuser account_locked=\"false\" capabilities=\"CAP_AACCT\"  test123")
