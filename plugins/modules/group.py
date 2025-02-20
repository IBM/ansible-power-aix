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

DOCUMENTATION = """
---
author:
- AIX development Team (@pbfinley1911)
module: group
short_description: Manage presence, attributes and member of AIX groups.
description:
- It allows to create new group, to change/remove attributes and administrators or members of a
  group, and to delete an existing group.
version_added: '1.0.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorizations:
  B(aix.security.group.remove.admin,aix.security.group.remove.normal,
  aix.security.group.create.admin,aix.security.group.create.normal,aix.security.group.list)'
options:
  name:
    description: Specifies the name of the group to manage.
    type: str
    aliases: [ group ]
    required: true
  state:
    description:
    - Specifies the action to be performed.
    - C(present) specifies to create a group if it does not exist, otherwise it changes the
      attributes of the specified group.
    - C(absent) deletes an existing group. Users who are group members are not removed.

    type: str
    choices: [ present, absent ]
    required: true
  group_attributes:
    description:
    - Specifies the attributes for the group to be created or modified.
    - Can be used when I(state=present)  .
    type: dict
  user_list_action:
    description:
    - Specifies to add or remove members/admins from the group.
    - C(add) to add members or admins of the group with provided I(users_list) in group I(name)
    - C(remove) to remove members or admins of the group with provided I(users_list) from group I(name)
    - Can be used when I(state=present).
    type: str
    choices: [ add, remove ]
  user_list_type:
    description:
    - Specifies the type of user to add/remove.
    - C(members) specifies the I(user_list_action) is performed on members of the group
    - C(admins) specifies the I(user_list_action) is performed on admins of the group
    - Can be used when I(state=present).
    type: str
    choices: [ members, admins ]
  users_list:
    description:
    - Specifies a list of user to be added/removed as members/admins of the group.
    - Should be used along with I(user_list_action) and I(user_list_type) parameters.
    - Can be used when I(state=present).
    type: list
    elements: str
  remove_keystore:
    description:
    - Specifies to remove the group's keystore information while removing the goup.
    - Can be used when I(state=absent).
    type: bool
    default: yes
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
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mkgroup.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chgrpmem.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmgroup.html).
"""

