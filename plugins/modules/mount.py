#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
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
module: mount
short_description: Mounts/unmounts a filesystem or device on AIX.
description:
- This module mounts/unmounts a Filesystem/Device on the specified path.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorizations:
  B(aix.fs.manage.list,aix.fs.manage.create,aix.fs.manage.change,aix.fs.manage.remove,aix.fs.manage.mount,aix.fs.manage.unmount)'
options:
  state:
    description:
    - Specifies the action to be performed.
    - C(mount) makes a file system available for use at a specified location (the mount point). In
      addition, you can use it to build other file trees made up of directory and file mounts. If no
      parameter is specified, it gets information for the mounted file systems.
    - C(umount) unmounts a previously mounted device, directory, file, or file system
    - C(show) list mounted filesytems
    type: str
    default: mount
    choices: [mount, umount, show]
  mount_dir:
    description:
    - Specifies the directory path to mount/unmount.
    type: str
  mount_over_dir:
    description:
    - Directory path on which the mount_dir should be mounted.
    - If you specify only this directory, it looks up the associated device, directory, or file and
      mounts/unmounts it.
    type: str
  node:
    description:
    - Specifies the remote node holding the directory/filesystem/device to be mounted/unmounted.
    type: str
  mount_all:
    description:
    - When I(state=mount) and I(mount_all=all), mounts all file systems in the
      /etc/filesystems file with stanzas that contain the true mount attribute.
    - When I(state=umount) and I(mount_all=all), unmounts all mounted filesystem.
    - When I(state=umount) and I(mount_all=remote), unmounts all remote mounted
      filesystems.
    type: str
    choices: [all, remote]
  force:
    description:
    - For remote mounted file systems, this attribute forces an unmount to free a
      client when the server is down and server path names cannot be resolved, or
      when a file system must be unmounted while it is still in use.
    type: bool
    default: false
  alternate_fs:
    description:
    - Mounts on a file of an alternate file system, other than the /etc/filesystems file.
    type: str
  removable_fs:
    description:
    - Mounts a file system as a removable file system.
    type: bool
    default: no
  read_only:
    description:
    - Mounts a file system as a read-only file system.
    type: bool
    default: no
  fs_type:
    description:
    - It specifies the name of the group to mount. It mounts/unmounts stanzas in the
      B(/etc/filesystems) file that contain the type=C(fs_type) attribute.
    type: str
  vfsname:
    description:
    - Specifies that the file system is defined by the vfsname parameter in the /etc/vfs file.
    type: str
  options:
    description:
    - Specifies options. Options should be of the form <option-name>=<value> and multiple
      options should be separated only by a comma.
    type: str
notes:
  - This module runs commands that require privileged operations. For more information about
    authorizations and privileges, see Privileged Command Database in Security. For a list of
    privileges and the authorizations associated with this command, see the lssecattr command or the
    getcmdattr subcommand documentation.
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mount.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/u_commands/umount.html).
'''

EXAMPLES = r'''
- name: List mounted filesystems
  ibm.power_aix.mount:
    state: show

- name: Mount filesystems
  ibm.power_aix.mount:
    state: mount
    mount_dir: /mnt/tesfs

- name: Mount filesystems provided by a node
  ibm.power_aix.mount:
    state: mount
    node: ansible-test1
    mount_dir: /mnt/servnfs
    mount_over_dir: /mnt/clientnfs

- name: Mount all filesystems from the 'local' mount group
  ibm.power_aix.mount:
    state: mount
    fs_type: local

- name: Unmount filesystem
  ibm.power_aix.mount:
    state: umount
    mount_dir: /mnt/testfs

- name: Unmount all remote filesystems
  ibm.power_aix.mount:
    state: umount
    mount_all: remote
    force: True

- name: Unmount all remote fileystems from a node
  ibm.power_aix.mount:
    state: umount
    node: ansible-test1

- name: Unmount all filesytems from the 'local' mount group
  ibm.power_aix.mount:
    state: umount
    fs_type: local
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import re

result = None


