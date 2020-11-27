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
module: nim_viosupgrade
short_description: Use NIM to upgrade VIOS(es) with the viosupgrade tool from a NIM master.
description:
- Uses the Network Installation Management (NIM) to performs the operations of backing up the
  virtual and logical configuration data, installing the specified image, and restoring the virtual
  and logical configuration data of the Virtual I/O Server (VIOS) from the NIM master.
- The installation is a new and complete installation using the provided VIOS image, any customized
  configurations that might exist on the currently running system before the installation starts
  (including the timezone) are not included in the new installation image.
version_added: '2.9'
requirements:
- AIX >= 7.2 TL3
- Python >= 2.7
- ios_mksysb VIOS level >= 3.1.0.0
- 'Privileged user with authorizations: B(aix.system.install,aix.system.nim.config.server)'
options:
  action:
    description:
    - Specifies the operation to perform.
    - C(get_status) to get the status of an ongoing upgrade operation.
    - C(bosinst) to perform a new and fresh installation on the current rootvg disk.
    - C(altdisk) to perform a new installation on the alternative disk. The current rootvg disk on
      the VIOS partition is not impacted by this installation. The VIOS partition that has the
      current rootvg disk, remains in the running state during the installation of the alternative
      disk.
    type: str
    choices: [ altdisk, bosinst, get_status ]
    required: true
  targets:
    description:
    - Specifies the list of VIOSes NIM targets to update.
    - Either I(targets) or I(target_file) must be specified.
    - For an SSP cluster, the viosupgrade command must be run on individual nodes. Out of the B(n)
      number of nodes in the SSP cluster, maximum B(n-1) nodes can be upgraded at the same time.
      Hence, you must ensure that at least one node is always active in the cluster and is not part
      of the upgrade process.
    type: list
    elements: str
  target_file:
    description:
    - Specifies the file name that contains the list of VIOS nodes.
    - Either I(targets) or I(target_file) must be specified.
    - The values and fields in the file must be specified in a particular sequence and format. The
      details of the format are specified in the B(/usr/samples/nim/viosupgrade.inst) file and they
      are comma-separated. The maximum number of nodes that can be installed through the -f option
      is 30.
    - The VIOS images are installed on the nodes simultaneously.
    - For an SSP cluster, the viosupgrade command must be run on individual nodes. Out of the B(n)
      number of nodes in the SSP cluster, maximum B(n-1) nodes can be upgraded at the same time.
      Hence, you must ensure that at least one node is always active in the cluster and is not part
      of the upgrade process.
    - Only the I(action) and I(preview) parameters will be considered while others should be
      provided in file.
    type: str
  viosupgrade_params:
    description:
    - Specifies the parameters for the viosupgrade command in a dictionary of disctionaries.
    - The keys of this dictionary can be the target name or the specific key B('all'). Then
      associated parameters will apply to the target or all of them. When I(target_file) is
      specified, then you must use the key B('all').
    - When building the viosugrade command, it will look first if the parameter is present for the
      target then into the B('all') section.
    - Valid keys are the follwoing.
    - I(ios_mksysb), specifies the ios_mksysb resource name on the NIM Master server for the
      specified VIOS installation.
    - I(spotname), when C(action=bosinst) it specifies the resource object name of the Shared
      Product Object Tree (SPOT) for NIM installation.
    - I(rootvg_clone_disk), mandatory if C(action=altdisk) this colon-separated list specifies
      alternative disks to install the selected VIOS image, current rootvg disk on the VIOS
      partition is not impacted by this installation.
      When C(action=bosinst), the provided disks are used to clone the current rootvg. After the
      completion of the migration process, the current rootvg disk is installed with the provided
      image. The provided disks are at the VIOS level before the migration process.
    - I(skip_rootvg_cloning), when C(action=bosinst) boolean (default=no) to skip the cloning of
      current rootvg disks to alternative disks and continues with the VIOS installation on the
      current rootvg disk.
    - I(rootvg_install_disk), when C(action=bosinst) this colon-separated list specifies new rootvg
      disks where the specified image must be installed instead of the existing rootvg disks, one
      and only one of I(rootvg_clone_disk) or I(rootvg_install_disk) or I(skip_rootvg_cloning) must
      be specified.
    - I(backup_file_resource), specifies the resource name of the VIOS configuration backup file.
    - I(resources), specifies the configuration resources to be applied after the installation,
      valid values are resolv_conf, script, fb_script, file_res, image_data, and log.
    - I(manage_cluster), boolean (default=yes) that specifies that cluster-level backup and restore
      operations are performed, mandatory for the VIOS that is part of an SSP cluster.
    - I(preview), boolean (default=false) that specifies only validation of VIOS hosts readyness for
      installation is performed, can be used for preview of the installation image only.
    type: dict
    required: false
  vios_status:
    description:
    - Specifies the result of a previous operation.
    - If set then the I(vios_status) of a target tuple must contain C(SUCCESS) to attempt update.
    - If no I(vios_status) value is found for a tuple, then returned I(status) for this tuple is set
      to C(SKIPPED-NO-PREV-STATUS).
    type: dict
  nim_node:
    description:
    - Allows to pass along NIM node info from a task to another so that it discovers NIM info only
      one time for all tasks.
    type: dict
