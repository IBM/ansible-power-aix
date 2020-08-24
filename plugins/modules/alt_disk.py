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
module: alt_disk
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
    - Specifies the operation to perform.
    - C(copy) to perform and alternate disk copy.
    - C(clean) to cleanup an existing alternate disk copy.
    type: str
    choices: [ copy, clean ]
    default: copy
  targets:
    description:
    - Specifies the target disks.
    type: list
    elements: str
  disk_size_policy:
    description:
    - When I(action=copy), specifies how to choose the alternate disk if I(targets) is not specified.
    - C(minimize) smallest disk that can be selected.
    - C(upper) first disk found bigger than the rootvg disk.
    - C(lower) disk size less than rootvg disk size but big enough to contain the used PPs.
    - C(nearest) disk size closest to the rootvg disk.
    type: str
    choices: [ minimize, upper, lower, nearest ]
  force:
    description:
    - Forces removal of any existing alternate disk copy on target disks.
    type: bool
    default: no
notes:
  - M(alt_disk) only backs up mounted file systems. Mount all file
    systems that you want to back up.
  - when no target is specified, copy is performed to only one alternate
    disk even if the rootvg contains multiple disks
'''

EXAMPLES = r'''
- name: Perform an alternate disk copy of the rootvg to hdisk1
  alt_disk:
    targets: hdisk1

- name: Perform an alternate disk copy of the rootvg to the smallest disk that can be selected
  alt_disk:
    disk_size_policy: minimize

- name: Perform a cleanup of any existing alternate disk copy
  alt_disk:
    action: clean
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'alt disk copy operation completed successfully'
stdout:
    description: The standard output
    returned: always
    type: str
    sample: 'Bootlist is set to the boot disk: hdisk0 blv=hd5'
stderr:
    description: The standard error
    returned: always
    type: str
