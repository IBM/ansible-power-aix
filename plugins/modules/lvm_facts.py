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
module: lvm_facts
short_description: Reports LVM information as facts.

description:
- List and reports details about defined AIX Logical Volume Manager (LVM) components such as
  Physical volumes, Logical volumes and Volume groups in Ansible facts.
version_added: '1.1.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
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

result = None


def load_pvs(module, name, LVM):
    """
    Get the details for the specified PV or all
    arguments:
        module  (dict): Ansible module argument spec.
        name     (str): physical volume name.
        LVM     (dict): LVM facts.
    return:
        warnings (list): List of warning messages
        LVM      (dict): LVM facts
    """
    warnings = []
    cmd = "lspv"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        warnings.append(
            f"Command failed. cmd={cmd} rc={rc} stdout={stdout} stderr={stderr}")
    else:
        for ln in stdout.splitlines():
            fields = ln.split()
            pv = fields[0]
            if (name != 'all' and name != pv):
                continue
            LVM['PVs'][pv] = {
                "PHYSICAL VOLUME": fields[0],
                "PV IDENTIFIER": fields[1]
            }
            if len(fields) > 2:
                LVM['PVs'][pv]["VOLUME GROUP"] = fields[2]
                LVM['PVs'][pv]["vg"] = fields[2]
            if len(fields) > 3:
                LVM['PVs'][pv]["VG_STATE"] = fields[3]
                LVM['PVs'][pv]["vg_state"] = fields[3]

            cmd = f"lspv -L { pv }"
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                warnings.append(f"Command failed. cmd={cmd} rc={rc} stdout={stdout} stderr={stderr}")
                if stderr.find('0516-320') > -1:
                    if fields[2] == "None":
                        del LVM['PVs'][pv]["VOLUME GROUP"]
                        del LVM['PVs'][pv]["vg"]
                elif stderr.find('0516-010') > -1:
                    try:
                        LVM['PVs'][pv] = parse_pvs(module, stdout, pv)
                    except (IndexError, AssertionError) as err:
                        warnings.append(str(err))
            else:
                try:
                    LVM['PVs'][pv] = parse_pvs(module, stdout, pv)
                except (IndexError, AssertionError) as err:
                    warnings.append(str(err))

    return warnings, LVM


def parse_pvs(module, lspv_output, pv_name):
    """
    Parse 'lspv <physicalvolume>' output
    arguments:
        lspv_output (str): Raw output of 'lspv <physicalvolume>' cmd
        pv_name     (str): Physical volume name
    return:
        pv_data    (dict): Dictionary of PV data.
    """
    pv_data = {}
    try:
        first_line = lspv_output.splitlines()[0]
    except IndexError as no_first_line:
        raise IndexError from no_first_line(
            f"Unable to get first line of 'lspv {pv_name}' output. lspv_output={lspv_output}"
        )
    match = re.search('VOLUME GROUP', first_line)
    if match is None:
        msg = f"Unable to parse 'lspv {pv_name}' first line to determine column"
        result['msg'] = msg
        module.fail_json(**result)
    right_col_start_i = match.start()
    for line in lspv_output.splitlines():
        left_col = line[:right_col_start_i]
        right_col = line[right_col_start_i:]
        if 'VG IDENTIFIER' in line:
            # special case
            match = re.search('VG IDENTIFIER', line)
            if match is None:
                msg = f"Unable to parse 'lspv {pv_name}' VG IDENTIFIER line."
                result['msg'] = msg
                module.fail_json(**result)
            left_col = line[:match.start()]
            right_col = 'VG IDENTIFIER:' + line.split()[-1]

        for col in [left_col, right_col]:
            if ':' in col:
                key, value = col.split(':', 1)
                pv_data[key] = value.strip()

    # The following key/values are redundant, but ensure backwards
    # compatibility with previous versions of this module
    pv_data['vg'] = pv_data['VOLUME GROUP']
    pv_data['pv_state'] = pv_data['PV STATE']
    pv_data['pp_size'] = pv_data['PP SIZE']
    for key in pv_data.copy():
        if pv_data[key] == "???????":
            del pv_data[key]
    if pv_data.get('TOTAL PPs') is not None:
        pv_data['total_pps'] = pv_data['TOTAL PPs'].split()[0]
    if pv_data.get('free_pps') is not None:
        pv_data['free_pps'] = pv_data['FREE PPs'].split()[0]
    if pv_data.get('pp_size') is not None:
        pp_size_int = int(pv_data['pp_size'].split()[0])
        if pv_data.get('total_pps') is not None:
            pv_data['size_g'] = int(pv_data['total_pps']) * pp_size_int / 1024
        if pv_data.get('free_pps') is not None:
            pv_data['free_g'] = int(pv_data['free_pps']) * pp_size_int / 1024
    return pv_data


