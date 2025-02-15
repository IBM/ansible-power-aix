#!/usr/bin/python
# -*- coding: utf-8 -*-

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# AIX 7.3: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_73/c_commands/chsec.html
# AIX 7.2: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/c_commands/chsec.html
# AIX 7.1: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_71/c_commands/chsec.html
# AIX 6.1 PDF: https://public.dhe.ibm.com/systems/power/docs/aix/61/aixcmds1_pdf.pdf

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

DOCUMENTATION = r'''
---
module: password_rules_policies
short_description: Manages password rules and policies
version_added: 1.9.0
description:
  - Manages password rules and policies by modifying stanza attributes in AIX config file - /etc/security/user
    using the C(chsec) command.
author:
  - Shreyansh Chamola (@schamola)
requirements:
  - AIX
  - Python >= 2.7
  - 'Privileged user with authorizations'
options:
  state:
    description:
      - If set to C(present) all given attrs values will be set.
      - If set to C(absent) all attrs provided will be un-set, regardless of value provided.
      - NB, this does not remove the entire stanza, only the provided attrs will be removed.
      - To remove a single attribute from the stanza set to C(present) and set key to an empty value (key=).
      - All rules/allowed file-stanza combos/allowed files for the AIX C(chsec) command apply here.
    type: str
    choices: [ absent, present ]
    default: present
  stanza:
    description:
      - Name of stanza to modify attributes of
    type: str
    required: true
  account_locked:
    description:
      - Indicates if the user account is locked.
    type: bool
    required: false
  admin:
    description:
      - Defines the administrative status of the user.
    type: bool
    required: false
  admgroups:
    description:
      - Lists the groups the user administrates.
    type: list
    required: false
  auditclasses:
    description:
      - Lists the user's audit classes.
    type: list
    required: false
  auth1:
    description:
      - Lists additional mandatory methods for authenticating the user.
      - The auth1 attribute has been deprecated and may not be supported in a future release. The SYSTEM attribute should be used instead.
      - The authentication process will fail if any of the methods specified by the auth1 attribute fail.
    type: list
    required: false
  auth2:
    description:
      - Lists additional optional methods for authenticating the user.
      - The auth2 attribute has been deprecated and may not be supported in a future release. The SYSTEM attribute should be used instead.
      - The authentication process will not fail if any of the methods specified by the auth2 attribute fail.
    type: list
    required: false
  core_compress:
    description:
      - Enables or disables core file compression.
      - If this attribute has a value of C(On), compression is enabled; otherwise, compression is disabled.
    type: str
    required: false
    choices: ['on', 'off']
  core_path:
    description:
      - Enables or disables core file path specification.
      - If this attribute has a value of C(On), core files will be placed in the directory specified by core_pathname (the feature is enabled);
      - If set to C(Off), core files are placed in the user's current working directory.
    type: str
    required: false
    choices: ['on', 'off']
  core_pathname:
    description:
      - Specifies a location to be used to place core files, if the core_path attribute is set to C(On).
      - If this is not set and I(core_path=On), core files will be placed in the user's current working directory.
      - This attribute is limited to 256 characters.
    type: str
    required: false
  core_naming:
    description:
      - Selects a choice of core file naming strategies.
      - A value of C(On) enables core file naming in the form core.pid.time
    type: str
    required: false
    choices: ['on', 'off']
  daemon:
    description:
      - Indicates whether the user specified by the Name parameter can execute programs using the cron daemon or the src (system resource controller) daemon.
    type: bool
    required: false
  dce_export:
    description:
      - Allows the DCE registry to overwrite the local user information with the DCE user information during a DCE export operation.
    type: bool
    required: false
  dictionlist:
    description:
      - Defines the password dictionaries used by the composition restrictions when checking new passwords.
    type: list
    required: false
  minloweralpha:
    description:
      - Defines the minimum number of lower case alphabetic characters that must be in a new password.
    type: str
    required: false
  minupperalpha:
    description:
      - Defines the minimum number of upper case alphabetic characters that must be in a new password.
    type: str
    required: false
  mindigit:
    description:
      - Defines the minimum number of digits that must be in a new password.
    type: str
    required: false
  minspecialchar:
    description:
      - Defines the minimum number of special characters that must be in a new password.
    type: str
    required: false
  efs_adminks_access:
    description:
      - Defines the efs_admin keystore location.
      - This attribute is valid only if the system is EFS-enabled.
    type: str
    required: false
    choices: ['files']
  efs_allowksmodechangebyuser:
    description:
      - Defines whether the user can change the mode or not.
      - This attribute is valid only if the system is EFS-enabled.
    type: str
    required: false
    choices: ['yes', 'no']
  efs_file_algo:
    description:
      - Defines the algorithm that is used to generate the file protection key.
      - This attribute is valid only if the system is EFS-enabled.
    type: str
    required: false
    choices: ['AES_128_CBC', 'AES_192_CBC', 'AES_256_CBC']
  efs_initialks_mode:
    description:
      - Defines the initial mode of the user keystore.
      - This attribute is valid only if the system is EFS-enabled.
    type: str
    required: false
    choices: ['guard', 'admin']
  efs_keystore_access:
    description:
      - Defines the user keystore location.
      - This attribute is valid only if the system is EFS-enabled.
    type: str
    required: false
    choices: ['none', 'file']
  efs_keystore_algo:
    description:
      - Defines the user keystore location.
      - This attribute is valid only if the system is EFS-enabled.
    type: str
    required: false
    choices: ['RSA_1024', 'RSA_2048', 'RSA_4096']
  expires:
    description:
      - Identifies the expiration date of the account.
      - The Value parameter is a 10-character string in the MMDDhhmmyy form, where MM = month,
        DD = day, hh = hour, mm = minute, and yy = last 2 digits of the years 1939 through 2038.
    type: str
    required: false
  histexpire:
    description:
      - Designates the period of time (in weeks) that a user cannot reuse a password.
    type: str
    required: false
  histsize:
    description:
      - Designates the number of previous passwords a user cannot reuse.
    type: str
    required: false
  login:
    description:
      - Indicates whether the user can log in to the system with the login command.
    type: bool
    required: false
  logintimes:
    description:
      - Specifies the times, days, or both, the user is allowed to access the system.
      - The day variable must be one digit between 0 and 6 that represents one of the days of the week.
        A 0 (zero) indicates Sunday and a 6 indicates Saturday.
      - The time variable is 24-hour military time (1700 is 5:00 p.m.). Leading zeroes are required.
        For example, you must enter 0800, not 800.
      - The date variable is a four digit string in the form mmdd. mm represents the calendar month and dd represents the day number.
      - Entries in this list specify times that a user is allowed or denied access to the system.
    type: str
    required: false
  loginretries:
    description:
      - Defines the number of unsuccessful login attempts allowed after the last successful login before the system locks the account.
    type: str
    required: false
  maxage:
    description:
      - Defines the maximum age (in weeks) of a password.
    type: str
    required: false
  maxexpired:
    description:
      - Defines the maximum time (in weeks) beyond the maxage value that a user can change an expired password.
    type: str
    required: false
  maxrepeats:
    description:
      - Defines the maximum number of times a character can be repeated in a new password.
    type: str
    required: false
  minage:
    description:
      - Defines the minimum age (in weeks) a password must be before it can be changed.
    type: str
    required: false
  minalpha:
    description:
      - Defines the minimum number of alphabetic characters that must be in a new password.
    type: str
    required: false
  mindiff:
    description:
      - Defines the minimum number of characters required in a new password that were not in the old password.
    type: str
    required: false
  minlen:
    description:
      - Defines the minimum length of a password.
    type: str
    required: false
  minother:
    description:
      - Defines the minimum number of non-alphabetic characters that must be in a new password.
    type: str
    required: false
  projects:
    description:
      - Defines the list of projects that the user's processes can be assigned to.
    type: list
    required: false
  pwdchecks:
    description:
      - Defines the password restriction methods enforced on new passwords.
    type: list
    required: false
  pwdwarntime:
    description:
      - Defines the number of days before the system issues a warning that a password change is required.
    type: str
    required: false
  registry:
    description:
      - Defines the authentication registry where the user is administered.
    type: str
    required: false
    choices: ['files', 'NIS', 'DCE']
  rlogin:
    description:
      - Permits access to the account from a remote location with the telnet or rlogin commands.
    type: bool
    required: false
  su:
    description:
      - Indicates whether another user can switch to the specified user account with the su command.
    type: bool
    required: false
  sugroups:
    description:
      - Lists the groups that can use the su command to switch to the specified user account.
    type: str
    required: false
  SYSTEM:
    description:
      - Defines the system authentication mechanism for the user.
    type: str
    required: false
  tpath:
    description:
      - Indicates the user's trusted path status.
    type: str
    required: false
    choices: ['always', 'notsh', 'nosak', 'on']
  ttys:
    description:
      - Lists the terminals that can access the account specified by the Name parameter.
    type: str
    required: false
  umask:
    description:
      - Determines file permissions. This value, along with the permissions of the creating process
        determines a file's permissions when the file is created.
    type: str
    required: false

notes:
  - If the registry is set to NIS or DCE, it can not be removed.
  - For removing an attribute, you need to provide a valid value along with state as absent.
  - Refer to the chsec manual page from the IBM Knowledge Center
    U(https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/c_commands/chsec)
  - Refer to the lssec manual page from the IBM Knowledge Center
    U(https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/l_commands/lssec.html)
'''

