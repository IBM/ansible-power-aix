# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
from unittest.mock import patch
import copy

from ansible_collections.ibm.power_aix.plugins.modules import pagingspace

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
)

# Initial parameters
params = {
    "action": "list",
    "list_all": False,
    "include_summary": False,
    "ps_helper_name": None,
    "ps_name": None,
    "nfs_server_hostname": None,
    "nfs_server_pathname": None,
    "paging_space_configured_at_sub_restart": False,
    "checksum_size": None,
    "activate_immediately": False,
    "logical_partitions": None,
    "ps_type": "lv",
    "volume_group": None,
    "pv_name": None,
    "logical_partitions_add": None,
    "logical_partitions_substract": None,
    "use_ps_at_next_restart": False,
    "use_on_next_swapon": False,
    "activate_all_ps": False,
    "ps_list": None
}


class TestListpagingspace(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_list_success_include_summary(self):
        # List paging space information
        self.module.params['include_summary'] = True

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.parse_ps_details') as mocked_parse_ps_details:
            mocked_parse_ps_details.return_value = ''
            msg = pagingspace.list_paging_space(self.module)

        pattern = r'Successfully retrieved information about paging spaces'

        self.assertRegexpMatches(msg, pattern)

    def test_list_fail_no_ps_provided(self):
        # Fail when none are provided from these: list_all, include_summary, ps_type, ps_name
        self.module.params['list_all'] = False
        self.module.params['include_summary'] = False
        self.module.params['ps_type'] = False
        self.module.params['ps_name'] = False

        with self.assertRaises(AnsibleFailJson) as result:
            pagingspace.list_paging_space(self.module)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])

        pattern = r"You need to provide one of the following"
        self.assertRegexpMatches(result['msg'], pattern)


    def test_list_fail(self):
        # General failure of the command
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        self.module.params['include_summary'] = True

        with self.assertRaises(AnsibleFailJson) as result:
            pagingspace.list_paging_space(self.module)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])

        testMsg = "Could not get the required information, command: /usr/sbin/lsps -s"
        self.assertEqual(result['msg'], testMsg)


