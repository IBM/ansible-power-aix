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
version_added: '2.9'
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
    - C(absent) deletes the user with provided I(name).
    - C(modify) changes the specified attributes of an exiting user.
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
    - Can be used when I(state=present).
    type: str
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


def modify_user(module):
    '''
    Modify_user function modifies the attributes of the user and returns
    output, return code and error of chuser command, if any.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Message for successfull command
    '''
    attributes = module.params['attributes']
    opts = ""
    load_module_opts = None
    msg = None

    if attributes is not None:
        for attr, val in attributes.items():
            if attr == 'load_module':
                load_module_opts = "-R %s " % val
            else:
                opts += "%s=%s " % (attr, val)
        if load_module_opts is not None:
            opts = load_module_opts + opts
        cmd = "chuser %s %s" % (opts, module.params['name'])

        rc, stdout, stderr = module.run_command(cmd)

        if rc != 0:
            msg = "\nFailed to modify attributes for the user: %s" % module.params['name']
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg = "\nAll provided attributes for the user: %s is set SUCCESSFULLY" % module.params['name']

    if module.params['password'] is not None:
        pass_msg = change_password(module)
        if msg is not None:
            msg += pass_msg
        else:
            msg = pass_msg

    return msg


def create_user(module):
    '''
    Create_user function creates the user with the attributes provided in the
    attribiutes field. It returns the standard output, return code and error
    for mkuser command, if any.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Message for successfull command
    '''
    attributes = module.params['attributes']
    opts = ""
    load_module_opts = None
    msg = None

    if attributes is not None:
        for attr, val in attributes.items():
            if attr == 'load_module':
                load_module_opts = "-R %s " % val
            else:
                opts += "%s=%s " % (attr, val)
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
        msg_pass = modify_user(module)
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
    cmd = ["lsuser"]
    cmd.append(module.params['name'])

    rc, out, err = module.run_command(cmd)
    if (rc == 0):
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
        Message for successfull command
    '''
    name = module.params['name']
    passwd = module.params['password']
    change_passwd_on_login = module.params['change_passwd_on_login']

    if change_passwd_on_login:
        cmd = "echo \'{user}:{password}\' | chpasswd -e".format(user=name, password=passwd)
    else:
        cmd = "echo \'{user}:{password}\' | chpasswd -ec".format(user=name, password=passwd)

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
        ),
        supports_check_mode=False
    )

    msg = ""
    attributes = module.params['attributes']
    changed = False

    if module.params['state'] == 'absent':
        if user_exists(module):
            msg = remove_user(module)
            changed = True
        else:
            msg = "User name is NOT FOUND : %s" % module.params['name']
    elif module.params['state'] == 'present':
        if not user_exists(module):
            msg = create_user(module)
            changed = True
        else:
            msg = "User %s already exists." % module.params['name']
    elif module.params['state'] == 'modify':
        if attributes is None and module.params['password'] is None:
            msg = "Please provide the attributes to be changed for the user: %s" % module.params['name']
        else:
            if user_exists(module):
                msg = modify_user(module)
                changed = True
            else:
                msg = "No user found in the system to modify the attributes: %s" % module.params['name']
    else:
        msg = "Invalid state. The state provided is not supported: %s" % module.params['state']

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
