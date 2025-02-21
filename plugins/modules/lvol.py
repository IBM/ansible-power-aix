#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
---
author:
- AIX development Team (@pbfinley1911)
module: lvol
short_description: Configure AIX LVM logical volumes
description:
- This module creates, removes and modifies attributes of LVM logical volumes.
version_added: '1.1.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorizations:
  B(aix.lvm.manage.change,aix.lvm.manage.create,aix.lvm.manage.remove)'
options:
  state:
    description:
    - Specifies the action to be performed on the logical volume.
    - C(present) creates or modifies the logical volume if already exists with I(lv_attributes).
    - C(absent) removes a logial volume.
    type: str
    choices: [ present, absent ]
    required: true
  lv:
    description:
    - Specified the logical volume name.
    type: str
    aliases: [ logical_volume ]
    required: true
  vg:
    description:
    - Specifies the volume group name this logical volume is part of.
    - Required when I(state=present).
    type: str
  lv_type:
    description:
    - Specifies the type of the logical volume to create.
    - The standard types are
      C(jfs) for journaled file systems,
      C(jfslog) for journaled file system logs,
      C(jfs2) for enhanced journaled file system,
      C(jfs2log) for enhanced journaled file system logs,
      C(paging) for paging spaces.
    - But you can define other logical volume types with this flag.
    - You B(cannot) create a striped logical volume of type C(boot).
    - Can be used to create a logical volume, hence when I(state=present).
    type: str
    default: jfs2
  strip_size:
    description:
    - Specifies the strip size of the striped logical volume to create.
    - Can be used to create a logical volume, hence when I(state=present).
    type: str
  extra_opts:
    description:
    - Any other options to be passed by the user to mklv or chlv command
    type: str
    default: ''
  copies:
    description:
    - Specifies number of copies of logical volume
    - Maximum value allowed is 3
    - Can be used to create a logical volume, hence when I(state=present).
    type: int
    default: 1
  size:
    description:
    - If you do not specify its value when trying to create a logical volume, default value '1' is considered.
    - Specifies the number of logical partitions or the size of the
      the logical volume in terms of K, M, or G.
    - Can be used to create a logical volume, hence when I(state=present).
    - Can be used to increase the size of the logical volume if it already
      exist. If the input I(size) is larger than the current logical volume
      size then extend the logical volume to match the input size. If the
      input I(size) uses the prefix "+" sign, then the logical volume is
      extended by that amount.
    - Cannot be used to decrease the size of an existing logical volume.
    - Explicitly use quotations when using the "+" sign to denote string
      type.
    type: str
  pv_list:
    description:
    - List of pysical volumes.
    - Can be used to create a logical volume, hence when I(state=present).
    type: list
    elements: str
  policy:
    description:
    - Specifies the inter-physical volume allocation policy. It is the number of physical volumes to
      extend across, using the volumes that provide the best allocation.
    - C(maximum) allocates across the maximum number of physical volumes.
    - C(minimum) allocates logical partitions across the minimum number of physical volumes.
    - Can be used to create or modify a logical volume, hence when I(state=present).
    type: str
    choices: [ maximum, minimum ]
    default: maximum
  lv_new_name:
    description:
    - Specifies the name of the logical volume to change an existing logical volume.
    - Can be used to modify a logical volume, hence when I(state=present).
    type: str
