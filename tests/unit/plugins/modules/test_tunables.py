# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import copy

from ansible_collections.ibm.power_aix.plugins.modules import tunables

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir
)


class TestTunables(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["action"] = 'show'
        params["component"] = 'vm'
        params["change_type"] = 'current'
        params["bosboot_tunables"] = True
        params["restricted_tunables"] = True
        params["tunable_params"] = None
        self.module.params = params
        rc, stdout, stderr = 0, '', "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.convert_to_dict = rootdir + "tunables.convert_to_dict"
        self.create_tunables_dict = rootdir + "tunables.create_tunables_dict"
        self.get_valid_tunables = rootdir + "tunables.get_valid_tunables"

    def test_show_vmo_tunables_failed(self):
        self.module.params["tunable_params"] = ['abc', 'xyz']
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            with mock.patch(self.convert_to_dict) as mocked_convert_to_dict:
                mocked_convert_to_dict.return_value = {}
                tunables.show(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_show_vmo_tunables_success(self):
        self.module.params["tunable_params"] = ['lgpg_regions', 'lgpg_size']
        with mock.patch(self.convert_to_dict) as mocked_convert_to_dict:
            mocked_convert_to_dict.return_value = {}
            tunables.show(self.module)
        result = copy.deepcopy(tunables.results)
        pattern = "Task has been SUCCESSFULLY executed."
        self.assertRegexpMatches(result['msg'], pattern)

    def test_modify_vmo_failed_prohibited_combination(self):
        self.module.params['tunable_params_with_value'] = {'lgpg_regions': 10, 'lgpg_size': 16777216}
        self.module.params["action"] = 'modify'
        self.module.params["change_type"] = 'both'
        with self.assertRaises(AnsibleFailJson) as result:
            with mock.patch(self.get_valid_tunables) as mocked_valid_tunables:
                mocked_valid_tunables = {'lgpg_regions': 10, 'lgpg_size': 16777216}
                tunables.modify(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "\nThe combination of change_type=both and bosboot_tunables=True is invalid."
        pattern += "\nREASON: The current value of Reboot and Bosboot tunables can't be changed."
        self.assertRegexpMatches(result['msg'], pattern)

    def test_modify_vmo_failed_no_tunables_and_value(self):
        self.module.params["action"] = 'modify'
        self.module.params['tunable_params_with_value'] = None
        with self.assertRaises(AnsibleFailJson) as result:
            tunables.modify(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = '\nPlease provide tunable parameter name and new values for modification'
        self.assertRegexpMatches(result['msg'], pattern)

    def test_modify_vmo_success(self):
        self.module.params["action"] = 'modify'
        self.module.params['tunable_params_with_value'] = {'lgpg_regions': 10, 'lgpg_size': 16777216}
        with mock.patch(self.create_tunables_dict) as mocked_create_tunables_dict, \
                mock.patch(self.get_valid_tunables) as mocked_valid_tunables:
            mocked_create_tunables_dict.return_value = {}
            mocked_valid_tunables = {'lgpg_regions': 10, 'lgpg_size': 16777216}
            tunables.modify(self.module)
        result = copy.deepcopy(tunables.results)
        pattern = '\nFollowing tunables have been changed SUCCESSFULLY:  \n'
        self.assertRegexpMatches(result['msg'], pattern)

    def test_reset_vmo_failed_prohibited_combination(self):
        self.module.params["action"] = 'reset'
        self.module.params["change_type"] = 'both'
        with self.assertRaises(AnsibleFailJson) as result:
            tunables.reset(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "\nThe combination of change_type=both and bosboot_tunables=True is invalid."
        pattern += "\nREASON: The current value of Reboot and Bosboot tunables can't be changed."
        self.assertRegexpMatches(result['msg'], pattern)

    def test_reset_success_all_tunables(self):
        self.module.params["action"] = 'reset'
        self.module.params['tunable_params'] = None
        tunables.reset(self.module)
        result = copy.deepcopy(tunables.results)
        pattern = 'All tunables including bosboot type have been reset SUCCESSFULLY\n'
        self.assertRegexpMatches(result['msg'], pattern)

    def test_reset_success_all_dynamic_tunables(self):
        self.module.params["action"] = 'reset'
        self.module.params['bosboot_tunables'] = False
        tunables.reset(self.module)
        result = copy.deepcopy(tunables.results)
        pattern = 'All dynamic tunables have been reset SUCCESSFULLY\n'
        self.assertRegexpMatches(result['msg'], pattern)

    def test_reset_success_given_tunables(self):
        self.module.params["action"] = 'reset'
        self.module.params['tunable_params'] = ['lgpg_regions', 'lgpg_size']
        changed_tunables = 'lgpg_regions lgpg_size'
        tunables.reset(self.module)
        result = copy.deepcopy(tunables.results)
        pattern = 'Following tunables have been reset SUCCESSFULLY: %s  \n' % changed_tunables
        self.assertRegexpMatches(result['msg'], pattern)
