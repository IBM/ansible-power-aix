# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import copy

from ansible_collections.ibm.power_aix.plugins.modules import lvg

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
    rootdir, lsvg_output_path1, lsvg_output_path2, lsvg_output_path3
)

params = {
    "state": "present",
    "vg_name": "testvg",
    "vg_type": "scalable",
    "enhanced_concurrent_vg": None,
    "critical_vg": None,
    "pvs": ["hdisk1"],
    "critical_pvs": None,
    "num_lvs": None,
    "delete_lvs": None,
    "num_partitions": None,
    "pp_size": None,
    "pp_limit": None,
    "force": None,
    "mirror_pool": "mp1",
    "mirror_pool_strict": None,
    "multi_node_vary": None,
    "auto_on": None,
    "retry": None,
    "major_num": None
}

init_result = {
    "changed": False,
    "msg": '',
    "cmd": '',
    "stdout": '',
    "stderr": ''
}


class TestMakeVG(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvg.result = init_result
        self.vg_name = params['vg_name']
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_fail_make_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.make_vg(self.module, self.vg_name)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to create volume group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_make_vg(self):
        lvg.make_vg(self.module, self.vg_name)
        result = copy.deepcopy(lvg.result)
        self.assertTrue(result['changed'])
        pattern = r"Volume group \w*\d* created"
        self.assertRegexpMatches(result['msg'], pattern)


class TestExtendVG(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvg.result = init_result
        self.vg_name = params['vg_name']
        self.vg_state = True
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.ansible_module_path = rootdir + "lvg.AnsibleModule"
        self.find_vg_state_path = rootdir + "lvg.find_vg_state"
        self.get_vg_props_path = rootdir + "lvg.get_vg_props"
        self.change_vg_path = rootdir + "lvg.change_vg"

        # load sample output
        with open(lsvg_output_path1, "r") as f:
            self.lsvg_output1 = f.read().strip()
        with open(lsvg_output_path2, "r") as f:
            self.lsvg_output2 = f.read().strip()

    def test_fail_extend_vg_varied_off(self):
        self.vg_state = False
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.extend_vg(
                self.module,
                self.vg_name,
                self.vg_state, self.lsvg_output1
            )
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Unable to extend volume group.*because it is not varied on"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_extend_vg_pvs_already_in_vg(self):
        with mock.patch(self.ansible_module_path) as mocked_ansible_module, \
                mock.patch(self.find_vg_state_path) as mocked_find_vg_state, \
                mock.patch(self.get_vg_props_path) as mocked_get_vg_props, \
                mock.patch(self.change_vg_path) as mocked_change_vg:

            mocked_ansible_module.return_value = self.module
            mocked_find_vg_state.return_value = self.vg_state
            mocked_get_vg_props.return_value = self.lsvg_output1
            mocked_change_vg.return_value = None
            with self.assertRaises(AnsibleExitJson) as result:
                lvg.main()

        result = result.exception.args[0]
        self.assertFalse(result['changed'])
        pattern = r"No changes were needed"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_extend_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params['pvs'] = ["hdisk1", "hdisk2"]
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.extend_vg(
                self.module,
                self.vg_name,
                self.vg_state,
                self.lsvg_output1
            )

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to extend volume group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_extend_vg(self):
        self.module.params['pvs'] = ["hdisk1", "hdisk2"]
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output2
            lvg.extend_vg(
                self.module,
                self.vg_name,
                self.vg_state,
                self.lsvg_output1
            )

            result = copy.deepcopy(lvg.result)
            self.assertTrue(result['changed'])
            pattern = r"Volume group.*extended"
            self.assertRegexpMatches(result['msg'], pattern)


class TestChangeVG(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvg.result = init_result
        self.vg_name = params['vg_name']
        self.vg_state = True
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.ansible_module_path = rootdir + "lvg.AnsibleModule"
        self.find_vg_state_path = rootdir + "lvg.find_vg_state"
        self.get_vg_props_path = rootdir + "lvg.get_vg_props"

        # load sample output
        with open(lsvg_output_path1, "r") as f:
            self.lsvg_output1 = f.read().strip()
        with open(lsvg_output_path2, "r") as f:
            self.lsvg_output2 = f.read().strip()

    def test_no_change_change_vg_type_no_opt(self):
        self.module.params['vg_type'] = "scalable"
        with mock.patch(self.ansible_module_path) as mocked_ansible_module, \
                mock.patch(self.find_vg_state_path) as mocked_find_vg_state, \
                mock.patch(self.get_vg_props_path) as mocked_get_vg_props:

            mocked_ansible_module.return_value = self.module
            mocked_find_vg_state.return_value = self.vg_state
            mocked_get_vg_props.return_value = self.lsvg_output1
            with self.assertRaises(AnsibleExitJson) as result:
                lvg.main()

        result = result.exception.args[0]
        self.assertFalse(result['changed'])
        pattern = r"Volume group is already.*VG type"
        self.assertRegexpMatches(result['msg'], pattern)
        pattern = r"No changes were needed"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_invalid_parameter_mirror_pool_change_vg(self):
        self.module.params['vg_type'] = "scalable"
        self.module.params['mirror_pool'] = "mp1"
        lvg.change_vg(self.module, self.vg_name, self.lsvg_output1)
        result = copy.deepcopy(lvg.result)
        self.assertFalse(result['changed'])
        pattern = r"Attributes major_num, pp_size or mirror_pool"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_invalid_parameter_major_num_change_vg(self):
        self.module.params['vg_type'] = "scalable"
        self.module.params['major_num'] = 5
        lvg.change_vg(self.module, self.vg_name, self.lsvg_output1)
        result = copy.deepcopy(lvg.result)
        self.assertFalse(result['changed'])
        pattern = r"Attributes major_num, pp_size or mirror_pool"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_invalid_parameter_pp_size_change_vg(self):
        self.module.params['vg_type'] = "scalable"
        self.module.params['pp_size'] = 512
        lvg.change_vg(self.module, self.vg_name, self.lsvg_output1)
        result = copy.deepcopy(lvg.result)
        self.assertFalse(result['changed'])
        pattern = r"Attributes major_num, pp_size or mirror_pool"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_change_vg_with_opt(self):
        self.module.params['vg_type'] = "scalable"
        self.module.params['auto_on'] = True
        with mock.patch(self.ansible_module_path) as mocked_ansible_module, \
                mock.patch(self.find_vg_state_path) as mocked_find_vg_state, \
                mock.patch(self.get_vg_props_path) as mocked_get_vg_props:

            mocked_ansible_module.return_value = self.module
            mocked_find_vg_state.return_value = self.vg_state
            mocked_get_vg_props.return_value = self.lsvg_output1
            with self.assertRaises(AnsibleExitJson) as result:
                lvg.main()

        result = result.exception.args[0]
        self.assertFalse(result['changed'])
        pattern = r"No changes were needed"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_change_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params['vg_type'] = "scalable"
        self.module.params['auto_on'] = True
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.change_vg(self.module, self.vg_name, self.lsvg_output1)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to modify volume group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_change_vg(self):
        self.module.params['vg_type'] = "scalable"
        self.module.params['auto_on'] = True
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output2
            lvg.change_vg(self.module, self.vg_name, self.lsvg_output1)
            result = copy.deepcopy(lvg.result)
            self.assertTrue(result['changed'])
            pattern = r"Volume group.*modified"
            self.assertRegexpMatches(result['msg'], pattern)


class TestReduceVG(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvg.result = init_result
        self.vg_name = params['vg_name']
        self.vg_state = True
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        # mocked functions path
        self.get_vg_props_path = rootdir + "lvg.get_vg_props"

        # load sample output
        with open(lsvg_output_path3, "r") as f:
            self.lsvg_output3 = f.read().strip()

    def test_fail_vg_deactivated_reduce_vg(self):
        self.vg_state = False
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.reduce_vg(self.module, self.vg_name, self.vg_state)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Volume group.*is deactivated"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_vg_does_not_exist_reduce_vg(self):
        self.vg_state = None
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.reduce_vg(self.module, self.vg_name, self.vg_state)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Volume group.*does not exist"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_completely_remove_reduce_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params['pvs'] = None
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output3
            with self.assertRaises(AnsibleFailJson) as result:
                lvg.reduce_vg(self.module, self.vg_name, self.vg_state)

            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"Unable to remove"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_completely_remove_reduce_vg(self):
        self.module.params['pvs'] = None
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output3
            lvg.reduce_vg(self.module, self.vg_name, self.vg_state)
            result = copy.deepcopy(lvg.result)
            self.assertTrue(result['changed'])
            pattern = r"Volume group.*removed"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_completely_remove_with_pvs_reduce_vg(self):
        self.module.params['pvs'] = ["hdisk1", "hdisk2", "hdisk3", "hdisk4"]
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output3
            lvg.reduce_vg(self.module, self.vg_name, self.vg_state)
            result = copy.deepcopy(lvg.result)
            self.assertTrue(result['changed'])
            pattern = r"Volume group.*removed"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_remove_some_pvs_reduce_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.params['pvs'] = ["hdisk1", "hdisk2", "hdisk3"]
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output3
            with self.assertRaises(AnsibleFailJson) as result:
                lvg.reduce_vg(self.module, self.vg_name, self.vg_state)

            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"Failed to remove Physical volume"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_some_remove_reduce_vg(self):
        self.module.params['pvs'] = ["hdisk1", "hdisk2", "hdisk3"]
        with mock.patch(self.get_vg_props_path) as mocked_get_vg_props:
            mocked_get_vg_props.return_value = self.lsvg_output3
            lvg.reduce_vg(self.module, self.vg_name, self.vg_state)
            result = copy.deepcopy(lvg.result)
            self.assertTrue(result['changed'])
            pattern = r"Physical volume.*removed from Volume group"
            self.assertRegexpMatches(result['msg'], pattern)


class TestVaryVG(unittest.TestCase):
    def setUp(self):
        global params, init_result
        lvg.result = init_result
        self.vg_name = params['vg_name']
        self.vg_state = True
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        rc, stdout, stderr = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_fail_vg_does_not_exist_vary_vg(self):
        state = "varyon"
        self.vg_state = None
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Volume group.*does not exist"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_vg_already_activated_varyon_vg(self):
        state = "varyon"
        lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)
        result = copy.deepcopy(lvg.result)
        self.assertFalse(result['changed'])
        pattern = r"Volume group.*is already active"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_varyon_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        state = "varyon"
        self.vg_state = False
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to activate volume group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_varyon_vg(self):
        state = "varyon"
        self.vg_state = False
        lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)
        result = copy.deepcopy(lvg.result)
        self.assertTrue(result['changed'])
        pattern = r"Volume group.*activated"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_vg_already_deactivated_varyoff_vg(self):
        state = "varyoff"
        self.vg_state = False
        lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)
        result = copy.deepcopy(lvg.result)
        self.assertFalse(result['changed'])
        pattern = r"Volume group.*is already deactivated"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_varyoff_vg(self):
        rc, stdout, stderr = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        state = "varyoff"
        with self.assertRaises(AnsibleFailJson) as result:
            lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to deactivate volume group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_varyoff_vg(self):
        state = "varyoff"
        self.vg_state = True
        lvg.vary_vg(self.module, state, self.vg_name, self.vg_state)
        result = copy.deepcopy(lvg.result)
        self.assertTrue(result['changed'])
        pattern = r"Volume group.*deactivated"
        self.assertRegexpMatches(result['msg'], pattern)
