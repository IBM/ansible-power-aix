#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: entstat
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Collects Ethernet device statistics using the entstat command on AIX
version_added: "2.2.0"
description:
  - This module allows you to gather statistics from Ethernet devices using the AIX entstat command.
  - Supports device-generic statistics, device-specific reporting, reset, and debug trace toggle.
options:
  device_name:
    description:
      - Name of the Ethernet device (for example, ent0).
    type: str
    required: true
  device_statistics:
    description:
      - Displays all statistics, including device-specific statistics (-d).
    type: bool
    default: false
  reset_stats:
    description:
      - Resets all statistics back to initial values (-r).
      - Only privileged users can issue this flag.
    type: bool
    default: false
  debug_trace:
    description:
      - Toggles debug trace in some device drivers (-t).
    type: bool
    default: false
  recorded_output:
    description:
      - Path to file where command output should be written.
    type: str
  concatenated_output:
    description:
      - Controls whether the output is appended to the file or overwrites it.
    type: bool
    required: true
notes:
  - You can refer to the IBM documentation for additional information on the entstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=e-entstat-command).
'''

EXAMPLES = r'''
- name: Run entstat on ent0 with generic stats
  ibm.power_aix.entstat:
    device_name: ent0

- name: Run entstat with device-specific stats on ent1
  ibm.power_aix.entstat:
    device_name: ent1
    device_statistics: true

- name: Run entstat with reset stats
  ibm.power_aix.entstat:
    device_name: ent0
    reset_stats: true

- name: Run entstat with debug trace enabled
  ibm.power_aix.entstat:
    device_name: ent0
    debug_trace: true
'''

RETURN = r'''
msg:
    description: Execution message indicating success or failure.
    returned: always
    type: str
    sample: 'entstat executed successfully with given options.'
cmd:
    description: Full entstat command executed.
    returned: always
    type: str
    sample: 'entstat -d ent0'
rc:
    description: Return code from entstat command.
    returned: always
    type: int
stdout:
    description: Standard output from entstat command.
    returned: always
    type: str
stderr:
    description: Error output from entstat command (if any).
    returned: on failure
    type: str
'''

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import os

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def build_entstat_command(module):
    '''
    Build the entstat command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created entstat command
    '''
    cmd = ['entstat']

    if module.params['device_statistics']:
        cmd.append('-d')
    if module.params['reset_stats']:
        cmd.append('-r')
    if module.params['debug_trace']:
        cmd.append('-t')

    cmd.append(module.params['device_name'])
    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            device_name=dict(type='str', required=True),
            device_statistics=dict(type='bool', default=False),
            reset_stats=dict(type='bool', default=False),
            debug_trace=dict(type='bool', default=False),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True),
        ),
        supports_check_mode=False
    )

    result = dict(changed=False, msg='', cmd='', rc=0, stdout='', stderr='')

    cmd = build_entstat_command(module)

    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)

    result = {
        'changed': False,
        'cmd': cmd,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr
    }

    if rc != 0:
        result['msg'] = f"entstat command failed with command  {cmd}"
        module.fail_json(**result)
    else:
        if module.params['recorded_output']:
            output_file = module.params['recorded_output']
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    module.fail_json(msg=f"Failed to create directory {output_dir}: {str(e)}", **result)
            mode = 'a' if module.params['concatenated_output'] else 'w'
            with open(output_file, mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] = f"entstat executed successfully with command '{cmd}' and output written to {output_file}"
        else:
            result['msg'] = f"entstat executed successfully with command '{cmd}'"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