def is_mount_group_mounted(module, mount_group):
    """
    Determines which FS are already mounted in a mount group
    arguments:
        module         (dict): Ansible module argument spec.
        mount_group    (str): Name of the mount group/type.
    return:
        returns a dictionary where the keys are the mount
        point of the FS and the values are boolean values.
        True if the mount point is mounted, else False.
    """

    # Fetch all FS in the mount_group
    cmd = "/usr/sbin/lsfs -u %s" % mount_group
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        result['msg'] = "Failed to fetch filesystem name in mount group '%s'" % mount_group
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        module.fail_json(**result)
    elif stdout == "":
        result['msg'] = "There are no filesytems in '%s' mount group." % mount_group
        module.fail_json(**result)

    # parse results - retain only the mount points
    mnt_grp_mounted = dict()
    lines = stdout.splitlines()[1:]
    for line in lines:
        mnt_pt = line.split()[2]
        mnt_grp_mounted[mnt_pt] = False

    # fetch all mounted FS
    cmd = "/usr/bin/df"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        result['msg'] = "Failed to get the filesystem name. Command '%s' failed." % cmd
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        module.fail_json(**result)

    # check if FS (in mount group) is mounted
    for mnt_pt in mnt_grp_mounted.keys():
        found = re.search(mnt_pt, stdout, re.MULTILINE)
        if found:
            mnt_grp_mounted[mnt_pt] = True

    return mnt_grp_mounted


def is_fspath_mounted(module, mount_dir, mount_over_dir):
    """
    Determines if a given mount path is a FS and is already mounted
    arguments:
        module         (dict): Ansible module argument spec.
        mount_dir       (str): FS/Dir to be mounted. Can be None.
        mount_over_dir  (str): path where to mount the mount_dir. Can be None.
    note:
        At least one of mount_dir or mount_over_dir must not be None.
        Exits with fail_json in case of error
    return:
        True - if FS and mounted
        False - if FS and not mounted
    """

    if mount_over_dir:
        # when mounting NFS, make sure we check for the NFS
        fs_name = mount_over_dir
    elif mount_dir:
        fs_name = mount_dir
    else:
        # should not happen
        result['msg'] = "Unexpected module FAILURE: one of the following is missing: "
        result['msg'] += ','.join(['mount_dir', 'mount_over_dir'])
        module.fail_json(**result)

    cmd = "/usr/bin/df"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        result['msg'] = "Failed to get the filesystem name. Command '%s' failed." % cmd
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        module.fail_json(**result)

    fdirs = []
    if stdout:
        for ln in stdout.splitlines()[1:]:
            fdirs.append(ln.split()[-1])
    for fdir in fdirs:
        found = re.search('^' + fs_name + '$', fdir)
        if found:
            return True

    return False


