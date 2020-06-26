#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018- IBM, Inc
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
module: nim_upgradeios
short_description: Perform a VIOS upgrade with NIM
description:
- Tool to upgrade one or a pair of VIOSes.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform.
    - C(backup) to create a backup.
    - C(view_backup) to view existing backups.
    - C(restore_backup) to restore an existing backup.
    - C(upgrade_restore) to upgrade and restore target VIOS.
    type: str
    choices: [ backup, view_backup, restore_backup, upgrade_restore, all ]
    required: true
  targets:
    description:
    - NIM target.
    - 'To perform an action on dual VIOSes, specify the list as a tuple
      with the following format: "(vios1, vios2) (vios3, vios4)".'
    - 'To specify a single VIOS, use the following format: "(vios1)".'
    type: str
    required: true
  email:
    description:
    - Email address to set in the NIM master's /etc/niminfo file if not already set.
    type: str
  location:
    description:
    - Existing directory to store the ios_backup on the NIM master.
    type: str
  backup_prefix:
    description:
    - Prefix of the ios_backup NIM resource.
    - The name of the target VIOS is added to this prefix.
    type: str
  force:
    description:
    - Removes any existing ios_backup NIM resource prior to creating the backup.
    type: str
    choices: [ 'yes', 'no' ]
    default: 'no'
  boot_client:
    description:
    - Boots the clients of the target VIOS after the upgrade and restore operation.
    type: str
    choices: [ 'yes', 'no' ]
    default: 'no'
  resolv_conf:
    description:
    - NIM resource to use for the VIOS installation.
    type: str
  spot_prefix:
    description:
    - Prefix of the Shared Product Object Tree (SPOT) NIM resource to use for
      the VIOS installation.
    - 'The NIM name of the target VIOS is added to find
      the actual NIM resource, like: "<spot_prefix>_<vios_name>".'
    type: str
  mksysb_prefix:
    description:
    - Prefix of the mksysb NIM resource to use for the VIOS installation.
    - 'The NIM name of the target VIOS is added to this prefix to find the actual
      NIM resource, like: "<mksysb_prefix>_<vios_name>".'
    type: str
  bosinst_data_prefix:
    description:
    - Prefix of the bosinst_data NIM resource that contains the BOS
      installation program to use.
    - 'The NIM name of the target VIOS is added to
      this prefix to find the actual NIM resource, like:
      "<bosinst_data_prefix>_<vios_name>".'
    type: str
  time_limit:
    description:
    - Before starting the action, the actual date is compared to this parameter value;
      if it is greater then the task is stopped; the format is C(mm/dd/yyyy hh:mm).
    type: str
  vars:
    description:
    - Specifies additional parameters.
    type: dict
  vios_status:
    description:
    - Specifies the result of a previous operation.
    type: dict
  nim_node:
    description:
    - Allows to pass along NIM node info from a task to another so that it
      discovers NIM info only one time for all tasks.
    type: dict
'''

EXAMPLES = r'''
- name: Perform a backup of nimvios01
  nim_upgradeios:
    targets: "(nimvios01)"
    action: backup
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
targets:
    description: List of VIOSes.
    returned: always
    type: list
    elements: str
nim_node:
    description: NIM node info.
    returned: always
    type: dict
status:
    description: Status for each VIOS (dicionnary key).
    returned: always
    type: dict
