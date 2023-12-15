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
    rootdir, lsfs_output_path2, lsfs_output_path3, lsfs_output_path4,
    df_output_path1, df_output_path2, df_output_path3, mount_output_path1
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

class TestIsMountGroupMounted(unittest.TestCase):
    def setUp(self):
        global params, init_result
        self.mount_group = "local"
        self.module = mock.Mock()
        self.module.params = params
        self.module.params['fs_type'] = self.mount_group
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.result = init_result
        # load sample output
        with open(lsfs_output_path4, "r") as f:
            self.lsfs_output4 = f.read().strip()
        with open(df_output_path1, "r") as f:
            self.df_output1 = f.read().strip()
        with open(df_output_path2, "r") as f:
            self.df_output2 = f.read().strip()
        with open(df_output_path3, "r") as f:
            self.df_output3 = f.read().strip()

    def test_fail_fetch_all_fs_in_mount_group(self):
        (rc, stdout, stderr) = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            mount.is_mount_group_mounted(self.module, self.mount_group)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to fetch filesystem name in mount group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_fs_in_mount_group(self):
        (rc, stdout, stderr) = (0, "", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            mount.is_mount_group_mounted(self.module, self.mount_group)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"There are no filesytems in.*mount group"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_fetch_mounted_fs(self):
        self.module.run_command.side_effect = [
            (0, self.lsfs_output4, "sample stderr"),
            (1, "sample stdout", "sample stderr")
        ]
        with self.assertRaises(AnsibleFailJson) as result:
            mount.is_mount_group_mounted(self.module, self.mount_group)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to get the filesystem name"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_all_fs_in_mount_group_are_mounted(self):
        expected_mnt_grp_mounted = {
            "/tmp/testfs": True,
            "/tmp/servnfs": True
        }
        self.module.run_command.side_effect = [
            (0, self.lsfs_output4, "sample stderr"),
            (0, self.df_output3, "sample stderr")
        ]
        actual_mnt_grp_mounted = mount.is_mount_group_mounted(self.module, self.mount_group)
        actual_mnt_pts = actual_mnt_grp_mounted.keys()
        self.assertEqual(
            len(expected_mnt_grp_mounted),
            len(actual_mnt_grp_mounted)
        )
        for mnt_pt in expected_mnt_grp_mounted.keys():
            self.assertTrue(mnt_pt in actual_mnt_pts)
            expected_is_mounted = expected_mnt_grp_mounted[mnt_pt]
            actual_is_mounted = actual_mnt_grp_mounted[mnt_pt]
            self.assertEqual(expected_is_mounted, actual_is_mounted)

    def test_some_mounted_some_unmounted_in_mount_group(self):
        expected_mnt_grp_mounted = {
            "/tmp/testfs": True,
            "/tmp/servnfs": False 
        }
        self.module.run_command.side_effect = [
            (0, self.lsfs_output4, "sample stderr"),
            (0, self.df_output1, "sample stderr")
        ]
        actual_mnt_grp_mounted = mount.is_mount_group_mounted(self.module, self.mount_group)
        actual_mnt_pts = actual_mnt_grp_mounted.keys()
        self.assertEqual(
            len(expected_mnt_grp_mounted),
            len(actual_mnt_grp_mounted)
        )
        for mnt_pt in expected_mnt_grp_mounted.keys():
            self.assertTrue(mnt_pt in actual_mnt_pts)
            expected_is_mounted = expected_mnt_grp_mounted[mnt_pt]
            actual_is_mounted = actual_mnt_grp_mounted[mnt_pt]
            self.assertEqual(expected_is_mounted, actual_is_mounted)
        
    def test_all_unmounted_in_mount_group(self):
        expected_mnt_grp_mounted = {
            "/tmp/testfs": False,
            "/tmp/servnfs": False 
        }
        self.module.run_command.side_effect = [
            (0, self.lsfs_output4, "sample stderr"),
            (0, self.df_output2, "sample stderr")
        ]
        actual_mnt_grp_mounted = mount.is_mount_group_mounted(self.module, self.mount_group)
        actual_mnt_pts = actual_mnt_grp_mounted.keys()
        self.assertEqual(
            len(expected_mnt_grp_mounted),
            len(actual_mnt_grp_mounted)
        )
        for mnt_pt in expected_mnt_grp_mounted.keys():
            self.assertTrue(mnt_pt in actual_mnt_pts)
            expected_is_mounted = expected_mnt_grp_mounted[mnt_pt]
            actual_is_mounted = actual_mnt_grp_mounted[mnt_pt]
            self.assertEqual(expected_is_mounted, actual_is_mounted)


class TestIsFSPathMounted(unittest.TestCase):
    def setUp(self):
        global params, init_result
        self.module = mock.Mock()
        self.module.params = params
        self.mount_dir = self.module.params["mount_dir"]
        self.mount_over_dir = self.module.params["mount_over_dir"]
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
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
        with open(mount_output_path1, "r") as f:
            self.mount_output1 = f.read().strip()

    def test_fail_missing_mount_dir_and_mount_over_dir(self):
        self.mount_dir = self.module.params["mount_dir"]
        self.mount_over_dir = self.module.params["mount_over_dir"]
        with self.assertRaises(AnsibleFailJson) as result:
            mount.is_fspath_mounted(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Unexpected module FAILURE: one of the following is missing"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_true_fs_mounted(self):
        self.module.params["mount_dir"] = "/tmp/testfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.mount_output1, "sample stderr")
        ]
        self.assertTrue(
            mount.is_fspath_mounted(self.module)
        )

    def test_false_fs_mounted(self):
        self.module.params["mount_dir"] = "/tmp/testfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output2, "sample stderr"),
            (0, self.mount_output1, "sample stderr")
        ]
        self.assertFalse(
            mount.is_fspath_mounted(self.module)
        )

    def test_false_nfs_mounted(self):
        self.module.params["mount_dir"] = "/tmp/clientnfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output3, "sample stderr"),
            (0, self.mount_output1, "sample stderr")
        ]
        self.assertFalse(
            mount.is_fspath_mounted(self.module)
        )

    def test_false_nfs_mounted_both_dir_present(self):
        self.module.params["mount_dir"] = "/tmp/servnfs"
        self.module.params["mount_over_dir"] = "/tmp/clientnfs"
        self.mount_dir = self.module.params["mount_dir"]
        self.mount_over_dir = self.module.params["mount_over_dir"]
        self.module.run_command.side_effect = [
            (0, self.lsfs_output3, "sample stderr"),
            (0, self.mount_output1, "sample stderr")
        ]
        self.assertFalse(
            mount.is_fspath_mounted(self.module)
        )


