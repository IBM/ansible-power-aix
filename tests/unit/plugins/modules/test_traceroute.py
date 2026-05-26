# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import traceroute
from .common.utils import fail_json, AnsibleFailJson


class TestTracerouteModule(unittest.TestCase):

    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson
        self.params = {
            'host': 'google.com',
            'max_ttl': None,
            'numeric': False,
            'port': None,
            'queries': None,
            'bypass_routing': False,
            'debug': False,
            'source_address': None,
            'tos': None,
            'verbose': False,
            'wait_time': None,
            'packet_size': None,
            'recorded_output': None,
            'concatenated_output': False,
        }
        self.module.params = self.params.copy()

    def test_default_command(self):
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', 'google.com'])

    def test_debug_flag(self):
        self.module.params.update({'debug': True})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-d', 'google.com'])

    def test_numeric_flag(self):
        self.module.params.update({'numeric': True})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-n', 'google.com'])

    def test_bypass_routing_flag(self):
        self.module.params.update({'bypass_routing': True})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-r', 'google.com'])

    def test_verbose_flag(self):
        self.module.params.update({'verbose': True})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-v', 'google.com'])

    def test_max_ttl(self):
        self.module.params.update({'max_ttl': 20})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-m', '20', 'google.com'])

    def test_port(self):
        self.module.params.update({'port': 33434})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-p', '33434', 'google.com'])

    def test_queries(self):
        self.module.params.update({'queries': 5})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-q', '5', 'google.com'])

    def test_source_address(self):
        self.module.params.update({'source_address': '192.168.1.100'})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-s', '192.168.1.100', 'google.com'])

    def test_tos(self):
        self.module.params.update({'tos': 16})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-t', '16', 'google.com'])

    def test_wait_time(self):
        self.module.params.update({'wait_time': 5})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-w', '5', 'google.com'])

    def test_packet_size(self):
        self.module.params.update({'packet_size': 512})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', 'google.com', '512'])

    def test_host_ip_address(self):
        self.module.params.update({'host': '8.8.8.8'})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '8.8.8.8'])

    def test_numeric_and_max_ttl_combo(self):
        self.module.params.update({'numeric': True, 'max_ttl': 20})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-n', '-m', '20', 'google.com'])

    def test_debug_and_verbose_combo(self):
        self.module.params.update({'debug': True, 'verbose': True})
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-d', '-v', 'google.com'])

    def test_all_boolean_flags_combo(self):
        self.module.params.update({
            'debug': True,
            'numeric': True,
            'bypass_routing': True,
            'verbose': True
        })
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-d', '-n', '-r', '-v', 'google.com'])

    def test_max_ttl_port_queries_combo(self):
        self.module.params.update({
            'max_ttl': 15,
            'port': 33435,
            'queries': 3
        })
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-m', '15', '-p', '33435', '-q', '3', 'google.com'])

    def test_source_tos_wait_combo(self):
        self.module.params.update({
            'source_address': '10.0.0.1',
            'tos': 8,
            'wait_time': 10
        })
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-s', '10.0.0.1', '-t', '8', '-w', '10', 'google.com'])

    def test_numeric_max_ttl_packet_size_combo(self):
        self.module.params.update({
            'numeric': True,
            'max_ttl': 25,
            'packet_size': 1024
        })
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, ['traceroute', '-n', '-m', '25', 'google.com', '1024'])

    def test_all_flags_combo(self):
        self.module.params.update({
            'debug': True,
            'numeric': True,
            'bypass_routing': True,
            'verbose': True,
            'max_ttl': 30,
            'port': 33440,
            'queries': 4,
            'source_address': '172.16.0.1',
            'tos': 4,
            'wait_time': 7,
            'packet_size': 256
        })
        cmd = traceroute.build_traceroute_command(self.module)
        self.assertEqual(cmd, [
            'traceroute', '-d', '-n', '-r', '-v',
            '-m', '30', '-p', '33440', '-q', '4',
            '-s', '172.16.0.1', '-t', '4', '-w', '7',
            'google.com', '256'
        ])

    def test_tos_negative_invalid(self):
        self.module.params.update({'tos': -1})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_tos_too_large_invalid(self):
        self.module.params.update({'tos': 256})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_max_ttl_zero_invalid(self):
        self.module.params.update({'max_ttl': 0})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_max_ttl_negative_invalid(self):
        self.module.params.update({'max_ttl': -5})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_port_zero_invalid(self):
        self.module.params.update({'port': 0})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_port_negative_invalid(self):
        self.module.params.update({'port': -100})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_queries_zero_invalid(self):
        self.module.params.update({'queries': 0})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_queries_negative_invalid(self):
        self.module.params.update({'queries': -3})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_wait_time_zero_invalid(self):
        self.module.params.update({'wait_time': 0})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_wait_time_negative_invalid(self):
        self.module.params.update({'wait_time': -2})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_packet_size_zero_invalid(self):
        self.module.params.update({'packet_size': 0})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_packet_size_negative_invalid(self):
        self.module.params.update({'packet_size': -512})
        with self.assertRaises(AnsibleFailJson):
            traceroute.validate_parameters(self.module)

    def test_tos_boundary_zero_valid(self):
        self.module.params.update({'tos': 0})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for tos=0")

    def test_tos_boundary_255_valid(self):
        self.module.params.update({'tos': 255})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for tos=255")

    def test_max_ttl_positive_valid(self):
        self.module.params.update({'max_ttl': 1})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for max_ttl=1")

    def test_port_positive_valid(self):
        self.module.params.update({'port': 1})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for port=1")

    def test_queries_positive_valid(self):
        self.module.params.update({'queries': 1})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for queries=1")

    def test_wait_time_positive_valid(self):
        self.module.params.update({'wait_time': 1})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for wait_time=1")

    def test_packet_size_positive_valid(self):
        self.module.params.update({'packet_size': 1})
        try:
            traceroute.validate_parameters(self.module)
        except AnsibleFailJson:
            self.fail("validate_parameters raised AnsibleFailJson unexpectedly for packet_size=1")


if __name__ == '__main__':
    unittest.main()