notes:
  - B(Attention:) using I(state=absent) destroys all data in the specified logical volumes. If the
    logical volume spans multiple physical volumes, the removal of only logical partitions on the
    physical volume can jeopardize the integrity of the entire logical volume.
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chlv.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mklv.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmlv.html).
"""

EXAMPLES = r'''
- name: Create a logical volume of 64M
  ibm.power_aix.lvol:
    vg: test1vg
    lv: test1lv
    size: "64M"
    state: present
- name: Create a logical volume of 10 logical partitions with disks testdisk1 and testdisk2
  ibm.power_aix.lvol:
    vg: test2vg
    lv: test2lv
    size: "10"
    pv_list: testdisk1, testdisk2
    state: present
- name: Create a logical volume of 32M with a minimum placement policy
  ibm.power_aix.lvol:
    vg: rootvg
    lv: test4lv
    size: "32M"
    policy: minimum
    state: present
- name: Create a logical volume with extra options like mirror pool
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    size: "128M"
    extra_opts: -p copy1=poolA -p copy2=poolB
    state: present
- name: Extend a logical volume by 5G
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    size: "+5G"
    state: present
- name: Extend a logical volume to 10G
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    size: "10G"
    state: present
- name: Reduce the number of mirrors of a logical volume with three mirrors
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    copies: 2
    state: present
- name: Increase the number of mirrors of a logical volume with one mirror
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    copies: 3
    state: present
- name: Rename a logical volume
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    lv_new_name: renamedlv
    state: present
- name: Remove the logical volume
  ibm.power_aix.lvol:
    state: absent
    lv: test1lv
'''

RETURN = r'''
msg:
  type: str
  description: The execution message.
  returned: always
  sample: 'Logical volume test1lv created.'
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
__metaclass__ = type


result = None


####################################################################################
# Action Handler Functions
####################################################################################
def create_lv(module, name):
    """
    Creates a logical volume with the attributes provided in the
    lv_attributes field.
    arguments:
        module (dict): The Ansible module
        name (str): Logical Volume Name
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    opts = ''
    lv_type = module.params['lv_type']
    strip_size = module.params['strip_size']
    copies = module.params['copies']
    policy = module.params['policy']
    vg = module.params['vg']
    num_log_part = module.params['size']

    if not num_log_part:
        num_log_part = '1'

    # -a position, -b badblocks, -C stripewidth, -d schedule
    # -R preferredRead, -L label, -m mapfile, -o y/n, -r relocate
    # -s strict, -T O, -u upperbound, -v verify, -w mirrorwriteconsistency
    # -x maxumum, -Y prefix, -U userid, -G groupid, -P modes
    # -p copyn=mirrorpool, -O y/n, -k y/n
    extra_opts = module.params['extra_opts']

    if strip_size is not None:
        isValid, reason = isSizeValid(module)
        if not isValid:
            result['msg'] = f"Invalid logical volume {name} strip_size: {strip_size}. {reason}"
            module.fail_json(**result)
        else:
            opts += f"-S {strip_size} "

    opts += f"-t {lv_type} "
    opts += f"-y {name} "
    opts += f"-c {copies} "

    if policy == 'maximum':
        lv_policy = 'x'
    else:
        lv_policy = 'm'
    opts += f"-e {lv_policy}"

    if module.params['pv_list']:
        pv_list = ' '.join(module.params['pv_list'])
    else:
        pv_list = ''

    cmd = f"mklv {opts} {extra_opts} {vg} {num_log_part} {pv_list}"
    success_msg = f"Logical volume {name} created."
    fail_msg = f"Failed to create logical volume {name} in volume group {vg}. \
        Command: {cmd} failed."
    lv_run_cmd(module, cmd, success_msg, fail_msg, None)


