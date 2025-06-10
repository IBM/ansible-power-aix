#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: vmstat
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Run the AIX vmstat command to report system stats.
description:
  - Enables Ansible to invoke AIX's vmstat utility with full flag support.
version_added: "2.1.0"
requirements:
  - AIX >= 7.1
options:
  show_fork_stats:
    description:
      - Reports the number of forks since system startup.
    type: bool
    default: false
  show_interrupts:
    description:
      - Displays the number of interrupts by the device since system startup.
    type: bool
    default: false
  show_paging_stats:
    description:
      - Shows the absolute count of paging events since system initialization.
    type: bool
    default: false
  io_view:
    description:
      - Displays I/O-oriented view with additional I/O wait columns.
    type: bool
    default: false
  with_fs_wait:
    description:
      - Adds file system wait column to I/O view. Used with C(io_view).
    type: bool
    default: false
  timestamp:
    description:
      - Prints timestamp for each output line.
    type: bool
    default: false
  vmm_stats:
    description:
      - Shows detailed VMM statistics.
    type: bool
    default: false
  hypervisor_stats:
    description:
      - Shows hypervisor paging-related statistics.
    type: bool
    default: false
  wide_output:
    description:
      - Enables wide mode display.
    type: bool
    default: false
  large_page_stats:
    description:
      - Displays large page section details.
    type: bool
    default: false
  recorded_output:
    description:
      - Folder path to command output in machine .
    type: str
  wpar_name:
    description:
      - Specifies WPAR name or ALL to report stats per WPAR.
    type: str
  pagesize_stats:
    description:
      - Appends stats for specified page size or physical volume (-p).
    type: str
  page_stats_only:
    description:
      - Displays only stats for specified page size or volume (-P).
    type: str
  scale_power:
    description:
      - Scaling factor for percentage values (e.g., 0-3 for 10^power).
    type: int
  interval:
    description:
      - Number of seconds between each report.
    type: int
  count:
    description:
      - Number of reports to generate. Used with C(interval).
    type: int
  concatenated_output:
    description:
      - Controls whether the output of the vmstat command is appended to the output file or is overwrited.
      - If set to true, output will be appended to the file.
      - If set to false, the file will be overwritten with fresh output.
    type: bool
    required: true

notes:
  - You can refer to the IBM documentation for additional information on the vmstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=v-vmstat-command).
'''

EXAMPLES = r'''
- name: Run vmstat with timestamp
  vmstat_command:
    timestamp: true
    interval: 2
    count: 5

- name: Run vmstat with showing paging stat
  vmstat_command:
    show_paging_stats: true
    wpar_name: "ALL"
    interval: 1
    count: 3
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Group: foo SUCCESSFULLY created.'
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: When the command is executed.
    type: int
stdout':
    description: The standard output.
    returned: If the command failed.
    type: str
stderr':
    description: The standard error.
    returned: If the command failed.
    type: str
