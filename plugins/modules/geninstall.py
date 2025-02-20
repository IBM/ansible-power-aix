#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: geninstall
short_description: Generic installer for various packaging formats.
description:
- A generic installer that installs software products of various packaging formats.
- For example, installp, RPM, SI, and ISMP.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorization: B(aix.system.install)'
options:
  action:
    description:
    - Controls what is performed.
    - C(install) performs an install of the specified software.
    - C(uninstall) performs an uninstall of the specified software.
    - C(list) lists the contents of the media.
    type: str
    choices: [ install, uninstall, list ]
    default: install
  device:
    description:
    - Specifies the device or directory that contains the images to install.
    - The geninstall command searches for the images in the following paths
      /mount_point/installp/ppc (installp package),
      /mount_point/RPMS/ppc (RPM package),
      /mount_point/emgr/ppc (Interim fix packages for AIX),
      /mount_point/ISMP/ppc (ISMP packages for AIX).
    - If the paths do not exist, it searches in the base directory of the specific device. If the
      image names are not preceded by a prefix that indicates the image type, it identifies a type
      for the image.
    - If the paths exist and the image is not found in any path, and if the image does not contain
      any prefix, the image is treated as an RPM-formatted image.
    type: str
  install_list:
    description:
    - List of products to install
    - C(all) installs all products
    - C(update_all) updates all products
    type: list
    elements: str
    default: []
  force:
    description:
    - Force the operation allowing to reinstall a package that is already installed, or to install
      a package that is older than the currently installed version.
    type: bool
    default: no
  agree_licenses:
    description:
    - Agrees to required software license agreements for software to be installed.
    type: bool
    default: no
  installp_flags:
    description:
    - Specifies the installp flags to use when calling the installp command.
    type: str
    default: ''
notes:
  - You can refer to the IBM documentation for additional information on the geninstall command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/g_commands/geninstall.html)
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

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Invalid parameter: install_list cannot be empty'
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: When the command is executed.
    type: int
stdout:
    description: The standard output of the command.
    returned: always
    type: str
    sample: 'bin:bin:::J:::::::bin Product::::\nsbin:sbin:::J:::::::sbin Product::::'
stderr:
    description: The standard error of the command.
    returned: always
    type: str
    sample: '0503-105 geninstall: The device or directory: /dev/cd0 does not exist.'
'''


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(type='str', default='install', choices=['install', 'uninstall', 'list']),
            device=dict(type='str'),
            force=dict(type='bool', default=False),
            installp_flags=dict(type='str', default=''),
            agree_licenses=dict(type='bool', default=False),
            install_list=dict(type='list', elements='str', default=[]),
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
        cmd='',
        stdout='',
        stderr='',
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
            result['msg'] = 'Invalid parameter: install_list cannot be empty'
            module.fail_json(**result)
        cmd += install_list
        result['changed'] = True

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = f'Command {cmd} failed with return code {rc}.'
        module.fail_json(**result)

    result['msg'] = f'Command {cmd} successful.'
    module.exit_json(**result)


if __name__ == '__main__':
    main()
