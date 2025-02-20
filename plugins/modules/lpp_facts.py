#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import re
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: lpp_facts
short_description: Returns installed software products or fixes as facts.
description:
- Lists and returns information about installed filesets or fileset updates in Ansible facts.
version_added: '1.1.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
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
  reqs:
    description:
    - Returns all requisites for a fileset.
    type: bool
    default: no
  fix_type:
    description:
    - Specifies the type of fixes.
    - C(all) lists all the fixes installed on the system.
    - C(apar) lists only APAR fixes installed on the system.
    - C(service_pack) (alias C(sp)) lists the fixes installed in the system in service packs.
    - C(technology_level) (alias C(tl)) lists the fixes installed in the system as part of technology levels.
    - Mutually exclusive with fixes.
    type: str
    choices: [ all, apar, service_pack, sp, technology_level, tl ]
  fixes:
    description:
    - Specifies the names of the fixes.
    - Mutually exclusive with fix_type.
    type: list
    elements: str
notes:
  - You can refer to the IBM documentation for additional information on the lslpp command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/l_commands/lslpp.html).
  - You can refer to the IBM documentation for additional information on the instfix command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/i_commands/instfix.html).
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

- name: Populate fileset facts with the installation state for the most recent
        level of installed filesets for all of the bos.rte filesets with the
        requisites
  lpp_facts:
    filesets: bos.rte.*
    req: true
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

- name: Populate fixes facts with the fixes which are APARs only.
  lpp_facts:
    fix_type: apar
- name: Print the fixes facts
  debug:
    var: ansible_facts.fixes

- name: Populate fixes facts for the list of fixes with keywords
        7200-01_AIX_ML, IV82301, IV99819, 72-02-021832_SP .
  lpp_facts:
    fixes: 7200-01_AIX_ML, IV82301, IV99819, 72-02-021832_SP
- name: Print the fixes facts
  debug:
    var: ansible_facts.fixes
'''

RETURN = r'''
ansible_facts:
  description:
  - Facts to add to ansible_facts about the installed software products or fixes on the system
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
            requisites:
               description:
               - Requisites of the filesets
               returned: when available
               type: dict
               sample:
                "requisites": {
                    "coreq": {
                        "bos.aso": {
                            "name": "bos.aso",
                            "level": [
                                "7.2.0.0"
                            ],
                        }
                    }
                }
            ver_cons_check:
                description:
                - Status of fileset version consistency check
                returned: always
                type: str
                sample: "OK"
    fixes:
      description:
      - Maps the fixes name to the dictionary of filesets.
      returned: success
      type: dict
      elements: dict
      contains:
        name:
          description:
          - fixes name
          returned: always
          type: str
          sample: "IV82301"
        abstract:
          description:
          - Abstract of the fix
          returned: always
          type: str
          sample: "clcomd generates coredump"
        filesets:
          description:
          - Maps the fileset level to the fixes information.
          returned: always
          type: dict
          elements: dict
          contains:
            inst_level:
              description:
              - Installed level.
              returned: always
              type: str
              sample: '"inst_level": "7.2.1.0"'
            name:
              description:
              - fileset name
              returned: always
              type: str
            reqLevel:
              description:
              - Required level for the fix.
              returned: always
              type: str
            status:
              description:
              - C(Down Level) specifies that the fileset installed on the system is at a lower level than the required level
              - C(Correct level) specifies that the fileset installed on the system is at the same level as the required level
              - C(Superseded) specifies that the fileset installed on the system is at a higher level than the required level
              - C(not installed) specifies that the fileset is not installed on the system
              returned: always
              type: str