notes:
  - See IBM documentation about requirements for the viosupgrade command at
    U(https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/v_commands/viosupgrade.html).
  - You can refer to the IBM documentation for additional information on the NIM concept at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/install/nim_concepts.html),
  - The viosupgrade command on NIM server is supported from IBM AIX 7.2 with Technology Level 3, or
    later.
  - For NIM bosinst method of installation, supported current VIOS levels are 2.2.6.30, or later.
  - If the altinst_rootvg or old_rootvg disks are already available in the VIOS, you must rename
    them.
  - The disks that are specified for the VIOS installation must not be in use.
  - In an SSP cluster, you must ensure that at least one node is always active in the cluster and is
    not part of the upgrade process.
  - If the viosupgrade command fails to restore all of the mappings, you must manually re-initiate
    the restore operation on the VIOS.
  - If you have installed any additional software on the VIOS apart from what is supplied as part of
    the base VIOS image, the viosupgrade command might fail to restore configurations that are
    related to that software. To manage this scenario, you must create a customized VIOS image with
    the software applications that you might want to include and provide this customized VIOS image
    as an input to the viosupgrade command for installation.
'''

EXAMPLES = r'''
- name: Validate an altdisk viosupgrade, no change on the vios
  nim_viosupgrade:
    action: altdisk
    targets: nimvios01
    viosupgrade_params:
      all:
        resources:              master_net_conf:logdir
        manage_cluster:         False
        preview:                True
      nimvios01:
        ios_mksysb:             vios-3-1-1-0_sysb
        rootvg_clone_disk:      hdisk1
        backup_file_resource:   nimvios01_iosb

- name: Perform an altdisk viosupgrade
  nim_viosupgrade:
    action: altdisk
    targets: nimvios01
    viosupgrade_params:
      all:
        resources:              master_net_conf:logdir
        manage_cluster:         False
        preview:                False
      nimvios01:
        ios_mksysb:             vios-3-1-1-0_sysb
        rootvg_clone_disk:      hdisk1
        backup_file_resource:   nimvios01_iosb

- name: Wait for up to an hour for the viosupgrade status to complete
  nim_viosupgrade:
    action: get_status
    targets: nimvios01
  register: result
  until: result.status['nimvios01'] != 'ONGOING'
  retries: 30
  delay: 120

- name: Validate an bosinst viosupgrade, no change on the vios
  nim_viosupgrade:
    action: bosinst
    targets: nimvios02
    viosupgrade_params:
      all:
        resources:              master_net_conf:logdir:my_filebackup_res
        manage_cluster:         False
        preview:                True
      nimvios02:
        ios_mksysb:             vios-3-1-1-0_sysb
        spotname:               vios-3-1-1-0_spot
        rootvg_install_disk:    "hdisk1:hdisk2"
        skip_rootvg_cloning:    False
        backup_file_resource:   nimvios02_iosb
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
targets:
    description: List of NIM client actually targeted for the operation.
    returned: always
    type: list
    elements: str
    sample: [vios1, vios2, ...]
