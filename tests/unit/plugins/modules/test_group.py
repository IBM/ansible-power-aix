# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import re
import copy

from ansible_collections.ibm.power_aix.plugins.modules import group

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir
)


class TestCreateUser(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["name"] = "test123"
        params["group_attributes"] = {'key1':'value1' , 'key2':'value2'}
        params["user_list_action"] = 'add'
        params["user_list_type"] = 'admins'
        params["users_list"] = ['user1', 'user2']
        params["remove_keystore"] = True
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_success_create_group_no_modify_group(self):
        self.module.params["group_attributes"] = None
        self.module.params["user_list_action"] = None
        msg = group.create_group(self.module)
        testMsg = "Group: %s SUCCESSFULLY created." %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_create_group_mock_modify_group(self):
        self.modify_group_path = rootdir + "group.modify_group"
        with mock.patch(self.modify_group_path) as mocked_modify_group:
            mocked_modify_group.return_value = "\n%s list for group: %s SUCCESSFULLY modified." \
            % (self.module.params['user_list_type'], self.module.params['name'])
            msg = group.create_group(self.module)
            testMsg = "Group: %s SUCCESSFULLY created." %self.module.params["name"]
            modify_testMsg = "\n%s list for group: %s SUCCESSFULLY modified." \
            % (self.module.params['user_list_type'], self.module.params['name'])
            testMsg += modify_testMsg
            self.assertEqual(msg, testMsg)

    def test_fail_create_group(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = group.create_group(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_remove_group_with_keystore(self):
        msg = group.remove_group(self.module)
        testMsg = "Group: %s SUCCESSFULLY removed." %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_remove_group_without_keystore(self):
        self.module.params["remove_keystore"] = False
        msg = group.remove_group(self.module)
        testMsg = "Group: %s SUCCESSFULLY removed." %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_fail_remove_group(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = group.remove_group(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_success_modify_group_without_user_list_action(self):
        self.module.params["user_list_action"] = None
        msg = group.modify_group(self.module)
        testMsg = "\nGroup: %s attributes SUCCESSFULLY set." %self.module.params["name"]
        self.assertEqual(msg, testMsg)

    def test_success_modify_group_with_user_list_action(self):
        msg = group.modify_group(self.module)
        testMsg = "\nGroup: %s attributes SUCCESSFULLY set." %self.module.params["name"]
        listMsg = "\n%s list for group: %s SUCCESSFULLY modified." % (self.module.params['user_list_type'], self.module.params['name'])
        testMsg += listMsg
        self.assertEqual(msg, testMsg)

    def test_fail_modify_group_attribute_error(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = group.modify_group(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_fail_modify_group_action_error_no_list_type(self):
        self.module.params["group_attributes"] = None
        self.module.params["user_list_type"] = None
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = group.modify_group(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_fail_modify_group_action_error_no_users_list(self):
        self.module.params["group_attributes"] = None
        self.module.params["users_list"] = None
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            msg = group.modify_group(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])
