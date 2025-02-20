#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@nitismis)
module: tunfile_mgmt
short_description: Save/Restore/Validate/Modify tunables configuration file for various components on AIX.
description:
- This module facilitates the save/restore/validate/modify action to tunables configuration file with provided inputs.
version_added: '1.5.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- Root user is required.
options:
  action:
    description:
    - Specifies the action to be performed for tunables in the system.
    - C(save) saves the tunables values in provided I(filename).
    - C(restore) restores the file I(filename) in current context or boot context as mention by I(make_nextboot).
    - C(modify) modifies the value of parameters I(tunables_with_values) for I(components) or
      or sets all tunables to default I(set_default) for I(components)
    - C(validate) validates the file to be used for other actions in context I(validation_type).
    type: str
    choices: [ save, restore, modify, validate ]
    required: true
  component_to_set_dflt:
    description:
    - Specifies the component name.
    - supported values in the list are schedo, vmo, ioo, no, nfso, raso and asoo.
    - It must be unique, you cannot use the ALL or default keywords in the component.
    type: list
    elements: str
  filename:
    description:
    - Specifies the file name for the I(action).
    - If the name not starts with '/' the file will be created in /etc/tunables.
    - If filename already exists, the existing file is overwritten
    type: str
    required: True
  tunables_with_values:
    description:
    - In the format of dictionary of dictionary (nested dict)
    - Specifies the component(s), tunable(s) and their value(s) whose modification is required.
    - supported keys in the outer dict are schedo, vmo, ioo, no, nfso, raso and asoo.
    - Cannot be used when I(set_default=True).
    type: dict
  make_nextboot:
    description:
    - Specifies the boot context as current or boot context during I(action=restore)
    - If changes includes bosboot/reboot tunables it is prefered to be used as true..
    type: bool
    default: False
  validation_type:
    description:
    - Specifies the type of validation for the I(filename).
    type: str
    choices: [current, reboot, both]
    default: current
  save_all_tunables:
    description:
    - Specifies that all tunables should be saved or only those that are having non default values currently
      for I(action=save)
    - If changes includes bosboot/reboot tunables it is prefered to be used as true..
    type: bool
    default: True
  set_default:
    description:
    - Specifies that all tunables should be modified to their default value for given I(component)
    - Shoul not be used if I(tunables_with_values) is used.
    type: bool
    default: False
'''

EXAMPLES = r'''
- name: "Save all tunables to a file"
  tunfile_mgmt:
  action: save
  filename: /tunfile_mgmt_test
  register: tunfile_result
- debug: var=tunfile_result

- name: "Validate a tunable file in current context"
  tunfile_mgmt:
  action: validate
  filename: /tunfile_mgmt_test
  register: tunfile_result
- debug: var=tunfile_result

- name: "Modify all tunables of given component as default to a file"
  tunfile_mgmt:
  action: modify
  filename: /tunfile_mgmt_test
  set_default: true
  component_to_set_dflt: schedo
  register: tunfile_result
- debug: var=tunfile_result

- name: "Modify multiple tunables for multiple components"
  tunfile_mgmt:
  action: modify
  filename: /tunfile_mgmt_test
  tunables_with_values:
    vmo:
    ame_mpsize_support: 1
    ame_min_ucpool_size: 10
    aso:
    abc: 1
    xyz: 2
  register: tunfile_result
- debug: var=tunfile_result
'''

RETURN = r'''

msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'All tunables have been saved SUCCESSFULLY in file: tunfile_mgmt_test'
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: always.
    type: str
stderr:
    description: The standard error.
    returned: always.
    type: str
cmd:
    description: Command executed.
    returned: always
    type: str
