#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}


import time

from datetime import datetime, timedelta

from ansible.errors import AnsibleConnectionFailure
from ansible.plugins.action import ActionBase


class TimedOutException(Exception):
    pass


class ActionModule(ActionBase):
    TRANSFERS_FILES = False
    _VALID_ARGS = frozenset(('post_reboot_delay', 'pre_reboot_delay', 'test_command', 'reboot_timeout'))

    boot_time_command = 'who -b'
    reboot_command = 'shutdown -r'
    DEFAULT_PRE_REBOOT_DELAY = 0
    DEFAULT_POST_REBOOT_DELAY = 0

    def __init__(self, *args, **kwargs):
        super(ActionModule, self).__init__(*args, **kwargs)

    @property
    def pre_reboot_delay(self):
        return self._check_delay('pre_reboot_delay', self.DEFAULT_PRE_REBOOT_DELAY)

    @property
    def post_reboot_delay(self):
        return self._check_delay('post_reboot_delay', self.DEFAULT_POST_REBOOT_DELAY)

    def _check_delay(self, key, default):
        """Ensure that the value is positive or zero"""
        value = int(self._task.args.get(key, self._task.args.get(key + '_sec', default)))
        if value < 0:
            value = 0
        return value

    def perform_reboot(self, pre_reboot_delay):
        reboot_result = {}
        reboot_command = 'shutdown -r'

        if pre_reboot_delay != 0:
            self._display.vvv("Waiting for pre reboot delay")
            time.sleep(pre_reboot_delay)

        try:
            self._display.vvv("System reboot process has started....")
            reboot_result = self._low_level_execute_command(reboot_command)
        except AnsibleConnectionFailure:
            # To handle the case when system closes too quickly, continuing ahead
            self._display.vvv('AnsibleConnectionFailure has been caught and handled')
            reboot_result['rc'] = 0

        return reboot_result

    def validate_reboot(self, test_command, reboot_timeout=None, action_kwargs=None):
        self._display.vvv('Validating reboot....')
        result = {}

        try:
            if reboot_timeout is None:
                reboot_timeout = 300

            self.do_until_success_or_timeout(
                reboot_timeout=reboot_timeout,
                test_command=test_command,
                action_kwargs=action_kwargs)

            result['rebooted'] = True
            result['changed'] = True
            result['msg'] = "System has been rebooted SUCCESSFULLY"

        except TimedOutException:
            result['failed'] = True
            result['rebooted'] = True
            result['msg'] = "Reboot Validation failed due to timeout"
            return result

        return result

    def do_until_success_or_timeout(self, reboot_timeout, test_command, action_kwargs=None):
        max_end_time = datetime.utcnow() + timedelta(seconds=reboot_timeout)
        if action_kwargs is None:
            action_kwargs = {}
        if test_command is None:
            test_command = 'whoami'

        while datetime.utcnow() < max_end_time:
            try:
                result = self._low_level_execute_command(test_command, sudoable=True)
                if result['rc'] == 0:
                    return
            except Exception as e:
                if isinstance(e, AnsibleConnectionFailure):
                    try:
                        self._connection.reset()
                    except AttributeError:
                        pass
        raise TimedOutException("Connection reset failed while validating the reboot.")

    def run(self, tmp=None, task_vars=None):
        self._supports_async = True

        test_command = self._task.args.get('test_command', None)
        reboot_timeout = self._task.args.get('reboot_timeout', None)

        start = datetime.utcnow()

        if self._connection.transport == 'local':
            msg = 'Cannot reboot the control node. Running with local connection.'
            return {'changed': False, 'elapsed': 0, 'rebooted': False, 'failed': True, 'msg': msg}

        if task_vars is None:
            task_vars = {}

        result = super(ActionModule, self).run(tmp, task_vars)

        if result.get('skipped', False) or result.get('failed', False):
            return result

        reboot_result = self.perform_reboot(self.pre_reboot_delay)

        if reboot_result['rc'] != 0:
            self._display.vvv("Reboot command has failed. System still running")
            result['failed'] = True
            result['rebooted'] = False
            reboot_res_stdout = reboot_result['stdout']
            reboot_res_stderr = reboot_result['stderr']
            result['msg'] = f"Reboot command failed. Error was {reboot_res_stdout}, {reboot_res_stderr}"
            elapsed = datetime.utcnow() - start
            result['elapsed'] = str(elapsed.seconds) + ' sec'
            return result

        if self.post_reboot_delay != 0:
            reboot_delay = self.post_reboot_delay
            self._display.vvv(f"waiting for post reboot delay of {reboot_delay} seconds")
            time.sleep(self.post_reboot_delay)

        result = self.validate_reboot(test_command, reboot_timeout, action_kwargs=None)

        elapsed = datetime.utcnow() - start
        result['elapsed'] = str(elapsed.seconds) + ' sec'

        return result
