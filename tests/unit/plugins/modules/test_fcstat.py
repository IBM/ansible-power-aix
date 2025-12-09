# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import fcstat
from .common.utils import fail_json, AnsibleFailJson


class TestFcstatModule(unittest.TestCase):

    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson
        self.module.run_command = mock.Mock(return_value=(0, "ok", ""))

        self.params = {
            'device_name': 'fcs0',
            'remove_delay': False,
            'all_statistics': False,
            'reset_stats': False,
            'interval': None,
            'count': None,
            'protocol': None,
            'recorded_output': None,
            'concatenated_output': True
        }
        self.module.params = self.params

    # 1. Default command
    def test_default_command(self):
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertEqual(cmd, ['fcstat', 'fcs0'])

    # 2. With -z reset_stats
    def test_reset_stats_command(self):
        self.module.params.update({'reset_stats': True})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertEqual(cmd, ['fcstat', '-z', 'fcs0'])

    # 3. With -e all_statistics
    def test_all_statistics_command(self):
        self.module.params.update({'all_statistics': True})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertEqual(cmd, ['fcstat', '-e', 'fcs0'])

    # 4. With -c remove_delay
    def test_remove_delay_command(self):
        self.module.params.update({'remove_delay': True})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertEqual(cmd, ['fcstat', '-c', 'fcs0'])

    # 5. With reset_stats and remove_delay (-z -c)
    def test_reset_with_remove_delay(self):
        self.module.params.update({'reset_stats': True, 'remove_delay': True})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertEqual(cmd, ['fcstat', '-z', '-c', 'fcs0'])

    # 6. With all_statistics and remove_delay (-e -c)
    def test_all_statistics_with_remove_delay(self):
        self.module.params.update({'all_statistics': True, 'remove_delay': True})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertEqual(cmd, ['fcstat', '-e', '-c', 'fcs0'])

    # 7. With interval and protocol (-t -p)
    def test_interval_and_protocol_command(self):
        self.module.params.update({'interval': 5, 'count': 2, 'protocol': 'scsi'})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertIn('-t 5', cmd)
        self.assertIn('-p scsi', cmd)

    # 8. interval without count (should fail)
    def test_interval_without_count_fails(self):
        self.module.params.update({'interval': 5})
        with self.assertRaises(AnsibleFailJson):
            fcstat.validate_mutual_exclusiveness(self.module)

    # 9. count without interval (should fail)
    def test_count_without_interval_fails(self):
        self.module.params.update({'count': 3})
        with self.assertRaises(AnsibleFailJson):
            fcstat.validate_mutual_exclusiveness(self.module)

    # 10. protocol without interval (should fail)
    def test_protocol_without_interval_fails(self):
        self.module.params.update({'protocol': 'scsi'})
        with self.assertRaises(AnsibleFailJson):
            fcstat.validate_mutual_exclusiveness(self.module)

    # 11. reset_stats and all_statistics together (should fail)
    def test_reset_and_all_statistics_mutual_exclusive(self):
        self.module.params.update({'reset_stats': True, 'all_statistics': True})
        with self.assertRaises(AnsibleFailJson):
            fcstat.validate_mutual_exclusiveness(self.module)

    # 12. interval + reset_stats conflict (should fail)
    def test_interval_and_reset_stats_conflict(self):
        self.module.params.update({'interval': 5, 'count': 3, 'reset_stats': True})
        with self.assertRaises(AnsibleFailJson):
            fcstat.validate_mutual_exclusiveness(self.module)

    # 13. interval + remove_delay conflict (should fail)
    def test_interval_and_remove_delay_conflict(self):
        self.module.params.update({'interval': 5, 'count': 2, 'remove_delay': True})
        with self.assertRaises(AnsibleFailJson):
            fcstat.validate_mutual_exclusiveness(self.module)
    # 14. Validate valid device check
    def test_is_valid_device_success(self):
        self.module.run_command.return_value = (0, "fcs0", "")
        valid = fcstat.is_valid_device(self.module, "fcs0")
        self.assertTrue(valid)

    # 15. Invalid device should raise fail_json
    def test_is_valid_device_fail(self):
        self.module.run_command.return_value = (1, "", "error")
        with self.assertRaises(AnsibleFailJson):
            fcstat.is_valid_device(self.module, "invalid_fcs")

    # 16. interval + count => awk generation check
    def test_command_with_interval_count_generates_awk(self):
        self.module.params.update({'interval': 5, 'count': 2})
        cmd = fcstat.build_fcstat_command(self.module)
        self.assertIn("awk", cmd)
        self.assertIn("unbuffer", cmd)


if __name__ == '__main__':
    unittest.main()
