# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import netstat
from .common.utils import fail_json, AnsibleFailJson


class TestNetstatModule(unittest.TestCase):

    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson
        self.params = {
            'numeric_network_address': False,
            'pcb_address': False,
            'all_sockets_state': False,
            'socket_options': False,
            'routing_table': False,
            'show_route_details': False,
            'packet_counts': False,
            'display_configured_interfaces': False,
            'interface_name': None,
            'protocol': None,
            'wpar': None,
            'memory_stats': False,
            'mbuf_pool_stats': False,
            'protocol_stats': False,
            'concise_protocol_stats': False,
            'domain_sockets': False,
            'display_adapter_statistics': False,
            'virtual_interface_and_multicast': False,
            'ras_artifacts': None,
            'ras_file': None,
            'ras_suppress_nonzero': False,
            'interactive_mode': False,
            'clear_stats': None,
            'address_family': None,
            'interval': None,
            'count': None,
            'recorded_output': None,
            'concatenated_output': True,
            'cache_stats': False,
        }
        self.module.params = self.params.copy()

    def test_default_command(self):
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat'])

    def test_numeric_flag(self):
        self.module.params.update({'numeric_network_address': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-n'])

    def test_pcb_flag(self):
        self.module.params.update({'pcb_address': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-A'])

    def test_all_sockets(self):
        self.module.params.update({'all_sockets_state': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-a'])

    def test_socket_options_with_all_sockets(self):
        self.module.params.update({'all_sockets_state': True, 'socket_options': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-a', '-o'])

    def test_routing_table(self):
        self.module.params.update({'routing_table': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-r'])

    def test_show_route_details(self):
        self.module.params.update({'show_route_details': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-C'])

    def test_packet_counts(self):
        self.module.params.update({'packet_counts': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-D'])

    def test_display_interfaces(self):
        self.module.params.update({'display_configured_interfaces': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-i'])

    def test_interface_name(self):
        self.module.params.update({'display_configured_interfaces': True, 'interface_name': 'ent0'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-i', '-I', 'ent0'])

    def test_protocol(self):
        self.module.params.update({'protocol': 'tcp'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-p', 'tcp'])

    def test_memory_stats(self):
        self.module.params.update({'memory_stats': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-m'])

    def test_mbuf_pool_stats(self):
        self.module.params.update({'mbuf_pool_stats': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-M'])

    def test_protocol_stats(self):
        self.module.params.update({'protocol_stats': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-s'])

    def test_concise_protocol_stats(self):
        self.module.params.update({'concise_protocol_stats': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-ss'])

    def test_domain_sockets(self):
        self.module.params.update({'domain_sockets': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-u'])

    def test_display_adapter_statistics(self):
        self.module.params.update({'display_adapter_statistics': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-v'])

    def test_virtual_interface_and_multicast(self):
        self.module.params.update({'virtual_interface_and_multicast': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-g'])

    def test_cache_stats(self):
        self.module.params.update({'cache_stats': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-c'])

    def test_ras_artifacts(self):
        self.module.params.update({'ras_artifacts': 'tcp'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-K', 'tcp'])

    def test_ras_artifacts_with_file(self):
        self.module.params.update({'ras_artifacts': 'tcp', 'ras_file': '/tmp/tcp_ras.log'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-K', 'tcp', '-F', '/tmp/tcp_ras.log'])

    def test_ras_artifacts_with_nonzero_and_interactive(self):
        self.module.params.update({'ras_artifacts': 'udp', 'ras_suppress_nonzero': True, 'interactive_mode': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-K', 'udp', '-b', '-w'])

    def test_clear_stats_s(self):
        self.module.params.update({'clear_stats': 's'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-Zs'])

    def test_clear_stats_c(self):
        self.module.params.update({'clear_stats': 'c'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-Zc'])

    def test_address_family_inet6(self):
        self.module.params.update({'address_family': 'inet6'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-f', 'inet6'])

    def test_interval_and_count(self):
        self.module.params.update({'interval': 2, 'count': 3})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '2', '| head -n ', '5'])

    def test_numeric_pcb_protocol_combo(self):
        self.module.params.update({'numeric_network_address': True, 'pcb_address': True, 'protocol': 'udp'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-n', '-A', '-p', 'udp'])

    def test_interface_and_family_combo(self):
        self.module.params.update({'display_configured_interfaces': True, 'interface_name': 'en1', 'address_family': 'inet'})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-i', '-I', 'en1', '-f', 'inet'])

    def test_multicast_and_packet_counts_combo(self):
        self.module.params.update({'virtual_interface_and_multicast': True, 'packet_counts': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-g', '-D'])

    def test_all_sockets_and_memory_combo(self):
        self.module.params.update({'all_sockets_state': True, 'memory_stats': True})
        cmd = netstat.build_netstat_command(self.module)
        self.assertEqual(cmd, ['/bin/netstat', '-a', '-m'])

    def test_protocol_stats_and_concise_protocol_stats_invalid(self):
        self.module.params.update({'protocol_stats': True, 'concise_protocol_stats': True})
        with self.assertRaises(AnsibleFailJson):
            netstat.validate_mutual_exclusiveness(self.module)

    def test_clear_stats_with_routing_table_invalid(self):
        self.module.params.update({'clear_stats': 'c', 'routing_table': True})
        with self.assertRaises(AnsibleFailJson):
            netstat.validate_mutual_exclusiveness(self.module)

    def test_interval_without_count_invalid(self):
        self.module.params.update({'interval': 2})
        with self.assertRaises(AnsibleFailJson):
            netstat.validate_mutual_exclusiveness(self.module)

    def test_count_without_interval_invalid(self):
        self.module.params.update({'count': 2})
        with self.assertRaises(AnsibleFailJson):
            netstat.validate_mutual_exclusiveness(self.module)


if __name__ == '__main__':
    unittest.main()
