#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
author:
- AIX development Team (@pbfinley1911)
module: lvol
short_description: Create/Delete logical volume or change characteristics of logical volume on AIX
description:
    - This module facilitates the creation of a new logical volume with provided characteristics, the
      modification of characteristics of existing logical volume and its deletion.
version_added: "2.9"
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- Root user is required.
options:
    state:
        description:
        - Specifies the action to be performed for the logical volume.
        - C(present) to create logical volume with I(lv_attributes) in the system. If volume is already
          present then attributes specified for the volume will be changed with the provided attributes.
        - C(absent) to delete logial volume with provided I(name). If volume is not present then message will be displayed for the same.
        type: str
        choices: [ present, absent ]
        required: true
    lv:
        description:
        - Logical volume name should be specified for which the action is to taken while removing or modifying
        type: str
        aliases: [ logical_volume ]
        required: true
    vg:
        description:
        - The volume group of the concerned logical volume.
        type: str
        required: True
    lv_type:
        description:
        - Type of the logical volume.
        type: str
        default: jfs2
    size:
        description:
        - Size of the concerned logical volume. Please check the valid sizes for mklv and chlv commands.
        type: str
    extra_opts:
        description:
        - Any other options to be passed by the user to mklv or chlv command
        type: str
    copies:
        description:
        - Specifies number of copies of logical volume
        - Maximum value allowed is 3
        type: int
        default: 1
    num_of_logical_partitions:
        description:
        - Specifies the number of logical partitions
        type: int
        default: 1
    policy:
        description:
        - Sets the inter-physical volume allocation policy
        - C(maximum) Allocates across the maximum number of physical volumes.
        - C(minimum) Allocates logical partitions across the minimum number of physical volumes.
        type: str
        choices: [ maximum, minimum ]
        default: maximum
    lv_new_name:
        description:
        - New name of the logical volume if user wants to change the name of existing logical volume.
        type: str
    phy_vol_list:
        description:
        - List of pysical volumes.
        type: list
        elements: str