'''

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

results = {}


def tunchange(module):
    '''
    Modifies the file according to the component and parameters provided.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        nothing, modifies the provided file
    '''

    filename = module.params['filename']
    tunables_with_values = module.params['tunables_with_values']
    set_default = module.params['set_default']
    component_to_set_dflt = module.params['component_to_set_dflt']

    # if user has not provided file name return fail json.
    if filename is None:
        msg_failed = '\nPlease provide file name.'
        module.fail_json(msg=msg_failed)

    if tunables_with_values is None and component_to_set_dflt is None:
        msg_failed = '\nPlease provide tunable_with_values, component_to_set_dflt or both.'
        module.fail_json(msg=msg_failed)

    # iterate through tunables_with_values to get stanzas and parameters
    # and form the tunchange command for multiple commands.
    if tunables_with_values:
        for stanza, tunables in tunables_with_values.items():
            if stanza == "false":
                stanza = "no"
            cmd = 'tunchange -f ' + filename + ' -t ' + stanza
            for tunable, value in tunables.items():
                cmd += ' -o ' + tunable + '=' + str(value) + ' '
            rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)
            results['stderr' + stanza] = std_err
            results['stdout' + stanza] = std_out
            results['rc' + stanza] = rc
            results['cmd' + stanza] = cmd
            if rc != 0:
                # In case command returns non zero return code, fail case
                results['msg' + stanza] = f"\nFailed to modify file for {stanza} component."
                module.fail_json(**results)
            else:
                results['msg' + stanza] = f'\nFile is modified SUCCESSFULLY for {stanza}.\n'
                results['msg' + stanza] += std_out

    if set_default:
        for stanza in component_to_set_dflt:
            cmd = 'tunchange -f ' + filename + ' -t ' + stanza + ' -D '
            rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)
            results['stderr' + stanza] = std_err
            results['stdout' + stanza] = std_out
            results['rc' + stanza] = rc
            results['cmd' + stanza] = cmd
            if rc != 0:
                # In case command returns non zero return code, fail case
                results['msg' + stanza] = f"\nFailed to modify file: {stanza}"
                module.fail_json(**results)
            else:
                results['msg' + stanza] = f'\nFile is modified SUCCESSFULLY: {stanza}\n'
                results['msg' + stanza] += std_out


def tuncheck(module):
    '''
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        nothing, resets the tunables to default values
    '''

    filename = module.params['filename']
    validation_type = module.params['validation_type']
    cmd = 'tuncheck '

    if validation_type == 'reboot':
        cmd += '-r '
    elif validation_type == 'both':
        cmd += '-p '

    # include file name in the command
    cmd += '-f ' + filename

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    results['rc'] = rc
    results['cmd'] = cmd
    results['stdout'] = std_out
    results['stderr'] = std_err

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = f"File {filename} is INVALID. Check the message for more details."
        module.fail_json(**results)
    else:
        results['msg'] = f"File provided is VALID: {filename}"


def tunrestore(module):
    '''
    Handles the restore action through tunrestore command

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        nothing, restrores the tunables in system through provided file name
    '''

    filename = module.params['filename']
    make_nextboot = module.params['make_nextboot']
    cmd = 'tunrestore '

    if make_nextboot:
        cmd += '-r '

    # include file name in the command
    cmd += '-f ' + filename

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    results['stderr'] = std_err
    results['stdout'] = std_out
    results['rc'] = rc
    results['cmd'] = cmd

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = f"\nFailed to restore tunable parameter from file: {filename}"
        module.fail_json(**results)
    else:
        results['msg'] = f'\nTunables have been restored SUCCESSFULLY from file: {filename}'
        results['msg'] += std_out

    if make_nextboot:
        results['Reboot_required'] = 'True'
        results['Bosboot_required'] = 'True'
        results['msg'] += '\nSome tunables require bosboot/reboot for the changes to take place.'
        results['msg'] += '\nPlease perform bosboot and reboot.'


def tunsave(module):
    '''
    Handles the save action through tunsave command

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Message for successful command.
    '''

    filename = module.params['filename']
    save_all_tunables = module.params['save_all_tunables']

    # if user has not provided file name return fail json.
    if filename is None:
        msg_failed = '\nPlease provide file name.'
        module.fail_json(msg=msg_failed)

    # form the tunsave command
    if save_all_tunables:
        cmd = 'tunsave -A -F ' + filename
    else:
        cmd = 'tunsave -F ' + filename

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    results['stderr'] = std_err
    results['stdout'] = std_out
    results['rc'] = rc
    results['cmd'] = cmd

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = f"Failed to save tunable parameters in file: {filename}"
        module.fail_json(**results)
    else:
        results['msg'] = f"\nAll tunables have been saved SUCCESSFULLY in file: {filename} \n"
        results['msg'] += std_out


def main():
    '''
    Main function
    '''
    global results
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True, choices=['save', 'restore',
                                                            'validate', 'modify']),
            filename=dict(type='str', required=True),
            tunables_with_values=dict(type='dict', default=None),
            make_nextboot=dict(type='bool', default='False'),
            validation_type=dict(type='str', default='current', choices=['current',
                                                                         'reboot', 'both']),
            save_all_tunables=dict(type='bool', default=True),
            set_default=dict(type='bool', default='False'),
            component_to_set_dflt=dict(type='list', elements='str', default=None)
        ),
        supports_check_mode=False
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    action = module.params['action']
    tunables_with_values = module.params['tunables_with_values']
    valid_components = ["schedo", "vmo", "ioo", "no", "nfso", "raso", "asoo"]
    invalid_components = ""

    # check for invalid stanza/components
    if tunables_with_values:
        for stanza in tunables_with_values:
            if stanza == "false":
                stanza = "no"
            if stanza not in valid_components:
                invalid_components += stanza + ', '

    if invalid_components:
        results['msg'] = f"Invalid components are found: {invalid_components}"
        module.fail_json(**results)

    if action == 'save':
        tunsave(module)
    elif action == 'restore':
        tunrestore(module)
    elif action == 'modify':
        tunchange(module)
    elif action == 'validate':
        tuncheck(module)

    # changed is False in case of show action.
    if action != 'save':
        results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
