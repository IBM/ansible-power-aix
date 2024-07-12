# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest

from ansible_collections.ibm.power_aix.plugins.modules import emgr

from .common.utils import (
    emgr_output_path1, emgr_output_path2,
    emgr_output_path3, emgr_output_path4
)


class TestEmgrListOutput(unittest.TestCase):
    def setUp(self):
        # sample emgr output
        with open(emgr_output_path1, "r") as f:
            self.emgr_output1 = f.read().strip()
        with open(emgr_output_path2, "r") as f:
            self.emgr_output2 = f.read().strip()
        with open(emgr_output_path3, "r") as f:
            self.emgr_output3 = f.read().strip()
        with open(emgr_output_path4, "r") as f:
            self.emgr_output4 = f.read().strip()

    def test_success_emgr_list_output_with_ifix(self):
        ifix_details = emgr.parse_ifix_details(self.emgr_output1)
        self.assertEqual(ifix_details[2], {'ID': '3',
                                           'STATE': '*Q*',
                                           'LABEL': 'IJ09625s2a',
                                           'INSTALL TIME': '04/30/20 11:04:14',
                                           'UPDATED BY': '',
                                           'ABSTRACT': 'IJ09624 7.2.3.2'})

        ifix_details = emgr.parse_ifix_details(self.emgr_output2)
        self.assertEqual(ifix_details[1], {'ID': '2',
                                           'STATE': 'S',
                                           'LABEL': 'IJ50428s1a',
                                           'INSTALL TIME': '06/25/24 10:16:31',
                                           'UPDATED BY': '',
                                           'ABSTRACT': 'IJ50428 for AIX 7.3 TL2 SP1'})

        ifix_details = emgr.parse_ifix_details(self.emgr_output3)
        self.assertEqual(ifix_details[0], {'ID': '1',
                                           'STATE': 'S',
                                           'LABEL': 'IJ49570tu1',
                                           'INSTALL TIME': '06/28/24 00:58:15',
                                           'UPDATED BY': '',
                                           'ABSTRACT': 'Trusted update signatures for IJ49570'})

    def test_success_emgr_list_output_with_empty_details(self):
        ifix_details = emgr.parse_ifix_details(self.emgr_output4)
        self.assertEqual(ifix_details, [])