'''

import os.path
import re

from ansible.module_utils.basic import AnsibleModule


def get_pvs(module):
    """
    Get the list of PVs.

    return: dictionary with PVs information
    """
    global results

    cmd = ['lspv']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        return None

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
    Get the list of free PVs.

    return: dictionary with free PVs information
    """
    global results

    cmd = ['lspv']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        return None

    # hdisk0           000018fa3b12f5cb                     rootvg           active
    free_pvs = {}
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(hdisk\S+)\s+(\S+)\s+(\S+)\s*(\S*)", line)
        # Only match disks that have no volume groups
        if match_key and match_key.group(3) == 'None':
            hdisk = match_key.group(1)
            # Check if the disk has an _LVM signature using lquerypv
            cmd = ['lquerypv', '-V', hdisk]
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                module.log('[WARN] could not query pv {0}'.format(hdisk))
                continue
            if stdout.strip() != "1":
                continue

            # Retrieve disk size using getconf (bootinfo -s is deprecated)
            cmd = ['getconf', 'DISK_SIZE', '/dev/' + hdisk]
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                module.log('[WARN] could not retrieve {0} size'.format(hdisk))
                continue
            size = stdout.strip()

            free_pvs[hdisk] = {}
            free_pvs[hdisk]['pvid'] = match_key.group(2)
            free_pvs[hdisk]['size'] = int(size)

    module.debug('List of available PVs:')
    for key in free_pvs.keys():
        module.debug('    free_pvs[{0}]: {1}'.format(key, free_pvs[key]))

    return free_pvs


def find_valid_altdisk(module, hdisks, rootvg_info, disk_size_policy, force):
    """
    Find a valid alternate disk that:
    - exists,
    - is not part of a VG
    - with a correct size
    and so can be used.
    """
    global results

    # check rootvg
    if rootvg_info['status'] != 0:
        results['msg'] = 'Wrong rootvg state'
        module.fail_json(**results)

    # get pv list
    pvs = get_pvs(module)
    if pvs is None:
        module.fail_json(**results)
    # check an alternate disk does not already exist
    found_altdisk = ''
    for pv in pvs:
        if pvs[pv]['vg'] == 'altinst_rootvg':
            found_altdisk = pv
            break
    if found_altdisk:
        if not force:
            results['msg'] = 'An alternate disk already exists on disk {0}'.format(found_altdisk)
            module.fail_json(**results)
        # Clean existing altinst_rootvg
        module.log('Removing altinst_rootvg')

        cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            results['stdout'] = stdout
            results['stderr'] = stderr
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)

        results['changed'] = True

        for pv in pvs:
            if pvs[pv]['vg'] == 'altinst_rootvg':
                module.log('Clearing the owning VG from disk {0}'.format(pv))

                cmd = ['/usr/sbin/chpv', '-C', pv]
                ret, stdout, stderr = module.run_command(cmd)
                if ret != 0:
                    results['stdout'] = stdout
                    results['stderr'] = stderr
                    results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
                    module.fail_json(**results)

    pvs = get_free_pvs(module)
    if pvs is None:
        module.fail_json(**results)
    if not pvs:
        results['msg'] = 'No free disk available'
        module.fail_json(**results)

    used_size = rootvg_info["used_size"]
    rootvg_size = rootvg_info["rootvg_size"]
    # in auto mode, find the first alternate disk available
    if not hdisks:
        selected_disk = ""
        prev_disk = ""
        diffsize = 0
        prev_diffsize = 0
        # parse free disks in increasing size order
        for key in sorted(pvs, key=lambda k: pvs[k]['size']):
            hdisk = key

            # disk too small, skip
            if pvs[hdisk]['size'] < used_size:
                continue

            # smallest disk that can be selected
            if disk_size_policy == 'minimize':
                selected_disk = hdisk
                break

            diffsize = pvs[hdisk]['size'] - rootvg_size
            # matching disk size
            if diffsize == 0:
                selected_disk = hdisk
                break

            if diffsize > 0:
                # diffsize > 0: first disk found bigger than the rootvg disk
                if disk_size_policy == 'upper':
                    selected_disk = hdisk
                elif disk_size_policy == 'lower':
                    if not prev_disk:
                        # Best Can Do...
                        selected_disk = hdisk
                    else:
                        selected_disk = prev_disk
                else:
                    # disk_size_policy == 'nearest'
                    if prev_disk == "":
                        selected_disk = hdisk
                    elif abs(prev_diffsize) > diffsize:
                        selected_disk = hdisk
                    else:
                        selected_disk = prev_disk
                break
            # disk size less than rootvg disk size
            #   but big enough to contain the used PPs
            prev_disk = hdisk
            prev_diffsize = diffsize

        if not selected_disk:
            if prev_disk:
                # Best Can Do...
                selected_disk = prev_disk
            else:
                results['msg'] = 'No available alternate disk with size greater than {0} MB'\
                                 ' found'.format(rootvg_size)
                module.fail_json(**results)

        module.debug('Selected disk is {0} (select mode: {1})'
                     .format(selected_disk, disk_size_policy))
        hdisks.append(selected_disk)

    # hdisks specified by the user
    else:
        tot_size = 0
        for hdisk in hdisks:
            if hdisk not in pvs:
                results['msg'] = 'Alternate disk {0} is either not found or not available'\
                                 .format(hdisk)
                module.fail_json(**results)
            tot_size += pvs[hdisk]['size']

        # check the specified hdisks are large enough
        if tot_size < rootvg_size:
            if tot_size >= used_size:
                module.log('[WARNING] Alternate disks smaller than the current rootvg.')
            else:
                results['msg'] = 'Alternate disks too small ({0} < {1}).'\
                                 .format(tot_size, rootvg_size)
                module.fail_json(**results)


def check_rootvg(module):
    """
    Check the rootvg
    - calculate the total and used size of the rootvg

    return:
        Dictionary with following keys: value
            "status":
                0 the rootvg can be saved with an alternate disk copy
                1 otherwise
            "rootvg_size": size in Megabytes (int)
            "used_size": size in Megabytes (int)
    """
    global results

    vg_info = {}
    vg_info["status"] = 1
    vg_info["rootvg_size"] = 0
    vg_info["used_size"] = 0

    total_pps = -1
    used_pps = -1
    pp_size = -1

    # get the rootvg pp size
    cmd = ['lsvg', 'rootvg']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        return None

    # parse lsvg output to get the size in megabytes:
    # TOTAL PPs:           639 (40896 megabytes)
    # USED PPs:            404 (25856 megabytes)
    # PP SIZE:             64 megabyte(s)
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r".*TOTAL PPs:\s+(\d+)\s+\(\d+\s+megabytes\).*", line)
        if match_key:
            total_pps = int(match_key.group(1))
            continue

        match_key = re.match(r".*USED PPs:\s+(\d+)\s+\(\d+\s+megabytes\).*", line)
        if match_key:
            used_pps = int(match_key.group(1))
            continue

        match_key = re.match(r".*PP SIZE:\s+(\d+)\s+megabyte\(s\)", line)
        if match_key:
            pp_size = int(match_key.group(1))
            continue

    if total_pps == -1 or used_pps == -1 or pp_size == -1:
        results['msg'] = 'Failed to get rootvg size, parsing error'
        return None

    total_size = pp_size * total_pps
    used_size = pp_size * used_pps

    vg_info["status"] = 0
    vg_info["rootvg_size"] = total_size
    vg_info["used_size"] = used_size
    return vg_info


def alt_disk_copy(module, hdisks, disk_size_policy, force):
    """
    alt_disk_copy operation

    - check the rootvg, find and validate the hdisks for the operation
    - perform the alt disk copy operation
    """
    global results

    # Either hdisks must be non-empty or disk_size_policy must be
    # explicitly set. This ensures the user knows what he is doing.
    if not hdisks and not disk_size_policy:
        results['msg'] = 'Either targets or disk_size_policy must be specified'
        module.fail_json(**results)

    rootvg_info = check_rootvg(module)
    if rootvg_info is None:
        module.fail_json(**results)

    if hdisks is None:
        hdisks = []
    find_valid_altdisk(module, hdisks, rootvg_info, disk_size_policy, force)

    module.log('Using {0} as alternate disks'.format(hdisks))

    # alt_disk_copy
    cmd = ['alt_disk_copy', '-B', '-d', ' '.join(hdisks)]

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        # an error occured during alt_root_vg
        results['msg'] = 'Failed to copy {0}: return code {1}.'.format(' '.join(hdisks), ret)
        module.fail_json(**results)
    results['changed'] = True


def alt_disk_clean(module, hdisks):
    """
    alt_disk_clean operation

    - cleanup alternate disk volume group (alt_rootvg_op -X)
    - clear the owning volume manager from each disk (chpv -C)
    """
    global results

    pvs = get_pvs(module)
    if pvs is None:
        module.fail_json(**results)

    if hdisks:
        # Check that all specified disks exist and belong to altinst_rootvg
        for hdisk in hdisks:
            if (hdisk not in pvs) or (pvs[hdisk]['vg'] != 'altinst_rootvg'):
                results['msg'] = 'Specified disk {0} is not an alternate install rootvg'\
                                 .format(hdisk)
                module.fail_json(**results)
    else:
        # Retrieve the list of disks that belong to altinst_rootvg
        hdisks = []
        for pv in pvs.keys():
            if pvs[pv]['vg'] == 'altinst_rootvg':
                hdisks.append(pv)
        if not hdisks:
            # Do not fail if there is no altinst_rootvg to preserve idempotency
            return

    # First remove the alternate VG
    module.log('Removing altinst_rootvg')

    cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
    ret, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    # Clears the owning VG from the disks
    for hdisk in hdisks:
        module.log('Clearing the owning VG from disk {0}'.format(hdisk))

        cmd = ['/usr/sbin/chpv', '-C', hdisk]
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            results['stdout'] = stdout
            results['stderr'] = stderr
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)

    results['changed'] = True


def main():
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str',
                        choices=['copy', 'clean'], default='copy'),
            targets=dict(type='list', elements='str'),
            disk_size_policy=dict(type='str',
                                  choices=['minimize', 'upper', 'lower', 'nearest']),
            force=dict(type='bool', default=False),
        ),
        mutually_exclusive=[
            ['targets', 'disk_size_policy']
        ],
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    # Make sure we are not running on a VIOS.
    # This could be dangerous because the automatic disk selection differs from VIOS.
    # It could think a disk is not being used when it is actually used (mapped to a client).
    if os.path.exists('/usr/ios'):
        results['msg'] = 'This should not be run on a VIOS'
        module.fail_json(**results)

    action = module.params['action']
    targets = module.params['targets']
    disk_size_policy = module.params['disk_size_policy']
    force = module.params['force']

    if action == 'copy':
        alt_disk_copy(module, targets, disk_size_policy, force)
    else:
        alt_disk_clean(module, targets)

    results['msg'] = 'alt_disk {0} operation completed successfully'.format(action)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
