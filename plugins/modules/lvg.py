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
- AIX Development Team (@pbfinley1911)
module: lvg
short_description: Configure AIX LVM volume groups
description:
- This module creates, removes, modifies attributes, resizes, activates and deactivates volume
  groups.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
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
    - Can be used only when creating a volume group, hence when I(state=present).
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
    default: none
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
- name: Extend a volume group
  ibm.power_aix.lvg:
    pvs=hdisk1
    vg_name=datavg
    state=present

- name: Varyon a volume group
  ibm.power_aix.lvg:
    vg_name=datavg
    state=varyon
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

from ansible.module_utils.basic import AnsibleModule

result = None


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
    global result

    cmd = 'lsvg -o'
    rc, active_vgs, stderr = module.run_command(cmd)
    if rc != 0:
        result['msg'] = "Command '%s' failed." % cmd
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = active_vgs
        result['stderr'] = stderr
        module.fail_json(**result)

    rc, all_vgs, stderr = module.run_command("lsvg")
    if rc != 0:
        result['msg'] = "Command 'lsvg' failed."
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = all_vgs
        result['stderr'] = stderr
        module.fail_json(**result)

    if vg_name in all_vgs and vg_name not in active_vgs:
        return False

    if vg_name in active_vgs:
        return True

    return None


def change_vg(module, vg_name, vg_state):
    """
    Modifies/Extends volume group
    arguments:
        module: Ansible module argument spec.
        vg_name: Volume group name
        vg_state: Volume group state
    note:
        Exits with fail_json in case of error
    return:
        none
    """
    global result
    pvs = module.params['pvs']
    force = module.params['force']
    fopt = ""
    if force:
        fopt = "-f "

    if module.params["major_num"] or module.params["pp_size"] or module.params["mirror_pool"]:
        result['msg'] = "Attributes major_num, pp_size and mirror_pool are not supported while changing volume group %s." % vg_name
        module.fail_json(**result)

    # if pvs, extend the volume group
    # if other attributes specified, change that too

    if pvs:
        # extend VG
        cmd = "extendvg %s %s %s" % (fopt, vg_name, ' '.join(pvs))
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            result['msg'] = "Failed to extend volume group %s. Command '%s' failed.\n" % (vg_name, cmd)
            result['cmd'] = cmd
            result['rc'] = rc
            result['stdout'] = stdout
            result['stderr'] = stderr
            module.fail_json(**result)

        result['msg'] = "Volume group %s extended.\n" % vg_name

    # Change other VG attributes
    vg_type = module.params["vg_type"]
    enhanced_con_vg = module.params["enhanced_concurrent_vg"]
    critical_pvs = module.params["critical_pvs"]
    mpool_strict = module.params["mirror_pool_strict"]
    multi_node_vary = module.params["multi_node_vary"]
    auto_on = module.params["auto_on"]
    retry = module.params["retry"]
    num_partitions = module.params["num_partitions"]
    critical_vg = module.params["critical_vg"]
    pp_limit = module.params["pp_limit"]
    num_lvs = module.params["num_lvs"]

    opt = ''
    if vg_type == "big":
        opt += '-B '
    elif vg_type == "scalable":
        opt += '-G '

    if enhanced_con_vg:
        opt += '-C '

    if critical_pvs is True:
        opt += "-e y "
    elif critical_pvs is False:
        opt += "-e n "

    if mpool_strict == 'strict':
        opt += "-M s "
    elif mpool_strict == 'normal':
        opt += "-M y "
    elif mpool_strict == 'none':
        opt += "-M n "

    if multi_node_vary is True:
        opt += "-N o "
    elif multi_node_vary is False:
        opt += "-N n "

    if auto_on is True:
        opt += "-a y "
    elif auto_on is False:
        opt += "-a n "

    if retry is True:
        opt += "-O y "
    elif retry is False:
        opt += "-O n "

    if num_partitions:
        opt += "-P %s " % num_partitions

    if critical_vg is True:
        opt += "-r y "
    elif critical_vg is False:
        opt += "-r n "

    if pp_limit:
        opt += "-t %s " % pp_limit

    if num_lvs:
        opt += "-v %s " % num_lvs

    if opt:
        cmd = "chvg %s %s %s " % (opt, fopt, vg_name)

        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] += "Failed to modify volume group %s attributes. Command '%s' failed." % (vg_name, cmd)
            module.fail_json(**result)

        result['msg'] += "Volume group %s modified.\n" % vg_name
        result['changed'] = True

    return


