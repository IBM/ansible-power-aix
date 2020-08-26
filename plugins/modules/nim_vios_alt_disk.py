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
short_description: Create/Cleanup an alternate rootvg disk
description:
- Copy the rootvg to an alternate disk or cleanup an existing one.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform on the VIOS.
    - C(alt_disk_copy) to perform and alternate disk copy.
    - C(alt_disk_clean) to cleanup an existing alternate disk copy.
    type: str
    choices: [ alt_disk_copy, alt_disk_clean ]
    required: true
  targets:
    description:
    - NIM VIOS targets.
    - Use a dictionary format, with the key being the VIOS NIM name and the
      value being the list of disks used for the alternate disk copy.
    type: list
    elements: dict
    required: true
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
  disk_size_policy:
    description:
    - Specifies how to choose the alternate disk if not specified.
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
notes:
  - C(alt_disk_copy) only backs up mounted file systems. Mount all file
    systems that you want to back up.
  - when no target is specified, copy is performed to only one alternate
    disk even if the rootvg contains multiple disks
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
nim_node:
    description: NIM node info.
    returned: always
    type: dict
status:
    description: Status for each VIOS tuples (dictionary key).
    returned: always
    type: dict
'''

import re
import time
import string

from ansible.module_utils.basic import AnsibleModule

OUTPUT = []
PARAMS = {}
NIM_NODE = {}


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - ret     return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

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


def get_hmc_info(module):
    """
    Get the hmc info on the nim master.

    return a dictionary with hmc info
    """
    info_hash = {}

    cmd = ['lsnim', '-t', 'hmc', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = 'Failed to get HMC NIM info, lsnim returned {0}: {1}'.format(ret, stderr)
        module.log(msg)
        OUTPUT.append(msg)
        return info_hash

    obj_key = ''
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        # HMC name
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            cstate = match_cstate.group(1)
            info_hash[obj_key]['cstate'] = cstate
            continue

        match_key = re.match(r"^\s+passwd_file\s+=\s+(.*)$", line)
        if match_key:
            info_hash[obj_key]['passwd_file'] = match_key.group(1)
            continue

        match_key = re.match(r"^\s+login\s+=\s+(.*)$", line)
        if match_key:
            info_hash[obj_key]['login'] = match_key.group(1)
            continue

        match_key = re.match(r"^\s+if1\s*=\s*\S+\s*(\S*)\s*.*$", line)
        if match_key:
            info_hash[obj_key]['ip'] = match_key.group(1)
            continue

    return info_hash


def get_nim_clients_info(module, lpar_type):
    """
    Get the list of lpars (standalones or vioses) defined on the
    nim master, and get their cstate.

    return a dictionary of the lpar objects defined on the
           nim master and their associated cstate value
    """
    info_hash = {}

    cmd = ['lsnim', '-t', lpar_type, '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = 'Failed to get NIM clients info, lsnim returned: {0}'.format(stderr)
        module.log(msg)
        OUTPUT.append(msg)
        return info_hash

    # lpar name and associated Cstate
    obj_key = ""
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            info_hash[obj_key]['cstate'] = match_cstate.group(1)
            continue

        # For VIOS store the management profile
        if lpar_type == 'vios':
            match_mgmtprof = re.match(r"^\s+mgmt_profile1\s+=\s+(.*)$", line)
            if match_mgmtprof:
                mgmt_elts = match_mgmtprof.group(1).split()
                if len(mgmt_elts) >= 3:
                    info_hash[obj_key]['mgmt_hmc_id'] = mgmt_elts[0]
                    info_hash[obj_key]['mgmt_vios_id'] = mgmt_elts[1]
                    info_hash[obj_key]['mgmt_cec'] = mgmt_elts[2]

            match_if = re.match(r"^\s+if1\s+=\s+\S+\s+(\S+)\s+.*$", line)
            if match_if:
                info_hash[obj_key]['vios_ip'] = match_if.group(1)

    return info_hash


def build_nim_node(module):
    """
    Build the nim node containing the nim vios and hmc info.
    """

    global NIM_NODE

    # =========================================================================
    # Build hmc info list
    # =========================================================================
    nim_hmc = get_hmc_info(module)
    NIM_NODE['nim_hmc'] = nim_hmc
    module.debug('NIM HMC: {0}'.format(nim_hmc))

    # =========================================================================
    # Build vios info list
    # =========================================================================
    nim_vios = get_nim_clients_info(module, 'vios')
    NIM_NODE['nim_vios'] = nim_vios
    module.debug('NIM VIOS: {0}'.format(nim_vios))


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
        targets: list of dictionaries of VIOS NIM names and
                    associated alternate disks

    return: True iff all targets are valid NIM VIOS objects and are reachable
    """
    global NIM_NODE

    # ===========================================
    # Check targets
    # ===========================================
    for vios_dict in targets:
        if len(vios_dict) > 2:
            OUTPUT.append('Malformed VIOS targets {0}. Dictionary should contain 1 or 2 elements.'
                          .format(vios_dict))
            module.log('Malformed VIOS targets {0}. Dictionary should contain 1 or 2 elements.'
                       .format(vios_dict))
            return False

        for vios in vios_dict:
            # check vios is known by the NIM master - if not ignore it
            # because it can concern another ansible host (nim master)
            if vios not in NIM_NODE['nim_vios']:
                module.log('skipping {0} as VIOS not known by the NIM master.'
                           .format(vios))
                return False

            # check vios connectivity
            cmd = ['true']
            ret, stdout, stderr = nim_exec(module, NIM_NODE['nim_vios'][vios]['vios_ip'], cmd)
            if ret != 0:
                module.log('skipping {0}: cannot reach with c_rsh: {1}, {2}, {3}'
                           .format(vios, ret, stdout, stderr))
                return False

    return True


def get_pvs(module, vios):
    """
    Get the list of PVs on the VIOS.

    return: dictionary with PVs information
    """
    global NIM_NODE
    global OUTPUT

    module.debug('vios: {0}'.format(vios))

    cmd = ['/usr/ios/cli/ioscli', 'lspv']
    ret, stdout, stderr = nim_exec(module, NIM_NODE['nim_vios'][vios]['vios_ip'], cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get the PV list on {0}, lspv returned: {1}'
                      .format(vios, stderr))
        module.log('Failed to get the PV list on {0}, lspv returned: {1} {2}'
                   .format(vios, ret, stderr))
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

    return: dictionary with free PVs information
    """
    global NIM_NODE
    global OUTPUT

    module.debug('vios: {0}'.format(vios))

    cmd = ['/usr/ios/cli/ioscli', 'lspv', '-free']
    ret, stdout, stderr = nim_exec(module, NIM_NODE['nim_vios'][vios]['vios_ip'], cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get the list of free PV on {0}: {1}'
                      .format(vios, stderr))
        module.log('Failed to get the list of free PVs on {0}, lspv returned: {1} {2}'
                   .format(vios, ret, stderr))
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


def find_valid_altdisk(module, action, vios_dict, vios_key, rootvg_info, altdisk_op_tab):
    """
    Find a valid alternate disk that:
    - exists,
    - is not part of a VG
    - with a correct size
    and so can be used.

    Sets the altdisk_op_tab accordingly:
        altdisk_op_tab[vios_key] = "FAILURE-ALTDC <error message>"
        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"

    return:
        0 if alternate disk is found
        1 otherwise
    """
    global NIM_NODE
    global OUTPUT
    global PARAMS
    global results

    pvs = {}
    used_pv = []

    for vios, hdisks in vios_dict.items():
        module.debug('action: {0}, vios: {1}, hdisks: {2}, vios_key: {3}'
                     .format(action, vios, hdisks, vios_key))

        OUTPUT.append('    Check the alternate disks {0} on {1}'.format(hdisks, vios))

        err_label = "FAILURE-ALTDC"

        # check value is a list
        if not isinstance(hdisks, list):
            altdisk_op_tab[vios_key] = "{0} value is not a list for {1}"\
                                       .format(err_label, vios)
            return 1

        # check rootvg
        if rootvg_info[vios]["status"] != 0:
            altdisk_op_tab[vios_key] = "{0} wrong rootvg state on {1}"\
                                       .format(err_label, vios)
            return 1

        # Clean existing altinst_rootvg if needed
        if PARAMS['force']:
            OUTPUT.append('    Remove altinst_rootvg from {0} of {1}'
                          .format(hdisks, vios))

            vios_ip = NIM_NODE['nim_vios'][vios]['vios_ip']

            cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
            ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
            if ret != 0:
                altdisk_op_tab[vios_key] = "{0} to remove altinst_rootvg on {1}"\
                                           .format(err_label, vios)
                OUTPUT.append('    Failed to remove altinst_rootvg on {0}: {1}'
                              .format(vios, stderr))
                module.log('Failed to remove altinst_rootvg on {0}: {1}'
                           .format(vios, stderr))
            else:
                for hdisk in hdisks:
                    cmd = ['/usr/sbin/chpv', '-C', hdisk]
                    ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to clear altinst_rootvg from {1} on {2}"\
                                                   .format(err_label, hdisk, vios)
                        OUTPUT.append('    Failed to clear altinst_rootvg from disk {0} on {1}: {2}'
                                      .format(hdisk, vios, stderr))
                        module.log('Failed to clear altinst_rootvg from disk {0} on {1}: {2}'
                                   .format(hdisk, vios, stderr))
                        continue
                    OUTPUT.append('    Clear altinst_rootvg from disk {0}: Success'
                                  .format(hdisk))
                    results['changed'] = True

        # get pv list
        pvs = get_pvs(module, vios)
        if (pvs is None) or (not pvs):
            altdisk_op_tab[vios_key] = "{0} to get the list of PVs on {1}"\
                                       .format(err_label, vios)
            return 1

        # check an alternate disk does not already exist
        for pv in pvs:
            if pvs[pv]['vg'] == 'altinst_rootvg':
                altdisk_op_tab[vios_key] = "{0} an alternate disk ({1}) already exists on {2}"\
                                           .format(err_label, pv, vios)
                OUTPUT.append('    An alternate disk is already available on disk {0} on {1}'
                              .format(pv, vios))
                module.log('An alternate disk is already available on disk {0} on {1}'
                           .format(pv, vios))
                return 1

        pvs = get_free_pvs(module, vios)
        if (pvs is None):
            altdisk_op_tab[vios_key] = "{0} to get the list of free PVs on {1}"\
                                       .format(err_label, vios)
            return 1

        if (not pvs):
            altdisk_op_tab[vios_key] = "{0} no disk available on {1}"\
                                       .format(err_label, vios)
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
                if PARAMS['disk_size_policy'] == 'minimize':
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
                    if PARAMS['disk_size_policy'] == 'upper':
                        selected_disk = hdisk
                    elif PARAMS['disk_size_policy'] == 'lower':
                        if prev_disk == "":
                            # Best Can Do...
                            selected_disk = hdisk
                        else:
                            selected_disk = prev_disk
                    else:
                        # PARAMS['disk_size_policy'] == 'nearest'
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
                    altdisk_op_tab[vios_key] = "{0} to find an alternate disk on {1}"\
                                               .format(err_label, vios)
                    OUTPUT.append('    No available alternate disk with size greater than {0} MB'
                                  ' found on {1}'.format(rootvg_size, vios))
                    module.log('No available alternate disk with size greater than {0} MB'
                               ' found on {1}'.format(rootvg_size, vios))
                    return 1

            module.debug('Selected disk on vios {0} is {1} (select mode: {2})'
                         .format(vios, selected_disk, PARAMS['disk_size_policy']))
            vios_dict[vios].append(selected_disk)

        # hdisks specified by the user
        else:
            tot_size = 0
            for hdisk in hdisks:
                if hdisk not in pvs:
                    altdisk_op_tab[vios_key] = "{0} disk {1} is not available on {2}"\
                                               .format(err_label, hdisk, vios)
                    OUTPUT.append('    Alternate disk {0} is not available on {1}'
                                  .format(hdisk, vios))
                    module.log('Alternate disk {0} is either not found or not available on {1}'
                               .format(hdisk, vios))
                    return 1
                if pvs[hdisk]['pvid'] in used_pv:
                    altdisk_op_tab[vios_key] = "{0} alternate disk {1} already"\
                                               " used on the mirror VIOS"\
                                               .format(err_label, hdisk)
                    module.log('Alternate disk {0} already used on the mirror VIOS.'
                               .format(hdisk))
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
                    module.log('[WARNING] Alternate disks smaller than the current rootvg.')
                else:
                    altdisk_op_tab[vios_key] = "{0} alternate disks too small on {1}"\
                                               .format(err_label, vios)
                    module.log('Alternate disks too small ({0} < {1}) on {2}.'
                               .format(tot_size, rootvg_size, vios))
                    return 1

    # Disks found
    return 0


def check_rootvg(module, vios):
    """
    Check the rootvg
    - check if the rootvg is mirrored
    - check stale partitions
    - calculate the total and used size of the rootvg

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
    global NIM_NODE
    global OUTPUT

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

    vios_ip = NIM_NODE['nim_vios'][vios]['vios_ip']

    cmd = ['/usr/sbin/lsvg', '-M', 'rootvg']
    ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
    if ret != 0:
        OUTPUT.append('    Failed to check mirroring on {0}, lsvg returned: {1}'
                      .format(vios, stderr))
        module.log('Failed to check mirroring on {0}, lsvg returned: {1} {2}'
                   .format(vios, ret, stderr))
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
        OUTPUT.append('    {0} rootvg contains stale partitions'
                      .format(vios))
        module.log('{0} rootvg contains stale partitions: {1}'
                   .format(vios, stdout))
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
                OUTPUT.append('    ' + msg)
                module.log(msg)
                return vg_info
        else:
            hdisk_dict[hdisk] = copy

        if copy not in copy_dict.keys():
            if hdisk in copy_dict.values():
                msg = "rootvg data structure is not compatible with an alt_disk_copy operation"
                OUTPUT.append('    ' + msg)
                module.log(msg)
                return vg_info
            copy_dict[copy] = hdisk

    if len(copy_dict.keys()) > 1:
        if len(copy_dict.keys()) != len(hdisk_dict.keys()):
            msg = "The {0} rootvg is partially or completely mirrored but some "\
                  "LP copies are spread on several disks. This prevents the "\
                  "system from creating an alternate rootvg disk copy."\
                  .format(vios)
            OUTPUT.append('    ' + msg)
            module.log(msg)
            return vg_info

        # the (rootvg) is mirrored then get the size of hdisk from copy1
        cmd = ['/usr/sbin/lsvg', '-p', 'rootvg']
        ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
        if ret != 0:
            OUTPUT.append('    Failed to get the pvs of rootvg on {0}, lsvg returned: {1}'
                          .format(vios, stderr))
            module.log('Failed to get the pvs of rootvg on {0}, lsvg returned: {1} {2}'
                       .format(vios, ret, stderr))
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
            OUTPUT.append('    Failed to get pv size on {0}, parsing error'
                          .format(vios))
            module.log('Failed to get pv size on {0}, parsing error'
                       .format(vios))
            return vg_info

    # now get the rootvg pp size
    cmd = ['/usr/sbin/lsvg', 'rootvg']
    ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get rootvg VG size on {0}, lsvg returned: {1}'
                      .format(vios, stderr))
        module.log('Failed to get rootvg VG size on {0}, lsvg returned: {1} {2}'
                   .format(vios, ret, stderr))
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
        OUTPUT.append('    Failed to get rootvg pp size on {0}, parsing error'
                      .format(vios))
        module.log('Failed to get rootvg pp size on {0}, parsing error'
                   .format(vios))
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

    return:
        True  if alternate disk is found
        False otherwise
    """
    global NIM_NODE
    global OUTPUT

    module.debug('action: {0}, vios: {1}, hdisks: {2}, vios_key: {3}'
                 .format(action, vios, hdisks, vios_key))

    OUTPUT.append('    Check the alternate disks {0} on {1}'.format(hdisks, vios))

    pvs = get_pvs(module, vios)
    if (pvs is None) or (not pvs):
        altdisk_op_tab[vios_key] = "{0} to get the list of PVs on {1}"\
                                   .format(err_label, vios)
        return False

    if not isinstance(hdisks, list):
        altdisk_op_tab[vios_key] = "{0} value is not a list for {1}"\
                                   .format(err_label, vios)
        return False

    if hdisks:
        # Check that all specified disks exist and belong to altinst_rootvg
        for hdisk in hdisks:
            if (hdisk not in pvs) or (pvs[hdisk]['vg'] != 'altinst_rootvg'):
                altdisk_op_tab[vios_key] = "{0} disk {1} is not an alternate install rootvg on {2}"\
                                           .format(err_label, hdisk, vios)
                OUTPUT.append('    Specified disk {0} is not an alternate install rootvg on {1}'
                              .format(hdisk, vios))
                module.log('Specified disk {0} is not an alternate install rootvg on {1}'
                           .format(hdisk, vios))
                return False
    else:
        # Retrieve the list of disks that belong to altinst_rootvg
        for pv in pvs.keys():
            if pvs[pv]['vg'] == 'altinst_rootvg':
                hdisks.append(pv)
        if not hdisks:
            OUTPUT.append('    There is no alternate install rootvg on {0}'.format(vios))
            module.log('There is no alternate install rootvg on {0}'.format(vios))
            return False

    return True


def wait_altdisk_install(module, vios, hdisks, vios_key, altdisk_op_tab, err_label):
    """
    Wait for the alternate disk copy operation to finish.

    When alt_disk_install operation ends, the NIM object state changes
    from "a client is being prepared for alt_disk_install" or
         "alt_disk_install operation is being performed"
    to   "ready for NIM operation"

    return:
        -1  if timedout before alt_disk_install ends
        0   if the alt_disk_install operation ends with success
        1   if the alt_disk_install operation ends with error
    """
    global OUTPUT

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
            altdisk_op_tab[vios_key] = "{0} to get the NIM state for {1}".format(err_label, vios)
            OUTPUT.append('    Failed to get the NIM state for {0}, lsnim returned: {1}'
                          .format(vios, stderr))
            module.log('Failed to get the NIM state for {0}, lsnim returned: {1} {2}'
                       .format(vios, ret, stderr))
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
            module.log('alt_disk copy operation on {0} ended with nim_result: {1}'
                       .format(vios, nim_result))
            if nim_result != "success":
                altdisk_op_tab[vios_key] = "{0} to perform alt_disk copy on {1} {2}"\
                                           .format(err_label, vios, nim_info)
                OUTPUT.append('    Failed to perform alt_disk copy on {0}: {1}'
                              .format(vios, nim_info))
                module.log('Failed to perform alt_disk copy on {0}: {1}'
                           .format(vios, nim_info))
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
    altdisk_op_tab[vios_key] = "{0} alternate disk copy of {1} blocked on {2}: NIM operation blocked"\
                               .format(err_label, vios, nim_info)
    OUTPUT.append('    Alternate disk copy of {0} blocked on {1}: {2}'
                  .format(hdisks, vios, nim_info))
    module.log('Alternate disk copy of {0} blocked on {1}: {2}'
               .format(hdisks, vios, nim_info))

    return -1


def alt_disk_action(module, action, targets, vios_status, time_limit):
    """
    alt_disk_copy / alt_disk_clean operation

    For each VIOS tuple,
    - retrieve the previous status if any (looking for SUCCESS-HC and SUCCESS-UPDT)
    - for each VIOS of the tuple, check the rootvg, find and valid the hdisk for the operation
    - unmirror rootvg if necessary
    - perform the alt disk copy or cleanup operation
    - wait for the copy to finish
    - mirror rootvg if necessary

    return: dictionary containing the altdisk status for each vios tuple
        altdisk_op_tab[vios_key] = "FAILURE-NO-PREV-STATUS"
        altdisk_op_tab[vios_key] = "FAILURE-ALTDC[12] <error message>"
        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"
    """
    global NIM_NODE
    global OUTPUT
    global PARAMS
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
                OUTPUT.append("    {0} vioses skipped (no previous status found)"
                              .format(vios_key))
                module.log("[WARNING] {0} vioses skipped (no previous status found)"
                           .format(vios_key))
                continue

            if vios_status[vios_key] != 'SUCCESS-HC' and vios_status[vios_key] != 'SUCCESS-UPDT':
                altdisk_op_tab[vios_key] = vios_status[vios_key]
                OUTPUT.append("    {0} vioses skipped ({1})"
                              .format(vios_key, vios_status[vios_key]))
                module.log("[WARNING] {0} vioses skipped ({1})"
                           .format(vios_key, vios_status[vios_key]))
                continue

        # check if there is time to handle this tuple
        if not (time_limit is None) and time.localtime(time.time()) >= time_limit:
            altdisk_op_tab[vios_key] = "SKIPPED-TIMEDOUT"
            time_limit_str = time.strftime("%m/%d/%Y %H:%M", time_limit)
            OUTPUT.append("    Time limit {0} reached, no further operation"
                          .format(time_limit_str))
            module.log('Time limit {0} reached, no further operation'
                       .format(time_limit_str))
            continue

        altdisk_op_tab[vios_key] = "SUCCESS-ALTDC"

        if action == 'alt_disk_copy':
            for vios in vios_dict:
                rootvg_info[vios] = check_rootvg(module, vios)

            ret = find_valid_altdisk(module, action, vios_dict, vios_key,
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

            OUTPUT.append('    Using {0} as alternate disks on {1}'.format(hdisks, vios))
            module.log('Using {0} as alternate disks on {1}'.format(hdisks, vios))

            vios_ip = NIM_NODE['nim_vios'][vios]['vios_ip']

            if action == 'alt_disk_copy':
                # unmirror the vg if necessary
                # check mirror

                copies_h = rootvg_info[vios]["copy_dict"]
                nb_copies = len(copies_h.keys())

                if nb_copies > 1:
                    if not PARAMS['force']:
                        altdisk_op_tab[vios_key] = "{0} rootvg is mirrored on {1}"\
                                                   .format(err_label, vios)
                        OUTPUT.append('    The rootvg is mirrored on {0} and force option is not set'
                                      .format(vios))
                        module.log('The rootvg is mirrored on {0} and force option is not set'
                                   .format(vios))
                        break

                    OUTPUT.append('    Stop mirroring on {0}'.format(vios))
                    module.log('[WARNING] Stop mirror on {0}'.format(vios))

                    cmd = ['/usr/sbin/unmirrorvg', 'rootvg']
                    ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to unmirror rootvg on {1}"\
                                                   .format(err_label, vios)
                        OUTPUT.append('    Failed to unmirror rootvg on {0}: {1}'
                                      .format(vios, stderr))
                        module.log('Failed to unmirror rootvg on {0}: {1}'
                                   .format(vios, stderr))
                        break
                    if stderr.find('rootvg successfully unmirrored') == -1:
                        # unmirror command Failed
                        altdisk_op_tab[vios_key] = "{0} to unmirror rootvg on {1}"\
                                                   .format(err_label, vios)
                        OUTPUT.append('    Failed to unmirror rootvg on {0}: {1} {2}'
                                      .format(vios, stdout, stderr))
                        module.log('Failed to unmirror rootvg on {0}: {1} {2}'
                                   .format(vios, stdout, stderr))
                        break

                    # unmirror command OK
                    OUTPUT.append('    Unmirror rootvg on {0} successful'
                                  .format(vios))
                    module.info('Unmirror rootvg on {0} successful'
                                .format(vios))

                OUTPUT.append('    Alternate disk copy on {0}'.format(vios))

                # alt_disk_copy
                cmd = ['nim', '-o', 'alt_disk_install',
                       '-a', 'source=rootvg',
                       '-a', 'disk=' + ' '.join(hdisks),
                       '-a', 'set_bootlist=no',
                       '-a', 'boot_client=no',
                       vios]
                ret_altdc, stdout, stderr = module.run_command(cmd)
                if ret_altdc != 0:
                    altdisk_op_tab[vios_key] = "{0} to copy {1} on {2}"\
                                               .format(err_label, hdisks, vios)
                    OUTPUT.append('    Failed to copy {0} on {1}: {2}'
                                  .format(hdisks, vios, stderr))
                    module.log('Failed to copy {0} on {1}: {2}'
                               .format(hdisks, vios, stderr))
                else:
                    # wait till alt_disk_install ends
                    ret_altdc = wait_altdisk_install(module, vios, hdisks,
                                                     vios_key, altdisk_op_tab,
                                                     err_label)

                # restore the mirroring if necessary
                if nb_copies > 1:
                    OUTPUT.append('    Restore mirror on {0}'.format(vios))
                    module.log('Restore mirror on {0}'.format(vios))

                    cmd = ['/usr/sbin/mirrorvg', '-m', '-c', nb_copies, 'rootvg', copies_h[2]]
                    if nb_copies > 2:
                        cmd += [copies_h[3]]

                    ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to mirror rootvg on {1}"\
                                                   .format(err_label, vios)
                        OUTPUT.append('    Failed to mirror rootvg on {0}: {1}'
                                      .format(vios, stderr))
                        module.log('Failed to mirror rootvg on {0}: {1}'
                                   .format(vios, stderr))
                        break
                    if stderr.find('Failed to mirror the volume group') == -1:
                        OUTPUT.append('    Mirror rootvg on {0} successful'
                                      .format(vios))
                        module.log('Mirror rootvg on {0} successful'
                                   .format(vios))

                    # mirror command failed
                    altdisk_op_tab[vios_key] = "{0} to mirror rootvg on {1}"\
                                               .format(err_label, vios)
                    OUTPUT.append('    Failed to mirror rootvg on {0}: {1} {2}'
                                  .format(vios, stdout, stderr))
                    module.log('Failed to mirror rootvg on {0}: {1} {2}'
                               .format(vios, stdout, stderr))
                    break

                if ret_altdc != 0:
                    # timed out or an error occured, continue with next target_tuple
                    break

                results['changed'] = True

            elif action == 'alt_disk_clean':
                OUTPUT.append('    Alternate disk clean on {0}'.format(vios))

                ret = check_valid_altdisks(module, action, vios, hdisks, vios_key,
                                           altdisk_op_tab, err_label)
                if not ret:
                    continue

                OUTPUT.append('    Using {0} as alternate disks on {1}'
                              .format(hdisks, vios))
                module.log('Using {0} as alternate disks on {1}'
                           .format(hdisks, vios))

                # First remove the alternate VG
                OUTPUT.append('    Remove altinst_rootvg from {0} of {1}'
                              .format(hdisks, vios))

                cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
                ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
                if ret != 0:
                    altdisk_op_tab[vios_key] = "{0} to remove altinst_rootvg on {1}"\
                                               .format(err_label, vios)
                    OUTPUT.append('    Failed to remove altinst_rootvg on {0}: {1}'
                                  .format(vios, stderr))
                    module.log('Failed to remove altinst_rootvg on {0}: {1}'
                               .format(vios, stderr))
                    continue

                for hdisk in hdisks:
                    # Clears the owning VG from the disk
                    OUTPUT.append('    Clear the owning VG from disk {0} on {1}'
                                  .format(hdisk, vios))

                    cmd = ['/usr/sbin/chpv', '-C', hdisk]
                    ret, stdout, stderr = nim_exec(module, vios_ip, cmd)
                    if ret != 0:
                        altdisk_op_tab[vios_key] = "{0} to clear altinst_rootvg from {1} on {2}"\
                                                   .format(err_label, hdisk, vios)
                        OUTPUT.append('    Failed to clear altinst_rootvg from disk {0} on {1}: {2}'
                                      .format(hdisk, vios, stderr))
                        module.log('Failed to clear altinst_rootvg from disk {0} on {1}: {2}'
                                   .format(hdisk, vios, stderr))
                        continue

                    OUTPUT.append('    Clear altinst_rootvg from disk {0}: Success'
                                  .format(hdisk))
                results['changed'] = True

    module.debug('altdisk_op_tab: {0}'. format(altdisk_op_tab))
    return altdisk_op_tab


def main():

    global OUTPUT
    global PARAMS
    global NIM_NODE
    global results

    module = AnsibleModule(
        argument_spec=dict(
            targets=dict(required=True, type='list', elements='dict'),
            action=dict(required=True, type='str',
                        choices=['alt_disk_copy', 'alt_disk_clean']),
            time_limit=dict(type='str'),
            vars=dict(type='dict'),
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
    )

    # =========================================================================
    # Get module params
    # =========================================================================
    action = module.params['action']
    targets = module.params['targets']

    PARAMS['action'] = action
    PARAMS['targets'] = targets
    PARAMS['disk_size_policy'] = module.params['disk_size_policy']
    PARAMS['force'] = module.params['force']

    OUTPUT.append('VIOS Alternate disk operation for {0}'.format(targets))

    vios_status = {}
    targets_altdisk_status = {}

    # =========================================================================
    # Build nim node info
    # =========================================================================
    if module.params['nim_node']:
        NIM_NODE = module.params['nim_node']
    else:
        build_nim_node(module)

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

    # =========================================================================
    # Perfom check and operation
    # =========================================================================
    ret = check_vios_targets(module, targets)
    if not ret:
        results['output'] = OUTPUT
        results['msg'] = 'Invalid target list'
        module.fail_json(**results)

    targets_altdisk_status = alt_disk_action(module, action, targets,
                                             vios_status, time_limit)

    if targets_altdisk_status:
        OUTPUT.append('VIOS Alternate disk operation status:')
        module.log('VIOS Alternate disk operation status:')
        for vios_key in targets_altdisk_status.keys():
            OUTPUT.append("    {0} : {1}".format(vios_key, targets_altdisk_status[vios_key]))
            module.log('    {0} : {1}'.format(vios_key, targets_altdisk_status[vios_key]))
    else:
        OUTPUT.append('VIOS Alternate disk operation: Error getting the status')
        module.log('VIOS Alternate disk operation: Error getting the status')
        targets_altdisk_status = vios_status

    results['nim_node'] = NIM_NODE
    results['status'] = targets_altdisk_status
    results['output'] = OUTPUT
    results['msg'] = 'VIOS alt disk operation completed successfully'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
