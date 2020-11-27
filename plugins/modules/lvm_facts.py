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
module: lvm_facts
short_description: Reports LVM information as facts.

description:
- List and reports details about defined AIX Logical Volume Manager (LVM) components such as
  Physical volumes, Logical volumes and Volume groups in Ansible facts.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  name:
    description:
    - Specifies the name of a LVM component.
    type: str
    default: 'all'
  component:
    description:
    - Specifies the type of LVM component to report information.
      A(pv) specifies physical volume.
      A(lv) specifies logical volume.
      A(vg) specifies volume group.
      C(all) specifies all previous LVM components to be reported.
    type: str
    choices: [pv, lv, vg, all]
    default: 'all'
  lvm:
    description:
    - Users can provide the existing LVM facts to which the queried facts should be updated.
      If not specified, the LVM facts in the ansible_facts will be replaced.
    type: dict
    default: {}

'''

EXAMPLES = r'''
- name: Gather all lvm facts
  lvm_facts:
- name: Gather VG facts
  lvm_facts:
    name: all
    component: vg
- name: Update PV facts to existing LVM facts
  lvm_facts:
    name: all
    component: pv
    lvm: "{{ ansible_facts.LVM }}"
- name: Gather LV facts
  lvm_facts:
    name: all
    component: lv
'''

RETURN = r'''
ansible_facts:
  description:
  - Facts to add to ansible_facts about the LVM components on the system.
  returned: always
  type: complex
  contains:
    lvm:
      description:
      - Contains a list of VGs, PVs and LVs.
      returned: success
      type: dict
      elements: dict
      contains:
        VGs:
          description:
          - Contains the list of volume groups on the system.
          returned: success
          type: dict
          elements: dict
          contains:
            name:
              description:
              - Volume Group name.
              returned: always
              type: str
              sample: "rootvg"
            vg_state:
              description:
              - State of the Volume Group.
              returned: always
              type: str
              sample: "active"
            num_lvs:
              description:
              - Number of logical volumes.
              returned: always
              type: str
              sample: "2"
            num_pvs:
              description:
              - Number of physical volumes.
              returned: always
              type: str
              sample: "2"
            total_pps:
              description:
              - Total number of physical partitions within the volume group.
              returned: always
              type: str
              sample: "952"
            free_pps:
              description:
              - Number of physical partitions not allocated.
              returned: always
              type: str
              sample: "100"
            pp_size:
              description:
              - Size of each physical partition.
              returned: always
              type: str
              sample: "64 megabyte (s)"
            size_g:
              description:
              - Total size of the volume group in gigabytes.
              returned: always
              type: str
              sample: "18.99"
            free_g:
              description:
              - Free space of the volume group in gigabytes.
              returned: always
              type: str
              sample: "10.6"
        PVs:
          description:
          - Contains a list of physical volumes on the system.
          returned: success
          type: dict
          elements: dict
          contains:
            name:
              description:
              - PV name
              returned: always
              type: str
              sample: "hdisk0"
            vg:
              description:
              - Volume group to which the physical volume has been assigned.
              returned: always
              type: str
              sample: "rootvg"
            pv_state:
              description:
              - Physical volume state.
              returned: always
              type: str
              sample: "active"
            total_pps:
              description:
              - Total number of physical partitions in the physical volume.
              returned: always
              type: str
              sample: "476"
            free_pps:
              description:
              - Number of free physical partitions in the physical volume.
              returned: always
              type: str
              sample: "130"
            pp_size:
              description:
              - Size of each physical partition.
              returned: always
              type: str
              sample: "64 megabyte (s)"
            size_g:
              description:
              - Total size of the physical volume in gigabytes.
              returned: always
              type: str
              sample: "18.99"
            free_g:
              description:
              - Free space of the physical volume in gigabytes.
              returned: always
              type: str
              sample: "10.6"
        LVs:
          description:
          - Contains a list of logical volumes on the system.
          returned: success
          type: dict
          elements: dict
          contains:
            name:
              description:
              - Logical volume name.
              returned: always
              type: str
              sample: "hd1"
            vg:
              description:
              - Volume group to which the Logical Volume belongs to.
              returned: always
              type: str
              sample: "rootvg"
            lv_state:
              description:
              - Logical Volume state.
              returned: always
              type: str
              sample: "active"
            type:
              description:
              - Logical volume type.
              returned: always
              type: str
              sample: "jfs2"
            LPs:
              description:
              - Total number of logical partitions in the logical volume.
              returned: always
              type: str
              sample: "476"
            PPs:
              description:
              - Total number of physical partitions in the logical volume.
              returned: always
              type: str
              sample: "130"
            PVs:
              description:
              - Number of physical volumes used by the logical volume.
              returned: always
              type: str
              sample: "2"
            mount_point:
              description:
              - File system mount point for the logical volume, if applicable.
              returned: always
              type: str
              sample: "/home"