class TestFSList(unittest.TestCase):
    def setUp(self):
        global params, init_result
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.result = init_result
        # mocked functions path
        self.is_fspath_mounted_path = rootdir + "mount.is_fspath_mounted"

    def test_fail_list_mounted_fs(self):
        (rc, stdout, stderr) = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            mount.fs_list(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"Failed to list mounted filesystems"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_success_list_mounted_fs(self):
        mount.fs_list(self.module)
        result = copy.deepcopy(mount.result)
        self.assertFalse(result['changed'])
        pattern = r"Mounted filesystems listed in stdout"
        self.assertRegexpMatches(result['msg'], pattern)


class TestMount(unittest.TestCase):
    def setUp(self):
        global params, init_result
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.result = init_result
        # mocked functions path
        self.is_fspath_mounted_path = rootdir + "mount.is_fspath_mounted"
        self.is_mount_group_mounted_path = rootdir + "mount.is_mount_group_mounted"
        # mocked is_mount_group_mounted return value
        self.init_mnt_grp_mounted = {
            "/tmp/testfs": False,
            "/tmp/servnfs": False
        }
        self.final_mnt_grp_mounted = {
            "/tmp/testfs": True,
            "/tmp/servnfs": True
        }

    def test_fail_mount_on_mount_group(self):
        self.module.params['fs_type'] = "local"
        self.final_mnt_grp_mounted['/tmp/servnfs'] = False
        with mock.patch(self.is_mount_group_mounted_path) as mocked_is_mount_group_mounted:
            mocked_is_mount_group_mounted.side_effect = [
                self.init_mnt_grp_mounted,
                self.final_mnt_grp_mounted
            ]
            with self.assertRaises(AnsibleFailJson) as result:
                mount.mount(self.module)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"Mount failed - '/tmp/servnfs'"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_all_fs_in_mount_group_already_mounted(self):
        self.module.params['fs_type'] = "local"
        self.init_mnt_grp_mounted['/tmp/testfs'] = True
        self.init_mnt_grp_mounted['/tmp/servnfs'] = True
        with mock.patch(self.is_mount_group_mounted_path) as mocked_is_mount_group_mounted:
            mocked_is_mount_group_mounted.side_effect = [
                self.init_mnt_grp_mounted,
                self.final_mnt_grp_mounted
            ]
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertFalse(result['changed'])
            pattern = r"'/tmp/testfs' already mounted"
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = r"'/tmp/servnfs' already mounted"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_some_fs_already_mounted_some_successfully_mounted(self):
        self.module.params['fs_type'] = "local"
        self.init_mnt_grp_mounted['/tmp/testfs'] = True
        with mock.patch(self.is_mount_group_mounted_path) as mocked_is_mount_group_mounted:
            mocked_is_mount_group_mounted.side_effect = [
                self.init_mnt_grp_mounted,
                self.final_mnt_grp_mounted
            ]
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertTrue(result['changed'])
            pattern = r"'/tmp/testfs' already mounted"
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = r"Mount successful - '/tmp/servnfs'"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_success_mount_by_mount_group(self):
        self.module.params['fs_type'] = "local"
        with mock.patch(self.is_mount_group_mounted_path) as mocked_is_mount_group_mounted:
            mocked_is_mount_group_mounted.side_effect = [
                self.init_mnt_grp_mounted,
                self.final_mnt_grp_mounted
            ]
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertTrue(result['changed'])
            pattern = r"Mount successful - '/tmp/testfs'"
            self.assertRegexpMatches(result['msg'], pattern)
            pattern = r"Mount successful - '/tmp/servnfs'"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_mount_dir_and_mount_over_dir_given_already_mounted(self):
        self.module.params['mount_dir'] = "/tmp/servnfs"
        self.module.params['mount_over_dir'] = "/tmp/clientnfs"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = True
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertFalse(result['changed'])
            pattern = r"'/tmp/clientnfs' already mounted"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_mount_over_dir_already_mounted(self):
        self.module.params['mount_over_dir'] = "/tmp/testfs"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = True
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertFalse(result['changed'])
            pattern = r"'/tmp/testfs' already mounted"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_mount_dir_already_mounted(self):
        self.module.params['mount_dir'] = "/tmp/testfs"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = True
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertFalse(result['changed'])
            pattern = r"'/tmp/testfs' already mounted"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_mount_fs(self):
        self.module.params['mount_dir'] = "/tmp/testfs"
        (rc, stdout, stderr) = (1, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = False 
            with self.assertRaises(AnsibleFailJson) as result:
                mount.mount(self.module)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"Mount failed"
            self.assertRegexpMatches(result['msg'], pattern)
    
    def test_success_mount_fs(self):
        self.module.params['mount_dir'] = "/tmp/testfs"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = False 
            mount.mount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertTrue(result['changed'])
            pattern = r"Mount successful"
            self.assertRegexpMatches(result['msg'], pattern)
    

class TestUmount(unittest.TestCase):
    def setUp(self):
        global params, init_result
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.result = init_result
        # mocked functions path
        self.is_fspath_mounted_path = rootdir + "mount.is_fspath_mounted"

    def test_no_change_unmount_all_remote_fs(self):
        self.module.params['mount_all'] = "remote"
        (rc, stdout) = (1, "sample stdout")
        stderr = "umount: 0506-347 Cannot find anything to unmount."
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.umount(self.module)
        result = copy.deepcopy(mount.result)
        self.assertFalse(result['changed'])
        pattern = r"There are no remote filesystems to unmount"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_unmount_remote_fs_by_node(self):
        self.module.params['node'] = "remote_node"
        (rc, stdout) = (1, "sample stdout")
        stderr = "umount: 0506-347 Cannot find anything to unmount."
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.umount(self.module)
        result = copy.deepcopy(mount.result)
        self.assertFalse(result['changed'])
        pattern = r"There are no remote filesystems to unmount"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_unmount_by_mount_group(self):
        self.module.params['fs_type'] = "local"
        (rc, stdout) = (1, "sample stdout")
        stderr = "umount: 0506-347 Cannot find anything to unmount."
        self.module.run_command.return_value = (rc, stdout, stderr)
        mount.umount(self.module)
        result = copy.deepcopy(mount.result)
        self.assertFalse(result['changed'])
        pattern = r"There are no remote filesystems to unmount"
        self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_mount_over_dir(self):
        self.module.params['mount_over_dir'] = "/tmp/nfs_client"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = False
            mount.umount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertFalse(result['changed'])
            pattern = r"is not mounted"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_no_change_mount_dir_and_mount_over_dir(self):
        self.module.params['mount_over_dir'] = "/tmp/nfs_client"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = False
            mount.umount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertFalse(result['changed'])
            pattern = r"'/tmp/nfs_client' is not mounted"
            self.assertRegexpMatches(result['msg'], pattern)

    def test_fail_umount(self):
        self.module.params['mount_over_dir'] = "/tmp/testfs"
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = True
            with self.assertRaises(AnsibleFailJson) as result:
                mount.umount(self.module)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"Unmount failed"
            self.assertRegexpMatches(result['msg'], pattern)
        
    def test_success_umount(self):
        self.module.params['mount_over_dir'] = "/tmp/testfs"
        with mock.patch(self.is_fspath_mounted_path) as mocked_is_fspath_mounted:
            mocked_is_fspath_mounted.return_value = True
            mount.umount(self.module)
            result = copy.deepcopy(mount.result)
            self.assertTrue(result['changed'])
            pattern = r"Unmount successful"
            self.assertRegexpMatches(result['msg'], pattern)