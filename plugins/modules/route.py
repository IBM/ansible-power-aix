#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024 IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import ipaddress
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: route
author:
- AIX Development Team (@vivekpandeyibm)
short_description: Manage routes on IBM AIX systems.
description:
- This module allows adding, deleting, flushing, or listing routes in IBM AIX systems.
- Supports advanced options such as `-f`, `-n`, `-C`, `-v`, and WPAR-specific routing.
version_added: '2.0.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- Root user is required.
options:
  action:
    description:
    - Specifies the action to perform: add, delete, flush, or change.
    - C(add) Adds a route.
    - C(flush) Removes all routes.
    - C(delete) Deletes a specific route.
    - C(change) Changes aspects of a route (such as its gateway).
    - C(get) Lookup and display the route for a destination.
    - C(set) Set the policy and weight attributes of a route.
    type: str
    choices: ['add', 'delete', 'flush', 'change', 'get', 'set']
    required: true
  destination:
    description:
    - The destination network or host IP address.
    type: str
    required: false
  gateway:
    description:
    - The gateway IP address for routing.
    type: str
    required: false
  netmask:
    description:
    - Specifies the network mask for the destination.
    type: str
    required: false
  prefixlen:
    description:
    - Specifies the prefix length of the destination.
    type: int
    required: false
  arguments:
    description:
    - Additional route-specific arguments like `-weight`, `-policy`, etc., to be appended after the gateway.
    type: list
    elements: str
    required: false
  flush:
    description:
    - Corresponds to the `-f` flag. Purges all entries in the routing table that are not associated with network interfaces.
    type: bool
    required: false
  numeric:
    description:
    - Corresponds to the `-n` flag. Displays host and network names numerically rather than symbolically.
    type: bool
    required: false
  ioctl_preference:
    description:
    - Corresponds to the `-C` flag. Specifies preference for ioctl calls over routing messages for adding and removing routes.
    type: bool
    required: false
  verbose:
    description:
    - Corresponds to the `-v` flag. Prints additional details.
    type: bool
    required: false
  flags:
    description:
    - List of additional flags for the route command such as `net` or`host`.
    type: str
    elements: str
    required: false
  family:
    description:
    - Specifies the address family, such as `-inet` or `-inet6`.
    type: str
    required: false
