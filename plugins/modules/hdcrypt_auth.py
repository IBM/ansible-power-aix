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
module: hdcrypt_auth
short_description: Controls authentication methods
description:
- This module is used for managing authentication methods for logical volumes.
- This module is a wrapper around hdcryptmgr command.
version_added: '2.1.0'
requirements:
- AIX >= 72X
- Python >= 3.6
options:
  action:
    description:
    - Specifies which operation needs to be performed.
      C(initialize) initializes master key for data encryption;
      C(unlock) authenticates to unlock master key of the device;
      C(add) adds additional authentication methods;
      C(check) checks validity of an authentication method;
      C(delete) removes an authentication method;
    type: str
    choices: [ initialize, unlock, add, check, delete ]
    required: true
  device:
    description:
    - Specifies the device for which you want to manage the authentication methods.
    type: str
    required: false
    default: null
  auth_name:
    description:
    - Specifies the name of the authentication method.
    type: str
    required: false
    default: null
  auth_index:
    description:
    - Specifies the index of the authentication method upon which C(action) needs to be performed.
    type: int
    required: false
  auth_detail:
    description:
    - Specifies any additional information about the key-protection method
    - In case of keyfile authentication method, input path to the authentication key file
      needs to be provided.
    type: str
  auto_key_protection:
    description:
    - Authenticates to the encrypted LV by using the automatic key-protection methods that
      do not require any user inputs.
    type: bool
    default: false
  auth_type:
    description:
    - Specifies the type of authentication method you want to perform the C(action) upon.
      C(pwd) specifies passphrase authentication method.
      C(keyfile) specifies key file based authentication method.
      C(pks) specifies PKS based authentication method.
    type: str
    choices: ["pwd", "keyfile", "pks"]
    required: false
  password:
    description:
    - Specifies the password in case when C(auth_type) is set to pwd.
    type: str
    default: null
  force:
    description:
    - Specifies if -f flag should be used with the command to forcefully perform the action.
    type: bool
    default: false
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.2?topic=h-hdcryptmgr-command).
"""

EXAMPLES = r"""
- name: "Initialize a authentication method"
  ibm.power_aix.hdcrypt_auth:
    action: initialize
    device: testlv
    auth_name: initpwd
    password: testpass

- name: Add a phasphrase authentication method
  ibm.power_aix.hdcrypt_auth:
    action: add
    device: testlv
    auth_name: pwd2
    auth_type: pwd
    password: 'testpass'

- name: Add a keyfile authentication method
  ibm.power_aix.hdcrypt_auth:
    action: add
    device: testlv
    auth_name: file_2
    auth_type: keyfile
    auth_detail: /key2

- name: Add a pks authentication method
  ibm.power_aix.hdcrypt_auth:
    action: add
    device: testlv
    auth_name: test_pks
    auth_type: pks

- name: Delete a passphrase auth method
  ibm.power_aix.hdcrypt_auth:
    action: delete
    device: testlv
    auth_type: pwd
    auth_name: pwd5
    password: "testpass"

- name: Delete a pks auth method
  ibm.power_aix.hdcrypt_auth:
    action: delete
    device: testlv
    auth_type: pks
    auth_name: test_pks

- name: Delete a keyfile auth method
  ibm.power_aix.hdcrypt_auth:
    action: delete
    device: testlv
    auth_type: keyfile
    auth_name: file_2
    auth_detail: /key2

- name: Unlock using keyfile authentication method
  ibm.power_aix.hdcrypt_auth:
    action: unlock
    device: testlv
    auth_type: keyfile
    auth_detail: /key2

- name: Check auth method passphrase
  ibm.power_aix.hdcrypt_auth:
    action: check
    device: testlv
    auth_name: pwd5
    auth_type: pwd
    password: 'testpass'

- name: Check auth method passphrase using keyfile
  ibm.power_aix.hdcrypt_auth:
    action: check
    device: testlv
    auth_name: file2
    auth_type: keyfile
    auth_detail: /key2

