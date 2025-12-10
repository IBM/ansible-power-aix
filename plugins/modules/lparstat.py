#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function


DOCUMENTATION = r'''
---
module: lparstat
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Collects LPAR statistics using the lparstat command on AIX
description:
  - Gather LPAR configuration, CPU, memory, hypervisor, and performance statistics using the AIX lparstat command.
version_added: "2.2.0"
requirements:
  - AIX >= 7.1

options:

  config_info:
    description:
      - Show general LPAR configuration information (-i).
    type: bool
    default: false

  wpar_output:
    description:
      - Show Workload Partition (WPAR) information (-W).
    type: bool
    default: false

  service_info:
    description:
      - Display service partition statistics (-s).
    type: bool
    default: false

  energy_tuning:
    description:
      - Show energy tuning parameters (-P).
    type: bool
    default: false

  security_mode:
    description:
      - Display extended security and environment information (-x).
    type: bool
    default: false

  detailed_cpu_stats:
    description:
      - Show detailed CPU statistics (-d).
    type: bool
    default: false

  memory_stats:
    description:
      - Display comprehensive memory statistics (-m).
    type: bool
    default: false

  io_memory_pools:
    description:
      - Display I/O memory entitlement pool statistics (-e).
    type: bool
    default: false

  page_coalescing:
    description:
      - Display page coalescing statistics (-p).
    type: bool
    default: false

  page_coalescing_wide:
    description:
      - Wide output for page coalescing statistics (-w).
    type: bool
    default: false

  reset_once:
    description:
      - Reset I/O memory entitlement high watermark once (-r).
    type: bool
    default: false

  reset_each_interval:
    description:
      - Reset I/O memory entitlement high watermark at each interval (-R).
    type: bool
    default: false

  hypervisor_stat_short:
    description:
      - Show short hypervisor statistics (-h).
    type: bool
    default: false

  hypervisor_stat_long:
    description:
      - Show detailed hypervisor statistics (-H).
    type: bool
    default: false

  export_xml:
    description:
      - Export output in XML format (-X).
    type: bool
    default: false

  output_file:
    description:
      - Path to the output file for XML or stored results.
    type: str

  spurr_based_metrics:
    description:
      - Report SPURR-based CPU utilization (-E).
    type: bool
    default: false

  spurr_based_metrics_wide:
    description:
      - Wide-format SPURR metrics (-Ew).
    type: bool
    default: false

  timestamp:
    description:
      - Include timestamp in output (-t).
    type: bool
    default: false

  micro_partition:
    description:
      - Display micro-partitioning statistics (-G).
    type: bool
    default: false

  utilization:
    description:
      - Display CPU utilization (-u).
    type: bool
    default: false

  interval:
    description:
      - Interval (seconds) between samples.
    type: int

  count:
    description:
      - Number of samples collected.
    type: int

  concatenated_output:
    description:
      - Whether to append output to the recorded file.
    type: bool
    required: true

  recorded_output:
    description:
      - Path to store recorded output.
    type: str

notes:
  - Refer to IBM documentation for more information at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=l-lparstat-command).
'''

EXAMPLES = r'''
- name: Run lparstat with basic configuration info
  ibm.power_aix.lparstat:
    config_info: true

- name: Run lparstat with WPAR and service information
  ibm.power_aix.lparstat:
    config_info: true
    wpar_output: true
    service_info: true
    energy_tuning: true

- name: Run detailed memory and I/O stats with page coalescing
  ibm.power_aix.lparstat:
    memory_stats: true
    io_memory_pools: true
    page_coalescing: true
    page_coalescing_wide: true
    reset_once: true

- name: Collect SPURR-based CPU metrics
  ibm.power_aix.lparstat:
    spurr_based_metrics: true
    spurr_based_metrics_wide: true

- name: Gather repeated interval samples
  ibm.power_aix.lparstat:
    detailed_cpu_stats: true
    interval: 2
    count: 5

- name: Export output in XML format
  ibm.power_aix.lparstat:
    export_xml: true
    output_file: "/tmp/lparstat_report.xml"

- name: Record output to a file with append mode
  ibm.power_aix.lparstat:
    config_info: true
    recorded_output: "/tmp/lparstat_output.txt"
    concatenated_output: true
'''