'''

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def build_vmstat_command(module):
    cmd = ['vmstat']

    # Fail if more than one of -@, -p, -P is used together
    count = sum([
        bool(module.params['wpar_name']),
        bool(module.params['pagesize_stats']),
        bool(module.params['page_stats_only'])])

    if count > 1:
        module.fail_json(msg="Options -@, -p, and -P are mutually exclusive. Only one of them can be used at a time.")

    # Fail: -S cannot be used with: -f, -s, -i, -v, -P
    if module.params['scale_power'] is not None and (
        module.params['show_fork_stats']
        or module.params['show_paging_stats']
        or module.params['show_interrupts']
        or module.params['vmm_stats']
        or module.params['page_stats_only']
    ):
        module.fail_json(msg="The -S option cannot be used with -f, -s, -i, -v, and -P.")

    # Fail: -i  cannot be used with: -S, -@, -p, -P, -h
    if module.params['show_interrupts'] and (
        module.params['scale_power']
        or module.params['wpar_name']
        or module.params['pagesize_stats']
        or module.params['page_stats_only']
        or module.params['hypervisor_stats']
    ):
        module.fail_json(msg="The -i option cannot be used with -S, -@, -p, -P, or -h.")

    # Fail:  -v cannot be used with: -p, -P when -s is not true
    if module.params['vmm_stats'] and (module.params['pagesize_stats'] or module.params['page_stats_only']) and not module.params['show_paging_stats']:
        module.fail_json(msg="The -v option cannot be used with -p or -P.")
    # Fail:  -l cannot be used with: -p, -P
    if module.params['large_page_stats'] and (module.params['pagesize_stats'] or module.params['page_stats_only']):
        module.fail_json(msg="The -l option cannot be used with -p or -P.")

        # Fail: -s  cannot be used with: -h, -P
    if module.params['show_paging_stats'] and (module.params['hypervisor_stats'] or module.params['page_stats_only']):
        module.fail_json(msg="The -s option cannot be used with -h, -P ")

        # Fail: -h  cannot be used with: -p, -P, -s, -i
    if module.params['hypervisor_stats'] and (
        module.params['show_paging_stats']
        or module.params['page_stats_only']
        or module.params['pagesize_stats']
        or module.params['show_interrupts']
    ):
        module.fail_json(msg="The -h option cannot be used with -s, -P, -p, -i")

    if module.params['show_fork_stats']:
        cmd.append('-f')

    elif module.params['show_paging_stats']:
        cmd.append('-s')
        # Only valid combinations with -s
        if module.params['vmm_stats']:
            cmd.append('-v')
        if module.params['large_page_stats']:
            cmd.append('-l')
        if module.params['wpar_name']:
            cmd.extend(['-@', module.params['wpar_name']])
        elif module.params['pagesize_stats']:
            cmd.extend(['-p', module.params['pagesize_stats']])
    elif module.params['show_interrupts']:
        if not module.params['vmm_stats']:
            cmd.append('-i')
            if module.params['interval'] is not None:
                cmd.append(str(module.params['interval']))
                if module.params['count'] is not None:
                    cmd.append(str(module.params['count']))
    elif module.params['hypervisor_stats']:
        cmd.append('-h')
        # Only allow with -I, -t, -l, -w, and -v
        if module.params['io_view']:
            cmd.append('-I')
            if module.params['with_fs_wait']:
                cmd.append('-W')
        if module.params['timestamp']:
            cmd.append('-t')
        if module.params['large_page_stats']:
            cmd.append('-l')
        if module.params['wide_output']:
            cmd.append('-w')
        if module.params['vmm_stats']:
            cmd.append('-v')
        if module.params['interval'] is not None:
            cmd.append(str(module.params['interval']))
            if module.params['count'] is not None:
                cmd.append(str(module.params['count']))

    else:
        # If -vmm_stats is set  ignore other flags listed in image
        if module.params['vmm_stats']:
            cmd.append('-v')
        else:
            # Regular compatible flags
            if module.params['io_view']:
                cmd.append('-I')
                if module.params['with_fs_wait']:
                    cmd.append('-W')  # -W only valid with -I

            if module.params['timestamp']:
                cmd.append('-t')

            if module.params['wide_output']:
                cmd.append('-w')

            if module.params['large_page_stats']:
                cmd.append('-l')

            if module.params['wpar_name']:
                cmd.extend(['-@', module.params['wpar_name']])
            elif module.params['pagesize_stats']:
                cmd.extend(['-p', module.params['pagesize_stats']])
            elif module.params['page_stats_only']:
                cmd.extend(['-P', module.params['page_stats_only']])

            # -S not allowed with -f, -s, -i, -v, -P
            if module.params['scale_power']:
                cmd.extend(['-S', str(module.params['scale_power'])])

            # Interval and count: valid for general usage
            if module.params['interval'] is not None:
                cmd.append(str(module.params['interval']))
                if module.params['count'] is not None:
                    cmd.append(str(module.params['count']))

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            show_fork_stats=dict(type='bool', default=False),
            show_interrupts=dict(type='bool', default=False),
            show_paging_stats=dict(type='bool', default=False),
            io_view=dict(type='bool', default=False),
            with_fs_wait=dict(type='bool', default=False),
            timestamp=dict(type='bool', default=False),
            vmm_stats=dict(type='bool', default=False),
            hypervisor_stats=dict(type='bool', default=False),
            wide_output=dict(type='bool', default=False),
            large_page_stats=dict(type='bool', default=False),
            concatenated_output=dict(type='bool', required=True),
            wpar_name=dict(type='str'),
            pagesize_stats=dict(type='str'),
            page_stats_only=dict(type='str'),
            scale_power=dict(type='int'),
            recorded_output=dict(type='str'),
            interval=dict(type='int'),
            count=dict(type='int'),
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    cmd = build_vmstat_command(module)
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)

    result = {
        'changed': False,
        'cmd': cmd,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr
    }

    if rc != 0:
        module.fail_json(msg=f'vmstat command failing with command {cmd} ', **result)
    else:

        if module.params['recorded_output']:
            output_file = module.params['recorded_output']
            should_concat = module.params['concatenated_output']
            mode = 'a' if should_concat else 'w'  # 'a' = append, 'w' = overwrite
            with open(output_file, mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] = f"vmstat executed successfully with command '{cmd}' and Output written to {output_file}"
        else:
            result['changed'] = False
            result['msg'] = f"vmstat executed successfully with command '{cmd}'"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
