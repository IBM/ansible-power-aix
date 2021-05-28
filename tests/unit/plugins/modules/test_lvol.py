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
    AnsibleFailJson, fail_json, rootdir
)


params = {
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


class TestCreateModifyLV(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.module.fail_json = fail_json
        self.lv_exist_path = rootdir + "lvol.lv_exists"

    def _prepare_create_lv(self, fail=False):
        # initialize global variable in lvol module
        lvol.result = {
            "changed": False,
            "msg": '',
            "cmd": '',
            "stdout": '',
            "stderr": ''
        }

        # compose the command that is ran in lvol module
        self.cmd = "mklv -t %s -y %s -c %s -e %s %s %s %s %s %s" % (
            self.module.params["lv_type"],
            self.module.params["lv"],
            self.module.params["copies"],
            "x" if self.module.params["policy"] == "maximum" else "m",
            self.module.params["extra_opts"],
            "" if self.module.params["strip_size"] is None else
            "-S " + self.module.params["strip_size"],
            self.module.params["vg"],
            self.module.params["num_of_logical_partitions"],
            "" if self.module.params["pv_list"] is None else
            " ".join(self.module.params["pv_list"])
        )

        if fail:
            rc, stdout, stderr = 1, "sample stdout", "sample stderr"
            self.module.run_command.return_value = (rc, stdout, stderr)

    def _assert_result(self, result, fail=False):
        self.module.run_command.assert_called_once_with(self.cmd)
        self.assertEqual(result["cmd"], self.cmd)
        self.assertEqual(result["stdout"], "sample stdout")
        self.assertEqual(result["stderr"], "sample stderr")
        if not fail:
            self.assertTrue(result["changed"])
            self.assertEqual(result["rc"], 0)
            pattern = r"Logical volume.*created"
        else:
            self.assertFalse(result["changed"])
            self.assertTrue(result["failed"])
            self.assertEqual(result["rc"], 1)
            pattern = r"Failed to create"
        self.assertRegexpMatches(result["msg"], pattern)

    def test_success_create_striped_lv(self):
        self.module.params["strip_size"] = "4K"
        self._prepare_create_lv()
        with mock.patch(self.lv_exist_path) as mocked_lv_exists:
            mocked_lv_exists.return_value = False
            lvol.create_modify_lv(self.module)
            result = copy.deepcopy(lvol.result)

        self._assert_result(result)

    def test_success_create_non_striped_lv(self):
        self._prepare_create_lv()
        with mock.patch(self.lv_exist_path) as mocked_lv_exists:
            mocked_lv_exists.return_value = False
            lvol.create_modify_lv(self.module)
            result = copy.deepcopy(lvol.result)

        self._assert_result(result)

    def test_fail_create_striped_lv(self):
        self.module.params["strip_size"] = "4K"
        self._prepare_create_lv(fail=True)
        with mock.patch(self.lv_exist_path) as mocked_lv_exists:
            mocked_lv_exists.return_value = False
            with self.assertRaises(AnsibleFailJson) as result:
                lvol.create_modify_lv(self.module)

        result = result.exception.args[0]
        self._assert_result(result, fail=True)

    def test_fail_create_non_striped_lv(self):
        self._prepare_create_lv(fail=True)
        with mock.patch(self.lv_exist_path) as mocked_lv_exists:
            mocked_lv_exists.return_value = False
            with self.assertRaises(AnsibleFailJson) as result:
                lvol.create_modify_lv(self.module)

        result = result.exception.args[0]
        self._assert_result(result, fail=True)
