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
module: llvupdate
short_description: Performs Live Library Update
description:
- Performs the Live Library Update (LLU) operation for the specified processes without a downtime for workloads.
version_added: '2.2.0'
requirements:
- AIX >= 7.3
- Python >= 3.6
- 'Privileged user with authorization:
  B(aix.system.install)'
options:
  action:
    description:
    - Controls what action is performed.
    - C(update) performs live update operation on the specified processes.
    - C(preview) performs live update operation in preview mode.
    - C(clean) performs clean up of kernel state and also uncleaned processes.
    type: str
    choices: [ update, preview, clean ]
    required: true
  processes_to_include:
    description:
    - Initiates the Live Library Update for the specified processes.
    - When used, the llvupdate command monitors the progress of the LLU operation of
      each process and stops the operation for any process that does not complete the
      update operation within the timeout period.
    type: list
    elements: str
  include_all:
    description:
    - Scans all the processes and initiates the Live Library Update operation for all LLU-capable processes
      according to the timeout policy.
    type: bool
    default: False
  processes_to_exclude:
    description:
    - Performs LLU operation on all LLU-capable processes except the ones provided using this flag.
    type: list
    elements: str
  logfile:
    description:
    - Specifies the log file that you want to use.
    - By default, the log file is /var/adm/ras/liveupdate/logs/llvupdlog.<date.time>.
    type: str
  retries:
    description:
    - Specifies the number of times the Live Library Update operation must be attempted.
    - The default value is 3.
    type: int
  timeout:
    description:
    - Specifies the time for all threads in a process to reach a state after which the LLU operation can be performed.
    - If the LLU operation cannot be started within this timeout period, the operation is canceled for that process and is retried
      after 10 seconds up to a number of attempts that are specified.
    - The default timeout period is 30 seconds. The maximum timeout value is 300 seconds.
    type: int
  auto_cleanup:
    description:
    - Specifies if cleanup needs to be automatically performed after performing live update for any process(s)
    - When set to I(auto_cleanup=true), cleanup will be performed after llvupdate command is run, regardless of
      the return code.
    type: bool
    default: false

notes:
  - You can refer to the IBM documentation for additional information on the llvupdate command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=l-llvupdate-command)
  - You can refer to the IBM documentation for additional information on the LLU operation at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=update-live-library-llu)
"""

EXAMPLES = r"""
- name: Perform LLU in preview mode
  ibm.power_aix.llvupdate:
    action: preview

- name: Perform LLU on one process.
  ibm.power_aix.llvupdate:
    action: update
    processes_to_include: 13369744

- name: Perform LLU on multiple processes
  ibm.power_aix.llvupdate:
    action: update
    processes_to_include: 12845566, 9568716

- name: Perform LLU on every process except one
  ibm.power_aix.llvupdate:
    action: update
    include_all: true
    processes_to_exclude: 13828604

- name: Perform LLU on all applicable processes.
  ibm.power_aix.llvupdate:
    action: update
    include_all: true

- name: Clean up kernal state and uncleaned processes
  ibm.power_aix.llvupdate:
    action: clean
"""

RETURN = r"""
msg:
  description: The execution message.
  returned: always
  type: str
stdout:
  description: The standard output.
  returned: If the command failed.
  type: str
stderr:
  description: The standard error.
  returned: If the command failed.
  type: str
cmd:
  description: Command that was run
  returned: always
  type: str