'''

import os
import re
import subprocess
import time
import threading

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule

# TODO: Replace argument with choice [yes,no] into bool
# TODO: -----------------------------------------------------------------------------
# TODO: Later, add SSP support
# TODO: Later, add mirrored rootvg support for upgrade & upgrade all in one
# TODO: Later, add cluster support for viosbr restore

# TODO: Check message indentation in OUTPUT
# TODO: Check if all debug section (TBC) are commented before commit
# TODO: -----------------------------------------------------------------------------

DEBUG_DATA = []
OUTPUT = []
CHANGED = False


def exec_cmd(cmd, module, exit_on_error=False, debug_data=True, shell=False):
    """
    Execute the given command

    Note: If executed in thread, fail_json does not exit the parent

    args:
        cmd           array of the command parameters
        module        the Ansible module
        exit_on_error an exception is raised if true and cmd return !0
        debug_data    prints some trace in DEBUG_DATA if set
        shell         execute cmd through the shell if set (vulnerable to shell
                      injection when cmd is from user inputs). If cmd is a string
                      string, the string specifies the command to execute through
                      the shell. If cmd is a list, the first item specifies the
                      command, and other items are arguments to the shell itself.
    return:
        ret    return code of the command
        output output and stderr of the command
        errout command stderr
    """

    global DEBUG_DATA
    global CHANGED
    global OUTPUT

    ret = 0
    output = ''
    errout = ''

    th_id = threading.current_thread().ident
    stderr_file = '/tmp/ansible_upgradeios_cmd_stderr_{0}'.format(th_id)

    module.debug('exec command:{0}'.format(cmd))
    if debug_data is True:
        DEBUG_DATA.append('exec command:{0}'.format(cmd))
    try:
        myfile = open(stderr_file, 'w')
        output = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)
        myfile.close()
        s = re.search(r'rc=([-\d]+)$', output)
        if s:
            ret = int(s.group(1))
            output = re.sub(r'rc=[-\d]+\n$', '', output)  # remove the rc of c_rsh with echo $?

    except subprocess.CalledProcessError as exc:
        myfile.close()
        errout = re.sub(r'rc=[-\d]+\n$', '', exc.output)  # remove the rc of c_rsh with echo $?
        ret = exc.returncode

    except (OSError, IOError) as exc:
        myfile.close()
        if exc.args:
            match = re.match(r'rc=[-\d]+\n$', exc.args[1])
            if match:
                errout = re.sub(r'rc=[-\d]+\n$', '', exc.args[1])  # remove the rc of c_rsh with echo $?
                ret = exc.args[0]
            else:
                msg = 'Command: {0} Exception: {1}'.format(cmd, exc)
                ret = 1
                module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                                 debug_output=DEBUG_DATA, status=module.status)
        else:
            msg = 'Command: {0} Exception: {1}'.format(cmd, exc)
            ret = 1
            module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT)

    # check for error message
    if os.path.getsize(stderr_file) > 0:
        myfile = open(stderr_file, 'r')
        errout += ''.join(myfile)
        myfile.close()
    os.remove(stderr_file)

    if debug_data is True:
        DEBUG_DATA.append('exec command rc:{0}, output:{1} errout:{2}'
                          .format(ret, output, errout))
        module.debug('exec command rc:{0}, output:{1} errout:{2}'
                     .format(ret, output, errout))

    if ret != 0 and exit_on_error is True:
        msg = 'Command: {0} RetCode:{1} ... stdout:{2} stderr:{3}'\
              .format(cmd, ret, output, errout)
        module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                         debug_output=DEBUG_DATA, status=module.status)

    return (ret, output, errout)


def get_nim_clients_info(module, lpar_type):
    """
    Get the list of the lpar (standalones or vios) defined on the
    nim master, and get their cstate.

    args:
        module    the Ansible module
        lpar_type type of partition: 'standalones' or 'vios'

    return:
        the list of the name of the lpar objects defined on the
        nim master and their associated cstate value
    """
    global CHANGED
    global OUTPUT
    global DEBUG_DATA
    info_hash = {}

    cmd = 'LC_ALL=C lsnim -t {0} -l'.format(lpar_type)
    (ret, std_out, std_err) = exec_cmd(cmd, module, shell=True)
    if ret != 0:
        msg = 'Cannot list NIM {0} objects: {1}'.format(lpar_type, std_err)
        module.log(msg)
        module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                         debug_output=DEBUG_DATA, status=module.status)

    # lpar name and associated Cstate
    obj_key = ''
    for line in std_out.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            cstate = match_cstate.group(1)
            info_hash[obj_key]['cstate'] = cstate
            continue

        # For VIOS store the management profile
        if lpar_type == 'vios':
            # Not used in this module so far
            # match_mgmtprof = re.match(r"^\s+mgmt_profile1\s+=\s+(.*)$", line)
            # if match_mgmtprof:
            #     mgmt_elts = match_mgmtprof.group(1).split()
            #     if len(mgmt_elts) >= 3:
            #         info_hash[obj_key]['mgmt_hmc_id'] = mgmt_elts[0]
            #         info_hash[obj_key]['mgmt_vios_id'] = mgmt_elts[1]
            #         info_hash[obj_key]['mgmt_cec_serial'] = mgmt_elts[2]
            #     else:
            #         module.log('VIOS {0} management profile has not 3 elements: {1}'
            #                    .format(obj_key, match_mgmtprof.group(1)))
            #     continue

            # Get VIOS interface info in case we need c_rsh
            match_if = re.match(r"^\s+if1\s+=\s+\S+\s+(\S+)\s+.*$", line)
            if match_if:
                info_hash[obj_key]['vios_ip'] = match_if.group(1)
                continue

    module.debug('get_nim_clients_info return: {0}'.format(info_hash))
    return info_hash


def check_vios_targets(module, targets):
    """
    check the list of the vios targets.

    args:
        module  the Ansible module
        targets list of tuple of NIM name of vios machine, could be
                of the following form: (vios1, vios2) (vios3)
    return:
        the list of the existing vios tuple matching the target list
    """
    module.debug('ENTER check_vios_targets targets: {0}'.format(targets))
    vios_list = {}
    vios_list_tuples_res = []
    vios_list_tuples = targets.replace(" ", "").replace("),(", ")(").split('(')

    # ===========================================
    # Build targets list
    # ===========================================
    for vios_tuple in vios_list_tuples[1:]:
        module.debug('Checking vios_tuple: {0}'.format(vios_tuple))

        tuple_elts = list(vios_tuple[:-1].split(','))
        tuple_len = len(tuple_elts)

        if tuple_len != 1 and tuple_len != 2:
            OUTPUT.append('Malformed VIOS targets {0}. Tuple {1} should be a 1 or 2 elements.'
                          .format(targets, tuple_elts))
            module.log('Malformed VIOS targets {0}. Tuple {1} should be a 1 or 2 elements.'
                       .format(targets, tuple_elts))
            return None

        # check vios not already exists in the target list
        if tuple_elts[0] in vios_list or (tuple_len == 2 and (tuple_elts[1] in vios_list
                                                              or tuple_elts[0] == tuple_elts[1])):
            OUTPUT.append('Malformed VIOS targets {0}. Duplicated VIOS'
                          .format(targets))
            module.log('Malformed VIOS targets {0}. Duplicated VIOS'
                       .format(targets))
            return None

        # check vios is knowed by the NIM master - if not ignore it
        if tuple_elts[0] not in module.nim_node['nim_vios']:
            msg = 'VIOS {0} is not client of the NIM master, will be ignored'\
                  .format(tuple_elts[0])
            OUTPUT.append(msg)
            module.log(msg)
            continue
        if tuple_len == 2 and tuple_elts[1] not in module.nim_node['nim_vios']:
            msg = 'VIOS {0} is not client of the NIM master, will be ignored'\
                  .format(tuple_elts[1])
            OUTPUT.append(msg)
            module.log(msg)
            continue

        # check vios connectivity
        res = 0
        for elem in tuple_elts:
            cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', elem,
                   '"/usr/bin/ls /dev/null; echo rc=$?"']
            (ret, std_out, std_err) = exec_cmd(cmd, module)
            if ret != 0:
                res = 1
                msg = 'skipping {0}: cannot reach {1} with c_rsh: {2}, {3}, {4}'\
                      .format(vios_tuple, elem, res, std_out, std_err)
                module.log(msg)
                continue
        if res != 0:
            continue

        if tuple_len == 2:
            vios_list[tuple_elts[0]] = tuple_elts[1]
            vios_list[tuple_elts[1]] = tuple_elts[0]
            my_tuple = (tuple_elts[0], tuple_elts[1])
            vios_list_tuples_res.append(tuple(my_tuple))
        else:
            vios_list[tuple_elts[0]] = tuple_elts[0]
            # vios_list.append(tuple_elts[0])
            my_tuple = (tuple_elts[0],)
            vios_list_tuples_res.append(tuple(my_tuple))

    return vios_list_tuples_res


def nim_set_infofile(module):
    """
    Additional settings in NIM master's /etc/niminfo file

    args:
        module the Ansible module

    module.param used:
        email (optional)

    return:
        0 if success, 1 otherwise
    """
    global CHANGED
    global OUTPUT
    global DEBUG_DATA
    file_path = '/etc/niminfo'

    if 'email' in module.params and module.params['email']:
        if not re.match(r"^\s*\s+@\s+$", module.params['email']):
            module.log('Check the email address is valid: "{0}"'.format(module.params['email']))
            OUTPUT.append('Check the email address is valid: "{0}"'.format(module.params['email']))
            return 1

        try:
            niminfo_file = open(file_path, 'a+')
            for line in niminfo_file:
                match_key = re.match(r'^export\S+NIM_MASTER_UID="\(\s+@\s+\)"$', line)
                if match_key:
                    msg = 'Existing email "{0}" found in "{1}", skip this setting'\
                          .format(match_key.group(1), file_path)
                    if match_key.group(1) != module.params['email']:
                        module.log(msg)
                        OUTPUT.append(msg)
                    else:
                        module.log(msg)
                    break
            else:  # NIM_MASTER_UID not found
                niminfo_file.write('export NIM_MASTER_UID="root,{0}"'
                                   .format(module.params['email']))
        except IOError as e:
            msg = 'Failed to parse file {0}: {1}.'.format(e.filename, e.strerror)
            module.log(msg)
            module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                             debug_output=DEBUG_DATA, status=module.status)
    return 0


def nim_backup(module):
    """
    Perform a NIM operation to create a backup for each VIOSes

    args:
        module   the module variable

    module.param used:
        vios_status   (optional)
        location      (optional)
        backup_prefix (optional) to build the name of the backup
        force         (optional) remove existing backup if any

    return:
        error_nb number of errors if any
        set module.status[<target_uple>] with the status
    """
    global CHANGED
    global OUTPUT
    error_nb = 0

    # fixed part of the command
    # nim -Fo define -t ios_backup -a mk_image=yes -a server=master
    #  -a source=<vios> -a location=/export/nim/ios_backup/ios_backup_<vios> ios_backup_<vios>
    cmd = 'nim -Fo define -t ios_backup -a mk_image=yes -a server=master'

    vios_key = []
    for target_tuple in module.targets:
        module.debug('Backup for target_tuple: {0}'.format(target_tuple))

        vios1 = target_tuple[0]
        if len(target_tuple) == 2:
            vios_key = '{0}-{1}'.format(target_tuple[0], target_tuple[1])
        else:
            vios_key = vios1
        module.debug('vios_key: {0}'.format(vios_key))

        # Check previous status if known
        if module.params['vios_status'] is not None:
            if vios_key not in module.params['vios_status']:
                module.status[vios_key] = 'FAILURE-NO-PREV-STATUS'
                OUTPUT.append('    {0} vioses skipped (no previous status found)'
                              .format(vios_key))
                module.log('[WARNING] {0} vioses skipped (no previous status found)'
                           .format(vios_key))
                continue

            if not re.match(r"^SUCCESS", module.params['vios_status'][vios_key]):
                module.status[vios_key] = module.params['vios_status'][vios_key]
                OUTPUT.append('    {0} vioses skipped (vios_status: {1})'
                              .format(vios_key, module.params['vios_status'][vios_key]))
                module.log('[WARNING] {0} vioses skipped (vios_status: {1})'
                           .format(vios_key, module.params['vios_status'][vios_key]))
                continue

        # check if there is time to handle this tuple
        if module.time_limit is not None and time.localtime(time.time()) >= module.time_limit:
            time_limit_str = time.strftime('%m/%d/%Y %H:%M', module.time_limit)
            msg = 'Time limit {0} reached, no further operation'\
                  .format(time_limit_str)
            module.log(msg)
            OUTPUT.append('    ' + msg)
            return 0

        module.status[vios_key] = 'SUCCESS-BCKP'

        for vios in target_tuple:
            OUTPUT.append('    Backup creation for VIOS: {0}'.format(vios))

            backup_info = {}
            if module.params['backup_prefix']:
                backup_info['name'] = '{0}_{1}'.format(module.params['backup_prefix'], vios)
            else:
                backup_info['name'] = 'ios_backup_{0}'.format(vios)
                msg = 'backup_prefix is missing, using default:"{0}"'.format(backup_info['name'])
                module.log(msg)
                OUTPUT.append('    ' + msg)
            if module.params['location']:
                backup_info['location'] = module.params['location']
            else:
                backup_info['location'] = '/export/nim/ios_backup'

            # finalize the command
            #  -a source=<vios>
            #  -a location=/export/nim/viosbr/ios_backup_<vios>
            #  ios_backup_<vios>
            cmd += ' -a source={0} -a location={1}/{2} {3}'\
                   .format(vios, backup_info['location'],
                           backup_info['name'], backup_info['name'])
            rm_cmd = ''
            if module.params['force'] == 'yes':
                rm_cmd = 'lsnim -l {0} && nim -o remove {1}; '\
                         .format(backup_info['name'], backup_info['name'])

            cmd = 'export NIM_DEBUG=1; ' + rm_cmd + cmd

            # TBC - Begin: Uncomment for testing without effective upgrade operation
            # OUTPUT.append('Warning: testing without effective upgrade operation')
            # OUTPUT.append('NIM Command: {0} '.format(cmd))
            # ret = 0
            # std_out = 'NIM Command: {0} '.format(cmd)
            # module.status[vios_key] = 'SUCCESS-BCKP'
            # module.nim_node['nim_vios'][vios]['backup'] = backup_info
            # continue
            # TBC - End

            (ret, std_out, std_err) = exec_cmd(cmd, module, shell=True)

            if ret != 0:
                module.log('NIM Command: {0} failed {1} {2} {3}'
                           .format(cmd, ret, std_out, std_err))
                OUTPUT.append('    Failed to backup VIOS {0} with NIM: {1}'
                              .format(vios, std_err))
                # set the error label to be used in sub routines
                if vios == vios1:
                    module.status[vios_key] = 'FAILURE-BCKP1'
                else:
                    module.status[vios_key] = 'FAILURE-BCKP2'
                error_nb += 1
                break  # next tuple

            module.nim_node['nim_vios'][vios]['backup'] = backup_info.copy()
            msg = 'VIOS {0} successfully backed up'.format(vios)
            module.log(msg)
            OUTPUT.append('    ' + msg)
            # CHANGED = True

    return error_nb


# TODO: test nim_viosbr function for restore backup
def nim_viosbr(module):
    """
    Perform a NIM operation to view or restore backup
    (depending on module.params['action'] value)

    args:
        module   the module variable

    module.param used:
        vios_status   (optional)
        action        (only view_backup, restore_backup are supported here)
        backup_prefix (optional) to build the name of the backup

    return:
        error_nb number of errors if any
        set module.status[<target_uple>] with the status
    """
    global CHANGED
    global OUTPUT
    global DEBUG_DATA
    error_nb = 0

    # set label for status depending of the action
    if module.params['action'] == 'view_backup':
        action_label = 'VIEW'
    elif module.params['action'] == 'restore_backup' or module.params['action'] == 'all':
        action_label = 'REST'
    else:
        # Should not happen
        msg = 'Unknown action "{0}" in nim_viosbr'.format(module.params['action'])
        module.log(msg)
        module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                         debug_output=DEBUG_DATA, status=module.status)

    # fixed part of the command for view and restore
    # nim -Fo viosbr -a viosbr_action=view -a ios_backup=ios_backup_<vios> <vios>
    # nim -Fo viosbr -a ios_backup=ios_backup_<vios> <vios>
    cmd = 'export NIM_DEBUG=1; nim -Fo viosbr'
    if module.params['action'] == 'view_backup':
        cmd += ' -a viosbr_action=view'

    vios_key = []
    for target_tuple in module.targets:
        module.debug('nim_backup for target_tuple: {0}'.format(target_tuple))

        vios1 = target_tuple[0]
        if len(target_tuple) == 2:
            vios_key = '{0}-{1}'.format(target_tuple[0], target_tuple[1])
        else:
            vios_key = vios1
        module.debug('vios_key: {0}'.format(vios_key))

        # Check previous status if known
        if module.params['vios_status'] is not None:
            if vios_key not in module.params['vios_status']:
                module.status[vios_key] = 'FAILURE-NO-PREV-STATUS'
                OUTPUT.append('    {0} vioses skipped (no previous status found)'
                              .format(vios_key))
                module.log('[WARNING] {0} vioses skipped (no previous status found)'
                           .format(vios_key))
                continue

            if not re.match(r"^SUCCESS", module.params['vios_status'][vios_key]):
                module.status[vios_key] = module.params['vios_status'][vios_key]
                OUTPUT.append('    {0} vioses skipped (vios_status: {1})'
                              .format(vios_key, module.params['vios_status'][vios_key]))
                module.log('[WARNING] {0} vioses skipped (vios_status: {1})'
                           .format(vios_key, module.params['vios_status'][vios_key]))
                continue

        # check if there is time to handle this tuple
        if module.time_limit is not None and time.localtime(time.time()) >= module.time_limit:
            time_limit_str = time.strftime('%m/%d/%Y %H:%M', module.time_limit)
            msg = 'Time limit {0} reached, no further operation'\
                  .format(time_limit_str)
            module.log(msg)
            OUTPUT.append('    ' + msg)
            return 0

        module.status[vios_key] = 'SUCCESS-' + action_label

        for vios in target_tuple:
            OUTPUT.append('    View backup for VIOS: {0}'.format(vios))

            # get the backup name
            if module.params['backup_prefix']:
                backup_name = '{0}_{1}'.format(module.params['backup_prefix'], vios)
            elif 'backup' in module.nim_node['nim_vios'][vios]:
                backup_name = module.nim_node['nim_vios'][vios]['backup']['name']
            else:
                backup_name = 'ios_backup_{0}'.format(vios)
                msg = 'backup_prefix is missing, using default:"{0}"'.format(backup_name)
                module.log(msg)
                OUTPUT.append('    ' + msg)
                # TODO: 'view_backup' we could also look into the NIM resource
                #           type=ios_backup and source_image=<vios>

            # finalize the command
            #  -a ios_backup=ios_backup_<vios> <vios>
            cmd += ' -a ios_backup={0} {1}'.format(backup_name, vios)

            # TBC - Begin: Uncomment for testing without effective upgrade operation
            # OUTPUT.append('Warning: testing without effective upgrade operation')
            # OUTPUT.append('NIM Command: {0} '.format(cmd))
            # ret = 0
            # std_out = 'NIM Command: {0} '.format(cmd)
            # module.status[vios_key] = 'SUCCESS-' + action_label
            # if module.params['action'] == 'restore_backup' or module.params['action'] == 'all':
            #     CHANGED = True
            # continue
            # TBC - End

            (ret, std_out, std_err) = exec_cmd(cmd, module, shell=True)

            if ret != 0:
                module.log('NIM Command: {0} failed {1} {2} {3}'
                           .format(cmd, ret, std_out, std_err))
                OUTPUT.append('    Failed to {0} for VIOS {1} with NIM: {2}'
                              .format(module.params['action'], vios, std_err))
                if vios != vios1:
                    module.status[vios_key] = 'FAILURE-{0}{1}'.format(action_label, '1')
                else:
                    module.status[vios_key] = 'FAILURE-{0}{1}'.format(action_label, '2')
                error_nb += 1
                break  # next tuple

            if module.params['action'] == 'view_backup':
                msg = 'VIOS {0} backup info:'.format(vios)
                module.log(msg)
                module.log(std_out)
                OUTPUT.append('    ' + msg)
                OUTPUT.append(map(lambda x: '      ' + str(x), std_out.split('\n')))
                # CHANGED = True
            elif module.params['action'] == 'restore_backup'\
                    or module.params['action'] == 'all':
                msg = 'VIOS {0} backup successfully restored'.format(vios)
                module.log(msg)
                OUTPUT.append('    ' + msg)
                CHANGED = True

    return error_nb


# TODO: test MigviosThread class
class MigviosThread(threading.Thread):
    """
    Class use for the migration of a VIOS tuple
    """

    def __init__(self, module, target_tuple, time_limit):
        if len(target_tuple) == 2:
            vios_key = '{0}-{1}'.format(target_tuple[0], target_tuple[1])
        else:
            vios_key = '{0}'.format(target_tuple[0])
        self._stop_event = threading.Event()
        self._module = module
        self._target_tuple = target_tuple
        self._time_limit = time_limit
        threading.Thread.__init__(self, name='MigviosThread({0})'.format(vios_key))

    def run(self):
        self._module.debug('Strating {0}'.format(self.getName()))
        nim_migvios_tuple(self._module, self._target_tuple, self._stop_event)
        self._module.debug('End of {0}'.format(self.getName()))

    def join(self, timeout=None):
        while self.isAlive():
            t = time.time()
            if self._time_limit and t >= self._time_limit:
                break
            time.sleep(60)
        self._stop_event.set()
        self._module.debug('Asking {0} to terminate, waiting for timeout={1}'
                           .format(self.getName(), timeout))
        threading.Thread.join(self, timeout)


# TODO: test nim_migvios_all function
def nim_migvios_all(module):
    """
    Execute the migvios command on the first vios of each tuples,
    wait for completion, if succeeded execute the migvios command
    for second vios and wait for completion.

    args:
        module  the Ansible module
    """
    global CHANGED
    global OUTPUT

    # threads = []

    for target_tuple in module.targets:
        # TODO: test and activate multi threading
        module.debug('Start nim_migvios_tuple for {0}'.format(target_tuple))
        nim_migvios_tuple(module, target_tuple, None)
        module.debug('End nim_migvios_tuple for {0}'.format(target_tuple))
    #     # Spawn a thread running nim_migvios_tuple(module, target_tuple, time_limit)
    #     module.debug('Spawning MigviosThread for {0} terminated'.format(target_tuple))

    #     th = MigviosThread(module=module,
    #                        target_tuple=target_tuple,
    #                        time_limit=module.time_limit)
    #     threads.append(th)
    #     th.start()

    # for th in threads:
    #     module.debug('Waiting for {0} termination...'.format(th.getName()))
    #     # No timeout in this join() as
    #     # - the user can set a time_limit
    #     # - there is a timeout when NIM states show no progress
    #     th.join()
    #     module.debug('{0} terminated'.format(th.getName()))

    # for th in threads:
    #     if th.isAlive():
    #         module.log('{0} is still alive'.format(th.getName()))

    return 0


# TODO: test nim_migvios_tuple function
def nim_migvios_tuple(module, target_tuple, stop_event):
    """
    Handle the migvios execution in a thread for the tuple.
    Watch for stop_event (set by join() if time_limit is reached).

    args:
        module        the Ansible module
        target_tuple  tuple of target to run migvios can be
                      (vios1,vios2) or (vios1)
        stop_event    flag set if we reached time_limit

    module.param used:
        action      (for logging only)
        vios_status (optional)

    return:
        -1 if timed out (stop_event set),
        0  if migvios succeeded,
        1  if migvios failed or has shown no progress for a long period,
        set module.status[<target_uple>] with the status
    """
    global CHANGED
    global OUTPUT

    # build the key from the tuple
    vios1 = target_tuple[0]
    if len(target_tuple) == 2:
        vios_key = '{0}-{1}'.format(target_tuple[0], target_tuple[1])
    else:
        vios_key = vios1

    module.log('nim_migvios {0} for target_tuple: {1}'
               .format(module.params['action'], target_tuple))

    for vios in target_tuple:
        module.log('nim_migvios {0} for VIOS {1}'
                   .format(module.params['action'], vios))

        # Check previous status if known
        if module.params['vios_status'] is not None:
            if vios_key not in module.params['vios_status']:
                module.status[vios_key] = 'FAILURE-NO-PREV-STATUS'
                msg = '{0} vioses skipped (no previous status found)'.format(vios_key)
                module.log(msg)
                OUTPUT.append('    ' + msg)
                continue

            if not re.match(r"^SUCCESS", module.params['vios_status'][vios_key]):
                module.status[vios_key] = module.params['vios_status'][vios_key]
                msg = '{0} vioses skipped (vios_status: {1})'\
                      .format(vios_key, module.params['vios_status'][vios_key])
                module.log(msg)
                OUTPUT.append('    ' + msg)
                continue

        # check if we are asked to stop (time_limit might be reached)
        if stop_event and stop_event.isSet():
            msg = 'Time limit {0} reached, no further operation'\
                  .format(time.strftime('%m/%d/%Y %H:%M', module.time_limit))
            module.log(msg)
            OUTPUT.append('    ' + msg)
            return -1

        ret = nim_migvios(module, vios)
        if ret == 0:
            if vios == vios1:
                module.status[vios_key] = 'SUCCESS-UPGR1-INIT'
            else:
                module.status[vios_key] = 'SUCCESS-UPGR2-INIT'
        else:
            if vios == vios1:
                module.status[vios_key] = 'FAILURE-UPGR1-INIT'
            else:
                module.status[vios_key] = 'FAILURE-UPGR2-INIT'
            return 1

        # check if we are asked to stop (time_limit might be reached)
        if stop_event and stop_event.isSet():
            msg = 'Time limit {0} reached, no further operation'\
                  .format(time.strftime('%m/%d/%Y %H:%M', module.time_limit))
            module.log(msg)
            OUTPUT.append('    ' + msg)
            return -1

        # check the operation progress, wait the completion and set the status
        ret = nim_wait_migvios(module, vios)
        if ret == 0:
            if vios == vios1:
                module.status[vios_key] = 'SUCCESS-UPGR1'
            else:
                module.status[vios_key] = 'SUCCESS-UPGR2'
        elif ret == -1:
            # timed out
            if vios == vios1:
                module.status[vios_key] = 'FAILURE-UPGR1-WAIT'
            else:
                module.status[vios_key] = 'FAILURE-UPGR2-WAIT'
            return 1
        else:
            if vios == vios1:
                module.status[vios_key] = 'FAILURE-UPGR1'
            else:
                module.status[vios_key] = 'FAILURE-UPGR2'
            return 1

    return 0


# TODO: test nim_migvios function
def nim_migvios(module, vios):
    """
    Execute the 'nim -o migvios' command against the specified vios

    args:
        module   the Ansible module
        vios     the VIOS to run the command against

    module.param used:
        action              (for logging only)
        backup_prefix       (optional) to build the name of the backup
        spot_prefix         (mandatory) to build the name of the spot
        mksysb_prefix       (mandatory) to build the name of the mksysb
        bosinst_data_prefix (mandatory) to build the name of the bosinst_data
        boot_client         (mandatory) <yes|no> does the client need to be booted
        resolv_conf         (mandatory) the resolv_conf NIM resource
        time_limit          (not supported yet)

    return:
        ret      the return code of the command
    """
    global CHANGED
    global OUTPUT

    OUTPUT.append('    Start upgrade for VIOS: {0}'.format(vios))

    # get the backup name
    if module.params['backup_prefix']:
        backup_name = '{0}_{1}'.format(module.params['backup_prefix'], vios)
    elif 'backup' in module.nim_node['nim_vios'][vios]:
        backup_name = module.nim_node['nim_vios'][vios]['backup']['name']
    else:
        backup_name = 'ios_backup_{0}'.format(vios)
        msg = 'backup_prefix is missing, using default:"{0}"'.format(backup_name)
        module.log(msg)
        OUTPUT.append('    ' + msg)

    # nim -o migvios
    #     -a mk_image=yes
    #     -a boot_client=<yes|no>
    #     -a resolv_conf=<resolv_conf>
    #     -a ios_backup=ios_backup_<vios>
    #     -a spot=ios_mksysb_spot_<vios>
    #     -a ios_mksysb=ios_mksysb_<vios>
    #     -a bosinst_data=bosinst_data_<vios>
    #     <vios>
# TODO: nim -o migvios -a debug possible value? set internally or from playbook?
    # TBC: -a time_limit is not supported yet
    cmd = 'nim -o migvios -a mk_image=yes'\
          ' -a boot_client={1} -a resolv_conf={2} -a ios_backup={3}'\
          ' -a spot={4}_{0} -a ios_mksysb={5}_{0} -a bosinst_data={6}_{0} {0}'\
          .format(vios,
                  module.params['boot_client'],
                  module.params['resolv_conf'],
                  backup_name,
                  module.params['spot_prefix'],
                  module.params['mksysb_prefix'],
                  module.params['bosinst_data_prefix'])

    # TBC - Begin: Uncomment for testing without effective migvios operation
    # OUTPUT.append('Warning: testing without effective migvios command')
    # OUTPUT.append('NIM Command: {0} '.format(cmd))
    # ret = 0
    # sleep(30)
    # if 'backup' in module.nim_node['nim_vios'][vios]:
    #     module.nim_node['nim_vios'][vios]['backup']['name'] = backup_name
    # else:
    #     module.nim_node['nim_vios'][vios]['backup'] = {0}
    #     module.nim_node['nim_vios'][vios]['backup']['name'] = backup_name
    # msg = 'VIOS {0} upgrade successfully initiated'.format(vios)
    # module.log(msg)
    # OUTPUT.append('    ' + msg)
    # CHANGED = True
    # return ret
    # TBC - End

    (ret, std_out, std_err) = exec_cmd(cmd, module, shell=True)

    if ret != 0:
        module.log('NIM Command: {0} failed ret={1}: {2} {3}'
                   .format(cmd, ret, std_out, std_err))
        OUTPUT.append('    Failed to initiate the upgrade of VIOS {0} with NIM: {1}'
                      .format(vios, std_err))
    else:
        if 'backup' in module.nim_node['nim_vios'][vios]:
            module.nim_node['nim_vios'][vios]['backup']['name'] = backup_name
        else:
            module.nim_node['nim_vios'][vios]['backup'] = {}
            module.nim_node['nim_vios'][vios]['backup']['name'] = backup_name
        msg = 'VIOS {0} upgrade successfully initiated'.format(vios)
        module.log(msg)
        OUTPUT.append('    ' + msg)
        CHANGED = True

    return ret


# TODO: test nim_check_migvios function
def nim_wait_migvios(module, vios):
    """
    Wait for the migvios to finish for the specified VIOS

    args:
        module  the Ansible module
        vios    the VIOS to wait for

    return:
        -1 if timed out,
        0  if migvios succeeded,
        1  if migvios failed,
        2  if internal or command error,
    """
    global CHANGED
    global OUTPUT
    global DEBUG_DATA

    module.log('Waiting completion of migvios on {0}...'
               .format(vios))

    cmd = 'LC_ALL=C lsnim -a info -a Cstate -a Cstate_result'\
          ' -a Mstate -a prev_state {0}'.format(vios)

# TODO: can we reduce the timeout (3 hours without states change)?
    # Time out if nim states do not change for more than 3 hours
    # check every 30 seconds
    # log debug every state change or every 5 minutes
    # (360 * 30s = 180 min)
    _TIMEOUT_NIMSTATE = 360 * 30
    wait_time = _TIMEOUT_NIMSTATE
    prev_states = {}
    curr_states = {}
    while wait_time >= 0:
        time.sleep(30)
        wait_time -= 30

        # TODO: remove time_limit for wait migvios? no limit there.
        #           only timeout when no nim states progress for a long time
        # if time_limit is not None and time.localtime(time.time()) >= time_limit:
        #     msg = 'Time limit {0} reached, no further operation'\
        #           .format(time_limit_str)
        #     module.log(msg)
        #     OUTPUT.append('    ' + msg)
        #     return -1

        (ret, std_out, std_err) = exec_cmd(cmd, module, debug_data=False, shell=True)
        if ret != 0:
            msg = 'Failed to get the NIM state for {0}: {1} {2}'\
                  .format(vios, std_out, std_err)
            module.log(msg)
            OUTPUT.append('    ' + msg)
            return 2

        if len(curr_states) >= 0:
            prev_states = curr_states.copy()
            curr_states = {}

# TODO: Should we also get NIM 'info' state to trace migvios progress in NIM?
        # Retrieve the NIM states
        # <vios>:
        #    Cstate = ready for a NIM operation
        #    prev_state = customization is being performed
        #    Mstate = ready for use
        #    Cstate_result = success
        for line in std_out.split('\n'):
            line = line.rstrip()
            match_key = re.match(r"^\s+(\S+)\s*=\s*(\S+)", line)
            if match_key:
                curr_states[match_key.group(1)] = match_key.group(2)
                continue

        if len(curr_states) <= 0:
            msg = 'Failed to retrieve NIM states for {0} from lsnim output'.format(vios)
            module.log(msg)
            module.log('cmd {0} stdout: \n{1}'.format(' '.join(cmd), std_out))
            OUTPUT.append('    ' + msg)
            return 2
        elif curr_states == prev_states:
            if wait_time % 300 == 0:
                # log only every 5 minutes
                msg = 'VIOS {0}, waiting migvios completion... {1} minute(s)'\
                      .format(vios, wait_time / 60)
                module.log(msg)
            continue

        # NIM states have changed
        wait_time = _TIMEOUT_NIMSTATE
        module.debug('VIOS {0}, NIM states: \n{1}'.format(vios, std_out))

# TODO: can we have Cstate_result != 'success' and the migvios is not finished? should we wait?
        if curr_states['Cstate_result'] != 'success':
            msg = 'VIOS {0} migration failed, NIM states:'.format(vios)
            module.log(msg)
            module.log(curr_states)
            OUTPUT.append('    ' + msg)
            OUTPUT.append(map(lambda x: '      ' + str(x), std_out.split('\n')))
            return 1

        # Check if it's the end of the operation
        if curr_states['Mstate'] != 'ready for use' and \
           curr_states['Cstate'] != 'ready for a NIM operation' and \
           curr_states['prev_state'] != 'customization is being performed':
            continue

        msg = 'VIOS {0} successfully upgraded'.format(vios)
        module.log(msg)
        OUTPUT.append('    ' + msg)
        CHANGED = True
        return 0

    msg = 'VIOS {0} upgrade shown no progress for {1} hours, NIM state:'\
          .format(vios, _TIMEOUT_NIMSTATE % 3600)
    module.log(msg)
    OUTPUT.append('    ' + msg)
    OUTPUT.append(map(lambda x: '      ' + str(x), std_out.split('\n')))
    return -1


###################################################################################

def main():
    global DEBUG_DATA
    global CHANGED
    global OUTPUT

    MODULE = AnsibleModule(
        argument_spec=dict(
            # description=dict(required=False, type='str'),

            # IBM automation generic attributes
            targets=dict(required=True, type='str'),
            action=dict(choices=['backup', 'view_backup', 'restore_backup',
                                 'upgrade_restore', 'all'],
                        required=True, type='str'),
            time_limit=dict(required=False, type='str'),
            vars=dict(required=False, type='dict'),
            vios_status=dict(required=False, type='dict'),
            nim_node=dict(required=False, type='dict'),
            # niminfo settings
            email=dict(required=False, type='str'),

            # backup operation
            location=dict(required=False, type='str'),
            backup_prefix=dict(required=False, type='str'),
            force=dict(choices=['yes', 'no'], required=False, type='str', default='no'),

            # viosbr view
            # backup_prefix=dict(required=False, type='str'),

            # viosbr restore operation
            # backup_prefix=dict(required=False, type='str'),
            # force=dict(choices=['yes', 'no'], required=False, type='str'),
            # viosbr_flags=dict(choices=['validate', 'inter', 'force'],
            #                   required=False, type='str'),

            # migvios operation
            # backup_prefix=dict(required=False, type='str'),
            boot_client=dict(choices=['yes', 'no'], required=False, type='str', default='no'),
            resolv_conf=dict(required=False, type='str'),
            spot_prefix=dict(required=False, type='str'),
            mksysb_prefix=dict(required=False, type='str'),
            bosinst_data_prefix=dict(required=False, type='str'),

            # TODO: nim_migvios_setup command not supported yet, remove this section
            # nim_migvios_setup command (Not supported yet)
            # file_system   # empty => default /export/nim
            # volume_group  # empty => default rootvg
            # disk_name     # empty => next available disk
            # device        # empty => /dev/cd0
            # sys_backup    # yes/no => disable the backup image creation
            # args for:
            # -F : Disables the creation of the file system.
            # -S : Disables the creation of the SPOT resource.
            # -v :  Enables verbose debug output during command execution.

        ),
        required_if=[
            ['action', ['all', 'upgrade_restore'],
                       ['resolv_conf', 'spot_prefix',
                        'mksysb_prefix', 'bosinst_data_prefix']],
        ],
    )

    # =========================================================================
    # Get Module params
    # =========================================================================
    MODULE.status = {}
    MODULE.targets = []
    MODULE.nim_node = {}
    nb_error = 0

    # build a time structure for time_limit attribute,
    MODULE.time_limit = None
    if MODULE.params['time_limit']:
        match_key = re.match(r"^\s*\d{2}/\d{2}/\d{4} \S*\d{2}:\d{2}\s*$",
                             MODULE.params['time_limit'])
        if match_key:
            time_limit = time.strptime(MODULE.params['time_limit'], '%m/%d/%Y %H:%M')
            MODULE.time_limit = time_limit
        else:
            msg = 'Malformed time limit "{0}", please use mm/dd/yyyy hh:mm format.'\
                  .format(MODULE.params['time_limit'])
            MODULE.fail_json(msg=msg)

    MODULE.debug('*** START NIM UPGRADE VIOS OPERATION ***')

    OUTPUT.append('Upgradeios operation for {0}'.format(MODULE.params['targets']))
    MODULE.log('Action {0} for {1} targets'
               .format(MODULE.params['action'], MODULE.params['targets']))

    # =========================================================================
    # build NIM node info (if needed)
    # =========================================================================
    if MODULE.params['nim_node']:
        MODULE.nim_node = MODULE.params['nim_node']
        MODULE.log('Using previous nim_node: {0}'.format(MODULE.nim_node))

    if 'nim_vios' not in MODULE.nim_node:
        MODULE.nim_node['nim_vios'] = get_nim_clients_info(MODULE, 'vios')
    MODULE.debug('NIM VIOS: {0}'.format(MODULE.nim_node['nim_vios']))

    ret = check_vios_targets(MODULE, MODULE.params['targets'])
    if not ret:
        msg = 'Empty target list'
        OUTPUT.append(msg)
        MODULE.warn(msg + ': {0}'.format(MODULE.params['targets']))

    else:
        MODULE.targets = ret
        OUTPUT.append('Targets list:{0}'.format(MODULE.targets))
        MODULE.debug('Target list: {0}'.format(MODULE.targets))

        nim_set_infofile(MODULE)

        if MODULE.params['action'] == 'backup'\
                or MODULE.params['action'] == 'all':
            nim_backup(MODULE)

        if MODULE.params['action'] == 'view_backup'\
                or MODULE.params['action'] == 'restore_backup'\
                or MODULE.params['action'] == 'all':
            nim_viosbr(MODULE)

        if MODULE.params['action'] == 'upgrade_restore'\
                or MODULE.params['action'] == 'all':
            nim_migvios_all(MODULE)

        # Prints status for each targets
        msg = 'NIM upgradeios {0} operation status:'.format(MODULE.params['action'])
        if MODULE.status:
            OUTPUT.append(msg)
            MODULE.log(msg)
            for vios_key in MODULE.status:
                OUTPUT.append('    {0} : {1}'.format(vios_key, MODULE.status[vios_key]))
                MODULE.log('    {0} : {1}'.format(vios_key, MODULE.status[vios_key]))
                if not re.match(r"^SUCCESS", MODULE.status[vios_key]):
                    nb_error += 1
        else:
            MODULE.log(msg + ' MODULE.status table is empty')
            OUTPUT.append(msg + ' Error getting the status')
            MODULE.status = MODULE.params['vios_status']  # can be None

        # Prints a global result statement
        if nb_error == 0:
            msg = 'NIM upgradeios {0} operation succeeded'\
                  .format(MODULE.params['action'])
            OUTPUT.append(msg)
            MODULE.log(msg)
        else:
            msg = 'NIM upgradeios {0} operation failed: {1} errors'\
                  .format(MODULE.params['action'], nb_error)
            OUTPUT.append(msg)
            MODULE.log(msg)

    # =========================================================================
    # Exit
    # =========================================================================
    if nb_error == 0:
        MODULE.exit_json(
            changed=CHANGED,
            msg=msg,
            targets=MODULE.targets,
            nim_node=MODULE.nim_node,
            debug_output=DEBUG_DATA,
            output=OUTPUT,
            status=MODULE.status)

    MODULE.fail_json(
        changed=CHANGED,
        msg=msg,
        targets=MODULE.targets,
        nim_node=MODULE.nim_node,
        debug_output=DEBUG_DATA,
        output=OUTPUT,
        status=MODULE.status)


if __name__ == '__main__':
    main()
