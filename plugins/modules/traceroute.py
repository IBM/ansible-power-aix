#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026 IBM
# GNU General Public License v3.0+

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: traceroute
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Trace the route to a network host using AIX traceroute
description:
  - This module traces the route that IP packets take to reach a destination host on AIX systems.
  - It launches UDP probe packets with incrementing time-to-live (TTL) values and listens for ICMP responses from gateways.
  - The module supports all major traceroute flags available on AIX and allows recording output to a file.
  - It is intended for network testing, measurement, and management purposes.
version_added: "2.3.0"
requirements:
  - AIX >= 7.1
  - Root or appropriate network privileges may be required for certain operations

options:
  host:
    description:
    - The destination host name or IP address to trace the route to.
    - This is the target host for which the network path will be determined.
    - Can be specified as a hostname (e.g., google.com) or IP address (e.g., 8.8.8.8).
    type: str
    required: true

  max_ttl:
    description:
    - Maximum number of hops (time-to-live) to trace (C(-m) flag).
    - Determines how many network hops the traceroute will attempt before stopping.
    - Each hop represents a router or gateway in the path to the destination.
    - Default is 30 hops if not specified.
    type: int

  numeric:
    description:
    - Display hop addresses numerically only, without performing DNS lookups (C(-n) flag).
    - When enabled, speeds up the traceroute by skipping reverse DNS resolution.
    - Useful when DNS is slow or unavailable, or when you only need IP addresses.
    type: bool
    default: false

  port:
    description:
    - Base UDP port number to use for probe packets (C(-p) flag).
    - The traceroute command uses sequential port numbers starting from this base value.
    - Each probe increments the port number to help identify responses.
    - Default is 33434 if not specified.
    type: int

  queries:
    description:
    - Number of probe packets to send per hop (C(-q) flag).
    - Determines how many probes are sent at each TTL level to measure round-trip time.
    - More queries provide better statistics but increase network load and execution time.
    - Default is 3 probes per hop if not specified.
    type: int

  bypass_routing:
    description:
    - Bypass the normal routing tables and send probe packets directly to a host on an attached network (C(-r) flag).
    - This option forces packets to be sent directly without consulting the routing table.
    - Only works for hosts on directly attached networks (same subnet).
    - Returns an error if the specified host is not on a directly attached network.
    - Useful for testing local network connectivity or debugging routing issues.
    type: bool
    default: false

  debug:
    description:
    - Enable socket-level debugging for detailed network operation information (C(-d) flag).
    - Provides low-level debugging output about socket operations and packet handling.
    - Useful for troubleshooting network issues or understanding packet flow.
    - Generates verbose output that may be difficult to interpret without networking knowledge.
    type: bool
    default: false

  source_address:
    description:
    - Use the specified IP address as the source address in outgoing probe packets (C(-s) flag).
    - Forces the source IP address to be different from the default interface address.
    - Useful on hosts with multiple network interfaces to control which interface is used.
    - The specified IP address must be configured on one of the machine's network interfaces.
    - Returns an error if the IP address is not found on any local interface.
    type: str

  tos:
    description:
    - Set the Type-Of-Service (TOS) value in probe packets (C(-t) flag).
    - TOS is a field in the IP header that indicates the desired quality of service.
    - Valid range is 0 to 255 (decimal integer).
    - Different TOS values may result in different routing paths through the network.
    - Common useful values include 16 (minimize delay), 8 (maximize throughput), 4 (maximize reliability), and 2 (minimize cost).
    - Default is 0 (normal service) if not specified.
    type: int

  verbose:
    description:
    - Enable verbose output to receive all ICMP packets, not just TIME_EXCEEDED and PORT_UNREACHABLE (C(-v) flag).
    - Displays additional information about ICMP packets received during the trace.
    - Useful for detailed network diagnostics and understanding all responses from intermediate hops.
    - May produce significantly more output than the standard traceroute.
    type: bool
    default: false

  wait_time:
    description:
    - Time in seconds to wait for a response to each probe packet (C(-w) flag).
    - Determines how long the traceroute waits before considering a probe as timed out.
    - Longer wait times may be necessary for slow or congested networks.
    - Shorter wait times speed up the traceroute but may miss legitimate responses.
    - Default is 3 seconds if not specified.
    type: int

  packet_size:
    description:
    - Size of the probe packet in bytes.
    - Allows testing with different packet sizes to identify MTU issues or size-dependent routing.
    - Larger packets may be fragmented or dropped on networks with smaller MTU values.
    - Default packet size is determined by the MTU of the outgoing network interface if not specified.
    - Typical values range from 40 bytes (minimum) to 1500 bytes (standard Ethernet MTU).
    type: int

  recorded_output:
    description:
    - File path where the traceroute command output will be recorded.
    - If specified, both stdout and stderr from the traceroute command are written to this file.
    - The directory path must exist or will be created automatically.
    - Useful for logging, auditing, or later analysis of network paths.
    type: str

  concatenated_output:
    description:
    - Controls whether to append to or overwrite the output file specified in recorded_output.
    - When true, new output is appended to the existing file content.
    - When false, the file is overwritten with new output.
    - Only used when recorded_output parameter is specified.
    - Useful for collecting multiple traceroute results in a single log file.
    type: bool
    default: false

notes:
  - You can refer to the IBM documentation for additional information on the traceroute command documentation
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=t-traceroute-command)

'''

EXAMPLES = r'''
- name: Basic traceroute
  ibm.power_aix.traceroute:
    host: google.com

- name: Traceroute with numeric output and max hops
  ibm.power_aix.traceroute:
    host: 8.8.8.8
    numeric: true
    max_ttl: 20