def make_vg(module, vg_name, vg_state):
    """
    Creates volume group
    arguments:
        module:     Ansible module argument spec.
        vg_name:    Volume group name
        vg_state:   Volume group state
    note:
        Exits with fail_json in case of error
    return:
        none
    """
    global result

    pvs = module.params['pvs']

    cmd = "mkvg "

    vg_type_opt = {
        "none": '',
        "big": '-B ',
        "scalable": '-S ',
    }

    vg_type = module.params["vg_type"]
    if vg_type:
        cmd += vg_type_opt[vg_type]

    enhanced_con_vg = module.params["enhanced_concurrent_vg"]
    if enhanced_con_vg:
        cmd += '-C '

    critical_pvs = module.params["critical_pvs"]
    if critical_pvs:
        cmd += '-e y '

    force = module.params["force"]
    if force:
        cmd += '-f '

    mpool_opt = {
        'none': '',
        'normal': '-M y ',
        'strict': '-M s ',
    }
    mpool_strict = module.params["mirror_pool_strict"]
    if mpool_strict:
        cmd += mpool_opt[mpool_strict]

    if module.params["multi_node_vary"] is False:
        cmd += '-N n '

    if module.params["auto_on"] is False:
        cmd += '-n '

    if module.params["retry"]:
        cmd += '-O y '

    mirror_pool = module.params["mirror_pool"]
    if mirror_pool:
        cmd += "-p %s " % mirror_pool

    num_partitions = module.params["num_partitions"]
    if num_partitions:
        cmd += "-P %s " % num_partitions

    critical_vg = module.params["critical_vg"]
    if critical_vg:
        cmd += "-r y "

    pp_size = module.params["pp_size"]
    if pp_size:
        cmd += "-s %s " % pp_size

    pp_limit = module.params["pp_limit"]
    if pp_limit:
        cmd += "-t %s " % pp_limit

    major_num = module.params["major_num"]
    if major_num:
        cmd += "-V %s " % major_num

    num_lvs = module.params["num_lvs"]
    if num_lvs:
        cmd += "-v %s " % num_lvs

    cmd += "-y %s %s" % (vg_name, ''.join(pvs))

    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = "Failed to create volume group %s. Command '%s' failed." % (vg_name, cmd)
        module.fail_json(**result)

    result['msg'] = "Volume group %s created." % vg_name
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
    global result

    if vg_state is None:
        result['msg'] = "Volume group %s does not exist." % vg_name
        module.fail_json(**result)

    if state == 'varyon':
        if vg_state is True:
            result['msg'] = "Volume group %s is already active." % vg_name
            return

        result['cmd'] = "varyonvg %s" % vg_name
        rc, stdout, stderr = module.run_command(result['cmd'])
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] = "Failed to activate volume group %s. Command '%s' failed." % (vg_name, result['cmd'])
            module.fail_json(**result)

        result['msg'] = "Volume group %s activated." % vg_name
        result['changed'] = True
        return

    elif state == 'varyoff':
        if vg_state is False:
            result['msg'] = "Volume group %s is already deactivated." % vg_name
            return

        result['cmd'] = "varyoffvg %s" % vg_name
        rc, stdout, stderr = module.run_command(result['cmd'])
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] = "Failed to deactivate volume group %s. Command '%s' failed." % (vg_name, result['cmd'])
            module.fail_json(**result)

        result['msg'] = "Volume group %s deactivated." % vg_name
        result['changed'] = True
        return


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
    global result

    pvs = module.params['pvs']

    if vg_state is False:
        result['msg'] = "Volume group %s is deactivated. Unable to reduce volume group." % vg_name
        module.fail_json(**result)

    elif vg_state is None:
        result['msg'] = "Volume group '%s' does not exist. Unable to reduce volume group." % vg_name
        module.fail_json(**result)

    if pvs is None:
        # Determine the pvs to be removed
        cmd = "lsvg -p %s " % vg_name
        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = cmd
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            result['msg'] = "Failed to list PVs of volume group %s. Command '%s' failed." % (vg_name, cmd)
            module.fail_json(**result)
        pvs = []
        for ln in stdout.splitlines()[2:]:
            pvs.append(ln.split()[0])

        msg = "Volume group %s removed." % vg_name
    else:
        msg = "Physical volume(s) '%s' removed from Volume group '%s'." % (' '.join(pvs), vg_name)

    delete_lvs = module.params["delete_lvs"]

    opt = ""
    if delete_lvs:
        opt += "-d -f "

    cmd = "reducevg %s %s %s" % (opt, vg_name, ' '.join(pvs))
    rc, stdout, stderr = module.run_command(cmd)
    result['cmd'] = cmd
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr
    if rc != 0:
        result['msg'] = "Unable to remove '%s'. Command '%s' failed." % (vg_name, cmd)
        module.fail_json(**result)

    result['msg'] = msg
    result['changed'] = True
    return


def main():
    global result

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            state=dict(type='str', choices=['absent', 'present', 'varyoff', 'varyon'], default='present'),
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
            mirror_pool_strict=dict(type='str', choices=['none', 'normal', 'strict'], default='none'),
            multi_node_vary=dict(type='bool'),
            auto_on=dict(type='bool'),
            retry=dict(type='bool'),
            major_num=dict(type='int'),
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
            # VG doesn't exist. Create it
            make_vg(module, vg_name, vg_state)
        else:
            # VG exists and can be in varyon/varyoff state. Extend/Modify it.
            # Some of the VG modifications require VG to be in varyoff/varyon state.
            # If 'pvs' provided, extend VG.
            change_vg(module, vg_name, vg_state)

    elif state == 'absent':
        # Reduce VG if 'pvs' are provided
        # Remove VG if 'pvs' are not provided
        reduce_vg(module, vg_name, vg_state)

    else:
        vary_vg(module, state, vg_name, vg_state)

    module.exit_json(**result)


if __name__ == '__main__':
    main()
