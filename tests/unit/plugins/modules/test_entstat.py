# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import entstat
from .common.utils import fail_json, AnsibleFailJson


class TestEntstatModule(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson

        self.params = {
            'device_name': 'ent0',
            'device_statistics': False,
            'reset_stats': False,
            'debug_trace': False,
            'recorded_output': "/tmp/entstatdata/entstat_output.txt",
            'concatenated_output': True,
        }
        self.module.params = self.params

    def test_default_command(self):
        cmd = entstat.build_entstat_command(self.module)
        self.assertEqual(cmd, ['entstat', 'ent0'])

    def test_device_statistics(self):
        self.module.params.update({'device_statistics': True})
        cmd = entstat.build_entstat_command(self.module)
        self.assertEqual(cmd, ['entstat', '-d', 'ent0'])

    def test_reset_stats(self):
        self.module.params.update({'reset_stats': True})
        cmd = entstat.build_entstat_command(self.module)
        self.assertEqual(cmd, ['entstat', '-r', 'ent0'])

    def test_debug_trace(self):
        self.module.params.update({'debug_trace': True})
        cmd = entstat.build_entstat_command(self.module)
        self.assertEqual(cmd, ['entstat', '-t', 'ent0'])

    def test_all_flags_enabled(self):
        self.module.params.update({
            'device_statistics': True,
            'reset_stats': True,
            'debug_trace': True
        })
        cmd = entstat.build_entstat_command(self.module)
        # Order matters, same as implementation
        self.assertEqual(cmd, ['entstat', '-d', '-r', '-t', 'ent0'])

    def test_output_file_handling(self):
        # Just simulate with params; full IO tested in integration
        self.module.params.update({'recorded_output': '/tmp/entstatdata/test_out.txt'})
        self.module.params.update({'device_name': 'ent2'})
        cmd = entstat.build_entstat_command(self.module)
        self.assertIn('ent2', cmd)


if __name__ == '__main__':
    unittest.main()
