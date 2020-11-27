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
short_description: Data or system volume group backup management.
description:
- This module manages backup image of data or system volume group on a logical partition (LPAR).
- It uses mksysb or savevg commands to create backup image of a volume group either in a file or
  onto a device.
- It uses restvg or alt_disk_mksysb to restore a backup image to disk(s).
- mksysb and alt_disk_mksysb operate on system volume group creating and restoring installable
  backup image while savevg and restvg operate on data volume group.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorization: B(aix.system.install)'
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
  type:
    description:
    - Specifies the type of backup object to operate.
    - C(mksysb) operates on backup of the operating system (that is, the root volume group) of a
      LPAR target.
    - C(savevg) operates on LPAR savevg, that is all files belonging to a volume group.
    - Discarded for I(action=view) as this action only applies to savevg.
    type: str
    choices: [ mksysb, savevg ]
    default: savevg
  name:
    description:
    - Specifies the targets of the operation.
    - Discarded if I(type=mksysb).
    - Required if I(action=create) and I(type=savevg), then it specifies the volume group to back
      up.
    - If I(action=restore) and I(type=savevg), it specifies the disk device to restore to and do
      not use the one in the vgname.data file.
    type: str
  flags:
    description:
    - Specifies additional flag to pass to the command. Refers to IBM documentation for details.
    - For I(action=create) and I(type=mksysb), you could use
      C(-a -A -b number -F filename -G|-N -M -P -t path -T -V -Z).
    - For I(action=restore) and I(type=mksysb), you could use
      C(-p platform -L mksysb_level -c console -K -O -g -k -r -z -T -S -C).
    - For I(action=create) and I(type=savevg), you could use C(-a -A -b Blocks -p -T -V -Z).
    - For I(action=restore) and I(type=savevg), you could use C(-b Blocks -n -P PPsize).
    type: str
  location:
    description:
    - Specifies the location of the backup files. It can be a device or file path.
    - When I(type=savevg) or I(action=view), the default device is C(/dev/rmt0).
    - Required if I(action=view) or I(type=mksysb).
    type: path
  disk:
    description:
    - Specifies the name or names of the target disk(s) where the alternate rootvg is created.
    - This disk or these disks must not currently contain any volume group definition.
    - Required if I(action=restore) and I(type=mksysb).
    type: list
    elements: str
  script:
    description:
    - Specifies the full path of a customization script file to run at the end of the mksysb
      installation.
    - Can be used if I(action=restore) or I(type=mksysb).
    type: path
  resolv_conf:
    description:
    - Specifies the full path of a alternate resolv.conf file to replace the existing one after the
      mksysb installation.
    - Can be used if I(action=restore) or I(type=mksysb).
    type: path
  phase:
    description:
    - Specifies the phase(s) to execute during the invocation of the alt_disk_mksysb command.
    - Can be used if I(action=restore) or I(type=mksysb).
    type: str
    choices: [ 1, 2, 3, 12, 23, all ]
  data_file:
    description:
    - Specifies a full path filename to use instead of the one from the image being restored.
    - If I(type=mksysb) it specifies the image.data file.
    - If I(type=savevg) it specifies the vgname.data file.
    - Can be used if I(action=restore).
    type: path
  create_data_file:
    description:
    - Specifies to create the data file containing information on the vloume group, logical volumes,
      file systems and their sizes.
    - If I(volume_group=rootvg), then data file will be in C(/image.data).
    - If C(volume_group) is a data volume group, data file will be in
      C(/tmp/vgdata/vgname/vgname.data).
    - Specify I(create_data_file=mapfile) to create the MAPFILE containing the mapping of the
      logical to physical partitions for each logical volume in the volume group. This mapping can
      be used to allocate the same logical-to-physical mapping when the image is restored.
    - Can be used if I(action=create).
    type: str
    choices: [ 'yes', 'mapfile', 'no' ]
    default: 'no'
  exclude_fs:
    description:
    - Specifies a file path that contains the list of file systems to exclude from the backup.
    - One file system mount point is listed per line.
    - Can be used if I(action=create).
    type: path
  remain_nim_client:
    description:
    - Specifies to remains NIM client after the mksysb installation.
    - The /.rhosts and /etc/niminfo files are copied to the alternate rootvg's file system.
    - Can be used if I(action=restore) or I(type=mksysb).
    type: bool
    default: no
  import_vg:
    description:
    - Specifies to look for and import volume groupe found in mksysb backup image.
    - Can be used if I(action=restore) or I(type=mksysb).
    type: bool
    default: no
  debug:
    description:
    - Specifies the debug mode (that is the set -x output).
    - Can be used if I(action=restore) or I(type=mksysb).
    type: bool
    default: no
  bootlist:
    description:
    - Specifies to run the bootlist command after the mksysb installation.
    - Cannot be used if I(flags) contains the C(-r) flag.
    - Can be used if I(action=restore) or I(type=mksysb).
    type: bool
    default: yes
  force:
    description:
    - Specifies to overwrite existing backup image.
    - Can be used if I(action=create) and I(type=savevg).
    type: bool
    default: no
  exclude_data:
    description:
    - If I(action=create), specifies to exclude user data from the backup. Backs up user volume
      group information and administration data files. This backs up files such as
      /tmp/vgdata/vgname/vgname.data and map files if any exist. Cannot be used on a rootvg.
    - If I(action=restore), specifies to recreate the volume group structure only without restoring
      any files or data.
    - Can be used if I(type=savevg).
    type: bool
    default: no
  exclude_packing_files:
    description:
    - Specifies to exclude files specified in the /etc/exclude_packing.rootvg,
      /etc/exclude_packing.vgname, or /etc/exclude_packing.WPARname file from being packed.
    - Can be used if I(action=create) and I(type=mksysb).
    type: bool
    default: no
  exclude_files:
    description:
    - Specifies to exclude files specified in the /etc/exclude.vgname file from being backed up.
    - The /etc/exclude.vgname file should contain patterns of file names that you do not want
      included in your system backup image. They are input to the pattern matching conventions of
      the grep command.
    - Can be used if I(action=create).
    type: bool
    default: no
  extend_fs:
    description:
    - Specifies to extend the filesystem if needed.
    - Can be used if I(action=create).
    type: bool
    default: no
  minimize_lv_size:
    description:
    - Specifies to create the logical volumes with minimum size possible to accomodate
      the file system.
    - Can be used if I(action=restore) and I(type=savevg).
    type: bool
    default: no
  verbose:
    description:
    - Specifies to run the operation in verbose mode.
    - Can be used if I(action=create) or I(action=restore).
    type: bool
    default: no
