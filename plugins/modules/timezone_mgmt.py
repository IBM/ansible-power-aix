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
module: timezone_mgmt
short_description: Manage timezone for AIX systems.
description:
- This module is useful for viewing and updating timezones.
- This module is a wrapper around tzupg.pl script.
version_added: '2.2.0'
requirements:
- AIX >= 7.3.3
- Python >= 3.9
options:
  action:
    description:
    - Specifies which action needs to be performed.
      C(list_versions) lists the available timezone versions and the current version;
      C(update_timezone) updates the timezone database;
      C(print_updated_zones) prints the updated zones from the system;
      C(update_timezone_offline) updates timezone using the provided timezone DB;
    type: str
    choices: [ list_versions, update_timezone, print_updated_zones, update_timezone_offline ]
    required: true
  timezone:
    description:
    - Specifies the timezone database that the system needs to be updated to.
    - Required for I(action=update_timezone).
    type: str
    required: false
  db_location:
    description:
    - Specifies the location of tar ball containg timezone DB.
    - This needs be provided with I(action=update_timezone_offline)
    - Only works when I(action=update_timezone_offline) is set
    type: str
    required: false
notes:
  - You can refer to the Community blog for additional information on the commands used at
    U(https://community.ibm.com/community/user/blogs/ravindra-shinde/2024/12/13/time-zone-update-tool-tz).
"""

EXAMPLES = r"""
- name: List all available versions of timezones
  ibm.power_aix.timezone_mgmt:
    action: list_versions

- name: Update timezone
  ibm.power_aix.timezone_mgmt:
    action: update_timezone
    timezone: 2025b

- name: Fetch updated zones
  ibm.power_aix.timezone_mgmt:
    action: print_updated_zones
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
import re
# import os.path

results = dict(
    changed=False,
    cmd="",
    msg="",
    rc="",
    stdout="",
    stderr="",
    timezone_details={},
)

# This is required as prompts are different for versions of tool (before and after 2537A_73H)
is_new = False

expectPrompts = {
    "list_version": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "set env(TERM) xterm; "
        "spawn /usr/sbin/tzupg.pl; "
        'expect \\"Enter your choice (1/2/3): \\"; '
        'send \\"1\\r\\"; '
        "expect { "
        "    -re \\\"Available Versions:[\\r\\n]+(.*)Enter the corresponding index number or 'x' to go back to the main menu:\\\" { "
        "        set output $expect_out(1,string); "
        "        puts $output; "
        "    } "
        "}; "
        'send \\"x\\r\\"; '
        'expect \\"Enter your choice (1/2/3): \\"; '
        'send \\"3\\r\\"; '
        "expect { "
        "    -re {Exiting} { exp_continue } "
        "    eof {} "
        "    timeout { } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
    "list_version_new": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "set env(TERM) xterm; "
        "spawn /usr/sbin/tzupg.pl; "
        'expect \\"Enter your choice (1/2/3/4): \\"; '
        'send \\"1\\r\\"; '
        "expect { "
        "    -re \\\"Available Versions:[\\r\\n]+(.*)Enter the corresponding index number or 'x' to go back to the main menu:\\\" { "
        "        set output $expect_out(1,string); "
        "        puts $output; "
        "    } "
        "}; "
        'send \\"x\\r\\"; '
        'expect \\"Enter your choice (1/2/3/4): \\"; '
        'send \\"4\\r\\"; '
        "expect { "
        "    -re {Exiting} { exp_continue } "
        "    eof {} "
        "    timeout { } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
    "update_timezone": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "set env(TERM) xterm; "
        "spawn /usr/sbin/tzupg.pl; "
        'expect \\"Enter your choice (1/2/3): \\"; '
        'send \\"1\\r\\"; '
        "expect { "
        "    -re \\\"Available Versions:[\\r\\n]+(.*)Enter the corresponding index number or 'x' to go back to the main menu:\\\" { "
        "        set output $expect_out(1,string); "
        "        puts $output; "
        "    } "
        "}; "
        'send \\"%s\\r\\"; '
        'expect \\"Press enter to go back to main menu! \\"; '
        'send \\"\\r\\"; '
        'expect \\"Enter your choice (1/2/3): \\"; '
        'send \\"3\\r\\"; '
        "expect { "
        "    -re {Exiting} { exp_continue } "
        "    eof {} "
        "    timeout { } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
    "update_timezone_new": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "set env(TERM) xterm; "
        "set timeout -1;"
        "spawn /usr/sbin/tzupg.pl; "
        'expect \\"Enter your choice (1/2/3/4): \\"; '
        'send \\"1\\r\\"; '
        "expect { "
        '    -re \\"Available Versions:[\\r\\n]+(.*)Current database version is .*[\\r\\n]+\\" { '
        "        set output $expect_out(1,string); "
        "        puts $output; "
        "    } "
        "} "
        "expect \\\"Enter the corresponding index number or 'x' to go back to the main menu: \\\"; "
        'send \\"%s\\r\\"; '
        'expect \\"Press enter to go back to main menu! \\"; '
        'send \\"\\r\\"; '
        'expect \\"Enter your choice (1/2/3/4): \\"; '
        'send \\"4\\r\\"; '
        "expect { "
        '    -re \\"Exiting.*\\" { '
        "        expect eof "
        "    } "
        "    eof { "
        "        # Child exited quickly without Exiting text "
        "    } "
        "    timeout { "
        "        catch { exec kill -TERM $child_pid }; "
        "        after 2000; "
        "        catch { exec kill -KILL $child_pid }; "
        "        exit 1 "
        "    } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
    "update_timezone_offline": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "exp_internal 1;"  # <-- Added internal debugging
        "set timeout 30;"  # <-- Set a global timeout for expect
        "set env(TERM) xterm; "
        "spawn /usr/sbin/tzupg.pl; "
        # 1. Expect Main Menu prompt
        'expect -re \\"Enter your choice \\(1/2/3/4\\):\\"; '
        'send \\"2\\r\\"; '
        # 2. Expect path prompt
        'expect \\"Please enter the full local path where tzdata\\"; '
        'send \\"%s\\r\\"; '
        # 3. Expect the 'Press Enter to continue' prompt
        'expect -re \\"Press Enter to continue.*\\"; '
        'send \\"\\r\\"; '
        'send \\"\\r\\"; '
        'send \\"4\\r\\"; '
        "sleep 1; "  # Added a short pause to ensure the terminal buffer is clear before the final command
        "expect { "
        "    eof { "
        "        # Child exited "
        "    } "
        "    timeout { "
        "        # Failure: Timeout occurred, forcefully kill the process "
        "        catch { exec kill -TERM $child_pid }; "
        "        after 2000; "
        "        catch { exec kill -KILL $child_pid }; "
        "        exit 1 "
        "    } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
    "print_updated_zones": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "exp_internal 1;"
        "set timeout 30;"
        "set env(TERM) xterm; "
        "spawn /usr/sbin/tzupg.pl; "
        'expect \\"Enter your choice (1/2/3): \\"; '
        'send \\"2\\r\\"; '
        "expect { "
        "  -re {## Updated Zones\\r?\\n((.|\\r|\\n)*?)\\r?\\nDatabase Version:\\s*(\\S+)} { "
        "      puts $expect_out(1,string);  # zones block (group 1) "
        "      puts \\nDBVER:$expect_out(3,string); "
        "  } "
        "  timeout { exit 2 } "
        "} "
        'expect \\"Enter your choice (1/2/3): \\"; '
        'send \\"3\\r\\"; '
        "expect { "
        "    -re {Exiting} { exp_continue } "
        "    eof {} "
        "    timeout { } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
    "print_updated_zones_new": (
        '/usr/bin/expect -c "'
        "log_user 1;"
        "set env(TERM) xterm; "
        "spawn /usr/sbin/tzupg.pl; "
        'expect \\"Enter your choice (1/2/3/4): \\"; '
        'send \\"3\\r\\"; '
        "expect { "
        "  -re {## Updated Zones\\r?\\n((.|\\r|\\n)*?)\\r?\\nDatabase Version:\\s*(\\S+)} { "
        "      puts $expect_out(1,string);  # zones block (group 1) "
        "      puts \\nDBVER:$expect_out(3,string); "
        "  } "
        "  timeout { exit 2 } "
        "} "
        'expect \\"Enter your choice (1/2/3/4): \\"; '
        'send \\"4\\r\\"; '
        "expect { "
        "    -re {Exiting} { exp_continue } "
        "    eof {} "
        "    timeout { } "
        "} "
        "close; "
        "wait; "
        'exit 0;"'
    ),
}


####################################################################################
# Helper Functions
####################################################################################


def check_tzupg(module):
    """
    Utility function to check if tzupg is available or not.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
        True    (bool): If the tool is available.
        False   (bool): If the tool is not available.
    """
    cmd = "which /usr/sbin/tzupg.pl"

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        return False

    return True


def check_db_exists(module):
    """
    Utility function to check if the database exists at the provided location

    arguments:
      module  (dict): Ansible module argument spec

    returns:
      True  (bool): If the DB exists at the location
      False (bool): If the DB does not exist at the provided location

    """

    cmd = f"ls {module.params['db_location']}"

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        return False

    return True


def is_new_script(module):
    """
    Utility function to find which version of tzupg will be used.

    arguemnts:
      module (dict): Ansible module argument spec.

    returns:
      True (bool): In case new version of tzupg is being used.
      False (bool): In case older verison of tzupg is being used.

    note:
      - In case of failure during command run, module exits with a failure.
    """

    # Get oslevel of the system
    cmd = "oslevel -s"

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        results["stdout"] = stdout
        results["stderr"] = stderr
        results["msg"] = f"Following command failed: {cmd}"
        module.fail_json(**results)

    level = int("".join(stdout.split("-")[:2]))

    # Get weekly build from proc/version
    cmd = "cat /proc/version"

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        results["stdout"] = stdout
        results["stderr"] = stderr
        results["msg"] = f"Following command failed: {cmd}"
        module.fail_json(**results)

    # wb = int(stdout.strip().splitlines()[-1].split()[-1].split("_")[0][:-1])

    match = re.search(r"(\d+)[A-Za-z]*_", stdout)
    if match:
        wb = int(match.group(1))
    else:
        results["msg"] = "Could not retrieve the weekly build of the system."
        module.fail_json(**results)

    if wb >= 2537 and level >= 730004:
        return True

    return False


####################################################################################
# Action Functions
####################################################################################


def list_versions(module):
    """
    Lists the available timezone versions in the system.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    cmd = expectPrompts["list_version"]

    if is_new:
        cmd = expectPrompts["list_version_new"]

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": "Failed to retrieve available timezone versions.",
            "rc": rc,
            "stderr": stderr,
        }

    if "Another session of the tool is running" in stdout:
        results["msg"] = (
            "Another session of the tool is running, please close it and try again."
        )
        module.fail_json(**results)

    # --- Parse versions and current version ---
    available = re.findall(r"(\d+)\s*:\s*([\w\d]+)", stdout)
    current = re.search(r"Current database version is\s+([\w\d]+)", stdout)

    payload = {
        "changed": False,
        "msg": "Successfully retrieved available versions.",
        "rc": 0,
        "stdout": stdout,
        # omit stderr on success to avoid failed_when rules tripping
        "timezone_details": {
            "available_versions": [v for k, v in available],
            "current_version": current.group(1) if current else "Unknown",
        },
    }
    return payload


def update_timezone(module):
    """
    Updates the timezone database of the system.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    tz = module.params["timezone"]

    versions = list_versions(module)

    tz_details = versions["timezone_details"]
    available_tz = tz_details["available_versions"]
    current_tz = tz_details["current_version"]

    if tz == current_tz:
        return {
            "changed": False,
            "msg": "No need to change, provided timezone is already set.",
        }

    ind = -1
    for i in range(len(available_tz)):
        if available_tz[i] == tz:
            ind = i
            break

    if ind == -1:
        return {
            "failed": True,
            "msg": "Timezone not found, please enter a valid timezone.",
        }

    cmd = expectPrompts["update_timezone"] % (ind)

    if is_new:
        cmd = expectPrompts["update_timezone_new"] % (ind)

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": "Failed to update the timezone version.",
            "rc": rc,
            "stderr": stderr,
        }

    payload = {
        "changed": True,
        "msg": "Successfully updated the timezone.",
        "rc": 0,
        "stdout": stdout,
    }

    return payload


