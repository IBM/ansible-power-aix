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
- Syahrul Aiman Shaharuddin (@psyntium)
module: emgr_list
short_description: List interim fixes on the system
description:
- Uses the interim fix manager (emgr) to list all interim fixes on the system.
version_added: '0.0.1'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorization: B(aix.system.install)'
options:
  ifix_label:
    description:
    - Specifies the interim fix label that is the unique key that binds all of the different
      database objects.
    - Can be used if I(action) has one of following values C(list), C(commit), C(remove), C(check),
      C(mount), C(unmount), C(remove).
    - Required if I(action=remove) and I(force=True).
    - Mutually exclusive with I(ifix_number), I(ifix_vuid), I(list_file).
    type: str
  ifix_number:
    description:
    - Specifies the interim fix identification number (ID).
    - The interim fix ID is simply the order number in which the interim fix is listed in the
      interim fix database. Using this option may be convenient if you are performing operations on
      interim fixes based on interim fix listings.
    - Can be used if I(action) has one of following values C(list), C(remove), C(check), C(mount),
      C(unmount), C(remove).
    - Mutually exclusive with I(ifix_label), I(ifix_vuid), I(list_file).
    type: str
  ifix_vuid:
    description:
    - Specifies the interim fix Virtually Unique ID (VUID) that can be used to differentiate
      packages with the same interim fix label.
    - Can be used if I(action) has one of following values C(list), C(remove), C(check), C(mount),
      C(unmount).
    - Mutually exclusive with I(ifix_label), I(ifix_number), I(list_file).
    type: str
  alternate_dir:
    description:
    - Specifies an alternative directory path for installation.
    - Can be used if I(action) has one of following values C(list), C(install), C(remove), C(check),
      C(mount), C(unmount), C(view_package).
    type: path
  extend_fs:
    description:
    - Attempts to resize any file systems where there is insufficient space.
    type: bool
    default: no
  verbose:
    description:
    - Specifies the verbosity level. The verbosity increases with the value.
    - Can be used if I(action) has one of following values C(list), C(check), C(view_package).
    type: int
    choices: [ 1, 2, 3 ]
notes:
  - System administrators or users with the aix.system.install authorization can run the emgr
    command on a multi-level secure (MLS) system.
  - Ifix data, saved files, and temporary files are accessible only by the root user.
  - You can refer to the IBM documentation for additional information on the emgr command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/e_commands/emgr.html).
'''

EXAMPLES = r'''
- name: List all interim fixes on the system
  emgr_list:
- name: Show IJ22714s1a interim fix on the system
  emgr_list:
    ifix_label: IJ22714s1a
'''

RETURN = r'''
count:
    description: Number of ifixes found
    returned: always
    type: int
    sample: 5
ifixes:
    description: List of ifixes on the system
    returned: always
    type: array
    sample: [{
      "abstract": "Multithreaded apps core dump / hang",
      "id": "1",
      "install_time": "10/16/22 01:44:18",
      "label": "IJ30808s1a",
      "state": "*Q*",
      "state_desc": "REBOOT REQUIRED",
      "updated_by": ""
    }]
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Command 'emgr -l' successful.",
stdout:
    description: The standard output.
    returned: always
    type: str
    sample: '
        ID  STATE LABEL      INSTALL TIME      UPDATED BY ABSTRACT\n
        === ===== ========== ================= ========== ======================================\n
        1    S    IJ20785s2a 04/30/20 11:03:46            tcpdump CVEs fixed                    \n
        2    S    IJ17065m3a 04/30/20 11:03:57            IJ17065 is for AIX 7.2 TL03           \n
        3   *Q*   IJ09625s2a 04/30/20 11:04:14            IJ09624 7.2.3.2                       \n
        4    S    IJ11550s0a 04/30/20 11:04:34            Xorg Security Vulnerability fix       \n
        \n
        STATE codes:\n
         S = STABLE\n
         M = MOUNTED\n
         U = UNMOUNTED\n
         Q = REBOOT REQUIRED\n
         B = BROKEN\n
         I = INSTALLING\n
         R = REMOVING\n
         T = TESTED\n
         P = PATCHED\n
         N = NOT PATCHED\n
         SP = STABLE + PATCHED\n
         SN = STABLE + NOT PATCHED\n
         QP = BOOT IMAGE MODIFIED + PATCHED\n
         QN = BOOT IMAGE MODIFIED + NOT PATCHED\n
         RQ = REMOVING + REBOOT REQUIRED'
stderr:
    description: The standard error.
    returned: always
    type: str
    sample: 'There is no efix data on this system.'
