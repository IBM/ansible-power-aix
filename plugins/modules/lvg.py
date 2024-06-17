#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
import re
from ansible.module_utils.basic import AnsibleModule

__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: lvg
short_description: Configure AIX LVM volume groups
description:
- This module creates, removes, modifies attributes, resizes, activates and deactivates volume
  groups.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorizations:
  B(aix.lvm.manage.extend,aix.lvm.manage.change,aix.lvm.manage.create,aix.lvm.manage.remove)'
options:
  state:
    description:
    - Specifies the action to be performed on a volume group.
      C(present) creates, extends or modifies a volume group;
      C(absent) reduces or removes a volume group;
      C(varyon) activates a volume group performing a varyon operation;
      C(varyoff) deactivates a volume group performing a varyoff operation.
    type: str
    choices: [ absent, present, varyoff, varyon ]
    default: present
  vg_name:
    description:
    - Specifies the volume group name.
    type: str
    required: true
  vg_type:
    description:
    - Specifies the type of the volume group.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: str
    choices: [ big, scalable, none ]
  enhanced_concurrent_vg:
    description:
    - Specifies Enhanced Concurrent Capable volume group.
    - Cannot be used on volume groups and systems that do not use the PowerHA SystemMirror enhanced
      scalability (ES) product.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: bool
  critical_vg:
    description:
    - Enables the Critical VG option of the volume group.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: bool
  pvs:
    description:
    - Specifies the list of physical volumes.
    - When I(state=present) and the VG exists, adds the PVs to the existing VG; otherwise creates
      the VG with the PVs.
    - When I(state=absent), removes the PVs from the VG.
    - Can be used when I(state=present) or I(state=absent).
    type: list
    elements: str
  critical_pvs:
    description:
    - Specifies the Critical PVs option for the volume group. If write request failures occur in the
      mirrored logical volume, the PV is marked as missing and it stops sending I/O requests to the
      failed mirrored logical volume.
    - Available only in IBM AIX 7.2 with Technology Level 1, or later.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: bool
  num_lvs:
    description:
    - Number of logical volumes that can be created.
    - Can be used with I(vg_type=scalable) volume groups.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: int
    choices: [ 256, 512, 1024, 2048, 4096 ]
  delete_lvs:
    description:
    - Deallocates existing logical volume partitions and then deletes resultant empty logical
      volumes from the specified physical volumes.
    - B(Attention:) using I(delete_lvs=yes) automatically deletes all logical volume data on the
      physical volume before removing the physical volume from the volume group. If a logical volume
      spans multiple physical volumes, the removal of any of those physical volumes may jeopardize
      the integrity of the entire logical volume.
    - Can be used when I(state=absent).
    type: bool
  num_partitions:
    description:
    - Total number of units of 1024 partitions in the volume group.
    - Can be used with I(vg_type=scalable) volume groups.
    - Default when not set is 32 hence 32k (32768 partitions).
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: int
    choices: [ 32, 64, 128, 256, 512, 768, 1024, 2048 ]
  pp_size:
    description:
    - Sets physical partition size expressed in units of megabytes from 1 (1 MB) through 131072
      (128 GB). It must be equal to a power of 2 (example 1, 2, 4, 8).
    - The default value for 32 and 128 PV volume groups is the lowest value to remain within the
      limitation of 1016 physical partitions per PV.
    - The default value for scalable volume groups is the lowest value to accommodate 2040 physical
      partitions per PV.
    - Can be used when creating a volume group, hence when I(state=present).
    type: int
  pp_limit:
    description:
    - Changes the limit of the number of physical partitions per physical volume.
    - The maximum number of physical partitions per physical volume for this volume group changes to
      I(pp_limit) x 1016.
    - It must be 1 - 16 for 32 PV volume groups and 1 and 64 for 128 PV volume groups.
    - The maximum number of PVs that can be included in the volume group is MaxPVs / I(pp_limit).
    - The default is the lowest value to remain within the physical partition limit of I(pp_limit) x
      1016.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: int
  force:
    description:
    - When I(state=present), forces the volume group to be created on the specified physical volume
      unless the physical volume is part of another volume group in the Device Configuration
      Database or a volume group that is active.
    - Can be used when creating or changing a volume group, hence when I(state=present).  Discaded
      when I(state=absent).
    type: bool
  mirror_pool:
    description:
    - Specifies the mirror pool name to assigns the physical volumes to.
    - After mirror pools are enabled in a volume group, the volume group can no longer be imported
      into a version of AIX that does not support mirror pools.
    - Can be used only when creating/extending a volume group, hence when I(state=present).
    - Mirror pools are only defined for I(vg_type=scalable) type volume group.
    type: str
  mirror_pool_strict:
    description:
    - Enables mirror pool strictness for the volume group.
    - C(none) specifies that no restrictions are placed on the user of mirror pool.
    - C(normal) specifies that mirror pools must be used on each logical volume in the volume group.
    - C(strict) specifies that super-strict mirror pools are enforced on this volume group.
      Partitions allocated for one mirror cannot share a physical volume with the partitions from
      another mirror; with this setting each mirror pool must contain at least one copy of each
      logical volume.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: str
    choices: [ none, normal, strict ]
  multi_node_vary:
    description:
    - Specified that the volume group is allowed to varyon in non-concurrent mode in more than one
      node at the same time or not. This is the default behavior.
    - This option is not available for volume groups varied on in the concurrent mode.
    - This VG can no longer be imported on a version of AIX that does not support this flag.
    - When I(multi_node_vary=no) the VG can no longer be imported on a version of AIX that does not
      support this mode.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: bool
  auto_on:
    description:
    - Specifies that the volume group is automatically available during a system restart.
    - By default I(auto_on=yes) when creating a volume group.
    - Can be used when creating or changing a volume group, hence when I(state=present).
    type: bool
  retry:
    description:
    - Enables the infinite retry option of the logical volume.
    - When (retry=no), a failing I/O of the logical volume is not retried. This is the default
      behavior.
    - When (retry=yes), a failed I/O request is retried until it is successful.
    type: bool
  major_num:
    description:
    - Specifies the major number of the volume group that is created.
    - Can be used only when creating a volume group, hence when I(state=present).
    type: int
  quorum:
    description:
    - Enables/disables quorum on the volume group.
    - Can be used while changing an existing volume group, hence when I(state=present).
    type: bool
