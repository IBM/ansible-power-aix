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
module: user
short_description: Create new users or change/remove attributes of users on AIX.
description:
- This module facilitates the creation of a new user with provided attributes, the
  modification of attributes or deletion of an existing user.
version_added: '1.0.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- Root user is required.
- 'Privileged user with authorizations:
  B(aix.security.user.remove.admin,aix.security.user.remove.normal,aix.security.user.create.admin,aix.security.user.create.normal,,aix.security.user.change,aix.security.user.list)'
options:
  state:
    description:
    - Specifies the action to be performed for the user.
    - C(present) creates a user with provided I(name) and I(attributes) in the system.
    - If the user already exists in the system, the I(attributes) will be changed.
    - C(absent) deletes the user with provided I(name).
    - C(modify) changes the specified I(attributes) of an exiting user.
    - If the user doesn't exist on the system, it will be created.
    type: str
    choices: [ present, absent, modify ]
    required: true
  name:
    description:
    - Specifies the user name.
    - It must be unique, you cannot use the ALL or default keywords in the user name.
    type: str
    aliases: [ user ]
    required: true
  attributes:
    description:
    - Specifies the attributes to be changed or created for the user.
    - For details on valid user attributes, please refers to IBM documentation at
      U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chuser.html).
    - If you have the proper authority, you can set the following usual user attributes
      account_locked, admin, admgroups, capabilities, cpu, daemon, data, default_roles, dictionlist,
      domains, expires, fsize, fsize_hard, gecos, groups, histexpire, home, id, login, loginretries,
      logintimes, maxages, maxexpired, maxrepeats, maxulogs, minage, minalpha, mindiff, minlen,
      minother, nofiles, nproc, pgrp, projects, pwdchecks, pwdwarntime, rcmds, rlogin, roles, rss,
      shell, stack, su, sugroups, sysenv, threads, tpath, ttys, umask, usrenv, etc.
    type: dict
  remove_homedir:
    description:
    - Specifies if the home directory should be deleted from the system while removing a user.
    - Can be used when I(state=absent).
    type: bool
    default: True
  change_passwd_on_login:
    description:
    - Specifies if the user is required to change the password when logging in the first time after
      the password change operation is performed.
    - Can be used when I(state=present).
    type: bool
    default: False
  password:
    description:
    - Specifies the encrypted string for the password to create or change the password.
    - Can be used when I(state=present) or I(state=modify).
    type: str
  load_module:
    description:
    - Specifies the location where the operations need to be performed on the user.
    - C(files) creates/updates/deletes the user present in the Local machine.
    - C(LDAP) creates/updates the user present in the LDAP server.
    type: str
    default: 'files'
    choices: [files, LDAP]
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chuser.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mkuser.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmuser.html).
'''

EXAMPLES = r'''
- name: Create user aixguest1010
  ibm.power_aix.user:
    state: present
    name: aixguest1010
    change_passwd_on_login: False
    password: as$12ndhkfjk$1c
    attributes:
      home: /home/test/aixguest1010
      data: 1272
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Username is created SUCCESSFULLY: aixguest1010'
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


def get_chuser_command(module):
    '''
    Returns the 'cmd' needed to run to implement changes on
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        cmd string, or None if no changes are necessary.
    '''
    # 'attributes' contains all of the key=value pairs that Ansible wants us to set
    attributes = module.params['attributes']
    if attributes is None:
        # No attributes to change, return None before we do anything.
        return None

    # 'user_attrs' contains the key=value pairs that are _currently_ set in AIX
    lsuser_cmd = "lsuser -R %s -C %s" % (module.params['load_module'], module.params['name'])
    rc, stdout, stderr = module.run_command(lsuser_cmd)
    if rc != 0:
        msg = "\nFailed to validate attributes for the user: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    keys = stdout.splitlines()[0].split(':')
    values = stdout.splitlines()[1].split(':')
    user_attrs = dict(zip(keys, values))

    # Adding the load module to the command so that the correct user's attributes are changed.
    load_module_opts = "-R %s " % module.params['load_module']

    # Now loop over every key-value in attributes
    opts = ""
    cmd = ""
    load_module_opts = None
    for attr, val in attributes.items():
        pattern = re.compile(r'(yes|true|always|no|false|never)', re.IGNORECASE)
        if val in [True, False] or re.match(pattern, str(val)):
            val = str(val).lower()
        # For idempotency, we compare what Anisble whats the value to be
        #  compared to what is already set
        # Only add attr=val to the opts list they're different. No reason to
        #  if the values are identical!
        if user_attrs[attr] != val:
            opts += "%s=\"%s\" " % (attr, val)

    if load_module_opts is not None:
        opts = load_module_opts + opts
    if opts:
        cmd = "chuser %s %s" % (opts, module.params['name'])

    if not cmd:
        # No change sare necessary.  It's best to return None instead of an empty string
        cmd = None
    return cmd


def parse_lsuserf_output(stdout):
    '''
    parse_lsuserf_output returns a dict with all values parsed from
    lsuser -f output.

    argument:
        stdout:  List of lines. Output from lsuser -f.
    return:
        (dict):  Attributes in python dict.
    '''
    attrs = {}
    for line in stdout.splitlines():
        if '=' in line:
            attr, value = line.split('=')
            attr = attr.strip()
            value = value.strip()
            if value != "":
                attrs[attr] = value
    return attrs


def get_user_attrs(module):
    '''
    get_user_attrs returns a dict with all attributes defined for the user.
    The user must exist. The function will not check its existence.

    argument:
        module  (dict): The Ansible module
    return:
        (dict): User attributes
    '''
    cmd = "lsuser -f %s" % module.params['name']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return {}
    return parse_lsuserf_output(stdout)


