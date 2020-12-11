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
short_description: Configure AIX LVM logical volumes
description:
- This module creates, removes and modifies attributes of LVM logical volumes.
version_added: "2.9"
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
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
  size:
    description:
    - Specifies the size of the logical volume to create.
    - Can be used to create a logical volume, hence when I(state=present).
    type: str
  extra_opts:
    description:
    - Any other options to be passed by the user to mklv or chlv command
    type: str
  copies:
    description:
    - Specifies number of copies of logical volume
    - Maximum value allowed is 3
    - Can be used to create a logical volume, hence when I(state=present).
    type: int
    default: 1
  num_of_logical_partitions:
    description:
    - Specifies the number of logical partitions
    - Can be used to create a logical volume, hence when I(state=present).
    type: int
    default: 1
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
    size: 64M
- name: Create a logical volume of 32M with disks testdisk1 and testdisk2
  ibm.power_aix.lvol:
    vg: test2vg
    lv: test2lv
    size: 32M
    pvs: [ testdisk1, testdisk2 ]
- name: Create a logical volume of 32M with a minimum placement policy
  ibm.power_aix.lvol:
    vg: rootvg
    lv: test4lv
    size: 32M
    policy: minimum
- name: Create a logical volume with extra options like mirror pool
  ibm.power_aix.lvol:
    vg: testvg
    lv: testlv
    size: 128M
    extra_opts: -p copy1=poolA -p copy2=poolB
- name: Remove the logical volume
  ibm.power_aix.lvol:
    vg: test1vg
    lv: test1lv
    state: absent
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

from ansible.module_utils.basic import AnsibleModule

result = None


def create_modify_lv(module):
    """
    Creates/Modify a logical volume with the attributes provided in the
    lv_attributes field.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        none
    """
    global result

    name = module.params['lv']
    new_name = module.params['lv_new_name']
    vg = module.params['vg']
    lv_type = module.params['lv_type']
    size = module.params['size']
    extra_opts = module.params['extra_opts']
    num_log_part = module.params['num_of_logical_partitions']
    copies = module.params['copies']
    policy = module.params['policy']
    if module.params['pv_list']:
        pv_list = ' '.join(module.params['pv_list'])
    else:
        pv_list = ''

    if size is not None:
        isValid, reason = isSizeValid(module)
        if not isValid:
            result['msg'] = "Invalid logical volume %s size: '%s'. %s" % (name, size, reason)
            module.fail_json(**result)

    if policy == 'maximum':
        lv_policy = 'x'
    else:
        lv_policy = 'm'

    exists = lv_exists(module)
    if not exists:
        cmd = "mklv -t %s -y %s -c %s  -e %s %s -S %s %s %s %s" % (lv_type, name, copies, lv_policy, extra_opts, size, vg, num_log_part, pv_list)
    else:
        cmd = "chlv -e %s %s %s" % (lv_policy, extra_opts, name)

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if rc != 0:
        if exists:
            result['msg'] = "Failed to modify logical volume %s. Command '%s' failed." % (name, cmd)
        else:
            result['msg'] += "Failed to create logical volume %s in volume group %s. Command '%s' failed." % (name, vg, cmd)
        module.fail_json(**result)
    else:
        if exists:
            result['msg'] += "Logical volume %s modified." % name
        else:
            result['msg'] += "Logical volume %s created." % name
        result['changed'] = True

    if new_name:
        cmd = 'chlv -n %s %s' % (new_name, name)

        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr

        if rc != 0:
            result['msg'] += "\nFailed to rename %s into %s. Command '%s' failed." % (name, new_name, cmd)
            result['msg'] += "\nCommand given: %s" % cmd
            module.fail_json(**result)
        else:
            result['msg'] += "\nLogical volume %s renamed into %s." % (name, new_name)
            result['changed'] = True
    return


def remove_lv(module):
    """
    Remove the logical volume without confirmation.
    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        none
    """
    global result
    name = module.params['lv']

    cmd = 'rmlv -f %s' % name

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if rc != 0:
        result['msg'] = "Failed to remove the logical volume: %s" % name
        module.fail_json(**result)
    else:
        result['msg'] = "Logical volume %s removed." % name
    return


def isSizeValid(module):
    """
    Checks if the specified size for the logical volume is valid or not.

    arguments:
        size     (str): size of the logical volume
    return:
        valid  (bool): true if valid, false if not valid
        reason  (str): message for the size invalidity
    """
    global result
    reason = ""
    valid = True

    size = module.params['size']
    num_size = int(size[:-1])

    isPowerof2 = (num_size and (not(num_size & (num_size - 1))))
    if not isPowerof2:
        valid = False
        reason = "Must be a power of 2. "

    unit = size[-1].upper()
    units = ['K', 'M']
    try:
        mult = 1024 ** units.index(unit)
    except ValueError:
        valid = False
        reason = "Valid size unit are K and M."
        return valid, reason    # existing as we cannot compute the size without valid unit

    actual_size = num_size * mult
    if not 4 <= actual_size <= (128 * 1024):
        valid = False
        reason += "Must be between 4K and 128M."

    return valid, reason


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

    rc, out, err = module.run_command(cmd)
    if rc == 0:
        return True
    else:
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
            size=dict(type='str'),
            extra_opts=dict(type='str', default=''),
            copies=dict(type='int', default=1),
            num_of_logical_partitions=dict(type='int', default=1),
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

    if state == 'absent':
        if not lv_exists(module):
            result['msg'] = "Logical volume %s does not exist. State is '%s'." % (name, state)
            module.fail_json(**result)
        remove_lv(module)

    else:
        create_modify_lv(module)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
