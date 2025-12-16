#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
author:
- Shreyansh Chamola (@schamola)
module: nimclient
short_description: Allows Network Installation Management (NIM) operations to be performed from a NIM client.
description:
- The nimclient module is used by workstations that are NIM clients to pull NIM resources.
- This module can enable or disable the NIM master server's ability to initiate workstation
  installation and customization for the workstation.
- The nimclient module can be used to generate a list of available NIM resources or display
  the NIM resources that have already been allocated to the client.
- A limited set of NIM operations can also be performed by the nimclient command using (action='perform_nim_op') action.
version_added: '2.2.0'
requirements:
- AIX >= 7.1
- Python >= 3.9
options:
  action:
    description:
    - Specifies which action needs to be performed.
      C(list) executes the lsnim command on the master, listing all the resources.
      C(perform_nim_op) specifies to perform NIM related operations with I(operation).
      C(other_op) specifies to perform Non - NIM related operations.
    type: str
    choices: [ list, perform_nim_op, other_op ]
    required: true
  operation:
    description:
    - Specifies which operation needs to be performed.
      C(allocate) allocates a resource for use.
      C(bos_inst) performs a BOS installation.
      C(change) changes an object's attributes.
      C(check) checks the status of a NIM object.
      C(cust) performs software customization.
      C(deallocate) deallocates the resource
      C(diag) enables a machine to boot a diagnostic image.
      C(maint_boot) enables a machine to boot in maintenance mode.
      C(reset) resets an object's NIM state.
      C(showres) displays the contents of a NIM resource.
    type: str
    required: false
    choices: [ allocate, bos_inst, change, check, cust, deallocate, diag, maint_boot, reset, showres ]
  master_push_perm:
    description:
    - C(enable) enables the NIM master to push commands.
    - C(disable) removes the NIM master's permissions to push commands.
    type: str
    choices: [ enable, disable ]
  crypto_auth_perm:
    description:
    - C(enable) enables SSL authentication during NIM master push operations
    - C(disable) disables SSL authentication and uses standard nimsh security
      during NIM master push operations.
    type: str
    choices: [ enable, disable ]
  set_master_date:
    description:
    - To Set the Date and Time to That of the NIM Master
    type: bool
    default: false
  attributes:
    description:
    - Passes information to NIM operations.
    type: list
    elements: str
notes:
  - You can refer to the IBM documenation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.1.0?topic=n-nimclient-command).
"""

EXAMPLES = r"""
- name: List all available NIM resources
  ibm.power_aix.nimclient:
    action: list

- name: Enable crypto auth permission
  ibm.power_aix.nimclient:
    action: other_op
    crypto_auth_perm: enable

- name: Enable master push auth permission
  ibm.power_aix.nimclient:
    action: other_op
    master_push_perm: enable

- name: Set same date as master
  ibm.power_aix.nimclient:
    action: other_op
    set_master_date: true

- name: perform bos_inst
  ibm.power_aix.nimclient:
    action: perform_nim_op
    operation: bos_inst

- name: allocate a lpp_source and spot
  ibm.power_aix.nimclient:
    action: perform_nim_op
    operation: allocate
    attributes:
      - lpp_source=2342B_73D
      - spot=2342B_73D_SPOT

- name: Show contents of a resource
  ibm.power_aix.nimclient:
    action: perform_nim_op
    operation: showres
    attributes:
      - resource=2342B_73D

- name: Enable the system to boot in maintenance mode using a SPOT
  ibm.power_aix.nimclient:
    action: perform_nim_op
    operation: maint_boot
    attributes:
      - spot=2342B_73D_SPOT

- name: Reset the state of client
  ibm.power_aix.nimclient:
    action: perform_nim_op
    operation: reset
"""

RETURN = r"""
msg:
    description: The execution message.
    returned: always
    type: str
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: always
    type: int
stdout:
    description: The standard output of the command.
    returned: always
    type: str
stderr:
    description: The standard error of the command.
    returned: always
    type: str
changed:
    description: Shows if any change was made.
    returned: always
    type: bool
timezone_details:
    description: Contains the details related to timezone.
    returned: If I(action=list_versions) or I(action=print_updated_zones)
    type: dict
