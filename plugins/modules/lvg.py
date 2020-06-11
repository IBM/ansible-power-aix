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
short_description: Create/Modify/Remove a volume group
description:
- This module facilitates
    a. Creation of a volume group
    b. Modification of attributes of an existing volume group
    c. Extension of a volume group
    d. Varyon/Varyoff of a volume group
    e. Reduction/Removal of a volume group
version_added: '2.9'
requirements: [ AIX ]
options:
  vg_type:
    description:
    - Specifies the type of the volume group.
    type: str
    choices: [ big, scalable, none ]
  enhanced_con_vg:
    description:
    - Specifies Enhanced Concurrent Capable volume group.
    type: bool
  critical_pvs:
    description:
    - Specifies the Critical PVs option for the volume group. If write request
      failures occur in the mirrored logical volume, the PV is marked as missing
      and it stops sending I/O requests to the failed mirrored logical volume.
    type: bool
  force:
    description:
    - When I(state=present), forces the volume group to be created on the specified
      physical volume unless the physical volume is part of another volume group
      in the Device Configuration Database or a volume group that is active.

      When I(state=absent), removes the requirement for user confirmation when
      delete_lvs has been specified
    type: bool
  delete_lvs:
    description:
    - When I(state=absent), deallocates the existing logical volume partitions and
      then deletes resultant empty logical volumes
    type: bool
  mpool_strict:
    description:
    - Enables mirror pool strictness for the volume group.
    type: str
    choices: [ none, normal, strict ]
  multi_node_vary:
    description:
    - Creates a volume group that is allowed to varyon in non-concurrent mode in
      more than one node at the same time
    type: bool
  sysstart_avail:
    description:
    - Specifies that the volume group is automatically available during a
      system restart
    type: bool
  retry:
    description:
    - Enables the infinite retry option of the logical volume.
    type: bool
  mpool:
    description:
    - Assigns each of the physical volumes that are being added to the specified
      mirror pool
    type: str
  num_partitions:
    description:
    - Total number of partitions in the volume group
      This attribute is valid for scalable volume groups.
    type: int
  critical_vg:
    description:
    - Enables the Critical VG option of the volume group
    type: bool
  pp_size:
    description:
    - Sets the number of megabytes in each physical partition, which is expressed
      in units of megabytes from 1 (1 MB) through 131072 (128 GB)
    type: int
  pp_limit:
    description:
    - Changes the limit of the number of physical partitions per physical volume.
      It must be 1 - 16 for 32 PV volume groups and 1 and 64 for 128 PV volume groups
    type: int
  major_num:
    description:
    - Specifies the major number of the volume group that is created
    type: int
  num_lvs:
    description:
    - Number of logical volumes that can be created.
      This attribute is valid for only scalable volume groups
    type: int
  vg_name:
    description:
    - Specifies the volume group name
    type: str
    required: true
  state:
    description:
    - Specifies the action to be performed on a VG.
      I(present) - Create/Extends/Modifies VG,
      I(absent) - Reduce/Remove VG,
      I(varyon) - Varyon VG,
      I(varyoff) - Varyoff VG
    type: str
    choices: [ absent, present, varyoff, varyon ]
    default: present
  pvs:
    description:
    - Comma separated list of physical volumes
    type: list
    elements: str
'''

EXAMPLES = r'''
- name: Extend a volume group
  lvg:
    pvs=hdisk1
    vg_name=datavg
    state=present

- name: Varyon a volume group
  lvg:
    vg_name=datavg
    state=varyon
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Volume group 'rootvg' is in varyon state."
stdout:
    description: The standard output
    returned: always
    type: str
    sample: 'datavg'
stderr:
    description: The standard error
    returned: always
    type: str
    sample: '0516-321 mkvg: Physical volume rootvg is not configured.\n
             0516-306 mkvg: Unable to find physical volume hdisk3 in the Device Configuration Database.\n
             0516-862 mkvg: Unable to create volume group.'
