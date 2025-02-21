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
module: hdcrypt_facts
short_description: Displays encryption/decryption related information
description:
- This module is used for getting encryption and decryption related information for logical volumes, physical volumes, volume groups.
- This module is a wrapper around hdcryptmgr command.
version_added: '1.9.0'
requirements:
- AIX >= 72X
- Python >= 2.7
options:
  action:
    description:
    - Specifies which information needs to be displayed.
      C(lv) displays logical volume encryption status;
      C(vg) displays volume group encryption capability;
      C(pv) displays physical volume encryption capability;
      C(meta) displays encryption metadata related to devices;
      C(conv) displays status of all the active and stopped conversions;
    type: str
    choices: [ lv, vg, pv, meta, conv ]
    required: true
  device:
    description:
    - Specifies the devices for which you want the information to be displayed.
    - Required for I(action=lv), I(action=pv) and I(action=meta).
    type: str
    required: false
    default: ''
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.2?topic=h-hdcryptmgr-command).
'''

EXAMPLES = r'''
- name: Display LV encryption status
  ibm.power_aix.hdcrypt_facts:
    action: lv
    device: "{{lv_val}}"

- name: Display LV encryption status of all the LVs in a VG
  ibm.power_aix.hdcrypt_facts:
    action: lv
    device: "{{vg_val}}"

- name: Display VG encryption status of all the VGs
  ibm.power_aix.hdcrypt_facts:
    action: vg

- name: Display VG encryption status of a VG
  ibm.power_aix.hdcrypt_facts:
    action: pv
    device: "{{vg_val}}"

- name: Display PV encryption status of all the PVs
  ibm.power_aix.hdcrypt_facts:
    action: pv

- name: Display meta facts of a VG
  ibm.power_aix.hdcrypt_facts:
    action: meta
    device: "{{vg_val}}"

- name: Display all active and stopped conversions
  ibm.power_aix.hdcrypt_facts:
    action: conv
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Logical Volume 'testlv' encrypted."
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
lv_facts:
    description: Contains logical volume encryption status information.
    returned: For I(action=lv)
    type: list
vg_facts:
    description: Contains volume group encryption capability information.
    returned: For I(action=vg)
    type: list
pv_facts:
    description: Contains physical volume encryption capability information.
    returned: For I(action=pv)
    type: list
meta_facts:
    description: Contains encryption metadata related information.
    returned: For I(action=meta)
    type: list
conv_facts:
    description: Contains information about all the active and stopped conversions.
    returned: For I(action=conv)
    type: list
