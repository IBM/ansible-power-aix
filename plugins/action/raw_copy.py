#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

#
# This implements a raw_copy action using the Ansible internal
# _transfer_file() function.
#

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

from ansible.errors import AnsibleAction, _AnsibleActionDone, AnsibleActionSkip
from ansible.module_utils._text import to_native
from ansible.plugins.action import ActionBase

class ActionModule(ActionBase):

    TRANSFERS_FILES = True

    def run(self, tmp=None, task_vars=None):
        ''' copy a file to remote node '''
        if task_vars is None:
            task_vars = dict()

        result = super(ActionModule, self).run(tmp, task_vars)

        try:
            dest = self._task.args.get('dest')
            if self._remote_file_exists(dest):
                raise AnsibleActionSkip("%s exists" % dest)

            src = self._task.args.get('src')
            src = self._find_needle('files', src)
            if not self._play_context.check_mode:
                self._transfer_file(src, dest)
                result['changed'] = True

            if self._play_context.check_mode:
                raise _AnsibleActionDone()

        except AnsibleAction as e:
            result.update(e.result)
        finally:
            self._remove_tmp_path(self._connection._shell.tmpdir)

        return result
