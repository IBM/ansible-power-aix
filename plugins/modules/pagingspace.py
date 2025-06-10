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
- AIX Development Team (@schamola)
module: pagingspace
short_description: Manage Paging space
description:
- This module allows to list, add, change, remove, activate and deactivate paging space(s).
version_added: '2.1.0'
requirements:
- AIX
- Python >= 3.6
- 'Privileged user with authorizations'
options:
  action:
    description:
    - Specifies the action to perform.
    - C(list) to display the characteristics of a paging space.
    - C(create) to add an additional paging space.
    - C(modify) to modify a paging space.
    - C(remove) to remove a paging space.
    - C(activate) to activate a paging space.
    - C(deactivate) to deactivate a paging space.
    type: str
    choices: [ list, create, modify, remove, activate, deactivate ]
    required: true
  list_all:
    description:
    - Used with I(action==list)
    - When set to true, It specifies that all the paging spaces should be listed
    type: bool
    default: false
  include_summary:
    description:
    - Used with I(action==list)
    - If set to true, specifies that the summary characteristics of all paging spaces are to be given.
    - This information consists of the total paging space in megabytes and the percentage of paging space currently assigned (used).
    type: bool
    default: false
  ps_type:
    description:
    - Specifies the characteristics of the paging space.
    - C(lv) specifies that characteristics of only logical volume paging spaces are to be given.
    - C(nfs) specifies that the characteristics of only NFS paging spaces are to be given. In case of C(action == list), the heading of the
    - output will be changed to display the host name of the NFS server and the path name of the file that
    - resides on the server that is being used for NFS paging.
    - C(ps_helper) specifies that a helper program is to be used.
    type: str
    choices: [lv, nfs, ps_helper]
  ps_helper_name:
    description:
    - Specifies the name of paging space helper program that needs to be used.
    - When C(ps_chars == ps_helper), It is required to provide I(ps_helper_name)
    type: str
  ps_name:
    description:
    - Specifies the name of the paging space.
    type: str
  nfs_server_hostname:
    description:
    - Specifies the NFS server where the ServerFileName resides.
    - It is required to specify this attribute, in case of I(ps_type == nfs) and I(action == create)
    type: str
  nfs_server_pathname:
    description:
    - Specifies the file which will be used for the NFS paging of the system.
    - It is required to specify this attribute, in case of I(ps_type == nfs) and I(action == create)
    - This file must exist and be exported correctly to the client that will use the file for paging.
    type: str
  paging_space_configured_at_sub_restart:
    description:
    - Specifies that the paging space is configured at subsequent restarts.
    type: bool
    default: false
  checksum_size:
    description:
    - Specifies the size of the checksum to use for the paging space, in bits.
    - If not specified, by default it takes the value as 0.
    type: int
    choices: [0,8,16,32]
  activate_immediately:
    description:
    - If set to true, specifies to activate the paging space immediately.
    type: bool
    default: false
  logical_partitions:
    description:
    - Specifies the size of the paging space and the logical volume to be made in logical partitions.
    - If you are trying to create non-nfs paging space, you need to provide this attribute.
    type: int
  volume_group:
    description:
    - Specifies the name of the volume group to be used for creating the paging space.
    - If you are trying to create non-nfs paging space, you need to provide this attribute.
    type: str
  pv_name:
    description:
    - Specifies the physical volume of the I(volume_group) on which the logical volume is to be made.
    type: str
  logical_partitions_add:
    description:
    - When I(action == modify), specifies the number of logical partitions to add.
    type: int
  logical_partitions_substract:
    description:
    - When I(action == modify), specifies the number of logical partitions to substract.
    type: int
  use_ps_at_next_restart:
    description:
    - Specifies to use a paging space at the next system restart.
    type: bool
  use_on_next_swapon:
    description:
    - Specifies that the I(checksum_size) will be used for the next swapon of the paging space.
    - This option has no effect if I(checksum_size) is not specified or paging space is not swapped on.
    type: bool
    default: false
  activate_all_ps:
    description:
    - Specifies that all the paging spaces available need to be activated.
    type: bool
    default: false
  ps_list:
    description:
    - Specifies the list of paging spaces that need to be activated or deactivated.
    type: list
    elements: str