notes:
  - C(restore) C(mksysb) operation can be long, one can use the default log file
    /var/adm/ras/alt_disk_inst.log to track progress.
  - C(savevg) only backs up varied-on volume group. The file systems must be mounted.
  - C(savevg) backs up all logical volume information and will be recreated. However, only
    JFS-mounted file system data will be backed up. Raw logical volume data will NOT be backed up
    using a savevg.
  - C(savevg) only backs up varied-on volume group. The file systems must be mounted.
  - This M(backup) module only operates on LPAR, for operation on VIOS, please checkout the
    M(backupios) module in the power-vios collection.
  - You can refer to the IBM documentation for additional information on the commands used at
    U(U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/a_commands/alt_disk_mksysb.html),
    U(U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/l_commands/lsmksysb.html),
    U(U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mksysb.html),
    U(U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/restvg.html),
    U(U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/s_commands/savevg.html).
'''

EXAMPLES = r'''
- name: backup the rootvg with mksysb
  backup:
    action: create
    type: mksysb
    location: /tmp/backup_rootvg
    exclude_files: false
    extend_fs: yes

- name: install the mksysb image to /dev/hdisk1 using the 64 bits kernel if possible
  backup:
    action: restore
    type: mksysb
    location: /ESSAI/backup_datavg
    disk: /dev/hdisk1
    flags: '-K'