notes:
  - Refer to IBM documentation for more details on route commands at
    U(https://www.ibm.com/docs/en/aix/7.3?topic=r-route-command).
'''

EXAMPLES = r'''
- name: Add a route to 192.168.1.0/24 via 192.168.0.1
  aix_route_command:
    action: add
    destination: 192.168.1.0
    netmask: 255.255.255.0
    gateway: 192.168.0.1

- name: Delete a route to 192.168.1.0/24
  aix_route_command:
    action: delete
    destination: 192.168.1.0
    netmask: 255.255.255.0

- name: Flush all routes
  aix_route_command:
    action: flush
    flush: true

- name: Add a route with verbose mode
  aix_route_command:
    action: add
    destination: 10.0.0.0
    prefixlen: 24
    gateway: 192.168.1.1
    verbose: true

- name: Add a route with weight and policy
  aix_route_command:
    action: add
    destination: 192.158.2.2
    gateway: 192.158.2.5
    arguments:
      - -weight
      - "5"
      - -policy
      - "4"

- name: Add a route for a specific destination_ip
  aix_route_command:
    action: add
    destination: 192.168.1.0
    netmask: 255.255.255.0
    gateway: 192.168.0.1
'''

RETURN = r'''
msg:
    description: Execution message.
    returned: always
    type: str
    sample: "Route added successfully."
rc:
    description: Return code of the route command.
    returned: always
    type: int
stdout:
    description: Standard output of the route command.
    returned: when applicable
    type: str
stderr:
    description: Standard error of the route command.
    returned: when applicable
    type: str
cmd:
    description: The exact command run by the module.
    returned: always
    type: str
'''


def normalize_route_entry(module, route_entry):
    """
    Normalize the route_entry to a valid CIDR(Classless Inter-Domain Routing) format.
    Converts entries like '10.12/16' to '10.12.0.0/16'.

    Arguments:
    - module (AnsibleModule): The Ansible module instance.
    - route_entry (str): The raw route entry string.

    Returns:
    - str: Normalized route entry in valid CIDR format.
    """
    if "/" in route_entry:  # Check if it looks like a CIDR entry
        try:
            base, prefix = route_entry.split("/")
            base_parts = base.split(".")
            while len(base_parts) < 4:  # Pad missing octets with '.0'
                base_parts.append("0")
            normalized_entry = ".".join(base_parts) + f"/{prefix}"
            # Validate the normalized entry
            ipaddress.ip_network(normalized_entry, strict=False)
            return normalized_entry
        except Exception as e:
            module.fail_json(
                changed=False,
                msg=f"Failed to normalize route_entry '{route_entry}': {e}")
    return route_entry  # Return as is if no '/' is present


def parse_routing_table(module):
    """
    Parses the routing table from the `netstat -rn` command output.

    Arguments:
    - module (AnsibleModule): The Ansible module instance.

    Returns:
    - list: A list of network entries as `ipaddress.IPv4Network` objects.
    """
    check_cmd = "netstat -rn"
    rc, stdout, stderr = module.run_command(check_cmd)
    if rc != 0:
        module.fail_json(msg="Failed to fetch routing table.", rc=rc, stdout=stdout, stderr=stderr)

    routing_table = []
    gateways = []
    lines = stdout.splitlines()

    for line in lines:
        columns = line.split()
        if not columns:
            continue
        # Inspect raw entry
        route_entry = columns[0]
        gateway_entry = columns[1]
        try:
            if "/" in route_entry:  # CIDR format
                normalized_entry = normalize_route_entry(module, route_entry)
                network = ipaddress.ip_network(normalized_entry, strict=False)
                routing_table.append(network)
                gateways.append(gateway_entry)
            elif "." in route_entry:  # IP format, assume /32
                network = ipaddress.ip_network(f"{route_entry}/32", strict=False)
                routing_table.append(network)
                gateways.append(gateway_entry)
        except Exception as e:
            module.warn(f"Invalid route entry skipped: {route_entry}, Error: {str(e)}")
            continue

    return routing_table, gateways


def check_destination_in_routing_table(module, destination):
    """
    Checks if the given destination exists in the routing table.

    Arguments:
    - module (AnsibleModule): The Ansible module instance.
    - destination (str): The destination to check.

    Returns:
    - bool: True if the destination matches an entry in the routing table, False otherwise.
    """
    netmask = module.params['netmask']
    prefixlen = module.params['prefixlen']
    flags = module.params['flags']
    gateway = module.params['gateway']
    action = module.params['action']

    if flags == 'net':  # check if network flag is set
        if netmask:
            input_mask = netmask
        elif prefixlen:
            input_mask = prefixlen
        else:
            input_mask = 32
        destination = calculate_network_address(module, destination, input_mask)  # Call the function for network address
    try:
        destination_ip = ipaddress.ip_address(destination)
    except Exception as e:
        module.fail_json(msg=f"Invalid destination IP address: {destination}, Error: {str(e)}")
    routing_table, gateways = parse_routing_table(module)
    # Check if the destination IP and gateway matches any network in the table
    for network, gateway_get in zip(routing_table, gateways):
        if action in ['set', 'change']:  # Skip gateway validation for 'set' or 'change'
            if destination_ip == network.network_address:
                return True
            elif destination_ip in network:
                return True
        else:  # Perform full validation for other actions
            if destination_ip == network.network_address and gateway == gateway_get:
                return True
            elif destination_ip in network and gateway == gateway_get:
                return True
    return False


def calculate_network_address(module, destination_ip, mask_or_prefix):
    """
    Calculates the network address given a destination IP and either a netmask or a prefix length.

    Parameters:
       - module (AnsibleModule): The Ansible module instance.
       - destination_ip (str): The destination IP address (e.g., '192.168.14.12').
       - mask_or_prefix (str|int): The netmask (e.g., '255.255.255.0') or prefix length (e.g., 24).

    Returns:
        str: The calculated network address (e.g., '192.168.14.0').
        None: If the calculation fails.
    """
    try:
        # Determine if the input is a netmask or a prefix length
        if '.' in str(mask_or_prefix):
            # Combine IP with netmask and calculate network address
            network = ipaddress.ip_network(f"{destination_ip}/{mask_or_prefix}", strict=False)
        else:
            # Treat as prefix length and calculate network address
            network = ipaddress.ip_network(f"{destination_ip}/{int(mask_or_prefix)}", strict=False)
        return str(network.network_address)

    except Exception as e:
        # Handle any unexpected errors
        module.fail_json(msg=f"The destination '{destination_ip}' is not currect, Error: {e}.")


def build_route_command(module):
    """
    Constructs the `route` command based on the input parameters.

    Parameters:
       - module (AnsibleModule): The Ansible module instance.
    Returns:
        str: The calculated command to run.
    """
    cmd = ['route']

    # Add flags before the command
    if module.params['flush']:
        cmd.append('-f')
        return ' '.join(cmd)
    if module.params['numeric']:
        cmd.append('-n')
    if module.params['ioctl_preference']:
        cmd.append('-C')
    elif module.params['verbose']:
        cmd.append('-v')

    # Add the command type
    action = module.params['action']
    cmd.append(action)

    # Add optional parameters
    destination = module.params['destination']
    gateway = module.params['gateway']
    netmask = module.params['netmask']
    prefixlen = module.params['prefixlen']
    arguments = module.params['arguments'] or []
    flags = module.params['flags']
    family = module.params['family']

    if family:
        cmd.append(family)

    if destination:
        if flags == 'net':  # check if network flag is set
            cmd.append('-net')
            if action in ['delete', 'set', 'change']:
                if netmask:
                    input_mask = netmask
                elif prefixlen:
                    input_mask = prefixlen
                else:
                    input_mask = 32
                network_destination_ip = calculate_network_address(module, destination, input_mask)  # Call the function for network address
                cmd.append(network_destination_ip)
            else:
                cmd.append(destination)

        elif flags == 'host':  # check if host flag is set
            cmd.append('-host')
            cmd.append(destination)
    else:
        destination = 0
        cmd.append(destination)

    if prefixlen:
        cmd.extend(['-prefixlen', str(prefixlen)])

    if netmask:
        cmd.extend(['-netmask', netmask])

    if gateway:
        cmd.append(gateway)
    if arguments:
        for key, value in arguments.items():
            cmd.extend([f"-{key}", value])

    return ' '.join(cmd)


def run_route_command(module):
    """
    Runs the constructed `route` command.

    Parameters:
       - module (AnsibleModule): The Ansible module instance.
    Returns:
        str: The Output of command run (rc ,stdout,stderr,cmd).
    """

    destination = module.params.get('destination')
    action = module.params['action']
    if destination:
        result = check_destination_in_routing_table(module, destination)
        if result and module.params['action'] in ['add']:
            module.exit_json(
                msg=f"The destination '{destination}' is  found in the routing table during action {action}.",
                changed=False
            )
        elif not result and module.params['action'] in ['delete', 'change', 'flush', 'get', 'set']:
            module.exit_json(
                msg=f"The destination '{destination}' is not found in the routing table during action {action}.",
                changed=False
            )
    cmd = build_route_command(module)
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        module.fail_json(msg=f"Route command '{action}' Failed to execute with error {stderr}.", cmd=cmd, rc=rc, stdout=stdout, stderr=stderr)
    return rc, stdout.strip(), stderr.strip(), cmd


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', choices=['add', 'delete', 'change', 'flush', 'get', 'set'], required=True),
            destination=dict(type='str', required=False),
            gateway=dict(type='str', required=False),
            netmask=dict(type='str', required=False),
            prefixlen=dict(type='int', required=False),
            arguments=dict(type='dict'),
            flush=dict(type='bool', required=False),
            numeric=dict(type='bool', required=False),
            ioctl_preference=dict(type='bool', required=False),
            verbose=dict(type='bool', required=False),
            flags=dict(type='str', default='host', choices=['host', 'net']),
            family=dict(type='str', required=False)
        ),
        supports_check_mode=True
    )

    result = dict(
        changed=False,
        cmd='',
        rc=0,
        stdout='',
        stderr='',
        msg=''
    )

    try:
        action = module.params['action']
        rc, stdout, stderr, cmd = run_route_command(module)
        is_changed = False if action == "get" else True
        result.update(
            cmd=cmd,
            rc=rc,
            stdout=stdout,
            stderr=stderr,
            changed=is_changed,
            msg="Route command executed successfully."
        )
    except Exception as e:
        result['msg'] = str(e)
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
