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
module: nim_vios_alt_disk
short_description: Uses NIM to create/cleanup an alternate rootvg disk of VIOS clients.
description:
- Performs alternate disk copy and cleanup operations through the Network Installation Management
  (NIM) copying the root volume group to an alternate disk or cleaning an existing copy.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorizations: B(aix.system.install,aix.system.nim.config.server)'
options:
  action:
    description:
    - Specifies the operation to perform on the VIOS.
    - Specifies the action to perform.
    - C(alt_disk_copy) to perform and alternate disk copy.
    - C(alt_disk_clean) to cleanup an existing alternate disk copy.
    type: str
    choices: [ alt_disk_copy, alt_disk_clean ]
    required: true
  targets:
    description:
    - Specifies the NIM VIOS clients to perform the action on.
    - Uses a dictionary format, with the key being the VIOS NIM name and the value being the list of
      disks used for the alternate disk copy.
    - When no target disks is specified, the alternate disk copy is performed to only one alternate
      disk even if the rootvg contains multiple disks.
    type: list
    elements: dict
    required: true
  time_limit:
    description:
    - Before starting the action, the actual date is compared to this parameter value; if it is
      greater then the task is stopped.
    - The valid format is C(mm/dd/yyyy hh:mm).
    type: str
  disk_size_policy:
    description:
    - Specifies how to choose the alternate disk when not specified.
    - C(minimize) smallest disk that can be selected.
    - C(upper) first disk found bigger than the rootvg disk.
    - C(lower) disk size less than rootvg disk size but big enough to contain the used PPs.
    - C(nearest) disk size closest to the rootvg disk.
    type: str
    choices: [ minimize, upper, lower, nearest ]
    default: nearest
  force:
    description:
    - Forces removal of any existing alternate disk copy on target disks.
    - Stops any active rootvg mirroring during the alternate disk copy.
    type: bool
    default: no
  vios_status:
    description:
    - Specifies the result of a previous operation.
    - If set then the I(vios_status) of a target tuple must contain C(SUCCESS) to attempt update.
    - If no I(vios_status) value is found for a tuple, then returned I(status) for this tuple is set
      to C(SKIPPED-NO-PREV-STATUS).
    type: dict
  nim_node:
    description:
    - Allows to pass along NIM node info from a previous task to another so that it discovers NIM
      info only one time for all tasks. The current task might update the NIM info it needs.
    type: dict
notes:
  - C(alt_disk_copy) only backs up mounted file systems. Mount all file systems that you want to
    back up.
  - When no target disks is specified, the alternate disk copy is performed to only one alternate
    disk even if the rootvg contains multiple disks.
  - You can refer to the IBM documentation for additional information on the NIM concept and command
    at U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/install/nim_concepts.html),
    U(https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/install/nim_op_alt_disk_install.html).
'''

EXAMPLES = r'''
- name: Perform an alternate disk copy of the rootvg to hdisk1 on nimvios01
  nim_vios_alt_disk:
    action: alt_disk_copy
    targets:
    - nimvios01: [hdisk1]

- name: Perform an alternate disk copy of the rootvg to the smallest disk that can be selected
  nim_vios_alt_disk:
    action: alt_disk_copy
    disk_size_policy: minimize
    targets:
    - nimvios01: []
      nimvios02: []
    - nimvios03: []

- name: Perform a cleanup of any existing alternate disk copy on nimvios01
  nim_vios_alt_disk:
    action: alt_disk_clean
    targets:
    - nimvios01: []
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
status:
    description: Status for each VIOS tuples (dictionary key).
    returned: always
    type: dict
    contains:
        <vios>:
            description: Status of the execution on the <vios>.
            returned: when vios is actually a NIM client
            type: str
            sample: 'SUCCESS-ALTDC'
    sample: "{ vios1: 'SUCCESS-ALTDC', vios2: 'FAILURE-ALTDC wrong rootvg state on vios2' }"
nim_node:
    description: NIM node info.
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
                    "ip": "vios1.aus.stglabs.ibm.com",
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
            description: Details on errors/warnings not related to a specific target.
            returned: always
            type: list
            elements: str
            sample: see below
        <target>:
            description: Detailed information on the execution on the C(target).
            returned: when target is actually a NIM client
            type: dict
            contains:
                messages:
                    description: Details on errors/warnings
                    returned: always
                    type: list
                    elements: str
