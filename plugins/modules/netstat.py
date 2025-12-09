#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025 IBM
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: netstat
author:
    - AIX Development Team (@vivekpandeyibm)
short_description: Collect network statistics using netstat on AIX
description:
  - This module allows you to gather network statistics using the AIX netstat command.
  - Supports all reporting flags, mutual exclusiveness, and output recording.
version_added: "2.1.0"
requirements:
    - AIX >= 7.1
options:
  numeric_network_address:
    description:
      - Display network addresses as numbers (-n).
      - When this flag is not specified, the netstat command interprets addresses where possible and displays them symbolically.
      - This flag can be used with any of the display formats.
    type: bool
    default: False
  pcb_address:
    description:
      - Shows the address of any protocol control blocks associated with the sockets (-A).
      - This flag acts with the default display and is used for debugging purposes.
    type: bool
    default: False
  all_sockets_state:
    description:
      - Show state of all sockets (-a).
      - If this flag is not specified, sockets that are used by server processes that are not bound to an interface are not shown.
    type: bool
    default: False
  socket_options:
    description:
      - Show detailed socket info with -a (-o).
    type: bool
    default: False
  routing_table:
    description:
      - Show routing tables (-r).
      - When used with the '-s' flag, the '-r' flag shows routing statistics
    type: bool
    default: False
  show_route_details:
    description:
      - Show routing tables with costs including the user-configured and current costs of each route (-C).
      - It also shows the weight and policy information associated with each route
    type: bool
    default: False
  packet_counts:
    description:
      - Shows the number of packets received, transmitted, and dropped in the communications subsystem (-D).
    type: bool
    default: False
  display_configured_interfaces:
    description:
      - Shows the state of all configured interfaces (-i).
    type: bool
    default: False
  interface_name:
    description:
      - Shows the state of the configured interface specified by the 'interface_name' variable. (-I).
    type: str
  protocol:
    description:
      - Shows statistics about the value specified for the 'protocol' variable (-p).
    type: str
  memory_stats:
    description:
      - Shows statistics recorded by the memory management routines. (-m).
    type: bool
    default: False
  mbuf_pool_stats:
    description:
      - Shows network memory's mbuf cluster pool statistics. (-M).
    type: bool
    default: False
  protocol_stats:
    description:
      - Shows statistics for each protocol. (-s).
    type: bool
    default: False
  concise_protocol_stats:
    description:
      - Displays all the non-zero protocol statistics and provides a concise display (-ss).
    type: bool
    default: False
  domain_sockets:
    description:
      - Displays information about domain sockets. (-u).
    type: bool
    default: False
  display_adapter_statistics:
    description:
      - Shows statistics for CDLI-based communications adapters. (-v).
      - This flag causes the netstat command to run the statistics commands for the netstat, tokstat, and fddistat commands
    type: bool
    default: False
  virtual_interface_and_multicast:
    description:
      - Shows Virtual Interface Table and Multicast Forwarding Cache information (-g).
      - If used in conjunction with the '-s' flag, it will show the multicast routing information.
    type: bool
    default: False
  ras_artifacts:
    description:
      - Displays all reliability, availability, and serviceability (RAS) artifacts for the specified protocol (-K).
    type: str
  ras_file:
    description:
      - Output file for RAS artifacts with '-K' (-F).
    type: str
  ras_suppress_nonzero:
    description:
      - Suppresses the printing of non-zero counter values when you use the -K flag to display the RAS artifacts for a specific protocol(-b).
    type: bool
    default: False
  interactive_mode:
    description:
      - Starts the user interactive mode. (-w).
    type: bool
    default: False
  clear_stats:
    description:
      - Zc	Clear network buffer cache statistics.
      - Zi	Clear interface statistics.
      - Zm	Clear network memory allocator statistics.
      - Zs	Clear protocol statistics
    type: str
    choices: ["c", "i", "m", "s"]
  address_family:
    description:
      - Limits reports of statistics or address control blocks to those items specified by the AddressFamily variable (-f).
    type: str
    choices: ["inet", "inet6", "unix"]
  interval:
    description:
      - Specifies the interval (in seconds) between lparstat readings.
      - Used to gather repeated samples over time.
    type: int
  count:
    description:
      - Number of reports to generate at the specified interval.
      - Must be used together with the interval option.
    type: int
   recorded_output:
    description:
      - Folder path to command output in machine .
    type: str
  concatenated_output:
    description:
      - Controls whether the output of the vmstat command is appended to the output file or is overwrited.
      - If set to true, output will be appended to the file.
      - If set to false, the file will be overwritten with fresh output.
    type: bool
    required: true
