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
short_description: Mounts/Unmounts a Filesystem/Device
description:
- This module mounts/unmounts a Filesystem/Device on the specified path
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  state:
    description:
    - Specifies the module to perform mount/unmount operation
    type: str
    default: mount
    choices: [mount, umount]
  node:
    description:
    - Specifies the node holding the directory/filesystem/device you want to mount/unmount.
    type: str
  mount_all:
    description:
    - When I(state=mount) and I(mount_all=all), mounts all file systems in the
      /etc/filesystems file with stanzas that contain the true mount attribute
    - When I(state=umount) and I(mount_all=all), unmounts all mounted filesystem
    - When I(state=umount) and I(mount_all=remote), unmounts all remote mounted
      filesystems
    type: str
    choices: [all, remote, none]
    default: none
  force:
    description:
    - For remote mounted file systems, this attribute forces an unmount to free a
      client when the server is down and server path names cannot be resolved, or
      when a file system must be unmounted while it is still in use.
    type: bool
    default: false
  alternate_fs:
    description:
    - Mounts on a file of an alternate file system, other than the /etc/filesystems file
    type: str
  removable_fs:
    description:
    - Mounts a file system as a removable file system
    type: bool
    default: no
  read_only:
    description:
    - Mounts a file system as a read-only file system
    type: bool
    default: no
  fs_type:
    description:
    - Mounts/unmounts all stanzas in the /etc/filesystems file that contain the type=fs_type
      attribute
    type: str
  vfsname:
    description:
    - Specifies that the file system is defined by the vfsname parameter in the /etc/vfs file
    type: str
  options:
    description:
    - Specifies options. Options should be of the form <option-name>=<value> and multiple
      options should be separated only by a comma.
    type: str
  mount_dir:
    description:
    - Directory path to be mounted/unmounted
    type: str
  mount_over_dir:
    description:
    - Directory path on which the mount_dir should be mounted.
    type: str
'''

EXAMPLES = r'''
- name: Mount filesystems
  mount:
    mount_dir: /dev/hd1
    mount_over_dir: /home

- name: Mount filesystems provided by a node"
  mount:
    node: aixbase.aus.stglabs.ibm.com
    mount_dir: /mnt

- name: Unmount remote filesystems
  mount:
   state: umount
   mount_all: remote
   force: True
'''

RETURN = r'''
msg:
    description: The execution message.
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


def is_fspath_mounted(module, mount, mount_dir, mount_over_dir):
    """
    Determines if a given mount path is a FS and is already mounted
    param module: Ansible module argument spec.
    param mount: If the action being performed is a mount (True/False)
    param mount_dir: FS/Dir to be mounted.
    param mount_over_dir: path where to mount the mount_dir
    return: True - if FS and mounted / False - if FS and not mounted
            None - if not FS
    """

    cmd = "lsfs -l %s" % mount_dir
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        # Get the fs_name of the Filesystem
        # check if it is listed in the first column of df command
        ln = stdout.splitlines()[1]
        fs_name = ln.split()[0]
        cmd = "df"
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            module.fail_json("Command '%s' failed." % cmd)

        if stdout:
            fdirs = []
        for ln in stdout.splitlines()[1:]:
            fdirs.append(ln.split()[0])
        if fs_name in fdirs:
            if mount is False or fs_name == mount_dir or mount_over_dir is None:
                return True
        return False
    return None


def mount(module):
    """
    Mount the specified device/filesystem
    param module: Ansible module argument spec.
    return: changed - True/False(device/filesystem state modified or not),
            msg - message
    """
    cmd = "mount "
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
    elif module.params['mount_all'] == 'all':
        cmd += "all"
    elif module.params['mount_dir']:
        mount_dir = module.params['mount_dir']
        mount_over_dir = module.params['mount_over_dir']
        mounted = is_fspath_mounted(module, True, mount_dir, mount_over_dir)
        if mounted is True:
            msg = "Filesystem/Mount point '%s' already mounted" % mount_dir
            return False, msg
        if mount_over_dir is None:
            mount_over_dir = ""
        cmd += "%s %s" % (mount_dir, mount_over_dir)

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Mount failed. Command '%s' failed with return code '%s'." % (cmd, rc)
        module.fail_json(msg=msg, stdout=stdout, stderr=stderr)

    msg = "Mount Successful. Command '%s' successful." % cmd
    return True, msg


def umount(module):
    """
    Unmount the specified device/filesystem
    param module: Ansible module argument spec.
    return: changed - True/False(device/filesystem state modified or not),
            msg - message
    """
    mount_all = module.params['mount_all']
    fs_type = module.params['fs_type']
    mount_dir = module.params['mount_dir']
    node = module.params['node']
    force = module.params['force']

    if is_fspath_mounted(module, False, mount_dir, None) is False:
        msg = "Filesystem/Mount point '%s' already unmounted" % mount_dir
        return False, msg

    cmd = "umount "
    if force:
        cmd += "-f "
    if mount_all == 'remote':
        cmd += "allr "
    elif mount_all == 'all':
        cmd += "all "
    if node:
        cmd += "-n %s " % node
    if fs_type:
        cmd += "-t %s " % fs_type
    if mount_dir:
        cmd += mount_dir

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Unmount failed. Command '%s' failed with return code '%s'." % (cmd, rc)
        module.fail_json(msg=msg, stdout=stdout, stderr=stderr)

    msg = "Unmount Successful. Command '%s' successful." % cmd
    return True, msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            mount_all=dict(type='str', default='none', choices=['all', 'remote', 'none']),
            alternate_fs=dict(type='str'),
            removable_fs=dict(type='bool'),
            read_only=dict(type='bool'),
            fs_type=dict(type='str'),
            vfsname=dict(type='str'),
            options=dict(type='str'),
            mount_dir=dict(type='str'),
            mount_over_dir=dict(type='str'),
            state=dict(type='str', default='mount', choices=['mount', 'umount']),
            node=dict(type='str'),
            force=dict(type='bool', default=False),
        ),

        mutually_exclusive=[
            ["mount_all", "fs_type", "mount_dir"]
        ]
    )

    state = module.params['state']

    if state == 'mount':
        changed, msg = mount(module)
    else:
        changed, msg = umount(module)

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
