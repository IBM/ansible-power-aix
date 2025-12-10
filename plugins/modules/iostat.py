#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: iostat
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Run the AIX iostat command to monitor system I/O statistics.
description:
  - Enables Ansible to invoke AIX's iostat utility with comprehensive flag support.
version_added: "2.2.0"
requirements:
  - AIX >= 7.1
options:
  adapter_report:
    description:
      - Display the adapter throughput report (-a).
    type: bool
    default: false
  block_io:
    description:
      - Displays the block I/O device utilization statistics. The -b flag is mutually exclusive to all flags, except the -T flag.
    type: bool
    default: false
  no_tty_cpu:
    description:
      - Turns off the display of TTY utilization report or CPU utilization report.
      - If you do not specify the -d or -p flag, then by default the -d flag is turned on.
      - The -t and -d flags together turn off both disks and TTY or CPU statistics, allowed only with the -a or -s flags.
      - The -d flag is mutually exclusive with the -t flag unless you specify the -a or -s flag, too.
      - The -d flag is mutually exclusive with the -p flag unless you specify the -a or -s flag, too.
    type: bool
    default: false
  extended_drive:
    description:
      - Display extended tape/drive utilization.
    type: bool
    default: false
  fs_utilization:
    description:
      - Display file system utilization (-f).
    type: bool
    default: false
  fs_only:
    description:
      - Displays the file system utilization report, and turns off other utilization reports..
    type: bool
    default: false
  filesystems:
    description:
      - List of file filesystem to be used.
    type: str
  long_list:
    description:
      - Displays the output in long listing mode.
    type: bool
    default: false
  path_utilization:
    description:
      - Displays the path utilization report.
    type: bool
    default: false
  reset_ext_stats:
    description:
      - Specifies that the reset of min* and max* values should happen at each interval.
      - The default is to reset the values once when iostat is started.
      - The -R flag can be specified only with the -D flag
    type: bool
    default: false
  system_throughput:
    description:
      - Specifies the system throughput report.
      - You can specify the -a flag with the -A flag, but not when you have specified the -q or -Q flag.
    type: bool
    default: false
  no_disk:
    description:
      - Turns off the display of disk utilization report.
      - The -t and -d flags together turn off both disks and TTY or CPU statistics, allowed only with the -a or -s flags
    type: bool
    default: false
  show_timestamp:
    description:
      - Displays the time stamp.
    type: bool
    default: false
  nonzero_stats:
    description:
      - Display valid nonzero statistics.
    type: bool
    default: false
  reset_io:
    description:
      - Resets the disk input/output statistics.
      - Only root users can use this option.
    type: bool
    default: false
  xml_output:
    description:
      - Generates the XML output.
      - The default file name is iostat_DDMMYYHHMM.xml unless you specify a different file name by using the -o option.
    type: bool
    default: false
  scale_power:
    description:
      - Displays the processor statistics that are multiplied by a value of 10power.
      - The default value of the power parameter is 0
    type: int
  options_override:
    description:
       - Changes the content and presentation of the iostat report based on the values specified in option parameters.
    type: str
  wpar_stats:
    description:
      - Reports I/O activities of a workload partition.
      - Specify -@ 'ALL' to display the activity for the global environment and all workload partitions in the system.
      - Specify the -@ flag with a list of workload partition names to display the activity for that workload partition.
      - Specify -@ 'Global' to display the activity for the global environment only.
      - Specify the -@ flag inside a WPAR to display system-wide statistics along with WPAR statistics.
    type: str
  xml_output_path:
    description:
      - Specifies the file name for the XML output.
    type: str
  drives:
    description:
      - List of drives to include in the report.
    type: list
    elements: str
  interval:
    description:
      - Parameter specifies the amount of time in seconds between each report.
      - If the Interval parameter is not specified, the iostat command generates a single report containing statistics for the time since system startup (boot).
    type: int
  count:
    description:
      - The Count parameter can be specified in conjunction with the Interval parameter.
      - If the Count parameter is specified, the value of count determines the number of reports generated at Interval seconds apart.
      - If the 'count' is not mentioned with the 'interval' option, then the default value of 5 will be considered.
    type: int
  concatenated_output:
    description:
      - Controls whether the output of the iostat command is appended to the output file or is overwrited.
      - If set to true, output will be appended to the file.
      - If set to false, the file will be overwritten with fresh output.
    type: bool
    required: true
  recorded_output:
    description:
      - Path to file where command output should be written.
    type: str