notes:
  - You can refer to the IBM documentation for additional information on the lparstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=l-netstat-command).
'''

EXAMPLES = r'''
- name: Show all sockets
  ibm.power_aix.netstat:
    all_sockets_state: true

- name: Show routing table with costs
  ibm.power_aix.netstat:
    routing_table: true

- name: Show RAS artifacts for TCP to file
  ibm.power_aix.netstat:
    ras_artifacts: tcp
    ras_file: /tmp/tcp_ras.log
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'netstat executed  SUCCESSFULLY '
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import os


def validate_mutual_exclusiveness(module):
    """
    Ensure valid combinations of netstat flags.
    """
    results = {}

    if module.params['count'] is None:
        for f in ['numeric_network_address', 'pcb_address', 'all_sockets_state', 'routing_table', 'show_route_details', 'display_configured_interfaces',
                  'interface_name', 'memory_stats', 'mbuf_pool_stats', 'protocol_stats', 'concise_protocol_stats', 'domain_sockets',
                  'display_adapter_statistics', 'address_family', 'protocol']:
            if module.params[f]:
                results['msg'] = f"' count ' is mandatory with '{f}' option."
                module.fail_json(**results)
    if module.params['count'] is not None:
        for f in ['virtual_interface_and_multicast', 'cache_stats', 'packet_counts']:
            if module.params[f]:
                results['msg'] = f"' count ' cannot be combined with '{f}' option."
                module.fail_json(**results)

    # clear stats cannot combine with display flags
    if module.params['clear_stats']:
        disallowed = ['routing_table', 'show_route_details', 'cache_stats', 'packet_counts',
                      'display_configured_interfaces', 'interface_name', 'protocol',
                      'memory_stats', 'mbuf_pool_stats', 'protocol_stats',
                      'concise_protocol_stats', 'domain_sockets',
                      'display_adapter_statistics', 'virtual_interface_and_multicast',
                      'numeric_network_address', 'pcb_address', 'all_sockets_state',
                      'socket_options', 'ras_artifacts', 'ras_file', 'ras_suppress_nonzero',
                      'interactive_mode', 'address_family', 'interval', 'count']
        for d in disallowed:
            if module.params[d]:
                module.fail_json(msg=f"'-Z{module.params['clear_stats']}' cannot be combined with option '{d}'.")
    # interval requires count
    if module.params['interval'] and not module.params['count']:
        module.fail_json(msg="When using 'interval', you must specify 'count'.")

    # count requires interval
    if module.params['count'] and not module.params['interval']:
        module.fail_json(msg="The 'count' option must be used with 'interval'.")