"""

from ansible.module_utils.basic import AnsibleModule
# import re
# import os.path

results = dict(
    changed=False,
    cmd="",
    msg="",
    rc="",
    stdout="",
    stderr="",
    nim_info={},
)

####################################################################################
# Helper Functions
####################################################################################


def parsed_info(stdout):
    """
    Utility function to return parsed information about the resources.

    arguments:
      stdout  (str) - standard output of the command.

    returns:
      niminfo (dict) - Dictionary containing resource information in parsed manner.
    """

    niminfo = {}

    stdout_lines = stdout.strip().splitlines()

    # Skip header line (first line)
    for line in stdout_lines[1:]:
        parts = line.split()

        # Ignore empty or malformed lines
        if len(parts) < 3:
            continue

        name, object_class, resource = parts[0], parts[1], parts[2]

        niminfo[name] = {
            "object_class": object_class,
            "object_type": resource,
        }

    return niminfo


####################################################################################
# Action Functions
####################################################################################


def list_info(module):
    """
    Lists information about the NIM Environment.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    cmd = "nimclient -l"

    # params = module.params['lsnim_params']
    # if params:
    #     cmd.append(f" {params}")

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": "Failed to retrieve information about the NIM environment.",
            "rc": rc,
            "stderr": stderr,
            "cmd": cmd,
        }

    niminfo = parsed_info(stdout)

    payload = {
        "changed": False,
        "msg": "Successfully retrieved available information. Check 'nim_info' for details.",
        "rc": 0,
        "stdout": stdout,
        "nim_info": niminfo,
        "cmd": cmd,
    }

    return payload


def nim_operations(module):
    """
    Perform a NIM operation.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    cmd = ["nimclient"]

    op = module.params["operation"]
    cmd.append(f"-o {op}")

    attrs = module.params["attributes"]

    if attrs:
        attrs = "-a " + " -a ".join(attrs) + " "
        cmd.append(attrs)

    cmd = " ".join(cmd)

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": f"Failed to run the following command: {cmd}",
            "rc": rc,
            "stderr": stderr,
            "cmd": cmd,
        }

    payload = {
        "changed": True,
        "msg": f"Successfully ran the following command: {cmd}.",
        "rc": 0,
        "stdout": stdout,
        "cmd": cmd,
    }

    if op == "showres":
        payload["changed"] = False

    return payload


def other_operations(module):
    """
    Performs non - NIM related operations on the system.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    cmd = ["nimclient"]

    push_perm = module.params["master_push_perm"]
    crypto_perm = module.params["crypto_auth_perm"]
    set_master_date = module.params["set_master_date"]

    if push_perm:
        if push_perm == "enable":
            cmd.append("-p")
        else:
            cmd.append("-P")

    if crypto_perm:
        if crypto_perm == "enable":
            cmd.append("-c")
        else:
            cmd.append("-C")

    if set_master_date:
        cmd.append("-d")

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": f"Failed to run the command: {' '.join(cmd)}.",
            "rc": rc,
            "stderr": stderr,
            "cmd": cmd,
        }

    payload = {
        "changed": True,
        "msg": f"Successfully ran the following command: {' '.join(cmd)}.",
        "rc": 0,
        "stdout": stdout,
        "cmd": cmd,
    }

    return payload


####################################################################################
# Main Function
####################################################################################


def main():

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            action=dict(
                type="str",
                choices=["list", "perform_nim_op", "other_op"],
                required=True,
            ),
            operation=dict(
                type="str",
                choices=[
                    "allocate",
                    "bos_inst",
                    "change",
                    "check",
                    "cust",
                    "deallocate",
                    "diag",
                    "maint_boot",
                    "reset",
                    "showres",
                ],
            ),
            master_push_perm=dict(
                type="str", choices=["enable", "disable"], required=False
            ),
            crypto_auth_perm=dict(
                type="str", choices=["enable", "disable"], required=False
            ),
            set_master_date=dict(type="bool", default=False),
            attributes=dict(type="list", elements="str"),
            # lsnim_params=dict(type='str'),
        ),
        required_if=[["action", "perform_nim_op", ["operation"]]],
    )

    action = module.params["action"]

    if action == "list":
        results = list_info(module)

    elif action == "perform_nim_op":
        results = nim_operations(module)

    else:
        results = other_operations(module)

    if results.get("failed"):
        module.fail_json(**results)
    else:
        module.exit_json(**results)


if __name__ == "__main__":
    main()
