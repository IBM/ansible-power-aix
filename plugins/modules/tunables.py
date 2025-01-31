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
module: tunables
short_description: Modify/Reset/Show tunables for various components on AIX.
description:
- This module facilitates in the modification/reset/show of tunable parameter(s) with provided inputs.
version_added: '1.5.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- Root user is required.
options:
  action:
    description:
    - Specifies the action to be performed for tunables of a component.
    - C(show) shows information of tunables specified by I(component) and optional I(tunable_params).
    - C(modify) modifies values of tunables specified by I(component) and I(tunable_params).
    - C(reset) resets values of tunables specified by I(component) and optional I(tunable_params).
    type: str
    choices: [ show, modify, reset ]
    required: true
  component:
    description:
    - Specifies the component name.
    - It must be unique, you cannot use the ALL or default keywords in the component.
    type: str
    choices: [ 'vmo', 'ioo', 'schedo', 'no', 'raso', 'nfso', 'asoo']
    required: true
  change_type:
    description:
    - Specifies the type of changes for the tunables.
    - For details on valid user attributes, please refers to IBM documentation.
    - For I(action=reset), C(change_type=current) resets the current values of tunable/s specified by I(component) and
      I(tunable_params) to its default value.
    - For I(action=modify), C(change_type=current) modifies the current values of tunable/s specified by I(component) and
      I(tunable_params_with_value).
    - For I(action=reset), C(change_type=reboot) resets the reboot values of tunable/s specified by I(component) and
      I(tunable_params) to its default value.
    - For I(action=modify), C(change_type=reboot) modifies the reboot values of a tunable/s specified by I(component) and
      I(tunable_params_with_value).
    - For I(action=reset), C(change_type=both) resets the current and reboot values of tunable/s specified by I(component) and
      I(tunable_params) to its default value.
    - For I(action=modify), C(change_type=both) modifies the current and reboot values of tunable/s specified by I(component) and
      I(tunable_params_with_value).
    type: str
    choices: [current, reboot, both]
    default: current
  bosboot_tunables:
    description:
    - Specifies whether the provided I(tunable_params) or I(tunable_params_with_value) are bosboot type or not.
    - Cannot be used when I(change_type=both).
    type: bool
    default: False
  tunable_params:
    description:
    - Specifies the tunables in list format whose details need to be displayed or reset.
    - Can be used when I(action=show or action=reset).
    - Cannot be used with I(action=modify).
    type: list
    elements: str
  tunable_params_with_value:
    description:
    - Specifies the tunable(s) and their value(s) whose modification is required.
    - Cannot be used when I(action=show or action=reset).
    - Can be used with I(action=modify).
    type: dict
  restricted_tunables:
    description:
    - forces the display, modification, or resetting of restricted tunables.
    type: bool
    default: False
'''

EXAMPLES = r'''
- name: "Modify vmo tunable parameters"
  ibm.power_aix.tunables:
    action: modify
    component: vmo
    tunable_params_with_value:
      lgpg_regions: 10
      lgpg_size: 16777216

- name: "Modify vmo tunable parameters of type bosboot"
  ibm.power_aix.tunables:
    action: modify
    component: vmo
    bosboot_tunables: true
    tunable_params_with_value:
      ame_mpsize_support: 1

- name: "Display information of all dynamic tunable parameters"
  ibm.power_aix.tunables:
    action: show
    component: vmo

- name: "Display information of all tunable parameters including restricted"
  ibm.power_aix.tunables:
    action: show
    component: vmo
    restricted_tunables: true

- name: "Display information of given tunable parameters"
  ibm.power_aix.tunables:
    action: show
    component: vmo
    tunable_params:
      - lgpg_regions
      - lgpg_size

- name: "show reboot value of lgpg_regions tunable"
  ibm.power_aix.tunables:
    action: show
    component: vmo
  register: output
- debug: var=output.tunables_details.lgpg_regions.reboot_value

