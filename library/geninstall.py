#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright:: 2020- IBM, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
######################################################################

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'IBM, Inc'
}

DOCUMENTATION = r'''
---
author:
- AIX Development Team
module: geninstall
short_description: Generic installer for various packaging formats
description:
- A generic installer that installs software products of various packaging formats.
- For example, installp, RPM, SI, and ISMP.
version_added: '2.9'
requirements: [ AIX ]
options:
  device:
    description:
    - The name of the device or directory.
    type: str
  install_list:
    description:
    - List of products to install
    - C(all) installs all products
    - C(update_all) updates all products
    type: list
    default: []
  force:
    description:
    - Forces action.
    type: bool
    default: no
  action:
    description:
    - Controls what is performed.
    - C(install) performs an install of the specified software.
    - C(uninstall) performs an uninstall of the specified software.
    - C(list) lists the contents of the media.
    type: str
    choices: [ install, uninstall, list ]
    default: install
  agree_licenses:
    description:
    - Agrees to required software license agreements for software to be installed.
    type: bool
    default: no
  installp_flags:
    description:
    - Specifies the installp flags to use when calling the installp command.
    type: str
'''

EXAMPLES = r'''
- name: Install all the products on a CD media
  geninstall:
    device: /dev/cd0
    install_list: all

- name: Install an interim fix located in /images/emgr/ppc directory
  geninstall:
    device: /images
    install_list: IV12345.160101.epkg.Z
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(type='str', default='install', choices=['install', 'uninstall', 'list']),
            device=dict(type='str'),
            debug=dict(type='bool', default=False),
            force=dict(type='bool', default=False),
            installp_flags=dict(type='str', default=''),
            agree_licenses=dict(type='bool', default=False),
            install_list=dict(type='list', default=[]),
        ),
        required_if=[
            ['action', 'list', ['device']],
            ['action', 'install', ['device', 'install_list']],
            ['action', 'uninstall', ['install_list']],
        ]
    )

    result = dict(
        changed=False,
        msg='',
    )

    action = module.params['action']
    device = module.params['device']
    installp_flags = module.params['installp_flags']
    install_list = module.params['install_list']

    cmd = ['geninstall']
    if action == 'list':
        cmd += ['-L', '-d', device]
    elif action == 'uninstall':
        cmd += ['-u']
    else:
        cmd += ['-d', device]
        if installp_flags:
            cmd += ['-I', installp_flags]
    if module.check_mode:
        cmd += ['-p']
    if module.params['force']:
        cmd += ['-F']
    if module.params['agree_licenses']:
        cmd += ['-Y']

    # Finally, append the install list
    if action != 'list':
        # For install and uninstall, check that install list is not empty
        if not install_list:
            result['msg'] = 'install_list cannot be empty'
            module.fail_json(**result)
        cmd += install_list

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        result['msg'] = stderr
        module.fail_json(**result)

    result['msg'] = stdout
    module.exit_json(**result)


if __name__ == '__main__':
    main()