- name: Record traceroute output
  ibm.power_aix.traceroute:
    host: example.com
    recorded_output: /tmp/traceroute.log
    concatenated_output: true

- name: Traceroute using specific interface
  ibm.power_aix.traceroute:
    host: 192.168.1.1
    verbose: true

- name: Traceroute with custom packet size and wait time
  ibm.power_aix.traceroute:
    host: example.com
    packet_size: 512
    wait_time: 5
    queries: 5
'''

RETURN = r'''
msg:
  description: Execution message.
  returned: always
  type: str
rc:
  description: Return code.
  returned: always
  type: int
stdout:
  description: Standard output.
  returned: always
  type: str
stderr:
  description: Standard error.
  returned: always
  type: str
cmd:
  description: Executed traceroute command.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
import os


def validate_parameters(module):

    """
    validate some of the parameters for boundry condition.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        NA
    """

    # Validate TOS (0-255)
    if module.params['tos'] is not None:
        if module.params['tos'] < 0 or module.params['tos'] > 255:
            module.fail_json(msg="tos must be between 0 and 255")
    # Validate max_ttl ( > 1)
    if module.params['max_ttl'] is not None:
        if module.params['max_ttl'] < 2:
            module.fail_json(msg="max ttl must be greater than 1")

    # Validate wait_time ( > 1)
    if module.params['wait_time'] is not None:
        if module.params['wait_time'] < 2:
            module.fail_json(msg="wait_time must be greater than 1")

    # Validate positive integers
    positive_int_params = ['max_ttl', 'port', 'queries', 'wait_time', 'packet_size']
    for param in positive_int_params:
        if module.params[param] is not None and module.params[param] <= 0:
            module.fail_json(msg=f"{param} must be a positive integer")


def build_traceroute_command(module):

    """
    Build the traceroute command with all flags.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        cmd      : Final command to execute
    """
    cmd = ['traceroute']

    # Boolean flags
    if module.params['debug']:
        cmd.append('-d')
    if module.params['numeric']:
        cmd.append('-n')
    if module.params['bypass_routing']:
        cmd.append('-r')
    if module.params['verbose']:
        cmd.append('-v')

    # Flags with values
    if module.params['max_ttl'] is not None:
        cmd.extend(['-m', str(module.params['max_ttl'])])
    if module.params['port'] is not None:
        cmd.extend(['-p', str(module.params['port'])])
    if module.params['queries'] is not None:
        cmd.extend(['-q', str(module.params['queries'])])

    if module.params['source_address']:
        cmd.extend(['-s', module.params['source_address']])
    if module.params['tos'] is not None:
        cmd.extend(['-t', str(module.params['tos'])])
    if module.params['wait_time'] is not None:
        cmd.extend(['-w', str(module.params['wait_time'])])

    # Host (required)
    cmd.append(module.params['host'])

    # Packet size (optional, comes after host)
    if module.params['packet_size'] is not None:
        cmd.append(str(module.params['packet_size']))

    return cmd


def write_output_to_file(module, output, result):

    """
    Write command output to file

    Arguments:
        module (AnsibleModule): The Ansible module instance
        output (str): The command output to write to file
        result (dict): The result dictionary containing command execution details

    Note:
        Exits with fail_json in case of error

    Return:
        None
    """

    output_file = module.params['recorded_output']
    output_dir = os.path.dirname(output_file)

    # Create directory if it doesn't exist
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, mode=0o755, exist_ok=True)
        except OSError as e:
            module.fail_json(
                msg=f"Failed to create directory {output_dir}: {str(e)}",
                **result
            )

    # Write output to file
    mode = 'a' if module.params['concatenated_output'] else 'w'
    try:
        with open(output_file, mode) as f:
            f.write(output)
            if not output.endswith('\n'):
                f.write('\n')
    except IOError as e:
        module.fail_json(
            msg=f"Failed to write to file {output_file}: {str(e)}",
            **result
        )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            host=dict(type='str', required=True),
            max_ttl=dict(type='int'),
            numeric=dict(type='bool', default=False),
            port=dict(type='int'),
            queries=dict(type='int'),
            bypass_routing=dict(type='bool', default=False),
            debug=dict(type='bool', default=False),
            source_address=dict(type='str'),
            tos=dict(type='int'),
            verbose=dict(type='bool', default=False),
            wait_time=dict(type='int'),
            packet_size=dict(type='int'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', default=False),
        ),
        supports_check_mode=False
    )

    # Validate parameters
    validate_parameters(module)

    result = dict(changed=False, rc=0, stdout='', stderr='', msg='', cmd='')

    # Build and execute command
    cmd = build_traceroute_command(module)
    result['cmd'] = " ".join(cmd)

    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=False)
    result.update({'rc': rc, 'stdout': stdout, 'stderr': stderr})

    if rc != 0:
        result['msg'] = 'traceroute execution failed'
        module.fail_json(**result)

    network_unreachable_error = "Cannot reach the destination network"

    # Check for network failure when rc==0
    if rc == 0 and network_unreachable_error in stderr:
        result['changed'] = False
        if module.params['bypass_routing']:
            result['msg'] = f"traceroute failed: Cannot reach the destination network for host '{module.params['host']}'"
        module.fail_json(**result)

    # Write output to file if requested
    if module.params['recorded_output']:
        write_output_to_file(module, stdout, result)
        result['changed'] = True
        result['msg'] = f"traceroute executed successfully for host '{module.params['host']}' and output written to {module.params['recorded_output']}"
    else:
        result['msg'] = f"traceroute executed successfully for host '{module.params['host']}'"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