def extend_lv(module, name, init_props):
    """
    Extend a logical volume with the given new size.
    arguments:
        module (dict): The Ansible module
        name (str): Logical Volume Name
        init_props (str): Initial properties of the logical volume
    note:
        The new size must be large than the original size.
    return:
        none
    """

    # get lvid to fetch additonal information
    pattern = r"^LV IDENTIFIER:\s+(\w+\.\d+)"
    lvid = re.search(pattern, init_props, re.MULTILINE).group(1)

    # get the physical partition size (PP size) for converting
    # size with prefixes B/b, K/k, M/m, and G/g into corresponding
    # number of logical partitions
    # also fetch the current lv size in logical partions (LPs)
    # e.g output of lquerykv wit -cst
    # Csize: <number of current LPs in LV>
    # PPsize: <PP size of each LP>
    cmd = f"lquerylv -L {lvid} -cst"
    fail_msg = "Failed to fetch the physical partition size and current \
        number of logical partitions in the logical volume"
    lv_run_cmd(module, cmd, None, fail_msg, fetch=True)
    pattern = r"^Csize:\s+(\d+)"
    curr_lps_in_lv = int(re.search(pattern, result['stdout'], re.MULTILINE).group(1))
    pattern = r"^PPsize:\s+(\d+)"
    pp_size = int(re.search(pattern, result['stdout'], re.MULTILINE).group(1))

    # check if plus (+) sign is used with the 'size' parameter
    size = module.params['size']
    plus_sign_used = False
    if size[0] == "+":
        plus_sign_used = True
        size = size[1:]  # remove plus sign
    elif size[0] == "-":
        # minus sign is not supported
        result['msg'] += "\nMinus sign (-) is not a supported prefix for 'size' parameter."
        module.fail_json(**result)

    # convert 'size' parameter to corresponding number of LPs
    # needed to satisfy the specified new size if suffixes are
    # used (B, b, K, k, M, m, G, g)
    # calculation logic lifted verbatim from extendlv cmd in lvm
    pp_size = 1 << pp_size
    if (size[-1] == "G") or (size[-1] == "g"):
        shift = 30
    elif (size[-1] == "M") or (size[-1] == "m"):
        shift = 20
    elif (size[-1] == "K") or (size[-1] == "k"):
        shift = 10
    elif (size[-1] == "B") or (size[-1] == "b"):
        shift = 9
    else:  # no suffix
        shift = 0

    # conversion from size with suffix to correspoding num
    # of LPs to satisfy the size
    if shift != 0:
        size = int(size[:-1])
        size = size * (1 << shift)
        size = (size + pp_size - 1) / pp_size
    size = int(size)

    # calculate how much to extend the LV on each scenario
    # (1) if the calculated new size is smaller than the
    # current size, then fail (without + sign)
    # (2) if the plus sign is USED, then add 'size' LPs
    # to the existing number of LPs in the LV
    # (3) if the plus sign is NOT used then extend current
    # LV until it satisfies the new specified number of
    # 'size' LPs
    # (4) if plus sign is NOT used AND expected new 'size'
    # is equal to current size, then no changes needed.
    fail_msg = f"\nFailed to extend logical volume {name}."
    if not plus_sign_used and size < curr_lps_in_lv:
        result['cmd'] = ""
        result['msg'] += "\nReducing the size of the logical volume is not supported."
        module.fail_json(**result)
    elif plus_sign_used:
        cmd = f"extendlv {name} {size}"
        msg_size = module.params['size']
        success_msg = f"\nLogical volume {name} has been extended by {msg_size}."
        lv_run_cmd(module, cmd, success_msg, fail_msg, None)
    elif size != curr_lps_in_lv:
        # calculate how much to extend in order to satisfy 'size'
        size = size - curr_lps_in_lv
        cmd = f"extendlv {name} {size}"
        msg_size = module.params['size']
        success_msg = f"\nLogical volume {name} has been extended to {msg_size}."
        lv_run_cmd(module, cmd, success_msg, fail_msg, None)
    elif size == curr_lps_in_lv:
        result['cmd'] = ""
        result['msg'] += "\nThere is no need to extend the logical volume. "
    else:
        result['msg'] += "\nIt should NEVER reach this path. "
        module.fail_json(**result)


def modify_lv(module, name, init_props):
    """
    Modify a logical volume with the attributes provided in the
    lv_attributes field.
    arguments:
        module (dict): The Ansible module
        name (str): Logical Volume Name
        init_props (str): Initial properties of the logical volume
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    new_name = module.params['lv_new_name']
    copies = module.params['copies']
    policy = module.params['policy']
    lv_type = module.params['lv_type']
    # -a position, -b badblocks, -d schedule, -R preferredRead,
    # -L label, -o y/n, -p permission, -r relocate, -s strict,
    # -u upperbound, -v verify, -w mirrorwriteconsistency, -x maxumum
    # -T O/F, -U userid, -G groupid, -P modes, -m copyn=mirrorpool
    # -M copyn, -O y/n
    extra_opts = module.params['extra_opts']

    if policy == 'maximum':
        lv_policy = 'x'
    else:
        lv_policy = 'm'

    opts = ''
    opts += f"-e {lv_policy} "
    opts += f"-t {lv_type} "
    cmd = f"chlv {opts} {extra_opts} {name}"
    success_msg = f"Logical volume {name} modified."
    fail_msg = f"Failed to modify logical volume {name}. Command: {cmd} failed."
    lv_run_cmd(module, cmd, success_msg, fail_msg, init_props)

    old_num_copies = re.search(r"^COPIES:\s*(?P<num_copy>\d)", init_props, re.MULTILINE)
    old_num_copies = int(old_num_copies.group('num_copy').strip())
    if copies != old_num_copies:
        if copies < old_num_copies:
            cmd = f"rmlvcopy {name} {copies}"
        elif copies > old_num_copies:
            cmd = f"mklvcopy -e {lv_policy} {name} {copies}"
        success_msg = f"\nLogical volume {name}'s number of copies is modified."
        fail_msg = f"\nFailed to modify the number of copies of logical volume {name}."
        lv_run_cmd(module, cmd, success_msg, fail_msg, None)

    if new_name:
        cmd = f'lslv {new_name}'
        rc = module.run_command(cmd)[0]
        if not rc:
            result['msg'] += f"Can not rename the logical volume to {new_name}, \
                a logical volume with the same name already exists."
            result['changed'] = False
            module.exit_json(**result)

        cmd = f'chlv -n {new_name} {name}'
        success_msg = f"\nLogical volume {name} renamed into {new_name}."
        fail_msg = f"\nFailed to rename {name} into {new_name}. Command {cmd} failed."
        lv_run_cmd(module, cmd, success_msg, fail_msg, None)


def remove_lv(module, name):
    """
    Remove the logical volume without confirmation.
    arguments:
        module  (dict): The Ansible module
        name (str): Logical Volume Name
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    cmd = f'rmlv -f {name}'
    success_msg = f"Logical volume {name} removed."
    fail_msg = f"Failed to remove the logical volume: {name}"
    lv_run_cmd(module, cmd, success_msg, fail_msg, None)


