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
module: backupios
short_description: Creates an installable image of the root volume group
description:
- Creates a backup of the Virtual I/O Server and places it onto a file system.
version_added: '2.9'
requirements:
- VIOS >= 2.2.2.00
- Python >= 2.7
options:
  file:
    description:
    - Specifies the directory on which the image is to be stored.
    - When I(mksysb=yes), specifies the file name.
    type: str
    required: true
  mksysb:
    description:
    - Creates an mksysb image.
    type: bool
    default: no
  nopack:
    description:
    - When I(mksysb=yes), specifies the list of files to exclude from being packed.
    type: list
    elements: str
  savevgstruct:
    description:
    - Specifies whether to save the volume groups structure of user-defined volume
      groups as part of the C(backupios) process.
    type: bool
    default: yes
  savemedialib:
    description:
    - Specifies whether to save the contents of the media repository as part of
      the C(backupios) process.
    type: bool
    default: yes
notes:
  - The C(backupios) module backs up only the volume group structures
    that are activated. The structures of volumes groups that are
    deactivated are not backed up.
'''

EXAMPLES = r'''
- name: Generate a backup to /home/padmin/backup directory
  backupios:
    file: /home/padmin/backup

- name: Generate an mksysb backup to /home/padmin/backup.mksysb
  backupios:
    file: /home/padmin/backup.mksysb
    mksysb: yes
    savemedialib: no
    savevgstruct: no
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
        argument_spec=dict(
            file=dict(required=True, type='str'),
            mksysb=dict(type='bool', default=False),
            nopack=dict(type='list', elements='str'),
            savevgstruct=dict(type='bool', default=True),
            savemedialib=dict(type='bool', default=True),
        )
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    get_ioslevel(module)

    cmd = [ioscli_cmd, 'backupios']

    params = module.params

    cmd += ['-file', params['file']]
    if params['mksysb']:
        cmd += ['-mksysb']
        if params['nopack']:
            # Create exclude file from exclude list
            with open('/etc/exclude_packing.rootvg', 'w+') as f:
                f.writelines(params['nopack'])
            cmd += ['-nopack']
    if not params['savevgstruct']:
        cmd += ['-nosvg']
    if not params['savemedialib']:
        cmd += ['-nomedialib']

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True
    results['msg'] = 'backupios completed successfully'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
