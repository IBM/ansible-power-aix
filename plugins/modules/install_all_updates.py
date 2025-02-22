#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- Syahrul Aiman Shaharuddin (@syahrul-aiman)
module: install_all_updates
short_description: Updates installed software to the latest level on media and verifies the current recommended maintenance or technology level.
description:
- install_all_updates examines currently installed software and attempts to update it to the latest level that is available on the media.
  install_all_updates will not install any filesets that are present on the media, but not installed on the system except if the new
  filesets are installed as requisites of other filesets or the /var/adm/ras/bosinst.data filesets ALL_DEVICES_KERNELS to yes.
version_added: '1.8.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorization: B(aix.system.install)'
options:
  device:
    description:
    - Specifies the device or directory that contains the installation images.
    type: str
    required: true
  utilities_only:
    description:
    - Update install utilities only (bos.rte.install update).
    type: bool
    default: no
  commit:
    description:
    - Commits all newly installed updates.
    type: bool
    default: no
  update_rpm:
    description:
    - Update rpm images (if possible).
    type: bool
    default: no
  dependencies:
    description:
    - Automatically install requisites.
    type: bool
    default: yes
  skip_verify:
    description:
    - Skip recommended maintenance or technology level verification.
    type: bool
    default: no
  extend_fs:
    description:
    - Attempts to resize any file systems where there is insufficient space to do the installation.
    type: bool
    default: yes
  checksum:
    description:
    - Verify that all installed files in the fileset have the correct checksum value after the installation.
    - This operation may require more time to complete the installation.
    type: bool
    default: no
  suppress_multivolume:
    description:
    - Suppress multi-volume processing of cdrom media.
    type: bool
    default: no
  agree_licenses:
    description:
    - Agrees to all software license agreements which are required for software installation.
    type: bool
    default: no
  check_mode:
    description:
    - Performs a preview of an action by running all preinstallation checks for the specified action. No software changes are made.
    type: bool
    default: False
notes:
  - You can refer to the IBM documentation for additional information on the installp command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_73/i_commands/install_all_updates.html)
'''


EXAMPLES = r'''
- name: Install all installp updates on device /dev/cd0 and to verify the current recommended maintenance or technology level
  ibm.power_aix.install_all_updates:
    device: /dev/cd0

- name: Update any rpm images on your system, with newer technology levels from the /images directory
  ibm.power_aix.install_all_updates:
    device: /images
    update_rpm: true

- name: install the latest level of install utilities on device /dev/cd0 (bos.rte.install update)
  ibm.power_aix.install_all_updates:
    device: /dev/cd0
    utilities_only: true
