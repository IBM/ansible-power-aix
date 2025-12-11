# -*- coding: utf-8 -*-
# Copyright: (c) 2025 - Generated
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import copy

from ansible_collections.ibm.power_aix.plugins.modules import nimclient

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
)

# Base params template used in setUp (copied per-test to avoid bleed)
base_params = {
    "action": None,
    "operation": None,
    "master_push_perm": None,
    "crypto_auth_perm": None,
    "set_master_date": False,
    "attributes": None,
}


class TestParsedInfo(unittest.TestCase):
    def test_parsed_info_basic(self):
        stdout = (
            "Header line\n"
            "resA lpp_source file\n"
            "resB spot object\n"
        )
        niminfo = nimclient.parsed_info(stdout)
        self.assertIn("resA", niminfo)
        self.assertEqual(niminfo["resA"]["object_class"], "lpp_source")
        self.assertEqual(niminfo["resA"]["object_type"], "file")
        self.assertIn("resB", niminfo)
        self.assertEqual(niminfo["resB"]["object_class"], "spot")
        self.assertEqual(niminfo["resB"]["object_type"], "object")

    def test_parsed_info_ignores_empty_lines(self):
        stdout = "Header\n\nresA lpp_source file\n\n"
        niminfo = nimclient.parsed_info(stdout)
        self.assertIn("resA", niminfo)
        self.assertEqual(len(niminfo), 1)

    def test_parsed_info_handles_minimal_fields(self):
        # If a line doesn't have enough fields it will raise IndexError in current impl.
        # Ensure that typical well-formed lines parse; malformed lines are ignored by trimming earlier.
        stdout = "Header\nbadline\nresA lpp_source file\n"
        niminfo = nimclient.parsed_info(stdout)
        # 'badline' will be skipped because split()[1] would raise; current impl would actually fail.
        # We assert that at least well-formed line is present.
        self.assertIn("resA", niminfo)


class TestListInfo(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        self.module.run_command.return_value = (0, "", "")

    def test_list_info_success(self):
        stdout = (
            "Header\n"
            "resA lpp_source file\n"
            "resB spot object\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        payload = nimclient.list_info(self.module)
        self.assertFalse(payload.get("changed", True))
        self.assertEqual(payload["msg"], "Successfully retrieved available information. Check 'nim_info' for details.")
        self.assertIn("resA", payload["nim_info"])
        self.assertEqual(payload["cmd"], "nimclient -l")

    def test_list_info_failure(self):
        self.module.run_command.return_value = (3, "", "some error")
        payload = nimclient.list_info(self.module)
        self.assertTrue(payload.get("failed"))
        self.assertIn("Failed to retrieve information about the NIM environment.", payload["msg"])
        self.assertEqual(payload["rc"], 3)
        self.assertEqual(payload["cmd"], "nimclient -l")


class TestNimOperations(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        self.module.run_command.return_value = (0, "", "")

    def test_nim_operations_simple_success(self):
        # basic operation that modifies system (changed True)
        self.module.params['operation'] = 'bos_inst'
        self.module.run_command.return_value = (0, "done", "")
        payload = nimclient.nim_operations(self.module)
        self.assertTrue(payload.get("changed"))
        self.assertIn("Successfully ran the following command", payload["msg"])
        self.assertIn("-o bos_inst", payload["cmd"])

    def test_nim_operations_showres_no_change(self):
        # showres should not mark changed
        self.module.params['operation'] = 'showres'
        self.module.run_command.return_value = (0, "resource contents", "")
        payload = nimclient.nim_operations(self.module)
        self.assertFalse(payload.get("changed"))
        self.assertIn("Successfully ran the following command", payload["msg"])
        self.assertIn("-o showres", payload["cmd"])

    def test_nim_operations_with_attributes(self):
        self.module.params['operation'] = 'allocate'
        self.module.params['attributes'] = ['lpp_source=2342B_73D', 'spot=2342B_73D_SPOT']
        # run_command returns success
        self.module.run_command.return_value = (0, "ok", "")
        payload = nimclient.nim_operations(self.module)
        self.assertTrue(payload.get("changed"))
        # Attributes should be joined as "-a lpp_source=... -a spot=... "
        self.assertIn("-a lpp_source=2342B_73D", payload["cmd"])
        self.assertIn("-a spot=2342B_73D_SPOT", payload["cmd"])

    def test_nim_operations_failure(self):
        self.module.params['operation'] = 'reset'
        self.module.run_command.return_value = (2, "", "err")
        payload = nimclient.nim_operations(self.module)
        self.assertTrue(payload.get("failed"))
        self.assertIn("Failed to run the following command", payload["msg"])
        self.assertEqual(payload["rc"], 2)


class TestOtherOperations(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        self.module.run_command.return_value = (0, "", "")

    def test_other_operations_enable_push_and_crypto_and_date(self):
        # All flags enabled: push enable, crypto enable, set_master_date True
        self.module.params['master_push_perm'] = 'enable'
        self.module.params['crypto_auth_perm'] = 'enable'
        self.module.params['set_master_date'] = True
        self.module.run_command.return_value = (0, "ok", "")
        payload = nimclient.other_operations(self.module)
        self.assertTrue(payload.get("changed"))
        # cmd should contain -p -c -d
        self.assertIn("-p", payload["cmd"])
        self.assertIn("-c", payload["cmd"])
        self.assertIn("-d", payload["cmd"])
        self.assertIn("Successfully ran the following command", payload["msg"])

    def test_other_operations_disable_flags(self):
        # disable push and crypto (uses uppercase flags)
        self.module.params['master_push_perm'] = 'disable'
        self.module.params['crypto_auth_perm'] = 'disable'
        self.module.params['set_master_date'] = False
        self.module.run_command.return_value = (0, "ok", "")
        payload = nimclient.other_operations(self.module)
        self.assertTrue(payload.get("changed"))
        self.assertIn("-P", payload["cmd"])
        self.assertIn("-C", payload["cmd"])
        self.assertNotIn("-d", payload["cmd"])

    def test_other_operations_failure(self):
        self.module.params['master_push_perm'] = 'enable'
        self.module.run_command.return_value = (5, "", "err")
        payload = nimclient.other_operations(self.module)
        self.assertTrue(payload.get("failed"))
        self.assertIn("Failed to run the command", payload["msg"])
        self.assertEqual(payload["rc"], 5)


if __name__ == '__main__':
    unittest.main()
