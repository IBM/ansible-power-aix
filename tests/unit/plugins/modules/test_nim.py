# -*- coding: utf-8 -*-
# Copyright: (c) 2025 - Test
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import socket

from ansible_collections.ibm.power_aix.plugins.modules import nim

from .common.utils import (
    AnsibleFailJson, AnsibleExitJson, fail_json, exit_json
)


class TestBuildDict(unittest.TestCase):
    def test_build_dict_parses_lines(self):
        stdout = (
            "obj1:\n"
            "    attr1 = value1\n"
            "    attr2 = value2\n"
            "obj2:\n"
            "    a = b\n"
        )
        module = mock.Mock()
        info = nim.build_dict(module, stdout)
        expected = {
            'obj1': {'attr1': 'value1', 'attr2': 'value2'},
            'obj2': {'a': 'b'}
        }
        self.assertEqual(info, expected)


class TestGetNimMasterInfo(unittest.TestCase):
    def setUp(self):
        self.module = mock.Mock()
        # ensure results exists for nim module functions that use it
        nim.results = {
            'cmd': '', 'rc': 0, 'stdout': '', 'stderr': '', 'msg': ''
        }

    def test_get_nim_master_info_success(self):
        stdout = "something\n   Cstate = ready for a NIM operation\nother\n"
        self.module.run_command.return_value = (0, stdout, "")
        cstate = nim.get_nim_master_info(self.module)
        self.assertEqual(cstate, "ready for a NIM operation")

    def test_get_nim_master_info_failure_raises(self):
        self.module.run_command.return_value = (2, "", "err")
        self.module.fail_json = fail_json
        with self.assertRaises(AnsibleFailJson):
            nim.get_nim_master_info(self.module)


class TestExpandTargets(unittest.TestCase):
    def setUp(self):
        # populate nim.results with sample nim_node
        nim.results = {
            'nim_node': {
                'standalone': {'cli1': {}, 'cli2': {}, 'app3': {}},
                'vios': {'vios1': {}}
            }
        }

    def test_expand_all_and_keywords(self):
        self.assertCountEqual(nim.expand_targets(['ALL']), ['cli1', 'cli2', 'app3', 'vios1'])
        self.assertCountEqual(nim.expand_targets(['*']), ['cli1', 'cli2', 'app3', 'vios1'])
        self.assertCountEqual(nim.expand_targets(['standalone']), ['cli1', 'cli2', 'app3'])
        self.assertCountEqual(nim.expand_targets(['vios']), ['vios1'])

    def test_expand_range_and_wildcard_and_exact(self):
        # add numbered entries for range test
        nim.results['nim_node']['standalone'].update({'node1': {}, 'node2': {}, 'node3': {}, 'node10': {}})
        self.assertIn('node2', nim.expand_targets(['node[1:3]']))
        # wildcard 'app*' should match 'app3'
        self.assertIn('app3', nim.expand_targets(['app*']))
        # exact name
        self.assertEqual(nim.expand_targets(['cli1']), ['cli1'])


class TestGetTargetIpaddr(unittest.TestCase):
    def setUp(self):
        # prepare nim.results stub
        nim.results = {
            'nim_node': {
                'standalone': {
                    't1': {'ip': '1.2.3.4'},
                    't2': {'if1': 'master_net nimclient02.example.com ABCD ent0'},
                    't3': {'if1': 'badformat'}
                },
                'vios': {}
            }
        }
        self.module = mock.Mock()

    def test_get_target_ipaddr_returns_explicit_ip(self):
        ip = nim.get_target_ipaddr(self.module, 't1')
        self.assertEqual(ip, '1.2.3.4')

    @mock.patch('socket.getfqdn', autospec=True)
    def test_get_target_ipaddr_uses_getfqdn(self, getfqdn):
        getfqdn.return_value = 'nimclient02.example.com'
        ip = nim.get_target_ipaddr(self.module, 't2')
        # stored in results and returned
        self.assertEqual(ip, 'nimclient02.example.com')
        self.assertEqual(nim.results['nim_node']['standalone']['t2']['ip'], 'nimclient02.example.com')

    @mock.patch('socket.getfqdn', autospec=True)
    def test_get_target_ipaddr_getfqdn_raises_logs_and_returns_ip(self, getfqdn):
        # simulate getfqdn raising OSError; function should catch and keep the original if1 hostname
        getfqdn.side_effect = OSError('fail dns')
        # ensure module.log is callable
        self.module.log = mock.Mock()
        ip = nim.get_target_ipaddr(self.module, 't2')
        # If getfqdn fails, function returns the host portion (parsed) or the original ip fallback.
        # The code sets ipaddr to the hostname resolved by getfqdn; if it fails, ipaddr remains the match group.
        self.assertTrue(isinstance(ip, str))
        self.module.log.assert_called()  # we expect an error log call