EXAMPLES = r'''
'''

RETURN = r'''
changed:
  description: Was this value changed
  returned: always
  type: bool
  sample: False
msg:
  description: The execution message.
  returned: always
  type: str
  sample: 'Invalid parameter: install_list cannot be empty'
file:
  description: The file being modified
  returned: always
  type: str
stanza:
  description: The stanza in file being modified
  returned: always
  type: str
attrs:
  description: For each attribute provided in the 'attrs' section, an entry (below) is returned
  type: dict
  returned: always
  contains:
    cmd:
      description: Command that is run to update attr
      returned: Only if attr requires change
      type: str
    stdout:
      description: The standard output of the command.
      returned: only when cmd is run
      type: str
    stderr:
      description: The standard error of the command.
      returned: only when cmd is run
      type: str
    rc:
      description: The command return code.
      returned: only when cmd is run
      type: int
'''

result = dict(
    changed=False,
    cmd='',
    msg='',
    rc='',
    stdout='',
    stderr='',
)


def set_attr_value(module, stanza, attr, target_value):
    # -> dict:
    """ Sets the selected file->stanza->attr=target_value.
    If command fails, exits using module.fail_json.
    Returns a dict of:
        cmd: string of command run
        rc: int of return code
        stdout: stdout
        stderr: stderr
    """
    chsec_command = module.get_bin_path('chsec', required=True)
    if str(target_value) in ["True", "False"]:
        if str(target_value) == "True":
            target_value = "true"
        else:
            target_value = "false"
    cmd = [
        chsec_command,
        '-f', '/etc/security/user',
        '-s', stanza,
        '-a', '='.join(map(str, [attr, target_value]))
    ]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run chsec command: ' + ' '.join(cmd)
        if "3004-692" in stderr:
            msg += f"Invalid value provided - {target_value}"
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    return_dict = {
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }
    return return_dict


