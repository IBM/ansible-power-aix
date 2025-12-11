# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import iostat
from .common.utils import fail_json, AnsibleFailJson


class TestIostatModule(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson

        self.params = {
            'adapter_report': False,
            'block_io': False,
            'no_tty_cpu': False,
            'extended_drive': False,
            'fs_utilization': False,
            'fs_only': False,
            'long_list': False,
            'path_utilization': False,
            'reset_ext_stats': False,
            'system_throughput': False,
            'no_disk': False,
            'show_timestamp': False,
            'nonzero_stats': False,
            'reset_io': False,
            'xml_output': False,
            'scale_power': None,
            'options_override': None,
            'filesystems': None,
            'wpar_stats': None,
            'xml_output_path': None,
            'drives': None,
            'recorded_output': "/tmp/iostatdata/iostat_output.txt",
            'concatenated_output': True,
            'interval': None,
            'count': None
        }
        self.module.params = self.params

    def test_xml_output_conflict(self):
        self.module.params.update({'xml_output': True, 'adapter_report': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("No other option except -o can be combined with -X option", str(err.exception))

    def test_block_io_missing_interval(self):
        self.module.params['block_io'] = True
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("interval is missing with -b option.", str(err.exception))

    def test_block_io_mutual_exclusion(self):
        self.module.params.update({'block_io': True, 'adapter_report': True, 'interval': 1})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-b is mutually exclusive with all flags except -T, -D, -O, -V , -z.", str(err.exception))

    def test_adapter_report_conflict_fs_utilization(self):
        self.module.params.update({'adapter_report': True, 'fs_utilization': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-a is mutually exclusive with:  -f, -F, -@, -X, -b", str(err.exception))

    def test_no_tty_cpu_conflict_fs_only(self):
        self.module.params.update({'no_tty_cpu': True, 'fs_only': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-d is mutually exclusive with: -F, -X, -S,", str(err.exception))

    def test_no_tty_cpu_and_no_disk_invalid(self):
        self.module.params.update({'no_tty_cpu': True, 'no_disk': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-d and -t cannot be used together unless -a or -s is specified", str(err.exception))

    def test_extended_drive_conflict_fs_utilization(self):
        self.module.params.update({'extended_drive': True, 'fs_utilization': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-D is mutually exclusive with: -f, -F, -P, -q, -Q, -S,", str(err.exception))

    def test_extended_drive_and_no_disk_invalid(self):
        self.module.params.update({'extended_drive': True, 'no_disk': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-D and -t together only allowed with -a or -s.", str(err.exception))

    def test_reset_ext_stats_requires_extended_drive(self):
        self.module.params['reset_ext_stats'] = True
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("The -R option can only be used together with -D.", str(err.exception))

    def test_fs_utilization_conflict_adapter_report(self):
        self.module.params.update({'fs_utilization': True, 'adapter_report': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-a is mutually exclusive with:  -f, -F, -@, -X, -b", str(err.exception))

    def test_path_utilization_conflict_fs_only(self):
        self.module.params.update({'path_utilization': True, 'fs_only': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-m is mutually exclusive with  -F,  -t, -@", str(err.exception))

    def test_system_throughput_conflict_wpar(self):
        self.module.params.update({'system_throughput': True, 'wpar_stats': 'ALL'})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-s is mutually exclusive with  -@", str(err.exception))

    def test_no_disk_reset_io_conflict(self):
        self.module.params.update({'no_disk': True, 'reset_io': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-t is mutually exclusive with -z, -@", str(err.exception))

    def test_wpar_stats_with_adapter_report(self):
        self.module.params.update({'wpar_stats': 'ALL', 'adapter_report': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-a is mutually exclusive with:  -f, -F, -@, -X, -b", str(err.exception))

    def test_drives_and_fs_only_conflict(self):
        self.module.params.update({'fs_only': True, 'drives': ['hdisk0']})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn(" 'drives' cannot be used with -F  Option.", str(err.exception))

    def test_fs_only_mutuals(self):
        self.module.params.update({'fs_only': True, 'adapter_report': True})
        with self.assertRaises(AnsibleFailJson) as err:
            iostat.build_iostat_command(self.module)
        self.assertIn("-a is mutually exclusive with:  -f, -F, -@, -X, -b", str(err.exception))

    def test_valid_basic_xml(self):
        self.module.params.update({'xml_output': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-X'])

    def test_valid_extended_drive_and_reset_ext_stats(self):
        self.module.params.update({'extended_drive': True, 'reset_ext_stats': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-D', '-R'])

    def test_valid_block_io(self):
        self.module.params.update({'block_io': True, 'interval': 2})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-b', '2', '5'])

    def test_valid_adapter_report(self):
        self.module.params.update({'adapter_report': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-a'])

    def test_valid_path_utilization(self):
        self.module.params.update({'path_utilization': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-m'])

    def test_valid_filesystems_fs_utilization(self):
        self.module.params.update({'fs_utilization': True, 'filesystems': '/'})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-f', '/'])

    def test_valid_drives(self):
        self.module.params.update({'drives': ['hdisk0']})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', 'hdisk0'])

    def test_valid_scale_power(self):
        self.module.params.update({'scale_power': 2})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-S', '2'])

    def test_valid_options_override(self):
        self.module.params.update({'options_override': 'ellipsis=on'})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-O', 'ellipsis=on'])

    def test_valid_wpar_stats(self):
        self.module.params.update({'wpar_stats': 'ALL'})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-@', 'ALL'])

    def test_valid_show_timestamp(self):
        self.module.params.update({'show_timestamp': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-T'])

    def test_valid_nonzero_stats(self):
        self.module.params.update({'nonzero_stats': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-V'])

    def test_valid_reset_io(self):
        self.module.params.update({'reset_io': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-z'])

    def test_valid_interval_count(self):
        self.module.params.update({'interval': 2, 'count': 5})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '2', '5'])

    def test_all_defaults(self):
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat'])

    # The extra 15 realistic valid combos:
    def test_adapter_report_with_timestamp(self):
        self.module.params.update({'adapter_report': True, 'show_timestamp': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-a', '-T'])

    def test_adapter_report_with_drives_and_interval(self):
        self.module.params.update({
            'adapter_report': True,
            'drives': ['hdisk0'],
            'interval': 5
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-a', 'hdisk0', '5', '5'])

    def test_extended_drive_with_scale_and_override(self):
        self.module.params.update({
            'extended_drive': True,
            'reset_ext_stats': True,
            'options_override': 'detail=on'
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-D', '-R', '-O', 'detail=on'])

    def test_block_io_with_reset_io_and_override(self):
        self.module.params.update({
            'block_io': True,
            'interval': 2,
            'reset_io': True,
            'options_override': 'ell=on'
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-b', '-z', '-O', 'ell=on', '2', '5'])

    def test_block_io_with_nonzero_stats(self):
        self.module.params.update({
            'block_io': True,
            'interval': 1,
            'nonzero_stats': True
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-b', '-V', '1', '5'])

    def test_reset_io_and_nonzero_stats(self):
        self.module.params.update({'reset_io': True, 'nonzero_stats': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-V', '-z'])

    def test_system_throughput_and_show_timestamp(self):
        self.module.params.update({'system_throughput': True, 'show_timestamp': True})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-s', '-T'])

    def test_long_list_with_drives(self):
        self.module.params.update({'long_list': True, 'drives': ['hdisk0']})
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-l', 'hdisk0'])

    def test_fs_utilization_with_override_and_scale(self):
        self.module.params.update({
            'fs_utilization': True,
            'filesystems': '/',
            'options_override': 'detail=on',
            'scale_power': 1
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-f', '/', '-S', '1', '-O', 'detail=on'])

    def test_valid_wpar_stats_with_drives(self):
        self.module.params.update({
            'wpar_stats': 'ALL',
            'drives': ['hdisk0']
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-@', 'ALL', 'hdisk0'])

    def test_valid_reset_io_with_drives_and_interval(self):
        self.module.params.update({
            'reset_io': True,
            'drives': ['hdisk0'],
            'interval': 2
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-z', 'hdisk0', '2', '5'])

    def test_valid_show_timestamp_with_drives_and_count(self):
        self.module.params.update({
            'show_timestamp': True,
            'drives': ['hdisk0'],
            'interval': 2,
            'count': 2
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-T', 'hdisk0', '2', '2'])

    def test_valid_nonzero_stats_with_drives(self):
        self.module.params.update({
            'nonzero_stats': True,
            'drives': ['hdisk0']
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-V', 'hdisk0'])

    def test_valid_scale_power_with_drives_and_override(self):
        self.module.params.update({
            'scale_power': 2,
            'options_override': 'perf=on',
            'drives': ['hdisk0']
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-S', '2', '-O', 'perf=on', 'hdisk0'])

    def test_valid_interval_count_drives_show_timestamp(self):
        self.module.params.update({
            'interval': 2,
            'count': 2,
            'drives': ['hdisk0'],
            'show_timestamp': True
        })
        cmd = iostat.build_iostat_command(self.module)
        self.assertEqual(cmd, ['iostat', '-T', 'hdisk0', '2', '2'])
