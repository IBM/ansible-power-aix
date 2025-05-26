# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
from unittest.mock import patch
import copy

from ansible_collections.ibm.power_aix.plugins.modules import nmon

from .common.utils import (
    AnsibleFailJson, fail_json, rootdir
)


class TestNMON(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        self.module.fail_json = fail_json
        params = dict()
        params["filename"] = "file_name"
        params["file_containing_disk_groups"] = "fcdg_file"
        params["disklist"] = ['hdisk1', 'hdisk2']
        params["save_to_dir"] = "some_dir"
        params["disks_per_line"] = 2
        params["timestamp_size"] = 10
        params["percentage_of_process_threshold"] = 5
        params["priority"] = 10
        params["runname"] = "hostname"
        params["interval_seconds"] = 2
        params["output_path"] = "/tmp/oppath"
        params["include_async"] = True
        params["number_of_snapshots"] = 5
        params["include_disk_service_time"] = True
        params["skip_disk_config"] = True
        params["skip_ess_config"] = True
        params["spreadsheet_output"] = True
        params["use_greenwhich_time"] = True
        params["report_thread_level_stats"] = True
        params["skip_JFS_section"] = True
        params["include_raw_kernal_section"] = True
        params["include_large_page_analysis"] = True
        params["include_mempages_section"] = True
        params["include_nfs_section"] = True
        params["include_nfsv4_section"] = True
        params["include_sea_vios_section"] = True
        params["include_paging_space_section"] = True
        params["include_wlm_section_with_subclasses"] = True
        params["include_top_processes"] = True
        params["include_top_processes_and_save_cli_agrs"] = True
        params["include_disk_vg_section"] = True
        params["include_wlm_section"] = True
        params["sensible_recording_for_one_day"] = True
        params["sensible_recording_for_one_hr"] = True
        params["scpu_details"] = 'on'
        params["pcpu_details"] = 'on'
        params["include_top_processes_with_commands"] = True
        params["sensible_recording_one_day_without_top"] = True
        params["include_fibre_channel_section"] = True
        params["restrict_commands_in_listing"] = ['db2', 'nmon', 'topas']
        self.module.params = params
        rc, stdout, stderr = 0, "sample stdout", "sample stderr"
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_success_run_nmon(self):
        # Success scenario
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            msg = nmon.run_nmon(self.module)
            # Adding all the flags in one go so that don't have to check for them individually
            testMsg = "Successfully ran the following command: /usr/bin/nmon"
            testMsg += " -f -F file_name -x -X -z -g fcdg_file -k hdisk1,hdisk2"
            testMsg += " -m some_dir -l 2 -w 10 -I 5 -Z 10 -r hostname -s 2 -o /tmp/oppath"
            testMsg += " -C db2:nmon:topas -A -c 5 -d -D -E -G -i -J -K -L -M -N -NN -O -P -S -t -T"
            testMsg += " -V -W -y SCPU=on -y PCPU=on -Y -^"

            self.assertEqual(msg, testMsg)


    def test_fail_run_nmon_without_required_flags(self):
        # Setting all the required attributes to None
        self.module.params["filename"] = None
        self.module.params["spreadsheet_output"] = None
        self.module.params["sensible_recording_for_one_day"] = None
        self.module.params["sensible_recording_for_one_hr"] = None
        self.module.params["sensible_recording_one_day_without_top"] = None

        with self.assertRaises(AnsibleFailJson) as result:
            nmon.run_nmon(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])

        # This string will be present in the result's msg
        pattern = r"Need to provide one of the following"
        self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_run_nmon_invalid_timestamp(self):
        # Providing an invalid value for timestamp size
        self.module.params['timestamp_size'] = 2
        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            with self.assertRaises(AnsibleFailJson) as result:
                nmon.run_nmon(self.module)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])

            # This string will be present in the result's msg
            pattern = r"Value of timestamp_size should be between 4-16"
            self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_run_nmon_invalid_dir(self):
        # Fail, as the provided directory is invalid
        self.module.params['save_to_dir'] = 'invalid'

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = False

            with self.assertRaises(AnsibleFailJson) as result:
                nmon.run_nmon(self.module)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])

            # This string will be present in the result's msg
            pattern = r"The provided directory does not exist"
            self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_run_nmon(self):
        # General failure of function
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")

        with patch("os.path.exists") as mock_exists:
            mock_exists.return_value = True

            with self.assertRaises(AnsibleFailJson) as result:
                nmon.run_nmon(self.module)
            result = result.exception.args[0]
            self.assertTrue(result['failed'])

            # This string will be present in the result's msg
            pattern = r"command failed"
            self.assertRegexpMatches(result['msg'], pattern)