'''

LPP_TYPE = {
    'I': 'install',
    'M': 'maintenance',
    'E': 'enhancement',
    'F': 'fix'
}


def list_fixes(module):
    """
    List the fixes installed on the system including APAR, technology level
    service pack.
    param module: Ansible module argument spec.
    return: dict fixes
    """

    fixes = {}
    cmd = []
    fixes_list = []
    fix_type = ''
    is_continue = False

    # Details on what each status symbol means from instfix output
    FIX_STATUS = {
        '-': "Down Level",
        '=': "Correct Level",
        '+': "Superseded",
        '!': "Not installed"
    }

    instfix_path = module.get_bin_path('instfix', required=True)
    '''
    instfix sample output:
    Keyword:Fileset:ReqLevel:InstLevel:Status:Abstract
    IV82292:bos.net.tcp.ftp:7.2.1.0:7.2.5.1:+:FTP LEAKS MEMORY AND MAY DUMP CORE WITH TLS
    '''
    cmd = [instfix_path, '-icq']
    if module.params['fix_type']:
        fix_type = module.params['fix_type']
    elif module.params['fixes']:
        fixes_list = module.params['fixes']
        if len(fixes_list) > 0:
            cmdstr = ''
            for fix in fixes_list:
                cmdstr += fix.strip() + ' '
            cmdstr.strip()
            cmd += ['-k', cmdstr]

    stdout = module.run_command(cmd)[1]

    instfix_stdout = stdout.splitlines()
    for line in instfix_stdout:
        raw_fields = line.split(':')
        if len(raw_fields) < 6:
            continue
        fields = [field.strip() for field in raw_fields]
        name = fields[0]
        fileset_name = fields[1]
        abstract = fields[5]
        is_continue = False
        if (fix_type == "apar" and name.startswith('I')) \
           or ((fix_type == "service_pack" or fix_type == "sp")
               and name.endswith("_SP")) \
           or ((fix_type == "technology_level" or fix_type == "tl")
               and name.endswith("_ML")) \
           or (fix_type == "all"):
            is_continue = True
        if (fix_type != '' and is_continue) or fix_type == '':
            if name not in fixes:
                fixes[name] = {'name': name, 'abstract': abstract, 'filesets': {}}
            if fileset_name not in fixes[name]['filesets']:
                fileset_info = {}
                fileset_info['name'] = fileset_name
                fileset_info['reqLevel'] = fields[2]
                fileset_info['inst_level'] = fields[3]
                fileset_info['status'] = FIX_STATUS.get(fields[4], '')

            fixes[name]['filesets'][fileset_name] = fileset_info

    return fixes


def list_reqs(name, module):
    """
    List the requisites of the filesets
    param module: Ansible module argument spec.
    param name: fileset name for which requisites has to be gathered
    return: dict requisites
    """
    requisites = {}
    req_type_list = ["*coreq", "*prereq", "*ifreq", "*instreq"]
    i = 0

    lslpp_path = module.get_bin_path('lslpp', required=True)
    '''
    sample command output
    lslpp -pcq bos.perf.tools
    /usr/lib/objrepos:bos.perf.tools 7.2.5.100:*coreq bos.sysmgt.trace 5.3.0.30
    *coreq bos.perf.perfstat 5.3.0.30 *coreq perfagent.tools 5.3.0.50 *coreq bos.perf.pmaix
    7.1.3.0 *ifreq bos.adt.include 5.3.0.30 *ifreq bos.mp64 5.3.0.30 *ifreq bos.pmapi.lib
    5.3.0.30 *ifreq bos.rte.control 5.3.0.10 *prereq bos.rte.libc 7.1.3.0\n
    /etc/objrepos:bos.perf.tools 7.2.5.100:*coreq bos.sysmgt.trace 5.3.0.30
    *coreq bos.perf.perfstat 5.3.0.30 *coreq perfagent.tools 5.3.0.50 *coreq bos.perf.pmaix
    7.1.3.0 *ifreq bos.adt.include 5.3.0.30 *ifreq bos.mp64 5.3.0.30 *ifreq bos.pmapi.lib
    5.3.0.30 *ifreq bos.rte.control 5.3.0.10 *prereq bos.rte.libc 7.1.3.0
    '''
    cmd = [lslpp_path, '-cpq', name]

    stdout = module.run_command(cmd)[1]

    for line in stdout.splitlines():
        raw_fields = line.split(':')
        '''
        In cases where requisites are not present, then the length of the raw fields from
        the output line will be less than 3. Hence continue to the next line as this would not
        need any processing.
        '''
        if len(raw_fields) < 3:
            continue
        fields = [field.strip() for field in raw_fields]

        '''
        3rd field contains the requisites separated by spaces.
        Parse the requisites and categorize it as coreqs, prereqs, ifreqs.
        Sample 3rd field from lslpp -cpq
        *coreq bos.sysmgt.trace 5.3.0.30 *coreq bos.perf.perfstat 5.3.0.30 *coreq
        perfagent.tools 5.3.0.50 *coreq bos.perf.pmaix 7.1.3.0 *ifreq bos.adt.include
        5.3.0.30 *ifreq bos.mp64 5.3.0.30 *ifreq bos.pmapi.lib 5.3.0.30 *ifreq bos.rte.control
        5.3.0.10 *prereq bos.rte.libc 7.1.3.0
        '''

        '''
        Some of the filesets might have no requisites.
        Example:
        /usr/lib/objrepos:udapl.rte 7.2.5.100:NONE
        /etc/objrepos:udapl.rte 7.2.5.100:NONE
        '''
        if fields[2] == "NONE":
            continue

        reqs = re.split(r"\s+|{", fields[2])
        num_reqs = len(reqs)

        '''
        Requisites has 3 fields : req_type, fileset name, level.
        Minimum 1st 2 fields should be present.
        Sample
        *coreq bos.sysmgt.trace 5.3.0.30
        '''
        if len(reqs) >= 2:
            while i < num_reqs:
                # Reinitialize the local variables
                req_type = ''
                fileset = ''
                level = ''
                '''
                Get the type of requisite, fileset name and the level
                The values are in order and hence parse through the list
                and assign the values to the corresponding field names.
                If the requisites is not one of the types :
                instreq, ifreq, coreq, prereq then we don't need to process further.
                We continue to next requisite
                '''
                if reqs[i] not in req_type_list:
                    i = i + 1
                    continue
                # 1st field will be requisite type. ignore '*' in the requisite_type(Eg:
                # *coreq as coreq )
                req_type = reqs[i][1:]
                i = i + 1

                '''
                2nd field will be fileset name.
                This is to fill the fileset name which will be followed by level
                *coreq bos.sysmgt.trace 5.3.0.30
                In  this fileset will "bos.sysmgt.trace "
                '''
                fileset = reqs[i]
                i = i + 1
                '''
                level field may not be present in some cases. Hence
                only if level field is present update the value.
                Increment the iterator if the next field doesn't start with
                the next requisite set of fields and has only level information.
                (Example: *coreq bos.perf.perfstat)
                '''
                if i < num_reqs:
                    '''
                    3rd field will be fileset level. Sometimes this might be some additional
                    text followed by the level. So process the additional texts here and get the
                    level .
                    '''
                    if reqs[i] not in req_type_list:
                        '''
                        In some cases, prerequisites might be listed in brackets like below:
                        * *ifreq bos.rte.libc (5.2.0.0) 5.2.0.41
                        *ifreq bos.rte.libc (5.3.0.0) 5.3.0.1
                        In this case, both will be listed as part of levels.
                        '''
                        if '(' in reqs[i] or ')' in reqs[i]:
                            level += reqs[i]
                            i = i + 1

                        level += reqs[i]
                        i = i + 1

                # create a dictionary for each requisite type if not present already.
                if req_type not in requisites:
                    requisites[req_type] = {}
                if fileset not in requisites[req_type]:
                    requisites[req_type][fileset] = {}
                    requisites[req_type][fileset]["level"] = [level]
                else:
                    requisites[req_type][fileset]["level"].append(level)

                requisites[req_type][fileset]["name"] = fileset

    return requisites


def fileset_consistency_check(module, name):
    """
    Check the fileset consistency
    param module: Ansible module argument spec.
    param name: fileset name for which fileset consistency check has to be done
    return: status of fileset version consistency check
            'OK' , if success
            'NOT OK', if failure
    """
    lppchk_path = module.get_bin_path('lppchk', required=True)
    cmd = f"{lppchk_path} -v {name}"
    cons_check = 'UNKNOWN'
    ret = module.run_command(cmd)[0]
    if ret == 0:
        cons_check = "OK"
    else:
        cons_check = "NOT OK"
    return cons_check


def main():
    module = AnsibleModule(
        argument_spec=dict(
            filesets=dict(type='list', elements='str'),
            bundle=dict(type='str'),
            path=dict(type='str'),
            all_updates=dict(type='bool', default=False),
            base_levels_only=dict(type='bool', default=False),
            fixes=dict(type='list', elements='str'),
            fix_type=dict(type='str', choices=['apar', 'technology_level',
                                               'service_pack', 'sp', 'tl', 'all']),
            reqs=dict(type='bool', default=False)
        ),
        mutually_exclusive=[
            ['filesets', 'bundle'],
            ['all_updates', 'base_levels_only'],
            ['fixes', 'fix_type']
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

    stdout = module.run_command(cmd)[1]

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
            cons_check = fileset_consistency_check(module, name)
            filesets[name] = {'name': name, 'levels': {}, 'ver_cons_check': cons_check}

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
            if module.params["reqs"] is True:
                info["requisites"] = list_reqs(name, module)

            filesets[name]['levels'][level] = info
        else:
            filesets[name]['levels'][level]['sources'].append(fields[0])

    fixes = {}
    if module.params["fix_type"] or module.params["fixes"]:
        fixes = list_fixes(module)

    results = dict(ansible_facts=dict(filesets=filesets, fixes=fixes))
    module.exit_json(**results)


if __name__ == '__main__':
    main()