EXAMPLES = r'''
- name: Add a member to a group
  ibm.power_aix.group:
    state: modify
    name: ansible
    user_list_action: 'add'
    user_list_type: 'members'
    users_list: 'test1'

- name: Remove a member from a group
  ibm.power_aix.group:
    state: modify
    name: ansible
    user_list_action: 'remove'
    user_list_type: 'members'
    users_list: 'test1'

- name: Create a group
  ibm.power_aix.group:
    state: present
    name: ansible

- name: Remove a group
  ibm.power_aix.group:
    state: absent
    name: ansible

- name: Modify group attributes
  ibm.power_aix.group:
    state: modify
    name: ansible
    group_attributes: "admin=true"
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Group: foo SUCCESSFULLY created.'
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: When the command is executed.
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

result = None


def modify_group(module):
    """
    Modify the attributes of the user.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (str): success or error message.
    """

    msg = ""

    opts = ""
    load_module_opts = None
    name = module.params['name']
    user_list_type = module.params['user_list_type']

    if module.params['group_attributes']:
        for attr, val in module.params['group_attributes'].items():
            if attr == 'load_module':
                load_module_opts = f"-R {val} "
            else:
                opts += f"{attr}={val} "
        if load_module_opts is not None:
            opts = load_module_opts + opts

        if module.params['load_module']:
            load_module_op = f" -R {module.params['load_module']} "
        cmd = f"chgroup {load_module_op} {opts} {name}"

        init_props = get_group_attributes(module)

        rc, stdout, stderr = module.run_command(cmd)

        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            # User is not in member list. (Not a problem: idempotency)
            pattern = "3004-692"
            found = re.search(pattern, stderr)

            if not found:
                result['msg'] += f"\nFailed to modify attributes for group: {name}."
                module.fail_json(**result)
            else:
                result['rc'] = 0

        if init_props != get_group_attributes(module):
            result['changed'] = True
            msg = f"\nGroup: {name} attributes SUCCESSFULLY set."
        else:
            msg = f"\nGroup: {name} attributes were not changed."
            result['changed'] = False

    if module.params['user_list_action']:
        cmd = "chgrpmem "

        load_module_opts = f" -R {module.params['load_module']} "
        cmd += load_module_opts

        if not module.params['user_list_type']:
            result['msg'] += "\nAttribute 'user_list_type' is missing."
            module.fail_json(**result)

        if not module.params['users_list']:
            result['msg'] += f"\nuser_list_type is {user_list_type} but 'users_list' is missing."
            module.fail_json(**result)

        if module.params['user_list_type'] == 'members':
            cmd += "-m "

        if module.params['user_list_type'] == 'admins':
            cmd += "-a "

        if module.params['user_list_action'] == 'add':
            cmd += "+ "

        if module.params['user_list_action'] == 'remove':
            cmd += "- "

        cmd += ",".join(module.params['users_list'])
        cmd = cmd + " " + module.params['name']

        init_props = get_group_attributes(module)
        rc, stdout, stderr = module.run_command(cmd)

        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            # 3004-641.User is not in member list. (Not a problem: idempotency)
            pattern = "3004-641"
            found = re.search(pattern, stderr)

            if not found:
                result['msg'] += f"\nFailed to modify {user_list_type} list for group: {name}."
                module.fail_json(**result)
            else:
                result['rc'] = 0

        if init_props != get_group_attributes(module):
            result['changed'] = True
            msg += f"\n {user_list_type} list for group: {name} SUCCESSFULLY modified."
        else:
            msg += f"\n {user_list_type} list for group: {name} was not modified."

    return msg


def create_group(module):
    """
    Creates the group with the attributes provided in the attributes field.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (str): success or error message.
    """

    msg = ""

    name = module.params['name']
    cmd = "mkgroup"

    load_module_opts = f" -R {module.params['load_module']} "
    cmd += load_module_opts
    if module.params['group_attributes']:
        for attr, val in module.params['group_attributes'].items():
            cmd += " " + str(attr) + "=" + str(val)

    cmd += " " + module.params['name']

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:

        result['msg'] = f"Failed to create group: {name}."
        module.fail_json(**result)
    else:
        msg = f"Group: {name} SUCCESSFULLY created."
        result['changed'] = True

    return msg


def remove_group(module):
    """
    Remove the group.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (str): success or error message.
    """

    msg = ""
    cmd = ['rmgroup']
    name = module.params['name']

    cmd = cmd + ['-R ']
    cmd = cmd + [module.params['load_module']]

    if module.params['remove_keystore']:
        cmd += ['-p']
    cmd += [module.params['name']]

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = f"Unable to remove the group: {name}."
        module.fail_json(**result)
    else:
        msg = f"Group: {name} SUCCESSFULLY removed"
    return msg


def group_exists(module):
    """
    Checks if the specified group exists in the system or not.
    arguments:
        module      (dict): The Ansible module
    return:
        true if exists
        false otherwise
    """
    cmd = ['lsgroup']

    cmd.append("-R")
    cmd.append(module.params['load_module'])

    cmd = cmd + [module.params['name']]

    rc, out, err = module.run_command(cmd)
    result['cmd'] = cmd
    result['stdout'] = out
    result['stderr'] = err

    if rc == 0:
        return True
    return False


def get_group_attributes(module):
    """
    Retrieve all group attributes
    arguments:
        module(dict): The Ansible module
    return:
        standard output of lsgroup <group name>
    """
    cmd = ['lsgroup']

    cmd.append("-R")
    cmd.append(module.params['load_module'])

    cmd = cmd + [module.params['name']]

    rc, out, err = module.run_command(cmd)

    return out


def main():
    """
    Main function
    """
    global result

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['present', 'absent', 'modify']),
            name=dict(type='str', required=True, aliases=['group']),
            group_attributes=dict(type='dict'),
            user_list_action=dict(type='str', choices=['add', 'remove']),
            user_list_type=dict(type='str', choices=['members', 'admins']),
            users_list=dict(type='list', elements='str'),
            remove_keystore=dict(type='bool', default=True),
            load_module=dict(type='str', default='files', choices=['files', 'LDAP']),
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )
    name = module.params['name']
    state = module.params['state']

    if module.params['state'] == 'absent':
        if group_exists(module):
            result['msg'] = remove_group(module)
            result['changed'] = True
        else:
            result['msg'] = f"Group name is NOT FOUND : {name}"

    elif module.params['state'] == 'present':
        if not group_exists(module):
            result['msg'] = create_group(module)
        else:
            result['msg'] = f"Group {name} already exists."

            if not module.params['group_attributes'] and not module.params['user_list_action']:
                result['msg'] = f"State is {state}. Please provide attributes or action."
            else:
                result['msg'] = modify_group(module)
    else:
        # should not happen
        result['msg'] = f"Invalid state. The state provided is not supported: {state}"
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
