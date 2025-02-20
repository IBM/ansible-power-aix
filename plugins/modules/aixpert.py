#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import os
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
module: aixpert
short_description: System security settings management.
description:
- This module uses the B(aixpert) command to manage a variety of system configuration settings
  enabling the desired security level on a logical partition (LPAR).
- It allows to query, check, apply, save, undo security settings.
version_added: '1.1.0'
requirements:
- AIX
- Python >= 3.6
- 'Privileged user with authorization: B(aix.security.aixpert)'
options:
  mode:
    description:
    - Specifies the action to be performed.
    - C(apply) applies the security settings based on the level specified or profile provided. If
      both are provided, I(level) will take precedence.
    - C(check) checks the security settings against the previously applied set of rules or the
      provided I(profile) file.
    - C(save) saves the security settings for the level specified or based on the specified
      I(profile) file. If I(abbr_fmt_file) is provided, the security rules are saved in the
      abbreviated file format. If I(norm_fmt_file) is provided, the security rules are saved in
      normal format.
    - C(undo) undoes the previously applied security settings.
    - C(query) gets the type of the profile applied on the system.
    type: str
    choices: [apply, check, save, undo, query]
    required: true
  level:
    description:
    - Specifies the security level settings to be applied or saved.
    - C(high) specifies high-level security options.
    - C(low) specifies low-level security options.
    - C(medium) specifies medium-level security options.
    - C(default) specifies AIX standards-level security options.
    - C(sox-cobit) specifies SOX-COBIT best practices-level security options.
    type: str
    choices: [ high, medium, low, default, sox-cobit ]
  profile:
    description:
    - When I(mode=apply), specifies the profile to be applied on the system.
    - When I(mode=check), specified the profile to be used to check the security settings.
    type: str
  abbr_fmt_file:
    description:
    - When I(mode=save) or I(mode=apply), specifies the file where the security settings need to
      be saved in abbreviated format.
    type: str
  norm_fmt_file:
    description:
    - When I(mode=apply) or I(mode=save), specifies the file where the settings should be saved in
      normal format.
    type: str
notes:
  - You can refer to the IBM documentation for additional information on the aixpert command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/a_commands/aixpert.html).
'''

EXAMPLES = r'''
- name: "Save default level rules in normal format"
  aixpert:
    mode: save
    level: default
    norm_fmt_file: /home/kavana/norm.xml

- name: "Apply using saved profile"
  aixpert:
    mode: apply
    profile: /home/kavana/norm.xml

- name: "Undo the settings"
  aixpert:
    mode: undo

- name: "Check the settings match the provided profile"
  aixpert:
    mode: check
    profile: /home/kavana/high.xml

- name: "Query the settings"
  aixpert:
    mode: query
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'aixpert security check completed successfully.'
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


def check_settings(module):
    """
    Checks the security settings against the previously applied set of rules
    param module: Ansible module argument spec.
    return: changed - True/False(check succeeded or not),
            msg - message
    """
    cmd = "aixpert -c "
    profile = module.params["profile"]
    if profile:
        cmd += f"-P {profile}"

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = f"aixpert security check failed. Command in failure {cmd}"
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    changed = True
    msg = "aixpert security check completed successfully."
    return changed, msg


def undo_settings(module):
    """
    Undoes the security settings
    param module: Ansible module argument spec.
    return: changed - True/False(settings undone or not),
            msg - message
    """
    cmd = "aixpert -u "
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = f"Unable to undo aixpert settings. Command in failure {cmd} "
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    changed = True
    msg = "aixpert settings undone successfully."
    return changed, msg


def apply_settings(module, mode):
    """
    Apply/save the specified level or provided security settings
    param module: Ansible module argument spec.
    param mode: apply/save
    return: changed - True/False(apply/save of security settings succeeded or not),
            msg - message
    """
    level = module.params["level"]
    abbr_fmt_file = module.params["abbr_fmt_file"]
    norm_fmt_file = module.params["norm_fmt_file"]
    profile = module.params["profile"]

    if profile and not os.path.isfile(profile):
        msg = f"Specified profile {profile} doesn't exist"
        return False, msg

    if mode == 'apply' and not level and not profile:
        msg = "Specify either level or profile to apply the security settings"
        return False, msg

    if mode == 'save' and not abbr_fmt_file and not norm_fmt_file:
        msg = "Specify either abbr_fmt_file or norm_fmt_file to save the security settings"
        return False, msg

    if profile and norm_fmt_file:
        msg = "'norm_fmt_file' cannot be specified when 'profile' is provided."
        return False, msg

    cmd = "aixpert "
    if level:
        cmd += f"-l {level} "
        if norm_fmt_file:
            cmd += f"-n -o {norm_fmt_file} "
    elif profile:
        cmd += f"-f {profile} "

    if abbr_fmt_file:
        cmd += f" -a -o {abbr_fmt_file} "

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = f"Unable to apply or save aixpert settings. Command in failure {cmd} "
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    # The aixpert can fail if file path is invalid  but still return 0"
    # setFilePosition():fopen(/home/test123321/norm.xml)  failed, errno=2
    pattern = "errno=2"
    found = re.search(pattern, stderr)
    if found:
        msg = f"Unable to access the file from command: {cmd} "
        module.fail_json(msg=msg, rc=1, stdout=stdout, stderr=stderr)

    changed = True
    msg = "aixpert settings applied/saved successfully."
    return changed, msg


def query_settings(module):
    """
    Get the security settings applied on the system
    param module: Ansible module argument spec.
    return: msg - message
    """
    cmd = "aixpert -t"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = f"Unable to query aixpert settings. Command in failure {cmd} "
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    msg = stdout
    return msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            level=dict(type='str', choices=['high', 'medium', 'low', 'default', 'sox-cobit']),
            mode=dict(type='str', required=True, choices=['check', 'undo', 'apply', 'save',
                                                          'query']),
            abbr_fmt_file=dict(type='str'),
            norm_fmt_file=dict(type='str'),
            profile=dict(type='str'),
        ),
    )

    mode = module.params['mode']

    if mode == 'check':
        # check the security settings against the previously applied rules
        changed, msg = check_settings(module)
    elif mode == 'undo':
        # Undoes the security settings
        changed, msg = undo_settings(module)
    elif mode == 'query':
        changed = False
        msg = query_settings(module)
    elif mode == 'apply' or mode == 'save':
        # Apply/save the security settings provided by level or profile
        changed, msg = apply_settings(module, mode)
    else:
        changed = False
        msg = f"Invalid state {mode}"

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
