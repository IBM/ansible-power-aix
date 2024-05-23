# -*- coding: utf-8 -*-
# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import re

from ansible_collections.ibm.power_aix.plugins.modules import flrtvc

from .common.utils import (
    mock_ftp_report, mock_http_report, mock_https_report
)

params = {
    'apar': None,
    'filesets': None,
    'csv': None,
    'path': '/var/adm/ansible',
    'save_report': False,
    'verbose': False,
    'force': False,
    'clean': False,
    'check_only': False,
    'download_only': False,
    'extend_fs': True,
    'protocol': None,
}

init_results = {
    'changed': False,
    'msg': '',
    'meta': {'messages': []}
    # meta structure will be updated as follow:
    # meta={'messages': [],     detail execution messages
    #       '0.report': [],     run_flrtvc reports the vulnerabilities
    #       '1.parse': [],      run_parser builds the list of URLs
    #       '2.discover': [],   run_downloader builds the list of epkgs found in URLs
    #       '3.download': [],   run_downloader builds the list of downloaded epkgs
    #       '4.1.reject': [],   check_epkgs builds the list of rejected epkgs
    #       '4.2.check': [],    check_epkgs builds the list of epkgs checking prerequisites
    #       '5.install': []}    run_installer builds the list of installed epkgs
}

module = None
results = None
mock_https = []
mock_http = []
mock_ftp = []


# this function will check that each entry in the list of urls has the correct protocol
# it is used to check the "1.parse" part of "meta" in the report for a protocol.
# this will determine whether the changes to the code worked as intended.
def _check_protocol(subs, s_lst):
    for url in s_lst:
        # the colon is important as to not match http in https
        pattern = r"^%s:" % subs
        found = re.search(pattern, url)
        if not found:
            # return false if even one of the urls does not have the correct protocol
            return False
        # return true if all urls in the list use the specified protocol
        return True


class TestRunParser(unittest.TestCase):
    def setUp(self):
        global params, init_results, mock_https, mock_http, mock_ftp
        self.module = mock.Mock()
        self.module.params = params
        self.localpatchserver = ""
        self.localpatchpath = ""
        self.module.debug.return_value = None
        self.results = init_results

        # mocks of what the flrtvc script returns
        with open(mock_https_report, "r") as mock_file:
            mock_https = mock_file.read()
            mock_https = mock_https.split(",")

        with open(mock_http_report, "r") as mock_file:
            mock_http = mock_file.read()
            mock_http = mock_http.split(",")

        with open(mock_ftp_report, "r") as mock_file:
            mock_ftp = mock_file.read()
            mock_ftp = mock_ftp.split(",")

    def test_http_to_ftp(self):
        self.module.params['protocol'] = "ftp"
        flrtvc.module = self.module
        flrtvc.results = self.results
        flrtvc.results['meta'].update({'0.report': mock_http})
        flrtvc.run_parser(flrtvc.results['meta']['0.report'], self.localpatchserver, self.localpatchpath)
        self.assertTrue(_check_protocol('ftp', flrtvc.results['meta']['1.parse']))

    def test_http_to_https(self):
        self.module.params['protocol'] = "https"
        flrtvc.module = self.module
        flrtvc.results = self.results
        flrtvc.results['meta'].update({'0.report': mock_http})
        flrtvc.run_parser(flrtvc.results['meta']['0.report'], self.localpatchserver, self.localpatchpath)
        self.assertTrue(_check_protocol('https', flrtvc.results['meta']['1.parse']))

    def test_ftp_to_http(self):
        self.module.params['protocol'] = "http"
        flrtvc.module = self.module
        flrtvc.results = self.results
        flrtvc.results['meta'].update({'0.report': mock_ftp})
        flrtvc.run_parser(flrtvc.results['meta']['0.report'], self.localpatchserver, self.localpatchpath)
        self.assertTrue(_check_protocol('http', flrtvc.results['meta']['1.parse']))

    def test_ftp_to_https(self):
        self.module.params['protocol'] = "https"
        flrtvc.module = self.module
        flrtvc.results = self.results
        flrtvc.results['meta'].update({'0.report': mock_ftp})
        flrtvc.run_parser(flrtvc.results['meta']['0.report'], self.localpatchserver, self.localpatchpath)
        self.assertTrue(_check_protocol('https', flrtvc.results['meta']['1.parse']))

    def test_https_to_ftp(self):
        self.module.params['protocol'] = "ftp"
        flrtvc.module = self.module
        flrtvc.results = self.results
        flrtvc.results['meta'].update({'0.report': mock_https})
        flrtvc.run_parser(flrtvc.results['meta']['0.report'], self.localpatchserver, self.localpatchpath)
        self.assertTrue(_check_protocol('ftp', flrtvc.results['meta']['1.parse']))

    def test_https_to_http(self):
        self.module.params['protocol'] = "http"
        flrtvc.module = self.module
        flrtvc.results = self.results
        flrtvc.results['meta'].update({'0.report': mock_https})
        flrtvc.run_parser(flrtvc.results['meta']['0.report'], self.localpatchserver, self.localpatchpath)
        self.assertTrue(_check_protocol('http', flrtvc.results['meta']['1.parse']))