'''

from ansible.module_utils.basic import AnsibleModule


def find_vg_state(module, vg_name):
    """
    Determines the current state of volume group.
    param module: Ansible module argument spec.
    param vg_name: Volume Group name.
    return: True - VG in varyon state / False - VG in varyoff state /
             None - VG does not exist
    """
    rc, active_vgs, stderr = module.run_command("lsvg -o")
    if rc != 0:
        module.fail_json("Command 'lsvg -o' failed.")

    rc, all_vgs, stderr = module.run_command("lsvg")
    if rc != 0:
        module.fail_json("Command 'lsvg' failed.")

    if vg_name in all_vgs and vg_name not in active_vgs:
        return False

    if vg_name in active_vgs:
        return True

    return None


def change_vg(module, vg_name, vg_state):
    """
    Modifies/Extends volume group
    param module: Ansible module argument spec.
    param vg_name: Volume group name
    param vg_state: Volume group state
    return: changed - True/False(vg state modified or not),
            msg - message
    """
    msg = ""
    pvs = module.params['pvs']
    force = module.params['force']
    fopt = ""
    if force:
        fopt = "-f "

    # if pvs, extend the volume group
    # if other attributes specified, change that too

    if pvs:
        # extend VG
        cmd = "extendvg %s %s %s" % (fopt, vg_name, ' '.join(pvs))
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "Extending volume group %s failed. Command in failure - '%s'\n " % (vg_name, cmd)
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

        msg = "Volume group %s extended.\n" % vg_name

    # Change other VG attributes
    vg_type = module.params["vg_type"]
    enhanced_con_vg = module.params["enhanced_con_vg"]
    critical_pvs = module.params["critical_pvs"]
    mpool_strict = module.params["mpool_strict"]
    multi_node_vary = module.params["multi_node_vary"]
    sysstart_avail = module.params["sysstart_avail"]
    retry = module.params["retry"]
    mpool = module.params["mpool"]
    num_partitions = module.params["num_partitions"]
    critical_vg = module.params["critical_vg"]
    pp_size = module.params["pp_size"]
    pp_limit = module.params["pp_limit"]
    major_num = module.params["major_num"]
    num_lvs = module.params["num_lvs"]

    if (major_num is not None) or (pp_size is not None) or (mpool is not None):
        module.fail_json(msg="Change of volume group attributes major_num/pp_size/mpool is not supported")

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

    if sysstart_avail is True:
        opt += "-a y "
    elif sysstart_avail is False:
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
        if rc != 0:
            msg += "Modification of volume group attributes for %s failed. Command in failure - '%s'" % (vg_name, cmd)
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

        msg += "Modification of Volume group %s succeeded." % vg_name

    return True, msg


def make_vg(module, vg_name, vg_state):
    """
    Creates volume group
    param module: Ansible module argument spec.
    param vg_name: Volume group name
    param vg_state: Volume group state
    return: changed - True/False(vg state modified or not),
            msg - message
    """

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

    enhanced_con_vg = module.params["enhanced_con_vg"]
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
    mpool_strict = module.params["mpool_strict"]
    if mpool_strict:
        cmd += mpool_opt[mpool_strict]

    if module.params["multi_node_vary"] is False:
        cmd += '-N n '

    if module.params["sysstart_avail"] is False:
        cmd += '-n '

    if module.params["retry"]:
        cmd += '-O y '

    mpool = module.params["mpool"]
    if mpool:
        cmd += "-p %s " % mpool

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
    if rc != 0:
        module.fail_json(msg="Creation of volume group %s failed. cmd - '%s'" % (vg_name, cmd), rc=rc, stdout=stdout, stderr=stderr)

    msg = "Creation of Volume group %s succeeded." % vg_name
    return True, msg


def vary_vg(module, state, vg_name, vg_state):

    if vg_state is None:
        module.fail_json(msg="Volume group '%s' does not exist." % vg_name)

    changed = True

    if state == 'varyon':
        if vg_state is True:
            changed = False
            msg = "Volume group '%s' is in varyon state." % vg_name
            return changed, msg

        rc, stdout, stderr = module.run_command("varyonvg %s" % vg_name)
        if rc != 0:
            module.fail_json(msg="Command 'varyonvg' failed.", rc=rc, stdout=stdout, stderr=stderr)

        msg = "Varyon volume group %s completed." % vg_name
        return changed, msg

    elif state == 'varyoff':
        if vg_state is False:
            changed = False
            msg = "Volume group '%s' is in varyoff state." % vg_name
            return changed, msg

        rc, stdout, stderr = module.run_command("varyoffvg %s" % vg_name)
        if rc != 0:
            module.fail_json(msg="Command 'varyoffvg' failed.", rc=rc, stdout=stdout, stderr=stderr)

        msg = "Varyoff volume group %s completed." % vg_name
        return changed, msg


def reduce_vg(module, vg_name, vg_state):

    pvs = module.params['pvs']

    if vg_state is False:
        module.fail_json(msg="Volume group '%s' is in varyoff state. Unable to reduce volume group." % vg_name)

    elif vg_state is None:
        module.fail_json(msg="Volume group '%s' does not exist. Unable to reduce volume group." % vg_name)

    if pvs is None:
        # Determine the pvs to be removed
        cmd = "lsvg -p %s " % vg_name
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            module.fail_json(msg="Command '%s' failed." % cmd, rc=rc, stdout=pvs, stderr=stderr)
        pvs = []
        for ln in stdout.splitlines()[2:]:
            pvs.append(ln.split()[0])

        msg = "Volume group '%s' removed." % vg_name
    else:
        msg = "Physical volume(s) '%s' removed from Volume group '%s'." % (' '.join(pvs), vg_name)

    force = module.params["force"]
    delete_lvs = module.params["delete_lvs"]

    opt = ""
    if delete_lvs:
        opt += "-d "
    if force:
        opt += "-f "

    cmd = "reducevg %s %s %s" % (opt, vg_name, ' '.join(pvs))
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Unable to remove '%s'. Command in failure '%s' " % (vg_name, cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    changed = True
    return changed, msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            vg_type=dict(type='str', choices=["none", "big", "scalable"]),
            enhanced_con_vg=dict(type='bool'),
            critical_pvs=dict(type='bool'),
            force=dict(type='bool'),
            mpool_strict=dict(type='str', choices=["none", "normal", "strict"]),
            multi_node_vary=dict(type='bool'),
            sysstart_avail=dict(type='bool'),
            retry=dict(type='bool'),
            mpool=dict(type='str'),
            num_partitions=dict(type='int'),
            critical_vg=dict(type='bool'),
            pp_size=dict(type='int'),
            pp_limit=dict(type='int'),
            major_num=dict(type='int'),
            num_lvs=dict(type='int'),
            delete_lvs=dict(type='bool'),
            vg_name=dict(type='str', required=True),
            state=dict(type='str', choices=['absent', 'present', 'varyoff', 'varyon'], default='present'),
            pvs=dict(type='list', elements='str')
        ),

    )

    vg_name = module.params["vg_name"]

    vg_state = find_vg_state(module, vg_name)

    state = module.params['state']

    if state == 'present':
        if vg_state is None:
            # VG doesn't exist. Create it
            changed, msg = make_vg(module, vg_name, vg_state)
        else:
            # VG exists and can be in varyon/varyoff state. Extend/Modify it.
            # Some of the VG modifications require VG to be in varyoff/varyon state.
            # If 'pvs' provided, extend VG.
            changed, msg = change_vg(module, vg_name, vg_state)

    elif state == 'absent':
        # Reduce VG if 'pvs' are provided
        # Remove VG if 'pvs' are not provided
        changed, msg = reduce_vg(module, vg_name, vg_state)

    elif state == 'varyon' or state == 'varyoff':
        changed, msg = vary_vg(module, state, vg_name, vg_state)

    else:
        changed = False
        msg = "Invalid state"

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
