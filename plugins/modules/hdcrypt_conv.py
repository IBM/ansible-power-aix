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
- Richard Taylor (@rtaylor-ibm)
- Shreyansh Chamola (@schamola)
module: hdcrypt_conv
short_description: Encrypt/Decrypt logical and physical volumes.
description:
- This module is used to convert a logical or physical volume into an encrypted one and vice versa.
version_added: '1.7.0'
requirements:
- AIX >= 72X
- Python >= 3.6
options:
  action:
    description:
    - Specifies which operation to perform on logical volumes.
      C(encrypt) enables encryption and encrypts a logical volume;
      C(decrypt) decrypts a logical volume;
    type: str
    choices: [ encrypt, decrypt ]
    required: true
  device:
    description:
    - Specifies the devices to encrypt or decrypt.
    - For I(action=encrypt) lv/pv/vg will become encryption enabled if it is not already.
    type: dict
    required: true
    suboptions:
      lv:
        description:
        - Specify the logical volume(s) to be encrypted/decrypted.
        type: 'list'
        elements: 'str'
      pv:
        description:
        - Specify the Physical volume(s) to be encrypted/decrypted.
        type: 'list'
        elements: 'str'
      vg:
        description:
        - Specify the volume group(s) to be encrypted/decrypted.
        type: 'list'
        elements: 'str'
      except_lv:
        description:
        - Specify the logical volume(s) to ignore when encrypting/decrypting.
        type: 'list'
        elements: 'str'
  password:
    description:
    - Specifies the password for encryption/decryption.
    - Used to set the intial password for encryption and provide authentication for decryption.
    - Password must also be encrypted.
    type: str
    required: true
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.2?topic=h-hdcryptmgr-command).
  - Using this module on SAN disks might throw an error. It is a known error for AIX.
'''

EXAMPLES = r'''
- name: "convert LV (testlv) to encrypted LV"
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      lv: testlv
    password: abc

- name: "convert multiple LVs to encrypted LV"
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      lv: testlv1, testlv2
    password: abc

- name: "convert LVs in VG (testvg) to encrypted LVs"
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      vg: testvg
    password: abc

- name: "convert multple VGs to encrypted LVs"
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      vg: testvg1, testvg2
    password: abc

- name: "convert LVs in VG (testvg) to encrypted LVs, except testlv3"
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      vg: testvg
      except_lv: testlv3
    password: abc

- name: "convert encrypted LV (testlv) to unencrypted LV"
  ibm.power_aix.hdcrypt_conv:
    action: decrypt
    device:
      lv: testlv
    password: abc

- name: "convert encrypted LVs in VG (testvg) to unencrypted LVs"
  ibm.power_aix.hdcrypt_conv:
    action: decrypt
    device:
      vg: testvg
    password: abc

- name: "convert encrypted LVs in VG (testvg) to unencrypted LVs, except testlv3"
  ibm.power_aix.hdcrypt_conv:
    action: decrypt
    device:
      vg: testvg
      except_lv: testlv3
    password: abc

- name: "Convert PV to encrypted PV"
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      pv: hdisk2
    password: abc

- name: "Convert encrypted PV to unencrypted PV"
  ibm.power_aix.hdcrypt_conv:
    action: decrypt
    device:
      pv: hdisk2
    password: abc

- name: Encrypt multiple PVs
  ibm.power_aix.hdcrypt_conv:
    action: encrypt
    device:
      pv: hdisk2, hdisk3
    password: abc
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
    returned: When the command is executed.
    type: int
stdout:
    description: The standard output of the command.
    returned: always
    type: str
stderr:
    description: The standard error of the command.
    returned: always
    type: str
