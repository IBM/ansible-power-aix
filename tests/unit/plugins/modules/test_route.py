# -*- coding: utf-8 -*-
# Copyright: (c) 2025- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import route

from .common.utils import AnsibleFailJson, fail_json


class TestRouteCommandFunctions(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson

        # Default parameters for route module
        params = dict()
        params["action"] = "add"  # Default action for tests
        params["destination"] = None
        params["gateway"] = None
        params["netmask"] = None
        params["prefixlen"] = None
        params["arguments"] = {}
        params["flush"] = False
        params["numeric"] = False
        params["ioctl_preference"] = False
        params["verbose"] = False
        params["flags"] = "host"  # Default flag for tests
        params["family"] = None

        self.module.params = params

        # Mock command return values
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_normalize_route_entry_valid_cidr(self):
        result = route.normalize_route_entry(self.module, "10.12/16")
        self.assertEqual(result, "10.12.0.0/16")

    def test_normalize_route_entry_invalid_cidr(self):
        with self.assertRaises(AnsibleFailJson) as result:
            route.normalize_route_entry(self.module, "10.12.300/16")
        self.assertIn("Failed to normalize route_entry", result.exception.args[0]['msg'])

    def test_normalize_route_entry_no_slash(self):
        result = route.normalize_route_entry(self.module, "10.12.15.1")
        self.assertEqual(result, "10.12.15.1")

    def test_parse_routing_table_single_entry(self):
        self.module.run_command.return_value = (0, "10.0.0.0/24 192.168.1.1", "")
        # Call the function to parse the routing table
        routing_table, gateways = route.parse_routing_table(self.module)
        self.assertEqual(str(routing_table[0]), "10.0.0.0/24")
        self.assertEqual(gateways[0], "192.168.1.1")  # Access the single gateway directly

    def test_parse_routing_table_success(self):
        self.module.run_command.return_value = (0, "10.0.0.0/24 192.168.1.1\n10.0.1.0/24 192.168.1.2", "")
        routing_table, gateways = route.parse_routing_table(self.module)
        self.assertEqual(len(routing_table), 2)
        self.assertEqual(gateways, ["192.168.1.1", "192.168.1.2"])

    def test_parse_routing_table_failure(self):
        self.module.run_command.return_value = (1, "", "Error fetching routing table")
        with self.assertRaises(AnsibleFailJson) as result:
            route.parse_routing_table(self.module)
        self.assertIn("Failed to fetch routing table", result.exception.args[0]['msg'])

    def test_check_destination_in_routing_table_found(self):
        self.module.params.update({
            "netmask": None,
            "prefixlen": 24,
            "flags": "net",
            "gateway": "192.168.1.1",
            "action": "add"
        })
        self.module.run_command.return_value = (0, "10.0.0.0/24 192.168.1.1", "")
        result = route.check_destination_in_routing_table(self.module, "10.0.0.0")
        self.assertTrue(result)

    def test_check_destination_in_routing_table_not_found(self):
        self.module.params.update({
            "netmask": None,
            "prefixlen": 24,
            "flags": "net",
            "gateway": "192.168.1.1",
            "action": "add"
        })
        self.module.run_command.return_value = (0, "10.0.1.0/24 192.168.1.2", "")
        result = route.check_destination_in_routing_table(self.module, "10.0.0.0")
        self.assertFalse(result)

    def test_calculate_network_address_with_netmask(self):
        result = route.calculate_network_address(self.module, "192.168.1.1", "255.255.255.0")
        self.assertEqual(result, "192.168.1.0")

    def test_calculate_network_address_with_prefix(self):
        result = route.calculate_network_address(self.module, "192.168.1.1", 24)
        self.assertEqual(result, "192.168.1.0")

    def test_build_route_command_flush(self):
        self.module.params = {
            "flush": True
        }
        cmd = route.build_route_command(self.module)
        self.assertEqual(cmd, "route -f")

    def test_build_route_command_with_destination(self):
        self.module.params = {
            "action": "add",
            "destination": "192.168.1.1",
            "prefixlen": None,
            "flags": "host",
            "flush": False,
            "numeric": False,
            "ioctl_preference": False,
            "verbose": False,
            "gateway": "192.168.1.254",
            "netmask": None,
            "arguments": None,
            "family": None
        }
        cmd = route.build_route_command(self.module)
        self.assertEqual(cmd, "route add -host 192.168.1.1 192.168.1.254")

    def test_build_route_command_with_net(self):
        self.module.params = {
            "action": "add",
            "destination": "192.168.1.4",
            "prefixlen": 24,
            "flags": "net",
            "flush": False,
            "numeric": False,
            "ioctl_preference": False,
            "verbose": False,
            "gateway": "192.168.1.1",
            "netmask": None,
            "arguments": None,
            "family": None
        }
        cmd = route.build_route_command(self.module)
        self.assertEqual(cmd, "route add -net 192.168.1.4 -prefixlen 24 192.168.1.1")

    def test_run_route_command_success(self):
        self.module.params = {
            "action": "add",
            "destination": "192.168.1.4",
            "prefixlen": 24,
            "flags": "net",
            "flush": False,
            "numeric": False,
            "ioctl_preference": False,
            "verbose": False,
            "gateway": "192.168.1.1",
            "netmask": None,
            "arguments": None,
            "family": None
        }
        self.module.run_command.return_value = (0, "Command executed successfully", "")
        rc, stdout, stderr, cmd = route.run_route_command(self.module)
        self.assertEqual(stdout, "Command executed successfully")

    def test_run_route_command_failure(self):
        self.module.params = {
            "action": "add",
            "destination": "192.168.1.4",
            "prefixlen": 24,
            "flags": "net",
            "flush": False,
            "numeric": False,
            "ioctl_preference": False,
            "verbose": False,
            "gateway": "192.168.1.1",
            "netmask": None,
            "arguments": None,
            "family": None
        }
        self.module.run_command.return_value = (1, "", "Error occurred")
        with self.assertRaises(AnsibleFailJson) as result:
            route.run_route_command(self.module)

        exception_result = result.exception.args[0]
        self.assertTrue(exception_result['failed'])


if __name__ == '__main__':
    unittest.main()