- name: savevg of rootvg to /dev/hdisk1
  backup:
    action: create
    type: savevg
    name: rootvg
    location: /dav/rmt1
    exclude_data: no
    exclude_files: no
    exclude_fs: /tmp/exclude_fs_list
    create_data_file: yes
    extend_fs: yes
    verbose: yes

- name: savevg of datavg structure to /dev/hdisk2
  backup:
    action: create
    type: savevg
    name: datavg
    location: /tmp/backup_datavg
    exclude_data: yes
    exclude_files: yes
    create_data_file: yes

- name: view the vg backup image stored on /dev/hdisk1 with savevg
  backup:
    action: view
    type: savevg
    location: /dev/hdisk1

- name: restvg to restore datavg structure only to /dev/hdisk2
  backup:
    action: restore
    type: savevg
    name: datavg
    location: /tmp/backup_datavg
    data_file: /tmp/datavg.mydata
    exclude_data: yes
    minimize_lv_size: yes
    flags: '-n'
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'AIX create backup operation successfull.'

cmd:
    description: The command executed.
    returned: when the command is run.
    type: str
    sample: '/bin/restvg -f /dev/rmt0 -l'

stdout:
    description: The standard output of the command.
    returned: always
    type: str
    sample:
      'hdisk1
       lv00
       x           11 ./tmp/vgdata/datavg/image.info
       x          127 ./tmp/vgdata/vgdata.files11928014
       x          127 ./tmp/vgdata/vgdata.files
       x         2320 ./tmp/vgdata/datavg/filesystems
       x         1530 ./tmp/vgdata/datavg/datavg.data
       x          278 ./tmp/vgdata/datavg/backup.data
           total size: 4393'
stderr:
    description: The standard error of the command.
    returned: always
    type: str
    sample:
      'Will create the Volume Group:	datavg
       Target Disks:	  Allocation Policy:
                Shrink Filesystems:	yes
                Preserve Physical Partitions for each Logical Volume:	no

       New volume on /tmp/datavg_backup:
        Cluster 51200 bytes (100 blocks).
           Volume number 1
           Date of backup: Thu Aug  6 03:53:53 2020
           Files backed up by name
           User root
           files restored: 6'
