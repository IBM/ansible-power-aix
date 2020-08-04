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
module: backup
short_description: Manage data or system volume group backup on a LPAR.
description:
- This module manages backup image of data or system volume group.
- It uses mksysb or savevg command to create the backup image of the volume group either in a file
  or onto a device.
- It uses restvg or alt_disk_mksysb to restore a backup image to a disk.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform on the LPAR.
    - C(create) to create a backup image.
    - C(restore) to restore a backup image.
    - C(view) to get useful information about a backup image.
    type: str
    choices: [ create, restore ]
    required: true
  os_backup:
    description:
    - Specifies the operation concerns the Operating system.
    - If I(yes), it will use mksysb to create an Operating System backup of the root volume group
      and alt_disk_mksysb to restore the backup image onto a disk.
    - If I(no), it will use savevg to list and back up all files belonging to a volume group and
      restvg to restore a backup image onto a disk.
    type: bool
    default: no
  name:
    description:
    - Specifies the targets of the operation.
    - Required if C(action=create) and C(os_backup=no), then it specifies the volume group to back up.
    - If C(action=restore), it specifies the disk device to restore to and do not use the one in
      the vgname.data file.
    type: str
  flags:
    description:
    - Specifies additional flag to pass to the command. Refers to IBM documentation for details.
    - For C(action=create) and C(os_backup=no), you could use I(-a -A -b Blocks -p -T -V -Z).
    - For C(action=restore) and C(os_backup=no), you could use I(-b Blocks -n -P PPsize).
    type: str
  location:
    description:
    - Specifies the location of the backup files. It can be a device or file path.
    - When C(os_backup=no), the default device is I(/dev/rmt0).
    - Can be used if C(os_backup=no). Required if C(action=view).
    type: path
  data_file:
    description:
    - Specifies a filename to be used as the vgname.data file instead of the one contained within
      the backup image being restored.
    - The filename can be specified by either a relative or an absolute pathname.
    - Can be used if C(os_backup=no) and C(action=restore).
    type: path
  use_data_file:
    description:
    - Specifies to create the data file containing information including the list of logical volumes
      file systems and their sizes, and the volume group name.
    - When C(volume_group) is the rootvg, data file will be in I(/image.data).
    - When C(volume_group) is a data volume group, data file will be in
      I(/tmp/vgdata/vgname/vgname.data).
    - Specify C(use_data_file=mapfile) to creates the MAPFILE containing the mapping of the logical
      to physical partitions for each logical volume in the volume group. This mapping can be used
      to allocate the same logical-to-physical mapping when the image is restored.
    - Can be used if C(action=create) and C(os_backup=no).
    type: str
    choices: [ yes, mapfile, no ]
    default: no
  exclude_file:
    description:
    - Specifies the exclude file path. This file lists the file systems ito exclude from the backup.
    - One file system mount point is listed per line.
    - Can be used if C(action=create) and C(os_backup=no).
    type: path
  exclude_data:
    description:
    - If C(action=create), specifies to exclude user data from the backup. Backs up user volume
      group information and administration data files. This backs up files such as
      /tmp/vgdata/vgname/vgname.data and map files if any exist. Cannot be used on a rootvg.
    - If C(action=restore), specifies to recreate the volume group structure only without restoring
      any files or data.
    - Can be used if C(os_backup=no) and C(action=create) or C(action=restore).
    type: bool
    default: no
  extend_fs:
    description:
    - Specifies to extend the filesystem if needed.
    - Can be used if C(action=create) and C(os_backup=no).
    type: bool
    default: no
  minimal_lv_size:
    description:
    - Specifies to create the logical volumes with minimum size possible to accomodate
      the file system.
    - Can be used if C(action=restore) and C(os_backup=no).
    type: bool
    default: no
  verbose:
    description:
    - Specifies to run the operation in verbose mode.
    - Can be used if C(action=create) or C(action=restore).
    type: bool
    default: no
notes:
  - C(savevg) only backs up varied-on volume group. The file systems must be mounted.
'''

EXAMPLES = r'''
- name: Perform an alternate disk copy of the rootvg to hdisk1
  backup:
    action: create
    targets: hdisk1
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'AIX backup create operation successfull.'
stdout:
    description: The standard output of the command.
    returned: always
    type: str
    sample: 'Bootlist is set to the boot disk: hdisk0 blv=hd5'
stderr:
    description: The standard error of the command.
    returned: always
    type: str