def get_current_attr_value(module, stanza, attr):
    """
    Returns the current value of the provided attribute
    arguments:
        module (dict) - Ansible generic argument spec
        stanza (str) - Stanza for which the attribute needs to be checked
        attr (str) - Attribute that needs to be checked
    returns:
        lssec_out (str) - Current value of the provided attribute
    """
    lssec_command = module.get_bin_path('lssec', required=True)
    cmd = [lssec_command, '-c', '-f', '/etc/security/user', '-s', stanza, '-a', attr]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        if "3004-725" in stderr:
            msg = f"Invalid stanza: '{stanza}'"
        else:
            msg = 'Failed to run lssec command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    # Strip newline and double-quotation marks that are sometimes added
    lssec_out = stdout.splitlines()[1].split(':', 1)[1].strip('\\\"\n')
    return str(lssec_out)


def run_chsec(module):
    """
    Runs chsec command to change/add the values of various attributes in /etc/security/user file.
    arguments:
        module (dict) - Generic Ansible module
    returns:
        results (dict) - Contains information about attributes.
    """
    stanza = module.params["stanza"]
    state = module.params["state"]

    results = {
        'changed': False,
        'stanza': stanza,
        'attrs': {},
    }

    changed_attrs = 0

    params = module.params
    for attr in params.keys():
        if attr in ["state", "stanza"] or not params[attr]:
            continue
        if state == 'absent':
            target_val = ''
        else:
            target_val = str(params[attr])
        current_val = get_current_attr_value(module, stanza, attr)

        msg_attr = {
            'status': 'unchanged',
            'desired_value': target_val,
            'existing_value': current_val,
        }

        if current_val != target_val:
            if module.check_mode:
                msg_attr["check_mode"] = True
            else:
                cmd_return = set_attr_value(module, stanza, attr, target_val)
                msg_attr.update(cmd_return)
            results['changed'] = True
            msg_attr['status'] = 'changed'
            changed_attrs += 1
        results['attrs'][attr] = msg_attr
    return results


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', default='present', choices=['absent', 'present']),
            stanza=dict(type='str', required=True),
            account_locked=dict(type='bool'),
            admin=dict(type='bool'),
            admgroups=dict(type='list'),
            auditclasses=dict(type='list'),
            auth1=dict(type='list'),
            auth2=dict(type='list'),
            core_compress=dict(type='str', choices=['on', 'off']),
            core_path=dict(type='str', choices=['on', 'off']),
            core_pathname=dict(type='str'),
            core_naming=dict(type='str', choices=['on', 'off']),
            daemon=dict(type='bool'),
            dce_export=dict(type='bool'),
            dictionlist=dict(type='list'),
            minloweralpha=dict(type='str'),
            minupperalpha=dict(type='str'),
            mindigit=dict(type='str'),
            minspecialchar=dict(type='str'),
            efs_adminks_access=dict(type='str', choices=['file']),
            efs_allowksmodechangebyuser=dict(type='str', choices=['yes', 'no']),
            efs_file_algo=dict(type='str', choices=['AES_128_CBC', 'AES_192_CBC', 'AES_256_CBC']),
            efs_initialks_mode=dict(type='str', choices=['guard', 'admin']),
            efs_keystore_access=dict(type='str', choices=['none', 'file']),
            efs_keystore_algo=dict(type='str', choices=['RSA_1024', 'RSA_2048', 'RSA_4096']),
            expires=dict(type='str'),
            histexpire=dict(type='str'),
            histsize=dict(type='str'),
            login=dict(type='bool'),
            logintimes=dict(type='str'),
            loginretries=dict(type='str'),
            maxage=dict(type='str'),
            maxexpired=dict(type='str'),
            maxrepeats=dict(type='str'),
            minage=dict(type='str'),
            minalpha=dict(type='str'),
            mindiff=dict(type='str'),
            minlen=dict(type='str'),
            minother=dict(type='str'),
            projects=dict(type='list'),
            pwdchecks=dict(type='list'),
            pwdwarntime=dict(type='str'),
            registry=dict(type='str'),
            rlogin=dict(type='bool'),
            su=dict(type='bool'),
            sugroups=dict(type='str'),
            SYSTEM=dict(type='str'),
            tpath=dict(type='str', choices=['always', 'notsh', 'nosak', 'on']),
            ttys=dict(type='str'),
            umask=dict(type='str'),
        ),
        supports_check_mode=True,
    )

    result = run_chsec(module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
