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
short_description: Collect network statistics using the AIX netstat command
description:
  - This module gathers detailed network statistics using the AIX C(netstat) command.
  - Supports all reporting flags, mutual exclusiveness validation, repeated sampling,
    and recording the command output to a file.
version_added: "2.2.0"
requirements:
  - AIX >= 7.1

options:
  numeric_network_address:
    description:
      - Display network addresses numerically using C(-n).
      - When omitted, symbolic hostnames may appear.
    type: bool
    default: false

  pcb_address:
    description:
      - Show protocol control block (PCB) addresses using C(-A).
    type: bool
    default: false

  all_sockets_state:
    description:
      - Display the state of all sockets using C(-a).
    type: bool
    default: false

  socket_options:
    description:
      - Show detailed socket options along with C(-a) using C(-o).
    type: bool
    default: false

  routing_table:
    description:
      - Display routing tables using C(-r).
    type: bool
    default: false

  show_route_details:
    description:
      - Display routing details including metrics and policy information using C(-C).
    type: bool
    default: false

  packet_counts:
    description:
      - Show communications subsystem packet counts using C(-D).
    type: bool
    default: false

  display_configured_interfaces:
    description:
      - Display all configured interfaces using C(-i).
    type: bool
    default: false

  interface_name:
    description:
      - Display information for a specific interface using C(-I <interface>).
    type: str

  protocol:
    description:
      - Display statistics for the given protocol using C(-p).
    type: str

  memory_stats:
    description:
      - Display memory management statistics using C(-m).
    type: bool
    default: false

  mbuf_pool_stats:
    description:
      - Display mbuf cluster pool statistics using C(-M).
    type: bool
    default: false

  protocol_stats:
    description:
      - Display protocol statistics using C(-s).
    type: bool
    default: false

  concise_protocol_stats:
    description:
      - Display only non-zero protocol statistics using C(-ss).
    type: bool
    default: false

  domain_sockets:
    description:
      - Display information about domain sockets using C(-u).
    type: bool
    default: false

  display_adapter_statistics:
    description:
      - Display adapter statistics for CDLI adapters using C(-v).
    type: bool
    default: false

  virtual_interface_and_multicast:
    description:
      - Display virtual interface table and multicast forwarding cache using C(-g).
    type: bool
    default: false

  ras_artifacts:
    description:
      - Display reliability, availability, and serviceability (RAS) artifacts using C(-K <protocol>).
    type: str

  ras_file:
    description:
      - File path to store RAS output when using C(-F).
    type: str

  ras_suppress_nonzero:
    description:
      - Suppress non-zero counters in RAS output using C(-b).
    type: bool
    default: false

  interactive_mode:
    description:
      - Start interactive mode using C(-w).
    type: bool
    default: false

  clear_stats:
    description:
      - Clear statistics using C(-Z).
      - C(c) clears network buffer statistics.
      - C(i) clears interface statistics.
      - C(m) clears memory allocator statistics.
      - C(s) clears protocol statistics.
    type: str
    choices: ["c", "i", "m", "s"]

  address_family:
    description:
      - Limit reports to a specific address family using C(-f).
    type: str
    choices: ["inet", "inet6", "unix"]

  interval:
    description:
      - Time in seconds between repeated netstat samples.
    type: int

  count:
    description:
      - Number of samples to collect along with interval.
    type: int

  recorded_output:
    description:
      - File path to record command output.
    type: str

  concatenated_output:
    description:
      - If true, append output to file; if false, overwrite file.
    type: bool
    required: true

  cache_stats:
    description:
      - Display network buffer cache statistics using C(-c).
    type: bool
    default: false

notes:
  - You can refer to the IBM documentation for additional information on the netstat command at
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
                    result['msg'] = f"Failed to create directory {output_dir}: {str(e)}"
                    module.fail_json(**result)
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