'''

import re

from ansible.module_utils.basic import AnsibleModule

module = None
results = None

def param_one_of(one_of_list, required=True, exclusive=True):
    """
    Check at parameter of one_of_list is defined in module.params dictionary.
    arguments:
        one_of_list (list) list of parameter to check
        required    (bool) at least one parameter has to be defined.
        exclusive   (bool) only one parameter can be defined.
    note:
        Ansible might have this embedded in some version: require_if 4th parameter.
        Exits with fail_json in case of error
    """
    global module
    global results

    count = 0
    for param in one_of_list:
        if module.params[param] is not None and module.params[param]:
            count += 1
            break
    if count == 0 and required:
        results['msg'] = 'Missing parameter: action is {0} but one of the following is missing: '.format(module.params['action'])
        results['msg'] += ','.join(one_of_list)
        module.fail_json(**results)
    if count > 1 and exclusive:
        results['msg'] = 'Invalid parameter: action is {0} supports only one of the following: '.format(module.params['action'])
        results['msg'] += ','.join(one_of_list)
        module.fail_json(**results)


def main():
    global module
    global results

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            ifix_label=dict(type='str'),
            ifix_number=dict(type='str'),
            ifix_vuid=dict(type='str'),
            alternate_dir=dict(type='path'),
            extend_fs=dict(type='bool', default=False),
            verbose=dict(type='int', choices=[1, 2, 3]),
        ),
        required_if=[],
        mutually_exclusive=[['ifix_label', 'ifix_number', 'ifix_vuid']],
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        ifixes=[],
        count=0
    )

    cmd = ['emgr']

    # Usage: emgr -l [-L <label> | -n <ifix number> | -u <VUID>] [-v{1-3}X] [-a <path>]
    param_one_of(['ifix_label', 'ifix_number', 'ifix_vuid'], required=False)
    cmd += ['-l']
    if module.params['ifix_label']:
        cmd += ['-L', module.params['ifix_label']]
    elif module.params['ifix_number']:
        cmd += ['-n', module.params['ifix_number']]
    elif module.params['ifix_vuid']:
        cmd += ['-u', module.params['ifix_vuid']]
    if module.params['verbose'] is not None:
        cmd += ['-v', '{0}'.format(module.params['verbose'])]
    if module.params['extend_fs']:
        cmd += ['-X']
    if module.params['alternate_dir']:
        cmd += ['-a', module.params['alternate_dir']]

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
      # Ifix was already installed(0645-065).
      # Ifix with label to remove is not there (0645-066).
      # Ifix with VUUID to remove is not there (0645-082).
      # Ifix with ID number to remove is not there (0645-081).
      pattern = "0645-065|0645-066|0645-081|0645-082|There is no efix data on this system"
      found = re.search(pattern, stderr)
      results['changed'] = False
      
      results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
      module.fail_json(**results)

    results['msg'] = 'Command \'{0}\' successful.'.format(' '.join(cmd))
        
    if stdout == "":
      module.exit_json(**results)
    stdout_lines = stdout.splitlines()

    states_map = {
        "S": "STABLE",
        "M": "MOUNTED",
        "U": "UNMOUNTED",
        "Q": "REBOOT REQUIRED",
        "B": "BROKEN",
        "I": "INSTALLING",
        "R": "REMOVING",
        "T": "TESTED",
        "P": "PATCHED",
        "N": "NOT PATCHED",
        "SP": "STABLE + PATCHED",
        "SN": "STABLE + NOT PATCHED",
        "QP": "BOOT IMAGE MODIFIED + PATCHED",
        "QN": "BOOT IMAGE MODIFIED + NOT PATCHED",
        "RQ": "REMOVING + REBOOT REQUIRED"
    }

    categories_line = stdout_lines[1]   # extract categories
    # equal sign strings to count width of column
    eqs = stdout_lines[2].split(" ")

    eqs_len = len(eqs)                  # length of string

    # count width of each column
    for i in range(eqs_len):
        eqs[i] = len(eqs[i])

    # count number of ifixes
    ifix_count = 0
    for i in range(2, len(stdout_lines)):
        if stdout_lines[i] == "":
            ifix_count = i - 3

    # set size of categories and ifix_list arrays
    categories = [None] * eqs_len
    ifix_list = [None] * ifix_count

    # extract and transform categories
    start = 0
    for i in range(eqs_len):
        end = start + eqs[i]
        categories[i] = categories_line[start:end].strip(
        ).lower().replace(" ", "_")
        start = end+1

    for i in range(ifix_count):
        line_count = 3 + i
        ifix_str = stdout_lines[line_count]
        ifix_item = {}

        # extract ifix item details
        start = 0
        for j in range(eqs_len):
            end = start + eqs[j]
            ifix_item[categories[j]] = ifix_str[start:end].strip()
            start = end+1

        ifix_item["state_desc"] = states_map[ifix_item["state"].replace("*","")]

        ifix_list[i] = ifix_item

    results["ifixes"] = ifix_list
    results["count"] = len(ifix_list)

    module.exit_json(**results)

if __name__ == '__main__':
    main()