notes:
  - You can refer to the IBM documentation for additional information on the vmstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=i-iostat-command).
'''

EXAMPLES = r'''
- name: Run iostat with adapter and timestamp
  ibm.power_aix.iostat:
    adapter_report: true
    show_timestamp: true
    interval: 2
    count: 3

- name: Run iostat with XML output
  ibm.power_aix.iostat:
    xml_output: true
    xml_output_path: '/tmp/iostat_report.xml'
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'iostat SUCCESSFULLY executed.'
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
import os

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def build_iostat_command(module):  # A, P need "Asynchronous I/O not configured" , F have issue and -p needed " No tapes found in the system"

    '''
    Build the iostat command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created iostat command
    '''

    cmd = ['iostat']

    if module.params['xml_output']:
        if any([
            module.params['adapter_report'], module.params['no_tty_cpu'],
            module.params['extended_drive'], module.params['fs_utilization'], module.params['fs_only'],
            module.params['long_list'], module.params['path_utilization'],
            module.params['reset_ext_stats'], module.params['system_throughput'], module.params['no_disk'],
            module.params['nonzero_stats'], module.params['reset_io'], module.params['wpar_stats'],
            module.params['block_io'], module.params['show_timestamp'], module.params['options_override'],
            module.params['scale_power']
        ]):
            module.fail_json(msg="No other option except -o can be combined with -X option")
        cmd.append('-X')
        if module.params['xml_output_path']:
            cmd.extend(['-o', module.params['xml_output_path']])
    else:

        if module.params['block_io']:
            if any([
                module.params['adapter_report'], module.params['no_tty_cpu'],
                module.params['fs_utilization'], module.params['fs_only'],
                module.params['long_list'], module.params['path_utilization'],
                module.params['reset_ext_stats'], module.params['system_throughput'], module.params['no_disk'],
                module.params['wpar_stats'], module.params['scale_power']
            ]):
                module.fail_json(msg="-b is mutually exclusive with all flags except -T, -D, -O, -V , -z.")
            elif not (module.params['interval']):
                module.fail_json(msg="interval is missing with -b option.")
            cmd.append('-b')
        if module.params['adapter_report']:
            if any([module.params['fs_utilization'], module.params['fs_only'], module.params['wpar_stats']]):
                module.fail_json(msg="-a is mutually exclusive with:  -f, -F, -@, -X, -b")
            cmd.append('-a')
        if module.params['no_tty_cpu']:
            if module.params['no_disk'] and not (module.params['adapter_report'] or module.params['system_throughput']):
                module.fail_json(msg="-d and -t cannot be used together unless -a or -s is specified")
            elif any([
                module.params['fs_only'], module.params['xml_output'], module.params['scale_power']
            ]):
                module.fail_json(msg="-d is mutually exclusive with: -F, -X, -S,")

            cmd.append('-d')

        if module.params['extended_drive']:
            if module.params['no_disk'] and not (module.params['adapter_report'] or module.params['system_throughput']):
                module.fail_json(msg="-D and -t together only allowed with -a or -s.")
            elif any([
                module.params['fs_utilization'], module.params['fs_only'], module.params['scale_power']
            ]):
                module.fail_json(msg="-D is mutually exclusive with: -f, -F, -P, -q, -Q, -S,")
            cmd.append('-D')
        if module.params['fs_utilization']:
            if any([
                module.params['adapter_report'], module.params['extended_drive'], module.params['fs_only'],
            ]):
                module.fail_json(msg="-f is mutually exclusive with -a, -D, -F, ")
            cmd.append('-f')
            if module.params['filesystems']:
                cmd.append(str(module.params['filesystems']))

        if module.params['long_list']:
            cmd.append('-l')

        if module.params['path_utilization']:
            if any([
                module.params['fs_only'], module.params['wpar_stats'],
                module.params['no_disk'], module.params['wpar_stats']
            ]):
                module.fail_json(msg="-m is mutually exclusive with  -F,  -t, -@")
            cmd.append('-m')

        if module.params['reset_ext_stats']:
            if not module.params['extended_drive']:
                module.fail_json(msg="The -R option can only be used together with -D.")
            cmd.append('-R')

        if module.params['system_throughput']:
            if any([
                module.params['wpar_stats']
            ]):
                module.fail_json(msg="-s is mutually exclusive with  -@")
            cmd.append('-s')

        if module.params['no_disk']:
            if any([
                module.params['reset_io'], module.params['wpar_stats']
            ]):
                module.fail_json(msg="-t is mutually exclusive with -z, -@")
            cmd.append('-t')

        if module.params['show_timestamp']:
            cmd.append('-T')

        if module.params['nonzero_stats']:
            cmd.append('-V')

        if module.params['reset_io']:
            cmd.append('-z')

        if module.params['scale_power'] is not None:
            cmd.extend(['-S', str(module.params['scale_power'])])

        if module.params['options_override']:
            cmd.extend(['-O', module.params['options_override']])

        if module.params['wpar_stats']:
            if any([
                module.params['adapter_report'], module.params['no_disk'], module.params['reset_ext_stats'],
                module.params['path_utilization'], module.params['system_throughput']
            ]):
                module.fail_json(msg="-@ cannot be used with -a, -t, -R, -s, or -m.")
            cmd.extend(['-@', module.params['wpar_stats']])

        if module.params['fs_only']:
            if any([
                module.params['adapter_report'], module.params['no_tty_cpu'], module.params['extended_drive'],
                module.params['fs_utilization'], module.params['path_utilization'],
                module.params['reset_ext_stats'], module.params['no_disk'],
                module.params['reset_io'], module.params['scale_power'], module.params['reset_ext_stats']
            ]):
                module.fail_json(msg="-F is mutually exclusive with -a, -d, -D, -f, -m, -R, -t -z , -S")
            cmd.append('-F')
            if module.params['filesystems']:
                cmd.append(str(module.params['filesystems']))

    if module.params['drives']:
        if any([
            module.params['fs_only']
        ]):
            module.fail_json(msg=" 'drives' cannot be used with -F  Option.")
        cmd.extend(module.params['drives'])

    if module.params['interval'] is not None:
        cmd.append(str(module.params['interval']))
        if module.params['count'] is not None:
            cmd.append(str(module.params['count']))
        else:
            module.params['count'] = 5
            cmd.append(str(module.params['count']))
    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            adapter_report=dict(type='bool', default=False),
            block_io=dict(type='bool', default=False),
            no_tty_cpu=dict(type='bool', default=False),
            extended_drive=dict(type='bool', default=False),
            fs_utilization=dict(type='bool', default=False),
            fs_only=dict(type='bool', default=False),
            long_list=dict(type='bool', default=False),
            path_utilization=dict(type='bool', default=False),
            reset_ext_stats=dict(type='bool', default=False),
            system_throughput=dict(type='bool', default=False),
            no_disk=dict(type='bool', default=False),
            show_timestamp=dict(type='bool', default=False),
            nonzero_stats=dict(type='bool', default=False),
            reset_io=dict(type='bool', default=False),
            xml_output=dict(type='bool', default=False),
            scale_power=dict(type='int'),
            options_override=dict(type='str'),
            filesystems=dict(type='str'),
            wpar_stats=dict(type='str'),
            xml_output_path=dict(type='str'),
            drives=dict(type='list', elements='str'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True),
            interval=dict(type='int'),
            count=dict(type='int')
        ),
        supports_check_mode=False
    )

    cmd = build_iostat_command(module)
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=False)

    result = {
        'changed': True,
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr
    }

    if rc != 0:
        result['msg'] = f"iostat command failed with command  {cmd}"
        module.fail_json(**result)
    else:

        if module.params['recorded_output']:
            output_file = module.params['recorded_output']
            should_concat = module.params['concatenated_output']
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    result['msg'] = f"Failed to create directory {output_dir}: {str(e)}"
                    module.fail_json(**result)
            mode = 'a' if should_concat else 'w'  # 'a' = append, 'w' = overwrite
            with open(output_file, mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] = f"iostat executed successfully with command '{cmd}' and Output written to {output_file}"
        else:
            result['changed'] = False
            result['msg'] = f"iostat executed successfully with command '{cmd}'"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
