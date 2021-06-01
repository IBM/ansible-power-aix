# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import copy

from ansible_collections.ibm.power_aix.plugins.modules import lvol

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
    rootdir, lslv_output_path1, lslv_output_path2
)


params = {
    "state": "present",
    "lv": "testlv",
    "lv_new_name": None,
    "vg": "testvg",
    "lv_type": "jfs2",
    "strip_size": None,
    "extra_opts": None,
    "num_of_logical_partitions": 5,
    "copies": 1,
    "policy": "maximum",
    "pv_list": None
}

init_result = {
    "changed": False,
    "msg": '',
    "cmd": '',
    "stdout": '',
    "stderr": ''
}


class TestCreateLV(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvol.result = init_result
        self.name = params['lv']
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.is_size_valid_path = rootdir + "lvol.isSizeValid"

    def test_invalid_strip_size_not_power_of_two(self):
        self.module.params['strip_size'] = "5M"
        with self.assertRaises(AnsibleFailJson) as result:
            lvol.create_lv(self.module, self.name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Must be a power of 2"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_invalid_strip_size_invalid_unit(self):
        self.module.params['strip_size'] = "64G"
        with self.assertRaises(AnsibleFailJson) as result:
            lvol.create_lv(self.module, self.name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Valid strip size unit are K and M."
        self.assertRegexpMatches(result['msg'], pattern)

    def test_invalid_strip_size_above_upper_range(self):
        self.module.params['strip_size'] = "129M"
        with self.assertRaises(AnsibleFailJson) as result:
            lvol.create_lv(self.module, self.name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Must be between 4K and 128M"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_invalid_strip_size_below_lower_range(self):
        self.module.params['strip_size'] = "3K"
        with self.assertRaises(AnsibleFailJson) as result:
            lvol.create_lv(self.module, self.name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Must be between 4K and 128M"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_valid_strip_size(self):
        self.module.params['strip_size'] = "64M"
        lvol.create_lv(self.module, self.name)
        result = copy.deepcopy(lvol.result)
        self.assertTrue(result['changed'])
        pattern = r"Logical volume \w*\d* created."
        self.assertRegexpMatches(result['msg'], pattern)
        pattern = "-S 64M"
        self.assertRegexpMatches(result['cmd'], pattern)

    def test_fail_create_lv(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            lvol.create_lv(self.module, self.name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Failed to create logical volume"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_create_lv(self):
        lvol.create_lv(self.module, self.name)
        result = copy.deepcopy(lvol.result)
        self.assertTrue(result['changed'])
        pattern = r"Logical volume \w*\d* created."
        self.assertRegexpMatches(result['msg'], pattern)


class TestModifyLV(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvol.result = init_result
        self.name = params['lv']
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.get_lv_props_path = rootdir + "lvol.get_lv_props"
        # load sample output
        with open(lslv_output_path1, "r") as f:
            self.lslv_output1 = f.read().strip()
        with open(lslv_output_path2, "r") as f:
            self.lslv_output2 = f.read().strip()

    def test_all_lv_props_no_change(self):
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.return_value = self.lslv_output1
            lvol.modify_lv(self.module, self.name)
            result = copy.deepcopy(lvol.result)
        self.assertFalse(result['changed'])
        pattern = "No changes were needed"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_modify_lv(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.return_value = self.lslv_output1
            with self.assertRaises(AnsibleFailJson) as result:
                lvol.modify_lv(self.module, self.name)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = "Failed to modify logical volume"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_fail_modify_copies(self):
        self.module.params['copies'] = 2
        self.module.run_command.side_effect = [
            (0, "sample stdout", "sample stderr"),
            (1, "sample stdout", "sample stderr")
        ]
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            with self.assertRaises(AnsibleFailJson) as result:
                lvol.modify_lv(self.module, self.name)
            result = result.exception.args[0]
            self.assertTrue(result['changed'])
            self.assertTrue(result['failed'])
            pattern = r"Logical volume \w*\d* modified."
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = "Failed to modify the number of copies"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_copies_no_change(self):
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            lvol.modify_lv(self.module, self.name)
            result = copy.deepcopy(lvol.result)
        self.assertTrue(result['changed'])
        pattern = r"Logical volume \w*\d* modified."
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_copies_no_change_fail_lv_rename(self):
        self.module.params['lv_new_name'] = "newtestlv"
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            self.module.run_command.side_effect = [
                (0, "sample stdout", "sample stderr"),
                (1, "sample stdout", "sample stderr")
            ]
            with self.assertRaises(AnsibleFailJson) as result:
                lvol.modify_lv(self.module, self.name)
            result = result.exception.args[0]
            self.assertTrue(result['changed'])
            self.assertTrue(result['failed'])
            pattern = r"Logical volume \w*\d* modified."
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = "Failed to rename"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_copies_no_change_lv_renamed(self):
        self.module.params['lv_new_name'] = "newtestlv"
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            lvol.modify_lv(self.module, self.name)
            result = copy.deepcopy(lvol.result)
        pattern = r"Logical volume \w*\d* modified."
        self.assertRegexpMatches(result['msg'], pattern)
        pattern = "renamed into"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_copies_changed(self):
        self.module.params['copies'] = 2
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            lvol.modify_lv(self.module, self.name)
            result = copy.deepcopy(lvol.result)
        self.assertTrue(result['changed'])
        pattern = r"Logical volume \w*\d* modified."
        self.assertRegexpMatches(result['msg'], pattern)
        pattern = "number of copies is modified."
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_copies_changed_fail_lv_rename(self):
        self.module.params['copies'] = 2
        self.module.params['lv_new_name'] = "newtestlv"
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            self.module.run_command.side_effect = [
                (0, "sample stdout", "sample stderr"),
                (0, "sample stdout", "sample stderr"),
                (1, "sample stdout", "sample stderr")
            ]
            with self.assertRaises(AnsibleFailJson) as result:
                lvol.modify_lv(self.module, self.name)
            result = result.exception.args[0]
            self.assertTrue(result['changed'])
            self.assertTrue(result['failed'])
            pattern = r"Logical volume \w*\d* modified."
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = "number of copies is modified."
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = "Failed to rename"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_modify_lv_copies_changed_lv_renamed(self):
        self.module.params['copies'] = 2
        self.module.params['lv_new_name'] = "newtestlv"
        with mock.patch(self.get_lv_props_path) as mocked_get_lv_props:
            mocked_get_lv_props.side_effect = [
                self.lslv_output1,
                self.lslv_output2
            ]
            lvol.modify_lv(self.module, self.name)
            result = copy.deepcopy(lvol.result)
        self.assertTrue(result['changed'])
        pattern = r"Logical volume \w*\d* modified."
        self.assertRegexpMatches(result['msg'], pattern)
        pattern = "number of copies is modified."
        self.assertRegexpMatches(result['msg'], pattern)
        pattern = "renamed into"
        self.assertRegexpMatches(result['msg'], pattern)


class TestRemoveLV(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvol.result = init_result
        self.name = params['lv']
        self.module = mock.Mock()
        self.module.params = params
        self.module.params['state'] = "absent"
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.ansible_module_path = rootdir + "lvol.AnsibleModule"
        self.lv_exists_path = rootdir + "lvol.lv_exists"

    def test_fail_remove_lv(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            lvol.remove_lv(self.module, self.name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Failed to remove the logical volume"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_remove_lv(self):
        with mock.patch(self.ansible_module_path) as mocked_ansible_module, \
                mock.patch(self.lv_exists_path) as mocked_lv_exists:
            mocked_ansible_module.return_value = self.module
            mocked_lv_exists.return_value = False
            with self.assertRaises(AnsibleExitJson) as result:
                lvol.main()
            result = result.exception.args[0]
            self.assertFalse(result['changed'])
            pattern = "there is no need to remove the logical volume"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_remove_lv(self):
        lvol.remove_lv(self.module, self.name)
        result = copy.deepcopy(lvol.result)
        self.assertTrue(result['changed'])
        pattern = r"Logical volume \w*\d* removed"
        self.assertRegexpMatches(result['msg'], pattern)
