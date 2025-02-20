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
author: AIX Development Team (@nitismis)
module: lku
short_description: Performs live kernel update
description:
- The module uses geninstall -k command for live kernel update.
- Currently in the module, support for LKU is supported only through PowerVC setup.
version_added: '1.9.0'
requirements:
- AIX >= 7.2
- Python >= 3.6
- 'Privilage user with authrization:B(aix.system.install)'
options:
  PVC_name:
    description:
    - Hostname of the PowerVC managing target node.
    type: str
  PVC_password:
    description:
    - Password of the PowerVC
    type: str
  PVC_user:
    description:
    - Username for the PowerVC
    type: str
  directory:
    description:
    - Path of the directory where fixes and filesets are present.
    type: str
    default: None
  filesets_fixes:
    description:
    - Space separated names of filesets and interim fixes to be installed from provided I(directory).
    - If I(directory) is provided then this attribute is required.
    - If you want to install all the updates and interim fixes then give input as all.
    - If you want to install only updates and not interim fixes then give input as update_all.
    type: str
    default: None
'''

EXAMPLES = r'''
- name: Perform LKU on target node using PowerVC
  ibm.power_aix.lku:
    PVC_name: powervchostname
    PVC_password: passw0rd123
    PVC_user: powervcuser
    directory: path/to/directory
    filesets_fixes: space separated names of filesets and interim fixes OR all OR update_all
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: When the command is executed.
    type: int
stdout':
    description: The standard output.
    returned: If the command failed.
    type: str
stderr':
    description: The standard error.
    returned: If the command failed.
    type: str
'''

result = None


def authenticate_PVC(module):
    """
    Authenticate the PowerVC for LKU operation
    arguments:
        module(dict): The Ansible module object
    return:
        None
    """

    pvc_name = module.params['PVC_name']
    pvc_passwd = module.params['PVC_password']
    pvc_user = module.params['PVC_user']

    cmd = f'pvcauth -a {pvc_name} -u {pvc_user} -p {pvc_passwd}'

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = f"\nFailed to authenticate PowerVC {pvc_name}. Please check the credentials."
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)


def perform_lku(module):
    """
    Performs the LKU operation on target node.
    arguments:
        module(dict): The Ansible module object
    return:
        None
    """

    cmd = "geninstall -k"

    directory = module.params['directory']
    filesets_fixes = module.params['filesets_fixes']

    if directory and filesets_fixes:
        cmd += f" -d {directory} {filesets_fixes}"

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if rc != 0:
        msg = "\nFailed to perform Live kernel update. Check the error in results."
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)


def main():
    """
    Main function
    """

    global result

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            PVC_name=dict(type='str', required=True),
            PVC_password=dict(type='str', required=True),
            PVC_user=dict(type='str', required=True),
            directory=dict(type='str', required=False, default=None),
            filesets_fixes=dict(type='str', required=False, default=None),
        ),
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    directory = module.params['directory']
    filesets_fixes = module.params['filesets_fixes']
    if directory and not filesets_fixes:
        msg = 'filesets_fixes not provided. Provide space separated fileset or interim fixes names.'
        msg += '\nIf you want to install all the updates and interim fixes provide \'all\'.'
        msg += '\nIf you want to install only updates but not interim fixes provide \'update_all\'.'
        module.fail_json(msg=msg)

    authenticate_PVC(module)

    perform_lku(module)

    result['msg'] = "Live Kernel Update operation has been performed successfully."

    module.exit_json(**result)


if __name__ == '__main__':
    main()
