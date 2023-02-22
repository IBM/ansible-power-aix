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
short_description: Alternate rootvg disk management.
description:
- Copy the rootvg to an alternate disk or cleanup an existing one on a logical partition (LPAR).
version_added: '1.1.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorizations: B(aix.system.install,aix.lvm.manage.change)'
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
    - Either I(targets) or I(disk_size_policy) must be specified.
    - If no I(targets) disk is specified, it will look for a valid candidate disk based on the
      provided I(disk_size_policy) policy.
    type: list
    elements: str
  disk_size_policy:
    description:
    - When I(action=copy), specifies how to choose the alternate disk if I(targets) is not
      specified.
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
  bootlist:
    description:
    - When I(action=copy), specifies to run bootlist after the alternate disk copy.
    type: bool
    default: no
  remain_nim_client:
    description:
    - When I(action=copy), specifies to copy the C(/.rhosts) and C(/etc/niminfo) files to the
      alternate rootvg.
    type: bool
    default: no
  device_reset:
    description:
    - When I(action=copy), specifies to reset any user-defined device configurations on the target
      C(altinst_rootvg).
    type: bool
    default: no
  first_boot_script:
    description:
    - When I(action=copy), specifies an optional customization script to run during the initial boot
      of the alternate rootvg, after all file systems are mounted.
    type: str
  resolvconf:
    description:
    - When I(action=copy), specifies the C(resolv.conf) file to replace the existing one after the
      rootvg has been cloned.
    type: str
  allow_old_rootvg:
    description:
    - Allows the removal or cleanup of existing old rootvg as well.
    type: bool
    default: no
notes:
  - M(alt_disk) only backs up mounted file systems. Mount all file
    systems that you want to back up.
  - When no target is specified, copy is performed to only one alternate
    disk even if the rootvg contains multiple disks.
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/a_commands/alt_disk_copy.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/a_commands/alt_rootvg_op.html).
'''

EXAMPLES = r'''
- name: Perform an alternate disk copy of the rootvg to hdisk1
  alt_disk:
    action: copy
    targets: hdisk1

- name: Perform an alternate disk copy of the rootvg to the smallest disk that can be selected
  alt_disk:
    action: copy
    disk_size_policy: minimize

- name: Perform a cleanup of any existing alternate disk copy
  alt_disk:
    action: clean

- name: Perform a cleanup of any existing alternate disk copy and old rootvg
  alt_disk:
    action: clean
    allow_old_rootvg: yes
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'alt disk copy operation completed successfully'
stdout:
    description: The standard output.
    returned: always
    type: str
    sample: 'Bootlist is set to the boot disk: hdisk0 blv=hd5'
stderr:
    description: The standard error.
    returned: always
    type: str
