#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
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
version_added: "2.9"
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
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
    - C(present) creates a new group. When the group already exists, use I(sate=modify) to change
      its attributes.
    - C(absent) deletes an existing group. Users who are group members are not removed.
    - C(modify) changes specified value of attributes of an existing group. When the group does not
      exist, use I(sate=present).
    type: str
    choices: [ present, absent, modify ]
    required: true
  group_attributes:
    description:
    - Specifies the attributes for the group to be created or modified.
    - Can be used when I(state=present) or I(state=modify).
    type: dict
  user_list_action:
    description:
    - Specifies to add or remove members/admins from the group.
    - C(add) to add members or admins of the group with provided I(users_list) in group I(name)
    - C(remove) to remove members or admins of the group with provided I(users_list) from group I(name)
    - Can be used when I(state=present) or I(state=modify).
    type: str
    choices: [ add, remove ]
  user_list_type:
    description:
    - Specifies the type of user to add/remove.
    - C(members) specifies the I(user_list_action) is performed on members of the group
    - C(admins) specifies the I(user_list_action) is performed on admins of the group
    - Can be used when I(state=present) or I(state=modify).
    type: str
    choices: [ members, admins ]
  users_list:
    description:
    - Specifies a list of user to be added/removed as members/admins of the group.
    - Should be used along with I(user_list_action) and I(user_list_type) parameters.
    - Can be used when I(state=present) or I(state=modify).
    type: list
    elements: str
  remove_keystore:
    description:
    - Specifies to remove the group's keystore information while removing the goup.
    - Can be used when I(state=absent).
    type: bool
    default: yes
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mkgroup.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chgrpmem.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmgroup.html).
"""

EXAMPLES = r'''
- name: Change group ansible
  ibm.power_aix.group:
    state: present
    name: ansible
    user_list_action: 'add'
    user_list_type: 'member'
    users_list: 'test1'
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


from ansible.module_utils.basic import AnsibleModule

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
    global result
    msg = ""

    opts = ""
    load_module_opts = None

    if module.params['group_attributes']:
        for attr, val in module.params['group_attributes'].items():
            if attr == 'load_module':
                load_module_opts = "-R %s " % val
            else:
                opts += "%s=%s " % (attr, val)
        if load_module_opts is not None:
            opts = load_module_opts + opts
        cmd = "chgroup %s %s" % (opts, module.params['name'])
        rc, stdout, stderr = module.run_command(cmd)

        result['cmd'] = ' '.join(cmd)
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] += "\nFailed to modify attributes for group: %s." % module.params['name']
            module.fail_json(**result)
        else:
            msg = "\nGroup: %s attributes SUCCESSFULLY set." % module.params['name']

    if module.params['user_list_action']:
        cmd = "chgrpmem "

        if not module.params['user_list_type']:
            result['msg'] += "\nuser_list_type is '%s' but 'user_list_type' is missing." % module.params['user_list_type']
            module.fail_json(**result)

        if not module.params['users_list']:
            result['msg'] += "\nuser_list_type is '%s' but 'users_list' is missing." % module.params['user_list_type']
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

        rc, stdout, stderr = module.run_command(cmd)

        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] += "\nFailed to modify %s list for group: %s." % (module.params['user_list_type'], module.params['name'])
            module.fail_json(**result)
        else:
            msg += "\n%s list for group: %s SUCCESSFULLY modified." % (module.params['user_list_type'], module.params['name'])

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
    global result
    msg = ""

    cmd = ['mkgroup']
    cmd += [module.params['name']]

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = "Failed to create group: %s." % module.params['name']
        module.fail_json(**result)
    else:
        msg = "Group: %s SUCCESSFULLY created." % module.params['name']

    if module.params['group_attributes'] or module.params['user_list_action']:
        result['msg'] += modify_group(module)

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
    global result
    msg = ""
    cmd = ['rmgroup']

    if module.params['remove_keystore']:
        cmd += ['-p']
    cmd += [module.params['name']]

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = "Unable to remove the group: %s." % module.params['name']
        module.fail_json(**result)
    else:
        msg = "Group: %s SUCCESSFULLY removed" % module.params['name']

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
    cmd = ["lsgroup"]
    cmd += [module.params['name']]

    rc, out, err = module.run_command(cmd)

    if rc == 0:
        return True
    else:
        return False


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

    if module.params['state'] == 'absent':
        if group_exists(module):
            result['msg'] = remove_group(module)
            result['changed'] = True
        else:
            result['msg'] = "Group name is NOT FOUND : %s" % module.params['name']

    elif module.params['state'] == 'present':
        if not group_exists(module):
            result['msg'] = create_group(module)
            result['changed'] = True
        else:
            result['msg'] = "Group %s already exists." % module.params['name']

    elif module.params['state'] == 'modify':
        if not module.params['group_attributes'] and not module.params['user_list_action']:
            result['msg'] = "State is '%s'. Please provide attributes to set or action to be taken for the group." % module.params['state']
        else:
            if group_exists(module):
                result['msg'] = modify_group(module)
                result['changed'] = True
            else:
                result['msg'] = "No group found in the system to modify the attributes: %s" % module.params['name']
                module.fail_json(**result)
    else:
        # should not happen
        result['msg'] = "Invalid state. The state provided is not supported: %s" % module.params['state']
        module.fail_json(**result)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