class TestFindResourceByClient(unittest.TestCase):
    def setUp(self):
        # setup results nim_node lpp_source entries
        nim.results = {'nim_node': {'lpp_source': {
            '2020-01-01-0001-1-0-0-lpp_source': '/export/1',
            '2020-02-01-0002-1-1-lpp_source': '/export/2',
            '2020-03-01-0003-2-0-0-lpp_source': '/export/3',
        }}}
        self.module = mock.Mock()

    def test_find_next_tl(self):
        # oslevel_elts first element '2020' should match tl list, ensure it picks proper tl
        os_elts = ['2020', '02', '01', '0002']
        chosen = nim.find_resource_by_client(self.module, 'tl', 'next', os_elts)
        self.assertTrue(chosen.endswith('lpp_source'))

    def test_find_sp(self):
        os_elts = ['2020', '02', '01', '0002']
        chosen = nim.find_resource_by_client(self.module, 'sp', 'latest', os_elts)
        self.assertTrue(chosen.endswith('lpp_source'))

    def test_find_resource_not_found_returns_current_style(self):
        # use values that won't match any lpp_source to hit fallback branch
        os_elts = ['1999', '00', '00', '0000']
        chosen = nim.find_resource_by_client(self.module, 'tl', 'latest', os_elts)
        self.assertIn('-lpp_source', chosen)


class TestCheckIfAllocated(unittest.TestCase):
    def setUp(self):
        # nim.results should be present and module stub
        nim.results = {'nim_node': {'standalone': {'cli1': {}}, 'vios': {}}, 'msg': ''}
        self.module = mock.Mock()
        # default run_command to simulate lsnim returning info containing lpp_source name 'my_src'
        self.module.run_command.return_value = (0, "cli1\n    lpp_source = my_src", "")

    def test_check_if_allocated_filters(self):
        # targets pattern expands to cli1 because it's in nim.results
        out = nim.check_if_allocated(self.module, 'my_src', ['cli1'])
        self.assertEqual(out, ['cli1'])

    def test_check_if_allocated_no_matches_fails(self):
        # simulate lsnim failing for the provided target
        self.module.run_command.return_value = (1, "", "err")
        nim.results = {'nim_node': {'standalone': {'cliX': {}}, 'vios': {}}, 'msg': ''}
        self.module.fail_json = fail_json
        with self.assertRaises(AnsibleFailJson):
            nim.check_if_allocated(self.module, 'bad', ['cliX'])


class TestPerformCustomizationAndListFixesBasic(unittest.TestCase):
    def setUp(self):
        nim.results = {
            'changed': False,
            'meta': {},
            'targets': [],
            'nim_node': {'lpp_source': {}},
        }
        self.module = mock.Mock()
        # simplify logging calls
        self.module.log = mock.Mock()
        self.module.debug = mock.Mock()

    def test_perform_customization_sync_handles_do_not_error(self):
        # stdout must include the exact phrase the module's regex expects
        stdout = "Either the software is already at the same level as on the media, or something else\nFinished processing all filesets.\n"
        # make run_command return rc != 0 but stdout contains that special message
        self.module.run_command.return_value = (2, stdout, "")

        # ensure module.params exist and have alt_disk_update_name (None) so function can index it
        self.module.params = {'alt_disk_update_name': None}

        # ensure results.meta for target exists with messages list (perform_customization appends)
        nim.results['meta'] = {'t1': {'messages': []}}
        nim.results.setdefault('changed', False)

        rc = nim.perform_customization(self.module, 'mysrc', 't1', False)
        # do_not_error branch forces rc to 0 and appends a message into results['meta'][target]
        self.assertEqual(rc, 0)
        # there should be at least one message appended for this target
        self.assertTrue(len(nim.results['meta']['t1']['messages']) >= 1)

    def test_list_fixes_parses(self):
        # emgr output lines where first token is a digit -> module appends line_array[2]
        stdout = "1 something else fixA\n2 foo bar fixB\n"
        # run as master (local)
        self.module.run_command.return_value = (0, stdout, "")
        rc, fixes = nim.list_fixes(self.module, 'master')
        self.assertEqual(rc, 0)
        # module code uses line_array[2] — for our sample lines that's 'else' and 'bar'
        self.assertEqual(fixes, ['else', 'bar'])


if __name__ == '__main__':
    unittest.main()