'''

import re
import time
import string
import socket

from ansible.module_utils.basic import AnsibleModule

results = {}


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - ret     return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

    node = get_target_ipaddr(module, node)

    rcmd = '( LC_ALL=C {0} ); echo rc=$?'.format(' '.join(command))
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    module.debug('exec command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        return (ret, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        ret = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug('exec command rc:{0}, output:{1}, stderr:{2}'.format(ret, stdout, stderr))

    return (ret, stdout, stderr)


def get_target_ipaddr(module, target):
    """
    Find the hostname or IP address in the nim_node dict.
    If not found, get the fqdn of the 2nd field of if1 attribute and save it.

    arguments:
        targets (str): The target name.
    return:
        the target hostname or IP address
        the target name if not found
    """
    global results

    ipaddr = target
    for type in results['nim_node']:
        if target not in results['nim_node'][type]:
            continue
        if 'ip' in results['nim_node'][type][target] and results['nim_node'][type][target]['ip']:
            return results['nim_node'][type][target]['ip']

        if 'if1' in results['nim_node'][type][target]:
            match_if = re.match(r"\S+\s+(\S+)\s+.*$", results['nim_node'][type][target]['if1'])
            if match_if:
                try:
                    ipaddr = socket.getfqdn(match_if.group(1))
                except OSError as exc:
                    module.log('NIM - Error: Cannot get FQDN for {0}: {1}'.format(match_if.group(1), exc))
            else:
                module.debug('Parsing of interface if1 failed, got: \'{0}\''.format(results['nim_node'][type][target]['ip']))
        results['nim_node'][type][target]['ip'] = ipaddr

    return ipaddr


def get_nim_type_info(module, lpar_type):
    """
    Build the hash of nim client of type=lpar_type defined on the
    nim master and their associated key = value information.

    arguments:
        module      (dict): The Ansible module
        lpar_type    (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        info_hash   (dict): information from the nim clients
    """
    global results

    cmd = ['lsnim', '-t', lpar_type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot get NIM {0} client information.'.format(lpar_type)

        module.log('NIM - Error: ' + results['msg'])
        module.log('cmd: {0}'.format(results['cmd']))
        module.log('rc: {0}'.format(rc))
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))
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


def check_vios_targets(module, targets):
    """
    Check the list of VIOS targets.

    A target name can be of the following forms:
        - vios1: [altdisk1]
        - vios1: [altdisk1,altdisk2]
          vios2: [altdisk2]
    altdisk can be an empty list if one wants to use the automatic discovery,
    in which case the first available disk with enough space is used.

    arguments:
        module  (dict): The Ansible module
        targets (list): list of dictionaries of VIOS NIM names and associated alternate disks

    return: True iff all targets are valid NIM VIOS objects and are reachable
    """
    global results

    # Check targets
    for vios_dict in targets:
        if len(vios_dict) > 2:
            msg = 'Malformed VIOS targets {0}. Dictionary should contain 1 or 2 elements.'.format(vios_dict)
            results['meta']['messages'].append(msg)
            module.log('ERROR: ' + msg)
            return False

        for vios in vios_dict:
            # check vios is known by the NIM master - if not ignore it
            # because it can concern another ansible host (nim master)
            if vios not in results['nim_node']['vios']:
                msg = 'VIOS target {0} unknown by the NIM master.'.format(vios)
                results['meta']['messages'].append(msg)
                module.log('ERROR' + msg)
                return False

            # check vios connectivity
            cmd = ['true']
            ret, stdout, stderr = nim_exec(module, vios, cmd)
            if ret != 0:
                module.log('skipping {0}: cannot reach with c_rsh: {1}, {2}, {3}'
                           .format(vios, ret, stdout, stderr))
                return False

    return True


def get_pvs(module, vios):
    """
    Get the list of PVs on the VIOS.

    arguments:
        module  (dict): The Ansible module
        vios     (str): The VIOS name
    return: dictionary with PVs information
    """
    module.debug('get_pvs vios: {0}'.format(vios))

    cmd = ['/usr/ios/cli/ioscli', 'lspv']
    ret, stdout, stderr = nim_exec(module, vios, cmd)
    if ret != 0:
        msg = 'Failed to get the PV list on {0}, lspv returned: {1} {2}'.format(vios, ret, stderr)
        results['meta'][vios]['messages'].append(msg)
        module.log(msg)
        return None

    # NAME             PVID                                 VG               STATUS
    # hdisk0           000018fa3b12f5cb                     rootvg           active
    pvs = {}
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(hdisk\S+)\s+(\S+)\s+(\S+)\s*(\S*)", line)
        if match_key:
            pvs[match_key.group(1)] = {}
            pvs[match_key.group(1)]['pvid'] = match_key.group(2)
            pvs[match_key.group(1)]['vg'] = match_key.group(3)
            pvs[match_key.group(1)]['status'] = match_key.group(4)

    module.debug('List of PVs:')
    for key in pvs.keys():
        module.debug('    pvs[{0}]: {1}'.format(key, pvs[key]))

    return pvs


def get_free_pvs(module, vios):
    """
    Get the list of free PVs on the VIOS.

    arguments:
        module  (dict): The Ansible module
        vios     (str): The VIOS name
    return: dictionary with free PVs information
    """
    global results
    module.debug('get_free_pvs vios: {0}'.format(vios))

    cmd = ['/usr/ios/cli/ioscli', 'lspv', '-free']
    ret, stdout, stderr = nim_exec(module, vios, cmd)
    if ret != 0:
        msg = 'Failed to get the list of free PVs on {0}: {1}'.format(vios, stderr)
        results['meta'][vios]['messages'].append(msg)
        module.log(msg)
        return None

    # NAME            PVID                                SIZE(megabytes)
    # hdiskX          none                                572325
    free_pvs = {}
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(hdisk\S+)\s+(\S+)\s+(\S+)", line)
        if match_key:
            free_pvs[match_key.group(1)] = {}
            free_pvs[match_key.group(1)]['pvid'] = match_key.group(2)
            free_pvs[match_key.group(1)]['size'] = int(match_key.group(3))

    module.debug('List of available PVs:')
    for key in free_pvs.keys():
        module.debug('    free_pvs[{0}]: {1}'.format(key, free_pvs[key]))

    return free_pvs


def find_valid_altdisk(module, params, action, vios_dict, vios_key, rootvg_info, altdisk_op_tab):
    """
    Find a valid alternate disk that:
    - exists,
    - is not part of a VG
    - with a correct size
    and so can be used.

    Sets the altdisk_op_tab accordingly:
        altdisk_op_tab[vios_key] = "FAILURE-ALTDC <error message>"
        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"

    arguments:
        module          (dict): The Ansible module
        params          (dict): The parameters for the provided action
        action           (str): The action to perform
        vios_dict       (dict): The list of VIOS dictionary with associated list of hdisks
        vios_key         (str): The key for altdisk_op_tab status dicionary
        rootvg_info     (dict): The rootvg information gathered with check_rootvg
        altdisk_op_tab  (dict): The operation status

    return:
        0 if alternate disk is found
        1 otherwise
    """
    global results

    pvs = {}
    used_pv = []

    for vios, hdisks in vios_dict.items():
        module.debug('find_valid_altdisk action: {0}, vios: {1}, hdisks: {2}, vios_key: {3}'
                     .format(action, vios, hdisks, vios_key))

        err_label = "FAILURE-ALTDC"

        # check value is a list
        if not isinstance(hdisks, list):
            msg = 'value is not a list for {0}'.format(vios)
            altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
            results['meta'][vios]['messages'].append('Target dictionary ' + msg)
            module.log('ERROR: Target dictionary ' + msg)
            return 1

        # check rootvg
        if rootvg_info[vios]["status"] != 0:
            msg = 'wrong rootvg state on {0}'.format(vios)
            altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
            results['meta'][vios]['messages'].append(msg)
            module.log('ERROR: ' + msg)
            return 1

        # Clean existing altinst_rootvg if needed
        if params['force']:
            module.log('Remove altinst_rootvg from {0} of {1}'.format(hdisks, vios))

            cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
            ret, stdout, stderr = nim_exec(module, vios, cmd)
            if ret != 0:
                msg = 'to remove altinst_rootvg on {0}: {1}'.format(vios, stderr)
                altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                results['meta'][vios]['messages'].append('Failed ' + msg)
                module.log('ERROR: Failed ' + msg)

            else:
                for hdisk in hdisks:
                    cmd = ['/usr/sbin/chpv', '-C', hdisk]
                    ret, stdout, stderr = nim_exec(module, vios, cmd)
                    if ret != 0:
                        msg = 'to clear altinst_rootvg from {0} on {1}'.format(hdisk, vios)
                        altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                        results['meta'][vios]['messages'].append('Failed ' + msg)
                        module.log('ERROR: ' + msg)
                        continue
                    msg = 'Clear altinst_rootvg from disk {0}: Success'.format(hdisk)
                    results['meta'][vios]['messages'].append(msg)
                    module.log(msg)
                    results['changed'] = True

        # get pv list
        pvs = get_pvs(module, vios)
        if (pvs is None) or (not pvs):
            msg = 'to get the list of PVs on {0}'.format(vios)
            altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
            results['meta'][vios]['messages'].append('Failed ' + msg)
            module.log('ERROR: Failed ' + msg)
            return 1

        # check an alternate disk does not already exist
        for pv in pvs:
            if pvs[pv]['vg'] == 'altinst_rootvg':
                msg = 'An alternate disk already exists on disk ({0}) on {1}'.format(pv, vios)
                altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                results['meta'][vios]['messages'].append(msg)
                module.log('ERROR: ' + msg)
                return 1

        pvs = get_free_pvs(module, vios)
        if (pvs is None):
            msg = 'to get the list of free PVs on {0}'.format(vios)
            altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
            results['meta'][vios]['messages'].append('Failed ' + msg)
            module.log('ERROR: Failed ' + msg)
            return 1

        if (not pvs):
            msg = 'no disk available on {0}'.format(vios)
            altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
            results['meta'][vios]['messages'].append(msg)
            module.log('ERROR: ' + msg)
            return 1

        used_size = rootvg_info[vios]["used_size"]
        rootvg_size = rootvg_info[vios]["rootvg_size"]
        # in auto mode, find the first alternate disk available
        if not hdisks:
            selected_disk = ""
            prev_disk = ""
            diffsize = 0
            prev_diffsize = 0
            # parse free disks in increasing size order
            for key in sorted(pvs, key=lambda k: pvs[k]['size']):
                hdisk = key

                # disk too small or already used
                if pvs[hdisk]['size'] < used_size or pvs[hdisk]['pvid'] in used_pv:
                    continue

                # smallest disk that can be selected
                if params['disk_size_policy'] == 'minimize':
                    selected_disk = hdisk
                    if pvs[hdisk]['pvid'] != 'none':
                        used_pv.append(pvs[hdisk]['pvid'])
                    break

                diffsize = pvs[hdisk]['size'] - rootvg_size
                # matching disk size
                if diffsize == 0:
                    selected_disk = hdisk
                    if pvs[hdisk]['pvid'] != 'none':
                        used_pv.append(pvs[hdisk]['pvid'])
                    break

                if diffsize > 0:
                    # diffsize > 0: first disk found bigger than the rootvg disk
                    if params['disk_size_policy'] == 'upper':
                        selected_disk = hdisk
                    elif params['disk_size_policy'] == 'lower':
                        if prev_disk == "":
                            # Best Can Do...
                            selected_disk = hdisk
                        else:
                            selected_disk = prev_disk
                    else:
                        # params['disk_size_policy'] == 'nearest'
                        if prev_disk == "":
                            selected_disk = hdisk
                        elif abs(prev_diffsize) > diffsize:
                            selected_disk = hdisk
                        else:
                            selected_disk = prev_disk

                    if pvs[selected_disk]['pvid'] != 'none':
                        used_pv.append(pvs[selected_disk]['pvid'])
                    break
                # disk size less than rootvg disk size
                #   but big enough to contain the used PPs
                prev_disk = hdisk
                prev_diffsize = diffsize
                continue

            if not selected_disk:
                if prev_disk:
                    # Best Can Do...
                    selected_disk = prev_disk
                    if pvs[selected_disk]['pvid'] != 'none':
                        used_pv.append(pvs[selected_disk]['pvid'])
                else:
                    msg = 'to find an alternate disk on {0}'.format(vios)
                    altdisk_op_tab[vios_key] = '{0} {1}'.format(err_label, msg)
                    results['meta'][vios]['messages'].append('Failed ' + msg)
                    module.log('ERROR: Failed ' + msg)
                    msg = 'No available alternate disk with size greater than {0} MB found on {1}'.format(rootvg_size, vios)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                    return 1

            module.debug('Selected disk on vios {0} is {1} (select mode: {2})'
                         .format(vios, selected_disk, params['disk_size_policy']))
            vios_dict[vios].append(selected_disk)

        # hdisks specified by the user
        else:
            tot_size = 0
            for hdisk in hdisks:
                if hdisk not in pvs:
                    msg = 'disk {0} is not available on {1}'.format(hdisk, vios)
                    altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                    return 1
                if pvs[hdisk]['pvid'] in used_pv:
                    msg = 'alternate disk {0} already used on the mirror VIOS'.format(hdisk)
                    altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                    return 1
                tot_size += pvs[hdisk]['size']

            # check the specified hdisks are large enough
            if tot_size >= rootvg_size:
                for hdisk in hdisks:
                    if pvs[hdisk]['pvid'] != 'none':
                        used_pv.append(pvs[hdisk]['pvid'])
            else:
                if tot_size >= used_size:
                    for hdisk in hdisks:
                        if pvs[hdisk]['pvid'] != 'none':
                            used_pv.append(pvs[hdisk]['pvid'])
                    module.log('WARNING: Alternate disks smaller than the current rootvg.')
                else:
                    msg = 'alternate disks too small on {0}'.format(vios)
                    altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                    msg += ' ({0} < {1})'.format(tot_size, rootvg_size)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                    return 1

    # Disks found
    return 0


def check_rootvg(module, vios):
    """
    Check the rootvg
    - check if the rootvg is mirrored
    - check stale partitions
    - calculate the total and used size of the rootvg

    arguments:
        module  (dict): The Ansible module
        vios     (str): The VIOS name
    return:
        Dictionary with following keys: value
            "status":
                0 the rootvg can be saved in an alternate disk copy
                1 otherwise (cannot unmirror then mirror again)
            "copy_dict":
                dictionary key, value
                    key: copy number (int)
                    value: hdiskX
                    example: {1: 'hdisk4', : 2: 'hdisk8', 3: 'hdisk9'}
            "rootvg_size": size in Megabytes (int)
            "used_size": size in Megabytes (int)
    """
    global results

    vg_info = {}
    copy_dict = {}
    vg_info["status"] = 1
    vg_info["copy_dict"] = copy_dict
    vg_info["rootvg_size"] = 0
    vg_info["used_size"] = 0

    nb_lp = 0
    copy = 0
    used_size = -1
    total_size = -1
    pp_size = -1
    pv_size = -1
    hdisk_dict = {}

    cmd = ['/usr/sbin/lsvg', '-M', 'rootvg']
    ret, stdout, stderr = nim_exec(module, vios, cmd)
    if ret != 0:
        msg = 'Failed to check mirroring on {0}, lsvg returned: {1}'.format(vios, stderr)
        results['meta'][vios]['messages'].append(msg)
        module.log('ERROR: ' + msg)
        return vg_info

    # lsvg -M rootvg command OK, check mirroring
    # hdisk4:453      hd1:101
    # hdisk4:454      hd1:102
    # hdisk4:257      hd10opt:1:1
    # hdisk4:258      hd10opt:2:1
    # hdisk4:512-639
    # hdisk8:255      hd1:99:2        stale
    # hdisk8:256      hd1:100:2       stale
    # hdisk8:257      hd10opt:1:2
    # hdisk8:258      hd10opt:2:2
    # ..
    # hdisk9:257      hd10opt:1:3
    # ..
    if stdout.find('stale') > 0:
        msg = '{0} rootvg contains stale partitions'.format(vios)
        results['meta'][vios]['messages'].append(msg)
        module.log(msg + ": " + stdout)
        return vg_info
    hdisk = ''

    for line in stdout.split('\n'):
        line = line.rstrip()
        mirror_key = re.match(r"^(\S+):\d+\s+\S+:\d+:(\d+)$", line)
        if mirror_key:
            hdisk = mirror_key.group(1)
            copy = int(mirror_key.group(2))
        else:
            single_key = re.match(r"^(\S+):\d+\s+\S+:\d+$", line)
            if single_key:
                hdisk = single_key.group(1)
                copy = 1
            else:
                continue

        if copy == 1:
            nb_lp += 1

        if hdisk in hdisk_dict.keys():
            if hdisk_dict[hdisk] != copy:
                msg = "rootvg data structure is not compatible with an "\
                      "alt_disk_copy operation (2 copies on the same disk)"
                results['meta'][vios]['messages'].append(msg)
                module.log(msg)
                return vg_info
        else:
            hdisk_dict[hdisk] = copy

        if copy not in copy_dict.keys():
            if hdisk in copy_dict.values():
                msg = "rootvg data structure is not compatible with an alt_disk_copy operation"
                results['meta'][vios]['messages'].append(msg)
                module.log(msg)
                return vg_info
            copy_dict[copy] = hdisk

    if len(copy_dict.keys()) > 1:
        if len(copy_dict.keys()) != len(hdisk_dict.keys()):
            msg = "The {0} rootvg is partially or completely mirrored but some "\
                  "LP copies are spread on several disks. This prevents the "\
                  "system from creating an alternate rootvg disk copy."\
                  .format(vios)
            results['meta'][vios]['messages'].append(msg)
            module.log(msg)
            return vg_info

        # the (rootvg) is mirrored then get the size of hdisk from copy1
        cmd = ['/usr/sbin/lsvg', '-p', 'rootvg']
        ret, stdout, stderr = nim_exec(module, vios, cmd)
        if ret != 0:
            msg = 'Failed to get the pvs of rootvg on {0}, lsvg returned: {1}'.format(vios, stderr)
            results['meta'][vios]['messages'].append(msg)
            module.log('ERROR: ' + msg)
            return vg_info

        # parse lsvg outpout to get the size in megabytes:
        # rootvg:
        # PV_NAME           PV STATE          TOTAL PPs   FREE PPs    FREE DISTRIBUTION
        # hdisk4            active            639         254         126..00..00..00..128
        # hdisk8            active            639         254         126..00..00..00..128

        for line in stdout.split('\n'):
            line = line.rstrip()
            match_key = re.match(r"^(\S+)\s+\S+\s+(\d+)\s+\d+\s+\S+", line)
            if match_key:
                pv_size = int(match_key.group(2))
                if match_key.group(1) == copy_dict[1]:
                    break
                continue

        if pv_size == -1:
            msg = 'Failed to get pv size on {0}, parsing error'.format(vios)
            results['meta'][vios]['messages'].append(msg)
            module.log('ERROR: ' + msg)
            return vg_info

    # now get the rootvg pp size
    cmd = ['/usr/sbin/lsvg', 'rootvg']
    ret, stdout, stderr = nim_exec(module, vios, cmd)
    if ret != 0:
        msg = 'Failed to get rootvg VG size on {0}, lsvg returned: {1}'.format(vios, stderr)
        results['meta'][vios]['messages'].append(msg)
        module.log('ERROR: ' + msg)
        return vg_info

    # parse lsvg outpout to get the size in megabytes:
    # VG PERMISSION:      read/write               TOTAL PPs:      558 (285696 megabytes)
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r".*TOTAL PPs:\s+\d+\s+\((\d+)\s+megabytes\).*", line)
        if match_key:
            total_size = int(match_key.group(1))
            continue

        match_key = re.match(r".*PP SIZE:\s+(\d+)\s+megabyte\(s\)", line)
        if match_key:
            pp_size = int(match_key.group(1))
            continue

    if pp_size == -1:
        msg = 'Failed to get rootvg pp size on {0}, parsing error'.format(vios)
        results['meta'][vios]['messages'].append(msg)
        module.log('ERROR: ' + msg)
        return vg_info

    if len(copy_dict.keys()) > 1:
        total_size = pp_size * pv_size

    used_size = pp_size * (nb_lp + 1)

    vg_info["status"] = 0
    vg_info["copy_dict"] = copy_dict
    vg_info["rootvg_size"] = total_size
    vg_info["used_size"] = used_size
    return vg_info


def check_valid_altdisks(module, action, vios, hdisks, vios_key, altdisk_op_tab, err_label):
    """
    Check a valid alternate disk that
    - exists,
    - is an alternate disk
    and so can be used.

    sets the altdisk_op_tab acordingly:
        altdisk_op_tab[vios_key] = "FAILURE-ALTDC[12] <error message>"
        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"

    arguments:
        module          (dict): The Ansible module
        action           (str): The action to perform
        vios             (str): The VIOS name
        hdisks          (list): The lists of hdisks
        vios_key         (str): The key for altdisk_op_tab status dicionary
        altdisk_op_tab  (dict): The operation status
        err_label        (str): The error to set the altdisk_op_tab value with
    return:
        True  if alternate disk is found
        False otherwise
    """
    global results

    module.debug('action: {0}, vios: {1}, hdisks: {2}, vios_key: {3}'
                 .format(action, vios, hdisks, vios_key))

    pvs = get_pvs(module, vios)
    if (pvs is None) or (not pvs):
        msg = 'to get the list of PVs on {0}'.format(vios)
        altdisk_op_tab[vios_key] = '{0} {1}'.format(err_label, msg)
        results['meta'][vios]['messages'].append('Failed ' + msg)
        module.log('ERROR: Failed ' + msg)
        return False

    if not isinstance(hdisks, list):
        msg = 'value is not a list for {0}'.format(vios)
        altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
        results['meta'][vios]['messages'].append('Target dictionary ' + msg)
        module.log('ERROR: Target dictionary ' + msg)
        return False

    if hdisks:
        # Check that all specified disks exist and belong to altinst_rootvg
        for hdisk in hdisks:
            if (hdisk not in pvs) or (pvs[hdisk]['vg'] != 'altinst_rootvg'):
                msg = 'disk {0} is not an alternate install rootvg on {1}'.format(hdisk, vios)
                altdisk_op_tab[vios_key] = '{0} {1}'.format(err_label, msg)
                msg = 'Specified ' + msg
                results['meta'][vios]['messages'].append(msg)
                module.log('ERROR: ' + msg)
                return False
    else:
        # Retrieve the list of disks that belong to altinst_rootvg
        for pv in pvs.keys():
            if pvs[pv]['vg'] == 'altinst_rootvg':
                hdisks.append(pv)
        if not hdisks:
            msg = 'There is no alternate install rootvg on {0}'.format(vios)
            results['meta'][vios]['messages'].append(msg)
            module.log('ERROR: ' + msg)
            return False

    return True


def wait_altdisk_install(module, vios, hdisks, vios_key, altdisk_op_tab, err_label):
    """
    Wait for the alternate disk copy operation to finish.

    When alt_disk_install operation ends, the NIM object state changes
    from "a client is being prepared for alt_disk_install" or
         "alt_disk_install operation is being performed"
    to   "ready for NIM operation"

    arguments:
        module          (dict): The Ansible module
        vios             (str): The VIOS name
        hdisks          (list): The lists of hdisks
        vios_key         (str): The key for altdisk_op_tab status dicionary
        altdisk_op_tab  (dict): The operation status
        err_label        (str): The error to set the altdisk_op_tab value with
    return:
        -1  if timedout before alt_disk_install ends
        0   if the alt_disk_install operation ends with success
        1   if the alt_disk_install operation ends with error
    """
    global results

    module.debug('vios: {0}, hdisks: {1}, vios_key: {2}'
                 .format(vios, hdisks, vios_key))
    module.log('Waiting completion of alt_disk copy {0} on {1}...'
               .format(hdisks, vios))

    # if there is no progress in nim operation "info" attribute for more than
    # 30 minutes we time out: 180 * 10s = 30 min
    wait_time = 0
    check_count = 0
    nim_info_prev = "___"   # this info should not appear in nim info attribute
    while check_count <= 180:
        time.sleep(10)
        wait_time += 10

        cmd = ['lsnim', '-Z', '-a', 'Cstate', '-a', 'info', '-a', 'Cstate_result', vios]
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            msg = 'to get the NIM state for {0}'.format(vios)
            altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
            msg = 'Failed ' + msg + ', lsnim returned: {0}' .format(stderr)
            results['meta'][vios]['messages'].append(msg)
            module.log('ERROR: ' + msg)
            break

        # info attribute (that appears in 3rd possition) can be empty. So stdout looks like:
        # #name:Cstate:info:Cstate_result:
        # <viosName>:ready for a NIM operation:success
        # <viosName>:alt_disk_install operation is being performed:
        #                 Creating logical volume alt_hd2.:success:
        # <viosName>:ready for a NIM operation:0505-126 alt_disk_install- target disk hdisk2 has
        #                 a volume group assigned to it.:failure:
        nim_status = stdout.split('\n')[1].rstrip().split(':')
        nim_Cstate = nim_status[1]
        if len(nim_status) == 4 and (string.lower(nim_status[2]) == "success"
                                     or string.lower(nim_status[2].lower()) == "failure"):
            nim_result = string.lower(nim_status[2])
        else:
            nim_info = nim_status[2]
            nim_result = string.lower(nim_status[3])

        if nim_Cstate == "ready for a NIM operation":
            msg = 'alt_disk copy operation on {0} ended with nim_result: {1}, nim_info:{2}'.format(vios, nim_result, nim_info)
            results['meta'][vios]['messages'].append(msg)
            module.log(msg)
            if nim_result != "success":
                msg = 'to perform alt_disk copy on {0}: {1}'.format(vios, nim_info)
                altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
                results['meta'][vios]['messages'].append('Failed ' + msg)
                module.log('ERROR: Failed ' + msg)
                return 1
            else:
                return 0
        else:
            if nim_info_prev == nim_info:
                check_count += 1
            else:
                nim_info_prev = nim_info
                check_count = 0

        if wait_time % 60 == 0:
            module.log('Waiting completion of alt_disk copy {0} on {1}... {2} minute(s)'
                       .format(hdisks, vios, wait_time / 60))

    # timed out before the end of alt_disk_install
    msg = 'alternate disk copy on {0} blocked'.format(vios)
    altdisk_op_tab[vios_key] = "{0} {1}".format(err_label, msg)
    msg += '. NIM operation for {0} blocked: {1}'.format(hdisks, nim_info)
    results['meta'][vios]['messages'].append(msg)
    module.log('WARNING: ' + msg)

    return -1


def alt_disk_action(module, params, action, targets, vios_status, time_limit):
    """
    alt_disk_copy / alt_disk_clean operation

    For each VIOS tuple,
    - retrieve the previous status if any (looking for SUCCESS-HC and SUCCESS-UPDT)
    - for each VIOS of the tuple, check the rootvg, find and valid the hdisk for the operation
    - unmirror rootvg if necessary
    - perform the alt disk copy or cleanup operation
    - wait for the copy to finish
    - mirror rootvg if necessary

    arguments:
        module      (dict): The Ansible module
        params      (dict): The parameters for the provided action
        action       (str): The action to perform
        targets     (list): The list of VIOS dictionary to perform the action on
        vios_status (dict): The previous operation status for each vios (if any)
        time_limit   (str): The limit of time to perform the operation

    return: dictionary containing the altdisk status for each vios tuple
        altdisk_op_tab[vios_key] = "FAILURE-NO-PREV-STATUS"
        altdisk_op_tab[vios_key] = "FAILURE-ALTDC[12] <error message>"
        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"
    """
    global results

    module.debug('action: {0}, targets: {1}, vios_status: {2}'
                 .format(action, targets, vios_status))

    rootvg_info = {}
    altdisk_op_tab = {}

    for vios_dict in targets:
        module.debug('action: {0} for target: {1}'.format(action, vios_dict))

        # sort VIOSes by name so that the key matches
        vios_list = list(vios_dict.keys())
        vios_list.sort()
        vios_key = '-'.join(vios_list)

        module.debug('vios_key: {0}'.format(vios_key))

        # if health check status is known, check the vios tuple has passed
        # the health check successfuly
        if not (vios_status is None):
            if vios_key not in vios_status:
                altdisk_op_tab[vios_key] = "FAILURE-NO-PREV-STATUS"
                msg = "{0} vioses skipped (no previous status found)".format(vios_key)
                results['meta']['messages'].append(msg)
                module.log("WARNING: " + msg)
                continue

            if 'SUCCESS' not in vios_status[vios_key]:
                altdisk_op_tab[vios_key] = vios_status[vios_key]
                msg = "{0} vioses skipped ({1})".format(vios_key, vios_status[vios_key])
                results['meta']['messages'].append(msg)
                module.log("WARNING: " + msg)
                continue

        # check if there is time to handle this tuple
        if not (time_limit is None) and time.localtime(time.time()) >= time_limit:
            altdisk_op_tab[vios_key] = "SKIPPED-TIMEDOUT"
            time_limit_str = time.strftime("%m/%d/%Y %H:%M", time_limit)
            msg = "Time limit {0} reached, no further operation".format(time_limit_str)
            results['meta']['messages'].append(msg)
            module.log(msg)
            continue

        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"

        if action == 'alt_disk_copy':
            for vios in vios_dict:
                rootvg_info[vios] = check_rootvg(module, vios)

            ret = find_valid_altdisk(module, params, action, vios_dict, vios_key,
                                     rootvg_info, altdisk_op_tab)
            if ret != 0:
                continue

        for vios, hdisks in vios_dict.items():

            # set the error label to be used in sub routines
            if action == 'alt_disk_copy':
                err_label = "FAILURE-ALTDCOPY1"
                if vios != vios_list[0]:
                    err_label = "FAILURE-ALTDCOPY2"
            elif action == 'alt_disk_clean':
                err_label = "FAILURE-ALTDCLEAN1"
                if vios != vios_list[0]:
                    err_label = "FAILURE-ALTDCLEAN2"

            msg = 'Using {0} as alternate disks on {1}'.format(hdisks, vios)
            results['meta'][vios]['messages'].append(msg)
            module.log(msg)

            if action == 'alt_disk_copy':
                # unmirror the vg if necessary
                # check mirror

                copies_h = rootvg_info[vios]["copy_dict"]
                nb_copies = len(copies_h.keys())

                if nb_copies > 1:
                    if not params['force']:
                        altdisk_op_tab[vios_key] = "{0} rootvg is mirrored on {1}".format(err_label, vios)
                        msg = 'The rootvg is mirrored on {0} and force option is not set'.format(vios)
                        results['meta'][vios]['messages'].append(msg)
                        module.log(msg)
                        break

                    msg = 'Stop mirroring on {0}'.format(vios)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('WARNING: ' + msg)

                    cmd = ['/usr/sbin/unmirrorvg', 'rootvg']
                    ret, stdout, stderr = nim_exec(module, vios, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to unmirror rootvg on {1}".format(err_label, vios)
                        msg = 'Failed to unmirror rootvg on {0}: {1}'.format(vios, stderr)
                        results['meta'][vios]['messages'].append(msg)
                        module.log('ERROR: ' + msg)
                        break
                    if stderr.find('rootvg successfully unmirrored') == -1:
                        # unmirror command Failed
                        altdisk_op_tab[vios_key] = "{0} to unmirror rootvg on {1}"\
                                                   .format(err_label, vios)
                        msg = 'Failed to unmirror rootvg on {0}: {1} {2}'.format(vios, stdout, stderr)
                        results['meta'][vios]['messages'].append(msg)
                        module.log('ERROR: ' + msg)
                        break

                    # unmirror command OK
                    msg = 'Unmirror rootvg on {0} successful'.format(vios)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('WARNING: ' + msg)

                module.log('Alternate disk copy on {0}'.format(vios))

                # alt_disk_copy
                cmd = ['nim', '-o', 'alt_disk_install',
                       '-a', 'source=rootvg',
                       '-a', 'disk=' + ' '.join(hdisks),
                       '-a', 'set_bootlist=no',
                       '-a', 'boot_client=no',
                       vios]
                ret_altdc, stdout, stderr = module.run_command(cmd)
                if ret_altdc != 0:
                    altdisk_op_tab[vios_key] = "{0} to copy {1} on {2}".format(err_label, hdisks, vios)
                    msg = 'Failed to copy {0} on {1}: {2}'.format(hdisks, vios, stderr)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                else:
                    results['changed'] = True
                    # wait till alt_disk_install ends
                    ret_altdc = wait_altdisk_install(module, vios, hdisks,
                                                     vios_key, altdisk_op_tab,
                                                     err_label)

                # restore the mirroring if necessary
                if nb_copies > 1:
                    msg = 'Restore mirror on {0}'.format(vios)
                    results['meta'][vios]['messages'].append(msg)
                    module.log(msg)

                    cmd = ['/usr/sbin/mirrorvg', '-m', '-c', nb_copies, 'rootvg', copies_h[2]]
                    if nb_copies > 2:
                        cmd += [copies_h[3]]

                    ret, stdout, stderr = nim_exec(module, vios, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to mirror rootvg on {1}".format(err_label, vios)
                        msg = 'Failed to mirror rootvg on {0}: {1}'.format(vios, stderr)
                        results['meta'][vios]['messages'].append(msg)
                        module.log('ERROR: ' + msg)
                        break
                    if stderr.find('Failed to mirror the volume group') == -1:
                        msg = 'Mirror rootvg on {0} successful'.format(vios)
                        results['meta'][vios]['messages'].append(msg)
                        module.log(msg)

                    # mirror command failed
                    altdisk_op_tab[vios_key] = "{0} to mirror rootvg on {1}".format(err_label, vios)
                    msg = 'Failed to mirror rootvg on {0}: {1} {2}'.format(vios, stdout, stderr)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                    break

                if ret_altdc != 0:
                    # timed out or an error occured, continue with next target_tuple
                    break

            elif action == 'alt_disk_clean':
                module.log('Alternate disk clean on {0}'.format(vios))

                ret = check_valid_altdisks(module, action, vios, hdisks, vios_key,
                                           altdisk_op_tab, err_label)
                if not ret:
                    continue

                msg = 'Using {0} as alternate disks on {1}'.format(hdisks, vios)
                results['meta'][vios]['messages'].append(msg)
                module.log(msg)

                # First remove the alternate VG
                cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
                ret, stdout, stderr = nim_exec(module, vios, cmd)
                if ret != 0:
                    altdisk_op_tab[vios_key] = "{0} to remove altinst_rootvg on {1}".format(err_label, vios)
                    msg = 'Failed to remove altinst_rootvg on {0}: {1}'.format(vios, stderr)
                    results['meta'][vios]['messages'].append(msg)
                    module.log('ERROR: ' + msg)
                    continue

                msg = 'Remove altinst_rootvg from {0} of {1}: Success'.format(hdisks, vios)
                results['meta'][vios]['messages'].append(msg)
                module.log(msg)
                results['changed'] = True

                for hdisk in hdisks:
                    # Clears the owning VG from the disk
                    cmd = ['/usr/sbin/chpv', '-C', hdisk]
                    ret, stdout, stderr = nim_exec(module, vios, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to clear altinst_rootvg from {1} on {2}".format(err_label, hdisk, vios)
                        msg = 'Failed to clear altinst_rootvg from disk {0} on {1}: {2}'.format(hdisk, vios, stderr)
                        results['meta'][vios]['messages'].append(msg)
                        module.log('ERROR: ' + msg)
                        continue

                    msg = 'Clear altinst_rootvg from disk from {0} of {1}: Success'.format(hdisks, vios)
                    results['meta'][vios]['messages'].append(msg)
                    module.log(msg)

    module.debug('altdisk_op_tab: {0}'. format(altdisk_op_tab))
    return altdisk_op_tab


def main():

    global results

    module = AnsibleModule(
        argument_spec=dict(
            targets=dict(required=True, type='list', elements='dict'),
            action=dict(required=True, type='str',
                        choices=['alt_disk_copy', 'alt_disk_clean']),
            time_limit=dict(type='str'),
            vios_status=dict(type='dict'),
            nim_node=dict(type='dict'),
            disk_size_policy=dict(type='str',
                                  choices=['minimize', 'upper', 'lower', 'nearest'],
                                  default='nearest'),
            force=dict(type='bool', default=False),
        )
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        meta={'messages': []},
        nim_node={},
        status={},
    )

    # Get module params
    params = {}
    action = module.params['action']
    targets = module.params['targets']

    params['action'] = action
    params['targets'] = targets
    params['disk_size_policy'] = module.params['disk_size_policy']
    params['force'] = module.params['force']

    vios_status = {}
    targets_altdisk_status = {}

    # Build nim node info
    refresh_nim_node(module, 'vios')

    if module.params['vios_status']:
        vios_status = module.params['vios_status']
    else:
        vios_status = None

    # build a time structure for time_limit attribute
    time_limit = None
    if module.params['time_limit']:
        match_key = re.match(r"^\s*\d{2}/\d{2}/\d{4} \S*\d{2}:\d{2}\s*$",
                             module.params['time_limit'])
        if match_key:
            time_limit = time.strptime(module.params['time_limit'], '%m/%d/%Y %H:%M')
        else:
            results['msg'] = 'Malformed time limit "{0}", please use mm/dd/yyyy hh:mm format.'\
                             .format(module.params['time_limit'])
            module.fail_json(**results)

    # Perfom check and operation
    ret = check_vios_targets(module, targets)
    if not ret:
        results['msg'] = 'Invalid target list'
        module.fail_json(**results)

    for vios_dict in targets:
        for vios in vios_dict:
            results['meta'][vios] = {'messages': []}  # first time init

    results['status'] = alt_disk_action(module, params, action, targets, vios_status, time_limit)

    target_errored = []
    if results['status']:
        msg = 'VIOS Alternate disk operation status:'
        results['meta']['messages'].append(msg)
        module.log(msg)
        for vios_key, status in results['status'].items():
            msg = '{0} : {1}'.format(vios_key, results['status'][vios_key])
            results['meta']['messages'].append(msg)
            module.log(msg)
            if 'FAILURE-ALTD' in status:
                target_errored.append(vios_key)
        if target_errored:
            results['msg'] = "NIM VIOS Alternate disk {0} operation failed for {1}. See status and meta for details.".format(action, target_errored)
            module.fail_json(**results)
    else:
        results['msg'] = 'VIOS Alternate disk operation: Error getting the status'
        module.log('ERROR: ' + results['msg'])
        results['status'] = vios_status
        module.fail_json(**results)

    results['status'] = targets_altdisk_status
    results['msg'] = 'VIOS alt disk operation completed. See status and meta for details.'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
