# -*- coding: utf-8 -*-
# Copyright: (c) 2025- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import snap
from .common.utils import (
    AnsibleFailJson, fail_json
)


class TestSnapCommand(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson

        # Parameters for snap module
        params = dict()
        params["all_info"] = False
        params["compress"] = False
        params["general_info"] = False
        params["live_kernel"] = False
        params["hacmp"] = False
        params["reset"] = False
        params["file_system_info"] = False
        params["collects_dump"] = False
        params["installation_info"] = False
        params["kernel_info"] = False
        params["security_info"] = False
        params["workload_manager_info"] = False
        params["hardware_info"] = False
        params["ss_filename"] = None
        params["ss_size"] = None
        params["ss_rejoining"] = False
        params["ss_machinename"] = None

        params["sc_output_dir"] = None
        params["sc_remove_core"] = False
        params["sc_core_file"] = None
        params["sc_program_name"] = None
        self.module.params = params

        # Mock command return values
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

    def test_snap_general_option_all_info(self):
        self.module.params["all_info"] = True
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-a'])

    def test_snap_general_option_hacmp(self):
        self.module.params["all_info"] = False
        self.module.params["hacmp"] = True
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-e'])

    def test_snap_general_option_file_system_info(self):
        self.module.params["file_system_info"] = True
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-f'])

    def test_snap_general_option_live_kernel(self):
        self.module.params["live_kernel"] = True
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-U'])

    def test_snap_general_option_multiple_params(self):
        self.module.params.update({
            "file_system_info": True,
            "installation_info": True,
            "kernel_info": True,
            "workload_manager_info": True,
            "general_info": True,
            "security_info": True,
            "compress": True,
        })
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-f', '-i', '-k', '-w', '-S', '-g', '-c'])

    def test_snap_general_option_hardware_info(self):
        self.module.params["hardware_info"] = True
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-H'])

    def test_snap_general_option_collects_dump(self):
        self.module.params["collects_dump"] = True
        cmd = snap.snap_general_option(self.module)
        self.assertEqual(cmd, ['snap', '-D'])

    # build_snap_command function calling
    def test_build_snap_command_hacmp(self):
        self.module.params["all_info"] = False
        self.module.params["hacmp"] = True
        cmd = snap.build_snap_command(self.module)
        self.assertEqual(cmd, ['snap', '-e'])

    def test_run_snap_command_with_expect_failed(self):
        rc, stdout, stderr = 1, "Cleanup completed. Command execution failed", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)
        with self.assertRaises(AnsibleFailJson) as result:
            snap.run_snap_command_with_expect(self.module)
        testResult = result.exception.args[0]
        self.assertTrue(testResult['failed'])

    def test_run_snap_command_with_expect_command_failed(self):
        rc, stdout, stderr = 1, "Error occurred during cleanup", "Detailed error message"
        self.module.run_command.return_value = (rc, stdout, stderr)
        # `module.fail_json` raises the expected exception
        with self.assertRaises(AnsibleFailJson) as result:
            snap.run_snap_command_with_expect(self.module)
        exception_result = result.exception.args[0]
        self.assertTrue(exception_result['failed'])

    def test_run_snap_command_with_expect_nothing_to_clean(self):
        rc, stdout, stderr = 0, "Cleanup completed. Nothing to clean up", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        result = snap.run_snap_command_with_expect(self.module)
        self.assertEqual(result['msg'], "No cleanup was required.")

    def test_run_snap_command_with_expect_successfull(self):
        rc, stdout, stderr = 0, "Cleanup completed. Command executed successfully", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)

        result = snap.run_snap_command_with_expect(self.module)
        self.assertEqual(result['msg'], "Command executed successfully.")

    def test_build_snapsplit_with_filename_only(self):
        self.module.params['ss_filename'] = 'core.snap'
        cmd = snap.build_snapsplit_command(self.module)
        self.assertEqual(cmd, ['snapsplit', ' -f core.snap'])

    def test_build_snapsplit_with_all_options(self):
        self.module.params.update({
            'ss_filename': 'core.snap',
            'ss_size': '1',
            'ss_machinename': 'host123'
        })
        cmd = snap.build_snapsplit_command(self.module)
        self.assertEqual(cmd, ['snapsplit', ' -s 1', ' -H host123', ' -f core.snap'])

    def test_build_snapsplit_rejoining_with_timestamp_and_host(self):
        self.module.params.update({
            'ss_rejoining': True,
            'ss_timestamp': '20240502',
            'ss_machinename': 'host123'
        })
        cmd = snap.build_snapsplit_command(self.module)
        self.assertEqual(cmd, ['snapsplit', '-u', ' -T 20240502', ' -H host123'])

    def test_build_snapsplit_invalid_minimal(self):
        # No valid params
        cmd = snap.build_snapsplit_command(self.module)
        self.assertEqual(cmd, ['snapsplit'])
    
    def test_snapcore_with_only_core_file(self):
        self.module.params['sc_core_file'] = 'core.123'
        cmd = snap.build_snapcore_command(self.module)
        self.assertEqual(cmd, ['snapcore', 'core.123'])

    def test_snapcore_with_all_options(self):
        self.module.params.update({
            'sc_output_dir': '/tmp/snapcore_out',
            'sc_remove_core': True,
            'sc_core_file': 'core.123',
            'sc_program_name': 'myprog'
        })
        cmd = snap.build_snapcore_command(self.module)
        self.assertEqual(cmd, ['snapcore', '-d /tmp/snapcore_out', '-r', 'core.123', 'myprog'])

    def test_snapcore_with_output_dir_only(self):
        self.module.params['sc_output_dir'] = '/output/dir'
        cmd = snap.build_snapcore_command(self.module)
        self.assertEqual(cmd, ['snapcore', '-d /output/dir'])

    def test_snapcore_with_remove_flag_only(self):
        self.module.params['sc_remove_core'] = True
        cmd = snap.build_snapcore_command(self.module)
        self.assertEqual(cmd, ['snapcore', '-r'])

    def test_snapcore_with_program_name_only(self):
        self.module.params['sc_program_name'] = 'myapp'
        cmd = snap.build_snapcore_command(self.module)
        self.assertEqual(cmd, ['snapcore', 'myapp'])

    def test_snapcore_with_no_params(self):
        cmd = snap.build_snapcore_command(self.module)
        self.assertEqual(cmd, ['snapcore'])


if __name__ == '__main__':
    unittest.main()
