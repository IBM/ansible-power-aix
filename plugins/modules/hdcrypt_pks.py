#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- Shreyansh Chamola (@schamola)
module: hdcrypt_pks
short_description: Adds PKS authentication method and manages PKS keys
description:
- This module is useful for adding Platform Key Store authentication method to a device and managing the PKS keys.
- This module is a wrapper around hdcryptmgr command.
version_added: '1.9.0'
requirements:
- AIX >= 72X
- Python >= 2.7
options:
  action:
    description:
    - Specifies which action needs to be performed.
      C(addpks) adds PKS as an authentication method;
      C(show) displays the LV ids that are associated with the PKS keys and their status;
      C(export) exports the PKS keys into a specific file;
      C(import) imports the PKS keys from the specified file;
      C(clean) removes an invalid key from the PKS;
    type: str
    choices: [ addpks, show, export, import, clean ]
    required: true
  device:
    description:
    - Specifies the devices for which you want to perform the action.
    - Required for I(action=addpks), I(action=export) and I(action=import).
    type: str
    required: false
    default: ''
  method_name:
    description:
    - Specifies a name for the PKS method.
    type: str
    default: initpks
    required: false
  location:
    description:
    - Location of the file where PKS keys will be exported/imported from
    type: str
    required: false
  passphrase:
    description:
    - Specifies the passphrase that will be used for importing/exporting PKS keys
    type: str
    default: ""
    required: false
    no_log: true
  pks_label:
    description:
    - logical volume ID that is associated with the invalid key that needs to be removed
    type: str
    required: false
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.2?topic=h-hdcryptmgr-command).
  - If the VG is in locked state, addpks action will not work.
'''

EXAMPLES = r'''
- name: Add PKS to filesystem
  ibm.power_aix.hdcrypt_pks:
    action: addpks
    device: testlv1
    method_name: initpks

- name: Display PKS keys status
  ibm.power_aix.hdcrypt_pks:
    action: show

- name: Export PKS key to a file
  ibm.power_aix.hdcrypt_pks:
    action: export
    device: testlv1
    location: /tmp/file123
    passphrase: abc1234
  no_log: true

- name: Import PKS key
  ibm.power_aix.hdcrypt_pks:
    action: import
    device: testlv1
    location: /tmp/file123
    passphrase: abc1234
  no_log: true

- name: Clean invalid PKS key
  ibm.power_aix.hdcrypt_pks:
    action: clean
    pks_label: 00fb293100004c000000018deea122dc.3
'''

RETURN = r'''
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
pksshow_results:
    description: Contains parsed output of "hdcryptmgr pksshow" command.
    returned: If I(action=show)
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule
import re
import os.path

results = dict(
    changed=False,
    cmd='',
    msg='',
    rc='',
    stdout='',
    stderr='',
    pksshow_results={},
)


expectPrompts = {
    "pksexport_weak_pwd": "/usr/bin/expect -c \"spawn hdcryptmgr pksexport -p %s %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Please confirm usage of an unsecure passphrase \\(y|n\\): \\\"; \
            send \\\"y\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"1 PKS keys exported.\\\";\"",
    "pksexport_strong_pwd": "/usr/bin/expect -c \"spawn hdcryptmgr pksexport -p %s %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"1 PKS keys exported.\\\";\"",
    "pksexport_weak_pwd_72Z": "/usr/bin/expect -c \"spawn hdcryptmgr pksexport -p %s %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Please confirm usage of an unsecure passphrase (y|n): \\\"; \
            send \\\"y\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"1 PKS keys exported.\\\";\"",
    "pksexport_strong_pwd_72Z": "/usr/bin/expect -c \"spawn hdcryptmgr pksexport -p %s %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"1 PKS keys exported.\\\";\"",
    "pksimport": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr pksimport -p %s %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Wrong passphrase\\\"; \
            send \\\"wrong\\r\\\"; \
            expect \\\"Wrong passphrase\\\"; \
            send \\\"wrong\\r\\\"; \
            expect \\\"hdcryptmgr authunlock failed.\\\";\""
}


####################################################################################
# Helper Functions
####################################################################################