def load_vgs(module, name, LVM):
    """
    Get the details for the specified VG or all
    arguments:
        module  (dict): Ansible module argument spec.
        name     (str): volume group name.
        LVM     (dict): LVM facts.
    return:
        warnings (list): List of warning messages
        LVM      (dict): LVM facts
    """
    warnings = []
    cmd = "lsvg"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        warnings.append(f"Command failed. cmd={cmd} rc={rc} stdout={stdout} stderr={stderr}")
    else:
        for ln in stdout.splitlines():
            vg = ln.split()[0].strip()
            if (name != 'all' and name != vg):
                continue
            cmd = f"lsvg { vg }"
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                warnings.append(f"Command failed. cmd={cmd} rc={rc} stdout={stdout} stderr={stderr}")
                # make sure that varied off volume groups
                # are returned.
                # 0516-010: Volume group must be varied on; use varyonvg command.
                pattern = r"0516-010"
                found = re.search(pattern, stderr)
                if found:
                    data = {
                        'vg_state': "deactivated"
                    }
                    LVM['VGs'][vg] = data
            else:
                try:
                    LVM['VGs'][vg] = parse_vgs(module, stdout, vg)
                except (IndexError, AssertionError) as err:
                    warnings.append(str(err))

    return warnings, LVM


def parse_vgs(module, lsvg_output, vg_name):
    """
    Parse 'lsvg <vg>' output
    arguments:
        lsvg_output (str): Raw output of 'lsvg <vg>' cmd
        vg_name     (str): Volume group name
    return:
        vg_data    (dict): Dictionary of VG data.
    """
    vg_data = {}
    try:
        first_line = lsvg_output.splitlines()[0]
    except IndexError as no_first_line:
        raise IndexError from no_first_line(
            f"Unable to get first line of 'lsvg {vg_name}' output. lsvg_output={lsvg_output}"
        )
    match = re.search('VG IDENTIFIER', first_line)
    if match is None:
        msg = f"Unable to parse 'lsvg {vg_name}' first line to determine column "
        result['msg'] = msg
        module.fail_json(**result)
    right_col_start_i = match.start()
    for line in lsvg_output.splitlines():
        left_col = line[:right_col_start_i]
        right_col = line[right_col_start_i:]
        for col in [left_col, right_col]:
            if ':' in col:
                key, value = col.split(':', 1)
                vg_data[key] = value.strip()

    # The following key/values are redundant, but ensure backwards
    # compatibility with previous versions of this module
    vg_data['num_lvs'] = vg_data['LVs']
    vg_data['num_pvs'] = vg_data['TOTAL PVs']
    vg_data['vg_state'] = vg_data['VG STATE']
    vg_data['pp_size'] = vg_data['PP SIZE']
    vg_data['total_pps'] = vg_data['TOTAL PPs'].split()[0]
    vg_data['free_pps'] = vg_data['FREE PPs'].split()[0]
    pp_size_int = int(vg_data['pp_size'].split()[0])
    vg_data['size_g'] = int(vg_data['total_pps']) * pp_size_int / 1024
    vg_data['free_g'] = int(vg_data['free_pps']) * pp_size_int / 1024

    return vg_data


def load_lvs(module, name, LVM):
    """
    Get the details for the specified LV or all
    arguments:
        module  (dict): Ansible module argument spec.
        name     (str): logical volume name.
        LVM     (dict): LVM facts.
    return:
        warnings (list): List of warning messages
        LVM      (dict): LVM facts
    """
    warnings = []
    cmd = "lsvg"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        warnings.append(f"Command failed. cmd={cmd} rc={rc} stdout={stdout} stderr={stderr}")
    else:
        for line in stdout.splitlines():
            vg = line.split()[0].strip()
            cmd = f"lsvg -l { vg }"
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                warnings.append(f"Command failed. cmd={cmd} rc={rc} stdout={stdout} stderr={stderr}")
            else:
                try:
                    lv_data, warnings = parse_lvs(module, stdout, vg, name, warnings)
                    LVM['LVs'].update(lv_data)
                except (IndexError, AssertionError) as err:
                    warnings.append(str(err))

    return warnings, LVM


