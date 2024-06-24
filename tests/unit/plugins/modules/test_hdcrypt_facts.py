# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.ibm.power_aix.plugins.modules import hdcrypt_facts

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir,
    lsvg_output_path1, lspv_output_path1, lslv_output_path1
)

params = {
    "action": '',
    "device": ''
}

init_result = {
    "changed": False,
    "msg": '',
    "cmd": '',
    "stdout": '',
    "stderr": ''
}


class TestLvFacts(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["action"] = "lv"
        params["device"] = "testlv"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        # mocked functions path
        self.lv_exists_path = rootdir + "hdcrypt_facts.lv_exists"
        self.vg_exists_path = rootdir + "hdcrypt_facts.vg_exists"

        # mocked lv_exists return value
        self.lv_exists_val = True
        self.vg_exists_val = True

        # sample lslv and lsvg outputs
        with open(lslv_output_path1, "r") as f:
            self.lslv_output1 = f.read().strip()
        with open(lsvg_output_path1, "r") as f:
            self.lsvg_output1 = f.read().strip()

    # Test for successful retrieval of LV facts - FAIL
    def test_success_get_lv_facts(self):
        msg = hdcrypt_facts.get_lv_facts(self.module, self.module.params["device"])
        testMsg = "Successfully fetched lv facts, check 'lv_facts' for more information."
        self.assertEqual(msg, testMsg)
    
    # Test for failure in running the command - FAIL
    def test_fail_get_lv_facts(self):
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        with mock.patch(self.lv_exists_path) as mocked_lv_exists_path, mock.patch(self.vg_exists_path) as mocked_vg_exists_path:
            mocked_vg_exists_path.return_value = True
            mocked_lv_exists_path.return_value = True
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.get_lv_facts(self.module, self.module.params["device"])
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Could not get the encryption status"
        self.assertRegexpMatches(result['msg'], pattern)

    # Test for failure to get lv facts when no device was provided - FAIL
    def test_fail_no_device_get_lv_facts(self):
        with self.assertRaises(AnsibleFailJson) as result:
            hdcrypt_facts.get_lv_facts(self.module, "")
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        testMsg = "To get lv_facts, you need to specify either a LV or a VG"
        self.assertEqual(result['msg'], testMsg)

    # Test for failure when the provided device is not present - FAIL
    def test_fail_device_not_present_get_lv_facts(self):
        with mock.patch(self.lv_exists_path) as mocked_lv_exists_path, mock.patch(self.vg_exists_path) as mocked_vg_exists_path:
            mocked_lv_exists_path.return_value = False
            mocked_vg_exists_path.return_value = False
            with self.assertRaises(AnsibleFailJson) as result:
                msg = hdcrypt_facts.get_lv_facts(self.module, self.module.params["device"])
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "lv or vg does not exist"
        self.assertRegexpMatches(result['msg'], pattern)

class TestVgFacts(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["action"] = "vg"
        params["device"] = "vg00"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        # mocked functions path
        self.vg_exists_path = rootdir + "hdcrypt_facts.vg_exists"

        # mocked vg_exists return value
        self.vg_exists_val = True

    # Test for successful retrieval of VG facts
    def test_success_get_vg_facts(self):
        msg = hdcrypt_facts.get_vg_facts(self.module, self.module.params['device'])
        testMsg = "Successfully fetched vg facts, check 'vg_facts' for more information"
        self.assertEqual(msg, testMsg)

    # Test for failure in running the command
    def test_fail_get_vg_facts(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with mock.patch(self.vg_exists_path) as mocked_vg_exists_path:
            mocked_vg_exists_path.return_value = True
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.get_vg_facts(self.module, self.module.params["device"])
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Could not get the encryption status"
        self.assertRegexpMatches(result['msg'], pattern)
    
    # Test for failure when the provided device is not present
    def test_fail_device_not_present_get_vg_facts(self):
        self.vg_exists_val = False
        with mock.patch(self.vg_exists_path) as mocked_vg_exists_path:
            mocked_vg_exists_path.side_effect = [
                self.vg_exists_val
            ]
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.get_vg_facts(self.module, self.module.params["device"])
            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = "vg does not exist"
            self.assertRegexpMatches(result['msg'], pattern)

    # get the test case when vg name is not defined. Need to make changes in module, separate checks for both cases.


class TestPvFacts(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["action"] = "pv"
        params["device"] = "hdisk0"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        # mocked functions path
        self.pv_exists_path = rootdir + "hdcrypt_facts.pv_exists"

        # mocked vg_exists return value
        self.pv_exists_val = True

    # Test for successful retrieval of PV facts
    def test_success_get_vg_facts(self):
        msg = hdcrypt_facts.get_pv_facts(self.module, self.module.params['device'])
        testMsg = "Successfully fetched pv facts, check 'pv_facts' for more information"
        self.assertEqual(msg, testMsg)

    # Test for failure in running the command
    def test_fail_get_pv_facts(self):
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        with mock.patch(self.pv_exists_path) as mocked_pv_exists_path:
            mocked_pv_exists_path.return_value = True
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.get_pv_facts(self.module, self.module.params["device"])
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "Could not get the encryption status"
        self.assertRegexpMatches(result['msg'], pattern)

    # Test for failure when no device was provided
    def test_fail_no_device_get_pv_facts(self):
        with self.assertRaises(AnsibleFailJson) as result:
            hdcrypt_facts.get_pv_facts(self.module, "")
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "You need to specify a PV"
        self.assertRegexpMatches(result['msg'], pattern)

    # Test for failure when the provided device is not present
    def test_fail_device_not_present_get_pv_facts(self):
        self.pv_exists_val = False
        with mock.patch(self.pv_exists_path) as mocked_pv_exists_path:
            mocked_pv_exists_path.side_effect = [
                self.pv_exists_val
            ]
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.get_pv_facts(self.module, self.module.params["device"])
            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = "PV does not exist"
            self.assertRegexpMatches(result['msg'], pattern)


class TestMetaFacts(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["action"] = "meta"
        params["device"] = "testlv"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        # mocked functions path
        self.lv_exists_path = rootdir + "hdcrypt_facts.lv_exists"
        self.vg_exists_path = rootdir + "hdcrypt_facts.vg_exists"
        self.pv_exists_path = rootdir + "hdcrypt_facts.pv_exists"

    # Test for successful retrieval of Meta facts
    def test_success_get_vg_facts(self):
        msg = hdcrypt_facts.disp_meta(self.module, self.module.params['device'])
        testMsg = "Successfully fetched meta facts, check 'meta_facts' for more information."
        self.assertEqual(msg, testMsg)

    # Test for failure in running the command - FAIL - Changed
    def test_fail_disp_meta(self):
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        with mock.patch(self.lv_exists_path) as mocked_lv, mock.patch(self.vg_exists_path) as mocked_vg, mock.patch(self.pv_exists_path) as mocked_pv:
            mocked_lv.return_value = True
            mocked_pv.return_value = True
            mocked_vg.return_value = True
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.disp_meta(self.module, self.module.params["device"])
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "command failed"
        self.assertRegexpMatches(result['msg'], pattern)

    # Test for failure when no device was provided - FAIL - Changed
    def test_fail_no_device_disp_meta(self):
        with self.assertRaises(AnsibleFailJson) as result:
            hdcrypt_facts.disp_meta(self.module, "")
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        testMsg = "You need to provide a device(lv/vg/pv) for getting the meta information."
        self.assertEqual(result['msg'], testMsg)

    # Test for failure when the provided device is not present - FAIL - Changed
    def test_fail_device_not_present_disp_meta(self):
        with mock.patch(self.lv_exists_path) as mocked_lv, mock.patch(self.vg_exists_path) as mocked_vg, mock.patch(self.pv_exists_path) as mocked_pv:
            mocked_lv.return_value = False
            mocked_pv.return_value = False
            mocked_vg.return_value = False
            with self.assertRaises(AnsibleFailJson) as result:
                hdcrypt_facts.disp_meta(self.module, self.module.params["device"])
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = "not a valid lv, vg or pv"
        self.assertRegexpMatches(result['msg'], pattern)


class TestConvFacts(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["action"] = "conv"
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

    # Test for successful retrieval of conv facts
    def test_success_disp_conv(self):
        msg = hdcrypt_facts.disp_conv(self.module)
        testMsg = "Successfully fetched conversion facts, check 'conv_facts' for more information."
        self.assertEqual(msg, testMsg)
    
    # Test for failure in retrieval of conv facts
    def test_fail_disp_conv(self):
        rc, stdout, stderr = 1, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr) 
        with self.assertRaises(AnsibleFailJson) as result:
            hdcrypt_facts.disp_conv(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])
        pattern = r"The following command failed"
        self.assertRegexpMatches(result['msg'], pattern)
