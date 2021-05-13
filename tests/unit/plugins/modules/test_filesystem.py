# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import unittest
from unittest import mock
import re

from ansible_collections.ibm.power_aix.plugins.modules import filesystem

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir
)


class TestCheckAttrChange(unittest.TestCase):

    def setUp(self):
        self.filesystem = "/tmp/testfs"
        self.module = mock.Mock()
        self.module.fail_json = fail_json


    def _set_valid_stdout_return_value(self):
        self.lsfs_output = "#MountPoint:Device:Vfs:Nodename:Type:Size:Options:AutoMount:Acct\n/tmp/issue76:/dev/fslv00:jfs2::test_mount:10485760:rw:yes:no\n(lv size 10485760:fs size 10485760:block size 4096:sparse files yes:inline log no:inline log size 0:EAformat v1:Quota no:DMAPI no:VIX yes:EFS no:ISNAPSHOT no:MAXEXT 0:MountGuard no:LFF no)"
        self.module.run_command.return_value = (0, self.lsfs_output, None)
        params = dict()
        params["attributes"] = None
        params["mount_group"] = "test_mount"
        params["permissions"] = "rw"
        params["auto_mount"] = True
        params["account_subsystem"] = False
        self.module.params = params


    def test_failed_to_fetch_curr_fs_attr(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        with self.assertRaises(AnsibleFailJson) as result:
            filesystem.check_attr_change(self.module, self.filesystem)

        result = result.exception.args[0]
        self.assertTrue(result["failed"])
        self.assertEqual(result["rc"], rc)
        self.assertEqual(result["stdout"], stdout)
        self.assertEqual(result["stderr"], stderr)
        pattern = "Failed to fetch"
        self.assertRegexpMatches(result["msg"], pattern)


    def test_mount_group_changed(self):
        self._set_valid_stdout_return_value()
        self.module.params["mount_group"] = "new_test_mount"
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_permissions_changed(self):
        self._set_valid_stdout_return_value()
        self.module.params["permissions"] = "ro"
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_auto_mount_change_yes_to_no(self):
        self._set_valid_stdout_return_value()
        self.module.params["auto_mount"] = False
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_auto_mount_change_no_to_yes(self):
        self._set_valid_stdout_return_value()
        pattern = r"rw:yes:no"
        stdout = re.sub(pattern, "rw:no:no", self.lsfs_output, count=1)
        self.module.run_command.return_value = (0, stdout, None)
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_account_subsystem_change_no_to_yes(self):
        self._set_valid_stdout_return_value()
        self.module.params["account_subsystem"] = True
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_account_subsystem_change_yes_to_no(self):
        self._set_valid_stdout_return_value()
        pattern = r"rw:yes:no"
        stdout = re.sub(pattern, "rw:yes:yes", self.lsfs_output, count=1)
        self.module.run_command.return_value = (0, stdout, None)
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_size_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["size=6G"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_ea_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["ea=v2"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_efs_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["efs=yes"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_dmapi_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["managed=v2"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_maxext_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["maxext=16000000"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_mountguard_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["mountguard=yes"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_vix_changed(self):
        self._set_valid_stdout_return_value()
        attributes = ["vix=no"]
        self.module.params["attributes"] = attributes
        self.assertTrue(filesystem.check_attr_change(self.module, self.filesystem))


    def test_no_change(self):
        self._set_valid_stdout_return_value()
        self.assertFalse(filesystem.check_attr_change(self.module, self.filesystem))



class TestChfs(unittest.TestCase):

    def setUp(self):
        self.filesystem = "/tmp/testfs"
        self.module = mock.Mock()


    def _setup_module_params(self):
        self.module.fail_json = fail_json
        self.module.run_command.return_value = (0, None, None)
        self.module.params = dict()
        self.module.params["attributes"] = None
        self.module.params["account_subsystem"] = False
        self.module.params["auto_mount"] = True
        self.module.params["device"] = self.filesystem
        self.module.params["permissions"] = "rw"
        self.module.params["mount_group"] = "test_mount"
        self.module.params["nfs_server"] = "nfs_server"


    def _setup_chfs_patch_path(self):
        self.check_attr_change_path = rootdir + "filesystem.check_attr_change"
        self.is_nfs_path = rootdir + "filesystem.is_nfs"


    def test_report_no_change_needed(self):
        self._setup_chfs_patch_path()
        with mock.patch(self.check_attr_change_path) as mocked_check_attr_change:
            mocked_check_attr_change.return_value = False
            changed, msg = filesystem.chfs(self.module, self.filesystem)
        self.assertFalse(changed)
        pattern = "No changes needed"
        self.assertRegexpMatches(msg, pattern)


    def test_success_run_chnfsmnt(self):
        self._setup_module_params()
        self._setup_chfs_patch_path()
        with mock.patch(self.check_attr_change_path) as mocked_check_attr_change, \
            mock.patch(self.is_nfs_path) as mocked_is_nfs:

            mocked_check_attr_change.return_value = True
            mocked_is_nfs.return_value = True
            changed, msg = filesystem.chfs(self.module, self.filesystem)
            self.assertTrue(changed)
            pattern = "Modification of filesystem"
            self.assertRegexpMatches(msg, pattern)


    def test_success_run_chfs(self):
        self._setup_module_params()
        self._setup_chfs_patch_path()
        with mock.patch(self.check_attr_change_path) as mocked_check_attr_change, \
            mock.patch(self.is_nfs_path) as mocked_is_nfs:

            mocked_check_attr_change.return_value = True
            mocked_is_nfs.return_value = False
            changed, msg = filesystem.chfs(self.module, self.filesystem)
            self.assertTrue(changed)
            pattern = "Modification of filesystem"
            self.assertRegexpMatches(msg, pattern)


    def test_fail_run_chnfsmnt(self):
        self._setup_module_params()
        self._setup_chfs_patch_path()
        with mock.patch(self.check_attr_change_path) as mocked_check_attr_change, \
            mock.patch(self.is_nfs_path) as mocked_is_nfs:

            mocked_check_attr_change.return_value = True
            mocked_is_nfs.return_value = True

            rc, stdout, stderr = 1, "sample stdout", "sample stderr"
            self.module.run_command.return_value = (rc, stdout, stderr)
            with self.assertRaises(AnsibleFailJson) as result:
                filesystem.chfs(self.module, self.filesystem)

            result = result.exception.args[0]
            self.assertTrue(result["failed"])
            self.assertEqual(result["rc"], rc)
            self.assertEqual(result["stdout"], stdout)
            self.assertEqual(result["stderr"], stderr)
            pattern = "Modification of filesystem"
            self.assertRegexpMatches(result["msg"], pattern)


    def test_fail_run_chfs(self):
        self._setup_module_params()
        self._setup_chfs_patch_path()
        with mock.patch(self.check_attr_change_path) as mocked_check_attr_change, \
            mock.patch(self.is_nfs_path) as mocked_is_nfs:

            mocked_check_attr_change.return_value = True
            mocked_is_nfs.return_value = False

            rc, stdout, stderr = 1, "sample stdout", "sample stderr"
            self.module.run_command.return_value = (rc, stdout, stderr)
            with self.assertRaises(AnsibleFailJson) as result:
                filesystem.chfs(self.module, self.filesystem)

            result = result.exception.args[0]
            self.assertTrue(result["failed"])
            self.assertEqual(result["rc"], rc)
            self.assertEqual(result["stdout"], stdout)
            self.assertEqual(result["stderr"], stderr)
            pattern = "Modification of filesystem"
            self.assertRegexpMatches(result["msg"], pattern)