def find_version(module):
    """
    Utility function to find out the version of the system.
    arguments:
        module: Ansible module argument spec.
    returns:
        version (str) - Version of the system.
    """
    cmd = "cat proc/version"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    if rc:
        results['msg'] = "Could not get information about the version"
        results['stderr'] = stderr
        module.fail_json(**results)

    version = stdout.splitlines()[2].split("_")[-1]
    return version


def lv_exists(module, device):
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
    cmd = "lslv " + device

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc:
        return 0
    return 1


def vg_exists(module, name):
    """
    Checks if the volume group exists.
    arguments:
        module: Ansible module argument spec.
        name: Name of the volume group
    returns:
        True: If the volume group exists.
        False: If the volume group does not exist.
    """
    # Command to get information about a VG(In this case, used to check existence)
    cmd = "lsvg " + name

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc:
        return 0
    return 1


def pv_exists(module, name):
    """
    Checks if the physical volume exists.
    arguments:
        module: Ansible module argument spec.
        name: Name of the physical volume
    returns:
        True: If the physical volume exists.
        False: If the physical volume does not exist.
    """
    # Command to get information about a PV(In this case, used to check existence)
    cmd = "lspv " + name

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc:
        return 0
    return 1


def is_pks_enabled(module):
    """
    Check if PKS is enabled on the system or not.
    arguments:
        module - The generic Ansible module.
    returns:
        True - If PKS is enabled
        False - If PKS is not enabled
    """
    cmd = "hdcryptmgr pksshow"

    rc, stdout, stderr = module.run_command(cmd)

    if rc and "3020-0349" in stdout:
        return False
    return True


def parse_stdout(stdout):
    """
    Helper function to parse the standard output provided.
    arguments:
        stdout (str) - Standard output of the previous command.
    returns:
        parsed_output (dict) - Parsed stdout
    """
    # The output will be something like this:
    # Total PKS size: 65536 bytes
    # Used  PKS size: 479 bytes
    # Estimated encryption key slots: 747

    # PKS_Label (LVid)                         Status		Device
    # 00fb293100004c0000000174c0a994b7.1       VALID		 testlv
    # 00fb293100004c0000000174c0a994b7.2       UNKNOWN
    # 00fb293100004c0000000174c0a994b7.3       UNKNOWN

    # PKS_Label (PVuuid)                           status           Device
    # pvuuid:706aa87a-e4d0-f2ec-3999-2631162226d2  VALID KEY        hdisk3

    # PKS_Label (objects)
    # ksvr:gpfs-pw-t2

    lines = stdout.splitlines()
    parsed_output = {}
    PKS_labels = {
        "PKS_Label (LVid)": {},
        "PKS_Label (PVuuid)": {},
        "PKS_Label (objects)": {}
    }

    curr_key = ""
    for line in lines:
        if ":" in line and curr_key == "":
            line = line.split(":")
            attr = line[0].strip()
            val = line[1].strip()
            if attr == "Estimated encryption key slots":
                val = int(val)
            parsed_output[attr] = val
        else:
            if line.strip() == "":
                continue

            if "PKS_Label (LVid)" in line:
                curr_key = "PKS_Label (LVid)"

            elif "PKS_Label (PVuuid)" in line:
                curr_key = "PKS_Label (PVuuid)"

            elif "PKS_Label (objects)" in line:
                curr_key = "PKS_Label (objects)"

            else:
                if curr_key == "":
                    if "MISC" not in parsed_output.keys():
                        parsed_output["MISC"] = line
                    else:
                        parsed_output["MISC"] += " " + line
                else:
                    line = re.split(r"\s+", line)
                    if curr_key == "PKS_Label (LVid)":
                        PKS_labels[curr_key][line[0]] = {}
                        LVid_status = line[1]
                        if len(line) > 2 and line[2] == "KEY":
                            LVid_status += " " + "KEY"

                        PKS_labels[curr_key][line[0]]["Status"] = LVid_status
                        PKS_labels[curr_key][line[0]]["Device"] = ""

                        if len(line) == 4:
                            PKS_labels[curr_key][line[0]]["Device"] = line[-1]
                    elif curr_key == "PKS_Label (PVuuid)":
                        pvuuid = line[0].split(":")[1]
                        PKS_labels[curr_key][pvuuid] = {}

                        pvuuid_status = line[1]
                        if len(line) > 2 and line[2] == "KEY":
                            LVid_status += " " + "KEY"

                        PKS_labels[curr_key][pvuuid] = pvuuid_status
                        PKS_labels[curr_key][pvuuid] = ""
                        if len(line) == 4:
                            PKS_labels[curr_key][pvuuid] = line[-1]
                    else:
                        obj_info = line[0].split(":")
                        if len(obj_info) < 2:
                            continue
                        PKS_labels[curr_key][obj_info[0]] = obj_info[1]

    parsed_output.update(PKS_labels)
    return parsed_output