####################################################################################
# Helper Functions
####################################################################################
def isSizeValid(module):
    """
    Checks if the specified strip size for the logical volume is valid or not.

    arguments:
        strip_size     (str): strip size of the logical volume
    return:
        valid  (bool): true if valid, false if not valid
        reason  (str): message for the strip size invalidity
    """

    reason = ""
    valid = True

    strip_size = module.params['strip_size']
    num_strip_size = int(strip_size[:-1])

    isPowerof2 = (num_strip_size and (not num_strip_size & (num_strip_size - 1)))
    if not isPowerof2:
        valid = False
        reason = "Must be a power of 2. "

    unit = strip_size[-1].upper()
    units = ['K', 'M']
    try:
        mult = 1024 ** units.index(unit)
    except ValueError:
        valid = False
        reason = "Valid strip size unit are K and M."
        return valid, reason    # existing as we cannot compute the strip size without valid unit

    actual_strip_size = num_strip_size * mult
    if not 4 <= actual_strip_size <= (128 * 1024):
        valid = False
        reason += "Must be between 4K and 128M."

    return valid, reason


def get_lv_props(module):
    """
    Fetches the current properties of the logical volume.
    param name: logical volume name.
    return: standard output of lslv
    """

    name = module.params['lv']
    cmd = f"lslv {name}"
    fail_msg = f"Failed to fetch the properties of logical volume {name}. \
        Command: {cmd} failed."
    lv_run_cmd(module, cmd, None, fail_msg, fetch=True)
    init_props = result['stdout']

    return init_props


def lv_run_cmd(module, cmd, success_msg, fail_msg, init_props=None, fetch=False):
    """
    Helper function for running commands to create/modify a
    logical volume.
    return: True - if any of the logical volume properties are modified
            False - if nothing changed
    """

    if success_msg is None:
        success_msg = ""

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] += fail_msg
        module.fail_json(**result)
    else:
        if (init_props is None) or (init_props != get_lv_props(module)):
            result['msg'] += success_msg
            if not fetch:
                result['cmd'] = cmd
                result['changed'] = True


def lv_exists(module):
    """
    Checks if the specified logical volume exists or not.
    arguments:
        module      (dict): The Ansible module
    return:
        true if exists
        false otherwise
    """
    cmd = ["lslv", module.params['lv']]

    rc = module.run_command(cmd)[0]
    if rc == 0:
        return True
    return False


def main():
    """
    Main function
    """

    global result

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['present', 'absent']),
            lv=dict(type='str', required=True, aliases=['logical_volume']),
            vg=dict(type='str'),
            lv_type=dict(type='str', default='jfs2'),
            strip_size=dict(type='str'),
            extra_opts=dict(type='str', default=''),
            copies=dict(type='int', default=1),
            size=dict(type='str'),
            pv_list=dict(type='list', elements='str'),
            policy=dict(type='str', default='maximum', choices=['maximum', 'minimum']),
            lv_new_name=dict(type='str'),
        ),
        required_if=[
            ['state', 'present', ['vg']],
        ],
        supports_check_mode=False,
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    name = module.params['lv']
    state = module.params['state']

    if state == 'present':
        if lv_exists(module):
            # get initial lv properties to compare with the final
            # state to check if something has changed with the lv
            init_props = get_lv_props(module)
            if module.params['size']:
                extend_lv(module, name, init_props)
                # make sure the the new init props is passed to modify_lv
                # in the case where the logical volume is extended
                if result['changed']:
                    init_props = get_lv_props(module)
            modify_lv(module, name, init_props)
            if not result['changed']:
                result['msg'] += f"No changes were needed on logical volume {name}."
        else:
            create_lv(module, name)
    else:
        if lv_exists(module):
            remove_lv(module, name)
        else:
            result['msg'] = \
                f"Logical volume {name} does not exist, there is no need to remove \
                    the logical volume."

    module.exit_json(**result)


if __name__ == '__main__':
    main()