rc:
    description:
    - The return code of the command.
    - Equal I(-1) when the command has not been run.
    returned: always
    type: int
'''

from ansible.module_utils.basic import AnsibleModule


def check_vg(module, vg):
    """
    Check if the volume group is active (i.e. varied-on).

    arguments:
        module  (dict): The Ansible module
        vg       (str): the volume group to back up
    return:
        True if the vg can be used
        False otherwise
    """
    global results

    # list active volume groups
    cmd = ['/usr/sbin/lsvg', 'o']
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        vgs = stdout.splitlines()
        module.log('checking {0}, active volume groups: {1}'.format(vg, vgs))
        if vg in vgs:
            return True

    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    return False


def mksysb(module, params):
    """
    Perform a mksysb of the OS.

    arguments:
        module      (dict): The Ansible module
        params  (dict): the command parameters
    return:
        True if backup succeeded
        False otherwise
    """
    global results

    # mksysb  device | file
    # not yet implemented:
    # [ -a ] [ -A ] [ -b number ] [ -e ] [ -F filename ] [ -i ] [ -m ] [ -p ] [ -P ]
    # [ -t argument ] [ -v ] [ -V ] [-x file ] [ -X ] [-Z] [ -G | -N ] [-M] [ -T ]
    cmd = ['/bin/mksysb']

    if params['flags']:
        for f in params['flags']:
            cmd += [f]

    return True


def alt_disk_mksysb(module, params):
    """
    Installs an alternate disk with a mksysb install base install image.

    arguments:
        module      (dict): The Ansible module
        params  (dict): the command parameters
    note:
    return:
        True if backup succeeded
        False otherwise
    """
    global results

    # alt_disk_mksysb -m device -d target_disks...
    # not yet implemented:
    # [ -i image.data ] [ -s script ] [-R resolv_conf ] [ -p platform ] [ -L mksysb_level ]
    # [ -n ]
    # [ -P phase_option ]
    # [ -c console ]
    # [ -K ]
    # [ -D B O V g k r y z T S C ]
    cmd = ['/usr/sbin/alt_disk_mksysb']
    if params['flags']:
        for f in params['flags']:
            cmd += [f]
    module.log('cmd: {0}'.format(cmd))

    return True


def savevg(module, params, vg):
    """
    Run the savevg command to back up files of a volume group.
    But first, checks the volume group is varied-on.

    arguments:
        module  (dict): the module variable
        params  (dict): the command parameters
        vg       (str): the volume group to back up
    return:
        rc       (int): the return code of the command
    """
    global results

    if not check_vg(module, vg):
        results['msg'] = 'Volume group {0} is not active, please vary on the volume group.'.format(vg)
        return 1

    # TODO Check if an existing backup is overwritten. Does it errors? Do we need a force option?

    # savevg VGName
    # [ -e ]        Excludes files specified in the /etc/exclude.vgname file from being backed up.
    # [ -f Device ] Device of file to store the image. Default is I(/dev/rmt0).
    # [ -i | -m ]   Create the data file calling mkvgdata (-m for map file).
    # [ -r ]        Backs up user VG inforamtion and administration data files. Does not back up user data files.
    # [ -v ]        Verbose mode.
    # [-x file]     Exclude fs listed in the file (one per line).
    # [ -X ]        Extend fs if needed.
    # not yet implemented:
    # [ -a ]        Does not back up extended attributes or NFSv4 ACLs.
    # [ -A ]        Backs up DMAPI file system files.
    # [ -b Blocks ] Specifies the number of 512-byte blocks to write in a single output operation.
    # [ -p ]        Disable software packing (tape drives).
    # [ -T ]        Create backup using snapshots.
    # [ -V ]        Verify a tape backup.
    # [ -Z ]        Does not back up the EFS information for all the files, directories, and file systems.
    cmd = ['/bin/savevg']
    if params['exclude_file']:
        cmd += ['-e', params['exclude_file']]
    if params['location']:
        cmd += ['-f', params['location']]
    if params['use_data_file'] == 'mapfile':
        cmd += ['-m']
    elif params['use_data_file']:
        cmd += ['-i']
    if params['exclude_data']:
        cmd += ['-r']
    if params['verbose']:
        cmd += ['-v']
    if params['exclude_file_system']:
        cmd += ['-x', params['exclude_file_system']]
    if params['extend_fs']:
        cmd += ['-X']
    if params['flags']:
        for f in params['flags']:
            cmd += [f]
    cmd += [vg]

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if rc == 0:
        results['changed'] = True
    return rc


def restvg(module, params, action, disk):
    """
    Run the restvg command to restore to backup files to a disk.

    arguments:
        module  (dict): the module variable
        params  (dict): the command parameters
        action   (str): the action to perform, can be view or restore.
        disk     (str): the disk to restore the volume group backup to
    return:
        rc       (int): the return code of the command
    """
    global results
    # savevg [DiskName]
    # [ -d FileName ]   Uses a file (absolute or relative path) instead of the vgname.data file in the backup image.
    # [ -f Device ]     Device of file to store the image. Default is I(/dev/rmt0).
    # [ -l ]            Displays useful information about a volume group backup. Used when action is 'view'.
    # [ -q ]            Does not display the VG name and target disk device name usual prompt before restoration.
    # [ -r ]            Recreates a VG structure only without restoring any files or data.
    # [ -s ]            Creates the LV with minimum size possible to accomodate the file system.
    # not yet implemented:
    # [ -b Blocks ]     Specifies the number of 512-byte blocks to write in a single output operation
    # [ -n ]            Ignores the existing MAP files.
    # [ -P PPsize ]     Specifies the number of megabytes in each physical partition.
    cmd = ['restvg']
    if params['data_file']:
        cmd += ['-d', params['data_file']]
    if params['location']:
        cmd += ['-f', params['location']]
    if action == 'view':
        cmd += ['-l']
    if not params['verbose']:
        cmd += ['-q']
    if params['exclude_data']:
        cmd += ['-r']
    if params['minimal_lv_size']:
        cmd += ['-s']
    if params['flags']:
        for f in params['flags']:
            cmd += [f]
    if disk:
        cmd += [disk]

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    if rc == 0:
        results['changed'] = True
    return rc


def main():
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, type='str',
                        choices=['create', 'restore']),
            os_backup=dict(type='bool', default=False),
            name=dict(type='str'),
            flags=dict(type='str'),
            # for savevg and restvg
            location=dict(type='path'),
            exclude_data=dict(type='bool', default=False),
            verbose=dict(type='bool', default=False),
            # for savevg
            use_data_file=dict(type='str', choices=[True, 'mapfile', False], default=False),
            exclude_file=dict(type='path'),
            extend_fs=dict(type='bool', default=False),
            # for restvg
            data_file=dict(type='path'),
            minimal_lv_size=dict(type='bool', default=False),
        ),
        required_if=[
            ['action', ['view'], ['location']],
        ],
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        rc=-1,
    )

    params = {}
    action = module.params['action']
    params['flags'] = module.params['flags']

    if action == 'create':
        if not params['os_backup']:

            rc = mksysb(module, params)

        else:
            params['name'] = module.params['name']
            params['location'] = module.params['location']
            params['exclude_data'] = module.params['exclude_data']
            params['verbose'] = module.params['verbose']
            params['use_data_file'] = module.params['use_data_file']
            params['exclude_file'] = module.params['exclude_file']
            params['extend_fs'] = module.params['extend_fs']

            if not params['name']:
                results['msg'] = 'Missing parameter: action is {0} but argument \'name\' is missing.'.format(action)
                module.fail_json(**results)
            if params['exclude_data'] and params['name'] == 'rootvg':
                results['msg'] = 'Bad parameter: exclude_data is {0}, name cannot be \'rootvg\'.'.format(params['exclude_data'])
                module.fail_json(**results)

            rc = savevg(module, params, params['name'])

    elif action == 'restore':
        if params['os_backup']:

            rc = alt_disk_mksysb(module, params)

        else:
            params['name'] = module.params['name']
            params['location'] = module.params['location']
            params['exclude_data'] = module.params['exclude_data']
            params['verbose'] = module.params['verbose']
            params['data_file'] = module.params['data_file']
            params['minimal_lv_size'] = module.params['minimal_lv_size']

            rc = restvg(module, params, action, params['name'])

    elif action == 'view':
        params['location'] = module.params['location']

        if not params['location'] or not params['location'].strip():
            results['msg'] = 'Missing parameter: action is {0} but argument \'location\' is missing.'.format(action)
            module.fail_json(**results)

        rc = restvg(module, params, action, params['name'])

    if rc == 0:
        results['msg'] = 'AIX backup {0} operation successfull.'.format(action)
        module.exit_json(**results)
    else:
        if not results['msg']:
            results['msg'] = 'AIX backup {0} operation failed.'.format(action)
        module.fail_json(**results)


if __name__ == '__main__':
    main()
