# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock

from ansible_collections.ibm.power_aix.plugins.modules import bootlist

from .common.utils import (
    AnsibleExitJson, exit_json, fail_json, rootdir
)

BOOTLIST_PATH = "/usr/bin/bootlist"

NORMAL_OUT = "hdisk0 blv=hd5 pathid=0\nhdisk1 blv=hd5 pathid=1\n"
SERVICE_OUT = "cd0\n"


class TestBootlistHelpers(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()

    def test_get_bootlist_parses_attributes(self):
        self.module.run_command.return_value = (0, NORMAL_OUT, "")
        result = bootlist.get_bootlist(self.module, BOOTLIST_PATH, "normal")
        self.assertEqual(result, [
            dict(device="hdisk0", blv="hd5", pathid="0"),
            dict(device="hdisk1", blv="hd5", pathid="1"),
        ])
        self.module.run_command.assert_called_once_with([BOOTLIST_PATH, "-m", "normal", "-o"])

    def test_get_bootlist_failure_returns_none(self):
        self.module.run_command.return_value = (1, "", "error")
        self.assertIsNone(bootlist.get_bootlist(self.module, BOOTLIST_PATH, "service"))

    def test_matches_ignores_unspecified_attributes(self):
        current = [dict(device="hdisk0", blv="hd5", pathid="0")]
        requested = [dict(device="hdisk0", blv=None, pathid=None, vlan_tag=None)]
        self.assertTrue(bootlist.bootlist_matches(current, requested))

    def test_matches_compares_specified_attributes_as_strings(self):
        current = [dict(device="ent0", vlan_tag="5")]
        self.assertTrue(bootlist.bootlist_matches(current, [dict(device="ent0", vlan_tag=5)]))
        self.assertFalse(bootlist.bootlist_matches(current, [dict(device="ent0", vlan_tag=6)]))

    def test_matches_respects_order(self):
        current = [dict(device="hdisk0"), dict(device="hdisk1")]
        requested = [dict(device="hdisk1"), dict(device="hdisk0")]
        self.assertFalse(bootlist.bootlist_matches(current, requested))

    def test_matches_different_length(self):
        current = [dict(device="hdisk0"), dict(device="hdisk1")]
        self.assertFalse(bootlist.bootlist_matches(current, [dict(device="hdisk0")]))
        self.assertFalse(bootlist.bootlist_matches([dict(device="hdisk0")], current))

    def test_matches_unreadable_current_list(self):
        self.assertFalse(bootlist.bootlist_matches(None, [dict(device="hdisk0")]))


class TestBootlistMain(unittest.TestCase):
    """Run main() with a mocked AnsibleModule and a fake 'bootlist' command."""

    def run_main(self, params, current):
        """Run main(); 'current' maps mode -> stdout of 'bootlist -m <mode> -o'.

        Returns (result dict, list of 'set' commands that were executed).
        """
        set_cmds = []

        def run_command(cmd, check_rc=False):
            if "-o" in cmd:
                mode = cmd[cmd.index("-m") + 1]
                if mode in current:
                    return 0, current[mode], ""
                return 1, "", "not set"
            set_cmds.append(cmd)
            return 0, "verbose output", ""

        module = mock.Mock()
        module.params = dict(normal=None, service=None, both=None, force=False)
        module.params.update(params)
        module.get_bin_path.return_value = BOOTLIST_PATH
        module.run_command.side_effect = run_command
        module.exit_json.side_effect = exit_json
        module.fail_json.side_effect = fail_json

        with mock.patch.object(bootlist, "AnsibleModule", return_value=module):
            with self.assertRaises(AnsibleExitJson) as result:
                bootlist.main()
        return result.exception.args[0], set_cmds

    def test_normal_already_set_is_not_changed(self):
        res, set_cmds = self.run_main(
            dict(normal=[dict(device="hdisk0"), dict(device="hdisk1")]),
            dict(normal=NORMAL_OUT, service=SERVICE_OUT))
        self.assertFalse(res["changed"])
        self.assertEqual(set_cmds, [])
        self.assertEqual(len(res["ansible_facts"]["bootlist"]["normal"]), 2)

    def test_normal_with_matching_attributes_is_not_changed(self):
        res, set_cmds = self.run_main(
            dict(normal=[dict(device="hdisk0", blv="hd5", pathid="0")]),
            dict(normal="hdisk0 blv=hd5 pathid=0\n"))
        self.assertFalse(res["changed"])
        self.assertEqual(set_cmds, [])

    def test_normal_different_order_is_changed(self):
        res, set_cmds = self.run_main(
            dict(normal=[dict(device="hdisk1"), dict(device="hdisk0")]),
            dict(normal=NORMAL_OUT))
        self.assertTrue(res["changed"])
        self.assertEqual(set_cmds, [[BOOTLIST_PATH, "-v", "-m", "normal", "hdisk1", "hdisk0"]])

    def test_normal_different_device_is_changed(self):
        res, set_cmds = self.run_main(
            dict(normal=[dict(device="hdisk2")]),
            dict(normal=NORMAL_OUT))
        self.assertTrue(res["changed"])
        self.assertEqual(len(set_cmds), 1)

    def test_normal_different_attribute_is_changed(self):
        res, set_cmds = self.run_main(
            dict(normal=[dict(device="hdisk0", pathid="1")]),
            dict(normal="hdisk0 blv=hd5 pathid=0\n"))
        self.assertTrue(res["changed"])
        self.assertEqual(len(set_cmds), 1)

    def test_current_list_not_readable_is_changed(self):
        res, set_cmds = self.run_main(
            dict(service=[dict(device="cd0")]),
            dict())
        self.assertTrue(res["changed"])
        self.assertEqual(len(set_cmds), 1)

    def test_service_already_set_is_not_changed(self):
        res, set_cmds = self.run_main(
            dict(service=[dict(device="cd0")]),
            dict(normal=NORMAL_OUT, service=SERVICE_OUT))
        self.assertFalse(res["changed"])
        self.assertEqual(set_cmds, [])

    def test_both_already_set_is_not_changed(self):
        res, set_cmds = self.run_main(
            dict(both=[dict(device="hdisk0")]),
            dict(normal="hdisk0\n", service="hdisk0\n"))
        self.assertFalse(res["changed"])
        self.assertEqual(set_cmds, [])

    def test_both_only_one_list_matches_is_changed(self):
        res, set_cmds = self.run_main(
            dict(both=[dict(device="hdisk0")]),
            dict(normal="hdisk0\n", service="cd0\n"))
        self.assertTrue(res["changed"])
        self.assertEqual(set_cmds, [[BOOTLIST_PATH, "-v", "-m", "both", "hdisk0"]])

    def test_force_option_is_passed(self):
        res, set_cmds = self.run_main(
            dict(normal=[dict(device="hdisk2")], force=True),
            dict(normal=NORMAL_OUT))
        self.assertTrue(res["changed"])
        self.assertIn("-F", set_cmds[0])

    def test_no_options_only_returns_facts(self):
        res, set_cmds = self.run_main(dict(), dict(normal=NORMAL_OUT, service=SERVICE_OUT))
        self.assertFalse(res["changed"])
        self.assertEqual(set_cmds, [])
        self.assertEqual(res["ansible_facts"]["bootlist"]["service"], [dict(device="cd0")])


if __name__ == "__main__":
    unittest.main()