RETURN = r'''
msg:
    description: The execution message indicating success or failure.
    returned: always
    type: str
    sample: 'lparstat executed successfully with given options.'

cmd:
    description: The full lparstat command that was executed.
    returned: always
    type: str

rc:
    description: The return code from the lparstat command.
    returned: always
    type: int

stdout:
    description: The standard output returned by the lparstat command.
    returned: always
    type: str

stderr:
    description: The standard error (if any) returned by the command.
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


def validate_mutual_exclusiveness(module):

    '''
    Check the lparstat option mutually exclusiveness
    arguments:
        module  (dict): The Ansible module
    '''

    results = {}
    if module.params['config_info']:
        allowed_with_i = ['wpar_output', 'service_info', 'energy_tuning', 'timestamp', 'recorded_output', 'concatenated_output']
        for key, value in module.params.items():
            if value and key not in allowed_with_i + ['config_info']:
                module.fail_json(msg=f"'-i' can only be used with {allowed_with_i}")

    elif module.params['wpar_output']:
        allowed_with_W = ['config_info', 'service_info', 'energy_tuning', 'timestamp', 'recorded_output', 'concatenated_output']
        for key, value in module.params.items():
            if value and key not in allowed_with_W + ['wpar_output']:
                module.fail_json(msg=f"'-W' can only be used with {allowed_with_W}")

    elif module.params['service_info']:
        allowed_with_s = ['config_info', 'wpar_output', 'energy_tuning', 'timestamp', 'recorded_output', 'concatenated_output']
        for key, value in module.params.items():
            if value and key not in allowed_with_s + ['service_info']:
                module.fail_json(msg=f"'-s' can only be used with {allowed_with_s}")

    elif module.params['energy_tuning']:
        allowed_with_P = ['config_info', 'wpar_output', 'service_info', 'timestamp', 'recorded_output', 'concatenated_output']
        for key, value in module.params.items():
            if value and key not in allowed_with_P + ['energy_tuning']:
                module.fail_json(msg=f"'-P' can only be used with {allowed_with_P}")

    if module.params['utilization']:
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['utilization']:
                module.fail_json(msg=f"'-u' can only be used with {allowed_option}")

    if module.params['security_mode']:
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output', 'interval', 'count']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['security_mode']:
                module.fail_json(msg=f"'-x' can only be used with {allowed_option}")

    if module.params['detailed_cpu_stats']:
        if module.params['interval'] and not module.params['count']:
            module.fail_json(msg=" 'count' is mandatory when you use the '-d' flag with an 'interval' ")
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output', 'interval', 'count']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['detailed_cpu_stats']:
                module.fail_json(msg=f"'-d' can only be used with {allowed_option}")

    if module.params['hypervisor_stat_short']:
        if module.params['interval'] and not module.params['count']:
            module.fail_json(msg=" 'count' is mandatory when you use the '-h' flag with an 'interval' ")
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output', 'interval', 'count']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['hypervisor_stat_short']:
                module.fail_json(msg=f"'-h' can only be used with {allowed_option}")

    if module.params['hypervisor_stat_long']:
        if module.params['interval'] and not module.params['count']:
            module.fail_json(msg=" 'count' is mandatory when you use the '-H' flag with an 'interval' ")
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output', 'interval', 'count']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['hypervisor_stat_long']:
                module.fail_json(msg=f"'-H' can only be used with {allowed_option}")

    if module.params['export_xml'] or module.params['output_file']:
        if module.params['output_file'] and not module.params['export_xml']:
            results['msg'] = "The 'output_file' option must be used with 'export_xml'"
            module.fail_json(**results)
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output', 'output_file']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['export_xml']:
                module.fail_json(msg=f"'-X' can only be used with {allowed_option}")

    if module.params['spurr_based_metrics'] or module.params['spurr_based_metrics_wide']:
        if module.params['spurr_based_metrics_wide'] and not module.params['spurr_based_metrics']:
            results['msg'] = "The 'spurr_based_metrics_wide' option must be used with 'spurr_based_metrics'."
            module.fail_json(**results)
        if module.params['interval'] and not module.params['count']:
            module.fail_json(msg=" 'count' is mandatory when you use the '-E ' flag with an 'interval' ")
        allowed_option = ['timestamp', 'recorded_output', 'concatenated_output', 'spurr_based_metrics_wide', 'interval', 'count']
        for key, value in module.params.items():
            if value and key not in allowed_option + ['spurr_based_metrics']:
                module.fail_json(msg=f"'-E' can only be used with {allowed_option}")

    if (
        module.params['memory_stats']
        or module.params['io_memory_pools']
        or module.params['page_coalescing']
        or module.params['reset_once']
        or module.params['reset_each_interval']
    ):

        if module.params['io_memory_pools'] and not module.params['memory_stats']:
            results['msg'] = "The 'io_memory_pools' option must be used with 'memory_stats'."
            module.fail_json(**results)
        if module.params['page_coalescing'] and not module.params['memory_stats']:
            results['msg'] = "The 'page_coalescing' option must be used with 'memory_stats'."
            module.fail_json(**results)

        if module.params['page_coalescing_wide']:
            if not (module.params['memory_stats'] and module.params['page_coalescing']):
                results['msg'] = "The '-w' options can only be used with both '-m' and '-p'."
                module.fail_json(**results)

        if module.params['reset_once'] or module.params['reset_each_interval']:
            if not (module.params['memory_stats'] and module.params['io_memory_pools']):
                results['msg'] = "The '-r' and '-R' options can only be used with both '-m' and '-e'."
                module.fail_json(**results)

        allowed_option = ['recorded_output', 'concatenated_output', 'io_memory_pools', 'page_coalescing', 'page_coalescing_wide', 'reset_once',
                          'reset_each_interval', 'interval', 'count', 'timestamp']
        if module.params['interval'] and not module.params['count']:
            module.fail_json(msg=" 'count' is mandatory when you use the '-m' flag with an 'interval' ")
        for key, value in module.params.items():
            if value and key not in allowed_option + ['memory_stats']:
                module.fail_json(msg=f"'-m' can only be used with {allowed_option}")

    if module.params['count'] and not module.params['interval']:
        results['msg'] = "The 'count' option must be used with 'interval'."
        module.fail_json(**results)


def build_lparstat_command(module):

    '''
    Build the lparstat command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created lparstat command
    '''

    cmd = ['lparstat']

    if module.params['config_info']:
        cmd.append('-i')
        if module.params['wpar_output']:
            cmd.append('-W')
        if module.params['service_info']:
            cmd.append('-s')
        if module.params['energy_tuning']:
            cmd.append('-P')

    elif module.params['wpar_output']:
        cmd.append('-W')
    elif module.params['service_info']:
        cmd.append('-s')
    elif module.params['energy_tuning']:
        cmd.append('-P')
    elif module.params['micro_partition']:
        cmd.append('-G')
    elif module.params['utilization']:
        cmd.append('-u')
    elif module.params['security_mode']:
        cmd.append('-x')
    elif module.params['detailed_cpu_stats']:
        cmd.append('-d')
    elif module.params['memory_stats']:
        cmd.append('-m')
        if module.params['io_memory_pools']:
            cmd.append('-e')
            if module.params['reset_each_interval']:
                cmd.append('-R')
            elif module.params['reset_once']:
                cmd.append('-r')
        if module.params['page_coalescing']:
            cmd.append('-p')
            if module.params['page_coalescing_wide']:
                cmd.append('-w')
    elif module.params['hypervisor_stat_short']:
        cmd.append('-h')
    elif module.params['hypervisor_stat_long']:
        cmd.append('-H')
    elif module.params['export_xml']:
        cmd.append('-X')
        if module.params['output_file']:
            if os.path.exists(module.params['output_file']):
                os.remove(module.params['output_file'])
            cmd.extend(['-o', module.params['output_file']])
    elif module.params['spurr_based_metrics']:
        cmd.append('-E')
        if module.params['spurr_based_metrics_wide']:
            cmd.append('-w')
    if module.params['timestamp']:
        cmd.append('-t')
    if module.params['interval'] is not None:
        cmd.append(str(module.params['interval']))
        if module.params['count'] is not None:
            cmd.append(str(module.params['count']))

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            config_info=dict(type='bool', default=False),
            wpar_output=dict(type='bool', default=False),
            service_info=dict(type='bool', default=False),
            energy_tuning=dict(type='bool', default=False),
            micro_partition=dict(type='bool', default=False),
            utilization=dict(type='bool', default=False),
            security_mode=dict(type='bool', default=False),
            detailed_cpu_stats=dict(type='bool', default=False),
            memory_stats=dict(type='bool', default=False),
            io_memory_pools=dict(type='bool', default=False),
            reset_once=dict(type='bool', default=False),
            reset_each_interval=dict(type='bool', default=False),
            page_coalescing=dict(type='bool', default=False),
            page_coalescing_wide=dict(type='bool', default=False),
            hypervisor_stat_long=dict(type='bool', default=False),
            hypervisor_stat_short=dict(type='bool', default=False),
            export_xml=dict(type='bool', default=False),
            output_file=dict(type='str'),
            spurr_based_metrics=dict(type='bool', default=False),
            spurr_based_metrics_wide=dict(type='bool', default=False),
            timestamp=dict(type='bool', default=False),
            interval=dict(type='int'),
            count=dict(type='int'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True),
        ),
        supports_check_mode=False
    )

    result = dict(changed=False, msg='', cmd='', rc=0, stdout='', stderr='')

    validate_mutual_exclusiveness(module)

    cmd = build_lparstat_command(module)
    result['cmd'] = cmd

    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)

    result = {
        'changed': False,
        'cmd': cmd,
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr
    }

    if rc != 0:
        result['msg'] = f"lparstat command failing with command  {cmd}"
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
                    module.fail_json(msg=f"Failed to create directory {output_dir}: {str(e)}", **result)

            mode = 'a' if should_concat else 'w'  # 'a' = append, 'w' = overwrite
            with open(output_file, mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] = f"lparstat executed successfully with command '{cmd}' and Output written to {output_file}"
        else:
            result['changed'] = False
            result['msg'] = f"lparstat executed successfully with command '{cmd}'"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