status:
    description:
    - Status of the operation for each VIOS C(target). It can be empty, SUCCESS or FAILURE.
    - When C(target_file) is set, then the key is 'all'.
    returned: always
    type: dict
    sample: "{ vios1: 'SUCCESS', vios2: 'FAILURE' }"
cmd:
    description: Command executed.
    returned: If the command was run when C(target_file) is set.
    type: str
stdout:
    description: Standard output of the command.
    returned: If the command was run when C(target_file) is set.
    type: str
stderr:
    description: Standard error of the command.
    returned: If the command was run when C(target_file) is set.
    type: str
nim_node:
    description: NIM node info. It can contains more information if passed as option I(nim_node).
    returned: always
    type: dict
    contains:
        vios:
            description: List of VIOS NIM resources.
            returned: always
            type: dict
    sample:
        "nim_node": {
            "vios": {
                "vios1": {
                    "Cstate": "ready for a NIM operation",
                    "Cstate_result": "success",
                    "Mstate": "currently running",
                    "cable_type1": "N/A",
                    "class": "management",
                    "connect": "nimsh",
                    "cpuid": "00F600004C00",
                    "if1": "master_net vios1.aus.stglabs.ibm.com 0",
                    "mgmt_profile1": "p8-hmc 1 vios-cec",
                    "netboot_kernel": "64",
                    "platform": "chrp",
                    "prev_state": "alt_disk_install operation is being performed",
                }
            }
        }
meta:
    description: Detailed information on the module execution.
    returned: always
    type: dict
    contains:
        messages:
            description: Details on errors/warnings not related to a specific target vios.
            returned: always
            type: list
            elements: str
        <vios>:
            description: Detailed information on the execution on the target vios. Can be 'all'.
            returned: when target is actually a NIM client
            type: dict
            contains:
                messages:
                    description: Details on errors/warnings.
                    returned: always
                    type: list
                    elements: str
                cmd:
                    description: Command executed.
                    returned: If the command was run.
                    type: str
                stdout:
                    description: Standard output of the command.
                    returned: If the command was run.
                    type: str
                stderr:
                    description: Standard error of the command.
                    returned: If the command was run.
                    type: str