"""

EXAMPLES = r'''
- name: Create a logical volume of 64M
  lvol:
    vg: test1vg
    lv: test1lv
    size: 64M
- name: Create a logical volume of 32M with disks testdisk1 and testdisk2
  lvol:
    vg: test2vg
    lv: test2lv
    size: 32M
    pvs: [ testdisk1, testdisk2 ]
- name: Create a logical volume of 32M with a minimum placement policy
  lvol:
    vg: rootvg
    lv: test4lv
    size: 32M
    policy: minimum
- name: Create a logical volume with extra options like mirror pool
  lvol:
    vg: testvg
    lv: testlv
    size: 128M
    extra_opts: -p copy1=poolA -p copy2=poolB
- name: Remove the logical volume
  lvol:
    vg: test1vg
    lv: test1lv
    state: absent
'''

RETURN = r'''
msg:
  type: str
  description: The execution message along with return code, output/error
  returned: always
  sample: 'Logical volume is created SUCCESSFULLY: test1lv'
'''

from ansible.module_utils.basic import AnsibleModule


def create_modify_lv(module):
    """
    Creates/Modify a logical volume with the attributes provided in the
    lv_attributes field.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success or error message.
    """

    name = module.params['lv']
    vg = module.params['vg']
    lv_type = module.params['lv_type']
    size = module.params['size']
    extra_opts = module.params['extra_opts']
    num_log_part = module.params['num_of_logical_partitions']
    copies = module.params['copies']
    policy = module.params['policy']
    msg = ""
    command_flag = False
    pvs = module.params['phy_vol_list']

    pv_list = ' '.join(pvs)

    if size is not None:
        valid_size = isSizeValid(module)

        if not valid_size:
            msg = "\nSize provided for the logical volume is not valid: %s" % module.params['lv']
            module.exit_json(changed=False, msg=msg)

    if policy == 'maximum':
        lv_policy = 'x'
    else:
        lv_policy = 'm'

    if not lv_exists(module):
        cmd = "mklv -t %s -y %s -c %s  -e %s %s -S %s %s %s %s" % (lv_type, name, copies, lv_policy, extra_opts, size, vg, num_log_part, pv_list)
        command_flag = True
    else:
        cmd = "chlv -e %s %s %s" % (lv_policy, extra_opts, name)

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        if command_flag:
            msg += "\nFailed to create logical volume in specified volume group: %s" % module.params['lv']
            msg += "\nCommand given: %s" % cmd
        else:
            msg += "\nFailed to modify logical volume with provided attributes: %s" % module.params['lv']
            msg += "\nCommand given: %s" % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        if command_flag:
            msg += "\nLogical volume is created SUCCESSFULLY: %s" % module.params['lv']
        else:
            msg += "\nLogical volume is modified SUCCESSFULLY with given attributes: %s" % module.params['lv']

    if module.params['lv_new_name'] is not None:
        cmd = 'chlv -n '
        cmd += module.params['lv_new_name']
        cmd += ' '
        cmd += module.params['name']

        rc, stdout, stderr = module.run_command(cmd)

        if rc != 0:
            msg += "\nFailed to change the name of the logical volume." % module.params['lv']
            msg += "\nCommand given: %s" % cmd
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            msg += "\nSuccesfully changed the name of the logical volume to: %s" % module.params['lv_new_name']

    return msg


def remove_lv(module):
    """
    Remove the logical volume without confirmation.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        msg      (srt): success or error message.
    """
    cmd = 'rmlv -f '
    cmd += module.params['lv']

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "Unable to remove the logical volume: %s" % module.params['lv']
        msg += "\nCommand given: %s" % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    else:
        msg = "Logical volume is REMOVED SUCCESSFULLY: %s" % module.params['lv']

    return msg


def isSizeValid(module):
    """
    Checks if the specified size for the logical volume is valid or not.
    arguments:
        size     (str): size of the logical volume
    return:
        true if valid
        false if not valid
    """

    size = module.params['size']
    num_size = int(size[:-1])

    isPowerof2 = (num_size and (not(num_size & (num_size - 1))))
    if not isPowerof2:
        return False

    unit = size[-1].upper()
    units = ['K', 'M']
    try:
        mult = 1024 ** units.index(unit)
    except ValueError:
        module.exit_json(changed=False, msg="Please specify valid size unit. Valid values are K and M.")

    actual_size = num_size * mult

    if not 4 <= actual_size <= (128 * 1024):
        return False

    return True


def lv_exists(module):
    """
    Checks if the specified logical volume exists or not.
    arguments:
        module      (dict): The Ansible module
    return:
        true if exists
        false otherwise
    """
    cmd = ["lslv"]
    cmd.append(module.params['lv'])

    rc, out, err = module.run_command(cmd)

    if (rc == 0):
        return True
    else:
        return False


def main():
    """
    Main function
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['present', 'absent']),
            lv=dict(type='str', required=True, aliases=['logical_volume']),
            vg=dict(type='str', required=True),
            lv_type=dict(type='str', default='jfs2'),
            size=dict(type='str'),
            extra_opts=dict(type='str', default=''),
            copies=dict(type='int', default=1),
            num_of_logical_partitions=dict(type='int', default=1),
            policy=dict(type='str', default='maximum', choices=['maximum', 'minimum']),
            lv_new_name=dict(type='str'),
            phy_vol_list=dict(type='list', elements='str', default=list())
        ),
        supports_check_mode=False
    )

    msg = ""

    if module.params['state'] == 'absent':
        if lv_exists(module):
            msg = remove_lv(module)
        else:
            msg = "Logical volume is NOT FOUND : %s" % module.params['lv']
            module.fail_json(msg=msg)
    elif module.params['state'] == 'present':
        msg = create_modify_lv(module)
    else:
        msg = "Invalid state '%s'" % module.params['state']
        module.exit_json(changed=False, msg=msg)

    module.exit_json(changed=True, msg=msg)


if __name__ == '__main__':
    main()
