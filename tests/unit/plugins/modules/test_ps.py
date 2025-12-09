# -*- coding: utf-8 -*-
import unittest
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import ps
from .common.utils import fail_json, AnsibleFailJson


class TestPsModule(unittest.TestCase):

    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson
        self.module.warn = mock.Mock()
        self.params = {
            'all_processes': False,
            'processes_on_terminals': False,
            'exclude_session_leaders': False,
            'exclude_kernel': False,
            'full_list': False,
            'long_list': False,
            'kernel_processes': False,
            'kernel_threads_processes': False,
            'all_64bit': False,
            'no_thread_stats': False,
            'groups': None,
            'process_groups': None,
            'pids': None,
            'descendants': None,
            'ttys': None,
            'users_in_current_env': None,
            'all_users': None,
            'alt_name_list': None,
            'output_format': None,
            'sysv_format': None,
            'project': False,
            'full_names': False,
            'page_sizes_settings': False,
            'tree_pid': None,
            'recorded_output': None,
            'concatenated_output': True
        }
        self.module.params = self.params.copy()

    # ---------- BASIC FLAG TESTS ----------
    def test_default_command(self):
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps'])

    def test_all_processes_flag(self):
        self.module.params.update({'all_processes': True})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-A'])

    def test_exclude_session_leaders_flag(self):
        self.module.params.update({'exclude_session_leaders': True})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-d'])

    def test_exclude_kernel_flag(self):
        self.module.params.update({'exclude_kernel': True})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-e'])

    def test_processes_on_terminals_flag(self):
        self.module.params.update({'processes_on_terminals': True})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-a'])

    def test_full_list_flag(self):
        self.module.params.update({'full_list': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-f', cmd)

    def test_long_list_flag(self):
        self.module.params.update({'long_list': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-l', cmd)

    def test_kernel_processes_flag(self):
        self.module.params.update({'kernel_processes': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-k', cmd)

    def test_kernel_threads_processes_flag(self):
        self.module.params.update({'kernel_threads_processes': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-m', cmd)

    def test_all_64bit_flag(self):
        self.module.params.update({'all_64bit': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-M', cmd)

    def test_no_thread_stats_flag(self):
        self.module.params.update({'no_thread_stats': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-N', cmd)

    def test_project_flag(self):
        self.module.params.update({'project': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-P', cmd)

    def test_full_names_flag(self):
        self.module.params.update({'full_names': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-X', cmd)

    def test_page_sizes_settings_flag(self):
        self.module.params.update({'page_sizes_settings': True})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-Z', cmd)

    # ---------- STRING FLAGS ----------
    def test_groups_flag(self):
        self.module.params.update({'groups': 'system'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-G', 'system'])

    def test_process_groups_flag(self):
        self.module.params.update({'process_groups': '1,2'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-g', '1,2'])

    def test_pids_flag(self):
        self.module.params.update({'pids': '100,200'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-p', '100,200'])

    def test_descendants_flag(self):
        self.module.params.update({'descendants': '1234'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-L', '1234'])

    def test_ttys_flag(self):
        self.module.params.update({'ttys': 'tty0'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-t', 'tty0'])

    def test_users_in_current_env_flag(self):
        self.module.params.update({'users_in_current_env': 'root'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-u', 'root'])

    def test_all_users_flag(self):
        self.module.params.update({'all_users': 'root'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-U', 'root'])

    def test_alt_name_list_flag(self):
        self.module.params.update({'alt_name_list': '/etc/namelist'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-n', '/etc/namelist'])

    def test_output_format_flag(self):
        self.module.params.update({'output_format': 'pid,user,comm'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-o', 'pid,user,comm'])

    def test_sysv_format_flag(self):
        self.module.params.update({'sysv_format': 'ruser,pid,args'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-F', 'ruser,pid,args'])

    def test_tree_pid_flag(self):
        self.module.params.update({'tree_pid': 1234})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-T', '1234'])

    def test_combined_flags(self):
        self.module.params.update({'all_processes': True, 'full_list': True, 'output_format': 'pid,user,comm'})
        cmd = ps.build_ps_command(self.module)
        self.assertEqual(cmd, ['/bin/ps', '-A', '-f', '-o', 'pid,user,comm'])

    def test_kernel_thread_with_output_format(self):
        self.module.params.update({'kernel_threads_processes': True, 'output_format': 'THREAD,pid,user'})
        cmd = ps.build_ps_command(self.module)
        self.assertIn('-m', cmd)
        self.assertIn('-o', cmd)

    def test_exceed_128_limit_groups_invalid(self):
        long_value = " ".join([f"user{i}" for i in range(130)])
        self.module.params.update({'groups': long_value})
        with self.assertRaises(AnsibleFailJson):
            ps.validate_mutual_exclusiveness(self.module)

    def test_exceed_128_limit_users_invalid(self):
        long_value = ",".join([f"uid{i}" for i in range(130)])
        self.module.params.update({'users_in_current_env': long_value})
        with self.assertRaises(AnsibleFailJson):
            ps.validate_mutual_exclusiveness(self.module)

    def test_all_mutually_exclusive_primary_flags(self):
        self.module.params.update({'all_processes': True, 'exclude_kernel': True})
        cmd = ps.build_ps_command(self.module)
        # Should pick the first satisfied condition (-A)
        self.assertEqual(cmd, ['/bin/ps', '-A'])


if __name__ == '__main__':
    unittest.main()
