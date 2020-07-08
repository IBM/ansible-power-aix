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
module: vios_alt_disk
short_description: Create/Cleanup an alternate rootvg disk on a VIOS
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
  target:
    description:
    - Specifies the target disk.
    type: str
  disk_size_policy:
    description:
    - Specifies how to choose the alternate disk if not specified.
    - C(minimize) smallest disk that can be selected.
    - C(upper) first disk found bigger than the rootvg disk.
    - C(lower) disk size less than rootvg disk size but big enough to contain the used PPs.
    - C(nearest)
    type: str
    choices: [ minimize, upper, lower, nearest ]
    default: nearest
  force:
    description:
    - Forces removal of any existing alternate disk copy on target disk.
    - Stops any active rootvg mirroring during the alternate disk copy.
    type: bool
    default: no
notes:
  - C(alt_disk_copy) only backs up mounted file systems. Mount all file
    systems that you want to back up.
  - copy is performed only on one alternate hdisk even if the rootvg
    contains multiple hdisks
  - error if several C(altinst_rootvg) exist for cleanup operation in
    automatic mode
'''

EXAMPLES = r'''
- name: Perform an alternate disk copy of the rootvg to hdisk1
  vios_alt_disk:
    action: alt_disk_copy
    target: hdisk1

- name: Perform an alternate disk copy of the rootvg to the smallest disk that can be selected
  vios_alt_disk:
    action: alt_disk_copy
    disk_size_policy: minimize
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
status:
    description: Status.
    returned: always
    type: str