def fs_list(module):
    """
    List mounted filesystems
    arguments:
        module  (dict): Ansible module argument spec.
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    cmd = "/usr/sbin/mount"
    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = "Failed to list mounted filesystems."
        module.fail_json(**result)

    result['msg'] = "Mounted filesystems listed in stdout."
    return


def mount(module):
    """
    Mount the specified device/filesystem
    arguments:
        module  (dict): Ansible module argument spec.
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    cmd = "/usr/sbin/mount "
    alternate_fs = module.params['alternate_fs']
    if alternate_fs:
        cmd += "-F %s " % alternate_fs
    if module.params['removable_fs']:
        cmd += "-p "
    if module.params['read_only']:
        cmd += "-r "
    vfsname = module.params['vfsname']
    if vfsname:
        cmd += "-v %s " % vfsname
    options = module.params['options']
    if options:
        cmd += "-o %s " % options
    fs_type = module.params['fs_type']
    node = module.params['node']
    if node:
        cmd += "-n %s " % node
    if fs_type:
        cmd += "-t %s " % fs_type
        init_mnt_grp_mounted = is_mount_group_mounted(module, mount_group=fs_type)
    elif module.params['mount_all'] == 'all':
        cmd += "all"
    else:
        mount_dir = module.params['mount_dir']
        mount_over_dir = module.params['mount_over_dir']
        if is_fspath_mounted(module, mount_dir, mount_over_dir):
            # if both mount_dir and mount_over_dir is given then check for
            # mount_over_dir
            if mount_over_dir:
                result['msg'] = "Filesystem/Mount point '%s' already mounted" % mount_over_dir
            elif mount_dir:
                result['msg'] = "Filesystem/Mount point '%s' already mounted" % mount_dir
            return
        if mount_over_dir is None:
            mount_over_dir = ""
        if mount_dir is None:
            mount_dir = ""
        cmd += "%s %s" % (mount_dir, mount_over_dir)

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    # if attempting to mount a mount group. may need to mount multiple FS
    if fs_type:
        final_mnt_grp_mounted = is_mount_group_mounted(module, mount_group=fs_type)
        num_mounted = 0
        for mnt_pt, mounted in init_mnt_grp_mounted.items():
            if mounted:
                result['msg'] += "Filesystem/Mount point '%s' already mounted\n" % mnt_pt
                continue
            # check if it is now mounted
            if final_mnt_grp_mounted[mnt_pt]:
                result['msg'] += "Mount successful - '%s'\n" % mnt_pt
                num_mounted += 1
            else:
                result['msg'] += "Mount failed - '%s'\n" % mnt_pt
                module.fail_json(**result)
        if num_mounted != 0:
            result['changed'] = True
        result['rc'] = 0  # to not make ansible fail
        return

    # attempting only to mount one FS
    if rc != 0:
        result['msg'] = "Mount failed. Command '%s' failed with return code '%s'." % (cmd, rc)
        module.fail_json(**result)

    result['msg'] = "Mount successful."
    result['changed'] = True
    return


def umount(module):
    """
    Unmount the specified device/filesystem
    arguments:
        module  (dict): Ansible module argument spec.
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    mount_all = module.params['mount_all']
    fs_type = module.params['fs_type']
    mount_dir = module.params['mount_dir']
    mount_over_dir = module.params['mount_over_dir']
    node = module.params['node']
    force = module.params['force']

    cmd = "/usr/sbin/umount "
    if force:
        cmd += "-f "
    if mount_all == 'remote':
        cmd += "allr "
    elif mount_all == 'all':
        cmd += "all "
    elif fs_type:
        cmd += "-t %s " % fs_type
    elif node:
        cmd += "-n %s " % node
    elif mount_dir or mount_over_dir:
        if is_fspath_mounted(module, mount_dir, mount_over_dir) is False:
            # if both mount_dir and mount_over_dir is given then check for
            # mount_over_dir
            if mount_over_dir:
                result['msg'] = "Filesystem/Mount point '%s' is not mounted" % mount_over_dir
            elif mount_dir:
                result['msg'] = "Filesystem/Mount point '%s' is not mounted" % mount_dir
            return
        if mount_over_dir:
            cmd += mount_over_dir
        elif mount_dir:
            cmd += mount_dir

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if mount_all == 'remote' or node or fs_type:
        # cannot find anything to umount
        pattern = r"0506-347"
        found = re.search(pattern, stderr)
        if found:
            result['rc'] = 0
            result['msg'] = "There are no remote filesystems to unmount."
            return

    if rc != 0:
        result['msg'] = "Unmount failed. Command '%s' failed with return code '%s'." % (cmd, rc)
        module.fail_json(**result)

    result['msg'] = "Unmount successful."
    result['changed'] = True
    return


def main():
    global result

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            state=dict(type='str', default='mount', choices=['mount', 'umount', 'show']),
            mount_dir=dict(type='str'),
            mount_over_dir=dict(type='str'),
            node=dict(type='str'),
            mount_all=dict(type='str', choices=['all', 'remote']),
            force=dict(type='bool', default=False),
            alternate_fs=dict(type='str'),
            removable_fs=dict(type='bool', default=False),
            read_only=dict(type='bool', default=False),
            fs_type=dict(type='str'),
            vfsname=dict(type='str'),
            options=dict(type='str'),
        ),
        mutually_exclusive=[
            ["mount_all", "fs_type", "mount_dir"]
        ],
    )
    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    if module.params['state'] == 'show':
        fs_list(module)
    elif module.params['state'] == 'mount':
        mount(module)
    else:
        umount(module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