rc:
    description:
    - The return code of the command.
    - Equal I(-1) when the command has not been run.
    returned: always
    type: int
    sample: 0
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
    if rc != 0:
        results['msg'] = 'Cannot get active volume group. Command \'{0}\' failed.'.format(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['rc'] = rc
        return False

    vgs = stdout.splitlines()
    module.log('Active volume groups are: {0}'.format(vgs))
    if vg in vgs:
        module.debug('volume group {0} is active'.format(vg))
        return True
    else:
        results['msg'] = 'Volume group {0} is not active. Active volume groups are: {1}. Please vary on the volume group.'.format(vg, vgs)
        return False


def mksysb(module, params):
    """
    Perform a mksysb of the OS.

    arguments:
        module  (dict): The Ansible module
        params  (dict): the command parameters
    return:
        rc       (int): the return code of the command
    """
    global results
    module.log('Creating OS backup with mksysb.')

    # mksysb  device | file
    # [ -e ]          Excludes files specified in the /etc/exclude.vgname file from being backed up.
    # [ -i | -m ]     Create the image.data file calling mkszfile to get VG, LV, PV, PS info (-m for map file).
    # [ -P ]          Excludes files that are listed line by line in predifined files from being packed.
    # [ -v ]          Verbose mode.
    # [-x file]       Exclude fs listed in the file (one per line).
    # [ -X ]          Extend fs if needed.
    # not yet implemented:
    # [ -a ]          Does not back up extended attributes or NFSv4 ACLs.
    # [ -A ]          Backs up DMAPI file system files.
    # [ -b number ]   Specifies the number of 512-byte blocks to write in a single output operation.
    # [ -F filename ] Specifies a previously created mksysb from which a backup tape is created to try to make the tape bootable.
    # [ -G | -N ]     Excludes|Includes WPAR file systems from|to the system backup.
    # [-M]            Creates a backup file that is intended for use with the multibos command.
    # [ -p ]          Disable software packing (tape drives).
    # [ -t path ]     Directory or file system to create a boot image from the mksysb file specified by the -F flag.
    # [ -T ]          Create backup using snapshots.
    # [ -V ]          Verify a tape backup.
    # [ -Z ]          Does not back up the EFS information for all the files, directories, and file systems.

    cmd = ['/bin/mksysb']
    if params['create_data_file'].lower() == 'mapfile':
        cmd += ['-m']
    elif params['create_data_file'].lower() == 'yes':
        cmd += ['-i']
    if params['exclude_packing_files']:
        cmd += ['-P']
    if params['exclude_files']:
        cmd += ['-e']
    if params['verbose']:
        cmd += ['-v']
    if params['exclude_fs']:
        cmd += ['-x', params['exclude_fs']]
    if params['extend_fs']:
        cmd += ['-X']
    if params['flags']:
        for f in params['flags'].split(' '):
            cmd += [f]
    cmd += [params['location']]

    module.log('running command: {0}'.format(cmd))
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = ' '.join(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    if rc == 0:
        results['changed'] = True
    return rc


def alt_disk_mksysb(module, params):
    """
    Installs an alternate disk with a mksysb install base install image.

    arguments:
        module  (dict): The Ansible module
        params  (dict): the command parameters
    return:
        rc       (int): the return code of the command
    """
    global results
    module.log('Restoring OS backup with alt_disk_mksysb.')

    # alt_disk_mksysb -m device -d target_disks...
    # [ -m device ]       Location of the mksysb. It can be a tape device (/dev/rmt0) or a path in the filesystem.
    # [ -d target_disks ] Space delimited list of disk where the alternate rootvg is created.
    # [ -s script ]       Customization script to run at the end of the mksysb install.
    # [ -R resolv_conf ]  Full path of resolv.conf file that replace the existing one after after the mksysb has been restored.
    # [ -i image.data ]   Full path of image.data to use instead of the default file from mksysb image.
    # [ -P phase_option ] Phase(s) to execute during this invocation of the alt_disk_mksysb command. Can be 1,2,3,12,23,all.
    # [ -n ]    Remains NIM client.
    # [ -B ]    Does not run bootlist after the operation. Invalid with -r.
    # [ -y ]    Looks for and import (if found) mksysb volume group.
    # [ -V ]    Verbose output showing files restored.
    # [ -D ]    Truns on debug (set -x output).
    # not yet implemented:
    # [ -p platform ]     Platform used to create the name of the disk boot image.
    # [ -L mksysb_level ] Level is combined with the platform type to create the boot image name.
    # [ -c console ]      Device name to be used as the alternate rootvg's system console. Valid with -O.
    # [ -K ]    Uses the 64 bits kernel if possible.
    # [ -O ]    Performs a device reset on the target alinst_rootvg.
    # [ -g ]    Overlooks the bootable checks for the target_disks
    # [ -k ]    Keeps mksysb devices.
    # [ -r ]    Reboots from the new disk when alt_disk_mksysb is complete.
    # [ -z ]    Does not import any type of non-rootvg. Overrides -y.
    # [ -T ]    Converts JSF file systems to JFS2 while recreating the rootvg on target disks.
    # [ -S ]    Skips space-checking on target disks before clone or install operation.
    # [ -C ]    Uses the /usr/lpp/bos.alt_disk_install/boot_images/bosboot.disk.chrp file from the current rootvg only.
    cmd = ['/usr/sbin/alt_disk_mksysb']
    cmd += ['-m', params['location']]
    if len(params['disk']) == 1:
        cmd += ['-d', params['disk'][0]]
    else:
        cmd += ['-d', '"{0}"'.format(' '.join(params['disk']))]
    if params['script']:
        cmd += ['-s', params['script']]
    if params['resolv_conf']:
        cmd += ['-R', params['resolv_conf']]
    if params['data_file']:
        cmd += ['-i', params['data_file']]
    if params['data_file']:
        cmd += ['-P', params['data_file']]
    if params['remain_nim_client']:
        cmd += ['-n']
    if params['import_vg']:
        cmd += ['-y']
    if params['bootlist']:
        cmd += ['-B']
    if params['verbose']:
        cmd += ['-V']
    if params['debug']:
        cmd += ['-D']
    if params['flags']:
        for f in params['flags'].split(' '):
            cmd += [f]

    module.log('running command: {0}'.format(cmd))
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = ' '.join(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    if rc == 0:
        results['changed'] = True
    return rc


def lsmksysb(module, params):
    """
    Installs an alternate disk with a mksysb install base install image.

    arguments:
        module  (dict): The Ansible module
        params  (dict): the command parameters
    return:
        rc       (int): the return code of the command
    """
    global results
    module.log('Viewing OS backup information with lsmksysb.')

    # lsmksysb [ -f device ][ -l ]
    # not yet implemented:
    # [ -a ] [ -b blocks ] [ -c ] [ -n ] [ -r ] [ -s ] [ -d path ] [ -B ] [ -D ] [ -L ] [ -V ] [ file_list ]
    cmd = ['/bin/lsmksysb', '-l']
    if params['location'].strip():
        cmd += ['-f', params['location']]

    module.log('running command: {0}'.format(cmd))
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = ' '.join(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    return rc


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
    if params['create_data_file'].lower() == 'mapfile':
        cmd += ['-m']
    elif params['create_data_file'].lower() == 'yes':
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
        for f in params['flags'].split(' '):
            cmd += [f]
    cmd += [vg]

    module.log('running command: {0}'.format(cmd))
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = ' '.join(cmd)
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
    # [ -f Device ]     Device name of the backup media. Default is I(/dev/rmt0).
    # [ -q ]            Does not display the VG name and target disk device name usual prompt before restoration.
    # [ -r ]            Recreates a VG structure only without restoring any files or data.
    # [ -s ]            Creates the LV with minimum size possible to accomodate the file system.
    # not yet implemented:
    # [ -b Blocks ]     Specifies the number of 512-byte blocks to write in a single output operation
    # [ -n ]            Ignores the existing MAP files.
    # [ -P PPsize ]     Specifies the number of megabytes in each physical partition.
    cmd = ['/bin/restvg']
    if params['data_file']:
        cmd += ['-d', params['data_file']]
    if params['location']:
        cmd += ['-f', params['location']]
    if not params['verbose']:
        cmd += ['-q']
    if params['exclude_data']:
        cmd += ['-r']
    if params['minimize_lv_size']:
        cmd += ['-s']
    if params['flags']:
        for f in params['flags'].split(' '):
            cmd += [f]
    if disk:
        cmd += [disk]

    module.log('running command: {0}'.format(cmd))
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = ' '.join(cmd)
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
        module  (dict): the module variable
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
    cmd = ['/bin/restvg', '-f', location, '-l']

    module.log('running command: {0}'.format(cmd))
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = ' '.join(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    results['rc'] = rc
    return rc


def main():
    global results

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            action=dict(required=True, type='str',
                        choices=['create', 'restore', 'view']),
            type=dict(type='str', choices=['mksysb', 'savevg'], default='savevg'),
            name=dict(type='str'),
            flags=dict(type='str'),
            verbose=dict(type='bool', default=False),
            # for alt_disk_mksysb and savevg, restvg
            location=dict(type='path'),
            # for alt_disk_mksysb and restvg
            data_file=dict(type='path'),
            # for mksysb and savevg
            exclude_files=dict(type='bool', default=False),
            exclude_fs=dict(type='path'),
            extend_fs=dict(type='bool', default=False),
            # for savevg and restvg
            exclude_data=dict(type='bool', default=False),
            # for mksysb
            exclude_packing_files=dict(type='bool', default=False),
            # for alt_disk_mksysb
            disk=dict(type='list', elements='str'),
            script=dict(type='path'),
            resolv_conf=dict(type='path'),
            phase=dict(type='str', choices=['1', '2', '3', '12', '23', 'all']),
            remain_nim_client=dict(type='bool', default=False),
            import_vg=dict(type='bool', default=False),
            debug=dict(type='bool', default=False),
            bootlist=dict(type='bool', default=True),
            # for savevg
            create_data_file=dict(type='str', choices=['yes', 'mapfile', 'no'], default='no'),
            force=dict(type='bool', default=False),
            minimize_lv_size=dict(type='bool', default=False),
        ),
        required_if=[
            ['action', 'view', ['location']],
            ['type', 'mksysb', ['location']],
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
    params['objtype'] = module.params['type']
    params['flags'] = module.params['flags']
    params['location'] = module.params['location']

    if action == 'create':
        params['verbose'] = module.params['verbose']
        params['create_data_file'] = module.params['create_data_file']
        params['exclude_fs'] = module.params['exclude_fs']
        params['exclude_files'] = module.params['exclude_files']
        params['extend_fs'] = module.params['extend_fs']

        if params['objtype'] == 'mksysb':
            params['exclude_packing_files'] = module.params['exclude_packing_files']

            rc = mksysb(module, params)

        elif params['objtype'] == 'savevg':
            params['name'] = module.params['name']
            params['exclude_data'] = module.params['exclude_data']
            params['force'] = module.params['force']

            if not params['name']:
                results['msg'] = 'Missing parameter: action is {0} but argument \'name\' is missing.'.format(action)
                module.fail_json(**results)
            if params['exclude_data'] and params['name'] == 'rootvg':
                results['msg'] = 'Bad parameter: exclude_data is {0}, name cannot be \'rootvg\'.'.format(params['exclude_data'])
                module.fail_json(**results)

            rc = savevg(module, params, params['name'])

    elif action == 'restore':
        params['data_file'] = module.params['data_file']
        params['verbose'] = module.params['verbose']

        if params['objtype'] == 'mksysb':
            params['disk'] = module.params['disk']
            params['script'] = module.params['script']
            params['resolv_conf'] = module.params['resolv_conf']
            params['phase'] = module.params['phase']
            params['remain_nim_client'] = module.params['remain_nim_client']
            params['import_vg'] = module.params['import_vg']
            params['debug'] = module.params['debug']
            params['bootlist'] = module.params['bootlist']

            if not params['disk']:
                results['msg'] = 'Missing parameter: action is {0} but argument \'disk\' is missing.'.format(action)
                module.fail_json(**results)

            rc = alt_disk_mksysb(module, params)

        elif params['objtype'] == 'savevg':
            params['name'] = module.params['name']
            params['exclude_data'] = module.params['exclude_data']
            params['minimize_lv_size'] = module.params['minimize_lv_size']

            rc = restvg(module, params, action, params['name'])

    elif action == 'view':
        params['location'] = module.params['location']
        if params['objtype'] == 'mksysb':
            rc = restvg_view(module, params)
        elif params['objtype'] == 'savevg':
            rc = lsmksysb(module, params)

    if rc == 0:
        if not results['msg']:
            msg = 'AIX {0} backup operation successfull.'.format(action)
            results['msg'] = msg
        module.log(results['msg'])
        module.exit_json(**results)
    else:
        if not results['msg']:
            results['msg'] = 'AIX {0} backup operation failed.'.format(action)
        module.log(results['msg'])
        module.fail_json(**results)


if __name__ == '__main__':
    main()
