#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: mount
short_description: Makes a file system available for use
description:
- This module makes a file system available for use at a specified location.
- Builds other file trees made up of directory and file mounts.
version_added: '2.9'
requirements: [ AIX ]
options:
  mount_all:
    description:
    - Mounts all file systems in the /etc/filesystems file with stanzas that contain the true mount attribute
    type: bool
    default: no
  alternate_fs:
    description:
    - Mounts on a file of an alternate file system, other than the /etc/file systems file
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
    - Mounts all stanzas in the /etc/filesystems file that contain the type=fs_type attribute
    type: str
  vfsname:
    description:
    - Specifies that the file system is defined by the vfsname parameter in the /etc/vfs file
    type: str
  options:
    description:
    - Specifies options. Options should be of the form <option-name>=<value> and multiple options should be separated only by a comma.
    type: str
  mount_dir:
    description:
    - Directory path to be mounted.
    type: str
  mount_over_dir:
    description:
    - Directory path on which the mount_dir should be mounted.
    type: str
'''

EXAMPLES = r'''
- name: Specify the filesystems to be mounted
  mount:
    mount_dir=/dev/hd1
    mount_over_dir=/home
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            mount_all=dict(type='bool'),
            alternate_fs=dict(type='str'),
            removable_fs=dict(type='str'),
            read_only=dict(type='str'),
            fs_type=dict(type='str'),
            vfsname=dict(type='str'),
            options=dict(type='str'),
            mount_dir=dict(type='str'),
            mount_over_dir=dict(type='str'),
        ),

        required_together=[["mount_dir", "mount_over_dir"]],
        mutually_exclusive=[
            ["mount_all", "fs_type", "mount_dir"]
        ]
    )

    result = dict(
        changed=False,
        msg='',
    )

    cmd = ['mount']
    alternate_fs = module.params['alternate_fs']
    if alternate_fs:
        cmd += ['-F', alternate_fs]
    if module.params['removable_fs']:
        cmd += ['-p']
    if module.params['read_only']:
        cmd += ['-r']
    vfsname = module.params['vfsname']
    if vfsname:
        cmd += ['-v', vfsname]
    options = module.params['options']
    if options:
        cmd += ['-o', options]
    fs_type = module.params['fs_type']
    if module.params['fs_type']:
        cmd += ['-t', fs_type]
    elif module.params['mount_all']:
        cmd += ['all']
    elif module.params['mount_dir']:
        mount_dir = module.params['mount_dir']
        mount_over_dir = module.params['mount_over_dir']
        cmd += [mount_dir, mount_over_dir]

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        result['msg'] = stderr
        module.fail_json(**result)

    result['changed'] = True
    result['msg'] = stdout + stderr
    module.exit_json(**result)


if __name__ == '__main__':
    main()