"""

from ansible.module_utils.basic import AnsibleModule
import re

module = None
results = None

####################################################################################
# Helper Functions
####################################################################################


def check_llu_capable(module):
    """
    Checks if the system/process is LLU capable or not.

    arguments:
        module  (dict): Ansible generic module.

    return:
        True - If the system/process is LLU capable.
        False - If the system/process is not LLU capable.

    note:
        Exits with a failure message in case of failure during the command run.
    """

    # Command to check if llu_mode is enabled or disabled
    cmd = "raso -o llu_mode"

    rc, stdout, stderr = module.run_command(cmd)

    results["stdout"] = stdout

    if rc:
        results["stderr"] = stderr
        results["msg"] = "Could not check if the llu_mode is set or not. "
        results["msg"] += f"The following command failed: {cmd}"
        module.fail_json(**results)

    val = (stdout.strip("=")[1]).strip()

    # If llu_mode has value 1 - All LLU-capable processes can run LLU, unless they explicitly disable it
    # if 2 - LLU is disabled by default, and is only possible for processes that explicitly opt-in
    # For 0 - LLU is disabled for all the processes.
    if val == "0":
        results["msg"] = "Value of llu_mode tunable is set to 0."
        results["msg"] += " For Live library update to be performed, you need to set it"
        results["msg"] += " to either 1 or 2."

        return False

    return True


def parse_output(stdout):
    """
    Parse the output of llvupdate command.

    arguments:
      stdout (str) - stdout of llvupdate command

    returns:
      fail_list (list) - List of processes that failed to update.
      success_list  (list) - List of processes that successfully updated.
    """

    fail_list = []
    success_list = []

    stdout = stdout.splitlines()

    flag = 0
    for line in stdout:

        if flag == 1:
            if "LLU Report End" in line:
                flag = 0
                break

            proc = line.split()

            if proc[-1] == "SUCCESS":
                success_list.append(proc[0])
            else:
                fail_list.append(proc[0])

        if "LLU Report" in line:
            flag = 1

    return fail_list, success_list


####################################################################################
# Action Functions
####################################################################################


def preview_llu(module):
    """
    Performs LLU operation in preview mode.

    attributes:
      module (dict): Ansible generic module

    returns:
      msg (str): Message as per the command run

    note:
      Exits with a failure message in case of failure during the command run.
    """

    cmd = ["llvupdate", "-P"]

    if module.params["logfile"]:
        cmd.append(f"-l {module.params['logfile']}")

    rc, stdout, stderr = module.run_command(cmd)

    results["stdout"] = stdout
    results["cmd"] = " ".join(cmd)
    results["rc"] = rc

    if rc:
        results["stderr"] = stderr
        results["msg"] = "LLU operation failed! Check stderr for more details."
        module.fail_json(**results)

    pid_l = []
    path_l = []

    pattern = r"pid\s+(\d+).*?Library needs to be updated\s+(\S+)"
    matches = re.findall(pattern, stdout, re.DOTALL)

    for pid, path in matches:
        pid_l.append(pid)
        if path not in path_l:
            path_l.append(path)

    if pid_l and path_l:
        msg = f"LLU-capable library(s) is new for: {', '.join(pid_l)}."
        msg += f" Following library(s) needs to be updated: {', '.join(path_l)}."
    else:
        msg = " No process requires a Live library Update operation."

    return msg


def perform_llu(module):
    """
    Performs LLU operation: runs the llvupdate command on the system.

    attributes:
      module  (dict): Ansible generic module.

    return:
      msg (str): Message as per the command run.

    note:
        Exits with a failure message in case of failure during the command run.
    """

    cmd = ["llvupdate"]

    p_include = module.params["processes_to_include"]

    if p_include:
        proc = " ".join(p_include)
        cmd.append(f"-p {proc}")

    if module.params["include_all"]:
        cmd.append("-a")

    p_exclude = module.params["processes_to_exclude"]

    if p_exclude:
        proc = " ".join(p_exclude)
        cmd.append(f"-e {proc}")

    if module.params["logfile"]:
        cmd.append(f"-l {module.params['logfile']}")

    if module.params["retries"]:
        cmd.append(f"-n {module.params['retries']}")

    if module.params["timeout"]:
        cmd.append(f"-t {module.params['timeout']}")

    rc, stdout, stderr = module.run_command(cmd)

    results["stdout"] = stdout
    results["cmd"] = " ".join(cmd)
    results["rc"] = rc

    if rc:
        if "No process requires a Live library Update operation." in stdout:
            msg = "No process requires a Live library Update operation. "
            return msg

        results["stderr"] = stderr
        base_msg = "LLU operation failed!"

        # If auto_cleanup is enabled, run it and append its message
        if module.params.get("auto_cleanup"):
            cleanup_msg = perform_cleanup(module)
            base_msg += f" {cleanup_msg}"

        results["msg"] = base_msg
        module.fail_json(**results)

    fail, success = parse_output(stdout)

    if not len(fail):
        msg = f"Live update operation successful for: {', '.join(success)}."
    else:
        msg = f"Live update operation failed for: {', '.join(fail)}."
        if success:
            msg += f" Succeeded for: {', '.join(success)}."

    if module.params["auto_cleanup"]:
        msg += " " + perform_cleanup(module)

    results["changed"] = True

    return msg


def perform_cleanup(module):
    """
    In case of failure during live library update, clean up needs to be performed.
    Attempt to clean up kernel state and also uncleaned processes after a failed Live Library Update operation.

    arguments:
      module  (dict): Generic ansible module

    return:
      success_msg (str): Message signifying successful command run.

    note:
      Exits with a failure message in case the command fails during execution.
    """

    cmd = ["/usr/sbin/cllvupdate", "-u"]

    rc, stdout, stderr = module.run_command(cmd)

    if results["stdout"]:
        results["stdout"] += "\n " + stdout
    else:
        results["stdout"] = stdout

    if results["cmd"]:
        results["cmd"] += ", " + " ".join(cmd)
    else:
        results["cmd"] = cmd

    success_msg = "Successfuly cleaned the kernel state and processes."
    no_change_msg = "No cleanup is required."
    fail_msg = "Failed to clean the kernel state and processes. "
    fail_msg += "Please check stderr for more information."

    if "No clean up is required" in stdout:
        return no_change_msg

    if rc:
        if results["msg"]:
            results["msg"] += " " + fail_msg
        else:
            results["msg"] = fail_msg

        if results["stderr"]:
            results["stderr"] += " " + stderr
        else:
            results["stderr"] += stderr

        module.fail_json(**results)

    return success_msg


def main():
    global module
    global results

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(
                type="str", choices=["update", "preview", "clean"], required=True
            ),
            processes_to_include=dict(type="list", elements="str"),
            include_all=dict(type="bool", default=False),
            processes_to_exclude=dict(type="list", elements="str"),
            logfile=dict(type="str"),
            retries=dict(type="int"),
            timeout=dict(type="int"),
            auto_cleanup=dict(type="bool", default=False),
        ),
    )

    results = dict(
        changed=False,
        msg="",
        stdout="",
        stderr="",
        cmd="",
    )

    # Check if the system is LLU capable or not
    if not check_llu_capable(module):
        results["msg"] = "The system is not LLU capable: 'llu_mode' is set to 0."
        results["msg"] += " Please change its value and try again."

        module.fail_json(**results)

    action = module.params["action"]

    if action == "clean":
        # Perform cleanup
        msg = perform_cleanup(module)

        if msg == "No cleanup is required.":
            results["changed"] = False
        else:
            results["changed"] = True

    elif action == "preview":

        results["msg"] = preview_llu(module)
        results["changed"] = False

    else:
        # Case for action - update
        include_proc = module.params["processes_to_include"]
        include_all = module.params["include_all"]
        exclude_proc = module.params["processes_to_exclude"]

        if not include_proc and not include_all and not exclude_proc:
            results["msg"] = (
                "You need to specify one of these: processes_to_include, include_all, processes_to_exclude"
            )
            results["msg"] += " for LLU operation to be performed."

            module.fail_json(**results)

        if exclude_proc and not include_all:
            results["msg"] = "LLU Failed: "
            results[
                "msg"
            ] += "'processes_to_exclude' needs to be used with 'include_all'."

            module.fail_json(**results)

        results["msg"] = perform_llu(module)

        if "failed" in results["msg"]:
            module.fail_json(**results)

    results["msg"] += f" Action '{action}' performed successfully."

    module.exit_json(**results)


if __name__ == "__main__":
    main()
