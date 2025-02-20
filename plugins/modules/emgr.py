#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import os
import re
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: emgr
short_description: System interim fixes management.
description:
- Uses the interim fix manager (emgr) to install packages created with the epkg command and maintain
  the database containing interim fix information.
- It can perform the following operations install, commit, check, mount, unmount, remove, list
  interim fix (ifix) and view package locks.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorization: B(aix.system.install)'
options:
  action:
    description:
    - Controls what action is performed.
    - C(install) performs an interim fix package installation.
    - C(commit) performs a commit operation on specified interim fix.
    - C(check) performs a check operation on installed interim fix.
    - C(mount) mounts specified interim fix that have been mount-installed.
    - C(unmount) unmounts specified interim fix that have been mount-installed.
    - C(remove) performs an uninstall of the specified interim fix.
    - C(view_package) displays all packages that are locked, their installer, and the locking
      label or labels.
    - C(display_ifix) displays the contents and topology of specified interim fix. This option is
      useful with C(verbose).
    - C(list) lists interim fix data.
    type: str
    choices: [ install, commit, check, mount, unmount, remove, view_package, display_ifix, list ]
    default: list
  ifix_package:
    description:
    - Specifies the path of the interim fix package file.
    - If I(from_epkg=yes), then the file must be created with the epkg command and must end with
      the 16-bit compression extension '.Z'.
      Otherwise the file is manage as a concurrent update ifix package file.
    - Can be used if I(action) has one of following values C(install), C(display_ifix).
    - Mutually exclusive with I(list_file).
    type: path
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
  list_file:
    description:
    - Specifies a file that contains a list of package locations if I(action=install)
      or a list of interim fix labels for the remove, mount, unmount and check operations.
    - The file must have one item per line, blank lines or starting with # character are ignored.
    - Can be used if I(action) has one of following values C(install), C(remove), C(check),
      C(mount), C(unmount), C(display_ifix).
    - Mutually exclusive with I(ifix_label), I(ifix_number), I(ifix_vuid), I(ifix_package).
    type: path
  package:
    description:
    - Specifies the package to view.
    - Can be used if I(action=view_package)
    type: str
  alternate_dir:
    description:
    - Specifies an alternative directory path for installation.
    - Can be used if I(action) has one of following values C(list), C(install), C(remove), C(check),
      C(mount), C(unmount), C(view_package).
    type: path
  working_dir:
    description:
    - Specifies an alternative working directory path instead of the default /tmp directory.
    - If not specified the emgr command will use the /tmp directory.
    - Can be used if I(action) has one of following values C(install), C(remove), C(check),
      C(mount), C(unmount), C(display_ifix).
    type: path
  from_epkg:
    description:
    - Specifies to install an interim fix package file created with the epkg command.
    - Can be used if I(action=install).
    type: bool
    default: no
  mount_install:
    description:
    - Perform a mount installation. When and interim fix is mount-installed, the interim fix files
      are mounted over the target files.
    - This option is not supported for interim fix packages that require rebooting.
    - Can be used if I(action=install). Cannot be set when I(from_epkg=no).
    type: bool
    default: no
  commit:
    description:
    - Commits interim fix containing concurrent updates to disk after its installation.
    - Can be used if I(action=install).
    type: bool
    default: no
  extend_fs:
    description:
    - Attempts to resize any file systems where there is insufficient space.
    type: bool
    default: no
  force:
    description:
    - Forces action.
    - Can be used if I(action) has one of following values C(install), C(remove).
    - When I(action=install), it specifies the interim fix installation can overwrite an existing
      package.
    - When I(action=remove), it should be considered an emergency procedure because this method can
      create inconsistencies on the system.
    type: bool
    default: no
  preview:
    description:
    - Perform a preview that runs all of the check operations but does not make any changes.
    - Can be used if I(action) has one of following values C(install), C(commit), C(remove).
    type: bool
    default: no
  quiet:
    description:
    - Suppresses all output other than errors and strong warnings.
    - Can be used if I(action) has one of following values C(install), C(commit), C(remove).
    type: bool
    default: no
  bosboot:
    description:
    - Controls the bosboot process.
    - C(skip) skips the usual bosboot process for ifix that require rebooting.
    - C(load_debugger) loads the low-level debugger during AIX bosboot.
    - C(invoke_debugger) invokes the low-level debugger for AIX bosboot.
    - Can be used if I(action) has one of following values C(install), C(commit), C(remove).
    type: str
    choices: [ skip, load_debugger, invoke_debugger ]
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
- name: List interim fix on the system
  emgr:
    action: list

