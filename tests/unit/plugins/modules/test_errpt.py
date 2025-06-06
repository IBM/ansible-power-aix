
# -*- coding: utf-8 -*-
# Copyright: (c) 2025 - IBM, Inc
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import errpt
from .common.utils import fail_json, AnsibleFailJson

class TestErrptModule(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson

        # Set all params to None or default initially
        self.params = {
            'detailed': False,
            'short_detail': False,
            'error_class': None,
            'consolidate_duplicates': False,
            'end_date': None,
            'ascii_format': False,
            'input_log': None,
            'diag_log': None,
            'include_errids': None,
            'exclude_errids': None,
            'include_labels': None,
            'exclude_labels': None,
            'sequence_number': None,
            'machine': None,
            'node': None,
            'resource_names': None,
            'start_date': None,
            'error_types': None,
            'recorded_output': None,
            'concatenated_output': True
        }
        self.module.params = self.params

    def test_all_defaults(self):
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt'])

    def test_short_detail_and_errid(self):
        self.module.params.update({
            'short_detail': True,
            'include_errids': '192AC072'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-A', '-j', '192AC072'])

    def test_mutual_exclusive_errid_failure(self):
        self.module.params['exclude_errids'] = 'ABCD1234'
        self.module.params['include_errids'] = 'ABCD1234'
        with self.assertRaises(AnsibleFailJson) as err:
            errpt.build_errpt_command(self.module)
        self.assertIn('-j option cannot be used with  -k', str(err.exception))

    def test_mutual_exclusive_labels_failure(self):
        self.module.params['exclude_labels'] = 'BOOT_ERR'
        self.module.params['include_labels'] = 'BOOT_ERR'
        with self.assertRaises(AnsibleFailJson) as err:
            errpt.build_errpt_command(self.module)
        self.assertIn('-J option cannot be used with  -K', str(err.exception))

    def test_mutual_exclusive_detailed_and_short_detail_failure(self):
        self.module.params['detailed'] = True
        self.module.params['short_detail'] = True
        with self.assertRaises(AnsibleFailJson) as err:
            errpt.build_errpt_command(self.module)
        self.assertIn('The -A option cannot be used with -a', str(err.exception))

    def test_ascii_format_only(self):
        self.module.params.update({
            'ascii_format': True
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-g'])

    def test_detailed_flag_only(self):
        self.module.params.update({
            'detailed': True
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-a'])

    def test_consolidate_duplicates_only(self):
        self.module.params.update({
            'consolidate_duplicates': True
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-D'])

    def test_with_time_filters(self):
        self.module.params.update({
            'start_date': '0512000025',
            'end_date': '0522150525'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-e', '0522150525', '-s', '0512000025'])

    def test_with_resource_names(self):
        self.module.params.update({
            'resource_names': 'SYSPROC'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-N', 'SYSPROC'])

    def test_with_node_and_machine(self):
        self.module.params.update({
            'node': 'node1',
            'machine': 'machine1'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-m', 'machine1', '-n', 'node1'])

    def test_with_sequence_number(self):
        self.module.params.update({
            'sequence_number': '100'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-l', '100'])

    def test_with_error_class_and_type(self):
        self.module.params.update({
            'error_class': 'H,S',
            'error_types': 'PERM'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-d', 'H,S', '-T', 'PERM'])

    def test_with_input_and_diag_log(self):
        self.module.params.update({
            'input_log': '/var/log/input',
            'diag_log': '/var/log/diag'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-i', '/var/log/input', '-I', '/var/log/diag'])

    def test_include_labels_only(self):
        self.module.params.update({
            'include_labels': 'BOOT_LABEL'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-J', 'BOOT_LABEL'])

    def test_exclude_labels_only(self):
        self.module.params.update({
            'exclude_labels': 'BOOT_LABEL'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-K', 'BOOT_LABEL'])

    def test_exclude_errids_only(self):
        self.module.params.update({
            'exclude_errids': '192AC072'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-k', '192AC072'])

    def test_consolidate_duplicates_and_ascii_conflict(self):
        self.module.params.update({
            'consolidate_duplicates': True,
            'ascii_format': True
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-g'])

    def test_combined_multiple_flags_with_short_detail(self):
        self.module.params.update({
            'short_detail': True,
            'consolidate_duplicates': True,
            'include_errids': '192AC072',
            'sequence_number': '120',
            'resource_names': 'SYSPROC'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-D', '-A', '-j', '192AC072', '-l', '120', '-N', 'SYSPROC'])

    def test_combined_multiple_flags_with_detail(self):
        self.module.params.update({
            'detailed': True,
            'consolidate_duplicates': True,
            'exclude_errids': '192AC072',
            'exclude_labels': '1BOOT_LABEL',
            'resource_names': 'SYSPROC'
        })
        cmd = errpt.build_errpt_command(self.module)
        self.assertEqual(cmd, ['errpt', '-D', '-a', '-k', '192AC072', '-K', '1BOOT_LABEL', '-N', 'SYSPROC'])

if __name__ == '__main__':
    unittest.main()
