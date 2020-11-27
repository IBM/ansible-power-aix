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
module: lpp_facts
short_description: Returns installed software products as facts.
description:
- Lists and returns information about installed filesets or fileset updates in Ansible facts.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  filesets:
    description:
    - Specifies the names of software products.
    - Pattern matching characters, such as C(*) (asterisk) and C(?) (question mark), are valid.
    - Mutually exclusive with I(bundle).
    type: list
    elements: str
  bundle:
    description:
    - Specifies a file or bundle to use as the fileset list source.
    - Mutually exclusive with I(filesets).
    type: str
  path:
    description:
    - Specifies an alternate install location.
    type: str
  all_updates:
    description:
    - Returns all updates for a fileset (default is to return the most recent level only).
    - Mutually exclusive with I(base_levels_only).
    type: bool
    default: no
  base_levels_only:
    description:
    - Limits listings to base level filesets (no updates returned).
    - Mutually exclusive with I(all_updates).
    type: bool
    default: no
notes:
  - You can refer to the IBM documentation for additional information on the lslpp command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/l_commands/lslpp.html).
'''

EXAMPLES = r'''
- name: Gather the fileset facts
  lpp_facts:
- name: Check whether a fileset called 'openssh.base.client' is installed
  debug:
    msg: Fileset 'openssh.base.client' is installed
  when: "'openssh.base.client' in ansible_facts.filesets"

- name: Populate fileset facts with the installation state for the most recent
        level of installed filesets for all of the bos.rte filesets
  lpp_facts:
    filesets: bos.rte.*
- name: Print the fileset facts
  debug:
    var: ansible_facts.filesets

- name: Populate fileset facts with the installation state for all the filesets
        contained in the Server bundle
  lpp_facts:
    bundle: Server
- name: Print the fileset facts
  debug:
    var: ansible_facts.filesets
'''

RETURN = r'''
ansible_facts:
  description:
  - Facts to add to ansible_facts about the installed software products on the system
  returned: always
  type: complex
  contains:
    filesets:
      description:
      - Maps the fileset name to a dictionary of installed levels.
      returned: success
      type: dict
      elements: dict
      contains:
        name:
          description:
          - Fileset name
          returned: always
          type: str
          sample: "devices.scsi.disk.rte"
        levels:
          description:
          - Maps the fileset level to the fileset information.
          returned: always
          type: dict
          elements: dict
          contains:
            vrmf:
              description:
              - Fileset Version Release Modification Fix (vrmf).
              returned: always
              type: dict
              sample: '"vrmf": { "fix": 0, "mod": 3, "rel": 2, "ver": 7 }'
            state:
              description:
              - State of the fileset on the system.
              - C(applied) specifies that the fileset is installed on the system.
              - C(applying) specifies that an attempt was made to apply the specified fileset, but
                it did not complete successfully, and cleanup was not performed.
              - C(broken) specifies that the fileset or fileset update is broken and should be
                reinstalled before being used.
              - C(committed) specifies that the fileset is installed on the system.
              - C(efixlocked) specifies that the fileset is installed on the system and is locked by
                the interim fix manager.
              - C(obsolete) specifies that the fileset was installed with an earlier version of the
                operating system but has been replaced by a repackaged (renamed) newer version.
              - C(committing) specifies that an attempt was made to commit the specified fileset,
                but it did not complete successfully, and cleanup was not performed.
              - C(rejecting) specifies that an attempt was made to reject the specified fileset, but
                it did not complete successfully, and cleanup was not performed.
              returned: always
              type: str
            ptf:
              description:
              - Program temporary fix.
              returned: when available
              type: str
            type:
              description:
              - Fileset type.
              - C(install) specifies install image (base level).
              - C(maintenance) specifies maintenance level update.
              - C(enhancement).
              - C(fix).
              returned: always
              type: str
            description:
              description:
              - Fileset description.
              returned: always
              type: str
            emgr_locked:
              description:
              - Specifies whether fileset is locked by the interim fix manager.
              returned: always
              type: bool
            sources:
              description:
              - Source paths.
              returned: always
              type: list
              elements: str
              sample: ["/etc/objrepos"]
'''

from ansible.module_utils.basic import AnsibleModule


LPP_TYPE = {
    'I': 'install',
    'M': 'maintenance',
    'E': 'enhancement',
    'F': 'fix'
}


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filesets=dict(type='list', elements='str'),
            bundle=dict(type='str'),
            path=dict(type='str'),
            all_updates=dict(type='bool', default=False),
            base_levels_only=dict(type='bool', default=False)
        ),
        mutually_exclusive=[
            ['filesets', 'bundle'],
            ['all_updates', 'base_levels_only']
        ],
        supports_check_mode=True
    )

    lslpp_path = module.get_bin_path('lslpp', required=True)

    cmd = [lslpp_path, '-lcq']
    if module.params['all_updates']:
        cmd += ['-a']
    elif module.params['base_levels_only']:
        cmd += ['-I']
    if module.params['path']:
        cmd += ['-R', module.params['path']]
    if module.params['bundle']:
        cmd += ['-b', module.params['bundle']]
    elif module.params['filesets']:
        cmd += module.params['filesets']
    else:
        cmd += ['all']
    ret, stdout, stderr = module.run_command(cmd)
    # Ignore errors as lslpp might return 1 with -b

    # List of fields returned by lslpp -lc:
    # Source:Fileset:Level:PTF Id:State:Type:Description:EFIX Locked
    filesets = {}
    for line in stdout.splitlines():
        raw_fields = line.split(':')
        if len(raw_fields) < 8:
            continue
        fields = [field.strip() for field in raw_fields]

        name = fields[1]
        level = fields[2]

        if name not in filesets:
            filesets[name] = {'name': name, 'levels': {}}

        # There can be multiple levels for the same fileset if all_updates
        # is set (otherwise only the most recent level is returned).
        if level not in filesets[name]['levels']:
            info = {}

            vrmf = level.split('.')
            if len(vrmf) == 4:
                info['vrmf'] = {
                    'ver': int(vrmf[0]),
                    'rel': int(vrmf[1]),
                    'mod': int(vrmf[2]),
                    'fix': int(vrmf[3])
                }
            if fields[3]:
                info['ptf'] = fields[3]
            info['state'] = fields[4].lower()
            if fields[5]:
                info['type'] = LPP_TYPE.get(fields[5], '')
            info['description'] = fields[6]
            info['emgr_locked'] = fields[7] == 'EFIXLOCKED'
            info['sources'] = [fields[0]]

            filesets[name]['levels'][level] = info
        else:
            filesets[name]['levels'][level]['sources'].append(fields[0])

    results = dict(ansible_facts=dict(filesets=filesets))

    module.exit_json(**results)


if __name__ == '__main__':
    main()