'''

import os.path
import re

from ansible.module_utils.basic import AnsibleModule

results = None


def get_pvs(module):
    """
    Get the list of PVs.

    return: dictionary with PVs information
    """

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
            # Check if the disk has VG info in ODM using getlvodm
            cmd = ['getlvodm', '-j', hdisk]
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 3:
                module.log('[WARN] could not query pv {0}'.format(hdisk))
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


def find_valid_altdisk(module, hdisks, rootvg_info, disk_size_policy, force, allow_old_rootvg):
    """
    Find a valid alternate disk that:
    - exists,
    - is not part of a VG
    - with a correct size
    and so can be used.
    """

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
    found_oldrootvg = ''
    for pv in pvs:
        if pvs[pv]['vg'] == 'altinst_rootvg':
            found_altdisk = pv
            break
    for pv in pvs:
        if allow_old_rootvg and pvs[pv]['vg'] == 'old_rootvg':
            found_oldrootvg = pv
            break
    if found_altdisk or found_oldrootvg:
        if not force:
            if found_altdisk:
                results['msg'] = 'An alternate disk already exists on disk {0}'.format(found_altdisk)
            elif found_oldrootvg:
                results['msg'] = 'An old rootvg already exists on disk {0}'.format(found_oldrootvg)
            module.fail_json(**results)

        # Clean existing altinst_rootvg
        if found_altdisk:
            module.log('Removing altinst_rootvg')
            cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                results['stdout'] = stdout
                results['stderr'] = stderr
                results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
                module.fail_json(**results)

        # Clean existing old_rootvg
        if found_oldrootvg:
            module.log('Removing old_rootvg')
            cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'old_rootvg']
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                results['stdout'] = stdout
                results['stderr'] = stderr
                results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
                module.fail_json(**results)

        results['changed'] = True

        for pv in pvs:
            if (pvs[pv]['vg'] == 'altinst_rootvg') or (allow_old_rootvg and pvs[pv]['vg'] == 'old_rootvg'):
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


def alt_disk_copy(module, params, hdisks, allow_old_rootvg):
    """
    alt_disk_copy operation

    - check the rootvg, find and validate the hdisks for the operation
    - perform the alt disk copy operation
    """

    # Either hdisks must be non-empty or disk_size_policy must be
    # explicitly set. This ensures the user knows what he is doing.
    if not hdisks and not params['disk_size_policy']:
        results['msg'] = 'Either targets or disk_size_policy must be specified'
        module.fail_json(**results)

    rootvg_info = check_rootvg(module)
    if rootvg_info is None:
        module.fail_json(**results)

    if hdisks is None:
        hdisks = []
    find_valid_altdisk(module, hdisks, rootvg_info, params['disk_size_policy'], params['force'], allow_old_rootvg)

    module.log('Using {0} as alternate disks'.format(hdisks))

    # alt_disk_copy
    cmd = ['alt_disk_copy', '-d', ' '.join(hdisks)]
    if not params['bootlist']:
        cmd += ['-B']
    if params['remain_nim_client']:
        cmd += ['-n']
    if params['device_reset']:
        cmd += ['-O']
    if params['first_boot_script']:
        cmd += ['-x', params['first_boot_script']]
    if params['resolvconf']:
        cmd += ['-R', params['resolvconf']]

    ret, stdout, stderr = module.run_command(cmd)
    results['rc'] = ret
    results['cmd'] = ' '.join(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        # an error occured during alt_disk_copy
        results['msg'] = 'Failed to copy {0}: return code {1}.'.format(' '.join(hdisks), ret)
        module.fail_json(**results)
    results['changed'] = True


def alt_disk_clean(module, hdisks, allow_old_rootvg):
    """
    alt_disk_clean operation

    - cleanup alternate disk volume group (alt_rootvg_op -X)
    - clear the owning volume manager from each disk (chpv -C)
    """

    pvs = get_pvs(module)
    if pvs is None:
        module.fail_json(**results)

    found_altdisk = False
    found_oldrootvg = False

    if hdisks:
        # Check that all specified disks exist and belong to altinst_rootvg
        for hdisk in hdisks:
            if (hdisk not in pvs) or ((pvs[hdisk]['vg'] != 'altinst_rootvg') and (not allow_old_rootvg or pvs[hdisk]['vg'] != 'old_rootvg')):
                results['msg'] = 'Specified disk {0} is not an alternate install rootvg'\
                                 .format(hdisk)
                module.fail_json(**results)

            if pvs[hdisk]['vg'] == 'altinst_rootvg':
                found_altdisk = True
            if allow_old_rootvg and pvs[hdisk]['vg'] == 'old_rootvg':
                found_oldrootvg = True
    else:
        # Retrieve the list of disks that belong to altinst_rootvg
        hdisks = []
        for pv in pvs.keys():
            if pvs[pv]['vg'] == 'altinst_rootvg':
                found_altdisk = True
                hdisks.append(pv)
            if allow_old_rootvg and pvs[pv]['vg'] == 'old_rootvg':
                found_oldrootvg = True
                hdisks.append(pv)
        if not hdisks:
            # Do not fail if there is no altinst_rootvg to preserve idempotency
            results['msg'] += "There is no alternate install rootvg. "
            return

    # First remove the alternate VG

    if found_altdisk:
        module.log('Removing altinst_rootvg')

        cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'altinst_rootvg']
        ret, stdout, stderr = module.run_command(cmd)
        results['rc'] = ret
        results['cmd'] = ' '.join(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr

        if ret != 0:
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)

    if found_oldrootvg:
        module.log('Removing old_rootvg')

        cmd = ['/usr/sbin/alt_rootvg_op', '-X', 'old_rootvg']
        ret, stdout, stderr = module.run_command(cmd)
        results['rc'] = ret
        results['cmd'] = ' '.join(cmd)
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
            bootlist=dict(type='bool', default=False),
            remain_nim_client=dict(type='bool', default=False),
            device_reset=dict(type='bool', default=False),
            first_boot_script=dict(type='str'),
            resolvconf=dict(type='str'),
            allow_old_rootvg=dict(type='bool', default=False),
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
    allow_old_rootvg = module.params['allow_old_rootvg']

    if action == 'copy':
        alt_disk_copy(module, module.params, targets)
    else:
        alt_disk_clean(module, targets, allow_old_rootvg)

    results['msg'] += 'alt_disk {0} operation completed successfully'.format(action)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
