#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: fcstat
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Collects Fibre Channel adapter statistics using the fcstat command on AIX
version_added: "2.2.0"
description:
  - This module allows you to gather statistics from Fibre Channel (FC) adapters using the AIX fcstat command.
  - Supports device-generic and device-specific reporting, diagnostic mode, reset, and time-series reporting.
options:
  device_name:
    description:
      - Name of the Fibre Channel device (for example, fcs0).
    type: str
    required: true
  remove_delay:
    description:
      - Removes delay in generating output when the device is opened in nondiagnostic mode and the link is down.
    type: bool
    default: false
  all_statistics:
    description:
      - Displays all statistics, including device-specific statistics (-e).
    type: bool
    default: false
  reset_stats:
    description:
      - Resets some statistics back to initial values (-z).
      - Only privileged users can issue this flag.
    type: bool
    default: false
  interval:
    description:
      - Displays a time-series report of the traffic statistics continuously with a time interval between two consecutive reports,.
      - If set to 0, only a single report is generated.
    type: int
  count:
    description:
      - Number of reports to generate at the specified interval.
      - Must be used together with the interval option.
    type: int
  protocol:
    description:
      - Displays a time-series report of traffic statistics for a specific transport protocol (TP) that is specified with the Protocol parameter.
    type: str
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
  - You can refer to the IBM documentation for additional information on the fcstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=f-fcstat-command).
'''

EXAMPLES = r'''
- name: Run fcstat on fcs0 with generic stats
  ibm.power_aix.fcstat:
    device_name: fcs0

- name: Run fcstat with extended stats on fcs1
  ibm.power_aix.fcstat:
    device_name: fcs1
    extended_stats: true

- name: Run fcstat in diagnostic mode and reset stats
  ibm.power_aix.fcstat:
    device_name: fcs0
    diagnostic_mode: true
    reset_stats: true

- name: Run fcstat time-series with 5 second interval, 3 reports
  ibm.power_aix.fcstat:
    device_name: fcs0
    interval: 5
    protocol: scsi
'''

RETURN = r'''
msg:
    description: Execution message indicating success or failure.
    returned: always
    type: str
    sample: 'fcstat executed successfully with given options.'
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
__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
import os

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def is_valid_device(module, device_name):
    """
    Check if the given device exists in ODM.
    Returns True if valid, False otherwise.
    """
    cmd = ["lsdev", "-C", "-l", device_name, "-F", "name"]
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0 or not stdout.strip():
        module.fail_json(msg=f"Invalid device: {device_name}. Please specify a valid AIX FC adapter (e.g., fcs0).")
    return True


def validate_mutual_exclusiveness(module):
    '''
    Validate flag combinations for fcstat
    '''
    if module.params['device_name']:
        device_name = module.params['device_name']
        is_valid_device(module, device_name)
    if module.params['protocol'] and not module.params['interval']:
        module.fail_json(msg="'protocol' (-p) requires 'interval' (-t).")

    if module.params['reset_stats'] and module.params['all_statistics']:
        module.fail_json(msg="'reset_stats' and 'all_statistics' can not use togather.")
    if module.params['reset_stats'] and module.params['remove_delay']:
        module.fail_json(msg="'reset_stats' (-z) can not be use with option 'remove_delay' (-c).")
    # 'interval' and 'count' must always be used together
    if bool(module.params.get('interval')) != bool(module.params.get('count')):
        module.fail_json(msg="Options 'interval' and 'count' must be used together.")

    if (module.params.get('interval') or module.params.get('protocol')):
        if (module.params.get('reset_stats') or module.params.get('all_statistics') or module.params.get('remove_delay')):
            module.fail_json(msg=(
                "Options '-z', '-e', or '-c' cannot be used together with "
                "'-t Interval' or '-p Protocol'."
            ))


def build_fcstat_command(module):
    '''
    Build fcstat command from module parameters
    '''
    cmd = ['fcstat']

    if module.params['reset_stats']:
        cmd.append('-z')
        if module.params['remove_delay']:
            cmd.append('-c')

    elif module.params['all_statistics']:
        cmd.append('-e')
        if module.params['remove_delay']:
            cmd.append('-c')
    elif module.params['remove_delay']:
        cmd.append('-c')

    if module.params['interval'] is not None:
        cmd.extend(['-t', str(module.params['interval'])])
        if module.params['protocol']:
            cmd.extend(['-p', module.params['protocol']])

    if module.params['device_name'] is not None:
        cmd.append(module.params['device_name'])

    if module.params['interval'] is not None:
        if module.params['count'] is not None:
            count_value = int(module.params['count'])
            count_value = count_value + 5
            awk_filter = (f"awk 'NR > {count_value} {{exit}} {{print}}'")
            cmd = " ".join(cmd)
            cmd = f"unbuffer sh -c '{cmd}' | {awk_filter}"
            return cmd
    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            device_name=dict(type='str', required=True),
            remove_delay=dict(type='bool', default=False),
            all_statistics=dict(type='bool', default=False),
            reset_stats=dict(type='bool', default=False),
            interval=dict(type='int'),
            count=dict(type='int'),
            protocol=dict(type='str'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True),
        ),
        supports_check_mode=False
    )

    result = dict(changed=False, msg='', cmd='', rc=0, stdout='', stderr='')

    validate_mutual_exclusiveness(module)
    cmd = build_fcstat_command(module)
    result['cmd'] = " ".join(cmd)
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)

    result = {
        'changed': False,
        'cmd': cmd,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr
    }

    if rc != 0:
        result['msg'] = f"fcstat command failed with command  {cmd}"
        module.fail_json(**result)
    else:
        if module.params['recorded_output']:
            output_file = module.params['recorded_output']
            mode = 'a' if module.params['concatenated_output'] else 'w'
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    module.fail_json(msg=f"Failed to create directory {output_dir}: {str(e)}", **result)
            with open(output_file, mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] = f"fcstat executed successfully with command '{cmd}' and output written to {output_file}"
        else:
            result['msg'] = f"fcstat executed successfully with command '{cmd}'"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