- name: Install ifix package from file generated with epkg
  emgr:
    action: install
    ifix_package: /usr/sys/inst.images/IJ22714s1a.200212.AIX72TL04SP00-01.epkg.Z
    working_dir: /usr/sys/inst.images
    from_epkg: true
    extend_fs: true

- name: List a specific ifix data in details
  emgr:
    action: list
    ifix_label: IJ22714s1a
    verbosity: 3

- name: Check an ifix
  emgr:
    action: check
    ifix_label: IJ22714s1a

- name: Preview ifix commit and display only errors and warnings
  emgr:
    action: commit
    ifix_label: IJ22714s1a
    preview: true
    quiet: true

- name: Remove an installed ifix based on its VUID
  emgr:
    action: remove
    ifix_vuid: 00F7CD554C00021210023020

- name: Display contents and topology of an ifix
  emgr:
    action: display_ifix
    ifix_package: /usr/sys/inst.images/IJ22714s1a.200212.AIX72TL04SP00-01.epkg.Z
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Missing parameter: force remove requires: ifix_label'
reboot_required:
    description: Indicates if ifix requires reboot.
    returned: always
    type: bool
    sample: True
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

    count = 0
    action = module.params['action']
    for param in one_of_list:
        if module.params[param] is not None and module.params[param]:
            count += 1
            break
    if count == 0 and required:
        results['msg'] = f'Missing parameter: action is {action} but\
                           one of the following is missing: '
        results['msg'] += ','.join(one_of_list)
        module.fail_json(**results)
    if count > 1 and exclusive:
        results['msg'] = f'Invalid parameter: action is {action} supports\
                           only one of the following: '
        results['msg'] += ','.join(one_of_list)
        module.fail_json(**results)


def parse_ifix_details(output):
    """
    Parses the output of "emgr -l" command to return the ifixes as a list instead of str.

    argument:
      stdout (str) standard output of the command.

    return:
      List of dictionaries containing information about the iFixes.
    """
    ifix_name = []

    info_list = ["ID", "STATE", "LABEL", "INSTALL TIME", "UPDATED BY", "ABSTRACT"]
    position_dict = {}

    def get_value(line, field):
        field_index = info_list.index(field)
        next_field_index = field_index + 1
        start_position = position_dict[field]

        # End-of-line
        if next_field_index >= len(info_list):
            end_position = None

        # All fields before the last one
        else:
            end_position = position_dict[info_list[next_field_index]]

        return line[start_position:end_position].strip()

    for line in output.split('\n'):
        line = line.strip()

        # Looking where each field position starts
        if line.upper().startswith(info_list[0].upper()):
            for field in info_list:
                if field not in position_dict:
                    position_dict[field] = line.find(field)

        # Iterating over each line looking for actual data
        elif len(position_dict) > 0:
            try:
                ifix_id = get_value(line, info_list[0])
                int(ifix_id)
            except ValueError:
                continue

            # Collect row values into dictionary
            ifix_data = {info_list[0]: ifix_id}
            for field in info_list[1:]:
                ifix_data[field] = get_value(line, field)

            ifix_name.append(ifix_data)

    return ifix_name


def is_ifix_installed(module, ifix_package):

    # Utility function to check if the ifix is installed in the system.
    ifix_label = ifix_package.split('/')[-1].split('.')[0]
    cmd = 'emgr -c -L' + ifix_label

    rc = module.run_command(cmd)[0]

    if rc == 0:
        return True
    else:
        return False


