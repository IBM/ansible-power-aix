# -*- coding: utf-8 -*-
import unittest
import re
from unittest import mock
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.power_aix.plugins.modules import audit
from .common.utils import fail_json, AnsibleFailJson


class TestAuditModule(unittest.TestCase):

    def setUp(self):
        self.module = mock.Mock(spec=AnsibleModule)
        self.module.fail_json = fail_json
        self.module.fail_json.side_effect = AnsibleFailJson
        self.module.exit_json = mock.Mock(side_effect=SystemExit)
        self.module.warn = mock.Mock()

        self.module.params = {
            "action": "query",
            "panic": False,
            "fullpath": False,
        }

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.access", return_value=True)
    def test_config_files_ok(self, m_access, m_exists):
        self.assertTrue(audit.check_audit_config_file(self.module))

    @mock.patch("os.path.exists", side_effect=[False, True, True, True, True])
    def test_missing_config(self, m_exists):
        with self.assertRaises(AnsibleFailJson):
            audit.check_audit_config_file(self.module)

    @mock.patch("os.path.exists", return_value=True)
    @mock.patch("os.access", return_value=False)    
    def test_unreadable_config(self, m_access, m_exists):
        with self.assertRaises(AnsibleFailJson):
            audit.check_audit_config_file(self.module)

    def test_build_query(self):
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "query"])

    def test_build_start(self):
        self.module.params.update({"action": "start"})
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "start"])

    def test_build_on(self):
        self.module.params.update({"action": "on"})
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "on"])

    def test_build_on_panic(self):
        self.module.params.update({"action": "on", "panic": True})
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "on", "panic"])

    def test_build_on_fullpath(self):
        self.module.params.update({"action": "on", "fullpath": True})
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "on", "fullpath"])

    def test_build_off(self):
        self.module.params.update({"action": "off"})
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "off"])

    def test_shutdown(self):
        self.module.params.update({"action": "shutdown"})
        cmd = audit.build_audit_command(self.module)
        self.assertEqual(cmd, ["audit", "shutdown"])

    def test_panic_invalid_start(self):
        self.module.params.update({"action": "start", "panic": True})
        with self.assertRaises(AnsibleFailJson):
            audit.validate_audit_status(self.module)

    def test_panic_invalid_off(self):
        self.module.params.update({"action": "off", "panic": True})
        with self.assertRaises(AnsibleFailJson):
            audit.validate_audit_status(self.module)

    def test_fullpath_invalid_start(self):
        self.module.params.update({"action": "start", "fullpath": True})
        with self.assertRaises(AnsibleFailJson):
            audit.validate_audit_status(self.module)

    def test_fullpath_invalid_off(self):
        self.module.params.update({"action": "off", "fullpath": True})
        with self.assertRaises(AnsibleFailJson):
            audit.validate_audit_status(self.module)

    def test_start_when_on(self):
        self.module.run_command = mock.Mock(return_value=(0, "auditing on\n", ""))

        self.module.params.update({"action": "start"})
        with self.assertRaises(SystemExit):
            audit.validate_audit_status(self.module)

    def test_on_when_on(self):
        self.module.run_command = mock.Mock(return_value=(0, "auditing on\n", ""))

        self.module.params.update({"action": "on"})
        with self.assertRaises(SystemExit):
            audit.validate_audit_status(self.module)

    def test_shutdown_when_off(self):
        self.module.run_command = mock.Mock(return_value=(0, "auditing off\n", ""))

        self.module.params.update({"action": "shutdown"})
        with self.assertRaises(SystemExit):
            audit.validate_audit_status(self.module)

    def test_off_when_fully_shutdown(self):
        self.module.run_command = mock.Mock(
            return_value=(0, "auditing off\naudit events:\n none\n", "")
        )

        self.module.params.update({"action": "off"})
        with self.assertRaises(SystemExit):
            audit.validate_audit_status(self.module)

    def test_valid_start_when_off(self):
        self.module.run_command = mock.Mock(return_value=(0, "auditing off\n", ""))

        self.module.params.update({"action": "start"})
        self.assertTrue(audit.validate_audit_status(self.module))

    def test_valid_on_when_off(self):
        self.module.run_command = mock.Mock(return_value=(0, "auditing off\n", ""))

        self.module.params.update({"action": "on"})
        self.assertTrue(audit.validate_audit_status(self.module))


if __name__ == "__main__":
    unittest.main()