'''


import re
from ansible.module_utils.basic import AnsibleModule


result = None
crypto_status = None
convert_failed = False

expectPrompts = {
    "weak_pwd": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr plain2crypt -f %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Please confirm usage of an unsecure passphrase \\(y|n\\): \\\"; \
            send \\\"y\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Passphrase authentication method with name\\\"; \
            expect \\\"Confirm to proceed further \\(y|n\\): \\\";\
            send \\\"y\\r\\\";\
            set timeout -1; \
            expect \\\"Successfully converted LV %s to an encrypted LV.\\\";\"",
    "strong_pwd": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr plain2crypt -f %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Passphrase authentication method with name\\\"; \
            expect \\\"Confirm to proceed further \\(y|n\\): \\\";\
            send \\\"y\\r\\\";\
            set timeout -1; \
            expect \\\"Successfully converted LV %s to an encrypted LV.\\\";\"",
    "weak_pwd_pv": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr pvenable %s; \
            expect \\\"Do you wish to continue? y(es) n(o)?\\\";\
            send \\\"y\\r\\n\\\"; \
            expect \\\"Enter Passphrase:\\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Please confirm usage of an unsecure passphrase \\(y|n\\): \\\"; \
            send \\\"y\\r\\\"; \
            expect \\\"Confirm Passphrase:\\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"Passphrase authentication method with name \"initpwd\" added successfully.\\\";\"",
    "strong_pwd_pv": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr pvenable %s; \
            expect \\\"Do you wish to continue? y(es) n(o)?\\\";\
            send \\\"y\\r\\\"; \
            expect \\\"Enter Passphrase:\\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Confirm Passphrase:\\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"Passphrase authentication method with name \"initpwd\" added successfully.\\\";\"",
    "authinit_weak_pwd": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr authinit %s; \
            expect \\\"Enter Passphrase:\\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Please confirm usage of an unsecure passphrase \\(y|n\\): \\\"; \
            send \\\"y\\r\\\"; \
            expect \\\"Confirm Passphrase:\\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"Passphrase authentication method with name \"initpwd\" added successfully.\\\";\"",
    "authinit_strong_pwd": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr authinit %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Confirm Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            set timeout -1; \
            expect \\\"Passphrase authentication method with name \"initpwd\" added successfully.\\\"; \"",
    "unlock": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr authunlock %s; \
            expect \\\"Enter Passphrase: \\\"; \
            send \\\"%s\\r\\\"; \
            expect \\\"Wrong passphrase\\\"; \
            send \\\"wrong\\r\\\"; \
            expect \\\"Wrong passphrase\\\"; \
            send \\\"wrong\\r\\\"; \
            expect \\\"hdcryptmgr authunlock failed.\\\";\"",
    "decrypt": "/usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr crypt2plain -f %s; \
            expect \\\"Confirm to proceed further \\(y|n\\): \\\";\
            send \\\"y\\r\\\";\
            set timeout -1; \
            expect \\\"Successfully converted LV testlv1 to an encryption disabled LV.\\\";\"",
    "pvdisable": "usr/bin/expect -c \"spawn /usr/sbin/hdcryptmgr pvdisable -f %s; \
            expect \\\"Do you wish to continue? y(es) n(o)? \\\"; \
            send \\\"y\\r\\\";\""
}


####################################################################################
# Action Handler Functions
####################################################################################


def encrypt_lv(module, name):
    """
    Encrypts the Logical Volume it is passed
    arguments:
        module: Ansible module argument spec.
        name: Name of the logical volume to encrypt
    note:
        If the volume group that the logical volume belongs to is not encryption enabled, it is first encryption enabled.
    return:
        None
    """
    password = module.params['password']
    vg_name = get_vg_name(module, name)

    # Enable Encryption if not already enabled on the VG
    vg_encrypt_enabled(module, vg_name)

    if crypto_status == "uninitialized":
        if not check_password_strength(password):
            cmd = expectPrompts['authinit_weak_pwd'] % (name, password, password)
        else:
            cmd = expectPrompts['authinit_strong_pwd'] % (name, password, password)
    else:
        if not check_password_strength(password):
            cmd = expectPrompts['weak_pwd'] % (name, password, password, name)
        else:
            cmd = expectPrompts['strong_pwd'] % (name, password, password, name)

    rc, stdout, stderr = module.run_command(cmd)
    result['stdout'] = stdout
    result['stderr'] = stderr
    result['cmd'] = cmd
    result['rc'] = rc
    if rc != 0:
        result['msg'] += f"Failed to encrypt logical volume {name}. Command '{cmd}' failed."
        module.fail_json(**result)
    elif "0516-2038" in stdout:  # 0516-2038: hdcryptmgr plain2crypt error: Logical Volume of type paging, boot, and aio_cache are not able to be encrypted
        result['msg'] += f"Logical volume {name} has type that is not supported for encryption, was not converted."
    elif f"LV {name} is already encrypted." in stdout:
        result['msg'] += f"LV {name} is already encrypted.\n"
    else:
        result['changed'] = True
        result['msg'] += f"Successfully converted LV {name} to an encrypted LV.\n"


def decrypt_lv(module, name):
    """
    Decrypts the Logical Volume it is passed
    arguments:
        module: Ansible module argument spec.
        name: Name of the logical volume to decrypt.
    return:
        None
    """
    global convert_failed

    password = module.params['password']
    cmd = expectPrompts['unlock'] % (name, password)
    rc, stdout, stderr = module.run_command(cmd)
    result['stdout'] = stdout
    result['stderr'] = stderr
    result['cmd'] = cmd
    if "3020-0125" in stdout:
        result['msg'] += f"Password to decrypt {name} was incorrect.\n"
        convert_failed = True
        return
    if f"LV {name} is not encryption enabled." in stdout:
        result['msg'] += f"LV {name} is already decrypted.\n"
        return
    if rc != 0:
        result['msg'] += f"Failed to unlock LV {name}. Command '{cmd}' failed."
        module.fail_json(**result)
    elif "Passphrase authentication succeeded." in stdout:
        result['changed'] = True
        result['msg'] += f"LV {name} was successfully unlocked.\n"

    cmd = expectPrompts['decrypt'] % (name)
    rc, stdout, stderr = module.run_command(cmd)
    result['stdout'] = stdout
    result['stderr'] = stderr
    result['cmd'] = cmd
    if rc != 0:
        result['msg'] += f"Failed to decrypt logical volume {name}. Command '{cmd}' failed."
        module.fail_json(**result)
    else:
        result['changed'] = True
        result['msg'] += f"Successfully converted LV {name} to a decrypted LV.\n"


def encrypt_pv(module, name):
    '''
    Encrypts the Physical Volume that is passed.
    arguments:
        module: Ansible module argument spec.
        name: Name of the Physical volume to encrypt.
    returns:
        None
    '''

    password = module.params['password']

    if check_password_strength(password):
        cmd = expectPrompts['strong_pwd_pv'] % (name, password, password)
    else:
        cmd = expectPrompts['weak_pwd_pv'] % (name, password, password)

    rc, stdout, stderr = module.run_command(cmd)
    result['stdout'] = stdout
    result['stderr'] = stderr
    result['cmd'] = cmd
    result['rc'] = rc
    if rc != 0:
        result['msg'] = "Failed to encrypt the physical volume."
        module.fail_json(**result)
    elif "3020-0445" in stdout:
        result['msg'] += f"Physical volume {name} is already encrypted."
    else:
        result['changed'] = True
        result['msg'] += f"Physical volume {name} was encrypted successfully."


def decrypt_pv(module, name):
    '''
    Decrypts the physical volume that is passed.

    arguments:
        module (dict): Ansible module argument spec.
        name (str) : Name of the PV that needs to be decrypted.

    returns:
        None
    '''

    password = module.params['password']

    cmd = expectPrompts['unlock'] % (name, password)

    rc, stdout, stderr = module.run_command(cmd)
    result['stdout'] = stdout
    result['stderr'] = stderr
    result['cmd'] = cmd
    result['rc'] = rc

    if rc != 0:
        result['msg'] = "Failed to unlock the Physical Volume. Check stdout/stderr for more information."
        module.fail_json(**result)

    cmd = expectPrompts['pvdisable'] % (name)

    rc, stdout, stderr = module.run_command(cmd)

    result['stdout'] = stdout
    result['stderr'] = stderr
    result['cmd'] = cmd
    result['rc'] = rc

    if rc != 0:
        result['msg'] = "Failed to Decrypt the Physical Volume."
        module.fail_json(**result)
    elif "3020-0446" in stdout:
        result['msg'] = "PV is not encryption enabled."
        result['changed'] = False
    else:
        result['changed'] = True
        result['msg'] = "PV was decrypted."


####################################################################################
# Helper Functions
####################################################################################

def get_crypto_status(stdout):
    '''
    Utility function to check the crypto status of a logical volume.
    arguments:
        stdout (str) : Standard output of a previous command.
    returns:
        status (str) : Status of the logical volume.
    '''

    status = stdout.split('\n')[1].split()[1]
    return status


def pv_exists(module, name):
    """
    Checks if the specified physical volume exists or not.
    arguments:
        module: Ansible module argument spec
    return:
        True - If the physical volume exists
        False - If the physical volume does not exist.
    """
    global convert_failed

    cmd = f"/usr/sbin/hdcryptmgr showpv {name}"

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc == 0:
        return True

    convert_failed = True
    result['msg'] += f"Physical volume {name} could not be found.\n"
    return False


def lv_exists(module, name):
    """
    Checks if the specified logical volume exists or not.
    arguments:
        module: Ansible module argument spec
    return:
        True if logical volume exists
        False if logical volume does not exist
    """
    global crypto_status
    global convert_failed

    cmd = f"/usr/sbin/hdcryptmgr showlv {name}"
    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc == 0:
        crypto_status = get_crypto_status(stdout)
        return True
    convert_failed = True
    result['msg'] += f"Logical volume {name} could not be found.\n"
    return False


def get_lv_props(module, name):
    """
    Gets the properties of a Logical Volume
    arguments:
        module: Ansible module argument spec.
        name: Name of the logical volume to get the properties of
    return:
        lv_props: The properties of the Logical Volume
    """
    cmd = f"/usr/sbin/lslv {name}"
    fail_msg = f"Failed to fetch the properties of logical volume {name}. \
        Command '{cmd}' failed."
    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] += fail_msg
        module.fail_json(**result)
    lv_props = result['stdout']
    return lv_props


def get_vg_props(module, name):
    """
    Gets the properties of a Volume Group
    arguments:
        module: Ansible module argument spec.
        name: Name of the volume group to get the properties of
    return:
        vg_props: The properties of the Volume Group
    """

    cmd = f"/usr/sbin/lsvg {name}"
    fail_msg = f"Failed to fetch the properties of volume group {name}. \
        Command '{cmd}' failed."
    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] += fail_msg
        module.fail_json(**result)
    vg_props = result['stdout']
    return vg_props


def get_vg_name(module, name):
    """
    Gets the name of the Volume Group that a Logical Volume belongs to
    arguments:
        module: Ansible module argument spec.
        name: Name of Logical volume to find the Volume group of
    return:
        vg_name: The volume group name
    """
    lv_props = get_lv_props(module, name)
    pattern = r"VOLUME GROUP:\s+(\w+)"
    vg_name = re.search(pattern, lv_props, re.MULTILINE).group(1)
    return vg_name


def vg_encrypt_enabled(module, name):
    """
    Checks if encryption is enabled on a Volume Group, and enables it if it is not
    arguments:
        module: Ansible module argument spec.
        name: Name of the volume group to enable encryption on
    return:
        None
    """
    vg_props = get_vg_props(module, name)
    pattern = r"^ENCRYPTION:\s+(\w+)"
    encrypt_status = re.search(pattern, vg_props, re.MULTILINE).group(1)

    if encrypt_status == 'no':
        # enable encryption on that vg
        cmd = f"/usr/sbin/chvg -k y {name}"
        fail_msg = f"Failed to enable encryption on the volume group {name}. \
            Command '{cmd}' failed."
        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] += fail_msg
            module.fail_json(**result)
        result['changed'] = True
        result['msg'] += f"Encryption was enabled on volume group {name}."


def get_lvs_of_vg(module, name):
    """
    Gets a list of the names of all the logical volumes that are in a Volume Group
    arguments:
        module: Ansible module argument spec
        name: Name of the volume group to get the LVs of
    return:
        lv_list: List of the LVs in the Volume Group
    """
    global convert_failed

    cmd = f"/usr/sbin/lsvg -l {name}"
    lv_list = []
    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        # The volume group requested could not be found.
        convert_failed = True
        result['msg'] += f"Volume Group {name} could not be found.\n"
        return lv_list
    pattern = r"(?<=\n).\w*"
    lv_list = re.findall(pattern, stdout)
    lv_list.pop(0)
    return lv_list


def check_password_strength(password):
    '''
    Utility function to check the strength of provided password.

    arguments:
        password (str) : User provided password.

    returns:
        true : If the password is strong.
        false: If the password is not strong.
    '''

    # pattern = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[(){}_~`'!@#$%^&*+=|:;<>,?/ \.\-\[\]\"\\])"
    pattern = r"(?=.*[A-Z])(?=.*[a-z])(?=.*[0-9])(?=.*[~`!@#$%^&*()_\-+={\[}\]|\\:;\"'<,>\.?/ ])"
    weak_pass = (len(password) < 12) or (re.search(pattern, password) is None)
    if weak_pass:
        return 0
    return 1


####################################################################################
# Main Function
####################################################################################


def main():
    global result

    device_spec = dict(
        lv=dict(type='list', elements='str'),
        vg=dict(type='list', elements='str'),
        pv=dict(type='list', elements='str'),
        except_lv=dict(type='list', elements='str'),
    )

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            action=dict(type='str', choices=['encrypt', 'decrypt'], required=True),
            device=dict(type='dict', required=True, options=device_spec),
            password=dict(type='str', required=True, no_log=True),
        ),
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    action = module.params['action']
    lvs = []
    vgs = []
    except_lvs = set()

    if module.params['device']['except_lv'] is not None:
        except_lvs.update(module.params['device']['except_lv'])
    if module.params['device']['lv'] is not None:
        lvs = module.params['device']['lv']
    if module.params['device']['vg'] is not None:
        vgs = module.params['device']['vg']
    for vg in vgs:
        lvs += get_lvs_of_vg(module, vg)

    for lv in lvs:
        if lv not in except_lvs and lv_exists(module, lv):
            if action == 'encrypt':
                encrypt_lv(module, lv)
            elif action == 'decrypt':
                decrypt_lv(module, lv)

    if module.params['device']['pv'] is not None:
        for pv in module.params['device']['pv']:
            if pv_exists(module, pv):
                if action == 'encrypt':
                    encrypt_pv(module, pv)
                else:
                    decrypt_pv(module, pv)

    if not result['changed']:
        result['msg'] += "No changes were needed to be made."
    if not convert_failed:
        module.exit_json(**result)
    else:
        module.fail_json(**result)


if __name__ == '__main__':
    main()