def check_password_strength(password, version):
    '''
    Utility function to check the strength of provided password.

    arguments:
        password (str) : User provided password.

    returns:
        true : If the password is strong.
        false: If the password is not strong.
    '''
    # pattern = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[(){}_~`'!@#$%^&*+=|:;<>,?/ \.\-\[\]\"\\])"
    if version == "72Z":
        return len(password) >= 12

    pattern = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[~`!@#$%^&*()_\-+={\[}\]|\\:;\"'<,>\.?/ ])"
    weak_pass = (len(password) < 12) or (re.search(pattern, password) is None)
    if weak_pass:
        return 0
    return 1


def validate_device(module, device):
    """
    Utility function to check if the provided device is a valid LV, PV or VG

    arguments:
        module (dict) - The Ansible module
        device (str) - The device (LV/VG/PV) that needs to be validated

    returns:
        True - If the device is valid
        False - If the device is invalid

    """
    if not lv_exists(module, device) and not vg_exists(module, device) and not pv_exists(module, device):
        return 0

    return 1


def validate_label(module, id):
    """
    Utility function to check if the provided id is valid or not

    arguments:
        module (dict) - The Ansible module
        id (str) - id that needs to be validated

    returns:
        Nothing

    Note:
        Fails if the key is not present in PKS storage or is a valid key
    """
    results['msg'] = pksshow(module)

    pksshow_res = results['pksshow_results']

    if id not in pksshow_res["PKS_Label (LVid)"].keys():
        results['msg'] = "The provided id is not present in PKS Storage."
        module.fail_json(**results)

    if pksshow_res["PKS_Label (LVid)"][id]["Status"] == "VALID KEY":
        results['msg'] = "A valid key can not be removed."
        module.fail_json(**results)


####################################################################################
# Action Handler Functions
####################################################################################


def addpks(module):
    """
    Adds pks as an authentication method for the device.
    arguments:
        module - The generic ansible module
    returns:
        Nothing
    """
    # hdcryptmgr authadd -t pks -n initpks testlv1
    # PKS authentication method with name "initpks" added successfully.
    success_msg = "PKS authentication method added successfully !"
    fail_msg = "Could not add PKS as an authentication method"
    pks_label = module.params['method_name']
    device = module.params['device']

    if not validate_device(module, device):
        results['msg'] = "Provided device is not valid"
        module.fail_json(**results)

    cmd = "hdcryptmgr authadd -t pks -n" + pks_label + " " + device

    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout

    if rc:
        results['stderr'] = stderr

        if "3020-1092" in stderr:
            return "PKS authentication already exists"

        results['msg'] = fail_msg
        module.fail_json(**results)

    results['changed'] = True
    return success_msg


def pksshow(module):
    """
    Displays the PKS label of volume that is associated with the PKS keys and the status of the PKS keys.
    arguements:
        module - The generic ansible module
    returns:
        success_msg: If the command runs successfully, success message is returned.
    """
    cmd = "hdcryptmgr pksshow"
    success_msg = "Successfully fetched PKS keys, labels and their status, check pksshow_results"
    fail_msg = "Could not fetch pksshow's output"

    rc, stdout, stderr = module.run_command(cmd)

    if not rc:
        results['stdout'] = stdout
        results['msg'] = success_msg
    else:
        results['stderr'] = stderr
        results['msg'] = fail_msg

    results['pksshow_results'] = parse_stdout(stdout)
    return success_msg


def pksclean(module):
    """
    Cleans invalid PKS keys
    arguments:
        module - The generic ansible module
    returns:
        success_msg (str) - In case of success
        fail_msg (str) - In case of failure
    """
    success_msg = "Successfully cleaned invalid PKS keys"
    fail_msg = "Could not clean invalid PKS keys"

    pks_label = module.params['pks_label']

    if not pks_label:
        results['msg'] = "You must specify the PKS label that is associated with the invalid key that you want to remove."
        module.fail_json(**results)

    validate_label(module, pks_label)

    cmd = "hdcryptmgr pksclean " + pks_label

    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    if rc:
        results['stderr'] = stderr
        results['msg'] = fail_msg
        module.fail_json(**results)

    results['changed'] = True
    return success_msg


def pksexport(module, version):
    """
    Exports the PKS keys into the specified file.
    arguments:
        module - The generic Ansible module.
    returns:
        Nothing
    """
    # hdcryptmgr pksexport -p /tmp/file123 testlv1
    # Enter Passphrase:
    # Trying to use unsecure passphrase. Constraints preceded by * are not met.
    # Passphrase must contain at least :
    #         * 12 characters
    #         1 lower case letters
    #         * 1 upper case letters
    #         * 1 digits
    #         * 1 special characters from list "~`!@#$%^&*()_-+={[}]|\:;"'<,>.?/ */"
    # Please confirm usage of an unsecure passphrase (y|n): y
    # Confirm Passphrase:
    # 1 PKS keys exported.

    success_msg = "Successfully exported the PKS key."
    fail_msg = "PKS export failed."
    location = module.params['location']
    device = module.params['device']
    password = module.params['passphrase']

    # Fail if the provided is not valid
    if not validate_device(module, device):
        results['msg'] = "Provided device is not valid"
        module.fail_json(**results)

    # Fail if the file already exists
    if os.path.exists(location):
        results['msg'] = "Key can not be exported, as the file already exists."
        module.fail_json(**results)

    # Check strength of the provided password use the proper expect Prompts accordingly
    if not check_password_strength(password, version):
        key = 'pksexport_weak_pwd'
        if version == "72Z":
            key += '_72Z'
        cmd = expectPrompts[key] % (location, device, password, password)
    else:
        key = 'pksexport_strong_pwd'
        if version == "72Z":
            key += '_72Z'
        cmd = expectPrompts[key] % (location, device, password, password)

    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    if rc:
        results['stderr'] = stderr
        results['msg'] = fail_msg
        module.fail_json(**results)

    results['changed'] = True
    return success_msg


def pksimport(module):
    """
    Imports the PKS keys into the specified file.
    arguments:
        module - The generic Ansible module.
    returns:
        success_msg (str) - Success message when the command runs successfully.
    """
    # hdcryptmgr pksimport -p /tmp/file123 testlv1
    # Enter Passphrase:
    # Wrong passphrase. Try again (1/3)
    # Enter Passphrase:
    # Key having label 00fb293100004c000000018deea122dc.2 is succesfully imported for the device testlv1.
    # 1 PKS keys imported.
    success_msg = "Successfully imported PKS keys"
    fail_msg = "Could not import PKS keys"
    location = module.params['location']
    device = module.params['device']
    password = module.params['passphrase']

    if not validate_device(module, device):
        results['msg'] = "Provided device is not valid"
        module.fail_json(**results)

    cmd = expectPrompts['pksimport'] % (location, device, password)

    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    if rc:
        results['stderr'] = stderr
        results['msg'] = fail_msg
        module.fail_json(**results)

    results['changed'] = True
    return success_msg


####################################################################################
# Main Function
####################################################################################


def main():

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(type='str', choices=['addpks', 'show', 'clean', 'import', 'export'], required=True),
            device=dict(type='str', default=""),
            method_name=dict(type='str', default="initpks"),
            pks_label=dict(type='str'),
            location=dict(type='str'),
            passphrase=dict(type='str', default="", no_log=True),
        ),
    )

    action = module.params['action']

    if not is_pks_enabled(module):
        results['msg'] = "PKS is not supported or PKS is not activated."
        module.fail_json(**results)

    version = find_version(module)

    if action == "addpks":
        results['msg'] = addpks(module)
        module.exit_json(**results)
    elif action == "show":
        results['msg'] = pksshow(module)
        module.exit_json(**results)
    elif action == "clean":
        results['msg'] = pksclean(module)
        module.exit_json(**results)
    elif action == "import":
        results['msg'] = pksimport(module)
        module.exit_json(**results)
    else:
        results['msg'] = pksexport(module, version)
        module.exit_json(**results)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