def build_netstat_command(module):
    '''
    Build the netstat command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created netstat command
    '''

    cmd = ['/bin/netstat']

    if module.params['numeric_network_address']:
        cmd.append('-n')
    if module.params['pcb_address']:
        cmd.append('-A')
    if module.params['all_sockets_state']:
        cmd.append('-a')
        if module.params['socket_options']:
            cmd.append('-o')
    if module.params['display_configured_interfaces']:
        cmd.append('-i')
        if module.params['interface_name']:
            cmd.extend(['-I', module.params['interface_name']])
    elif module.params['show_route_details']:
        cmd.append('-C')
    elif module.params['routing_table']:
        cmd.append('-r')

    # To Display the Contents of a Network Data Structure
    if module.params['memory_stats']:
        cmd.append('-m')
    elif module.params['mbuf_pool_stats']:
        cmd.append('-M')
    elif module.params['display_adapter_statistics']:
        cmd.append('-v')
    elif module.params['domain_sockets']:
        cmd.append('-u')

    if module.params['concise_protocol_stats']:
        cmd.append('-ss')
    elif module.params['protocol_stats']:
        cmd.append('-s')

    # To Display the Virtual Interface Table and Multicast Forwarding Cache
    if module.params['virtual_interface_and_multicast']:
        cmd.append('-g')

    # To Display the Network Buffer Cache Statistics
    if module.params['cache_stats']:
        cmd.append('-c')

    # To Display the Packet Counts Throughout the Communications Subsystem
    if module.params['packet_counts']:
        cmd.append('-D')

    # To display artifacts for a specific protocol
    if module.params['ras_artifacts']:
        cmd.extend(['-K', module.params['ras_artifacts']])
        if module.params['ras_file']:
            if os.path.exists(module.params['ras_file']):
                os.remove(module.params['ras_file'])
            cmd.extend(['-F', module.params['ras_file']])
        if module.params['ras_suppress_nonzero']:
            cmd.append('-b')
        if module.params['interactive_mode']:
            cmd.append('-w')
    # To Clear the Associated Statistics
    if module.params['clear_stats']:
        cmd.append(f"-Z{module.params['clear_stats']}")

    # Independent modifiers (can stack with others)

    if module.params['address_family']:
        cmd.extend(['-f', module.params['address_family']])
    if module.params['protocol']:
        cmd.extend(['-p', module.params['protocol']])
    # Interval/count logic
    if module.params['interval'] is not None:
        cmd.append(str(module.params['interval']))
        if module.params['count'] is not None:
            count_value = int(module.params['count']) + 2
            cmd.extend(['| head -n ', str(count_value)])
    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            numeric_network_address=dict(type='bool', default=False),
            pcb_address=dict(type='bool', default=False),
            all_sockets_state=dict(type='bool', default=False),
            socket_options=dict(type='bool', default=False),
            routing_table=dict(type='bool', default=False),
            show_route_details=dict(type='bool', default=False),
            packet_counts=dict(type='bool', default=False),
            display_configured_interfaces=dict(type='bool', default=False),
            interface_name=dict(type='str'),
            protocol=dict(type='str'),
            memory_stats=dict(type='bool', default=False),
            mbuf_pool_stats=dict(type='bool', default=False),
            protocol_stats=dict(type='bool', default=False),
            concise_protocol_stats=dict(type='bool', default=False),
            domain_sockets=dict(type='bool', default=False),
            display_adapter_statistics=dict(type='bool', default=False),
            virtual_interface_and_multicast=dict(type='bool', default=False),
            ras_artifacts=dict(type='str'),
            ras_file=dict(type='str'),
            ras_suppress_nonzero=dict(type='bool', default=False),
            interactive_mode=dict(type='bool', default=False),
            clear_stats=dict(type='str', choices=["c", "i", "m", "s"]),
            address_family=dict(type='str', choices=["inet", "inet6", "unix"]),
            interval=dict(type='int'),
            count=dict(type='int'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True),
            cache_stats=dict(type='bool', default=False),
        ),
        supports_check_mode=False
    )

    result = dict(changed=False, cmd='', rc=0, stdout='', stderr='', msg='')

    validate_mutual_exclusiveness(module)
    cmd = build_netstat_command(module)
    result['cmd'] = " ".join(cmd)
    new_cmd = " ".join(cmd)
    rc, stdout, stderr = module.run_command(new_cmd, use_unsafe_shell=True)
    result.update({'rc': rc, 'stdout': stdout, 'stderr': stderr})

    if rc != 0:
        result['msg'] = f"netstat failed with {cmd}"
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
            with open(module.params['recorded_output'], mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] += f"netstat executed successfully with command '{cmd}' and Output written to {output_file}"
        else:
            result['msg'] += f"netstat executed successfully with command '{cmd}'"
        module.exit_json(**result)


if __name__ == '__main__':
    main()
