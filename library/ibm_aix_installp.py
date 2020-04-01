#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'IBM, Inc'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team
module: ibm_aix_installp
short_description: Installs and updates software
description:
- Installs available software products in a compatible installation package.
version_added: '2.9'
requirements: [ AIX ]
options:
  device:
    description:
    - The name of the device or directory containing installation images.
    type: str
  install_list:
    description:
    - List of products to install
    - C(all) installs all products
    type: list
    default: all
  force:
    description:
    - Forces the installation of a software product even if there exists a previously
      installed version of the software product that is the same as or newer than the
      version currently being installed.
    type: bool
    default: no
  bosboot:
    description:
    - Performs a bosboot in the event that one is needed.
    type: bool
    default: yes
  delete_image:
    description:
    - Deletes the installation image file after the software product or update has
      been successfully installed.
    type: bool
    default: no
  save:
    description:
    - Saves existing files that are replaced when installing or updating.
    type: bool
    default: yes
  part:
    description:
    - Installs the specified part of the software product.
    - C(root)
    - C(share)
    - C(usr)
    type: list
    default: [ root, share, usr ]
  expand_fs:
    description:
    - Attempts to expand any file systems where there is insufficient space to do the installation.
    type: bool
    default: yes
  commit:
    description:
    - Commit after apply.
    type: bool
    default: no
  dependencies:
    description:
    - Automatically installs any software products or updates that are requisites
      of the specified software product.
    - Automatically removes or rejects dependents of the specified software.
    type: bool
    default: no
  base_only:
    description:
    - Limits the requested action to base level filesets.
    type: bool
    default: no
  updates_only:
    description:
    - Indicates that the requested action should be limited to software updates.
    type: bool
    default: no
  platform:
    description:
    - Specifies the platform.
    - C(POWER) specifies POWER processor-based platform packages only.
    - C(neutral) specifies neutral packages, that is, packages that are not restricted
      to the POWER processor-based platform.
    - C(all) specifies all packages.
    type: str
    default: all
  action:
    description:
    - Controls what is performed.
    - C(apply) to install with apply.
    - C(commit) to commit applied updates.
    - C(reject) to reject applied updates.
    - C(deinstall) to deinstall (remove) installed software.
    - C(cleanup) to clean up a failed installation.
    - C(list) to list all installable software on media.
    - C(list_fixes) to obtain a list of the Authorized Program Analysis Report (APAR) numbers and summaries.
    - C(list_applied) to list all software products and updates that have been applied but not committed.
    type: str
    choices: [ apply, commit, reject, uninstall, list ]
    default: apply
  agree_licenses:
    description:
    - Agrees to required software license agreements for software to be installed.
    type: bool
    default: no
'''

EXAMPLES = r'''
- name: List all software products and installable options contained on an installation cartridge tape
  ibm_aix_installp:
    action: list
    device: /dev/rmt0.1

- name: List all customer-reported problems fixed by all software products on an installation tape
  ibm_aix_installp:
    action: list_fixes
    device: /dev/rmt0.1
    install_list: all

- name: Install all filesets within the bos.net software package and expand file systems if necessary
  ibm_aix_installp:
    expand_fs: yes
    device: /usr/sys/inst.images
    install_list: bos.net

- name: Reinstall and commit the NFS software product option that is already installed on the system at the same level
  ibm_aix_installp:
    commit: yes
    force: yes
    device: /dev/rmt0.1
    install_list: bos.net.nfs.client:4.1.0.0

- name: Remove a fileset named bos.net.tcp.server
  ibm_aix_installp:
    action: deinstall
    install_list: bos.net.tcp.server
'''

RETURN = r''' # '''

from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            device=dict(type='str'),
            install_list=dict(type='list', default=None),
            force=dict(type='bool', default=False),
            bosboot=dict(type='bool', default=True),
            delete=dict(type='bool', default=False),
            save=dict(type='bool', default=True),
            parts=dict(type='list', default=[]),
            expand_fs=dict(type='bool', default=True),
            commit=dict(type='bool', default=False),
            dependencies=dict(type='bool', default=False),
            base_only=dict(type='bool', default=False),
            updates_only=dict(type='bool', default=False),
            platform=dict(type='str', default='all', choices=['POWER', 'neutral', 'all']),
            action=dict(type='str', default='apply', choices=['apply', 'commit', 'reject', 'deinstall', 'cleanup', 'list', 'list_fixes', 'list_applied']),
            agree_licenses=dict(type='bool', default=False),
        ),
        required_if=[
            ['action', 'apply', ['device', 'install_list']],
            ['action', 'commit', ['install_list']],
            ['action', 'reject', ['install_list']],
            ['action', 'deinstall', ['install_list']],
            ['action', 'list', ['device']],
            ['action', 'list_fixes', ['device', 'install_list']],
        ]
    )

    result = dict(
        changed=False,
        msg='',
    )

    action = module.params['action']
    device = module.params['device']
    install_list = module.params['install_list']

    cmd = ['installp']

    if module.check_mode:
        cmd += ['-p']

    if not module.params['bosboot']:
        cmd += ['-b']
    if module.params['expand_fs']:
        cmd += ['-X']
    if module.params['updates_only']:
        cmd += ['-B']
    if module.params['base_only']:
        cmd += ['-I']
    if device and device != '':
        cmd += ['-d', device]
    if module.params['force']:
        cmd += ['-F']
    if module.params['dependencies']:
        cmd += ['-g']
    parts = module.params['parts']
    strparts = ''
    for part in parts:
        if part == 'root':
            strparts += 'r'
        elif part == 'share':
            strparts += 's'
        elif part == 'usr':
            strparts += 'u'
    if strparts != '':
        cmd += ['-O'+strparts]

    if action == 'apply':
        cmd += ['-a']
        if module.params['commit']:
            cmd += ['-c']
            if not module.params['save']:
                cmd += ['-N']
        if module.params['delete']:
            cmd += ['-D']
        if module.params['agree_licenses']:
            cmd += ['-Y']
    elif action == 'commit':
        cmd += ['-c']
    elif action == 'reject':
        cmd += ['-r']
    elif action == 'deinstall':
        cmd += ['-u']
    elif action == 'cleanup':
        cmd += ['-C']
    elif action == 'list':
        cmd += ['-l']
        platform = module.params['platform']
        if platform == 'all':
            cmd += ['-MA']
        elif platform.upper() == 'POWER':
            cmd += ['-MR']
        elif platform == 'neutral':
            cmd += ['-MN']
    elif action == 'list_fixes':
        cmd += ['-A']
    elif action == 'list_applied':
        cmd += ['-s']

    # Finally, append the install list
    if install_list:
        for fileset in install_list:
            cmd += fileset.split(':', 1)

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        result['msg'] = stderr
        module.fail_json(**result)

    result['msg'] = stdout
    module.exit_json(**result)

if __name__ == '__main__':
    main()
