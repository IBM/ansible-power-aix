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
- AIX Development Team (@jdejoya17)
module: nim_select_target_disk
short_description: verify/autoselect a disk used for alternate disk migration role.
description:
- Verify validity of user specified disk or automatically select a valid disk based on disk size policy.
version_added: '1.5.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorizations: B(aix.system.install,aix.lvm.manage.change)'
options:
  nim_client:
    description:
    - Specifies which NIM client LPAR to select target disks from.
    type: str
    required: true
  target_disk:
    description:
    - Specifies which physical volume in I(nim_client) to verify if it is available.
    type: str
  target_disk_policy:
    description:
    - C(minimize) smallest disk that can be selected.
    - C(upper) first disk found bigger than the rootvg disk.
    - C(lower) disk size less than rootvg disk size but big enough to contain the used PPs.
    - C(nearest) disk size closest to the rootvg disk.
    - if C(upper) or C(lower) cannot be satisfied, it will default to C(minimize).
    - if an alternate disk copy exists, then this module will fail regardless of the policy selected.
    - if I(force) parameter is used while an alternate disk copy exists, then it will clean up the disk.
    type: str
    choices: [ 'minimize', 'upper', 'lower', 'nearest' ]
  force:
    description:
    - Forces removal of any existing alternate disk copy on target disks for
      I(target_disk_policy).
    - Removes I(target_disk) from an online volume group.
    type: bool
    default: no
'''


EXAMPLES = r'''
- name: validate hdisk1 for availability and size
  ibm.power_aix.internal.nimadm_select_target_disk:
    nim_client: aix1
    target_disk: hdisk1

- name: validate hdisk1 for availability and size and
        cleanup disk if needed
  ibm.power_aix.internal.nimadm_select_target_disk:
    nim_client: aix1
    target_disk: hdisk1
    force: true

- name: automatically select valid disks for altinst_rootvg
        installation based on policy
  ibm.power_aix.internal.nimadm_select_target_disk:
    nim_client: aix1
    target_disk_policy: minimize

- name: select physical volume where an existing altinst_rootvg
        resides and clean it up to be used to alt disk migration
  ibm.power_aix.internal.nimadm_select_target_disk:
    nim_client: aix1
    target_disk_policy: minimize
    force: true
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
target_disk:
    description: The selected target disk used for alternate disk migration
    returned: always
    type: str
    sample: 'hdisk1'
valid:
    description: Determines if the selected target disk is valid. Which means
     it is both available and has enough space for used physical
     partitions of rootvg
    returned: always
    type: bool
    sample: True
