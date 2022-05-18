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
module: installp
short_description: Installs and updates software.
description:
- Installs available software products in a compatible installation package.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorization: B(aix.system.install)'
options:
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
    choices: [ apply, commit, reject, deinstall, cleanup, list, list_fixes, list_applied ]
    default: apply
  device:
    description:
    - Specifies the device or directory that contains the installation images.
    type: str
  install_list:
    description:
    - Lists the software products to install.
    - One can specify either an entire software product or any separately installable filesets
      within the software product. This can be used to specify the name of a fileset or fileset
      update.
    - A specific level of the software can be provided using the following format 'fileset:level'.
    - It indicates the level of the software product or update that is to be installed and is of
      the form vv.rr.mmmm.ffff. If a fileset update has an additional fix ID (also know as ptf id),
      that ID must also be specified in the level as in vv.rr.mmmm.ffff.ppppppp.
    - C(all) installs all software products available.
    type: list
    elements: str
  force:
    description:
    - Forces the installation of a software product even if there exists a previously installed
      version of the software product that is the same as or newer than the version currently being
      installed.
    type: bool
    default: no
  bosboot:
    description:
    - Performs a bosboot in the event that creating the boot image is needed.
    type: bool
    default: yes
  delete_image:
    description:
    - Deletes the installation image file after the software product or update has been successfully
      installed.
    type: bool
    default: no
  save:
    description:
    - Saves existing files that are replaced when installing or updating.
    - When I(save=no) and there is a failure in the system during the installation, then no recovery
      of replaced files is performed.
    type: bool
    default: yes
  parts:
    description:
    - Installs the specified part of the software product.
    - C(root)
    - C(share)
    - C(usr)
    - When not specified, all parts of software are installed by default.
    type: list
    elements: str
  extend_fs:
    description:
    - Attempts to resize any file systems where there is insufficient space to do the installation.
    type: bool
    default: yes
  commit:
    description:
    - Commits all specified updates that are currently applied but not committed.
    - When an update is committed all other software products it is dependent on must also be
      committed. If the requisite software products are not in the committed state, the commit fails
      and error messages are displayed.
    type: bool
    default: no
  dependencies:
    description:
    - Automatically installs any software products or updates that are requisites of the specified
      software product.
    - Automatically removes or rejects dependents of the specified software.
    - It causes the newest update to be installed for a given fileset, when there are multiple
      superseding updates for the same fileset on the installation media.
    type: bool
    default: no
  base_only:
    description:
    - Limits the requested action to base level filesets.
    - Base level filesets can be used to install software, reinstall existing fileset or downlevel
      existing filesets.
    - Some fileset do not have a base level version of the software, come preloaded on the system
      and cannot be force overwritten or reinstalled.
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
    - C(neutral) specifies neutral packages, that is, packages that are not restricted to the POWER
      processor-based platform.
    - C(all) specifies all packages.
    type: str
    choices: [ POWER, neutral, all ]
    default: all
  agree_licenses:
    description:
    - Agrees to required software license agreements for software to be installed.
    type: bool
    default: no
notes:
  - You can refer to the IBM documentation for additional information on the installp command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/i_commands/installp.html)
'''

EXAMPLES = r'''
- name: List all software products and installable options contained on an installation cartridge tape
  ibm.power_aix.installp:
    action: list
    device: /dev/rmt0.1

- name: List all customer-reported problems fixed by all software products on an installation tape
  ibm.power_aix.installp:
    action: list_fixes
    device: /dev/rmt0.1
    install_list: all

- name: Install all filesets within the bos.net software package and expand file systems if necessary
  ibm.power_aix.installp:
    extend_fs: yes
    device: /usr/sys/inst.images
    install_list: bos.net

- name: Reinstall and commit the NFS software product option that is already installed on the system at the same level
  ibm.power_aix.installp:
    commit: yes
    force: yes
    device: /dev/rmt0.1
    install_list: bos.net.nfs.client:4.1.0.0

