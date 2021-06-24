# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import copy

from ansible_collections.ibm.power_aix.plugins.modules import mount

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
    rootdir, lsfs_output_path2, lsfs_output_path3, df_output_path1, 
    df_output_path2
)


params = {
    "state": "mount",
    "mount_dir": None,
    "mount_over_dir": None,
    "node": None,
    "mount_all": None,
    "force": False,
    "alternate_fs": None,
    "removable_fs": False,
    "read_only": False,
    "fs_type": None,
    "vfsname": None,
    "options": None
}

init_result = {
    "changed": False,
    "msg": '',
    "cmd": '',
    "stdout": '',
    "stderr": ''
}

class TestIsFSPathMounted(unittest.TestCase):
    def setUp(self):
        global params, init_result
        self.module = mock.Mock()
        self.module.params = params
        self.mount_dir = self.module.params["mount_dir"]
        self.mount_over_dir = self.module.params["mount_over_dir"]
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stdin")
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.result = init_result
        # load sample output
        with open(lsfs_output_path2, "r") as f:
            self.lsfs_output2 = f.read().strip()
        with open(lsfs_output_path3, "r") as f:
            self.lsfs_output3 = f.read().strip()
        with open(df_output_path1, "r") as f:
            self.df_output1 = f.read().strip()
        with open(df_output_path2, "r") as f:
            self.df_output2 = f.read().strip()

    def test_fail_missing_mount_dir_and_mount_over_dir(self):
        self.mount_dir = self.module.params["mount_dir"]
        self.mount_over_dir = self.module.params["mount_over_dir"]
        with self.assertRaises(AnsibleFailJson) as result:
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Unexpected module FAILURE: one of the following is missing"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_is_none_mount_dir(self):
        self.module.params["mount_dir"] = "/tmp/testfs"
        self.mount_dir = self.module.params["mount_dir"]
        (rc, stdout, stderr) = (1, "sample stdout", "sample stdin")
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.assertIsNone(
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        )
        
    def test_is_none_mount_over_dir(self):
        self.module.params["mount_over_dir"] = "/tmp/testfs"
        self.mount_over_dir = self.module.params["mount_over_dir"]
        (rc, stdout, stderr) = (1, "sample stdout", "sample stdin")
        self.module.run_command.return_value = (rc, stdout, stderr)
        self.assertIsNone(
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        )

    def test_fail_fetching_mounted_fs_list(self):
        self.module.params["mount_dir"] = "/tmp/testfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output2, "sample stderr"),
            (1, "sample stdout", "sample stderr")
        ]
        with self.assertRaises(AnsibleFailJson) as result:
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to get the filesystem name"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_true_fs_mounted(self):
        self.module.params["mount_dir"] = "/tmp/testfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output2, "sample stderr"),
            (0, self.df_output1, "sample stderr")
        ]
        self.assertTrue(
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        )

    def test_true_nfs_mounted(self):
        self.module.params["mount_dir"] = "/tmp/clientnfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output3, "sample stderr"),
            (0, self.df_output2, "sample stderr")
        ]
        self.assertTrue(
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        )

    def test_false_fs_mounted(self):
        self.module.params["mount_dir"] = "/tmp/testfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output2, "sample stderr"),
            (0, self.df_output2, "sample stderr")
        ]
        self.assertFalse(
            mount.is_fspath_mounted(self.module, self.mount_dir, self.mount_over_dir)
        )