'''

from ansible.module_utils.basic import AnsibleModule
import re

results = dict(
    changed=False,
    cmd='',
    msg='',
    rc='',
    stdout='',
    stderr='',
    lv_facts='',
    vg_facts='',
    pv_facts='',
    meta_facts='',
    conv_facts='',
)


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

    results['cmd'] = cmd
    results['rc'] = rc

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
    cmd = f"lsvg {name}"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc

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
    cmd = f"lspv {name}"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc

    if rc:
        return 0
    return 1


def parse_facts(action, stdout):
    """
    Parses the standard output.
    arguments:
        stdout: Standard output of hdcryptmgr command.
    returns:
        parsed_output: Parsed standard output.
    """
    stdout = stdout.splitlines()

    parsed_output = {}
    keys = {}

    keys['vg'] = ["VG NAME / ID", "ENCRYPTION ENABLED"]
    keys['lv'] = ["NAME", "CRYPTO_STATUS", "%_ENCRYPTED", "NOTE"]
    keys['pv'] = ["NAME", "CRYPTO_STATUS", "%_ENCRYPTED", "NOTE"]
    keys['conv'] = ["NAME", "TID/STATUS", "%_ENCRYPTED", "DIRECTION", "START_TIME"]

    if len(stdout) == 1:
        parsed_output = "No information was present on the system for your request."
    else:
        for line in stdout[1:]:
            line = re.split(r"\s+", line)
            key = line[0]
            parsed_output[key] = {}
            for it in range(len(keys[action])):
                if it >= len(line):
                    value = ""
                else:
                    value = line[it]

                parsed_output[key][keys[action][it]] = value

    return parsed_output


####################################################################################
# Action Handler Functions
####################################################################################


def get_lv_facts(module, name):
    """
    Displays LV encryption status.
    arguments:
        module: Ansible module argument spec.
        name: Name of the logical volume/volume group.
    returns:
        stdout: standard output of the command.
    """
    # If device(VG/LV) was not provided, fail
    if not name:
        results['msg'] = "To get lv_facts, you need to specify either a LV or a VG"
        module.fail_json(**results)

    # Check if the provided device(VG/LV) exists
    if not lv_exists(module, name) and not vg_exists(module, name):
        results['msg'] = f"The provided lv or vg does not exist: {name}"
        module.fail_json(**results)

    # Command for getting lv encryption status
    cmd = f"hdcryptmgr showlv {name}"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout

    if rc:
        results['stderr'] = stderr
        results['msg'] = f"Could not get the encryption status of '{name}'"
        module.fail_json(**results)

    success_msg = "Successfully fetched lv facts, check 'lv_facts' for more information."

    return success_msg


def get_vg_facts(module, vg):
    """
    Displays VG encryption capability.
    arguments:
        module: Ansible module argument spec.
        vg: Name of the Volume group.
    returns:
        stdout: standard output of the command.
    """
    # Command to get VG encryption capabilities
    cmd = "hdcryptmgr showvg"

    # Fail if the provided volume group does not exist
    if vg != "" and not vg_exists(module, vg):
        results['msg'] = f"The following vg does not exist: {vg}"
        module.fail_json(**results)

    # Modify the command if a valid VG was provided
    if vg != "":
        cmd += f" {vg}"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout

    if rc:
        results['msg'] = f"Could not get the encryption status of '{vg}'"
        results['stderr'] = stderr
        module.fail_json(**results)

    success_msg = "Successfully fetched vg facts, check 'vg_facts' for more information"
    return success_msg


def get_pv_facts(module, pv):
    """
    Displays PV encryption capabilities.
    arguments:
        module: Ansible module argument spec.
        pv: Name of the physical volume.
    returns:
        stdout: standard output of the command.
    """
    # Fail if pv was not provided
    if not pv:
        results['msg'] = "You need to specify a PV to get PV facts"
        module.fail_json(**results)

    # Fail if the provided PV does not exist
    if not pv_exists(module, pv):
        results['msg'] = f"The following PV does not exist: {pv}"
        module.fail_json(**results)

    # Command for getting pv encryption capabilities
    cmd = f"hdcryptmgr showpv {pv}"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout

    if rc:
        results['msg'] = f"Could not get the encryption status of '{pv}'"
        results['stderr'] = stderr
        module.fail_json(**results)

    success_msg = "Successfully fetched pv facts, check 'pv_facts' for more information"
    return success_msg


def disp_meta(module, name):
    """
    Displays encryption metadata
    arguments:
        module: Ansible module argument spec.
        name: Name of the device for which you want to get the metadata.
    returns:
        stdout: standard output of the command.
    """
    # Fail if the device was not provided
    if not name:
        results['msg'] = "You need to provide a device(lv/vg/pv) for getting the meta information."
        module.fail_json(**results)

    # Fail if the provided device does not exist
    if not lv_exists(module, name) and not vg_exists(module, name) and not pv_exists(module, name):
        results['msg'] = f"The provided device '{name}' is not a valid lv, vg or pv. Please provide a valid device and try again."
        module.fail_json(**results)

    # Command to get metadata
    cmd = f"hdcryptmgr showmd {name}"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout

    if rc:
        results['msg'] = f"The following command failed: {cmd}"
        results['stderr'] = stderr
        module.fail_json(**results)

    success_msg = "Successfully fetched meta facts, check 'meta_facts' for more information."
    return success_msg


def disp_conv(module):
    """
    Displays status of all active and stopped conversions
    arguments:
        module: Ansible module argument spec.
    returns:
        stdout: standard output of the command.
    """
    # Command for getting the conversion facts
    cmd = "hdcryptmgr showconv"

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout

    if rc:
        results['msg'] += f"The following command failed: {cmd}"
        results['stderr'] = stderr
        module.fail_json(**results)

    success_msg = "Successfully fetched conversion facts, check 'conv_facts' for more information."
    return success_msg


####################################################################################
# Main Function
####################################################################################


def main():

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(type='str', choices=['lv', 'vg', 'pv', 'meta', 'conv'], required=True),
            device=dict(type='str', default=""),
        ),
    )

    action = module.params['action']
    device = module.params['device']

    if action == "lv":
        results['msg'] = get_lv_facts(module, device)
        results['lv_facts'] = parse_facts("lv", results['stdout'])
        module.exit_json(**results)

    elif action == "vg":
        results['msg'] = get_vg_facts(module, device)
        results['vg_facts'] = parse_facts("vg", results['stdout'])
        module.exit_json(**results)

    elif action == "pv":
        results['msg'] = get_pv_facts(module, device)
        results['pv_facts'] = parse_facts("pv", results['stdout'])
        module.exit_json(**results)

    elif action == "meta":
        results['msg'] = disp_meta(module, device)
        facts = results['stdout'].splitlines()
        results['meta_facts'] = facts
        module.exit_json(**results)

    else:
        results['msg'] = disp_conv(module)
        results['conv_facts'] = parse_facts("conv", results['stdout'])
        module.exit_json(**results)


if __name__ == '__main__':
    main()