- name: Remove a fileset named bos.net.tcp.server
  ibm.power_aix.installp:
    action: deinstall
    install_list: bos.net.tcp.server
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "installp 'apply' failed."
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: always
    type: int
stdout:
    description: The standard output.
    returned: always
    type: str
    sample: "
        *******************************************************************************\n
        installp PREVIEW:  deinstall operation will not actually occur.\n
        *******************************************************************************\n
        \n
        +-----------------------------------------------------------------------------+\n
                            Pre-deinstall Verification...\n
        +-----------------------------------------------------------------------------+\n
        Verifying selections...done\n
        Verifying requisites...done\n
        Results...\n
        \n
        WARNINGS\n
        --------\n
          Problems described in this section are not likely to be the source of any\n
          immediate or serious failures, but further actions may be necessary or\n
          desired.\n
        \n
          Not Installed\n
          -------------\n
          No software could be found on the system that could be deinstalled for the\n
          following requests:\n
        \n
            bos.sysmgt.nim.master                    \n
        \n
          (The fileset may not be currently installed, or you may have made a\n
           typographical error.)\n
        \n
          << End of Warning Section >>\n
        \n
        FILESET STATISTICS \n
        ------------------\n
            1  Selected to be deinstalled, of which:\n
                1  FAILED pre-deinstall verification\n
          ----\n
            0  Total to be deinstalled\n
        \n
        \n
        ******************************************************************************\n
        End of installp PREVIEW.  No deinstall operation has actually occurred.\n
        ******************************************************************************"
stderr:
    description: The standard error.
    returned: always
    type: str
    sample: "installp: Device /dev/rfd0 could not be accessed.\nSpecify a valid device name."
'''

from ansible.module_utils.basic import AnsibleModule
import re


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            device=dict(type='str'),
            install_list=dict(type='list', elements='str', default=None),
            force=dict(type='bool', default=False),
            bosboot=dict(type='bool', default=True),
            delete_image=dict(type='bool', default=False),
            save=dict(type='bool', default=True),
            parts=dict(type='list', elements='str', default=None),
            extend_fs=dict(type='bool', default=True),
            commit=dict(type='bool', default=False),
            dependencies=dict(type='bool', default=False),
            base_only=dict(type='bool', default=False),
            updates_only=dict(type='bool', default=False),
            platform=dict(type='str', default='all', choices=['POWER', 'neutral', 'all']),
            action=dict(type='str', default='apply', choices=['apply', 'commit', 'reject',
                                                              'deinstall', 'cleanup', 'list',
                                                              'list_fixes', 'list_applied']),
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
        stdout='',
        stderr='',
    )

    action = module.params['action']
    device = module.params['device']
    install_list = module.params['install_list']

    cmd = ['installp']

    if module.check_mode:
        cmd += ['-p']

    if not module.params['bosboot']:
        cmd += ['-b']
    if module.params['extend_fs']:
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
    if parts:
        for part in parts:
            if part == 'root':
                strparts += 'r'
            elif part == 'share':
                strparts += 's'
            elif part == 'usr':
                strparts += 'u'
    if strparts != '':
        cmd += ['-O' + strparts]

    if action == 'apply':
        cmd += ['-a']
        if module.params['commit']:
            cmd += ['-c']
            if not module.params['save']:
                cmd += ['-N']
        if module.params['delete_image']:
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

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if rc != 0:
        result['msg'] = 'installp \'{0}\' failed.'.format(action)
        module.fail_json(**result)

    result['msg'] = 'installp \'{0}\' successful.'.format(action)
    if action in ['apply', 'commit', 'reject', 'deinstall', 'cleanup']:
        result['changed'] = True

    # check if anything changed
    pattern = r"(Already Installed|Not Installed|Not Committable|Not Rejectable|0503-439)"
    if not re.search(r"SUCCESSES", stdout) and\
            not re.search(r"SUCCESS", stderr) and\
            (re.search(pattern, stdout) or re.search(pattern, stderr)):
        result['changed'] = False

    module.exit_json(**result)


if __name__ == '__main__':
    main()
