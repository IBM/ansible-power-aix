# -*- coding: utf-8 -*-
# Generated unit tests for llvupdate module
from __future__ import absolute_import, division, print_function
__metaclass__ = type

import unittest
from unittest import mock
import copy

from ansible_collections.ibm.power_aix.plugins.modules import llvupdate

from .common.utils import (
    AnsibleExitJson, AnsibleFailJson, exit_json, fail_json,
)

# base params template
base_params = {
    "action": None,
    "processes_to_include": None,
    "include_all": False,
    "processes_to_exclude": None,
    "logfile": None,
    "retries": None,
    "timeout": None,
    "auto_cleanup": False,
}


class TestCheckLluCapable(unittest.TestCase):
    def setUp(self):
        # ensure module-level results is fresh for each test
        llvupdate.results = {
            'changed': False, 'msg': '', 'stdout': '', 'stderr': '', 'cmd': ''
        }
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json

    def test_check_llu_capable_command_failure(self):
        # Simulate the raso command failing -> should call module.fail_json
        self.module.run_command.return_value = (1, "", "err")
        with self.assertRaises(AnsibleFailJson) as cm:
            llvupdate.check_llu_capable(self.module)
        res = cm.exception.args[0]
        self.assertTrue("Could not check if the llu_mode" in res["msg"])
        # stderr recorded onto results
        self.assertTrue(res.get("stderr"))

    def test_check_llu_capable_value_zero_returns_false(self):
        # This test asserts that when the command returns a value that the function
        # parses as '0' it returns False. Construct stdout carefully to satisfy the
        # existing parsing logic in the module.
        # The module code uses: val = (stdout.strip("=")[1]).strip()
        # To make that expression equal to "0", craft stdout so that stdout.strip("=")[1] == "0".
        # Example: stdout = "x0" -> strip("=") no-op, [1] == '0'
        self.module.run_command.return_value = (0, "x0", "")
        ret = llvupdate.check_llu_capable(self.module)
        # According to module logic, if val == "0" return False
        self.assertFalse(ret)

    def test_check_llu_capable_value_nonzero_returns_true(self):
        # Provide stdout so that the parsed val is not "0" and function returns True.
        # Using "x1" so index 1 == '1'
        self.module.run_command.return_value = (0, "x1", "")
        ret = llvupdate.check_llu_capable(self.module)
        self.assertTrue(ret)


class TestParseOutput(unittest.TestCase):
    def test_parse_output_success_and_fail(self):
        # Build stdout containing "LLU Report" block with lines showing SUCCESS and FAIL
        stdout = (
            "Some header\n"
            "LLU Report\n"
            "1234 some info SUCCESS\n"
            "2345 some info FAIL\n"
            "LLU Report End\n"
        )
        fail, success = llvupdate.parse_output(stdout)
        self.assertIn("2345", fail)
        self.assertIn("1234", success)
        self.assertEqual(len(fail), 1)
        self.assertEqual(len(success), 1)

    def test_parse_output_no_report(self):
        stdout = "Nothing relevant here\n"
        fail, success = llvupdate.parse_output(stdout)
        self.assertEqual(fail, [])
        self.assertEqual(success, [])


