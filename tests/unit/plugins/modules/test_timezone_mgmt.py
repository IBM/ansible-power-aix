#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
from unittest.mock import patch
import copy

from ansible_collections.ibm.power_aix.plugins.modules import timezone_mgmt

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
)

# Base params template used in setUp (copied per-test to avoid bleed)
base_params = {
    "action": None,
    "timezone": None,
    "db_location": None,
}


class TestListVersions(unittest.TestCase):
    def setUp(self):
        global base_params
        self.module = mock.Mock()
        # copy to ensure each test gets a fresh dict
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        # default run_command result; tests override as needed
        (rc, stdout, stderr) = (0, "", "")
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_list_versions_success(self):
        # stdout includes an available versions block and current version
        stdout = (
            "Available Versions:\n"
            "1 : 2025b\n"
            "2 : 2024a\n"
            "Current database version is 2024a\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        payload = timezone_mgmt.list_versions(self.module)

        self.assertFalse(payload.get("changed", True))
        self.assertEqual(payload["msg"], "Successfully retrieved available versions.")
        tz_details = payload["timezone_details"]
        self.assertIn("2025b", tz_details["available_versions"])
        # current_version uses current.group(1) which in module returns the token after regex;
        # the module sets current_version to current.group(1) if found, else "Unknown"
        # In this stdout the regex captures the version string; ensure it's present
        self.assertEqual(tz_details["current_version"], "2024a")

    def test_list_versions_command_failure(self):
        self.module.run_command.return_value = (2, "", "some error")
        payload = timezone_mgmt.list_versions(self.module)
        self.assertTrue(payload.get("failed"))
        self.assertIn("Failed to retrieve available timezone versions.", payload["msg"])
        self.assertEqual(payload["rc"], 2)

    def test_list_versions_tool_busy(self):
        # If stdout contains "Another session of the tool is running" module.fail_json is called
        stdout = "Another session of the tool is running - please wait"
        self.module.run_command.return_value = (0, stdout, "")
        with self.assertRaises(AnsibleFailJson) as cm:
            timezone_mgmt.list_versions(self.module)
        result = cm.exception.args[0]
        self.assertTrue(result["msg"].startswith("Another session of the tool is running"))

    def test_list_versions_no_current_version(self):
        # If Current database version isn't found, current_version should be "Unknown"
        stdout = "Available Versions:\n1 : 2026a\n"
        self.module.run_command.return_value = (0, stdout, "")
        payload = timezone_mgmt.list_versions(self.module)
        self.assertEqual(payload["timezone_details"]["current_version"], "Unknown")


class TestUpdateTimezone(unittest.TestCase):
    def setUp(self):
        global base_params
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        self.module.run_command.return_value = (0, "", "")

    def test_update_timezone_no_change_when_same_as_current(self):
        # Patch list_versions to return current == requested timezone
        self.module.params['timezone'] = "2025b"
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.timezone_mgmt.list_versions') as mocked_lv:
            mocked_lv.return_value = {
                "timezone_details": {
                    "available_versions": ["2025b", "2024a"],
                    "current_version": "2025b"
                }
            }
            result = timezone_mgmt.update_timezone(self.module)
        self.assertFalse(result.get("changed", True))
        self.assertEqual(result["msg"], "No need to change, provided timezone is already set.")

    def test_update_timezone_not_found(self):
        # requested tz not in available_versions
        self.module.params['timezone'] = "2030z"
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.timezone_mgmt.list_versions') as mocked_lv:
            mocked_lv.return_value = {
                "timezone_details": {
                    "available_versions": ["2025b", "2024a"],
                    "current_version": "2024a"
                }
            }
            result = timezone_mgmt.update_timezone(self.module)
        self.assertTrue(result.get("failed"))
        self.assertIn("Timezone not found", result["msg"])

    def test_update_timezone_success_old_script(self):
        # When timezone is present and run_command returns success
        self.module.params['timezone'] = "2025b"
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.timezone_mgmt.list_versions') as mocked_lv:
            mocked_lv.return_value = {
                "timezone_details": {
                    "available_versions": ["2025b", "2024a"],
                    "current_version": "2024a"
                }
            }
            # ensure script uses old prompts (is_new False)
            timezone_mgmt.is_new = False
            # simulate expect command running successfully
            self.module.run_command.return_value = (0, "Switched to 2025b", "")
            result = timezone_mgmt.update_timezone(self.module)
        self.assertTrue(result.get("changed"))
        self.assertEqual(result["msg"], "Successfully updated the timezone.")
        self.assertEqual(result["rc"], 0)

    def test_update_timezone_success_new_script(self):
        # similar to above but for new script flow
        self.module.params['timezone'] = "2025b"
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.timezone_mgmt.list_versions') as mocked_lv:
            mocked_lv.return_value = {
                "timezone_details": {
                    "available_versions": ["2025b", "2024a"],
                    "current_version": "2024a"
                }
            }
            timezone_mgmt.is_new = True
            self.module.run_command.return_value = (0, "Switched to 2025b (new)", "")
            result = timezone_mgmt.update_timezone(self.module)
        self.assertTrue(result.get("changed"))
        self.assertEqual(result["msg"], "Successfully updated the timezone.")

    def test_update_timezone_command_failure(self):
        # simulate the expect command failing (non-zero rc)
        self.module.params['timezone'] = "2025b"
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.timezone_mgmt.list_versions') as mocked_lv:
            mocked_lv.return_value = {
                "timezone_details": {
                    "available_versions": ["2025b"],
                    "current_version": "2024a"
                }
            }
            self.module.run_command.return_value = (3, "", "error occurred")
            result = timezone_mgmt.update_timezone(self.module)
        self.assertTrue(result.get("failed"))
        self.assertIn("Failed to update the timezone version.", result["msg"])
        self.assertEqual(result["rc"], 3)


class TestUpdateTimezoneOffline(unittest.TestCase):
    def setUp(self):
        global base_params
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        self.module.run_command.return_value = (0, "", "")

    def test_update_offline_success(self):
        # Provide db_location and successful run_command
        self.module.params['db_location'] = "/tmp/tzdb.tar"
        timezone_mgmt.is_new = True
        self.module.run_command.return_value = (0, "Updated successfully", "")
        result = timezone_mgmt.update_timezone_offline(self.module)
        self.assertTrue(result.get("changed"))
        self.assertIn("Successfully updated timezone using the provided DB location.", result["msg"])

    def test_update_offline_nothing_to_update(self):
        # stdout indicates already installed DB -> changed False
        self.module.params['db_location'] = "/tmp/tzdb.tar"
        timezone_mgmt.is_new = True
        self.module.run_command.return_value = (0, "The system is already installed with 2025b", "")
        result = timezone_mgmt.update_timezone_offline(self.module)
        self.assertFalse(result.get("changed"))
        self.assertIn("Nothing to update", result["msg"])

    def test_update_offline_command_failure(self):
        self.module.params['db_location'] = "/tmp/tzdb.tar"
        timezone_mgmt.is_new = True
        self.module.run_command.return_value = (2, "", "some stderr")
        result = timezone_mgmt.update_timezone_offline(self.module)
        self.assertTrue(result.get("failed"))
        self.assertIn("Failed to update the timezone version", result["msg"])
        self.assertEqual(result["rc"], 2)

    def test_update_offline_tool_busy_triggers_fail(self):
        self.module.params['db_location'] = "/tmp/tzdb.tar"
        timezone_mgmt.is_new = True
        # stdout contains busy message -> should call module.fail_json
        self.module.run_command.return_value = (0, "Another session of the tool is running", "")
        with self.assertRaises(AnsibleFailJson) as cm:
            timezone_mgmt.update_timezone_offline(self.module)
        result = cm.exception.args[0]
        self.assertIn("Another session of the tool is running", result["msg"])


class TestPrintUpdatedZones(unittest.TestCase):
    def setUp(self):
        global base_params
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json
        self.module.run_command.return_value = (0, "", "")

    def test_print_updated_zones_success(self):
        # Build stdout with "Updated Zones" block and a trailing Database Version line
        stdout = (
            "Some header\n"
            "## Updated Zones\n"
            "ZoneA\n"
            "ZoneB\n"
            "Database Version: 2025b\n"
            "Some footer\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        payload = timezone_mgmt.print_updated_zones(self.module)
        self.assertFalse(payload.get("changed"))
        tz_details = payload.get("timezone_details", {})
        self.assertIn("ZoneA", tz_details["updated_zones"])
        self.assertIn("ZoneB", tz_details["updated_zones"])
        self.assertEqual(payload["msg"], "Successfully retrieved the updated timezone.")

    def test_print_updated_zones_command_failure(self):
        self.module.run_command.return_value = (5, "", "err")
        payload = timezone_mgmt.print_updated_zones(self.module)
        self.assertTrue(payload.get("failed"))
        self.assertIn("Failed to retrieve updated zones", payload["msg"])

    def test_print_updated_zones_no_zones(self):
        # stdout doesn't contain updated zones section -> returned list empty
        stdout = "No updates\nDatabase Version: 2025b\n"
        self.module.run_command.return_value = (0, stdout, "")
        payload = timezone_mgmt.print_updated_zones(self.module)
        self.assertEqual(payload["timezone_details"]["updated_zones"], [])


if __name__ == '__main__':
    unittest.main()
