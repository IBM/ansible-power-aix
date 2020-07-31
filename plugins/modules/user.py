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
  modification of attributes of existing user and the deletion of user.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- Root user is required.
options:
  state:
    description:
    - Specifies the action to be performed for the user.
    - C(present) to create user with provided I(name) and I(attributes) in the system.
    - C(absent) to delete user with provided I(name). If username is not present then message will be displayed.
    - C(modify) to change the specified attributes with provided value of the given username.
    type: str
    choices: [ present, absent, modify ]
    required: true
  name:
    description: Specifies the user name for which the action is to be taken.
    type: str
    aliases: [ user ]
    required: true
  attributes:
    description: Specifies the attributes to be changed or created for the user.
    type: dict
  remove_password:
    description:
    - Specifies if the password information should be deleted from the system's password
      file while performing the delete operation on username.
    type: bool
    default: True
  change_passwd_on_login:
    description:
    - Specifies if the user is required to change the password when logging in the first time
      after the password change operation is performed.
    type: bool
    default: False
  password:
    description: Specifies the encrypted string for the password to create or change the password.
    type: str
'''

EXAMPLES = r'''
- name: Create user aixguest1010
  user:
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

    cmd = ['mkuser']
    cmd.append(module.params['name'])

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "Failed to create user: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "Username is created SUCCESSFULLY: %s" % module.params['name']

    if attributes is not None or module.params['password'] is not None:
        msg_attr = modify_user(module)
        msg += msg_attr

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
    cmd = ['rmuser']

    if module.params['remove_password']:
        cmd.append('-p')

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
        cmd = "echo \'{user}:{password}\' | chpasswd -ec".format(user=name, password=passwd)
    else:
        cmd = "echo \'{user}:{password}\' | chpasswd -e".format(user=name, password=passwd)

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
            remove_password=dict(type='bool', default=True),
            change_passwd_on_login=dict(type='bool', default=False),
            password=dict(type='str'),
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
