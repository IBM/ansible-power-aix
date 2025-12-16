#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025- IBM, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: audit
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Control the AIX auditing subsystem.
description:
  - Provides Ansible automation support for managing AIX audit subsystem using the audit command.
  - The module supports start, shutdown, on, off, and query operations with validation for WPAR and fullpath/panic options.
  - It reads configuration from /etc/security/audit/config and related audit configuration files.
version_added: "2.2.0"
requirements:
  - AIX >= 7.1
options:
  action:
    description:
      - Defines the audit operation to perform.
      - C(start) Starts the audit subsystem. This option reads the instructions in the configuration files and performs the auditing
      - C(shutdown) Stops the collection of audit records and resets the configuration information by removing the definition of classes from the kernel tables
      - C(off) Suspends the auditing system, but leaves the configuration valid. Data collection pauses until you give the 'audit on' command
      - C(on) Restarts the auditing system after a suspension.
      - C(query) Queries the auditing status of the audit subsystem.
    required: true
    type: str
    choices: [ 'start', 'shutdown', 'on', 'off', 'query' ]
  panic:
    description:
      - Used only with C(action=on). Enables panic mode (system halts if bin data cannot be written).
    type: bool
    default: false
  fullpath:
    description:
      - Used with C(action=on). Enables full path capture for FILE_* and PROC_* events.
    type: bool
    default: false
notes:
  - Refer to IBM documentation for more details U(https://www.ibm.com/docs/en/aix/7.3?topic=a-audit-command)
'''

EXAMPLES = r'''
- name: Start the AIX audit subsystem
  audit:
    action: start

- name: Turn auditing off
  audit:
    action: 'off'

- name: Restart audit with panic mode
  audit:
    action: 'on'
    panic: true

- name: Query audit subsystem status
  audit:
    action: query
'''

RETURN = r'''
msg:
    description: Execution message indicating success or failure.
    returned: always
    type: str
    sample: 'audit executed successfully with given options.'
cmd:
    description: Full fcstat command executed.
    returned: always
    type: str
    sample: 'fcstat -e fcs0'
rc:
    description: Return code from fcstat command.
    returned: always
    type: int
stdout:
    description: Standard output from fcstat command.
    returned: always
    type: str
stderr:
    description: Error output from fcstat command (if any).
    returned: on failure
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import os
import re


def check_audit_config_file(module):
    """
    check audit configration file:
    arguments:
        module  (dict): The Ansible module
    Returns:
        True : If all the configration file is present
    """

    required_files = [
        "/etc/security/audit/config",
        "/etc/security/audit/events",
        "/etc/security/audit/objects",
        "/etc/security/audit/bincmds",
        "/etc/security/audit/streamcmds"
    ]

    missing = []
    unreadable = []

    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
        elif not os.access(f, os.R_OK):
            unreadable.append(f)

    if missing:
        module.fail_json(msg=f"Missing audit configuration files: {', '.join(missing)}")

    if unreadable:
        module.fail_json(msg=f"Unreadable audit configuration files: {', '.join(unreadable)}")

    return True


def validate_audit_status(module):
    """
    Applies REAL AIX audit state rules including:
      - No 'start' when auditing on
      - No 'on' when auditing on
      - No 'shutdown' when auditing off
      - No 'off' when system already fully shutdown
      - Check mutual exclusiveness of options
    """

    action = module.params['action']
    panic = module.params['panic']
    fullpath = module.params['fullpath']

    if panic and action != "on":
        module.fail_json(msg=f" 'panic' option is not allowed with action: '{action}'.")
    if fullpath and action != "on":
        module.fail_json(
            msg=f"'fullpath' option is not allowed with action: '{action}'."
        )

    # Query always executes
    if action == "query":
        return True

    rc, stdout, stderr = module.run_command(["audit", "query"])

    if rc != 0:
        module.fail_json(msg=f"Failed to run 'audit query': {stderr}", rc=rc)

    auditing_on = bool(re.search(r"auditing\s+on", stdout, re.IGNORECASE))
    auditing_off = bool(re.search(r"auditing\s+off", stdout, re.IGNORECASE))
    events_empty = bool(re.search(r"audit events:\s*none", stdout, re.IGNORECASE))

    if auditing_on and action == "start":
        module.exit_json(
            changed=False,
            msg="Audit already ON — cannot run 'audit start' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    if auditing_on and action == "on":
        module.exit_json(
            changed=False,
            msg="Audit already ON — cannot run 'audit on' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    if auditing_off and action == "shutdown":
        module.exit_json(
            changed=False,
            msg="Audit already OFF — cannot run 'audit shutdown' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    if (auditing_off or events_empty) and action == "off":
        module.exit_json(
            changed=False,
            msg="Audit already OFF — cannot run 'audit off' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    return True


def build_audit_command(module):
    '''
    Build the audit command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created ps command
    '''

    cmd = ['audit']
    action = module.params['action']
    panic = module.params['panic']
    fullpath = module.params['fullpath']

    if action == 'on':
        cmd.append('on')
        if panic:
            cmd.append('panic')
        if fullpath:
            cmd.append('fullpath')

    elif action == 'off':
        cmd.append('off')

    elif action == 'start':
        cmd.append('start')

    elif action == 'shutdown':
        cmd.append('shutdown')

    elif action == 'query':
        cmd.append('query')

    return cmd


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['start', 'shutdown', 'on', 'off', 'query']),
            panic=dict(type='bool', default=False),
            fullpath=dict(type='bool', default=False),
        ),
        supports_check_mode=False
    )

    check_audit_config_file(module)
    validate_audit_status(module)

    cmd = build_audit_command(module)

    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=False)

    result = {
        'changed': True,
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout.strip(),
        'stderr': stderr.strip(),
    }

    if rc != 0:
        result['msg'] = f"audit command failing with command: '{' '.join(cmd)}'"
        module.fail_json(**result)

    if module.params['action'] == 'query':
        result['changed'] = False

    result['msg'] = f"Audit command executed successfully with cmd: '{' '.join(cmd)}'"
    module.exit_json(**result)


if __name__ == '__main__':
    main()