'''

import re

from ansible.module_utils.basic import AnsibleModule

OUTPUT = []
PARAMS = {}


def get_pvs(module):
    """
    Get the list of PVs on the VIOS.

    return: dictionary with PVs information
    """
    global OUTPUT

    cmd = ['/usr/ios/cli/ioscli', 'lspv']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get the PV list, lspv returned: {0}'
                      .format(stderr))
        module.log('Failed to get the PV list, lspv returned: {0} {1}'
                   .format(ret, stderr))
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


def get_free_pvs(module):
    """
    Get the list of free PVs on the VIOS.

    return: dictionary with free PVs information
    """
    global OUTPUT

    cmd = ['/usr/ios/cli/ioscli', 'lspv', '-free']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get the list of free PV: {0}'
                      .format(stderr))
        module.log('Failed to get the list of free PVs, lspv returned: {0} {1}'
                   .format(ret, stderr))
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


def find_valid_altdisk(module, action, hdisk, rootvg_info):
    """
    Find a valid alternate disk that:
    - exists,
    - is not part of a VG
    - with a correct size
    and so can be used.

    return:
        '' if alternate disk is found
        reason for failure otherwise
    """
    global OUTPUT
    global PARAMS
    global results

    pvs = {}
    used_pv = []

    module.debug('action: {0}'.format(action))
    OUTPUT.append('    Check the alternate disk {0}'.format(hdisk))

    err_label = "FAILURE-ALTDC"
    # check rootvg
    if rootvg_info["status"] != 0:
        altdisk_op = "{0} wrong rootvg state".format(err_label)
        return altdisk_op

    # Clean existing altinst_rootvg if needed
    if PARAMS['force']:
        OUTPUT.append('    Remove altinst_rootvg from {0}'
                      .format(hdisk))

        cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            altdisk_op = "{0} to remove altinst_rootvg".format(err_label)
            OUTPUT.append('    Failed to remove altinst_rootvg: {0}'
                          .format(stderr))
            module.log('Failed to remove altinst_rootvg: {0}'
                       .format(stderr))
        else:
            cmd = ['/usr/sbin/chpv', '-C', hdisk]
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                altdisk_op = "{0} to clear altinst_rootvg from {1}"\
                             .format(err_label, hdisk)
                OUTPUT.append('    Failed to clear altinst_rootvg from disk {0}: {1}'
                              .format(hdisk, stderr))
                module.log('Failed to clear altinst_rootvg from disk {0}: {1}'
                           .format(hdisk, stderr))
                return altdisk_op
            OUTPUT.append('    Clear altinst_rootvg from disk {0}: Success'
                          .format(hdisk))
            results['changed'] = True

    # get pv list
    pvs = get_pvs(module)
    if (pvs is None) or (not pvs):
        altdisk_op = "{0} to get the list of PVs".format(err_label)
        return altdisk_op

    # check an alternate disk does not already exists
    for pv in pvs:
        if pvs[pv]['vg'] == 'altinst_rootvg':
            altdisk_op = "{0} an alternate disk ({1}) already exists"\
                         .format(err_label, hdisk)
            OUTPUT.append('    An alternate disk is already available on disk {0}'
                          .format(hdisk))
            module.log('An alternate disk is already available on disk {0}'
                       .format(hdisk))
            return altdisk_op

    pvs = get_free_pvs(module)
    if pvs is None:
        altdisk_op = "{0} to get the list of free PVs".format(err_label)
        return altdisk_op

    if not pvs:
        altdisk_op = "{0} no disk available".format(err_label)
        return altdisk_op

    used_size = rootvg_info["used_size"]
    rootvg_size = rootvg_info["rootvg_size"]
    # in auto mode, find the first alternate disk available
    if hdisk == "":
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
                if pvs[hdisk]['pvid'] != 'none':
                    used_pv.append(pvs[hdisk]['pvid'])
                break

            diffsize = pvs[hdisk]['size'] - rootvg_size
            # matching disk size
            if diffsize == 0:
                if pvs[hdisk]['pvid'] != 'none':
                    used_pv.append(pvs[hdisk]['pvid'])
                break

            if diffsize > 0:
                # diffsize > 0: first disk found bigger than the rootvg disk
                selected_disk = ""
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

                hdisk = selected_disk
                if pvs[selected_disk]['pvid'] != 'none':
                    used_pv.append(pvs[selected_disk]['pvid'])
                break
            # disk size less than rootvg disk size
            #   but big enough to contain the used PPs
            prev_disk = hdisk
            prev_diffsize = diffsize
            continue

        if hdisk == "":
            if prev_disk != "":
                # Best Can Do...
                hdisk = prev_disk
                if pvs[prev_disk]['pvid'] != 'none':
                    used_pv.append(pvs[prev_disk]['pvid'])
            else:
                altdisk_op = "{0} to find an alternate disk {1}"\
                             .format(err_label, hdisk)
                OUTPUT.append('    No available alternate disk with size greater than {0} MB'
                              ' found'.format(rootvg_size))
                module.log('No available alternate disk with size greater than {0} MB'
                           ' found'.format(rootvg_size))
                return altdisk_op

        module.debug('Selected disk is {0} (select mode: {1})'
                     .format(hdisk, PARAMS['disk_size_policy']))

    # hdisk specified by the user
    else:
        # check the specified hdisk is large enough
        if hdisk in pvs:
            if pvs[hdisk]['pvid'] in used_pv:
                altdisk_op = "{0} alternate disk {1} already"\
                             " used on the mirror VIOS"\
                             .format(err_label, hdisk)
                module.log('Alternate disk {0} already used on the mirror VIOS.'
                           .format(hdisk))
                return 1
            if pvs[hdisk]['size'] >= rootvg_size:
                if pvs[hdisk]['pvid'] != 'none':
                    used_pv.append(pvs[hdisk]['pvid'])
            else:
                if pvs[hdisk]['size'] >= used_size:
                    if pvs[hdisk]['pvid'] != 'none':
                        used_pv.append(pvs[hdisk]['pvid'])
                    module.log('[WARNING] Alternate disk {0} smaller than the current rootvg.'
                               .format(hdisk))
                else:
                    altdisk_op = "{0} alternate disk {1} too small"\
                                 .format(err_label, hdisk)
                    module.log('Alternate disk {0} too small ({1} < {2}).'
                               .format(hdisk, pvs[hdisk]['size'], rootvg_size))
                    return altdisk_op
        else:
            altdisk_op = "{0} disk {1} is not available"\
                         .format(err_label, hdisk)
            OUTPUT.append('    Alternate disk {0} is not available'
                          .format(hdisk))
            module.log('Alternate disk {0} is either not found or not available'
                       .format(hdisk))
            return altdisk_op

    # Disks found
    return ''


def check_rootvg(module):
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

    cmd = ['/usr/sbin/lsvg', '-M', 'rootvg']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        OUTPUT.append('    Failed to check mirroring, lsvg returned: {0}'
                      .format(stderr))
        module.log('Failed to check mirroring, lsvg returned: {0} {1}'
                   .format(ret, stderr))
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
        OUTPUT.append('    rootvg contains stale partitions')
        module.log('rootvg contains stale partitions: {0}'.format(stdout))
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
            msg = "The rootvg is partially or completely mirrored but some "\
                  "LP copies are spread on several disks. This prevents the "\
                  "system from creating an alternate rootvg disk copy."
            OUTPUT.append('    ' + msg)
            module.log(msg)
            return vg_info

        # the (rootvg) is mirrored then get the size of hdisk from copy1
        cmd = ['/usr/sbin/lsvg', '-p', 'rootvg']
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            OUTPUT.append('    Failed to get the pvs of rootvg, lsvg returned: {0}'
                          .format(stderr))
            module.log('Failed to get the pvs of rootvg, lsvg returned: {0} {1}'
                       .format(ret, stderr))
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
            OUTPUT.append('    Failed to get pv size, parsing error')
            module.log('Failed to get pv size, parsing error')
            return vg_info

    # now get the rootvg pp size
    cmd = ['/usr/sbin/lsvg', 'rootvg']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get rootvg VG size, lsvg returned: {0}'
                      .format(stderr))
        module.log('Failed to get rootvg VG size, lsvg returned: {0} {1}'
                   .format(ret, stderr))
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
        OUTPUT.append('    Failed to get rootvg pp size, parsing error')
        module.log('Failed to get rootvg pp size, parsing error')
        return vg_info

    if len(copy_dict.keys()) > 1:
        total_size = pp_size * pv_size

    used_size = pp_size * (nb_lp + 1)

    vg_info["status"] = 0
    vg_info["copy_dict"] = copy_dict
    vg_info["rootvg_size"] = total_size
    vg_info["used_size"] = used_size
    return vg_info


def check_valid_altdisk(module, action, hdisk, err_label):
    """
    Check a valid alternate disk that
    - exists,
    - is an alternate disk
    and so can be used.

    return:
        '' if alternate disk is found
        error reason otherwise
    """
    global OUTPUT

    module.debug('action: {0}, hdisk: {1}'.format(action, hdisk))
    OUTPUT.append('    Check the alternate disk {0}'.format(hdisk))

    pvs = get_pvs(module)
    if (pvs is None) or (not pvs):
        altdisk_op = "{0} to get the list of PVs".format(err_label)
        return altdisk_op

    if hdisk != "":
        if hdisk in pvs and pvs[hdisk]['vg'] == 'altinst_rootvg':
            return ''
        else:
            altdisk_op = "{0} disk {1} is not an alternate install rootvg"\
                         .format(err_label, hdisk)
            OUTPUT.append('    Specified disk {0} is not an alternate install rootvg'
                          .format(hdisk))
            module.log('Specified disk {0} is not an alternate install rootvg'
                       .format(hdisk))
            return altdisk_op
    else:
        # check there is one and only one alternate install rootvg
        for pv in pvs.keys():
            if pvs[pv]['vg'] == 'altinst_rootvg':
                if hdisk:
                    altdisk_op = "{0} there are several alternate"\
                                 " install rootvg"\
                                 .format(err_label)
                    OUTPUT.append('    There are several alternate install rootvg: {0} and {1}'
                                  .format(hdisk, pv))
                    module.log('There are several alternate install rootvg: {0} and {1}'
                               .format(hdisk, pv))
                    return altdisk_op
                else:
                    hdisk = pv
        if hdisk:
            return ''
        else:
            altdisk_op = "{0} no alternate install rootvg".format(err_label)
            OUTPUT.append('    There is no alternate install rootvg')
            module.log('There is no alternate install rootvg')
            return altdisk_op


def alt_disk_action(module, action, hdisk):
    """
    alt_disk_copy / alt_disk_clean operation

    - check the rootvg, find and valid the hdisk for the operation
    - unmirror rootvg if necessary
    - perform the alt disk copy or cleanup operation
    - wait for the copy to finish
    - mirror rootvg if necessary

    return: string containing the altdisk status
        altdisk_op = "FAILURE-ALTDC <error message>"
        altdisk_op = "SUCCESS-ALTDC"
    """
    global OUTPUT
    global PARAMS
    global results

    module.debug('action: {0}'.format(action))

    rootvg_info = {}
    altdisk_op = "SUCCESS-ALTDC"

    if action == 'alt_disk_copy':
        rootvg_info = check_rootvg(module)

        ret = find_valid_altdisk(module, action, hdisk, rootvg_info)
        if ret != '':
            return ret

    # set the error label to be used in sub routines
    if action == 'alt_disk_copy':
        err_label = "FAILURE-ALTDCOPY"
    elif action == 'alt_disk_clean':
        err_label = "FAILURE-ALTDCLEAN"

    OUTPUT.append('    Using {0} as alternate disk'.format(hdisk))
    module.log('Using {0} as alternate disk'.format(hdisk))

    if action == 'alt_disk_copy':
        # unmirror the vg if necessary
        # check mirror

        copies_h = rootvg_info["copy_dict"]
        nb_copies = len(copies_h.keys())

        if nb_copies > 1:
            if not PARAMS['force']:
                altdisk_op = "{0} rootvg is mirrored".format(err_label)
                OUTPUT.append('    The rootvg is mirrored and force option is not set')
                module.log('The rootvg is mirrored and force option is not set')
                return altdisk_op

            OUTPUT.append('    Stop mirroring')
            module.log('[WARNING] Stop mirror')

            cmd = ['/usr/sbin/unmirrorvg', 'rootvg']
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                altdisk_op = "{0} to unmirror rootvg".format(err_label)
                OUTPUT.append('    Failed to unmirror rootvg: {0}'
                              .format(stderr))
                module.log('Failed to unmirror rootvg: {0}'
                           .format(stderr))
                return altdisk_op
            if stderr.find('rootvg successfully unmirrored') == -1:
                # unmirror command Failed
                altdisk_op = "{0} to unmirror rootvg".format(err_label)
                OUTPUT.append('    Failed to unmirror rootvg: {0} {1}'
                              .format(stdout, stderr))
                module.log('Failed to unmirror rootvg: {0} {1}'
                           .format(stdout, stderr))
                return altdisk_op

            # unmirror command OK
            OUTPUT.append('    Unmirror rootvg successful')
            module.info('Unmirror rootvg successful')

        OUTPUT.append('    Alternate disk copy')

        # alt_disk_install
        cmd = ['alt_disk_install', '-C', '-B', hdisk]
        ret_altdc, stdout, stderr = module.run_command(cmd)
        if ret_altdc != 0:
            altdisk_op = "{0} to copy {1}".format(err_label, hdisk)
            OUTPUT.append('    Failed to copy {0}: {1}'
                          .format(hdisk, stderr))
            module.log('Failed to copy {0}: {1}'
                       .format(hdisk, stderr))

        # restore the mirroring if necessary
        if nb_copies > 1:
            OUTPUT.append('    Restore mirror')
            module.log('Restore mirror')

            cmd = ['/usr/sbin/mirrorvg', '-m', '-c', nb_copies, 'rootvg', copies_h[2]]
            if nb_copies > 2:
                cmd += [copies_h[3]]

            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                altdisk_op = "{0} to mirror rootvg".format(err_label)
                OUTPUT.append('    Failed to mirror rootvg: {0}'
                              .format(stderr))
                module.log('Failed to mirror rootvg: {0}'
                           .format(stderr))
                return altdisk_op
            if stderr.find('Failed to mirror the volume group') != -1:
                # mirror command failed
                altdisk_op = "{0} to mirror rootvg".format(err_label)
                OUTPUT.append('    Failed to mirror rootvg: {0} {1}'
                              .format(stdout, stderr))
                module.log('Failed to mirror rootvg: {0} {1}'
                           .format(stdout, stderr))
                return altdisk_op

        if ret_altdc != 0:
            # an error occured
            return altdisk_op

        results['changed'] = True

    elif action == 'alt_disk_clean':
        OUTPUT.append('    Alternate disk clean')

        altdisk_op = check_valid_altdisk(module, action, hdisk, err_label)
        if altdisk_op != '':
            return altdisk_op

        OUTPUT.append('    Using {0} as alternate disk'
                      .format(hdisk))
        module.log('Using {0} as alternate disk'
                   .format(hdisk))

        # First remove the alternate VG
        OUTPUT.append('    Remove altinst_rootvg from {0}'
                      .format(hdisk))

        cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            altdisk_op = "{0} to remove altinst_rootvg".format(err_label)
            OUTPUT.append('    Failed to remove altinst_rootvg: {0}'
                          .format(stderr))
            module.log('Failed to remove altinst_rootvg: {0}'
                       .format(stderr))
            return altdisk_op

        # Clears the owning VG from the disk
        OUTPUT.append('    Clear the owning VG from disk {0}'
                      .format(hdisk))

        cmd = ['/usr/sbin/chpv', '-C', hdisk]
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            altdisk_op = "{0} to clear altinst_rootvg from {1}".format(err_label, hdisk)
            OUTPUT.append('    Failed to clear altinst_rootvg from disk {0}: {1}'
                          .format(hdisk, stderr))
            module.log('Failed to clear altinst_rootvg from disk {0}: {1}'
                       .format(hdisk, stderr))
            return altdisk_op

        OUTPUT.append('    Clear altinst_rootvg from disk {0}: Success'
                      .format(hdisk))
        results['changed'] = True

    module.debug('altdisk_op: {0}'. format(altdisk_op))
    return altdisk_op


def main():

    global OUTPUT
    global PARAMS
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, type='str',
                        choices=['alt_disk_copy', 'alt_disk_clean']),
            target=dict(type='str', default=''),
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
    target = module.params['target']

    PARAMS['action'] = action
    PARAMS['target'] = target
    PARAMS['disk_size_policy'] = module.params['disk_size_policy']
    PARAMS['force'] = module.params['force']

    OUTPUT.append('VIOS Alternate disk operation')

    altdisk_status = alt_disk_action(module, action, target)

    OUTPUT.append('VIOS Alternate disk operation status:')
    module.log('VIOS Alternate disk operation status:')
    OUTPUT.append("    {0}".format(altdisk_status))
    module.log('    {0}'.format(altdisk_status))

    results['status'] = altdisk_status
    results['output'] = OUTPUT
    results['msg'] = 'VIOS alt disk operation completed successfully'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
