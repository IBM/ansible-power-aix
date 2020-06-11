#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: mktcpip
short_description: Sets the required values for starting TCP/IP on a host
description:
- This module sets the required minimal values required for using TCP/IP on a host machine.
- These values are written to the configuration database.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  hostname:
    description:
    - Sets the name of the host.
    type: str
    required: true
  address:
    description:
    - Sets the Internet address of the host.
    type: str
    required: true
  interface:
    description:
    - Specifies a particular network interface.
    type: str
    required: true
  netmask:
    description:
    - Specifies the mask the gateway should use in determining the appropriate subnetwork for routing.
    type: str
  gateway:
    description:
    - Adds the default gateway address to the routing table.
    type: str
  nameserver:
    description:
    - Specifies the Internet address of the name server the host uses for name resolution.
    type: str
  domain:
    description:
    - Specifies the domain name of the name server the host should use for name resolution.
    type: str
  start_daemons:
    description:
    - Starts the TCP/IP daemons.
    type: bool
    default: no
'''

EXAMPLES = r'''
- name: Set the required values for starting TCP/IP
  mktcpip:
    hostname: fred.austin.century.com
    address: 192.9.200.4
    interface: en0
    nameserver: 192.9.200.1
    domain: austin.century.com
    start_daemons: yes
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Command 'mktcpip -h quimby01.aus.stglabs.ibm.com -a 9.3.149.150 -i en1' successful."
stdout:
    description: The standard output.
    returned: always
    type: str
    sample: 'en1\n
             quimby01.aus.stglabs.ibm.com\n
             inet0 changed\n
             en1 changed'
stderr:
    description: The standard error.
    returned: always
    type: str
    sample: 'en1\n
             x.x.x.x is an invalid address.\n
             /usr/sbin/mktcpip: Problem with command: hostent, return code = 1\n'
'''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            hostname=dict(required=True, type='str'),
            address=dict(required=True, type='str'),
            interface=dict(required=True, type='str'),
            netmask=dict(type='str'),
            gateway=dict(type='str'),
            nameserver=dict(type='str'),
            domain=dict(type='str'),
            start_daemons=dict(type='bool', default=False),
        ),
        required_together=[
            ["nameserver", "domain"],
        ]
    )

    result = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    hostname = module.params['hostname']
    address = module.params['address']
    interface = module.params['interface']

    cmd = ['mktcpip', '-h', hostname, '-a', address, '-i', interface]
    netmask = module.params['netmask']
    if netmask:
        cmd += ['-m', netmask]
    gateway = module.params['gateway']
    if gateway:
        cmd += ['-g', gateway]
    nameserver = module.params['nameserver']
    if nameserver:
        cmd += ['-n', nameserver]
        domain = module.params['domain']
        if domain:
            cmd += ['-d', domain]
    if module.params['start_daemons']:
        cmd += ['-s']

    rc, stdout, stderr = module.run_command(cmd)

    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.fail_json(**result)

    result['msg'] = 'Command \'{0}\' successful.'.format(' '.join(cmd))
    result['changed'] = True
    module.exit_json(**result)


if __name__ == '__main__':
    main()