'''


RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "install_all_updates 'apply' failed."
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
    sample:
      'install_all_updates: Initializing system parameters.\n
      install_all_updates: Log file is /var/adm/ras/install_all_updates.log\n
      install_all_updates: Checking for updated install utilities on media.\n
      install_all_updates: Updating install utilities to latest level on media.\n
      *******************************************************************************\n
      installp PREVIEW:  installation will not actually occur.\n
      *******************************************************************************\n
      \n
      +-----------------------------------------------------------------------------+\n
                          Pre-installation Verification...\n
      +-----------------------------------------------------------------------------+\n
      Verifying selections...done\n
      Verifying requisites...done\n
      Results...\n
      \n
      SUCCESSES\n
      ---------\n
        Filesets listed in this section passed pre-installation verification\n
        and will be installed.\n
      \n
        Mandatory Fileset Updates\n
        -------------------------\n
        (being installed automatically due to their importance)\n
        bos.rte.install 7.2.5.203                   \# LPP Install Commands\n
      \n
        << End of Success Section >>\n
      \n
      +-----------------------------------------------------------------------------+\n
                         BUILDDATE Verification ...\n
      +-----------------------------------------------------------------------------+\n
      Verifying build dates...done\n
      FILESET STATISTICS \n
      ------------------\n
          1  Selected to be installed, of which:\n
              1  Passed pre-installation verification\n
        ----\n
          1  Total to be installed\n
      \n
      RESOURCES\n
      ---------\n
        Estimated system resource requirements for filesets being installed:\n
                      (All sizes are in 512-byte blocks)\n
            Filesystem                     Needed Space             Free Space\n
            /                                      72                 419656\n
            /usr                                24024                5421432\n
            /tmp                                  560                8378576\n
            -----                            --------                 ------\n
            TOTAL:                              24656               14219664\n
      \n
        NOTE:  "Needed Space" values are calculated from data available prior\n
        to installation.  These are the estimated resources required for the\n
        entire operation.  Further resource checks will be made during\n
        installation to verify that these initial estimates are sufficient.\n
      \n
      ******************************************************************************\n
      End of installp PREVIEW.  No apply operation has actually occurred.\n
      ******************************************************************************\n
      install_all_updates: Processing media.\n
      install_all_updates: Generating list of updatable installp filesets.\n
      install_all_updates: The following filesets have been selected as updates\n
      to currently installed software:\n
      \n
         bos.64bit 7.2.5.201\n
         ...\n
         security.acf 7.2.5.201\n
      \n
         << End of Fileset List >>\n
      \n
      install_all_updates: Performing installp update.\n
      *******************************************************************************\n
      installp PREVIEW:  installation will not actually occur.\n
      *******************************************************************************\n
      \n
      +-----------------------------------------------------------------------------+\n
                          Pre-installation Verification...\n
      +-----------------------------------------------------------------------------+\n
      Verifying selections...done\n
      Verifying requisites...done\n
      Results...\n
      \n
      SUCCESSES\n
      ---------\n
        Filesets listed in this section passed pre-installation verification\n
        and will be installed.\n
      \n
        Mandatory Fileset Updates\n
        -------------------------\n
        (being installed automatically due to their importance)\n
        bos.rte.install 7.2.5.203                   \# LPP Install Commands\n
      \n
        << End of Success Section >>\n
      \n
      +-----------------------------------------------------------------------------+\n
                         BUILDDATE Verification ...\n
      +-----------------------------------------------------------------------------+\n
      Verifying build dates...done\n
      FILESET STATISTICS \n
      ------------------\n
         53  Selected to be installed, of which:\n
              1  Passed pre-installation verification\n
             52  Deferred (see *NOTE below)\n
        ----\n
          1  Total to be installed\n
      \n
      *NOTE  The deferred filesets mentioned above will be processed after the\n
             installp update and its requisites are successfully installed.\n
      \n
      RESOURCES\n
      ---------\n
        Estimated system resource requirements for filesets being installed:\n
                      (All sizes are in 512-byte blocks)\n
            Filesystem                     Needed Space             Free Space\n
            /                                      72                 419656\n
            /usr                                24024                5421432\n
            /tmp                                  560                8378208\n
            -----                            --------                 ------\n
            TOTAL:                              24656               14219296\n
      \n
        NOTE:  "Needed Space" values are calculated from data available prior\n
        to installation.  These are the estimated resources required for the\n
        entire operation.  Further resource checks will be made during\n
        installation to verify that these initial estimates are sufficient.\n
      \n
      ******************************************************************************\n
      End of installp PREVIEW.  No apply operation has actually occurred.\n
      ******************************************************************************\n
      \n
      install_all_updates: ATTENTION, a higher level of install utilities is\n
      available. The preview option will be more accurate and complete after\n
      updating to the latest level (see the -i option).\n
      \n
      install_all_updates: Log file is /var/adm/ras/install_all_updates.log\n
      install_all_updates: Result = SUCCESS'
stderr:
    description: The standard error.
    returned: always
    type: str
    sample:
      'install_all_updates: Initializing system parameters.\n
      install_all_updates: Log file is /var/adm/ras/install_all_updates.log\n
      install_all_updates: Checking for updated install utilities on media.\n
      install_all_updates: ATTENTION, no installp images were found on media.\n
      install_all_updates: Processing media.\n
      installp: Device /dev/rfd0 could not be accessed.\n
              Specify a valid device name.\n
      install_all_updates: Error reading media on /dev/rfd0\n
      \n
      install_all_updates: Log file is /var/adm/ras/install_all_updates.log\n
      install_all_updates: Result = FAILURE'
'''

from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


def main():
    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            device=dict(type='str', required=True),
            utilities_only=dict(type='bool', default=False),
            update_rpm=dict(type='bool', default=False),
            skip_verify=dict(type='bool', default=False),
            checksum=dict(type='bool', default=False),
            suppress_multivolume=dict(type='bool', default=False),
            extend_fs=dict(type='bool', default=True),
            commit=dict(type='bool', default=False),
            dependencies=dict(type='bool', default=True),
            agree_licenses=dict(type='bool', default=False),
            check_mode=dict(type='bool', default=False),
        ),
        required_if=[]
    )

    result = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    device = module.params['device']

    cmd = ['install_all_updates']
    cmd += ['-d']
    cmd += [device]

    if module.check_mode:
        cmd += ['-p']

    if module.params['utilities_only']:
        cmd += ['-i']
    if module.params['update_rpm']:
        cmd += ['-r']
    if module.params['skip_verify']:
        cmd += ['-s']
    if module.params['checksum']:
        cmd += ['-v']
    if module.params['suppress_multivolume']:
        cmd += ['-S']
    if not module.params['extend_fs']:
        cmd += ['-x']
    if module.params['commit']:
        cmd += ['-c']
    if not module.params['dependencies']:
        cmd += ['-n']
    if module.params['agree_licenses']:
        cmd += ['-Y']

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if rc != 0:
        result['msg'] = 'install_all_updates failed.'
        if module.check_mode:
            result['msg'] = 'install_all_updates preview failed.'
        module.fail_json(**result)

    result['msg'] = 'install_all_updates successful.'
    if not module.check_mode:
        if stdout.find('No filesets on the media could be used') == -1:
            result['changed'] = True
    else:
        result['msg'] = 'install_all_updates preview successful.'

    module.exit_json(**result)


if __name__ == '__main__':
    main()
