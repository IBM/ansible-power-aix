#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
author:
- AIX development Team (@pbfinley1911)
module: group
short_description: Create new group or change/remove attributes of group on AIX
description:
    - This module facilitates the creation of a new group with provided attributes, the
      modification of attributes of existing group and the deletion of group.
version_added: "2.9"
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- Root user is required.

options:
    group_attributes:
        description:
        - Provide the attributes to be changed or created for the group.
        type: dict
        default: None
    user_list_action:
        description:
        - Provides the action choices of adding or removing the members or admins.
        I(add) = Adding members or amdins of the group
        I(remove) = Removing members or admins of the group
        type: str
        default: None
    user_list_type:
        description:
        - Provides the action to be taken for the group members or admins.
        I(members) = Provided I(user_list_action) choice will be performed on members of the group
        I(admins) = Provided I(user_list_action) choice will be performed on admins of the group
        type: str
        default: None
    state:
        description:
        - Specifies the action to be performed for the group.
        - I(present) = New group will be created in the system with provided attributes. If group is already
          present then attributes specified for the group will be changed with the provided attributes.
        - I(absent) = Group will be deleted. If group is not present then message will be displayed for the same.
        type: str
    name:
        description:
        - Group name should be specified for which the action is to taken
        type: str
    users_list:
        description:
        - Name of the users separated by commas to be added/removed as members/admins of the group.
        - Should be used along with I(user_list_action) and I(user_list_type parameters).
        type: str
        default: None
    remove_keystore:
        description:
        - Specifies if the group's keystore information should be deleted from the system while performing
          the delete operation on group.
        type: bool
        default: True
"""

EXAMPLES = r'''
- name: "Change group ansible"
    group:
        state: 'present'
        name: 'ansible'
        user_list_action: 'add'
        user_list_type: 'member'
        users_list: 'test1'
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
rc':
    description: The return code.
    returned: If the command failed.
    type: int
stdout':
    description: The standard output.
    returned: If the command failed.
    type: str
stderr':
    description: The standard error.
    returned: If the command failed.
    type: str
'''


from ansible.module_utils.basic import AnsibleModule


def modify_group(module):
    """
    Modify the attributes of the user.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success or error message.
    """

    group_attributes = module.params['group_attributes']
    user_list_action = module.params['user_list_action']
    opts = ""
    load_module_opts = None
    msg = ""

    if group_attributes is not None:
        for attr, val in group_attributes.items():
            if attr == 'load_module':
                load_module_opts = "-R %s " % val
            else:
                opts += "%s=%s " % (attr, val)
        if load_module_opts is not None:
            opts = load_module_opts + opts
        cmd = "chgroup %s %s" % (opts, module.params['name'])
        rc, stdout, stderr = module.run_command(cmd)

        if rc != 0:
            msg = "\nFailed to modify attributes for the group: %s" % module.params['name']
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg = "\nAll provided attributes for the group: %s is set SUCCESSFULLY" % module.params['name']

    if user_list_action is not None:
        cmd = "chgrpmem "

        if module.params['user_list_type'] is None:
            msg += "\nPlease provide the choice of members or admins type."
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

        if module.params['users_list'] is None:
            msg += "\nPlease provide the list of users to %s" % module.params['user_list_action']
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

        if module.params['user_list_type'] == 'members':
            cmd += "-m "

        if module.params['user_list_type'] == 'admins':
            cmd += "-a "

        if module.params['user_list_action'] == 'add':
            cmd += "+ "

        if module.params['user_list_action'] == 'remove':
            cmd += "- "

        cmd += module.params['users_list']
        cmd = cmd + " " + module.params['name']

        rc, stdout, stderr = module.run_command(cmd)

        if rc != 0:
            msg += "\nFailed to modify member/admin list for the group: %s" % module.params['name']
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg += "\nMember/Admin list modified for the group %s SUCCESSFULLY" % module.params['name']

    return msg


def create_group(module):
    """
    Creates the group with the attributes provided in the
    attribiutes field.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success or error message.
    """

    group_attributes = module.params['group_attributes']
    user_list_action = module.params['user_list_action']
    msg = ""

    cmd = ['mkgroup']

    cmd.append(module.params['name'])

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg += "\nFailed to create group: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg += "\nGroup is created SUCCESSFULLY: %s" % module.params['name']

    if group_attributes is not None or user_list_action is not None:
        msg_attr = modify_group(module)
        msg += msg_attr

    return msg


def remove_group(module):
    """
    Remove the user from the group.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success or error message.
    """
    cmd = ['rmgroup']

    if module.params['remove_keystore']:
        cmd.append('-p')
    cmd.append(module.params['name'])

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "Unable to remove the group: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "Group is REMOVED SUCCESSFULLY: %s" % module.params['name']

    return msg


def group_exists(module):
    """
    Checks if the specified user exists in the system or not.

    arguments:
        module      (dict): The Ansible module
    return:
        true if exists
        false otherwise
    """
    cmd = ["lsgroup"]
    cmd.append(module.params['name'])

    rc, out, err = module.run_command(cmd)

    if (rc == 0):
        return True
    else:
        return False


def main():
    """
    Main function
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['present', 'absent']),
            name=dict(type='str', required=True, aliases=['group']),
            group_attributes=dict(type='dict', default=None),
            user_list_action=dict(type='str', choices=['add', 'remove'], default=None),
            user_list_type=dict(type='str', choices=['members', 'admins'], default=None),
            users_list=dict(type='str', default=None),
            remove_keystore=dict(type='bool', default=True),
        ),
        supports_check_mode=False
    )

    msg = ""
    group_attributes = module.params['group_attributes']
    user_list_action = module.params['user_list_action']

    if module.params['state'] == 'absent':
        if group_exists(module):
            msg = remove_group(module)
        else:
            msg = "Group name is NOT FOUND : %s" % module.params['name']
            module.fail_json(msg=msg)
    if module.params['state'] == 'present':
        if not group_exists(module):
            msg = create_group(module)
        else:
            if group_attributes is None and user_list_action is None:
                msg = "Please provide the attributes to be set or action to be taken for the group."
                module.fail_json(msg=msg)
            else:
                msg = modify_group(module)

    module.exit_json(changed=True, msg=msg)


if __name__ == '__main__':
    main()