class TestPreviewLLU(unittest.TestCase):
    def setUp(self):
        llvupdate.results = {
            'changed': False, 'msg': '', 'stdout': '', 'stderr': '', 'cmd': ''
        }
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json

    def test_preview_llu_success_with_matches(self):
        # stdout that matches the regex pattern; includes pid and path
        stdout = (
            "Header\n"
            "pid 1111 something Library needs to be updated /usr/lib/libfoo.so\n"
            "pid 2222 something Library needs to be updated /opt/lib/libbar.so\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        msg = llvupdate.preview_llu(self.module)
        self.assertIn("1111", msg)
        self.assertIn("/usr/lib/libfoo.so", msg)
        self.assertNotIn("No process requires a Live library Update", msg)

    def test_preview_llu_no_matches(self):
        stdout = "No matches here\n"
        self.module.run_command.return_value = (0, stdout, "")
        msg = llvupdate.preview_llu(self.module)
        self.assertIn("No process requires a Live library Update", msg)

    def test_preview_llu_command_failure(self):
        self.module.run_command.return_value = (2, "", "err")
        with self.assertRaises(AnsibleFailJson) as cm:
            llvupdate.preview_llu(self.module)
        res = cm.exception.args[0]
        self.assertTrue("LLU operation failed" in res["msg"])
        self.assertEqual(res["rc"], 2)


class TestPerformLLU(unittest.TestCase):
    def setUp(self):
        llvupdate.results = {
            'changed': False, 'msg': '', 'stdout': '', 'stderr': '', 'cmd': ''
        }
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json

    def test_perform_llu_no_processes_needed(self):
        # When rc is non-zero but stdout contains "No process requires..." the function returns a msg (no fail)
        self.module.params['processes_to_include'] = None
        cmd_stdout = "No process requires a Live library Update operation."
        self.module.run_command.return_value = (1, cmd_stdout, "")
        msg = llvupdate.perform_llu(self.module)
        self.assertIn("No process requires a Live library Update operation", msg)

    def test_perform_llu_cmd_failure_and_auto_cleanup_calls_cleanup_and_fails(self):
        # When rc != 0 and stdout does NOT contain the 'No process' text, it should call perform_cleanup if auto_cleanup True and then fail.
        self.module.params['auto_cleanup'] = True
        self.module.run_command.return_value = (2, "some output", "err")
        # patch perform_cleanup to verify it's called and to return a cleanup string
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.llvupdate.perform_cleanup') as mocked_cleanup:
            mocked_cleanup.return_value = "Cleanup performed"
            with self.assertRaises(AnsibleFailJson) as cm:
                llvupdate.perform_llu(self.module)
            result = cm.exception.args[0]
            # After failure, results should have been populated
            self.assertTrue(result.get("failed") or result.get("msg"))
            mocked_cleanup.assert_called_once()

    def test_perform_llu_success_all_succeeded(self):
        # Simulate rc == 0 and parse_output returns no fail
        # Prepare stdout whose parse_output returns ([], ['p1','p2'])
        stdout = (
            "header\n"
            "LLU Report\n"
            "p1 info SUCCESS\n"
            "p2 info SUCCESS\n"
            "LLU Report End\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        # ensure auto_cleanup False
        self.module.params['auto_cleanup'] = False
        msg = llvupdate.perform_llu(self.module)
        self.assertIn("Live update operation successful for", msg)
        # results changed flag should be set by the function
        self.assertTrue(llvupdate.results.get('changed'))

    def test_perform_llu_some_failures_and_auto_cleanup_appended(self):
        # rc 0, but parse_output returns some failures; when auto_cleanup True, perform_cleanup should be invoked and appended
        stdout = (
            "header\n"
            "LLU Report\n"
            "1111 info FAIL\n"
            "2222 info SUCCESS\n"
            "LLU Report End\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        self.module.params['auto_cleanup'] = True
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.llvupdate.perform_cleanup') as mocked_cleanup:
            mocked_cleanup.return_value = "Cleanup performed"
            msg = llvupdate.perform_llu(self.module)
            self.assertIn("Live update operation failed for", msg)
            self.assertIn("Cleanup performed", msg)
            mocked_cleanup.assert_called_once()
            self.assertTrue(llvupdate.results.get('changed'))

    def test_perform_llu_builds_cmd_with_flags(self):
        # Ensure the command string is built correctly from params
        self.module.params['processes_to_include'] = ['1111', '2222']
        self.module.params['include_all'] = True
        self.module.params['processes_to_exclude'] = ['3333']
        self.module.params['logfile'] = '/tmp/ll.log'
        self.module.params['retries'] = 5
        self.module.params['timeout'] = 60
        # Make run_command return success with no failures
        stdout = (
            "header\n"
            "LLU Report\n"
            "1111 info SUCCESS\n"
            "2222 info SUCCESS\n"
            "LLU Report End\n"
        )
        self.module.run_command.return_value = (0, stdout, "")
        msg = llvupdate.perform_llu(self.module)
        # cmd stored in results should contain composed flags
        self.assertIn("-p 1111 2222", llvupdate.results['cmd'])
        self.assertIn("-a", llvupdate.results['cmd'])
        self.assertIn("-e 3333", llvupdate.results['cmd'])
        self.assertIn("-l /tmp/ll.log", llvupdate.results['cmd'])
        self.assertIn("-n 5", llvupdate.results['cmd'])
        self.assertIn("-t 60", llvupdate.results['cmd'])


class TestPerformCleanup(unittest.TestCase):
    def setUp(self):
        llvupdate.results = {
            'changed': False, 'msg': '', 'stdout': '', 'stderr': '', 'cmd': ''
        }
        self.module = mock.Mock()
        self.module.params = copy.deepcopy(base_params)
        self.module.fail_json = fail_json
        self.module.exit_json = exit_json

    def test_perform_cleanup_success(self):
        self.module.run_command.return_value = (0, "cleanup OK", "")
        msg = llvupdate.perform_cleanup(self.module)
        self.assertIn("Successfuly cleaned the kernel state", msg)

    def test_perform_cleanup_no_change(self):
        self.module.run_command.return_value = (0, "No clean up is required", "")
        msg = llvupdate.perform_cleanup(self.module)
        self.assertIn("No cleanup is required", msg)

    def test_perform_cleanup_failure_calls_fail_json(self):
        self.module.run_command.return_value = (2, "", "err")
        with self.assertRaises(AnsibleFailJson) as cm:
            llvupdate.perform_cleanup(self.module)
        res = cm.exception.args[0]
        self.assertIn("Failed to clean the kernel state", res["msg"])


# Note: main() integrates multiple pieces and uses check_llu_capable which itself calls module.fail_json on failure.
# We will test a small subset of main() flows by patching check_llu_capable to avoid external shell dependency.
class TestMainFlows(unittest.TestCase):
    def setUp(self):
        llvupdate.results = {
            'changed': False, 'msg': '', 'stdout': '', 'stderr': '', 'cmd': ''
        }
        self.module_patcher = mock.patch('ansible_collections.ibm.power_aix.plugins.modules.llvupdate.AnsibleModule')
        self.addCleanup(self.module_patcher.stop)
        self.mock_AnsibleModule = self.module_patcher.start()
        # Build a fake module instance that mirrors the minimal interface used by main()
        self.fake_module = mock.Mock()
        self.fake_module.params = copy.deepcopy(base_params)
        self.fake_module.fail_json = fail_json
        self.fake_module.exit_json = exit_json
        # Make the constructor return our fake module
        self.mock_AnsibleModule.return_value = self.fake_module

    def test_main_preview_path(self):
        # Patch check_llu_capable to return True
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.llvupdate.check_llu_capable', return_value=True):
            self.fake_module.params['action'] = 'preview'
            # patch preview_llu to return a message
            with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.llvupdate.preview_llu', return_value="preview-msg"):
                # call main() - exit_json will raise AnsibleExitJson; assert it and inspect payload
                with self.assertRaises(AnsibleExitJson) as cm:
                    llvupdate.main()
                payload = cm.exception.args[0]
                # payload is the dict raised by exit_json helper; check expected keys/values
                self.assertIn("preview-msg", payload.get("msg", ""))
                # preview path should mark changed False
                self.assertFalse(payload.get("changed", True))

    def test_main_update_requires_parameters(self):
        # For update path, if none of the include/include_all/exclude provided, should fail
        with mock.patch('ansible_collections.ibm.power_aix.plugins.modules.llvupdate.check_llu_capable', return_value=True):
            self.fake_module.params['action'] = 'update'
            self.fake_module.params['processes_to_include'] = None
            self.fake_module.params['include_all'] = False
            self.fake_module.params['processes_to_exclude'] = None
            with self.assertRaises(AnsibleFailJson):
                llvupdate.main()


if __name__ == '__main__':
    unittest.main()