def add_lslv_data(module, lv, lv_data, warnings):
    """
    Get additional details about the logical volume using lslv command.
    arguments:
        module (dict): Ansible module argument spec.
        warnings (list): List of warning messages
        lv (str): Name of the logical volume.
        lv_data (dict): Contains lv details fetched using lsvg -l <lvname>
    return:
        lv_data (dict): Dictionary containing all the details about the provided
                        logical volume, fetched using lslv and lsvg -l <lvname> combined.
                        These details are present in parsed format.
        warnings (list): List of warning messages, updated in case of failure
                         during command execution.
    """
    cmd = f"lslv {lv}"
    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        warnings.append(f"Failed to get additional details about {lv}, using the command {cmd}")
        return lv_data, warnings

    # This pattern will be used to fetch all the keys fetched using lslv command, except "PP SIZE"
    general_pattern = r"""\s*(LV IDENTIFIER|INTER-POLICY|VOLUME GROUP|LOGICAL VOLUME
                        |PERMISSION|VG STATE|LV STATE|TYPE|WRITE VERIFY|MAX LPs|COPIES|SCHED POLICY|
                        LPs|PPs|STALE PPs|BB POLICY|RELOCATABLE|INTRA-POLICY|UPPER BOUND|MOUNT POINT|
                        LABEL|DEVICE UID|DEVICE GID|DEVICE PERMISSIONS|MIRROR WRITE CONSISTENCY|
                        INFINITE RETRY|PREFERRED READ|DEVICESUBTYPE|COPY 1 MIRROR POOL|COPY 2 MIRROR POOL
                        |COPY 3 MIRROR POOL|ENCRYPTION|[A-Za-z\s\?]+):\s*([^\n\s]+)"""

    # PP size has its value in a different pattern(eg: 16 megabyte(s)), so need to match accordiingly
    PP_size_pattern = r"PP SIZE:\s*(\d+\s+[a-zA-Z]+(?:\([a-zA-Z]+\))?)"

    general_matches = re.findall(general_pattern, stdout)

    for match in general_matches:
        if match[0] not in lv_data[lv].keys():
            lv_data[lv][match[0]] = match[1]

    match_pp_size = re.search(PP_size_pattern, stdout)

    if match_pp_size:
        lv_data[lv]["PP SIZE"] = match_pp_size.group(1).strip()

    return lv_data, warnings


def parse_lvs(module, lsvg_output, vg_name, lv_name, warnings):
    """
    Parse 'lsvg -l <vg>' output
    arguments:
        lsvg_output (str): Raw output of 'lsvg -l <vg>' cmd
        vg_name     (str): Volume group name
        lv_name     (str): Logical volume name (or 'all')
        warnings (list): List of warning messages
    return:
        lv_data    (dict): Dictionary of LV data. Top level keys are LV NAMEs,
                           values are data parse from the rest of the lsvg -l
                           columns.
    """
    lv_data = {}
    try:
        header = lsvg_output.splitlines()[1]
    except IndexError as no_second_line:
        raise IndexError from no_second_line(
            f"Unable to get header (second line) of lsvg -l {vg_name} output.\
                lsvg_output={lsvg_output}"
        )
    headings = ['LV NAME', 'TYPE', 'LPs', 'PPs', 'PVs', 'LV STATE', 'MOUNT POINT']
    headings_indexes = []
    for heading in headings:
        match = re.search(heading, header)
        if match is None:
            msg = f"Unable to parse lsvg -l {vg_name} header."
            msg += f"header={header}, expected headings={headings}"
            result['msg'] = msg
            module.fail_json(**result)
        headings_indexes.append(match.start())

    for ln in lsvg_output.splitlines()[2:]:
        ln = ln.ljust(len(header))
        lv = ln[headings_indexes[0]:headings_indexes[1]].strip()
        if lv_name in ['all', lv]:
            type = ln[headings_indexes[1]:headings_indexes[2]].strip()
            lps = ln[headings_indexes[2]:headings_indexes[3]].strip()
            pps = ln[headings_indexes[3]:headings_indexes[4]].strip()
            pvs = ln[headings_indexes[4]:headings_indexes[5]].strip()
            lv_state = ln[headings_indexes[5]:headings_indexes[6]].strip()
            mnt_pt = ln[headings_indexes[6]:].strip()
            lv_data[lv] = {
                'TYPE': type,
                'VOLUME GROUP': vg_name,
                'PVs': pvs,
                'LV STATE': lv_state,
                'PPs': pps,
                'LPs': lps,
                'MOUNT POINT': mnt_pt
            }
            lv_data, warnings = add_lslv_data(module, lv, lv_data, warnings)

            if lv_name != 'all':
                break

    msg = f"Could not get any information about the provided LV - {lv_name}"

    if not lv_data and msg not in warnings:
        warnings.append(msg)

    return lv_data, warnings


def main():
    module = AnsibleModule(
        argument_spec=dict(
            component=dict(type='str', default='all', choices=['pv', 'lv', 'vg', 'all']),
            name=dict(type='str', default='all'),
            lvm=dict(type='dict', default={}),
        ),
        supports_check_mode=True,
    )

    global result

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    return_values = {}
    warnings = []
    type = module.params['component']
    name = module.params['name']
    LVM = module.params['lvm']
    if type == 'vg' or type == 'all':
        if 'VGs' not in LVM:
            LVM['VGs'] = {}
        warnings_vg, LVM = load_vgs(module, name, LVM)
        warnings += warnings_vg
    if type == 'pv' or type == 'all':
        if 'PVs' not in LVM:
            LVM['PVs'] = {}
        warnings_pv, LVM = load_pvs(module, name, LVM)
        warnings += warnings_pv
    if type == 'lv' or type == 'all':
        if 'LVs' not in LVM:
            LVM['LVs'] = {}
        warnings_lv, LVM = load_lvs(module, name, LVM)
        warnings += warnings_lv

    if len(warnings) > 0:
        return_values['warnings'] = warnings

    result['ansible_facts'] = dict(LVM=LVM)
    result['return_values'] = return_values

    module.exit_json(**result)


if __name__ == '__main__':
    main()
