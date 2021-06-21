# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import os


#########################################################################################
# Mock Exceptions
#########################################################################################
class AnsibleExitJson(Exception):
    """Exception class to be raised by module.exit_json and caught by the test case"""
    pass


class AnsibleFailJson(Exception):
    """Exception class to be raised by module.fail_json and caught by the test case"""
    pass


#########################################################################################
# Mocked methods for AnsibleModule
#########################################################################################
def exit_json(*args, **kwargs):
    """function to patch over exit_json; package return data into an exception"""
    if 'changed' not in kwargs:
        kwargs['changed'] = False
    raise AnsibleExitJson(kwargs)


def fail_json(*args, **kwargs):
    """function to patch over fail_json; package return data into an exception"""
    kwargs['failed'] = True
    raise AnsibleFailJson(kwargs)


#########################################################################################
# Common Variables
#########################################################################################
rootdir = "ansible_collections.ibm.power_aix.plugins.modules."
lsfs_output_path = os.path.dirname(os.path.abspath(__file__)) + "/sample_lsfs_output"
lslv_output_path1 = os.path.dirname(os.path.abspath(__file__)) + "/sample_lslv_output1"
lslv_output_path2 = os.path.dirname(os.path.abspath(__file__)) + "/sample_lslv_output2"
mock_ftp_report = os.path.dirname(os.path.abspath(__file__)) + "/mock_ftp_report"
mock_http_report = os.path.dirname(os.path.abspath(__file__)) + "/mock_http_report"
mock_https_report = os.path.dirname(os.path.abspath(__file__)) + "/mock_https_report"
