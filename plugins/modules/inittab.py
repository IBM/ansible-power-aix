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
module: inittab
short_description: Manage inittab entries on AIX.
description:
    - It allows to create, change and remove entries in the B(/etc/inittab) file.
version_added: "2.9"
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorization: B(aix.system.config.inittab)'
options:
    state:
        description:
        - Specifies the action to be performed for the entry.
        - C(present) creates the entry in the /etc/inittab file.
        - C(absent) deletes an existing entry.
        - C(modify) changes an existing entry.
        type: str
        choices: [ present, absent, modify ]
        required: true
    name:
        description:
        - Specifies the name of the entry to manage.
        type: str
        aliases: [ service ]
        required: true
    runlevel:
        description:
        - Specifies the run levels in which the I(name) can be processed.
        - The format is the level number next to each other without separators, such as C('235789').
        type: str
        required: true
    action:
        description:
        - Specifies the action init will perform.
        type: str
        required: true
        choices: [
                'boot',
                'bootwait',
                'hold',
                'initdefault',
                'off',
                'once',
                'ondemand',
                'powerfail',
                'powerwait',
                'respawn',
                'sysinit',
                'wait',
            ]
    command:
        description:
        - Specifies the command to run.
        type: str
        required: true
    insertafter:
        description:
        - Specifies the name of the entry to write the new entry after.
        type: str
"""

EXAMPLES = r'''
- name: Create new entry for uprintfd
  inittab:
    state: present
    name: uprintfd
    runlevel: '23456789'
    action: 'respawn'
    command: '/usr/sbin/uprintfd'
    insertafter: 'perfstat'

- name: Change entry for uprintfd
  inittab:
    state: modify
    name: uprintfd
    runlevel: '1234567'
    action: 'respawn'
    command: '/usr/sbin/uprintfd'
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


def modify_entry(module):
    """
    Modifies the entry in the /etc/inittab file.
    arguments:
        module  (dict): The Ansible module.
    note:
        Exits with fail_json in case of error.
    return:
        msg      (srt): success message.
    """

    name = module.params['name']
    action = module.params['action']
    runlevel = module.params['runlevel']
    command = module.params['command']
    msg = ""

    cmd = 'chitab'

    new_entry = name + ":" + runlevel + ":" + action + ":" + command
    cmd = cmd + " " + new_entry

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "\nFailed to change the entry in inittab file: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "\nEntry for: %s is changed SUCCESSFULLY in inittab file" % module.params['name']

    return msg


def create_entry(module):
    """
    Creates the entry in /etc/inittab file with provided options.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success message.
    """

    msg = ""

    name = module.params['name']
    action = module.params['action']
    runlevel = module.params['runlevel']
    command = module.params['command']
    identifier = module.params['insertafter']

    cmd = 'mkitab'

    if identifier is not None:
        ident_opts = "-i " + identifier
        cmd = cmd + " " + ident_opts

    new_entry = name + ":" + runlevel + ":" + action + ":" + command
    cmd = cmd + " " + new_entry

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg += "\nFailed to create entry in inittab file: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg += "\nEntry is created in inittab file SUCCESSFULLY: %s" % module.params['name']

    return msg


def remove_entry(module):
    """
    Removes the entry in /etc/inittab file.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success message.
    """
    cmd = ['rmitab']
    cmd.append(module.params['name'])

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "Unable to remove the entry from inittab file: %s" % module.params['name']
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "Entry is REMOVED SUCCESSFULLY from inittab file: %s" % module.params['name']

    return msg


def entry_exists(module):
    """
    Checks if the specific entry exists in the /etc/inittab file or not.
    arguments:
        module      (dict): The Ansible module
    return:
        true if exists
        false otherwise
    """
    cmd = ["lsitab"]
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
            state=dict(type='str', required=True, choices=['present', 'absent', 'modify']),
            name=dict(type='str', required=True, aliases=['service']),
            runlevel=dict(type='str', required=True),
            action=dict(type='str', required=True, choices=[
                'boot',
                'bootwait',
                'hold',
                'initdefault',
                'off',
                'once',
                'ondemand',
                'powerfail',
                'powerwait',
                'respawn',
                'sysinit',
                'wait',
            ]),
            command=dict(type='str', required=True),
            insertafter=dict(type='str'),
        ),
        supports_check_mode=False
    )

    msg = ""
    changed = False

    if module.params['state'] == 'absent':
        if entry_exists(module):
            msg = remove_entry(module)
            changed = True
        else:
            msg = "Entry is NOT FOUND in inittab file: %s" % module.params['name']
    elif module.params['state'] == 'present':
        if not entry_exists(module):
            msg = create_entry(module)
            changed = True
        else:
            msg = "Entry %s already exists. If you want to change the entry, please use modify state." % module.params['name']
    elif module.params['state'] == 'modify':
        if entry_exists(module):
            msg = modify_entry(module)
            changed = True
        else:
            msg = "Entry does NOT exists in inittab file: %s" % module.params['name']
    else:
        msg = "Invalid state. The state provided is not supported: %s" % module.params['state']

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