def update_timezone_offline(module):
    """
    Updates the timezone version using DB that is stored offline

    arguments:
      module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    db_loc = module.params["db_location"]

    cmd = expectPrompts["update_timezone_offline"] % (db_loc)

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": "Failed to update the timezone version. Check stderr for more information",
            "rc": rc,
            "stderr": stderr,
        }

    if "Another session of the tool is running" in stdout:
        results["msg"] = (
            "Another session of the tool is running, please close and try again."
        )
        module.fail_json(**results)

    payload = {
        "changed": True,
        "msg": "Successfully updated timezone using the provided DB location.",
        "rc": 0,
        "stdout": stdout,
    }

    if "The system is already installed with" in stdout:
        payload["changed"] = False
        payload["msg"] = "Nothing to update,"
        payload[
            "msg"
        ] += " the system is already installed with the provided database version."

    return payload


def print_updated_zones(module):
    """
    Lists the updated zones from the system.

    arguments:
        module  (dict): Ansible module argument spec.

    returns:
      payload (dict): Contains information about the command execution.

    note:
      - In case of command failure, module exits with fail_json.
    """

    cmd = expectPrompts["print_updated_zones"]

    if is_new:
        cmd = expectPrompts["print_updated_zones_new"]

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        return {
            "failed": True,
            "msg": "Failed to retrieve updated zones.",
            "rc": rc,
            "stderr": stderr,
        }

    updated_zones = []

    flag = 0
    for line in stdout.splitlines():
        if flag == 1:
            if "Database Version" in line:
                break

            if len(line):
                updated_zones.append(line)

        if "Updated Zones" in line:
            flag = 1

    payload = {
        "changed": False,
        "msg": "Successfully retrieved the updated timezone.",
        "rc": 0,
        "stdout": stdout,
        "timezone_details": {"updated_zones": updated_zones},
    }

    return payload


####################################################################################
# Main Function
####################################################################################


def main():
    global is_new
    global results

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            action=dict(
                type="str",
                choices=[
                    "list_versions",
                    "print_updated_zones",
                    "update_timezone",
                    "update_timezone_offline",
                ],
                required=True,
            ),
            timezone=dict(type="str"),
            db_location=dict(type="str"),
        ),
    )

    if not check_tzupg(module):
        results[
            "msg"
        ] += (
            "Please check the AIX version. 'tzupg' tool is not available on the system."
        )
        module.fail_json(**results)

    if is_new_script(module):
        is_new = True

    action = module.params["action"]

    if action == "update_timezone":
        tz = module.params.get("timezone")
        if not tz:
            results["msg"] = (
                "You need to provide the timezone parameter for action 'update_timezone'"
            )
            module.fail_json(**results)

        results = update_timezone(module)

    elif action == "print_updated_zones":
        results = print_updated_zones(module)

    elif action == "update_timezone_offline":
        if not is_new:
            results["msg"] = (
                "This functionality is only available for version '2537A_73H' and higher."
            )
            results["msg"] += " Please check the version and try again."
            module.fail_json(**results)

        if not module.params["db_location"]:
            results["msg"] = (
                "You need to provide 'db_location' for updating timezone offline."
            )
            module.fail_json(**results)

        if not check_db_exists(module):
            results["msg"] = (
                "The database does not exist at the provided location. Please check and retry."
            )
            module.fail_json(**results)

        results = update_timezone_offline(module)

    else:
        results = list_versions(module)

    if results.get("failed"):
        module.fail_json(**results)
    else:
        module.exit_json(**results)


if __name__ == "__main__":
    main()