- name: "Modify dynamic tunables/restricted dynamic tunables"
  # this will change the current value of given dynamic tunables and does NOT require any bosboot or reboot
  ibm.power_aix.tunables:
    action: modify
    component: vmo
    restricted_tunables: true # in case of restricted tunables otherwise default is false
    tunable_params_with_value:
      lgpg_regions: 10   # dynamic tunable
      lgpg_size: 16777216 # dynamic tunables
      enhanced_affinity_balance: 1000 # restricted dynamic tunable
  register: result

- name: "Modify bosboot tunables/ restricted bosboot tunables"
  # this will only change the REBOOT VALUE and needs bosboot and reboot.
  ibm.power_aix.tunables:
    action: modify
    component: vmo
    bosboot_tunables: true # mandatory
    restricted_tunables: true # if restricted tunable to be changed
    tunable_params_with_value:
      kernel_heap_psize: 16777216 # bosboot tunable
      batch_tlb: 0 # restricted bosboot tunables
  register: result
  # check for:
  # result.bosboot_required == True
  # result.reboot_required == True

- name: "Modify combination of bosboot and dynamic tunables"
  # this will only change the REBOOT VALUE for both bosboot and dynamic tunables and needs bosboot and reboot.
  # so, if bosboot and dynamic tunables are used together, only reboot value will get changed and needs bosboot and reboot
  # to make changes take into effect.
  ibm.power_aix.tunables:
    action: modify
    component: vmo
    restricted_tunables: true # because of restricted tunables otherwise default is false
    bosboot_tunables: true # because of bosboot tunables otherwise default is false
    # if restricted tunable to be changed also then restricted_tunable: True
    tunable_params_with_value:
      lgpg_regions: 10   # dynamic tunable
      lgpg_size: 16777216 # dynamic tunables
      kernel_heap_psize: 16777216 # bosboot tunable

  register: result
  # check for:
  # result.bosboot_required == True
  # result.reboot_required == True

- name: "Reset bosboot tunables/ restricted bosboot tunables"
  # this will only change the REBOOT VALUE and needs bosboot and reboot.
  # example of one restricted and one non restricted bosboot tunable
  ibm.power_aix.tunables:
    action: reset
    component: vmo
    restricted_tunables: true # because of restricted tunables otherwise default is false
    bosboot_tunables: true # because of bosboot tunables otherwise default is false
    tunable_params: ['kernel_heap_psize', 'batch_tlb']

  register: result
  # check for:
  # result.bosboot_required == True
  # result.reboot_required == True

- name: "Reset combination of bosboot and dynamic tunables"
  # this will only reset the REBOOT VALUE for both bosboot and dynamic tunables and needs bosboot and reboot.
  # so, if bosboot and dynamic tunables are used together, only reboot value will get reset and needs bosboot and reboot.
  ibm.power_aix.tunables:
    action: modify
    component: vmo
    restricted_tunables: true # because of restricted tunables otherwise default is false
    bosboot_tunables: true # # because of bosboot tunables otherwise default is false
    tunable_params: ['kernel_heap_psize', 'lgpg_regions', 'kernel_heap_psize', 'enhanced_affinity_balance']

  register: result
  # check for:
  # result.bosboot_required == True
  # result.reboot_required == True
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Following tunables have been reset SUCCESSFULLY: lgpg_size lgpg_regions'
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
tunables_details:
    description: Dictionary output with the tunables detailed information.
    returned: If I(action=show).
    type: dict
    sample:
        "tunables_details": {
            "lgpg_regions": {
                "reboot_value": "0",
                "current_value": "0",
                "default": "0",
                "dependencies": "lgpg_size ",
                "maximum_value": "9223372036854775807",
                "minimum_value": "0",
                "type": "Dynamic: can be freely changed",
                "unit": ""
            }
        }