notes:
  - B(Attention:) using I(state=absent) with I(delete_lvs=yes) automatically deletes all logical
    volume data on the physical volume before removing the physical volume from the volume group.
    If a logical volume spans multiple physical volumes, the removal of any of those physical
    volumes may jeopardize the integrity of the entire logical volume.
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chvg.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/e_commands/extendvg.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mkvg.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/reducevg.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/v_commands/varyonvg.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/v_commands/varyoffvg.html).
'''

EXAMPLES = r'''
- name: Create a scalable volume group with a mirror pool
  ibm.power_aix.lvg:
    state: present
    vg_name: datavg
    pvs: hdisk1
    vg_type: scalable
    mirror_pool: mp1

- name: Create a volume group with multiple physical volumes
  ibm.power_aix.lvg:
    state: present
    vg_name: datavg
    pvs: hdisk1 hdisk2 hdisk3

- name: Extend a volume group
  ibm.power_aix.lvg:
    state: present
    vg_name: datavg
    pvs: hdisk1

- name: Remove a volume group
  ibm.power_aix.lvg:
    state: absent
    vg_name: datavg

- name: Removing hdisk1 and hdisk2 physical volumes from a volume group
  ibm.power_aix.lvg:
    state: absent
    vg_name: datavg
    pvs: hdisk1 hdisk2

- name: Varyon a volume group
  ibm.power_aix.lvg:
    vg_name: datavg
    state: varyon

- name: Varyoff a volume group
  ibm.power_aix.lvg:
    state: varyoff
    vg_name: datavg
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Volume group 'rootvg' activated."
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
    sample: 'datavg'
