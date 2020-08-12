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
module: updateios
short_description: Updates the Virtual I/O Server to the latest maintenance level
description:
- Install fixes or update the VIOS to the latest maintenance level.
version_added: '2.9'
requirements:
- VIOS >= 2.2.5.0
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform on the VIOS.
    - C(update) to perform an update to the VIOS.
    - C(commit) to commit all uncommitted updates to the VIOS.
    - C(cleanup) to remove all incomplete pieces of the previous installation.
    - C(install) to install a file set from the VIOS installation media.
    - C(remove) to remove the specified file sets from the system.
    - C(list) to list the file sets on the VIOS installation media that are
      available to be installed.
    type: str
    choices: [ update, commit, cleanup, install, remove, list ]
    required: true
  device:
    description:
    - Specifies the device or directory containing the images to install.
    - When I(action=list) or I(action=install), only C(/dev/cdX) can be specified.
    type: str
  force:
    description:
    - Forces all uncommitted updates to be committed before applying the new updates.
    type: bool
    default: no
  filesets:
    description:
    - When I(action=install), specifies the name of the file set to be installed
      from the VIOS installation media.
    - When I(action=remove), specifies the list of file sets to uninstall.
    type: list
    elements: str
  install_new:
    description:
    - Installs new and supported file sets onto the VIOS.
    type: bool
    default: no
  accept_licenses:
    description:
    - Specifies that you agree to the required software license agreements for
      software to be installed.
    type: bool
    default: no
notes:
  - A fix pack or service pack cannot be applied if the VIOS partition is part
    of a shared storage pool and the cluster node state is UP.
'''

EXAMPLES = r'''
- name: Update the VIOS to the latest level, where the updates are
        located on the mounted file system /home/padmin/update
  updateios:
    action: update
    device: /home/padmin/update

- name: Update the VIOS to the latest level, when previous levels are not committed
  updateios:
    action: update
    force: yes
    device: /home/padmin/update

- name: Cleanup partially installed updates
  updateios:
    action: cleanup

- name: Commit the installed updates
  updateios:
    action: commit

- name: List the available file sets on the VIOS installation media
  updateios:
    action: list
    device: /dev/cd0

- name: Install a file set from the VIOS installation media
  updateios:
    action: install
    filesets: ILMT-TAD4D-agent
    device: /dev/cd1
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
stdout:
    description: The standard output
    returned: always
    type: str
stderr:
    description: The standard error
    returned: always
    type: str
ioslevel:
    description: The latest installed maintenance level of the system
    returned: always
    type: str
    sample: '3.1.0.00'
'''

import re

from ansible.module_utils.basic import AnsibleModule


ioscli_cmd = 'ioscli'


def get_ioslevel(module):
    """
    Return the latest installed maintenance level of the system.
    """
    global results

    cmd = [ioscli_cmd, 'ioslevel']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Could not retrieve ioslevel, return code {0}.'.format(ret)
        module.fail_json(**results)

    ioslevel = stdout.split('\n')[0]

    if not re.match(r"^\d+.\d+.\d+.\d+$", ioslevel):
        results['msg'] = 'Could not parse ioslevel output {0}.'.format(ioslevel)
        module.fail_json(**results)

    results['ioslevel'] = ioslevel

    return ioslevel


def main():
    global results

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(required=True, type='str',
                        choices=['update', 'commit', 'cleanup', 'install', 'remove', 'list']),
            device=dict(type='str'),
            accept_licenses=dict(type='bool', default=False),
            force=dict(type='bool', default=False),
            filesets=dict(type='list', elements='str'),
            install_new=dict(type='bool', default=False),
        ),
        required_if=[
            ['action', 'update', ['device']],
            ['action', 'list', ['device']],
            ['action', 'install', ['device', 'filesets']],
            ['action', 'remove', ['filesets']],
        ]
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    get_ioslevel(module)

    cmd = [ioscli_cmd, 'updateios']

    action = module.params['action']
    params = module.params

    if action == 'update':
        cmd += ['-dev', params['device']]
        if params['force']:
            cmd += ['-f']
        if params['install_new']:
            cmd += ['-install']
        if params['accept_licenses']:
            cmd += ['-accept']
    elif action == 'install':
        cmd += ['-dev', params['device']]
        cmd += ['-fs']
        cmd += params['filesets']
    elif action == 'remove':
        cmd += ['-remove']
        cmd += params['filesets']
    elif action == 'commit':
        cmd += ['-commit']
    elif action == 'cleanup':
        cmd += ['-cleanup']
    elif action == 'list':
        cmd += ['-list', '-dev', params['device']]

    # Note: updateios is an interactive command.
    # We use the same mechanism nim uses (c_updateios.sh) to implement preview mode.
    response = 'n'
    if not module.check_mode:
        response = 'y\ny'

    # Do we want to implement a manage_ssp flag like in nim_updateios
    # that would call clstartstop to remove the VIOS from the cluster
    # before applying the update?
    # It is probably better to manage this within playbooks/roles.

    shcmd = "eval echo '{0}' | {1}".format(response, ' '.join(cmd))
    ret, stdout, stderr = module.run_command(shcmd, use_unsafe_shell=True)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(shcmd, ret)
        module.fail_json(**results)

    if action != 'list' and not module.check_mode:
        results['changed'] = True

    results['msg'] = 'updateios completed successfully'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