'''

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

results = {}
tunables_dict = {}


def create_tunables_dict(module):
    '''
    Utility function to create tunables dictionary with values

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        creates a dictionary with all tunables and their values
    '''

    component = module.params['component']
    global tunables_dict
    cmd = component + ' -F -x'

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = "Failed to get tunables existing values for validation."
        results['rc'] = rc
        results['cmd'] = cmd
        results['stderr'] = std_err
        module.fail_json(**results)
    else:
        # Convert the comma separated output into python dictionary for displaying full details
        tunables_dict = convert_to_dict(std_out)


def get_valid_tunables(module):
    '''
    Utility function to check validity of new values provided

    arguments:
        module  (dict): The Ansible module

    return:
        dictionary with valid tunables value pair
    '''
    # logic for creating updated dictionary
    change_type = module.params['change_type']
    new_dict = module.params['tunable_params_with_value']
    bosboot_tunables = module.params['bosboot_tunables']
    valid_tunables = {}
    unchanged_tunables = ''

    if change_type == 'current':
        for key, value in new_dict.items():
            current_val = tunables_dict[key]['current_value']
            if 'n/a' in current_val or int(current_val) != int(value):
                valid_tunables[key] = value
            else:
                unchanged_tunables += key + ' '
    elif change_type == 'reboot' or bosboot_tunables:
        for key, value in new_dict.items():
            reboot_val = tunables_dict[key]['reboot_value']
            if 'n/a' in reboot_val or int(reboot_val) != int(value):
                valid_tunables[key] = value
            else:
                unchanged_tunables += key + ' '
    elif change_type == 'both':
        for key, value in new_dict.items():
            current_val = tunables_dict[key]['current_value']
            reboot_val = tunables_dict[key]['reboot_value']
            if ('n/a' in current_val or int(current_val) != int(value)) or ('n/a' in reboot_val or int(reboot_val) != int(value)):
                valid_tunables[key] = value
            else:
                unchanged_tunables += key + ' '

    if unchanged_tunables:
        results["unchanged_tunables"] = "New value of some tunables are same as existing value\n"
        results["unchanged_tunables"] += f"These tunables are not modified: { unchanged_tunables }"

    return valid_tunables


def convert_to_dict(tunable_info):
    '''
    Utility function to convert comma separated tunables values into dictionary

    arguments:
        tunable_info: String
    return:
        Python dictionary
    '''

    # split the comma-separated input string by \n and create a list
    tunables = tunable_info.split("\n")
    display_dict = {}
    restricted_flag = False

    # Remove all empty list items from list
    for tunable in tunables:
        if tunable == '':
            tunables.remove(tunable)

    # form dictionary for each tunable parameters and include in result dictionary
    for tunable in tunables:
        form_tunables_value = tunable.split(',')
        tunable_value = {}
        if form_tunables_value[0] == '##Restricted tunables':
            restricted_flag = True
            continue
        if len(form_tunables_value) == 9:
            if form_tunables_value[8] != '':
                tunable_value['dependencies'] = form_tunables_value[8]
        if restricted_flag:
            # To specify the restricted tunables in dictionary
            tunable_value['note'] = 'This is a RESTRICTED tunable'
        tunable_value['current_value'] = form_tunables_value[1]
        tunable_value['default_value'] = form_tunables_value[2]
        tunable_value['reboot_value'] = form_tunables_value[3]
        tunable_value['minimum_value'] = form_tunables_value[4]
        tunable_value['maximum_value'] = form_tunables_value[5]
        tunable_value['unit'] = form_tunables_value[6]
        tunable_value['type'] = form_tunables_value[7]
        display_dict[form_tunables_value[0]] = tunable_value

        # Detail statement for tunable types
        # Static
        if tunable_value['type'] == 'S':
            tunable_value['type'] = 'Static: cannot be changed'
        # Dynamic
        elif tunable_value['type'] == 'D':
            tunable_value['type'] = 'Dynamic: can be freely changed'
        # Bosboot
        elif tunable_value['type'] == 'B':
            tunable_value['type'] = 'Bosboot: can only be changed using bosboot and reboot'
        # Reboot
        elif tunable_value['type'] == 'R':
            tunable_value['type'] = 'Reboot: can only be changed during reboot'
        # Connect
        elif tunable_value['type'] == 'C':
            tunable_value['type'] = 'Connect: changes only effective for future socket connections'
        # Mount
        elif tunable_value['type'] == 'M':
            tunable_value['type'] = 'Mount: changes are only effective for future mountings'
        # Incremental
        elif tunable_value['type'] == 'I':
            tunable_value['type'] = 'Incremental: can only be incremented'
        # deprecated
        elif tunable_value['type'] == 'd':
            tunable_value['type'] = 'deprecated: deprecated and cannot be changed'

    return display_dict


def show(module):
    '''
    Handles the show action

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        updated global results dictionary.
    '''
    tunable_params = module.params['tunable_params']
    restricted_tunables = module.params['restricted_tunables']
    component = module.params['component']
    tunables_to_show = ''
    cmd = ''

    # according to the component form the initial command
    cmd += component + ' '

    # Force display of the restricted tunable parameters
    if restricted_tunables:
        cmd += '-F '

    # if-else block to determine that command includes ALL parameters or specific tunable parameters
    if tunable_params is not None:
        for tunables in tunable_params:
            cmd += '-x ' + tunables + ' '
            tunables_to_show += tunables
    else:
        cmd += '-x'

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    results['rc'] = rc
    results['cmd'] = cmd
    results['stderr'] = std_err

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = f"Failed to display values for tunables: { tunables_to_show }"
        module.fail_json(**results)
    else:
        # Convert the comma separated output into python dictionary for displaying full details
        results['msg'] = "Task has been SUCCESSFULLY executed."
        results['tunables_details'] = convert_to_dict(std_out)


def reset(module):
    '''
    Handles the reset action

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Updated global results dictionary
    '''

    component = module.params['component']
    tunable_params = module.params['tunable_params']
    bosboot_tunables = module.params['bosboot_tunables']
    change_type = module.params['change_type']
    restricted_tunables = module.params['restricted_tunables']
    changed_tunables = ''
    cmd = ''

    # use of -r and -p together is prohibited. Reason explained in the message.
    if change_type == 'both' and bosboot_tunables:
        msg_failed = "\nThe combination of change_type=both and bosboot_tunables=True is invalid."
        msg_failed += "\nREASON: The current value of Reboot and Bosboot tunables can't be changed."
        module.fail_json(msg=msg_failed)

    # take the user consent about modifying restricted tunables
    if restricted_tunables:
        cmd_echo = '{ echo "yes"; echo "no"; } | '
    else:
        cmd_echo = '{ echo "no"; echo "no"; } |'

    cmd += cmd_echo

    # according to the component, choose the initial command
    # yes command is included in pipe as input to prompt for restricted tunables. no otherwise
    # according to the component form the initial command
    cmd += component + ' '

    # code block to include bosboot/reboot type parameters
    # this also suppresses the prompt for bosboot after resetting values.
    if bosboot_tunables or change_type == 'reboot':
        cmd += '-r '

    live_update = getOSlevel(module)
    if live_update and component in ['vmo', 'no']:
        valid_live_update_tunables = validate_live_update(module, tunable_params)
        if valid_live_update_tunables:
            if change_type != "reboot":
                results['msg'] = "In AIX 7.3, if you want to change tunables which support"
                results['msg'] += "live update flag, -K, then provide change_type as reboot."
                module.fail_json(**results)
            else:
                cmd += '-K '

    # -p when used in combination with -o, -d or -D, makes changes apply to both current and
    # reboot values, that is, turns on the updating of the /etc/tunables/nextboot file in addition
    # to the updating of the current value.
    if change_type == 'both':
        cmd += '-p '

    # flags to reset SPECIFIC tunables to defaults
    if tunable_params is not None:
        for tunables in tunable_params:
            cmd += '-d ' + tunables + ' '
            changed_tunables += tunables + ' '

    # flag to reset ALL tunables to defaults
    else:
        cmd += '-D '

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    results['stderr'] = std_err
    results['stdout'] = std_out
    results['rc'] = rc
    results['cmd'] = cmd

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = f"\nFailed to reset tunable parameter for component: { component }"
        module.fail_json(**results)
    else:
        if tunable_params is not None:
            results['msg'] = f'Tunables have been reset SUCCESSFULLY: { changed_tunables } \n'
        else:
            if bosboot_tunables:
                results['msg'] = 'Tunables have been reset SUCCESSFULLY for nextboot.\n'
                results['msg'] += 'Perform bosboot and reboot for the changes to take effect.'
        results['msg'] += std_out


def getOSlevel(module):
    '''
    Checks if target node is AIX v7.3

    arguments:
        module (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        True in case AIX is version 7.3
    '''

    cmd = 'oslevel -s'
    rc, stdout, stderr = module.run_command(cmd)

    if rc == 0:
        oslevel = stdout.split("-")
        if oslevel[0] == "7300":
            return True
        else:
            return False
    else:
        module.fail_json(msg=stderr)


def modify(module):
    '''
    Handles the modify action

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        Message for successful command along with display standard output
    '''

    component = module.params['component']
    bosboot_tunables = module.params['bosboot_tunables']
    change_type = module.params['change_type']
    restricted_tunables = module.params['restricted_tunables']
    tunable_params_with_value = module.params['tunable_params_with_value']
    parameters = ''
    changed_tunables = ''
    cmd = ''

    # if user has not provided tunables and new values return fail json.
    if tunable_params_with_value is None:
        msg_failed = '\nPlease provide tunable parameter name and new values for modification'
        module.fail_json(msg=msg_failed)

    # First create a dictionary with all the current values.
    create_tunables_dict(module)

    # get an updated dictionary of tunables which needs to be changed.
    tunable_params_with_value = get_valid_tunables(module)

    # if updated new dictionary is None, means all values provided are same as in system. Exit.
    if not tunable_params_with_value:
        msg_exit = "All new values provided is same as existing values. No changes have been made."
        module.exit_json(msg=msg_exit, changed=False)

    # use of -r and -p together is prohibited. Reason explained in the message.
    if change_type == 'both' and bosboot_tunables:
        msg_failed = "\nThe combination of change_type=both and bosboot_tunables=True is invalid."
        msg_failed += "\nREASON: The current value of Reboot and Bosboot tunables can't be changed."
        module.fail_json(msg=msg_failed)

    # take the user consent about modifying restricted tunables
    # take the user consent about modifying restricted tunables
    if restricted_tunables:
        cmd_echo = '{ echo "yes"; echo "no"; } | '
    else:
        cmd_echo = '{ echo "no"; echo "no"; } |'

    cmd += cmd_echo

    # according to the component, choose the initial command
    # yes command is included in pipe as input to prompt for restricted tunables. no otherwise
    # according to the component form the initial command
    cmd += component + ' '

    # code block to include bosboot/reboot type parameters
    # this also suppresses the prompt for bosboot after resetting values.
    if bosboot_tunables:
        cmd += '-r '

    # -p when used in combination with -o, -d or -D, makes changes apply to both
    # current and reboot values, that is, turns on the updating of the /etc/tunables/nextboot
    # file in addition to the updating of the current value.
    if change_type == 'both':
        cmd += '-p '

    # because tunables are not of type bosboot, system will not prompt for bosboot
    # so, dont need to suppress it. In this case reboot values of other tunables will be changed.
    if not bosboot_tunables and change_type == 'reboot':
        cmd += '-r '

    live_update = getOSlevel(module)
    if live_update and component in ['vmo', 'no']:
        to_be_validated = []
        for params in tunable_params_with_value.keys():
            to_be_validated.append(params)
        valid_live_update_tunables = validate_live_update(module, to_be_validated)
        if valid_live_update_tunables:
            if change_type != "reboot":
                results['msg'] = "In AIX 7.3, if you want to change tunables which support"
                results['msg'] += "live update flag, -K, then provide change_type as reboot."
                module.fail_json(**results)
            else:
                cmd += '-K '

    # include the tunables to be modified and their new values in command
    for tunable, value in tunable_params_with_value.items():
        parameters += '-o ' + tunable + '=' + str(value) + ' '
        changed_tunables += tunable + ' '
    cmd += parameters

    rc, std_out, std_err = module.run_command(cmd, use_unsafe_shell=True)

    results['stderr'] = std_err
    results['stdout'] = std_out
    results['rc'] = rc
    results['cmd'] = cmd

    if rc != 0:
        # In case command returns non zero return code, fail case
        results['msg'] = f"Failed to set new values to tunables for component: { component }"
        module.fail_json(**results)
    else:
        results['msg'] = f"\nTunables have been changed SUCCESSFULLY: { changed_tunables } \n"
        results['msg'] += std_out
        if bosboot_tunables:
            results['msg'] += "\n To make the changes take effect, bosboot and reboot is required"
            results['bosboot_required'] = True
            results['reboot_required'] = True


def validate_live_update(module, to_be_validated):
    '''
    Checks that all tunables support -K option in AIX 7.3

    arguments:
        module: The ansible module
        tunable_params_with_value  (dict): Tunable parameters and values
    note:
        Exits with fail_json in case of both supported and non supported tunables are present
    return:
        True if all tunables are -K supported
    '''

    contain_supported_tunables = False
    contain_non_supported_tunables = False

    supported_tunables = ["ame_cpus_per_pool", "kernel_heap_size", "msem_nlocks",
                          "num_locks_per_semid", "vmm_klock_mode", "timer_wheel_tick",
                          "extendednetstats", "lo_perf", "ipqmaxlen", "arptab_bsiz",
                          "arptab_nb", "tcp_inpcb_hashtab_siz", "udp_inpcb_hashtab_siz",
                          "use_sndbufpool", "udp_recv_perf", "udp_send_perf", "rtentry_lock_complex"]

    for params in to_be_validated:
        if params in supported_tunables:
            contain_supported_tunables = True
        else:
            contain_non_supported_tunables = True
        if contain_supported_tunables and contain_non_supported_tunables:
            results['msg'] = "Live update flag -K supported and non supported tunables are used together."
            results['msg'] += "Please use those tunables separately."
            module.fail_json(**results)

    if contain_supported_tunables and not contain_non_supported_tunables:
        return True


def main():
    '''
    Main function
    '''
    global results
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True, choices=['show', 'modify', 'reset']),
            component=dict(type='str', required=True, choices=['vmo', 'ioo', 'schedo', 'no',
                                                               'raso', 'nfso', 'asoo']),
            change_type=dict(type='str', default='current', choices=['current', 'reboot', 'both']),
            bosboot_tunables=dict(type='bool', default=False),
            tunable_params=dict(type='list', elements='str'),
            tunable_params_with_value=dict(type='dict'),
            restricted_tunables=dict(type='bool', default=False)
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
    change_type = module.params['change_type']
    bosboot_tunables = module.params['bosboot_tunables']

    if action == 'show':
        show(module)
    elif action == 'modify':
        if change_type == 'current' and bosboot_tunables:
            results['msg'] = 'Not possible to change current value of bosboot tunables\n'
            results['msg'] += 'Please provide change_type as reboot.'
            results['msg'] += 'For change_type = current, only dynamic tunables are supported.'
            module.fail_json(**results)
        modify(module)
    elif action == 'reset':
        reset(module)

    # changed is False in case of show action.
    if action == 'modify' or action == 'reset':
        results['changed'] = True

    module.exit_json(**results)


if __name__ == '__main__':
    main()