stderr:
    description: The standard error of the command.
    returned: always
    type: str
    sample: '0516-321 mkvg: Physical volume rootvg is not configured.\n
             0516-306 mkvg: Unable to find physical volume hdisk3 in the Device Configuration Database.\n
             0516-862 mkvg: Unable to create volume group.'
'''

result = None
MAX_PP_PER_SMALL_VG = 32512
MAX_PP_PER_BIG_VG = 130048


####################################################################################
# Action Handler Functions
####################################################################################
def make_vg(module, vg_name):
    """
    Creates volume group
    arguments:
        module:     Ansible module argument spec.
        vg_name:    Volume group name
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    pvs = module.params['pvs']
    opt = build_vg_opts(module)

    vg_type_opt = {
        "none": '',
        "big": '-B ',
        "scalable": '-S ',
    }
    vg_type = module.params["vg_type"]
    if vg_type:
        opt += vg_type_opt[vg_type]

    # specify which mirror pool the PVs will be
    # assigned into on creation of the VG
    # NOTE: mirror pools are only for scalable VG
    # this option is ignored in small and big VG
    mirror_pool = module.params["mirror_pool"]
    if mirror_pool:
        opt += f"-p { mirror_pool } "

    # specify the PP size of the VG
    pp_size = module.params["pp_size"]
    if pp_size:
        opt += f"-s { pp_size } "

    # specify the major number of the VG
    major_num = module.params["major_num"]
    if major_num:
        opt += f"-V { major_num } "

    pvs_option = ' '.join(pvs)
    cmd = f"mkvg { opt } -y { vg_name } { pvs_option }"
    success_msg = f"Volume group { vg_name } created."
    fail_msg = f"Failed to create volume group { vg_name }. Command { cmd } failed."
    run_cmd(module, cmd, success_msg, fail_msg)


def extend_vg(module, vg_name, vg_state, init_props):
    """
    Extends a varied on volume group
    arguments:
        module:     Ansible module argument spec.
        vg_name:    Volume group name
        vg_state:   Volume group state
        init_props: Initial properties of the volume group
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    # fail extendvg if vg is varied off
    varied_on = vg_state
    if not varied_on:
        result['rc'] = 1
        result['msg'] = f"Unable to extend volume group { vg_name } because it is not varied on."
        module.fail_json(**result)

    # fetch initial properties of the volume group, include
    # the list of pvs it is associated and their corresponding
    # mirror pool if any.
    pvs = module.params['pvs']
    pvs = ' '.join(pvs).split()
    pv_list = []
    for pv in pvs:
        found = re.search(pv, init_props, re.MULTILINE)
        if not found:
            pv_list.append(pv)

    if len(pv_list) == 0:
        result['rc'] = 0
        return

    opt = ''
    force = module.params['force']
    if force:
        opt += "-f "
    mirror_pool = module.params['mirror_pool']
    if mirror_pool:
        opt += f"-p { mirror_pool } "

    pv_list_option = ' '.join(pv_list)
    cmd = f"extendvg { opt } { vg_name } { pv_list_option }"
    success_msg = f"Volume group { vg_name } extended.\n"
    fail_msg = f"Failed to extend volume group { vg_name }. Command { cmd } failed."
    run_cmd(module, cmd, success_msg, fail_msg, init_props=init_props)
    return


def change_vg(module, vg_name, init_props):
    """
    Modifies volume group
    arguments:
        module: Ansible module argument spec.
        vg_name: Volume group name
        init_props: Initial properties of the volume group
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    major_num = module.params["major_num"]
    pp_size = module.params["pp_size"]
    mirror_pool = module.params["mirror_pool"]
    if major_num or pp_size or mirror_pool:
        result['msg'] += "Attributes major_num, pp_size or mirror_pool "
        result['msg'] += f"are not supported while changing volume group { vg_name }\n"

    # get initial vg type
    pattern = r"^(MAX PPs per VG:)\s+(\d+)"
    max_pp_per_vg = re.search(pattern, init_props, re.MULTILINE)
    max_pp_per_vg = int(max_pp_per_vg.groups()[1])
    if max_pp_per_vg == MAX_PP_PER_SMALL_VG:
        init_vg_type = "small"
    elif max_pp_per_vg == MAX_PP_PER_BIG_VG:
        init_vg_type = "big"
    else:
        init_vg_type = "scalable"

    opt = build_vg_opts(module, modify=True)

    # determine if vg type needs to be changed
    vg_type = module.params["vg_type"]
    if init_vg_type == vg_type:
        result['msg'] += f"Volume group is already { vg_type } VG type."
    elif vg_type == "big":
        opt += '-B '
    elif vg_type == "scalable":
        opt += '-G '

    if opt:
        cmd = f"chvg {opt}{vg_name} "
        success_msg = f"Volume group {vg_name} modified.\n"
        fail_msg = f"Failed to modify volume group {vg_name} attributes. Command {cmd} failed."
        run_cmd(module, cmd, success_msg, fail_msg, init_props=init_props)


def reduce_vg(module, vg_name, vg_state):
    """
    Reduce volume group
    arguments:
        module: Ansible module argument spec.
        vg_name: Volume group name
        vg_state: Volume group state
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    pvs = module.params['pvs']

    if vg_state is False:
        result['msg'] = f"Volume group {vg_name} is deactivated. Unable to reduce volume group."
        module.fail_json(**result)

    elif vg_state is None:
        result['msg'] = f"Volume group {vg_name} does not exist. Unable to reduce volume group."
        module.fail_json(**result)

    # check all pvs in the vg
    init_props = get_vg_props(module, just_pvs=True)
    pvs_in_vg = []
    for ln in init_props.splitlines()[2:]:
        pvs_in_vg.append(ln.split()[0])

    # if the pv list is not specified, remove all pvs
    # to delete the vg
    success_msg = None
    fail_msg = None
    if pvs is None:
        pv_list = pvs_in_vg

    # if the pv list is specified, then filter out the
    # specified pvs that do not belong to the vg
    else:
        pvs = ' '.join(pvs).split()
        pv_list = []
        for pv in pvs:
            if pv in pvs_in_vg:
                pv_list.append(pv)

        if len(pv_list) == 0:
            # no pvs to remove
            return
        if len(pv_list) < len(pvs_in_vg):
            # not all pvs in the vg will be removed
            msg_pvlist = ' '.join(pv_list)
            success_msg = f"Physical volume(s) {msg_pvlist} removed from Volume group {vg_name}."
            fail_msg = f"Failed to remove Physical volume(s) {msg_pvlist} from Volume group {vg_name}."

    # the pvs that will be removed is all the pvs in the vg
    if success_msg is None:
        success_msg = f"Volume group {vg_name} removed."
    if fail_msg is None:
        fail_msg = f"Unable to remove {vg_name}."

    delete_lvs = module.params["delete_lvs"]
    opt = ""
    if delete_lvs:
        opt += "-d -f "

    pv_list_option = ' '.join(pv_list)
    cmd = f"reducevg {opt} {vg_name} {pv_list_option}"
    run_cmd(module, cmd, success_msg, fail_msg)

    return


def vary_vg(module, state, vg_name, vg_state):
    """
    Varyon/off volume group
    arguments:
        module: Ansible module argument spec.
        state: requested action, can be varyon or varyoff
        vg_name: Volume group name
        vg_state: Volume group state
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    if vg_state is None:
        result['msg'] = f"Volume group {vg_name} does not exist."
        module.fail_json(**result)

    if state == 'varyon':
        if vg_state is True:
            result['msg'] += f"Volume group {vg_name} is already active. "
            return

        cmd = f"varyonvg {vg_name}"
        success_msg = f"Volume group {vg_name} activated."
        fail_msg = f"Failed to activate volume group {vg_name}. Command {cmd} failed."
        run_cmd(module, cmd, success_msg, fail_msg)

    elif state == 'varyoff':
        if vg_state is False:
            result['msg'] += f"Volume group {vg_name} is already deactivated. "
            return

        cmd = f"varyoffvg {vg_name}"
        success_msg = f"Volume group {vg_name} deactivated."
        fail_msg = f"Failed to deactivate volume group {vg_name}. Command {cmd} failed."
        run_cmd(module, cmd, success_msg, fail_msg)

    return


####################################################################################
# Helper Functions
####################################################################################
def run_cmd(module, cmd, success_msg, fail_msg, init_props=None, fetch=False):
    """
    Helper function for running commands.
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
        if (init_props is None) or (init_props != get_vg_props(module)):
            result['msg'] += success_msg
            if not fetch:
                result['cmd'] = cmd
                result['changed'] = True


def get_vg_props(module, just_pvs=False):
    """
    Fetches volume group information such as properties and the
    list of physical volumes associated to the volume group.
    arguments:
        module: Ansible module argument spec.
        vg_name: Volume Group name.
    return:
        init_props: string containing volume group info
    """

    vg_name = module.params['vg_name']
    init_props = ''

    if not just_pvs:
        cmd = f"lsvg {vg_name}"
        fail_msg = "Failed to fetch volume group properties."
        run_cmd(module, cmd, None, fail_msg, fetch=True)
        init_props = result['stdout']

    cmd = f"lsvg -p {vg_name}"
    fail_msg = f"Failed to fetch the list of physical volumes associated to \
        volume group {vg_name}."
    run_cmd(module, cmd, None, fail_msg, fetch=True)
    init_props += result['stdout']

    if not just_pvs:
        cmd = f"lsvg -P {vg_name}"
        fail_msg = f"Failed to fetch information regarding mirror pools of volume \
            group {vg_name}"
        run_cmd(module, cmd, None, fail_msg, fetch=True)
        init_props += result['stdout']

    return init_props


def find_vg_state(module, vg_name):
    """
    Determines the current state of volume group.
    arguments:
        module: Ansible module argument spec.
        vg_name: Volume Group name.
    note:
        Exits with fail_json in case of error
    return:
        True - VG in varyon state
        False - VG in varyoff state
        None - VG does not exist
    """

    cmd = 'lsvg -o'
    fail_msg = f"Command {cmd} failed."
    run_cmd(module, cmd, None, fail_msg, fetch=True)
    active_vgs = result['stdout']

    cmd = 'lsvg'
    fail_msg = f"Command {cmd} failed."
    run_cmd(module, cmd, None, fail_msg, fetch=True)
    all_vgs = result['stdout']

    if vg_name in all_vgs and vg_name not in active_vgs:
        return False
    if vg_name in active_vgs:
        return True
    return None


def build_vg_opts(module, modify=False):
    """
    Builds the options used together when calling mkvg/chvg command.
    arguments:
        module: Ansible module argument spec.
        modify: Specify if we are building options for chvg
    return:
        opts: The options that will be used of mkvg or chvg command
    """
    opt = ''

    # specify force option
    force = module.params['force']
    if force:
        opt += '-f '

    # specify if enhanced concurrent mode is enabled
    enhanced_con_vg = module.params["enhanced_concurrent_vg"]
    if enhanced_con_vg:
        opt += '-C '

    # specify critical PV option
    critical_pvs = module.params["critical_pvs"]
    if critical_pvs is True:
        opt += "-e y "
    elif critical_pvs is False:
        opt += "-e n "

    # specify mirror pool strictness policy
    mpool_strict = module.params["mirror_pool_strict"]
    if mpool_strict == 'strict':
        opt += "-M s "
    elif mpool_strict == 'normal':
        opt += "-M y "
    elif (not modify and mpool_strict is None) or (mpool_strict == 'none'):
        opt += "-M n "

    # specify if the VG can be varied on in non-concurrent mode
    # in multiple nodes
    multi_node_vary = module.params["multi_node_vary"]
    if multi_node_vary is True:
        opt += "-N o "
    elif multi_node_vary is False:
        opt += "-N n "

    # specify if VG is automatically activated during system startup
    auto_on = module.params["auto_on"]
    if modify:
        if auto_on is True:
            opt += "-a y "
        elif auto_on is False:
            opt += "-a n "
    else:
        if auto_on is False:
            opt += "-n "

    # specify VG infinite retry option
    retry = module.params["retry"]
    if retry is True:
        opt += "-O y "
    elif retry is False:
        opt += "-O n "

    # specify VG quorum option
    quorum = module.params["quorum"]
    if modify:
        if quorum is True:
            opt += "-Q y "
        elif quorum is False:
            opt += "-Q n "

    # specify total number of partitions in the VG
    # NOTE: this is only available for scalable VG
    num_partitions = module.params["num_partitions"]
    if num_partitions:
        opt += f"-P {num_partitions} "

    # specify the critical VG option
    critical_vg = module.params["critical_vg"]
    if critical_vg is True:
        opt += "-r y "
    elif critical_vg is False:
        opt += "-r n "

    # specify the PP limit per PV factor
    pp_limit = module.params["pp_limit"]
    if pp_limit:
        opt += f"-t {pp_limit} "

    # specify the number of LVs that can be
    # created in the VG
    num_lvs = module.params["num_lvs"]
    if num_lvs:
        opt += f"-v {num_lvs} "

    return opt


####################################################################################
# Main Function
####################################################################################
def main():
    global result

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            state=dict(type='str', choices=['absent', 'present', 'varyoff', 'varyon'],
                       default='present'),
            vg_name=dict(type='str', required=True),
            vg_type=dict(type='str', choices=['none', 'big', 'scalable']),
            enhanced_concurrent_vg=dict(type='bool'),
            critical_vg=dict(type='bool'),
            pvs=dict(type='list', elements='str'),
            critical_pvs=dict(type='bool'),
            num_lvs=dict(type='int', choices=[256, 512, 1024, 2048, 4096]),
            delete_lvs=dict(type='bool'),
            num_partitions=dict(type='int', choices=[32, 64, 128, 256, 512, 768, 1024, 2048]),
            pp_size=dict(type='int'),
            pp_limit=dict(type='int'),
            force=dict(type='bool'),
            mirror_pool=dict(type='str'),
            mirror_pool_strict=dict(type='str', choices=['none', 'normal', 'strict']),
            multi_node_vary=dict(type='bool'),
            auto_on=dict(type='bool'),
            retry=dict(type='bool'),
            major_num=dict(type='int'),
            quorum=dict(type='bool'),
        ),
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    vg_name = module.params["vg_name"]

    vg_state = find_vg_state(module, vg_name)

    state = module.params['state']

    if state == 'present':
        if vg_state is None:
            # Creating VG does not support quorum option
            quorum = module.params['quorum']
            if quorum:
                result['msg'] += f"Attribute quorum is not supported while \
                    changing volume group {vg_name}.\n"
                module.fail_json(**result)

            # VG doesn't exist. Create it
            make_vg(module, vg_name)
        else:
            # get initial properties of VG
            init_props = get_vg_props(module)

            # If 'pvs' provided, extend VG.
            if module.params['pvs']:
                extend_vg(module, vg_name, vg_state, init_props)

            # VG exists and can be in varyon/varyoff state. Extend/Modify it.
            # Some of the VG modifications require VG to be in varyoff/varyon state.
            change_vg(module, vg_name, init_props)

    elif state == 'absent':
        # Reduce VG if 'pvs' are provided
        # Remove VG if 'pvs' are not provided
        reduce_vg(module, vg_name, vg_state)

    else:
        vary_vg(module, state, vg_name, vg_state)

    if (result['msg'] == '') or (not result['changed']):
        result['msg'] += f"No changes were needed on volume group {vg_name}."

    module.exit_json(**result)


if __name__ == '__main__':
    main()