def changed_attrs(module, current):
    '''
    changed_attrs checks the difference between current attributes of
    a user and the attributes set in the module.
    Dictionary with changed values is returned.

    argument:
        module  (dict): The Ansible module
        current (dict): Current user attributes
    return:
        (dict): Changed user attributes
    '''
    newattrs = module.params['attributes']
    changed = {k: newattrs[k] for k in newattrs if k in current and str(newattrs[k]) != current[k]}
    return changed


def modify_user(module):
    '''
    Modify_user function modifies the attributes of the user and returns
    output, return code and error of chuser command, if any.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        (message for command, changed status)
    '''

    msg = None
    changed = False
    # Get current user attributes
    current_attrs = get_user_attrs(module)
    # Get user attributes to change
    attrs = changed_attrs(module, current_attrs)
    # Redefine attributes
    module.params['attributes'] = attrs
    # Get + Run chuser commands
    cmd = get_chuser_command(module)
    if cmd is not None:
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "\nFailed to modify attributes for the user: %s" % module.params['name']
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg = "\nAll provided attributes for the user: %s are set SUCCESSFULLY" % module.params['name']
        changed = True

    # Change user password
    if module.params['password'] is not None:
        msg_pass = change_password(module)
        if msg is not None:
            msg += msg_pass
        else:
            msg = msg_pass
        changed = True

    if msg is None:
        msg = "No changes were made."

    return (msg, changed)


def create_user(module):
    '''
    Create_user function creates the user with the attributes provided in the
    attribiutes field. It returns the standard output, return code and error
    for mkuser command, if any.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
        If this successfully returns, that means changes were made.
    return:
        Message for successful command.
    '''
    attributes = module.params['attributes']
    opts = ""
    load_module_opts = None
    msg = ""

    # Adding the load module to the command so that the user is created at the right location.
    load_module_opts = "-R %s " % module.params['load_module']

    if attributes is not None:
        for attr, val in attributes.items():
            opts += "%s=\"%s\" " % (attr, val)
        if load_module_opts is not None:
            opts = load_module_opts + opts
    cmd = "mkuser %s %s" % (opts, module.params['name'])
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Failed to create user: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "Username is created SUCCESSFULLY: %s" % module.params['name']

    if module.params['password'] is not None:
        msg_pass = change_password(module)
        msg += msg_pass
    return msg


def remove_user(module):
    '''
    Remove_user function removes the user from the system.It returns the standard output,
    return code and error for mkuser command, if any.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Message for successfull command
    '''
    cmd = ['userdel']

    if module.params['remove_homedir']:
        cmd.append('-r')

    cmd.append(module.params['name'])

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "Unable to remove the user name: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "User name is REMOVED SUCCESSFULLY: %s" % module.params['name']

    return msg


def user_exists(module):
    '''
    Checks if the specified user exists in the system or not.

    arguments:
        module  (dict): The Ansible module
    return:
        True if the user exists
        False if the user does not exist
    '''
    cmd = "lsuser "

    # Adding the load module to the command so that the user's existence is checked at the right location.
    load_module_opts = "-R %s" % module.params['load_module']
    cmd += load_module_opts
    cmd += " %s" % module.params['name']

    rc, out, err = module.run_command(cmd)
    if rc == 0:
        return True
    else:
        return False


def change_password(module):
    '''
    Changes the password of the specified user. Clears all the default
    flags set by system if first time login password change is not required

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Message for successful command
    '''
    name = module.params['name']
    passwd = module.params['password']
    change_passwd_on_login = module.params['change_passwd_on_login']

    if change_passwd_on_login:
        cmd = "echo \'{user}:{password}\' | chpasswd -e".format(user=name, password=passwd)
    else:
        cmd = "echo \'{user}:{password}\' | chpasswd -e -c".format(user=name, password=passwd)

    cmd += " -R %s" % module.params['load_module']
    pass_rc, pass_out, pass_err = module.run_command(cmd, use_unsafe_shell=True)
    if pass_rc != 0:
        msg = "\nFailed to set password for the user: %s" % module.params['name']
        module.fail_json(msg=msg, rc=pass_rc, stdout=pass_out, stderr=pass_err)
    else:
        msg = "\nPassword is set successfully for the user: %s" % module.params['name']

    return msg


def main():
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['present', 'absent', 'modify']),
            name=dict(type='str', required=True, aliases=['user']),
            attributes=dict(type='dict'),
            remove_homedir=dict(type='bool', default=True, no_log=False),
            change_passwd_on_login=dict(type='bool', default=False, no_log=False),
            password=dict(type='str', no_log=True),
            load_module=dict(type='str', default='files', choices=['files', 'LDAP']),
        ),
        supports_check_mode=False
    )

    msg = ""
    changed = False

    if module.params['state'] == 'absent':
        if user_exists(module):
            msg = remove_user(module)
            changed = True
        else:
            msg = "User name is NOT FOUND : %s" % module.params['name']
    elif module.params['state'] == 'present' or module.params['state'] == 'modify':
        if not user_exists(module):
            msg = create_user(module)
            changed = True
        else:
            msg = "User %s already exists." % module.params['name']
            if module.params['attributes'] is None and module.params['password'] is None:
                msg = "Please provide the attributes to be changed for the user: %s" % module.params['name']
            else:
                msg, changed = modify_user(module)
    else:
        msg = "Invalid state. The state provided is not supported: %s" % module.params['state']

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