notes:
  - The /etc/swapspaces file specifies the paging spaces and the attributes of the paging spaces.
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.2?topic=concepts-paging-space-file-commands-options),
  - For more information on lsps, U(https://www.ibm.com/docs/en/ssw_aix_72/l_commands/lsps.html)
  - For more information on mkps, U(https://www.ibm.com/docs/en/ssw_aix_72/m_commands/mkps.html)
  - For more information on chps, U(https://www.ibm.com/docs/en/ssw_aix_72/c_commands/chps.html)
  - For more information on rmps, U(https://www.ibm.com/docs/en/ssw_aix_72/r_commands/rmps.html)
  - For more information on swapoff, U(https://www.ibm.com/docs/en/ssw_aix_72/s_commands/swapoff.html)
  - For more information on swapon, U(https://www.ibm.com/docs/en/ssw_aix_72/s_commands/swapon.html)
"""

EXAMPLES = r"""
- name: List paging space summary
  ibm.power_aix.pagingspace:
    action: list
    include_summary: true

- name: List all the paging spaces
  ibm.power_aix.pagingspace:
    action: list
    list_all: true
    include_summary: true
    output_list_format: true

- name: Create a lv paging space
  ibm.power_aix.pagingspace:
    action: create
    activate_immediately: false
    ps_type: lv
    volume_group: rootvg
    logical_partitions: 2

- name: Create nfs paging space
  ibm.power_aix.pagingspace:
    action: create
    activate_immediately: true
    ps_type: nfs
    nfs_server_hostname: hostname
    nfs_server_pathname: pathname

- name: Modify a particular paging space, add lpars and change checksum size
  ibm.power_aix.pagingspace:
    action: modify
    logical_partitions_add: 2
    checksum_size: 8
    use_on_next_swapon: true
    ps_name: paging00

- name: Activate all paging spaces
  ibm.power_aix.pagingspace:
    action: activate
    activate_all_ps: true

- name: Activate a paging space
  ibm.power_aix.pagingspace:
    action: activate
    ps_name: /dev/paging00

- name: Deactivate a paging space
  ibm.power_aix.pagingspace:
    action: deactivate
    ps_name: /dev/paging00

- name: Remove a paging space
  ibm.power_aix.pagingspace:
    action: remove
    ps_name: paging00
"""

RETURN = r"""
msg:
    description: The execution message.
    returned: always
    type: str
rc:
    description: The return code.
    returned: always
    type: int
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
changed:
    description: Tells whether any change occured on the system
    returned: always
    type: bool
"""

from ansible.module_utils.basic import AnsibleModule

results = dict(
    changed=False,
    rc=0,
    msg="",
    stdout="",
    stderr="",
    paging_space_attributes={},
)


# Utility functions
def parse_ps_details(module, stdout):
    """
    Parse the information provided from lsps command.

    arguments:
        module (dict): Ansible generic module.
        stdout (str): Standard output of lsps command.

    returns:
        parsed_output (dict): Dictionary containing output of lsps in parsed format.
    """
    parsed_output = {}

    stdout_lines = stdout.splitlines()

    # Fail if no information is present
    if len(stdout_lines) <= 1:
        results["msg"] = "No information is present on the system that can be listed."
        module.exit_json(**results)

    # Information is included from the second line (index=1)
    stdout_info = stdout_lines[1:]

    if module.params["include_summary"]:
        # Only these values will be present in case of summary
        parsed_output["Total Paging space"] = stdout_info[0].split()[0]
        parsed_output["Percent used"] = stdout_info[0].split()[1]

        # No need to run further
        return parsed_output

    elif module.params["ps_type"] == "nfs":
        key_attrs = [
            "Paging space name",
            "Server Hostname",
            "File Name",
            "Size",
            "Percentage Used",
            "Active",
            "Auto",
            "Type",
            "Checksum",
        ]
    else:
        key_attrs = [
            "Paging space name",
            "Physical Volume",
            "Volume Group",
            "Size",
            "Percentage Used",
            "Active",
            "Auto",
            "Type",
            "Checksum",
        ]

    # Iterate through all the paging spaces present and add their information into the dictionary.
    for line in stdout_info:
        info = line.split()
        ps_name = info[0]

        # Total 9 attributes are there when we list the information about paging spaces.
        for index in range(9):
            # For cases when some information is missing from the output
            try:
                if index == 0:
                    parsed_output[ps_name] = {}
                    continue

                parsed_output[ps_name][key_attrs[index]] = info[index]
            except IndexError:
                break

    return parsed_output


def check_if_exists(module, ps_name):
    """
    Checks if a paging space exists and return its attributes if available.
    Helpful in checking for idempotency.

    arguments:
        module (dict): Ansible generic module.
        ps_name (str): Name of the paging space.

    returns:
        0 (int): If The paging space does not exist
        parsed_output (dict): Properties of the paging space if it exists
    """

    # Command to check existence
    cmd = f"lsps {ps_name}"

    rc, stdout, stderr = module.run_command(cmd)

    # If the command fails, the paging space does not exist
    if rc:
        return False

    # If the paging space exists, return the details of the paging space
    return parse_ps_details(module, stdout)


# Action functions
def list_paging_space(module):
    """
    List the information about existing paging space(s)

    arguments:
        module (dict): Ansible generic module.

    returns:
        success_msg (str): Success message in case the command ran successfully,
        fails otherwise.
    """
    cmd = ["/usr/sbin/lsps"]

    # Add additional flags to the main command
    # If the -s flag is specified, other flags are ignored.
    if module.params["include_summary"]:
        cmd.append("-s")
    else:
        # -a, -t and psname are mutually exclusive flags
        if module.params["list_all"]:
            cmd.append("-a")
        elif module.params["ps_type"]:
            chars = module.params["ps_type"]

            if chars == "lv":
                cmd.append("-t lv")
            elif chars == "nfs":
                cmd.append("-t nfs")
            else:
                helper_name = module.params["ps_helper_name"]
                cmd.append(f"-t {helper_name}")
        else:
            if module.params["ps_name"]:
                cmd.append(module.params["ps_name"])
            else:
                results["msg"] = (
                    "You need to provide one of the following: ['list_all', 'ps_chars', 'ps_name']"
                )
                module.fail_json(**results)

    joined_cmd = " ".join(cmd)

    rc, stdout, stderr = module.run_command(joined_cmd)

    fail_msg = f"Could not get the required information, command: {joined_cmd}"
    success_msg = "Successfully retrieved information about paging spaces. Please check 'paging_space_attributes'"

    results["stdout"] = stdout

    if rc:
        results["stderr"] = stderr
        results["msg"] = fail_msg
        module.fail_json(**results)

    results["paging_space_attributes"] = parse_ps_details(module, stdout)

    # Nothing is changing in the system.
    results["changed"] = False
    return success_msg


def create_paging_space(module):
    """
    Create a new paging space.

    arguments:
        module (dict): Ansible generic module

    returns:
        success_msg (str): Success message in case the command ran successfully,
        fails otherwise.
    """
    # Idempotency check
    if module.params["ps_name"] and check_if_exists(module, module.params["ps_name"]):
        ps_name = module.params["ps_name"]
        msg = f"The provided paging space already exists : {ps_name}"
        return msg

    cmd = ["/usr/sbin/mkps"]

    # Adding addtional flags to the command
    if module.params["paging_space_configured_at_sub_restart"]:
        cmd.append("-a")

    if module.params["activate_immediately"]:
        cmd.append("-n")

    if module.params["ps_type"]:
        ps_type = module.params["ps_type"]

        if ps_type == "lv":
            cmd.append("-t lv")
        elif ps_type == "ps_helper":
            helper_name = module.params["ps_helper_name"]

            if module.params["ps_name"]:
                ps_name = module.params["ps_name"]

            cmd.append(f"-t {helper_name} {ps_name}")
        else:
            nfs_hostname = module.params["nfs_server_hostname"]
            nfs_pathname = module.params["nfs_server_pathname"]

            cmd.append(f"-t nfs {nfs_hostname} {nfs_pathname}")

            # In case of nfs type, no other flags are required
            joined_cmd = " ".join(cmd)

            rc, stdout, stderr = module.run_command(joined_cmd)

            results["stdout"] = stdout

            success_msg = f"Command {joined_cmd} ran successfully!"
            fail_msg = f"The following command failed: {joined_cmd}. Please check stderr for more information."

            if rc:
                results["stderr"] = stderr
                results["msg"] = fail_msg
                module.fail_json(**results)

            results["changed"] = True
            return success_msg

    if module.params["checksum_size"]:
        checksum_size = module.params["checksum_size"]

        cmd.append(f"-c {checksum_size}")

    if not module.params["logical_partitions"] or not module.params["volume_group"]:
        results["msg"] = (
            "When trying to create non-nfs paging space, you need to specify both 'logical_partitions' and 'volume_group'."
        )
        module.fail_json(**results)
    else:
        lpar = module.params["logical_partitions"]
        vg = module.params["volume_group"]

        cmd.append(f"-s {lpar} {vg}")

    if module.params["pv_name"]:
        cmd.append(module.params["pv_name"])

    joined_cmd = " ".join(cmd)
    rc, stdout, stderr = module.run_command(joined_cmd)

    results["stdout"] = stdout
    success_msg = f"Successfully created paging space, Command: {joined_cmd}"
    fail_msg = f"Couldn't create paging space, command: {joined_cmd}."
    fail_msg += "Please check stderr for more information."

    if rc:
        results["stderr"] = stderr
        results["msg"] = fail_msg
        module.fail_json(**results)

    results["changed"] = True
    return success_msg


def modify_paging_space(module):
    """
    modify the provided paging space.

    arguments:
        module (dict): Ansible generic module

    returns:
        success_msg (str): Success message in case the command ran successfully,
        fails otherwise.
    """
    ps_name = module.params["ps_name"]
    get_ps_info = check_if_exists(module, ps_name)

    if not get_ps_info:
        results["msg"] = "The provided paging space does not exit!"
        module.fail_json(**results)

    cmd = ["/usr/sbin/chps"]

    # Adding additional flags
    if module.params["ps_helper_name"]:
        helper_name = module.params["ps_helper_name"]
        cmd.append(f"-t {helper_name}")

    if module.params["logical_partitions_add"]:
        lpar_add = module.params["logical_partitions_add"]
        cmd.append(f"-s {lpar_add}")

    if module.params["logical_partitions_substract"]:
        lpar_sub = module.params["logical_partitions_substract"]
        cmd.append(f"-d {lpar_sub}")

    if module.params["use_on_next_swapon"]:
        cmd.append("-f")

    if module.params["checksum_size"]:
        # Without -f flag set, the command will fail when trying to change the checksum size
        if not module.params["use_on_next_swapon"]:
            results["msg"] = (
                "When specifying 'checksum_size', you also need to set 'use_on_next_swapon' to true."
            )
            module.fail_json(**results)

        checksum_size = module.params["checksum_size"]

        # Idempotency check
        # Only add checksum size to the command if it is not already set
        if get_ps_info[ps_name]["Checksum"] != str(checksum_size):
            cmd.append(f"-c {checksum_size}")
        else:
            cmd.remove("-f")

    if module.params["use_ps_at_next_restart"] is True:
        cmd.append("-a y")

    if module.params["use_ps_at_next_restart"] is False:
        cmd.append("-a n")

    if len(cmd) == 1:
        msg = "All the provided attributes are already set, no need to modify"
        return msg

    cmd.append(module.params["ps_name"])

    joined_cmd = " ".join(cmd)
    rc, stdout, stderr = module.run_command(joined_cmd)

    fail_msg = f"Failed to modify the paging space, check stderr for more information. Command: {joined_cmd}"
    success_msg = f"Successfully modified the paging space, Command: {joined_cmd}"

    results["stdout"] = stdout

    if rc:
        results["rc"] = rc
        results["msg"] = fail_msg
        results["stderr"] = stderr
        module.fail_json(**results)

    results["changed"] = True
    return success_msg


def remove_paging_space(module):
    """
    Remove the provided paging space.

    arguments:
        module (dict): Ansible generic module

    returns:
        success_msg (str): Success message in case the command ran successfully,
        fails otherwise.
    """
    # Idempotency check
    if not check_if_exists(module, module.params["ps_name"]):
        results["msg"] = "The paging space does not exist, no need to remove it."
        module.fail_json(**results)

    cmd = ["/usr/sbin/rmps"]

    # Adding additional flags
    if module.params["ps_helper_name"]:
        helper_name = module.params["ps_helper_name"]
        cmd.append(f"-t {helper_name}")

    # Paging space that needs to be removed should be provided
    cmd.append(module.params["ps_name"])

    joined_cmd = " ".join(cmd)
    rc, stdout, stderr = module.run_command(joined_cmd)

    fail_msg = f"Failed to remove the paging space, check stderr for more information. Command: {joined_cmd}"
    success_msg = f"Successfully removed the paging space, Command: {joined_cmd}"

    results["stdout"] = stdout

    if rc:
        results["rc"] = rc
        results["msg"] = fail_msg
        results["stderr"] = stderr
        module.fail_json(**results)

    results["changed"] = True
    return success_msg


def activate_paging_space(module):
    """
    Activate the provided paging space(s).

    arguments:
        module (dict): Ansible generic module

    returns:
        success_msg (str): Success message in case the command ran successfully,
        fails otherwise.
    """
    cmd = ["/usr/sbin/swapon"]
    active_ps = []

    # Adding additional flags
    if module.params["activate_all_ps"]:
        all_ps_info = check_if_exists(module, "-a")

        # Idempotency check
        if all_ps_info:
            total_ps = 0
            for key in all_ps_info.keys():
                total_ps += 1
                if all_ps_info[key]["Active"] == "yes":
                    active_ps.append(key)

            if total_ps == len(active_ps):
                return "All the paging spaces are already in active state, no need to run the command."
        else:
            results["msg"] = "No paging spaces are present."
            module.fail_json(**results)

        cmd.append("-a")
    elif module.params["ps_list"]:
        ps_list = module.params["ps_list"]

        # Checking for idempotency
        already_active = []
        does_not_exist = []
        for ps in ps_list:
            ps_name = ps
            if "/" in ps_name:
                ps_name = ps.split("/")[-1]

            check_exist = check_if_exists(module, ps_name)
            if not check_exist:
                does_not_exist.append(ps)
                continue
            if check_exist and check_exist[ps_name]["Active"] == "yes":
                already_active.append(ps)
                continue

            cmd.append(ps)

        # Remove the paging spaces that are already active
        for ps in already_active:
            module.params["ps_list"].remove(ps)

        # Remove the paging spaces that does not exist
        for ps in does_not_exist:
            module.params["ps_list"].remove(ps)

        # No need to run the command and set changed to true in case the paging space(s) is already in active state
        if not len(module.params["ps_list"]):
            return "All the provided paging spaces are either already in active state or do not exist."
    else:
        # For activating just one paging space
        if module.params["ps_name"]:
            ps_name = module.params["ps_name"]

            if "/" in ps_name:
                ps_name = ps_name.split("/")[-1]

            check_exists = check_if_exists(module, ps_name)
            # Negative test
            if not check_exists:
                return "The provided paging space does not exist."

            # Idempotency check
            if check_exists != 0 and check_exists[ps_name]["Active"] == "yes":
                return "The provided paging space is already in active state."

            cmd.append(module.params["ps_name"])
        else:
            results["msg"] = (
                "You need to set either 'activate_all_ps' as true, or provide the paging space names using 'ps_name' or 'ps_list'"
            )
            module.fail_json(**results)

    joined_cmd = " ".join(cmd)
    rc, stdout, stderr = module.run_command(joined_cmd)

    if stderr or stdout:
        already_active = []
        activated = []
        could_not_activate = []

        # Paging spaces that are already active, or could not be activated
        # are present in stderr
        if stderr:
            stderr_lines = stderr.splitlines()
            for line in stderr_lines:
                line = line.split()
                ps_name = ""

                for item in line:
                    if "/dev" in item:
                        ps_name = item
                        break

                if line[0] == "0517-075":
                    already_active.append(ps_name)
                else:
                    could_not_activate.append(ps_name)

        # For paging spaces that were activated successfully
        if stdout:
            stdout_lines = stdout.splitlines()

            for line in stdout_lines:
                line = line.split()
                for item in line:
                    if "/dev" in item:
                        activated.append(item)
                        break

        results["stderr"] = stderr
        results["stdout"] = stdout

        # Fail if even one paging space could not be activated
        if len(could_not_activate):
            results["msg"] = (
                f"Could not activate the following paging spaces: {could_not_activate}."
            )
            if len(activated):
                results["msg"] += f" Activated: {activated}."

            if len(already_active):
                results["msg"] += f" Already active: {already_active}"

            results["stdout"] = stdout
            results["stderr"] = stderr
            module.fail_json(**results)
        else:
            msg = ""

            # Changed should be set to True, even if only one paging space is activated.
            if len(activated):
                results["changed"] = True
                msg += f"Activated the following paging spaces: {activated}."

            if len(already_active):
                msg += f" These were already active: {already_active}"

            results["msg"] = msg
            module.exit_json(**results)

    if module.params["ps_name"]:
        fail_msg = f"Failed to activate paging space: {module.params['ps_name']}, check stderr for more information. Command: {joined_cmd}"
        success_msg = f"Successfully activated the paging space: {module.params['ps_name']}, Command: {joined_cmd}"
    elif module.params["activate_all_ps"]:
        fail_msg = f"Failed to activate the paging space(s). Command: {joined_cmd}"
        success_msg = (
            f"Successfully activated all the paging spaces. Command: {joined_cmd}"
        )
    else:
        fail_msg = f"Failed to activate paging spaces: {module.params['ps_list']}, check stderr for more information. Command: {joined_cmd}"
        success_msg = f"Successfully activated the paging space: {module.params['ps_list']}, Command: {joined_cmd}"

    results["stdout"] = stdout

    if rc:
        results["rc"] = rc
        results["msg"] = fail_msg
        results["stderr"] = stderr
        module.fail_json(**results)

    results["changed"] = True
    return success_msg


def deactivate_paging_space(module):
    """
    Deactivate the provided paging space.

     arguments:
         module (dict): Ansible generic module

     returns:
         success_msg (str): Success message in case the command ran successfully,
         fails otherwise.
    """
    cmd = ["/usr/sbin/swapoff"]
    # Add check for if the customer has provided all the paging spaces

    # Adding additional flags
    # Need to provide the paging space(s) to be deactivated
    if not module.params["ps_list"] and not module.params["ps_name"]:
        results["msg"] = "You need to provide the paging spaces to be deactivated."
        module.fail_json(**results)

    if module.params["ps_list"]:
        inactive_ps = []
        does_not_exist = []
        ps_list = module.params["ps_list"]
        for ps in ps_list:
            ps_name = ps
            if "/" in ps:
                ps_name = ps.split("/")[-1]

            check_exist = check_if_exists(module, ps_name)

            if not check_exist:
                does_not_exist.append(ps)
                continue

            if check_exist and check_exist[ps_name]["Active"] != "yes":
                inactive_ps.append(ps)
                continue

            cmd.append(ps)

        # Idempotency check in case of multiple paging spaces
        if len(ps_list) and (len(ps_list) == (len(inactive_ps) + len(does_not_exist))):
            return "No need to deactivate as the provided paging space(s) are either already in deactivated state or do not exist."

    if module.params["ps_name"]:
        ps_name = module.params["ps_name"]

        if "/" in ps_name:
            ps_name = ps_name.split("/")[-1]

        check_exist = check_if_exists(module, ps_name)

        if not check_exist:
            results["msg"] = "The provided paging space does not exist."
            module.fail_json(**results)

        if check_exist and check_exist[ps_name]["Active"] != "yes":
            return "No need to deactivate, already deactivated."

        cmd.append(module.params["ps_name"])

    joined_cmd = " ".join(cmd)
    rc, stdout, stderr = module.run_command(joined_cmd)

    if module.params["ps_list"]:
        fail_msg = f"Failed to deactivate paging spaces: {module.params['ps_list']}, check stderr for more information. Command: {joined_cmd}"
        success_msg = f"Successfully deactivated the paging space: {module.params['ps_list']}, Command: {joined_cmd}"
    else:
        fail_msg = f"Failed to deactivate paging spaces: {module.params['ps_name']}, check stderr for more information. Command: {joined_cmd}"
        success_msg = f"Successfully deactivated the paging space: {module.params['ps_name']}, Command: {joined_cmd}"

    results["stdout"] = stdout

    if rc:
        results["rc"] = rc
        results["msg"] = fail_msg
        results["stderr"] = stderr
        module.fail_json(**results)

    results["changed"] = True
    return success_msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            action=dict(
                type="str",
                required=True,
                choices=[
                    "list",
                    "create",
                    "modify",
                    "remove",
                    "activate",
                    "deactivate",
                ],
            ),
            list_all=dict(type="bool", default=False),
            include_summary=dict(type="bool", default=False),
            ps_helper_name=dict(type="str"),
            ps_name=dict(type="str"),
            nfs_server_hostname=dict(type="str"),
            nfs_server_pathname=dict(type="str"),
            paging_space_configured_at_sub_restart=dict(type="bool", default=False),
            checksum_size=dict(type="int", choices=[0, 8, 16, 32]),
            activate_immediately=dict(type="bool", default=False),
            logical_partitions=dict(type="int"),
            ps_type=dict(type="str", choices=["lv", "nfs", "ps_helper"]),
            volume_group=dict(type="str"),
            pv_name=dict(type="str"),
            logical_partitions_add=dict(type="int"),
            logical_partitions_substract=dict(type="int"),
            use_ps_at_next_restart=dict(type="bool"),
            use_on_next_swapon=dict(type="bool", default=False),
            activate_all_ps=dict(type="bool", default=False),
            ps_list=dict(type="list", elements="str"),
        ),
        mutually_exclusive=[["ps_name", "ps_list"]],
        required_if=[
            ["action", "remove", ["ps_name"]],
            ["ps_type", "ps_helper", ["ps_helper_name"]],
        ],
    )

    # Validation of attributes
    if module.params["action"] == "create" and module.params["ps_type"] == "nfs":
        if (
            not module.params["nfs_server_hostname"]
            or not module.params["nfs_server_pathname"]
        ):
            results["msg"] = (
                "You need to provide NFS hostname and pathname, when creating a paging space with ps_type = nfs"
            )
            module.fail_json(**results)

    action = module.params["action"]

    if action == "list":
        results["msg"] = list_paging_space(module)
    elif action == "create":
        results["msg"] = create_paging_space(module)
    elif action == "modify":
        results["msg"] = modify_paging_space(module)
    elif action == "remove":
        results["msg"] = remove_paging_space(module)
    elif action == "activate":
        results["msg"] = activate_paging_space(module)
    else:
        results["msg"] = deactivate_paging_space(module)

    module.exit_json(**results)


if __name__ == "__main__":
    main()
