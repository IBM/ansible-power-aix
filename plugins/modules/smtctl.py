#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import (absolute_import, division, print_function)
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---

author:
- Madhu Pillai (@resvrin)
module: smtctl
short_description: Enable and Disable Simultaneous MultiThreading Mode
description:
- This command is provided for privileged users and applications to control utilization of processors with simultaneous multithreading support.
- The simultaneous multithreading mode allows processors to have thread level parallelism at the instruction level.
- This mode can be enabled or disabled for all processors either immediately or on subsequent boots of the system.
- This command controls the simultaneous multithreading options.
version_added: '1.3.0'
requirements:
- AIX  7.2
- IBM Power9_Power8
- Python >= 3.6
options:
  smt_value:
    description:
    - This value takes appropriate SMT value
    type: int
    choices: [1, 2, 4, 8]
  smt_extra:
    description:
    - C("recommended or suspend") This values is mutually exclusive with smt_value and smt_state.
    type: str
    choices: [recommended, suspend]
  smt_limit:
    description:
    - This values set the limit for the multithreading.
    type: str
  bos_boot:
    description:
    - This runs the bosboot after the respective action get executed.It is freeform command can executed with any parameter.
    type: bool
  chtype:
    description:
    - C(boot or now) This take either boot or now value.
    type: str
    choices: [boot, now]
  smt_state:
   description:
   - This enable or disable  the SMT in the lpar.
   type: str
   choices: [enabled, disabled]

notes:
- Please refer to the IBM documentation for additional information on the commands used in the module.
  U(https://www.ibm.com/support/knowledgecenter/en/ssw_aix_71/s_commands/smtctl.html)
'''

EXAMPLES = r'''
- name: Enable the SMT value to 8 and value needs to be persist across subsequent reboot
  ibm.power_aix.smtctl:
    smt_value: 8
    bos_boot: true

- name: Enable the SMT value to 8 to next boot if bos_boot set to yes
  ibm.power_aix.smtctl:
    smt_value: 8
    chtype: boot
    bos_boot: true

- name: Limit the SMT value to 4
  ibm.power_aix.smtctl:
    smt_value: 4
    smt_limit: limit

- name: Disable the smtctl
  ibm.power_aix.smtctl:
    smt_state: disabled

- name: Sets the number of threads to a value that provides the best performance
  ibm.power_aix.smtctl:
    smt_extra: recommended
'''

RETURN = r'''
msg:
    description: Output on Debug
    returned: always
    type: str
    sample: Command Executed Successfully smtctl -t 8

'''


def get_smt_state(module):
    """ Determines the current SMT status and return the present smtvalue else none"""
    cmd = "smtctl"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = f"Command {cmd} failed."
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    if stdout:
        present_value = False
        for line in stdout.split('\n'):
            line_out = line.strip().split()
            try:
                if "proc" in line_out[0] and int(line_out[2]) > 1:
                    # Value greater than 1 is SMT Enabled
                    present_value = int(line_out[2])
                    break
            except IndexError:
                pass
        return present_value
    return None


def smt_set(module):
    """

    Set the smt value to enable or disable or set the
    threads value as per the default smt_value

    """

    smt_value = module.params["smt_value"]
    smt_extra = module.params["smt_extra"]
    chtype = module.params["chtype"]
    smt_limit = module.params["smt_limit"]
    smt_state = module.params["smt_state"]

    # Setting the conditional to execute the appropriate flags

    opts = ""

    if smt_value and chtype and not smt_limit:
        opts += f"-t {smt_value} -w {chtype}"

    elif smt_value and smt_limit:
        opts += f"-m {smt_limit} -t {smt_value}"

    elif smt_value:
        opts += f"-t {smt_value}"

    elif smt_extra:
        opts += f"-m {smt_extra}"

    elif smt_state == "enabled":
        opts += "-m on"

    elif smt_state == "disabled":
        opts += "-m off"

    else:
        opts = ""

    cmd = f"smtctl {opts}"
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = f"Command Execution Failure cmd: {cmd}"
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    else:
        msg = f"Command Executed Successfully cmd: {cmd}"
        return True, msg


def run_bosboot(module):
    """ Running bosboot the changes to take effect on subsequent reboots """

    opts = ""

    bos_boot = module.params["bos_boot"]

    if bos_boot:
        opts += "-a"

        cmd = f"bosboot {opts} "
        rc, stdout, stderr = module.run_command(cmd)

        if rc != 0:
            msg = f"Command Execution Failed cmd - {cmd}"
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg = f"Command Executed Successfully output- {stdout}"
            return True, msg

    return None


def run_module():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        smt_value=dict(type='int', required=False, choices=[1, 2, 4, 8]),
        smt_extra=dict(type='str', required=False, choices=['recommended', 'suspend']),
        smt_limit=dict(type='str', required=False),
        bos_boot=dict(type='bool', required=False),
        chtype=dict(type='str', required=False, choices=['boot', 'now']),
        smt_state=dict(type='str', required=False, choices=['enabled', 'disabled'])
    )

    result = dict(
        changed=False,
        msg='No Changes',
        bos_changed=False,
        bos_message='No Changes'
    )

    # Instantiation of common attributes from module_Arg

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False,
        mutually_exclusive=[['smt_extra', 'smt_value', 'smt_state']]
    )

    current_state = get_smt_state(module)
    smt_value = module.params["smt_value"]
    smt_extra = module.params["smt_extra"]
    bos_boot = module.params["bos_boot"]
    smt_limit = module.params["smt_limit"]
    smt_state = module.params["smt_state"]

    # Adding the condition to execute the bosboot if it is set

    if smt_value and not smt_limit:
        if smt_value != current_state:
            result["changed"], result["msg"] = smt_set(module)
            if result["changed"] and bos_boot:
                result["bos_changed"], result["bos_message"] = run_bosboot(module)

    if smt_value and smt_limit:
        result["changed"], result["msg"] = smt_set(module)
        if result["changed"] and bos_boot:
            result["bos_changed"], result["bos_message"] = run_bosboot(module)

    if smt_extra:
        result["changed"], result["msg"] = smt_set(module)
        if result["changed"] and bos_boot:
            result["bos_changed"], result["bos_message"] = run_bosboot(module)

    if smt_state:
        result["changed"], result["msg"] = smt_set(module)
        if result["changed"] and bos_boot:
            result["bos_changed"], result["bos_message"] = run_bosboot(module)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