def main():
    global module
    global results

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(type='str', default='list', choices=['install', 'commit', 'check', 'mount', 'unmount',
                                                             'remove', 'view_package', 'display_ifix', 'list']),
            ifix_package=dict(type='path'),
            ifix_label=dict(type='str'),
            ifix_number=dict(type='str'),
            ifix_vuid=dict(type='str'),
            package=dict(type='str'),
            alternate_dir=dict(type='path'),
            list_file=dict(type='path'),
            working_dir=dict(type='path'),
            from_epkg=dict(type='bool', default=False),
            mount_install=dict(type='bool', default=False),
            commit=dict(type='bool', default=False),
            extend_fs=dict(type='bool', default=False),
            force=dict(type='bool', default=False),
            preview=dict(type='bool', default=False),
            quiet=dict(type='bool', default=False),
            bosboot=dict(type='str', choices=['skip', 'load_debugger', 'invoke_debugger']),
            verbose=dict(type='int', choices=[1, 2, 3]),
        ),
        required_if=[],
        mutually_exclusive=[['ifix_package', 'ifix_label', 'ifix_number', 'ifix_vuid', 'list_file']],
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        ifix_details=[],
        reboot_required=False,
    )

    bosboot_flags = {'skip': '-b', 'load_debugger': '-k', 'invoke_debugger': '-I'}

    action = module.params['action']
    verbose = module.params['verbose']

    cmd = ['emgr']
    if action == 'install':

        # check if ifix is already installed in the system
        if module.params['ifix_package']:
            if is_ifix_installed(module, module.params['ifix_package']):
                results['msg'] = 'This ifix is already installed. Nothing to do.'
                module.exit_json(**results)

        # Usage: emgr -e <ifix pkg> | -f <lfile> [-w <dir>] [-a <path>] [-bkpIqmoX]
        # Usage: emgr -i <ifix pkg> | -f <lfile> [-w <dir>] [-a <path>] [-CkpIqX]
        param_one_of(['ifix_package', 'list_file'])

        if module.params['list_file']:
            cmd += ['-f', module.params['list_file']]
        else:
            if module.params['from_epkg']:
                param_one_of(['from_epkg', 'commit'])
                cmd += ['-e', module.params['ifix_package']]
            else:
                if module.params['bosboot'] and module.params['bosboot'] == 'skip':
                    results['msg'] = 'Invalid parameter: action is install, does not support bosboot set to skip'
                    module.fail_json(**results)
                if module.params['ifix_package']:   # this test is optional thanks to param_one_of check.
                    cmd += ['-i', module.params['ifix_package']]
        if module.params['working_dir']:
            cmd += ['-w', module.params['working_dir']]
        if module.params['alternate_dir']:
            cmd += ['-a', module.params['alternate_dir']]
        if module.params['commit']:
            cmd += ['-C']
        if module.params['bosboot']:
            cmd += [bosboot_flags[module.params['bosboot']]]
        if module.check_mode or module.params['preview']:
            cmd += ['-p']
        if module.params['quiet']:
            cmd += ['-q']
        if module.params['mount_install']:
            cmd += ['-m']
        if module.params['force']:
            cmd += ['-o']
        if module.params['extend_fs']:
            cmd += ['-X']

    elif action == 'commit':
        # Usage: emgr -C -L <label> [-kpIqX]
        # Usage: emgr -C -i <ifix pkg> | -f <lfile> [-w <dir>] [-a <path>] [-kpIqX]
        param_one_of(['ifix_label', 'ifix_package', 'list_file'])
        if module.params['bosboot'] == 'skip':
            results['msg'] = 'Invalid parameter: action is commit, does not support bosboot set to skip'
            module.fail_json(**results)

        cmd += ['-C']
        if module.params['ifix_label']:
            cmd += ['-L', module.params['ifix_label']]
        else:
            if module.params['ifix_package']:
                cmd += ['-i', module.params['ifix_package']]
            elif module.params['list_file']:
                cmd += ['-f', module.params['list_file']]
            if module.params['working_dir']:
                cmd += ['-w', module.params['working_dir']]
            if module.params['alternate_dir']:
                cmd += ['-a', module.params['alternate_dir']]
        if module.params['bosboot']:
            cmd += [bosboot_flags[module.params['bosboot']]]
        if module.check_mode or module.params['preview']:
            cmd += ['-p']
        if module.params['quiet']:
            cmd += ['-q']
        if module.params['extend_fs']:
            cmd += ['-X']

    elif action == 'check' or action == 'mount' or action == 'unmount':
        # Usage: emgr -c [-L <label> | -n <ifix num> | -u <VUID> | -f <lfile>] [-w <dir>] [-a <path>] [-v{1-3}X]
        # Usage: emgr -M | -U [-L <label> | -n <ifix num> | -u <VUID> | -f <lfile>] [-w <dir>] [-a <path>] [-X]
        param_one_of(['ifix_label', 'ifix_number', 'ifix_vuid', 'list_file'])
        if action == 'check':
            cmd += ['-c']
        elif action == 'mount':
            cmd += ['-M']
        else:
            cmd += ['-U']
        if module.params['ifix_label']:
            cmd += ['-L', module.params['ifix_label']]
        elif module.params['ifix_number']:
            cmd += ['-n', module.params['ifix_number']]
        elif module.params['ifix_vuid']:
            cmd += ['-u', module.params['ifix_vuid']]
        elif module.params['list_file']:
            cmd += ['-f', module.params['list_file']]
        if module.params['working_dir']:
            cmd += ['-w', module.params['working_dir']]
        if module.params['alternate_dir']:
            cmd += ['-a', module.params['alternate_dir']]
        if module.params['extend_fs']:
            cmd += ['-X']
        if action == 'check' and verbose is not None:
            cmd += ['-v', f'{verbose}']

    elif action == 'remove' and module.params['force']:
        # Usage: emgr -R <ifix label> [-w <dir>] [-a <path>] [-X]
        if module.params['ifix_package']:
            if not is_ifix_installed(module, module.params['ifix_package']):
                results['msg'] = 'This ifix is NOT installed in the system. Nothing to do.'
                module.exit_json(**results)
        if not module.params['ifix_label']:
            results['msg'] = 'Missing parameter: force remove requires: ifix_label'
            module.fail_json(**results)
        cmd += ['-R', module.params['ifix_label']]
        if module.params['working_dir']:
            cmd += ['-w', module.params['working_dir']]
        if module.params['alternate_dir']:
            cmd += ['-a', module.params['alternate_dir']]
        if module.params['extend_fs']:
            cmd += ['-X']

    elif action == 'remove':
        # Usage: emgr -r -L <label> | -n <ifix num> | -u <VUID> | -f <lfile> [-w <dir>] [-a <path>] [-bkpIqX]
        if module.params['ifix_package']:
            if not is_ifix_installed(module, module.params['ifix_package']):
                results['msg'] = 'This ifix is NOT installed in the system. Nothing to do.'
                module.exit_json(**results)
        param_one_of(['ifix_label', 'ifix_number', 'ifix_vuid', 'list_file'])
        cmd += ['-r']
        if module.params['ifix_label']:
            cmd += ['-L', module.params['ifix_label']]
        elif module.params['ifix_number']:
            cmd += ['-n', module.params['ifix_number']]
        elif module.params['ifix_vuid']:
            cmd += ['-u', module.params['ifix_vuid']]
        elif module.params['list_file']:
            cmd += ['-f', module.params['list_file']]
        if module.params['working_dir']:
            cmd += ['-w', module.params['working_dir']]
        if module.params['alternate_dir']:
            cmd += ['-a', module.params['alternate_dir']]
        if module.params['bosboot']:
            cmd += [bosboot_flags[module.params['bosboot']]]
        if module.check_mode or module.params['preview']:
            cmd += ['-p']
        if module.params['quiet']:
            cmd += ['-q']
        if module.params['extend_fs']:
            cmd += ['-X']

    elif action == 'view_package':
        # Usage: emgr -P [<Package>] [-a <path>] [-X]
        cmd += ['-P']
        if module.params['package']:
            cmd += [module.params['package']]
        if module.params['alternate_dir']:
            cmd += ['-a', module.params['alternate_dir']]
        if module.params['extend_fs']:
            cmd += ['-X']

    elif action == 'display_ifix':
        # Usage: emgr -d -e <ifix pkg> | -f <lfile> [-w <path>] [-v{1-3}X]
        param_one_of(['ifix_package', 'list_file'])
        cmd += ['-d']
        if module.params['ifix_package']:
            cmd += ['-e', module.params['ifix_package']]
        elif module.params['list_file']:
            cmd += ['-f', module.params['list_file']]
        if module.params['working_dir']:
            cmd += ['-w', module.params['working_dir']]
        if verbose is not None:
            cmd += ['-v', f'{verbose}']
        if module.params['extend_fs']:
            cmd += ['-X']

    else:   # action=list
        # Usage: emgr -l [-L <label> | -n <ifix number> | -u <VUID>] [-v{1-3}X] [-a <path>]
        param_one_of(['ifix_label', 'ifix_number', 'ifix_vuid'], required=False)
        cmd += ['-l']
        if module.params['ifix_label']:
            cmd += ['-L', module.params['ifix_label']]
        elif module.params['ifix_number']:
            cmd += ['-n', module.params['ifix_number']]
        elif module.params['ifix_vuid']:
            cmd += ['-u', module.params['ifix_vuid']]
        if verbose is not None:
            cmd += ['-v', f'{verbose}']
        if module.params['extend_fs']:
            cmd += ['-X']
        if module.params['alternate_dir']:
            cmd += ['-a', module.params['alternate_dir']]

    if module.params['working_dir'] and not os.path.exists(module.params['working_dir']):
        os.makedirs(module.params['working_dir'])

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    if not module.check_mode or ((action in ['install', 'commit', 'check', 'view_package', 'display_ifix', 'list'])
                                 and (action == 'remove' and not module.params['force'])):
        rc, stdout, stderr = module.run_command(cmd)

        results['stdout'] = stdout
        results['stderr'] = stderr

        if "system reboot is required" in stderr:
            results['reboot_required'] = True

        pattern = "There is no efix data on this system"
        found = re.search(pattern, stderr)

        if rc == 0 and found:
            module.exit_json(**results)

        if rc != 0:
            line_pattern = r"(\s*)E(PKG|FIX) NUMBER(\s*)LABEL(\s*)OPERATION(\s*)RESULT(\s*)"
            res_line = re.search(line_pattern, stdout)

            if module.params['list_file'] and res_line:
                summary_line = res_line.group(0)
                success_list = []
                fail_list = []
                stdout_lines = (stdout.split(summary_line)[1]).splitlines()[1:-1]
                for line in stdout_lines:
                    line = line.split()
                    if len(line):
                        if line[-1] == "SUCCESS":
                            success_list.append(line[1])
                        if line[-1] == "FAILURE":
                            fail_list.append(line[1])

                if len(success_list):
                    results['msg'] = f"Action - {module.params['action']} performed successfuly on {', '.join(success_list)}."
                    results['msg'] += f" Failed for the following: {', '.join(fail_list)}."
                    results['changed'] = True
                    module.exit_json(**results)

            # Ifix was already installed(0645-065).
            # Ifix with label to remove is not there (0645-066).
            # Ifix with VUUID to remove is not there (0645-082).
            # Ifix with ID number to remove is not there (0645-081).
            pattern = "0645-065|0645-066|0645-081|0645-082|There is no efix data on this system"
            found = re.search(pattern, stderr)
            results['changed'] = False

            if not found:
                results['msg'] = f'Command {cmd} failed with return code {rc}.'

            module.fail_json(**results)

        results['msg'] = f'Command {cmd} successful.'
        if action in ['install', 'commit', 'mount', 'unmount', 'remove'] and not module.params['preview'] and not module.check_mode and (rc == 0):
            results['changed'] = True
        elif action == 'list' and not module.params['preview'] and not module.check_mode and (rc == 0):
            results['ifix_details'] = parse_ifix_details(stdout)
    else:
        results['msg'] = f'Command {cmd} has no preview mode, execution skipped.'
        results['stdout'] = 'No stdout as execution has been skipped.'

    for i in results['ifix_details']:
        if "Q" in i['STATE']:
            results['reboot_required'] = True
            break

    module.exit_json(**results)


if __name__ == '__main__':
    main()