'''

import re
import csv
import socket

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule


def param_one_of(one_of_list, required=True, exclusive=True):
    """
    Check that parameter of one_of_list is defined in module.params dictionary.

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


def refresh_nim_node(module, type):
    """
    Get nim client information of provided type and update nim_node dictionary.

    arguments:
        module  (dict): The Ansible module
        type     (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        none
    """
    global results

    if module.params['nim_node']:
        results['nim_node'] = module.params['nim_node']

    nim_info = get_nim_type_info(module, type)

    if type not in results['nim_node']:
        results['nim_node'].update({type: nim_info})
    else:
        for elem in nim_info.keys():
            if elem in results['nim_node']:
                results['nim_node'][type][elem].update(nim_info[elem])
            else:
                results['nim_node'][type][elem] = nim_info[elem]
    module.debug("results['nim_node'][{0}]: {1}".format(type, results['nim_node'][type]))


def get_nim_type_info(module, type):
    """
    Build the hash of nim client of type=lpar_type defined on the
    nim master and their associated key = value information.

    arguments:
        module      (dict): The Ansible module
        type     (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        info_hash   (dict): information from the nim clients
    """
    global results

    cmd = ['lsnim', '-t', type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Cannot get NIM Client information. Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.log(msg)
        results['msg'] = msg
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)

    info_hash = build_dict(module, stdout)

    return info_hash


def build_dict(module, stdout):
    """
    Build dictionary with the stdout info

    arguments:
        module  (dict): The Ansible module
        stdout   (str): stdout of the command to parse
    returns:
        info    (dict): NIM info dictionary
    """
    info = {}

    for line in stdout.rstrip().splitlines():
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info[obj_key] = {}
            continue
        rmatch_attr = re.match(r"^\s+(\S+)\s+=\s+(.*)$", line)
        if rmatch_attr:
            info[obj_key][rmatch_attr.group(1)] = rmatch_attr.group(2)
            continue
    return info


def check_vios_targets(module, targets):
    """
    Check the list of VIOS targets.
    Check that each target can be reached.

    A target name can be of the following form:
        vios1,vios2 or vios3

    arguments:
        module  (dict): the Ansible module
        targets (list): list of tuple of NIM name of vios machine
    return:
        vios_list    (list): The list of the existing vios matching the target list
    """
    global results

    vios_list = []

    # Build targets list
    for elems in targets:
        module.debug('Checking elems: {0}'.format(elems))

        tuple_elts = list(set(elems.replace(" ", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "").split(',')))
        tuple_len = len(tuple_elts)
        module.debug('Checking tuple: {0}'.format(tuple_elts))

        if tuple_len == 0:
            continue

        if tuple_len > 2:
            msg = 'Malformed VIOS targets \'{0}\'. Tuple {1} should be a 1 or 2 elements.'.format(targets, elems)
            module.log(msg)
            results['msg'] = msg
            module.exit_json(**results)

        error = False
        for elem in tuple_elts:
            if len(elem) == 0:
                msg = 'Malformed VIOS targets tuple {0}: empty string.'.format(elems)
                module.log(msg)
                results['msg'] = msg
                module.exit_json(**results)

            # check vios not already exists in the target list
            if elem in vios_list:
                msg = 'Malformed VIOS targets \'{0}\': Duplicated VIOS: {1}'.format(targets, elem)
                module.log(msg)
                results['msg'] = msg
                error = True
                continue

            # check vios is knowed by the NIM master - if not ignore it
            if elem not in results['nim_node']['vios']:
                msg = "VIOS {0} is not client of the NIM master, tuple {1} will be ignored".format(elem, elems)
                module.log(msg)
                results['meta']['messages'].append(msg)
                error = True
                continue

            # Get VIOS interface info in case we need to connect using c_rsh
            if 'if1' not in results['nim_node']['vios'][elem]:
                msg = "VIOS {0} has no interface set, check its configuration in NIM, tuple {1} will be ignored".format(elem, elems)
                module.log(msg)
                results['meta']['messages'].append(msg)
                error = True
                continue
            fields = results['nim_node']['vios'][elem]['if1'].split(' ')
            if len(fields) < 2:
                msg = "VIOS {0} has no hostname set, check its configuration in NIM, tuple {1} will be ignored".format(elem, elems)
                module.log(msg)
                results['meta']['messages'].append(msg)
                error = True
                continue
            results['nim_node']['vios'][elem]['hostname'] = fields[1]

        if not error:
            vios_list.extend(tuple_elts)

    return vios_list


def viosupgrade_query(module, params_flags):
    """
    Query to get the status of the upgrade .

    arguments:
        module        (dict): The Ansible module
        params_flags  (dict): Supported parameter flags.
    module.param used:
        target_file   (optional) filename with targets info
        targets       (required if not target_file)
        viosupgrade_params  (required)
    note:
        Set the upgrade status in results['status'][vios] or results['status']['all'].
    return:
        ret     (int) the number of error
    """
    global results
    ret = 0

    # viosupgrade -q { [-n hostname | -f filename] }
    cmd = ['/usr/sbin/viosupgrade', '-q']
    if module.params['target_file']:
        cmd += ['-f', module.params['target_file']]

        rc, stdout, stderr = module.run_command(cmd)

        results['cmd'] = ' '.join(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))

        if rc == 0:
            msg = 'viosupgrade get status successful.'
        else:
            msg = 'viosupgrade get status command failed with rc: {0}'.format(rc)
            ret += 1
        module.log(msg)
        results['meta']['messages'].append(msg)
    else:
        for vios in module.params['targets']:
            # get the fqdn hostname because short hostname can match several NIM objects
            # and require user input to select the right one.
            target_fqdn = socket.getfqdn(vios)
            cmd += ['-n', target_fqdn]
            rc, stdout, stderr = module.run_command(cmd)

            results['meta'][vios]['cmd'] = ' '.join(cmd)
            results['meta'][vios]['stdout'] = stdout
            results['meta'][vios]['stderr'] = stderr
            module.log('stdout: {0}'.format(stdout))
            module.log('stderr: {0}'.format(stderr))

            if rc == 0:
                # Parse stdout to get viosupgrade result
                info_hash = build_dict(module, stdout)
                if vios in info_hash and 'Cstate' in info_hash[vios] and info_hash[vios]['Cstate'] == 'ready for a NIM operation':
                    if 'Cstate_result' in info_hash[vios] and info_hash[vios]['Cstate_result'] == 'success':
                        msg = 'viosupgrade command successful. See results or meta data "stdout".'
                        results['status'][vios] = 'SUCCESS'
                    else:
                        msg = 'viosupgrade command might have failed. See meta data "stdout" and log on NIM master.'
                        results['status'][vios] = 'FAILURE'
                else:
                    msg = 'viosupgrade command ongoing. See meta data "stdout" and log on NIM master.'
                    results['status'][vios] = 'ONGOING'
            else:
                msg = 'Command failed with rc: {0}'.format(rc)
                results['status'][vios] = 'FAILURE'
                ret += 1
            module.log(msg)
            results['meta'][vios]['messages'].append(msg)
    return ret


def viosupgrade(module, params_flags):
    """
    Upgrade each VIOS.

    arguments:
        module        (dict): The Ansible module
        params_flags  (dict): Supported parameter flags.
    module.param used:
        action              (required)
        target_file         (optional) filename with targets info
        targets             (required if not target_file)
        viosupgrade_params  (required)
    note:
        Set the upgrade status in results['status'][vios] or results['status']['all'].
    return:
        ret     (int) the number of error
    """
    global results
    ret = 0

    cmd = ['/usr/sbin/viosupgrade']
    cmd += ['-t', module.params['action']]

    # viosupgrade -t {bosinst | altdisk} -f filename [-v]
    if module.params['target_file']:
        # check parameters
        for key in module.params['viosupgrade_params']['all'].keys():
            if key not in params_flags['file']:
                msg = 'key \'{0}\' is not valid, supported keys for viosupgrade_params are: {1}'.format(key, params_flags['file'])
                ret += 1
                module.log(msg)
                results['meta']['messages'].append(msg)
        if ret != 0:
            results['status']['all'] = 'FAILURE'
            return ret

        cmd += ['-f', module.params['target_file']]

        for key, flag in params_flags['file'].items():
            if key in module.params['viosupgrade_params']['all']:
                if module.params['viosupgrade_params']['all'][key]:
                    if isinstance(module.params['viosupgrade_params']['all'][key], (bool)) and module.params['viosupgrade_params']['all'][key]:
                        cmd += [flag]
                    else:
                        cmd += [flag, module.params['viosupgrade_params']['all'][key]]

        rc, stdout, stderr = module.run_command(cmd)

        results['changed'] = True  # don't really know
        results['cmd'] = ' '.join(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))

        if rc == 0:
            msg = 'viosupgrade command successful'
            results['status']['all'] = 'SUCCESS'
        else:
            msg = 'Command failed with rc: {0}'.format(rc)
            results['status']['all'] = 'FAILURE'
            ret += 1
        module.log(msg)
        results['meta']['messages'].append(msg)
        return ret

    # check parameters
    for vios in module.params['viosupgrade_params'].keys():
        for key in module.params['viosupgrade_params'][vios].keys():
            if key not in params_flags[module.params['action']]:
                msg = 'key \'{0}\' is not valid, supported keys for viosupgrade_params for action={1} are: {2}'\
                      .format(key, module.params['action'], params_flags[module.params['action']].keys())
                ret += 1
                module.log(msg)
                results['meta']['messages'].append(msg)
        if ret != 0:
            results['status'][vios] = 'FAILURE'
            return ret

    # Check previous status if known
    if module.params['vios_status'] is not None and module.params['vios_status']:
        for vios in module.params['targets']:
            if vios in module.params['vios_status'] and 'SUCCESS' not in module.params['vios_status'][vios]:
                msg = '{0} VIOS skipped (vios_status: {1})'.format(vios, module.params['vios_status'][vios])
                module.log(msg)
                results['meta'][vios]['messages'].append(msg)
                results['status'][vios] = module.params['vios_status'][vios]
                continue
            for key in module.params['vios_status']:
                if vios in key:
                    if 'SUCCESS' not in module.params['vios_status'][key]:
                        msg = '{0} VIOS skipped (vios_status[{1}: {2})'.format(vios, key, module.params['vios_status'][key])
                        module.log(msg)
                        results['meta'][vios]['messages'].append(msg)
                        results['status'][vios] = module.params['vios_status'][key]
                        break
            else:
                msg = '{0} vios skipped (no previous status found)'.format(vios)
                module.log('[WARNING] ' + msg)
                results['meta'][vios]['messages'].append(msg)
                results['status'][vios] = 'SKIPPED-NO-PREV-STATUS'

    # viosupgrade -t bosinst -n hostname -m mksysbname -p spotname
    #             {-a RootVGCloneDisk: ... | -r RootVGInstallDisk: ...| -s}
    #             [-b BackupFileResource] [-c] [-e Resources: ...] [-v]
    # viosupgrade -t altdisk -n hostname -m mksysbname
    #             -a RootVGCloneDisk
    #             [-b BackupFileResource] [-c] [-e Resources: ...] [-v]
    for vios in module.params['targets']:
        # get the fqdn hostname because short hostname can match several NIM objects
        # and require user input to select the right one.
        target_fqdn = socket.getfqdn(vios)
        cmd += ['-n', target_fqdn]

        for key, flag in params_flags[module.params['action']].items():
            if vios in module.params['viosupgrade_params'] and key in module.params['viosupgrade_params'][vios]:
                if module.params['viosupgrade_params'][vios][key]:
                    if isinstance(module.params['viosupgrade_params'][vios][key], (bool)) and module.params['viosupgrade_params'][vios][key]:
                        cmd += [flag]
                    else:
                        cmd += [flag, module.params['viosupgrade_params'][vios][key]]
            elif key in module.params['viosupgrade_params']['all']:
                if module.params['viosupgrade_params']['all'][key]:
                    if isinstance(module.params['viosupgrade_params']['all'][key], (bool)) and module.params['viosupgrade_params']['all'][key]:
                        cmd += [flag]
                    else:
                        cmd += [flag, module.params['viosupgrade_params']['all'][key]]

        # run the command
        rc, stdout, stderr = module.run_command(cmd)

        results['meta'][vios]['cmd'] = ' '.join(cmd)
        results['meta'][vios]['stdout'] = stdout
        results['meta'][vios]['stderr'] = stderr
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))

        if rc == 0:
            if vios in module.params['viosupgrade_params'] and 'preview' in module.params['viosupgrade_params'][vios] and \
               not module.params['viosupgrade_params'][vios]['preview'] or 'preview' in module.params['viosupgrade_params']['all'] and \
               not module.params['viosupgrade_params']['all']['preview']:
                results['changed'] = True
            msg = 'viosupgrade command successful.'
            results['status'][vios] = 'SUCCESS'
        else:
            msg = 'Command failed with rc: {0}'.format(rc)
            results['status'][vios] = 'FAILURE'
            ret += 1
        results['meta'][vios]['messages'].append(msg)
        module.log(msg)

    return ret


###################################################################################

def main():
    global module
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['altdisk', 'bosinst', 'get_status']),
            vios_status=dict(type='dict'),
            nim_node=dict(type='dict'),
            targets=dict(type='list', elements='str'),
            target_file=dict(type='str'),
            # viosupgrade_params={
            #   all:   { ios_mksysb: 'vios3-1-1-0_mksysb', preview: false, resources: 'my_resolv_conf:my_fb_script'}
            #   vios1: { rootvg_clone_disk: 'hdisk1', 'backup_file_resource': 'vios1_fb'}
            #   vios2: { rootvg_clone_disk: 'hdisk2:hdisk3', 'backup_file_resource': 'vios2_filebackup'}
            viosupgrade_params=dict(type='dict'),
        ),
        mutually_exclusive=[['targets', 'target_file']],
    )

    results = dict(
        changed=False,
        msg='',
        targets=[],
        # cmd='',
        # stdout='',
        # stderr='',
        meta={'messages': []},
        # meta structure will be updated as follow:
        # meta={
        #   'messages': [],
        #   target:{
        #       'messages': [],
        #       'cmd': '',
        #       'stdout': '',
        #       'stderr': '',
        #   }
        # }
        nim_node={},
        status={},
        # status structure will be updated as follow:
        # status={
        #   target_name: 'SUCCESS' or 'FAILURE'
        # }
    )

    params_flags = {
        'file': {'preview': '-v'},
        'bosinst': {'ios_mksysb': '-m', 'spotname': '-p', 'rootvg_clone_disk': '-a',
                    'skip_rootvg_cloning': '-s', 'rootvg_install_disk': '-r',
                    'backup_file_resource': '-b', 'resources': '-e', 'manage_cluster': '-c', 'preview': '-v'},
        'altdisk': {'ios_mksysb': '-m', 'rootvg_clone_disk': '-a',
                    'backup_file_resource': '-b', 'resources': '-e', 'manage_cluster': '-c', 'preview': '-v'},
    }

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    param_one_of(module.params, ['targets', 'target_file'])
    if not module.params['viosupgrade_params']:
        module.params['viosupgrade_params'] = {}
    if not module.params['target_file']:
        if 'all' not in module.params['viosupgrade_params']:
            module.params['viosupgrade_params']['all'] = {}

    # build NIM node info (if needed)
    refresh_nim_node(module, 'vios')

    # get targests and check they are valid NIM clients
    targets = []
    if module.params['target_file']:
        try:
            myfile = open(module.params['target_file'], 'r')
            csvreader = csv.reader(myfile, delimiter=':')
            for line in csvreader:
                targets.append(line[0].strip())
            myfile.close()
        except IOError as e:
            msg = 'Failed to parse file {0}: {1}. Check the file content is '.format(e.filename, e.strerror)
            module.log(msg)
            module.fail_json(**results)
    else:
        targets = module.params['targets']

    results['targets'] = check_vios_targets(module, targets)

    if not results['targets']:
        module.log('Warning: Empty target list.')
        results['msg'] = 'Empty target list, please check their NIM states and they are reacheable.'
        module.exit_json(**results)
    module.debug('Target list: {0}'.format(results['targets']))

    # initialize the results dictionary for targets
    for vios in results['targets']:
        results['status'][vios] = ''
        results['meta'][vios] = {'messages': []}

    # check viosupgrade_params dict keys are in target list (can help debuging issue with playbook)
    if not module.params['target_file']:
        for vios in module.params['viosupgrade_params'].keys():
            if vios != 'all' and vios not in results['targets']:
                msg = 'Info: \'viosupgrade_params\' key \'{0}\' is not in targets list.'.format(vios)
                module.log(msg)
                results['meta']['messages'].append(msg)

    # perfom the operation
    if 'get_status' in module.params['action']:
        viosupgrade_query(module, params_flags)
    else:
        viosupgrade(module, params_flags)

    # set status and exit
    if not results['status']:
        module.log('NIM upgradeios {0} operation: status table is empty'.format(module.params['action']))
        results['meta']['messages'].append('Warning: status table is empty, returning initial vios_status.')
        results['status'] = module.params['vios_status']
        results['msg'] = 'NIM updateios {0} operation completed. See meta data for details.'.format(module.params['action'])
        module.log(results['msg'])
    else:
        target_errored = [key for key, val in results['status'].items() if 'FAILURE' in val]
        if len(target_errored):
            results['msg'] = 'NIM upgradeios {0} operation failed for {1}. See status and meta for details.'.format(module.params['action'], target_errored)
            module.log(results['msg'])
            module.fail_json(**results)
        else:
            results['msg'] = 'NIM upgradeios {0} operation completed. See status and meta for details.'.format(module.params['action'])
            module.log(results['msg'])
            module.exit_json(**results)


if __name__ == '__main__':
    main()