- name: Check pks authentication method using pks
  ibm.power_aix.hdcrypt_auth:
    action: check
    device: testlv
    auth_name: test_pks
    auth_type: pks
"""

RETURN = r"""
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Successfully unlocked the authentication method, command:
    /usr/sbin/hdcryptmgr authunlock -t pwd testlv. Action(unlock) completed successfully."
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: When an error is encountered while running the command.
    type: int
stdout:
    description: The standard output of the command.
    returned: always
    type: str
stderr:
    description: The standard error of the command.
    returned: When an error is encountered while running the command.
    type: str
changed:
    description: Shows if any change was made.
    returned: always
    type: bool
"""

from ansible.module_utils.basic import AnsibleModule
import re

results = dict(
    changed=False,
    cmd="",
    msg="",
    rc=0,
    stdout="",
    stderr="",
    lv_facts="",
    vg_facts="",
    pv_facts="",
    meta_facts="",
    conv_facts="",
)


expectPrompts = {
    "authinit_weak_pwd": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase:"; '
        'send "%s\\r"; '
        'expect "Please confirm usage of an unsecure passphrase (y|n): "; '
        'send "y\\r"; '
        'expect "Confirm Passphrase:"; '
        'send "%s\\r"; '
        "set timeout -1; "
        'expect "Passphrase authentication method with name \\"initpwd\\" added successfully."\''
    ),
    "authinit_strong_pwd": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase: "; '
        'send "%s\\r"; '
        'expect "Confirm Passphrase: "; '
        'send "%s\\r"; '
        "set timeout -1; "
        'expect "Passphrase authentication method with name \\"initpwd\\" added successfully."\''
    ),
    "authadd_weak_pwd": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase:"; '
        'send "%s\\r"; '
        'expect "Please confirm usage of an unsecure passphrase (y|n): "; '
        'send "y\\r"; '
        'expect "Confirm Passphrase:"; '
        'send "%s\\r"; '
        "set timeout -1; "
        'expect "Passphrase authentication method with name \\"%s\\" added successfully."\''
    ),
    "authadd_strong_pwd": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase: "; '
        'send "%s\\r"; '
        'expect "Confirm Passphrase: "; '
        'send "%s\\r"; '
        "set timeout -1; "
        'expect "Passphrase authentication method with name \\"%s\\" added successfully."\''
    ),
    "unlock": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase: "; '
        'send "%s\\r"; '
        'expect "Wrong passphrase. Try again (2/3)"; '
        'expect "Enter Passphrase: "; '
        'send "wrong\\r"; '
        'expect "Wrong passphrase. Try again (3/3)"; '
        'expect "Enter Passphrase: "; '
        'send "wrong\\r"; '
        "set timeout -1; "
        'expect "hdcryptmgr authunlock failed for device %s." { exit 5 } \''
    ),
    "authdelete": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase: "; '
        'send "%s\\r"; '
        'expect "Wrong passphrase. Try again (2/3)"; '
        'expect "Enter Passphrase: "; '
        'send "wrong\\r"; '
        'expect "Wrong passphrase. Try again (3/3)"; '
        'expect "Enter Passphrase: "; '
        'send "wrong\\r"; '
        "set timeout -1; "
        'expect "3020-0386 Unable to check selected authentication method." { exit 5 } \''
    ),
    "authcheck": (
        "/usr/bin/expect -c '"
        "spawn %s; "
        'expect "Enter Passphrase:"; '
        'send "%s\\r"; '
        'expect "Enter Passphrase:"; '
        'send "Wrong\\r"; '
        'expect "Enter Passphrase:"; '
        'send "Wrong\\r"; '
        "set timeout -1; "
        'expect "3020-0464 hdcryptmgr authcheck failed for device" { exit 5 } \''
    ),
}


####################################################################################
# Helper Functions
####################################################################################


def lv_exists(module, name):
    """
    Checks if the logical volume exists.

    arguments:
        module: Ansible module argument spec.
        name: Name of the logical volume.

    returns:
        True: If the logical volume exists.
        False: If the logical volume does not exist.
    """

    # Command to get information about a LV(In this case, used to check existence)
    cmd = f"lslv {name}"

    rc, stdout, stderr = module.run_command(cmd)

    results["cmd"] = cmd
    results["rc"] = rc

    if rc:
        return False

    return True


def check_password_strength(password):
    """
    Utility function to check the strength of provided password.

    arguments:
        password (str) - User provided password.

    returns:
        true - If the password is strong.
        false - If the password is not strong.
    """

    # pattern = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[(){}_~`'!@#$%^&*+=|:;<>,?/ \.\-\[\]\"\\])"
    pattern = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[~`!@#$%^&*()_\-+={\[}\]|\\:;\"'<,>\.?/ ])"
    weak_pass = (len(password) < 12) or (re.search(pattern, password) is None)
    if weak_pass:
        return False
    return True


def get_auth_details(module, device):
    """
    Utility function to retrieve information about an LV.

    aruments:
        module (dict) - The generic ansible module
        device (str) - Name of the LV for which information needs to be retrieved.

    returns:
        curr_auth (dict) - Dictionary containing information about the LV.
    """

    # The function will create a dictionary like this:
    # curr_auth = {
    #     testlv:{
    #         "initialized": "yes",
    #         "locked": "no",
    #         "passphrase": ["initpwd", "pwd2"],
    #         "pks": ["initpks"],
    #         "keyfile": ["key1", "key2"],
    #         "index": ['1','2','3','4','5'],
    #         "auth_names": ["initpwd", "pwd2", "initpks", "key1", "key2"]
    #     }
    # }

    curr_auth = dict()
    curr_auth[device] = {}

    cmd = "hdcryptmgr showlv"
    cmd += f" {device} -v"

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        results["stderr"] = stderr
        results["rc"] = rc
        results["msg"] = (
            "Could not get the details about current authentication methods."
        )
        module.fail_json(**results)

    stdout_lines = stdout.splitlines()

    for line in stdout_lines[1:]:
        line = line.split()

        if line[0] == device:
            curr_auth[device]["initialized"] = "no"
            curr_auth[device]["locked"] = "no"

            if line[1] != "uninitialized":
                curr_auth[device]["initialized"] = "yes"

                if line[1] == "locked":
                    curr_auth[device]["locked"] = "yes"
            else:
                break

        elif "#" in line[0]:
            auth_index = line[0]
            auth_type = line[1].lower()
            if len(line) > 2:
                auth_name = line[2]
            else:
                auth_name = None

            # Storing index and auth_name in different lists so that searching for them becomes easy
            if auth_type not in curr_auth[device].keys():
                curr_auth[device][auth_type] = []
            if auth_name:
                curr_auth[device][auth_type].append(auth_name)

            if "index" not in curr_auth[device].keys():
                curr_auth[device]["index"] = []

            if "auth_names" not in curr_auth[device].keys():
                curr_auth[device]["auth_names"] = []

            # Storing all the indices and names for easily searching them
            curr_auth[device]["index"].append(auth_index[1:])
            if auth_name:
                curr_auth[device]["auth_names"].append(auth_name)

        else:
            continue

    return curr_auth


####################################################################################
# Action Handler Functions
####################################################################################


def auth_init(module):
    """
    Initializes the primary key and encryption metadata for an encrypted volume.

    arguements:
        module (dict) - Ansible generic mdoule.

    returns:
        success_msg (str) - Success message if the command runs successfully.
        Fails if the command returns non-zero return code.
    """
    device = module.params["device"]

    # Check if it is uninitialized
    curr_auth = get_auth_details(module, device)

    if curr_auth[device]["initialized"] == "yes":
        results["msg"] = "No need to initialize, the LV is already initialized."
        module.exit_json(**results)

    cmd = ["/usr/sbin/hdcryptmgr authinit"]

    if module.params["auth_detail"]:
        auth_detail = module.params["auth_detail"]
        cmd.append(f"-e {auth_detail}")

    if module.params["auth_name"]:
        auth_name = module.params["auth_name"]
        cmd.append(f"-n {auth_name}")

    cmd.append(device)

    password = module.params["password"]

    joined_cmd = " ".join(cmd)

    # Creating the messages before using expect as it can manipulate the actual command.
    success_msg = (
        f"Successfully initialized authentication method, command: {joined_cmd}"
    )
    fail_msg = f"The following command failed: {joined_cmd}. Check stderr for more information."

    if not check_password_strength(password):
        cmd = expectPrompts["authinit_weak_pwd"] % (joined_cmd, password, password)
    else:
        cmd = expectPrompts["authinit_strong_pwd"] % (joined_cmd, password, password)

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        results["stderr"] = stderr
        results["rc"] = rc
        results["msg"] = fail_msg
        module.fail_json(**results)

    return success_msg


def auth_add(module):
    """
    Adds an additional key-protection method to an encrypted volume in which a
    key-protection method is already initialized.

    arguements:
        module (dict) - Ansible generic mdoule.

    returns:
        success_msg (str) - Success message if the command runs successfully.
        Fails if the command returns non-zero return code.
    """
    device = module.params["device"]

    # Get the current auth details of the LV
    curr_auth = get_auth_details(module, device)

    # You can not add authentication methods until the LV has been initialized.
    if curr_auth[device]["initialized"] == "no":
        results["msg"] = (
            "The provided LV is uninitialized, you can not add authentication methods."
        )
        module.fail_json(**results)

    cmd = "/usr/sbin/hdcryptmgr authadd"

    type = module.params["auth_type"]
    if not type:
        results["msg"] = "You need to specify the type of authentication method to use."
        module.fail_json(**results)

    cmd += f" -t {type}"

    method_detail = module.params["auth_detail"]
    if method_detail:
        cmd += f" -m {method_detail}"
    else:
        if type == "keyfile":
            results["msg"] = (
                "You need to provide the key file's location in auth_detail, when auth_type is set to keyfile."
            )
            module.fail_json(**results)

    name = module.params["auth_name"]
    if name:
        if (
            "auth_names" in curr_auth[device].keys()
            and name in curr_auth[device]["auth_names"]
        ):
            results["msg"] = (
                "The provided authentication method's name is already present, kindly use a different one."
            )
            module.fail_json(**results)

        cmd += f" -n {name}"

    cmd += f" {device}"

    # Creating the messages before using expect as it can manipulate the actual command.
    success_msg = f"Successfully added authentication method, command: {cmd}"
    fail_msg = (
        f"The following command failed: {cmd}. Check stderr for more information."
    )

    # For PKS or file, it does not prompt for inputs. Just in case of passphrase/pwd
    if type == "pwd":

        password = module.params["password"]

        if password != "" and not password:
            results["msg"] = "In case of pwd auth type, you need to provide password."
            module.fail_json(**results)

        if not check_password_strength(password):
            cmd = expectPrompts["authadd_weak_pwd"] % (cmd, password, password, name)
        else:
            cmd = expectPrompts["authadd_strong_pwd"] % (cmd, password, password, name)

    else:
        # Check if pks already exists
        if type == "pks":
            if "pks" in curr_auth[device].keys():
                results["msg"] = (
                    "PKS authentication method already exists, can not add a new one."
                )
                module.fail_json(**results)

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        results["stderr"] = stderr
        results["rc"] = rc
        results["msg"] = fail_msg
        module.fail_json(**results)

    return success_msg


def auth_delete(module):
    """
    Removes an initiated key-protection method.

    arguements:
        module (dict) - Ansible generic mdoule.

    returns:
        success_msg (str) - Success message if the command runs successfully.
        Fails if the command returns non-zero return code.
    """
    device = module.params["device"]

    # Get information about current authentication methods
    curr_auth = get_auth_details(module, device)

    cmd = "/usr/sbin/hdcryptmgr authdelete"

    type = module.params["auth_type"]
    if type:
        cmd += f" -t {type}"
    else:
        results["msg"] = (
            "Please provide the authentication type of the method that you want to delete."
        )
        module.fail_json(**results)

    auth_detail = module.params["auth_detail"]
    if auth_detail:
        cmd += f" -m {auth_detail}"

    index = module.params["auth_index"]
    if index:
        if (
            "index" not in curr_auth[device].keys()
            or str(index) not in curr_auth[device]["index"]
        ):
            results["msg"] = (
                "The provided auth_index does not exist for this device's methods."
            )
            module.fail_json(**results)

        cmd += f" -i {index}"

    name = module.params["auth_name"]
    if name:
        if (
            "auth_names" not in curr_auth[device].keys()
            or name not in curr_auth[device]["auth_names"]
        ):
            results["msg"] = (
                "The provided auth_name does not exist for this device's methods."
            )
            module.fail_json(**results)

        cmd += f" -n {name}"

    if not name and not index:
        results["msg"] = (
            "You need to either provide the name or index of the method that you want to delete."
        )
        module.fail_json(**results)

    if module.params["force"]:
        cmd += " -f"

    cmd += f" {device}"

    # Creating the messages before using expect as it can manipulate the actual command.
    success_msg = f"Successfully deleted the authentication method, command: {cmd}"
    fail_msg = (
        f"The following command failed: {cmd}. Check stderr for more information."
    )

    if type == "pwd":
        password = module.params["password"]
        if password != "" and not password:
            results["msg"] = "In case of pwd auth type, you need to provide password."
            module.fail_json(**results)

        cmd = expectPrompts["authdelete"] % (cmd, password)
    else:
        if type == "keyfile" and not auth_detail:
            results["msg"] = (
                "You need to provide the location of key file with type=keyfile."
            )
            module.fail_json(**results)

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        if rc == 5:
            results["msg"] = (
                "Could not delete the auth method, incorrect password provided."
            )
        else:
            results["msg"] = fail_msg

        results["stderr"] = stderr
        results["rc"] = rc
        module.fail_json(**results)

    return success_msg


def auth_unlock(module):
    """
    Authenticates to the encrypted volume and unlocks the encrypted volumes.

    arguements:
        module (dict) - Ansible generic mdoule.

    returns:
        success_msg (str) - Success message if the command runs successfully.
        Fails if the command returns non-zero return code.
    """

    device = module.params["device"]

    curr_auth_details = get_auth_details(module, device)

    # Check if locked or not
    if curr_auth_details[device]["locked"] == "no":
        results["msg"] = "The provided device is already unlocked."
        module.exit_json(**results)

    cmd = ["/usr/sbin/hdcryptmgr authunlock"]

    auth_type = module.params["auth_type"]
    if not auth_type:
        results["msg"] = "You need to provide the auth_type that you want to use."
        module.fail_json(**results)

    cmd.append(f"-t {auth_type}")

    auth_detail = module.params["auth_detail"]
    if auth_detail:
        cmd.append(f"-m {auth_detail}")

    if module.params["auto_key_protection"]:
        if auth_type or auth_detail:
            results["msg"] = (
                "Can not use auth_detail or auth_type when auth_key_protection is set."
            )
            module.fail_json(**results)
        cmd.append("-A")

    cmd.append(device)

    cmd = " ".join(cmd)

    # Creating the messages before using expect as it can manipulate the actual command.
    success_msg = f"Successfully unlocked the authentication method, command: {cmd}"
    fail_msg = (
        f"The following command failed: {cmd}. Check stderr for more information."
    )

    if auth_type == "pwd":
        password = module.params["password"]

        if password != "" and not password:
            results["msg"] = "You need to provide password in case of pwd auth_type"
            module.fail_json(**results)

        cmd = expectPrompts["unlock"] % (cmd, password, device)
    else:
        if auth_type == "keyfile" and not auth_detail:
            results["msg"] = (
                "You need to provide the location in auth_detail, when type = keyfile."
            )
            module.fail_json(**results)

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        if rc == 5:
            results["msg"] = (
                "Could not unlock the device using the provided auth method, incorrect password provided."
            )
        else:
            results["msg"] = fail_msg

        results["stderr"] = stderr
        results["rc"] = rc
        module.fail_json(**results)

    return success_msg


def auth_check(module):
    """
    Checks the validity of an authentication method.

    arguements:
        module (dict) - Ansible generic mdoule.

    returns:
        success_msg (str) - Success message if the command runs successfully.
        Fails if the command returns non-zero return code.
    """
    cmd = ["/usr/sbin/hdcryptmgr authcheck"]

    auth_type = module.params["auth_type"]
    if auth_type:
        cmd.append(f"-t {auth_type}")
    else:
        results["msg"] = "You need to provide the authentication type for action=check."
        module.fail_json(**results)

    auth_detail = module.params["auth_detail"]
    if auth_detail:
        cmd.append(f"-m {auth_detail}")

    index = module.params["auth_index"]
    if index:
        cmd.append(f"-i {index}")

    name = module.params["auth_name"]
    if name:
        cmd.append(f"-n {name}")

    cmd.append(module.params["device"])

    cmd = " ".join(cmd)

    success_msg = f"Successfully checked the authentication method, command: {cmd}"
    fail_msg = (
        f"The following command failed: {cmd}. Check stderr for more information."
    )

    if auth_type == "pwd":
        password = module.params["password"]

        if password != "" and not password:
            results["msg"] = "You need to provide password in case of pwd auth_type"
            module.fail_json(**results)

        cmd = expectPrompts["authcheck"] % (cmd, password)
    else:
        if auth_type == "keyfile":
            if not index and not name:
                results["msg"] = (
                    "You need to provide either index or name in case of keyfile auth_type."
                )
                module.fail_json(**results)

            if not auth_detail:
                results["msg"] = (
                    "You need to provide keyfile path in auth_detail in case of keyfile auth_type."
                )
                module.fail_json(**results)

    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        if rc == 5:
            results["msg"] = (
                "Could not check the auth method, incorrect password provided."
            )
        else:
            results["msg"] = fail_msg

        results["stderr"] = stderr
        results["rc"] = rc
        module.fail_json(**results)

    return success_msg


####################################################################################
# Main Function
####################################################################################


def main():

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            action=dict(
                type="str",
                choices=["initialize", "unlock", "add", "check", "delete"],
                required=True,
            ),
            auth_type=dict(type="str", choices=["pwd", "keyfile", "pks"]),
            auth_name=dict(type="str", default=None),
            password=dict(type="str", default=None, no_log=True),
            auth_detail=dict(type="str"),
            auth_index=dict(type="int"),
            device=dict(type="str", default=None),
            auto_key_protection=dict(type="bool", default=False),
            force=dict(type="bool", default=False),
        ),
    )

    action = module.params["action"]
    device = module.params["device"]

    get_auth_details(module, device)

    if not lv_exists:
        results["msg"] = f"The provided device({device}) is not valid."
        module.fail_json(**results)

        # Setting rc to 0 as it could have become non-zero while checking for the device's existence.
        results["rc"] = 0

    if action == "initialize":
        results["msg"] = auth_init(module)

    elif action == "add":
        results["msg"] = auth_add(module)

    elif action == "unlock":
        results["msg"] = auth_unlock(module)

    elif action == "delete":
        results["msg"] = auth_delete(module)

    else:
        results["msg"] = auth_check(module)

    if action != "check":
        results["changed"] = True

    results["msg"] += f". Action({action}) completed successfully."
    module.exit_json(**results)


if __name__ == "__main__":
    main()