'''

import re
from ansible.module_utils.basic import AnsibleModule

results = None


def fail_handler(module, rc, cmd, stdout, stderr, msg=None):
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr
    if results is None:
        results['msg'] += 'Command \'{0}\' failed with return code {1}.'.format(
            ' '.join(cmd), rc)
    else:
        results['msg'] += msg
    module.fail_json(**results)


def clean_disk(module, disk_name, pvs):
    nim_client = module.params['nim_client']

    # cleanup for disks that belong to altinst_rootvg or old_rootvg
    if pvs[disk_name]['vg'] == 'altinst_rootvg' or pvs[disk_name]['vg'] == 'old_rootvg':
        # Clean existing altinst_rootvg or old_rootvg
        module.log('Removing {0}'.format(pvs[disk_name]['vg']))
        cmd = [
            '/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
            nim_client,
            '/usr/sbin/alt_rootvg_op -X {0}'.format(pvs[disk_name]['vg'])
        ]
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            fail_handler(module, rc, cmd, stdout, stderr)
        results['changed'] = True

    # cleanup for disks that belong to any other volume group
    else:
        module.log('Removing physical volume {0} from volume group {1}'.format(
            disk_name, pvs[disk_name]['vg']
        ))
        # reduce PV from active volume group
        if pvs[disk_name]['status'] == 'active':
            cmd = [
                '/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
                nim_client,
                '/usr/sbin/reducevg -df {0} {1}'.format(pvs[disk_name]['vg'], disk_name)
            ]
        # if VG where PV belongs is varied off
        else:
            results['msg'] += "Unable to cleanup {0} because it belongs ".format(disk_name)
            results['msg'] += "to a varied off volume group."
            return False

        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            fail_handler(module, rc, cmd, stdout, stderr)
        results['changed'] = True

    module.log('Clearing the owning VG from disk {0}'.format(disk_name))
    cmd = [
        '/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
        nim_client,
        '/usr/sbin/chpv -C {0}'.format(disk_name)
    ]
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        fail_handler(module, rc, cmd, stdout, stderr)
    results['changed'] = True
    return True


def belong_to_vg(module, target_disk):
    """
    Check in ODM if target_disk belongs to a volume group.
    return:
        True - target disk belongs to a volume group
        False - target disk does not belong to a volume group
    """
    nim_client = module.params['nim_client']
    # check if 'target_disk' does not belong to any volume group
    cmd = [
        '/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
        nim_client,
        '/usr/sbin/getlvodm -j {0}'.format(target_disk)
    ]
    rc, stdout, stderr = module.run_command(cmd)
    # 0516-320 /usr/sbin/getlvodm: Physical volume hdisk1 is not assigned to
    #        a volume group.
    # physical volume belongs to a volume group if 'found' is not null
    # pattern = r"0516-320"
    pattern = r"0516-320|0516-1396"
    found = re.search(pattern, stderr, re.MULTILINE)
    if rc != 0 and not found:
        fail_handler(module, rc, cmd, stdout, stderr)
    else:
        if stdout != "" or (stderr != "" and not found):
            return True
    return False


def is_valid(module, target_disk):
    """
    Check if target disk is valid
    - must not belong to a volume group
    - must have space big enough for rootvg used PPs
    return:
        True - target disk can be used for alt_disk
        False - target disk cannot be used for alt_disk
    """
    nim_client = module.params['nim_client']
    force = module.params['force']

    # fetch rootvg disk information on the NIM client
    rootvg_info = check_rootvg(module)

    # fetch physical volume size or the target disk
    cmd = [
        '/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
        nim_client,
        '/usr/sbin/bootinfo -s {0}'.format(target_disk)
    ]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        fail_handler(module, rc, cmd, stdout, stderr)
    else:
        pv_size = int(stdout)

    # make sure there is enough space in the target_disk for rootvg
    if pv_size < rootvg_info["used_size"]:
        results['msg'] += "There is not enough space in {0}".format(target_disk)
        results['msg'] += " for an alternate disk.\n"
        return False

    # check if 'target_disk' does not belong to any volume group
    if belong_to_vg(module, target_disk):
        if force:
            pvs = get_pvs(module)
            cleaned = clean_disk(module, target_disk, pvs)
            if not cleaned:
                return False
        else:
            results['msg'] += "Physical volume '{0}' belongs ".format(target_disk)
            results['msg'] += "to a volume group.\n"
            results['rc'] = rc
            results['stdout'] = stdout
            results['stderr'] = stderr
            return False

    # target disk is available and big enough for rootvg
    results['msg'] += "The physical volume {0} is a valid target disk.\n".format(target_disk)
    return True


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

    nim_client = module.params["nim_client"]
    vg_info = {}
    vg_info["status"] = 1
    vg_info["rootvg_size"] = 0
    vg_info["used_size"] = 0

    total_pps = -1
    used_pps = -1
    pp_size = -1

    # get the rootvg pp size
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', nim_client, '/usr/sbin/lsvg rootvg']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        fail_handler(module, rc, cmd, stdout, stderr)

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

        match_key = re.match(r"TOTAL PVs:\s+(\d+)\s+.*", line)
        if match_key:
            total_pvs = int(match_key.group(1))
            continue

    if total_pps == -1 or used_pps == -1 or pp_size == -1:
        msg = 'Failed to get rootvg size, parsing error.\n'
        fail_handler(module, rc, cmd, stdout, stderr, msg=msg)

    total_size = pp_size * total_pps / total_pvs
    used_size = pp_size * used_pps / total_pvs

    vg_info["status"] = 0
    vg_info["rootvg_size"] = total_size
    vg_info["used_size"] = used_size
    return vg_info


def get_pvs(module):
    """
    Get the list of PVs.

    return: dictionary with PVs information
    """
    nim_client = module.params["nim_client"]

    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', nim_client, '/usr/sbin/lspv']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        fail_handler(module, rc, cmd, stdout, stderr)

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


def get_free_pvs(module, pvs):
    """
    Get the list of free PVs.

    return: dictionary with free PVs information
    """
    nim_client = module.params["nim_client"]

    # hdisk0           000018fa3b12f5cb                     rootvg           active
    free_pvs = {}
    for pv in pvs.keys():
        # Only match disks that have no volume groups
        if pvs[pv]['vg'] == 'None':
            # Check if the disk has VG info in ODM using getlvodm
            if belong_to_vg(module, pv):
                continue

            # Retrieve disk size
            cmd = [
                '/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
                nim_client,
                '/usr/sbin/bootinfo -s {0}'.format(pv)
            ]
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                module.log('[WARN] could not retrieve {0} size'.format(pv))
                continue
            size = stdout.strip()

            free_pvs[pv] = pvs[pv]
            free_pvs[pv]['size'] = int(size)

    module.debug('List of available PVs:')
    for key in free_pvs.keys():
        module.debug('    free_pvs[{0}]: {1}'.format(key, free_pvs[key]))

    return free_pvs


def find_valid_altdisk(module):
    """
    Find a valid alternate disk that:
    - exists,
    - is not part of a VG
    - with a correct size
    and so can be used.
    """
    disk_size_policy = module.params['target_disk_policy']
    force = module.params['force']
    rootvg_info = check_rootvg(module)

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
        if pvs[pv]['vg'] == 'altinst_rootvg' or pvs[pv]['vg'] == 'old_rootvg':
            found_altdisk = pv
            break

    if found_altdisk:
        if not force:
            results['msg'] += "An alternate disk already exists on disk '{0}'.\n".format(found_altdisk)
            return found_altdisk, False

        # Clean existing altinst_rootvg
        cleaned = clean_disk(module, found_altdisk, pvs)
        if cleaned:
            return found_altdisk, True
        else:
            return found_altdisk, False

    pvs = get_free_pvs(module, pvs)
    if pvs is None:
        module.fail_json(**results)
    if not pvs:
        results['msg'] += 'No free disk available\n'
        return None, False

    used_size = rootvg_info["used_size"]
    rootvg_size = rootvg_info["rootvg_size"]
    selected_disk = ""
    prev_disk = ""
    diffsize = 0
    prev_diffsize = 0
    # parse free disks in increasing size order
    for pv in sorted(pvs, key=lambda k: pvs[k]['size']):
        # disk too small, skip
        if pvs[pv]['size'] < used_size:
            continue

        # smallest disk that can be selected
        if disk_size_policy == 'minimize':
            selected_disk = pv
            break

        diffsize = pvs[pv]['size'] - rootvg_size
        # matching disk size
        if diffsize == 0:
            selected_disk = pv
            break

        if diffsize > 0:
            # diffsize > 0: first disk found bigger than the rootvg disk
            if disk_size_policy == 'upper':
                selected_disk = pv
            elif disk_size_policy == 'lower':
                if not prev_disk:
                    # Best Can Do...
                    results['msg'] += "Disk size policy 'lower' could not be met."
                    results['msg'] += "Selecting available disk meeting 'minimize' policy."

                    selected_disk = pv
                else:
                    selected_disk = prev_disk
            elif disk_size_policy == 'nearest':
                if not prev_disk:
                    selected_disk = pv
                elif abs(prev_diffsize) > diffsize:
                    selected_disk = pv
                else:
                    selected_disk = prev_disk
            break
        # disk size less than rootvg disk size
        #   but big enough to contain the used PPs
        prev_disk = pv
        prev_diffsize = diffsize

    if not selected_disk:
        if prev_disk:
            # Best Can Do...
            results['msg'] += "Disk size policy 'upper' could not be met."
            results['msg'] += "Selecting available disk meeting 'minimize' policy."
            selected_disk = prev_disk
        else:
            results['msg'] += 'No available alternate disk with size greater than {0} MB'\
                ' found.\n'.format(rootvg_size)
            return None, False

    module.debug('Selected disk is {0} (select mode: {1})'.format(
        selected_disk, disk_size_policy)
    )
    results['msg'] += "Selected disk is {0}".format(selected_disk)
    results['msg'] += " (select mode: {0})\n".format(disk_size_policy)
    return selected_disk, True


def main():
    global results
    module = AnsibleModule(
        argument_spec=dict(
            nim_client=dict(type='str', required=True),
            target_disk=dict(type='str'),
            target_disk_policy=dict(
                type='str',
                choices=['minimize', 'upper', 'lower', 'nearest']
            ),
            force=dict(type='bool', default=False),
        ),
        mutually_exclusive=[
            ['targets_disk', 'target_disk_policy']
        ],
    )

    results = dict(
        changed=False,
        msg='',
        rc=0,
        stdout='',
        stderr='',
    )

    target_disk = module.params['target_disk']
    if target_disk is not None:
        results['target_disk'] = target_disk
        results['valid'] = is_valid(module, target_disk)
    else:
        target_disk, valid = find_valid_altdisk(module)
        results['target_disk'] = target_disk
        results['valid'] = valid

    module.exit_json(**results)


if __name__ == '__main__':
    main()
