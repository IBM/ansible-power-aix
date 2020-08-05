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
    choices: [ create, restore, view ]
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
  create_data_file:
    description:
    - Specifies to create the data file containing information including the list of logical volumes
      file systems and their sizes, and the volume group name.
    - When C(volume_group) is the rootvg, data file will be in I(/image.data).
    - When C(volume_group) is a data volume group, data file will be in
      I(/tmp/vgdata/vgname/vgname.data).
    - Specify C(create_data_file=mapfile) to creates the MAPFILE containing the mapping of the logical
      to physical partitions for each logical volume in the volume group. This mapping can be used
      to allocate the same logical-to-physical mapping when the image is restored.
    - Can be used if C(action=create) and C(os_backup=no).
    type: str
    choices: [ yes, mapfile, no ]
    default: no
  exclude_fs:
    description:
    - Specifies a file path that contains the list of file systems to exclude from the backup.
    - One file system mount point is listed per line.
    - Can be used if C(action=create) and C(os_backup=no).
    type: path
  force:
    description:
    - Specifies to overwrite existing backup image.
    - Can be used if C(os_backup=no) and C(action=create).
    type: bool
    default: no
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
  exclude_files:
    description:
    - Specifies to exclude files specified in the /etc/exclude.vgname file from being backed up.
    - The /etc/exclude.vgname file should contain patterns of file names that you do not want
      included in your system backup image. They are input to the pattern matching conventions of
      the grep command.
    - Can be used if C(action=create) and C(os_backup=no).
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
  - C(savevg) backs up all logical volume information and will be recreated. However, only
    JFS-mounted file system data will be backed up. Raw logical volume data will NOT be backed up
    using a savevg.
'''

EXAMPLES = r'''
- name: savevg of rootvg to /dev/hdisk1
  backup:
    action: create
    os_backup: no
    name: rootvg
    location: /dev/hdisk1
    exclude_data: no
    exclude_files: no
    exclude_fs: /tmp/exclude_fs_list
    create_data_file: yes
    extend_fs: yes
    verbose: yes

- name: savevg of datavg structure to /dev/hdisk2
  backup:
    action: create
    os_backup: no
    name: datavg
    location: /dev/hdisk2
    exclude_data: yes
    exclude_files: yes
    create_data_file: yes

- name: view the vg backup image stored on /dev/hdisk1 with savevg
  backup:
    action: view
    os_backup: no
    location: /dev/hdisk1

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
    module.log('Checking {0} is active.'.format(vg))

    # list active volume groups
    cmd = ['/usr/sbin/lsvg', '-o']
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        vgs = stdout.splitlines()
        module.log('Active volume groups are: {0}'.format(vgs))
        if vg in vgs:
            module.debug('volume group {0} is active'.format(vg))
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
    module.log('Creating OS backup with mksysb.')

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
    module.log('Restoring OS backup with alt_disk_mksysb.')

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
    module.log('Creating VG backup of {0} with savevg.'.format(vg))

    # Check if the backup image already exists
    if not params['force']:
        rc = restvg_view(module, params)
        if rc == 0:
            vg_name = [s for s in results['stdout'].splitlines() if "VOLUME GROUP:" in s][0].split(':')[1].strip()
            if vg_name == vg:
                results['msg'] = 'Backup images for {0} already exists.'.format(vg)
                return 0
            else:
                results['msg'] = 'Backup images already exists for {0} volume group. Use force to overwrite.'.format(vg_name)
                return 1
        else:
            results['msg'] = 'Cannot check {0} backup image existence.'.format(vg)
            return rc

    if not check_vg(module, vg):
        results['msg'] = 'Volume group {0} is not active, please vary on the volume group.'.format(vg)
        return 1

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
    if params['exclude_files']:
        cmd += ['-e']
    if params['location']:
        cmd += ['-f', params['location']]
    if params['create_data_file'] == 'mapfile':
        cmd += ['-m']
    elif params['create_data_file']:
        cmd += ['-i']
    if params['exclude_data']:
        cmd += ['-r']
    if params['verbose']:
        cmd += ['-v']
    if params['exclude_fs']:
        cmd += ['-x', params['exclude_fs']]
    if params['extend_fs']:
        cmd += ['-X']
    if params['flags']:
        for f in params['flags']:
            cmd += [f]
    cmd += [vg]

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
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
    module.log('VG backup {0} on {1} with restvg.'.format(action, disk))

    # restvg [DiskName]
    # [ -d FileName ]   Uses a file (absolute or relative path) instead of the vgname.data file in the backup image.
    # [ -f Device ]     Device of file to store the image. Default is I(/dev/rmt0).
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


def restvg_view(module, params):
    """
    Run the restvg command to get backup information.

    arguments:
        module     (dict): the module variable
        params  (dict): the command parameters
    return:
        rc       (int): the return code of the command
    """
    global results

    location = params['location'].strip()
    if not location:
        location = '/dev/rmt0'
    module.log('View VG backup {0} with restvg.'.format(location))

    # restvg -f Device -l
    # [ -f Device ]     Device of file to store the image. Default is I(/dev/rmt0).
    # [ -l ]            Displays useful information about a volume group backup. Used when action is 'view'.
    cmd = ['restvg', '-f', location, '-l']

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    return rc


def main():
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, type='str',
                        choices=['create', 'restore', 'view']),
            os_backup=dict(type='bool', default=False),
            name=dict(type='str'),
            flags=dict(type='str'),
            # for savevg and restvg
            location=dict(type='path'),
            exclude_data=dict(type='bool', default=False),
            verbose=dict(type='bool', default=False),
            # for savevg
            create_data_file=dict(type='str', choices=[True, 'mapfile', False], default=False),
            exclude_fs=dict(type='path'),
            force=dict(type='bool', default=False),
            exclude_files=dict(type='bool', default=False),
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
    params['os_backup'] = module.params['os_backup']
    params['flags'] = module.params['flags']

    if action == 'create':
        if params['os_backup']:

            rc = mksysb(module, params)

        else:
            params['name'] = module.params['name']
            params['location'] = module.params['location']
            params['exclude_data'] = module.params['exclude_data']
            params['verbose'] = module.params['verbose']
            params['create_data_file'] = module.params['create_data_file']
            params['exclude_fs'] = module.params['exclude_fs']
            params['force'] = module.params['force']
            params['exclude_files'] = module.params['exclude_files']
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
        if params['os_backup']:
            results['msg'] = 'Bad parameter: action is {0}, os_backup cannot be \'{1}\'.'.format(action, params['os_backup'])
            module.fail_json(**results)

        params['location'] = module.params['location']
        if not params['location'] or not params['location'].strip():
            results['msg'] = 'Missing parameter: action is {0} but argument \'location\' is missing.'.format(action)
            module.fail_json(**results)

        rc = restvg_view(module, params)

    if rc == 0:
        if not results['msg']:
            msg = 'AIX backup {0} operation successfull.'.format(action)
            results['msg'] = msg
        module.log(results['msg'])
        module.exit_json(**results)
    else:
        if not results['msg']:
            results['msg'] = 'AIX backup {0} operation failed.'.format(action)
        module.log(results['msg'])
        module.fail_json(**results)


if __name__ == '__main__':
    main()