class TestCreatepagingspace(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_create_non_nfs_paging_space(self):
        # Create a non nfs paging space
        self.module.params['paging_space_configured_at_sub_restart'] = True
        self.module.params['activate_immediately'] = True
        self.module.params['checksum_size'] = 4
        self.module.params['logical_partitions'] = 4
        self.module.params['volume_group'] = "vg1"

        msg = pagingspace.create_paging_space(self.module)
        testMsg = 'Successfully created paging space, Command: /usr/sbin/mkps -a -n -t lv -c 4 -s 4 vg1'
        self.assertEqual(msg, testMsg)


    def test_create_nfs_paging_space(self):
        # Create a  nfs paging space
        self.module.params['paging_space_configured_at_sub_restart'] = True
        self.module.params['activate_immediately'] = True
        self.module.params['ps_type'] = 'nfs'
        self.module.params['nfs_server_hostname'] = "nfs_host"
        self.module.params['nfs_server_pathname'] = "/somepath"

        msg = pagingspace.create_paging_space(self.module)
        testMsg = 'Command /usr/sbin/mkps -a -n -t nfs nfs_host /somepath ran successfully!'
        self.assertEqual(msg, testMsg)


    def test_fail_no_lp_vg_provided(self):
        # For non-nfs paging spaces, you need to provide both logical partitions and volume group
        self.module.params['logical_partitions'] = None
        self.module.params['volume_group'] = None
        with self.assertRaises(AnsibleFailJson) as result:
            pagingspace.create_paging_space(self.module)
        result = result.exception.args[0]
        self.assertTrue(result['failed'])

        pattern = r"you need to specify both 'logical_partitions' and 'volume_group'"
        self.assertRegexpMatches(result['msg'], pattern)


    def test_no_change_already_exists(self):
        # The command will not run as the paging space already exists.
        self.module.params['ps_name'] = "testps"

        # Mock check_if_exist's return value to True
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = True
            msg = pagingspace.create_paging_space(self.module)

        pattern = r"The provided paging space already exists"
        self.assertRegexpMatches(msg, pattern)


    def test_fail_create_pagingspace(self):
        # General failure of function
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        self.module.params['logical_partitions'] = 4
        self.module.params['volume_group'] = "vg1"

        with self.assertRaises(AnsibleFailJson) as result:
            pagingspace.create_paging_space(self.module)
        result = result.exception.args[0]

        pattern = r"Couldn't create paging space"
        self.assertRegexpMatches(result['msg'], pattern)


class TestModifypagingspace(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_success_modify_paging_space(self):
        # General successful run of function
        self.module.params['logical_partitions_add'] = 4
        self.module.params['ps_helper_name'] = 'ps_helper_name'
        self.module.params['use_ps_at_next_restart'] = True
        self.module.params['logical_partitions_substract'] = 2
        self.module.params['use_on_next_swapon'] = True
        self.module.params['ps_name'] = 'testps'

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = True
            msg = pagingspace.modify_paging_space(self.module)

            testMsg = "Successfully modified the paging space, Command: "
            testMsg += "/usr/sbin/chps -t ps_helper_name -s 4 -d 2 -f -a y testps"

        self.assertEqual(msg, testMsg)


    def test_nochange_modify_same_checksum(self):
        # Do nothing as checksum size is same as what is set and no other attribute needs to be modified
        self.module.params['checksum_size'] = 4
        self.module.params['use_on_next_swapon'] = True
        self.module.params['ps_name'] = 'testps'
        self.module.params['use_ps_at_next_restart'] = None

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Checksum': "4"}}

            msg = pagingspace.modify_paging_space(self.module)

            testMsg = 'All the provided attributes are already set, no need to modify'
            self.assertEquals(msg, testMsg)


    def test_fail_modify_paging_space_no_ps(self):
        # Try to modify when the paging space does not exist
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = False
            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.modify_paging_space(self.module)

            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r'The provided paging space does not exit!'
            self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_modify_paging_space_no_next_swapon(self):
        # Try to modify when 'checksum_size' is provided but 'use_on_next_swapon' is not provided
        self.module.params['checksum_size'] = 5

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = True

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.modify_paging_space(self.module)

            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"you also need to set 'use_on_next_swapon' to true"
            self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_modify_pagingspace(self):
        # General failure of function
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        self.module.params['logical_partitions_add'] = 4
        self.module.params['ps_name'] = 'testps'

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = True
            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.modify_paging_space(self.module)

            result = result.exception.args[0]
            self.assertTrue(result['failed'])
            pattern = r"Failed to modify the paging space"
            self.assertRegexpMatches(result['msg'], pattern)


class TestRemovepagingspace(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_remove_paging_space(self):
        # Remove a paging space
        self.module.params['ps_name'] = 'testps'

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = True
            msg = pagingspace.remove_paging_space(self.module)

        testMsg = 'Successfully removed the paging space, Command: /usr/sbin/rmps testps'
        self.assertEqual(msg, testMsg)


    def test_remove_fail_nonexistent_ps(self):
        # The command will not run as the paging space does not exists.
        self.module.params['ps_name'] = "testps"

        # Mock check_if_exist's return value to True
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = False

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.remove_paging_space(self.module)

            result = result.exception.args[0]
            self.assertTrue(result['failed'])

            pattern = r"The paging space does not exist"
            self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_remove_pagingspace(self):
        # General failure of function
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        self.module.params['ps_name'] = "testps"
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = True

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.remove_paging_space(self.module)
            result = result.exception.args[0]

            pattern = r"Failed to remove the paging space"
            self.assertRegexpMatches(result['msg'], pattern)


class TestActivatepagingspace(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_success_activate_all_ps(self):
        # Successfully run the command for all ps
        self.module.params['activate_all_ps'] = True
        self.module.run_command.return_value = (0, '', '')
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Active': "no"}}
            msg = pagingspace.activate_paging_space(self.module)

        testMsg = "Successfully activated all the paging spaces. Command: /usr/sbin/swapon -a"

        self.assertEqual(testMsg, msg)

    def test_nochange_activate_ps_list(self):
        # Try to activate multiple paging spaces when all of them are already active
        self.module.params['ps_list'] = ['testps1', 'testps2']
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps1':{'Active': "yes"}, 'testps2':{'Active': "yes"}}
            msg = pagingspace.activate_paging_space(self.module)

        testMsg = "All the provided paging spaces are either already in active state or do not exist."

        self.assertEqual(msg, testMsg)

    def test_nochange_activate_all_ps(self):
        # Try to activate, when all the ps are already active
        self.module.params['activate_all_ps'] = True
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Active': "yes"}}
            msg = pagingspace.activate_paging_space(self.module)

        testMsg = "All the paging spaces are already in active state, no need to run the command."

        self.assertEqual(testMsg, msg)


    def test_fail_activate_all_no_ps(self):
        # Fail when no paging spaces are present but trying to activate all
        self.module.params['activate_all_ps'] = True
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = False

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.activate_paging_space(self.module)

        result = result.exception.args[0]
        self.assertTrue(result['failed'])

        pattern = r"No paging spaces are present"
        self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_no_ps_provided(self):
        # Fail when no ps is provided
        self.module.params['activate_all_ps'] = None
        self.module.params['ps_name'] = None
        self.module.params['ps_list'] = None

        with self.assertRaises(AnsibleFailJson) as result:
            pagingspace.activate_paging_space(self.module)
        result = result.exception.args[0]

        self.assertTrue(result['failed'])
        pattern = r"set either 'activate_all_ps' as true, or provide the paging space names"

        self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_activate_nonexistent_ps(self):
        # Fail when the provided paging space doesn't exist
        self.module.params['ps_name'] = 'testps'

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = False

            msg = pagingspace.activate_paging_space(self.module)

        pattern = r"The provided paging space does not exist."
        self.assertRegexpMatches(msg, pattern)


    def test_fail_activate(self):
        # General failure of function
        self.module.run_command.return_value = (1, "", "")
        self.module.params['ps_name'] = 'testps'

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Active': "no"}}
            msg = pagingspace.deactivate_paging_space(self.module)  

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.activate_paging_space(self.module)
            result = result.exception.args[0]

            self.assertTrue(result['failed'])
            pattern = r"Failed to activate paging space"
            self.assertRegexpMatches(result['msg'], pattern)


class TestDeactivatepagingspace(unittest.TestCase):
    def setUp(self):
        global params
        self.module = mock.Mock()
        self.module.params = params
        self.module.fail_json = fail_json
        (rc, stdout, stderr) = (0, "sample stdout", "sample stderr")
        self.module.run_command.return_value = (rc, stdout, stderr)


    def test_success_deactivate_ps(self):
        # Successfully run the command
        self.module.params['ps_name'] = 'testps'
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Active': "yes"}}
            msg = pagingspace.deactivate_paging_space(self.module)        

        testMsg = "Successfully deactivated the paging space: testps"
        testMsg += ", Command: /usr/sbin/swapoff testps"

        self.assertEqual(testMsg, msg)


    def test_success_deactivate_ps_list(self):
        # Successfully run the command with ps_list
        self.module.params['ps_list'] = ['testps1', 'testps2']
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps1':{'Active': "yes"}, 'testps2':{'Active': "yes"}}
            msg = pagingspace.deactivate_paging_space(self.module)        

        testMsg = "Successfully deactivated the paging space: ['testps1', 'testps2']"
        testMsg += ", Command: /usr/sbin/swapoff testps1 testps2"

        self.assertEqual(testMsg, msg)


    def test_nochange_deactivate_ps(self):
        # Try to deactivate the paging space which is already in deactivated state
        self.module.params['ps_name'] = 'testps'
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Active': "no"}}
            msg = pagingspace.deactivate_paging_space(self.module)        

        testMsg = "No need to deactivate, already deactivated."

        self.assertEqual(testMsg, msg)


    def test_nochange_deactivate_ps_list(self):
        # Try to deactivate the ps from ps_list when they are already deactivated
        self.module.params['ps_list'] = ['testps1', 'testps2']
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps1':{'Active': "no"}, 'testps2':{'Active': "no"}}
            msg = pagingspace.deactivate_paging_space(self.module)        

        pattern = r"No need to deactivate as the provided paging space"

        self.assertRegexpMatches(msg, pattern)


    def test_fail_deactivate_no_ps(self):
        # Try to deactivate a paging space without providing ps_name and ps_list
        self.module.params['ps_name'] = None
        self.module.params['ps_list'] = None

        with self.assertRaises(AnsibleFailJson) as result:
            pagingspace.deactivate_paging_space(self.module)
        result = result.exception.args[0]

        self.assertTrue(result['failed'])
        pattern = r"need to provide the paging spaces to be deactivated."
        self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_deactivate_nonexistent_ps(self):
        # Try to delete a paging space that doesn't exist
        self.module.params['ps_name'] = 'testps'
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = False

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.deactivate_paging_space(self.module)
            result = result.exception.args[0]

            self.assertTrue(result['failed'])
            pattern = r"The provided paging space does not exist."

            self.assertRegexpMatches(result['msg'], pattern)


    def test_fail_deactivate(self):
        # General failure of function
        self.module.run_command.return_value = (1, "sample stdout", "sample stderr")
        self.module.params['ps_name'] = 'testps'

        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.pagingspace.check_if_exists') as mocked_check_if_exists:
            mocked_check_if_exists.return_value = {'testps':{'Active': "yes"}}

            with self.assertRaises(AnsibleFailJson) as result:
                pagingspace.deactivate_paging_space(self.module)
            result = result.exception.args[0]

            self.assertTrue(result['failed'])
            pattern = r"Failed to deactivate paging spaces"
            self.assertRegexpMatches(result['msg'], pattern)