'''

from ansible.module_utils.basic import AnsibleModule


def load_pvs(module, name, LVM):
    """
    Get the details for the specified PV or all
    arguments:
        module  (dict): Ansible module argument spec.
        name     (str): physical volume name.
        LVM     (dict): LVM facts.
    return:
        msg  (str): message
        LVM (dict): LVM facts
    """
    msg = ""
    cmd = "lspv"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg += "Command '%s' failed." % cmd
    else:
        for ln in stdout.splitlines():
            fields = ln.split()
            if (name != 'all' and name != fields[0]):
                continue
            cmd = "lspv -L %s" % fields[0]
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                msg += "Command '%s' failed." % cmd
            else:
                pv_state = stdout.splitlines()[2].split()[2].strip()
                pp_size = stdout.splitlines()[4].split()[2].strip()
                total_pps = stdout.splitlines()[5].split()[2].strip()
                free_pps = stdout.splitlines()[6].split()[2].strip()
                size_g = int(total_pps) * int(pp_size) / 1024
                free_g = int(free_pps) * int(pp_size) / 1024
                data = {
                    'vg': fields[2],
                    'pv_state': pv_state,
                    'pp_size': "%s megabytes" % pp_size,
                    'total_pps': total_pps,
                    'free_pps': free_pps,
                    'size_g': str(size_g),
                    'free_g': str(free_g)
                }
                LVM['PVs'][fields[0]] = data

    return msg, LVM


def load_vgs(module, name, LVM):
    """
    Get the details for the specified VG or all
    arguments:
        module  (dict): Ansible module argument spec.
        name     (str): volume group name.
        LVM     (dict): LVM facts.
    return:
        msg  (str): message
        LVM (dict): LVM facts
    """
    msg = ""
    cmd = "lsvg"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg += "Command '%s' failed." % cmd
    else:
        for ln in stdout.splitlines():
            vg = ln.split()[0].strip()
            if (name != 'all' and name != vg):
                continue
            cmd = "lsvg %s" % vg
            rc, out, err = module.run_command(cmd)
            if rc != 0:
                msg += "Command '%s' failed." % cmd
            else:
                vg_state = out.splitlines()[1].split()[2].strip()
                num_lvs = out.splitlines()[4].split()[1].strip()
                num_pvs = out.splitlines()[6].split()[2].strip()
                pp_size = out.splitlines()[1].split()[5].strip()
                total_pps = out.splitlines()[2].split()[5].strip()
                free_pps = out.splitlines()[3].split()[5].strip()
                size_g = int(total_pps) * int(pp_size) / 1024
                free_g = int(free_pps) * int(pp_size) / 1024
                data = {
                    'num_lvs': num_lvs,
                    'num_pvs': num_pvs,
                    'vg_state': vg_state,
                    'pp_size': "%s megabytes" % pp_size,
                    'total_pps': total_pps,
                    'free_pps': free_pps,
                    'size_g': str(size_g),
                    'free_g': str(free_g)
                }
                LVM['VGs'][vg] = data
    return msg, LVM


def load_lvs(module, name, LVM):
    """
    Get the details for the specified LV or all
    arguments:
        module  (dict): Ansible module argument spec.
        name     (str): logical volume name.
        LVM     (dict): LVM facts.
    return:
        msg  (str): message
        LVM (dict): LVM facts
    """
    msg = ""
    cmd = "lsvg"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg += "Command '%s' failed." % cmd
    else:
        for line in stdout.splitlines():
            vg = line.split()[0].strip()
            cmd = "lsvg -l %s" % vg
            rc, out, err = module.run_command(cmd)
            if rc != 0:
                msg += "Command '%s' failed." % cmd
            else:
                for ln in out.splitlines()[2:]:
                    lv_info = ln.split()
                    lv = lv_info[0].strip()
                    if (name != 'all' and name != lv):
                        continue
                    type = lv_info[1].strip()
                    lv_state = lv_info[5].strip()
                    lps = lv_info[2].strip()
                    pps = lv_info[3].strip()
                    pvs = lv_info[4].strip()
                    mnt_pt = lv_info[6].strip()
                    data = {
                        'type': type,
                        'vg': vg,
                        'PVs': pvs,
                        'lv_state': lv_state,
                        'PPs': pps,
                        'LPs': lps,
                        'mount point': mnt_pt
                    }
                    LVM['LVs'][lv] = data
    return msg, LVM


def main():
    module = AnsibleModule(
        argument_spec=dict(
            component=dict(type='str', default='all', choices=['pv', 'lv', 'vg', 'all']),
            name=dict(type='str', default='all'),
            lvm=dict(type='dict', default={}),
        ),
        supports_check_mode=False
    )
    msg = ""
    type = module.params['component']
    name = module.params['name']
    LVM = module.params['lvm']
    if type == 'vg' or type == 'all':
        if 'VGs' not in LVM:
            LVM['VGs'] = {}
        msg, LVM = load_vgs(module, name, LVM)
    if type == 'pv' or type == 'all':
        if 'PVs' not in LVM:
            LVM['PVs'] = {}
        msg, LVM = load_pvs(module, name, LVM)
    if type == 'lv' or type == 'all':
        if 'LVs' not in LVM:
            LVM['LVs'] = {}
        msg, LVM = load_lvs(module, name, LVM)

    module.exit_json(msg=msg, ansible_facts=dict(LVM=LVM))


if __name__ == '__main__':
    main()
