# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import lparstat
from .common.utils import fail_json, AnsibleFailJson


class TestLparstatModule(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson

        self.params = {
            'config_info': False,
            'wpar_output': False,
            'service_info': False,
            'energy_tuning': False,
            'micro_partition': False,
            'utilization': False,
            'security_mode': False,
            'detailed_cpu_stats': False,
            'memory_stats': False,
            'io_memory_pools': False,
            'page_coalescing': False,
            'page_coalescing_wide': False,
            'reset_once': False,
            'reset_each_interval': False,
            'hypervisor_stat_short': False,
            'hypervisor_stat_long': False,
            'export_xml': False,
            'output_file': None,
            'spurr_based_metrics': False,
            'spurr_based_metrics_wide': False,
            'timestamp': False,
            'interval': None,
            'count': None,
            'recorded_output': "/tmp/lparstatdata/lparstat_output.txt",
            'concatenated_output': True,
        }
        self.module.params = self.params

    def test_config_info_conflict(self):
        self.module.params.update({'config_info': True, 'memory_stats': True})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("'-i' can only be used", str(err.exception))

    def test_page_coalescing_wide_without_page_coalescing(self):
        self.module.params.update({'memory_stats': True, 'page_coalescing_wide': True})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("The '-w' options can only be used with both '-m' and '-p'.", str(err.exception))

    def test_reset_once_without_io_memory(self):
        self.module.params.update({'memory_stats': True, 'reset_once': True})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("The '-r' and '-R' options can only be used with both '-m' and '-e'.", str(err.exception))

    def test_spurr_metrics_interval_without_count(self):
        self.module.params.update({'spurr_based_metrics': True, 'interval': 2})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("'count' is mandatory when you use the '-E ' flag with an 'interval'", str(err.exception))

    def test_security_mode_conflict(self):
        self.module.params.update({'security_mode': True, 'memory_stats': True})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("'-x' can only be used with", str(err.exception))

    def test_detailed_cpu_stats_requires_count(self):
        self.module.params.update({'detailed_cpu_stats': True, 'interval': 2})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("'count' is mandatory when you use the '-d' flag with an 'interval'", str(err.exception))

    def test_hypervisor_short_requires_count(self):
        self.module.params.update({'hypervisor_stat_short': True, 'interval': 2})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("'count' is mandatory when you use the '-h' flag with an 'interval'", str(err.exception))

    def test_hypervisor_long_requires_count(self):
        self.module.params.update({'hypervisor_stat_long': True, 'interval': 2})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("'count' is mandatory when you use the '-H' flag with an 'interval'", str(err.exception))

    def test_output_file_without_export_xml(self):
        self.module.params.update({'output_file': '/tmp/out.xml'})
        with self.assertRaises(AnsibleFailJson) as err:
            lparstat.validate_mutual_exclusiveness(self.module)
        self.assertIn("The 'output_file' option must be used with 'export_xml'", str(err.exception))

    def test_valid_basic_config_info(self):
        self.module.params.update({'config_info': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-i'])

    def test_valid_config_info_with_allies(self):
        self.module.params.update({'config_info': True, 'wpar_output': True, 'service_info': True, 'energy_tuning': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-i', '-W', '-s', '-P'])

    def test_valid_memory_stats_with_io_pools_and_reset(self):
        self.module.params.update({'memory_stats': True, 'io_memory_pools': True, 'reset_once': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-m', '-e', '-r'])

    def test_valid_memory_stats_with_page_coalescing_and_wide(self):
        self.module.params.update({'memory_stats': True, 'page_coalescing': True, 'page_coalescing_wide': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-m', '-p', '-w'])

    def test_valid_security_mode(self):
        self.module.params.update({'security_mode': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-x'])

    def test_valid_detailed_cpu_stats_with_interval_and_count(self):
        self.module.params.update({'detailed_cpu_stats': True, 'interval': 2, 'count': 3})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-d', '2', '3'])

    def test_valid_hypervisor_short(self):
        self.module.params.update({'hypervisor_stat_short': True, 'interval': 1, 'count': 1})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-h', '1', '1'])

    def test_valid_hypervisor_long(self):
        self.module.params.update({
            'hypervisor_stat_long': True, 
            'interval': 2, 
            'count': 2,
            'timestamp': True
        })
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-H', '-t', '2', '2'])

    def test_valid_export_xml_with_file(self):
        self.module.params.update({'export_xml': True, 'output_file': '/tmp/lpar.xml'})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-X', '-o', '/tmp/lpar.xml'])

    def test_valid_spurr_based_metrics(self):
        self.module.params.update({'spurr_based_metrics': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-E'])

    def test_valid_spurr_based_metrics_with_wide(self):
        self.module.params.update({
            'spurr_based_metrics': True, 
            'spurr_based_metrics_wide': True,
            'timestamp': True
        })
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-E', '-w', '-t'])

    def test_valid_timestamp_only(self):
        self.module.params.update({'timestamp': True})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-t'])

    def test_valid_interval_and_count(self):
        self.module.params.update({'interval': 5, 'count': 10})
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '5', '10'])

    def test_valid_combination_memory_with_timestamp(self):
        self.module.params.update({
            'memory_stats': True, 
            'io_memory_pools': True, 
            'reset_each_interval': True, 
            'timestamp': True
        })
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat', '-m', '-e', '-R', '-t'])

    def test_all_defaults(self):
        cmd = lparstat.build_lparstat_command(self.module)
        self.assertEqual(cmd, ['lparstat'])
