#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018- IBM, Inc
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
module: nim_vios_hc
short_description: Check if a pair of VIOSes can be updated
description:
- Check if a pair of Virtual I/O Servers can be updated.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform.
    - C(health_check) to perform a health check.
    type: str
    choices: [ health_check ]
    required: true
  targets:
    description:
    - NIM target.
    - 'To perform a health check on dual VIOSes specify a tuple
      with the following format: "vios1,vios2".'
    type: list
    elements: str
    required: true
  vars:
    description:
    - Specifies additional parameters.
    type: dict
notes:
  - Use the C(power_aix_vioshc) role to install the required C(vioshc.py) script on the NIM master.
'''

EXAMPLES = r'''
- name: Perform a health check on dual VIOSes vios1,vios2 and on VIOS vios3
  nim_vios_hc:
    targets:
    - vios1,vios2
    - vios3
    action: health_check
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
targets:
    description: List of VIOS tuples.
    returned: always
    type: list
    elements: str
nim_node:
    description: NIM node info.
    returned: always
    type: dict
status:
    description: Status for each VIOS (dictionary key).
    returned: always
    type: dict
'''

import re

from ansible.module_utils.basic import AnsibleModule

OUTPUT = []
NIM_NODE = {}


def get_hmc_info(module):
    """
    Get the hmc info on the nim master.

    return a dictionary with hmc info
    """
    info_hash = {}

    cmd = ['lsnim', '-t', 'hmc', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = 'Failed to get HMC NIM info, lsnim returned {0}: {1}'.format(ret, stderr)
        module.log(msg)
        OUTPUT.append(msg)
        return info_hash

    obj_key = ''
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        # HMC name
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            cstate = match_cstate.group(1)
            info_hash[obj_key]['cstate'] = cstate
            continue

        match_key = re.match(r"^\s+passwd_file\s+=\s+(.*)$", line)
        if match_key:
            info_hash[obj_key]['passwd_file'] = match_key.group(1)
            continue

        match_key = re.match(r"^\s+login\s+=\s+(.*)$", line)
        if match_key:
            info_hash[obj_key]['login'] = match_key.group(1)
            continue

        match_key = re.match(r"^\s+if1\s*=\s*\S+\s*(\S*)\s*.*$", line)
        if match_key:
            info_hash[obj_key]['ip'] = match_key.group(1)
            continue

    return info_hash


def get_nim_cecs_info(module):
    """
    Get the list of cecs defined on the nim master and
    get their serial number.

    return a dictionary of the cec objects defined on the
           nim master and their associated serial number value
    """
    info_hash = {}

    cmd = ['lsnim', '-t', 'cec', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = 'Failed to get CEC NIM info, lsnim returned {0}: {1}'.format(ret, stderr)
        module.log(msg)
        OUTPUT.append(msg)
        return info_hash

    # cec name and associated serial
    obj_key = ""
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_serial = re.match(r"^\s+serial\s+=\s+(.*)$", line)
        if match_serial:
            info_hash[obj_key]['serial'] = match_serial.group(1)
            continue

    return info_hash


def get_nim_clients_info(module, lpar_type):
    """
    Get the list of lpars (standalones or vioses) defined on the
    nim master, and get their cstate.

    return a dictionary of the lpar objects defined on the
           nim master and their associated cstate value
    """
    info_hash = {}

    cmd = ['lsnim', '-t', lpar_type, '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = 'Failed to get NIM clients info, lsnim returned: {0}'.format(stderr)
        module.log(msg)
        OUTPUT.append(msg)
        return info_hash

    # lpar name and associated Cstate
    obj_key = ""
    for line in stdout.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            info_hash[obj_key]['cstate'] = match_cstate.group(1)
            continue

        # For VIOS store the management profile
        if lpar_type == 'vios':
            match_mgmtprof = re.match(r"^\s+mgmt_profile1\s+=\s+(.*)$", line)
            if match_mgmtprof:
                mgmt_elts = match_mgmtprof.group(1).split()
                if len(mgmt_elts) >= 3:
                    info_hash[obj_key]['mgmt_hmc_id'] = mgmt_elts[0]
                    info_hash[obj_key]['mgmt_vios_id'] = mgmt_elts[1]
                    info_hash[obj_key]['mgmt_cec'] = mgmt_elts[2]

            match_if = re.match(r"^\s+if1\s+=\s+\S+\s+(\S+)\s+.*$", line)
            if match_if:
                info_hash[obj_key]['vios_ip'] = match_if.group(1)

    return info_hash


def build_nim_node(module):
    """
    Build the nim node containing the nim vios and hmc info.
    """

    global NIM_NODE

    # =========================================================================
    # Build hmc info list
    # =========================================================================
    nim_hmc = get_hmc_info(module)
    NIM_NODE['nim_hmc'] = nim_hmc
    module.debug('NIM HMC: {0}'.format(nim_hmc))

    # =========================================================================
    # Build CEC info list
    # =========================================================================
    nim_cec = get_nim_cecs_info(module)

    # =========================================================================
    # Build vios info list
    # =========================================================================
    nim_vios = get_nim_clients_info(module, 'vios')

    # =========================================================================
    # Complete the CEC serial in nim_vios dict
    # =========================================================================
    for key in nim_vios:
        mgmt_cec = nim_vios[key]['mgmt_cec']
        if mgmt_cec in nim_cec:
            nim_vios[key]['mgmt_cec_serial'] = nim_cec[mgmt_cec]['serial']

    NIM_NODE['nim_vios'] = nim_vios
    module.debug('NIM VIOS: {0}'.format(nim_vios))


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - ret     return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

    rcmd = '( LC_ALL=C {0} ); echo rc=$?'.format(' '.join(command))
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    module.debug('exec command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        return (ret, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        ret = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug('exec command rc:{0}, output:{1}, stderr:{2}'.format(ret, stdout, stderr))

    return (ret, stdout, stderr)


def check_vios_targets(module, targets):
    """
    Check the list of vios targets.
    Check that each target can be reached.

    A target name can be of the following form:
        vios1,vios2 or vios3

    arguments:
        targets: list of tuple of NIM names of VIOSes

    return: the list of the existing vios tuple matching the target list
    """
    global NIM_NODE

    vios_list = {}
    vios_list_tuples_res = []

    # ===========================================
    # Build target list
    # ===========================================
    for vios_tuple in targets:

        module.debug('vios_tuple: {0}'.format(vios_tuple))

        tuple_elts = list(set(vios_tuple.split(',')))
        tuple_len = len(tuple_elts)

        if tuple_len != 1 and tuple_len != 2:
            module.log('Malformed VIOS targets {0}. Tuple {1} should have one or two elements.'
                       .format(targets, tuple_elts))
            return None

        # check vios not already exists in the target list
        if tuple_elts[0] in vios_list or (tuple_len == 2 and (tuple_elts[1] in vios_list
                                                              or tuple_elts[0] == tuple_elts[1])):
            module.log('Malformed VIOS targets {0}. Duplicated VIOS'
                       .format(targets))
            return None

        # check vios is known by the NIM master - if not ignore it
        if tuple_elts[0] not in NIM_NODE['nim_vios'] or \
           (tuple_len == 2 and tuple_elts[1] not in NIM_NODE['nim_vios']):
            module.log('skipping {0} as VIOS not known by the NIM master.'
                       .format(vios_tuple))
            continue

        # check vios connectivity
        res = 0
        for vios in tuple_elts:
            cmd = ['true']
            ret, stdout, stderr = nim_exec(module, NIM_NODE['nim_vios'][vios]['vios_ip'], cmd)
            if ret != 0:
                res = 1
                msg = 'skipping {0}: cannot reach {1} with c_rsh: {2}, {3}, {4}'\
                      .format(vios_tuple, vios, res, stdout, stderr)
                module.log(msg)
                continue
        if res != 0:
            continue

        if tuple_len == 2:
            vios_list[tuple_elts[0]] = tuple_elts[1]
            vios_list[tuple_elts[1]] = tuple_elts[0]
            # vios_list = vios_list.extend([tuple_elts[0], tuple_elts[1]])
            my_tuple = (tuple_elts[0], tuple_elts[1])
            vios_list_tuples_res.append(tuple(my_tuple))
        else:
            vios_list[tuple_elts[0]] = tuple_elts[0]
            # vios_list.append(tuple_elts[0])
            my_tuple = (tuple_elts[0],)
            vios_list_tuples_res.append(tuple(my_tuple))

    return vios_list_tuples_res


def vios_health(module, mgmt_sys_uuid, hmc_ip, vios_uuids):
    """
    Check the health of the given VIOS or pair of VIOSes from a rolling
    update point of view.

    This operation uses the vioshc.py script to evaluate the capacity of
    the pair of VIOSes to support the rolling update operation.

    return: 0 if ok,
            1 otherwise
    """
    module.debug('hmc_ip: {0} vios_uuids: {1}'.format(hmc_ip, vios_uuids))

    # Build the vioshc cmd
    cmd = [vioshc_cmd, '-i', hmc_ip, '-m', mgmt_sys_uuid]
    for uuid in vios_uuids:
        cmd.extend(['-U', uuid])
    if module._verbosity > 0:
        cmd.extend(['-' + 'v' * module._verbosity])
        if module._verbosity >= 3:
            cmd.extend(['-D'])

    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        OUTPUT.append('    VIOS Health check failed, vioshc returned: {0}'
                      .format(stderr))
        module.log('VIOS Health check failed, vioshc returned: {0} {1}'
                   .format(ret, stderr))
        OUTPUT.append('    VIOS can NOT be updated')
        module.log('vioses {0} can NOT be updated'.format(vios_uuids))
        ret = 1
    elif re.search(r'Pass rate of 100%', stdout, re.M):
        OUTPUT.append('    VIOS Health check passed')
        module.log('vioses {0} can be updated'.format(vios_uuids))
        ret = 0
    else:
        OUTPUT.append('    VIOS can NOT be updated')
        module.log('vioses {0} can NOT be updated'.format(vios_uuids))
        ret = 1

    return ret


def vios_health_init(module, hmc_id, hmc_ip):
    """
    Collect CEC and VIOS UUIDs using vioshc.py script for a given HMC.

    return: True if ok,
            False otherwise
    """
    global NIM_NODE
    global results
    global OUTPUT

    module.debug('hmc_id: {0}, hmc_ip: {1}'.format(hmc_id, hmc_ip))

    # Call the vioshc.py script a first time to collect UUIDs
    cmd = [vioshc_cmd, '-i', hmc_ip, '-l', 'a']
    if module._verbosity > 0:
        cmd.extend(['-' + 'v' * module._verbosity])
        if module._verbosity >= 3:
            cmd.extend(['-D'])

    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        OUTPUT.append('    Failed to get the VIOS information, vioshc returned: {0}'
                      .format(stderr))
        module.log('Failed to get the VIOS information, vioshc returned: {0} {1}'
                   .format(ret, stderr))
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Failed to get the VIOS information, vioshc returned: {0}'.format(ret)
        module.fail_json(**results)

    # Parse the output and store the UUIDs
    data_start = 0
    vios_section = 0
    cec_uuid = ''
    cec_serial = ''
    for line in stdout.split('\n'):
        line = line.rstrip()
        # TBC - remove?
        module.debug('--------line {0}'.format(line))
        if vios_section == 0:
            # skip the header
            match_key = re.match(r"^-+\s+-+$", line)
            if match_key:
                data_start = 1
                continue
            if data_start == 0:
                continue

            # New managed system section
            match_key = re.match(r"^(\S+)\s+(\S+)$", line)
            if match_key:
                cec_uuid = match_key.group(1)
                cec_serial = match_key.group(2)

                module.debug('New managed system section:{0},{1}'
                             .format(cec_uuid, cec_serial))
                continue

            # New vios section
            match_key = re.match(r"^\s+-+\s+-+$", line)
            if match_key:
                vios_section = 1
                continue

            # skip all header and empty lines until the vios section
            continue

        # new vios partition
        match_key = re.match(r"^\s+(\S+)\s+(\S+)$", line)
        if match_key:
            vios_uuid = match_key.group(1)
            vios_part_id = match_key.group(2)
            module.debug('new vios partitionsection:{0},{1}'
                         .format(vios_uuid, vios_part_id))

            # retrieve the vios with the vios_part_id and the cec_serial value
            # and store the UUIDs in the dictionaries
            for vios_key in NIM_NODE['nim_vios']:
                if NIM_NODE['nim_vios'][vios_key]['mgmt_vios_id'] == vios_part_id \
                   and NIM_NODE['nim_vios'][vios_key]['mgmt_cec_serial'] == cec_serial:
                    NIM_NODE['nim_vios'][vios_key]['vios_uuid'] = vios_uuid
                    NIM_NODE['nim_vios'][vios_key]['cec_uuid'] = cec_uuid
                    break
            continue

        # skip vios line where lparid is not found.
        match_key = re.match(r"^\s+(\S+)\s+none$", line)
        if match_key:
            continue

        # skip empty line after vios section. stop the vios section
        match_key = re.match(r"^$", line)
        if match_key:
            vios_section = 0
            continue

        OUTPUT.append('    Bad command output for the hmc: {0}'.format(hmc_id))
        module.log('vioshc command, bad output line: {0}'.format(line))
        results['msg'] = 'Health init check failed. Bad vioshc.py command output for the {0} hmc - output: {1}'\
                         .format(hmc_id, line)
        module.fail_json(**results)

    module.debug('vioshc output: {0}'.format(line))
    return ret


def health_check(module, targets):
    """
    Health assessment of the VIOS targets to ensure they can support
    a rolling update operation.

    For each VIOS tuple:
    - call vioshc.py a first time to collect the VIOS UUIDs
    - call vioshc.py a second time to check the healthiness

    return: a dictionary with the state of each VIOS tuple
    """
    global NIM_NODE

    module.debug('targets: {0}'.format(targets))

    health_tab = {}
    vios_key = []
    for target_tuple in targets:
        OUTPUT.append('Checking: {0}'.format(target_tuple))
        module.debug('target_tuple: {0}'.format(target_tuple))

        tup_len = len(target_tuple)
        vios1 = target_tuple[0]
        if tup_len == 2:
            vios2 = target_tuple[1]
            vios_key = "{0}-{1}".format(vios1, vios2)
        else:
            vios_key = vios1

        module.debug('vios1: {0}'.format(vios1))
        # cec_serial = NIM_NODE['nim_vios'][vios1]['mgmt_cec_serial']
        hmc_id = NIM_NODE['nim_vios'][vios1]['mgmt_hmc_id']

        if hmc_id not in NIM_NODE['nim_hmc']:
            OUTPUT.append('    VIOS {0} refers to an inexistant hmc {1}'
                          .format(vios1, hmc_id))
            module.log("[WARNING] VIOS {0} refers to an inexistant hmc {1}"
                       .format(vios1, hmc_id))
            health_tab[vios_key] = 'FAILURE-HC'
            continue

        hmc_ip = NIM_NODE['nim_hmc'][hmc_id]['ip']

        vios_uuid = []

        # if needed call vios_health_init to get the UUIDs value
        if 'vios_uuid' not in NIM_NODE['nim_vios'][vios1] \
           or tup_len == 2 and 'vios_uuid' not in NIM_NODE['nim_vios'][vios2]:
            OUTPUT.append('    Getting VIOS UUID')

            ret = vios_health_init(module, hmc_id, hmc_ip)
            if ret != 0:
                OUTPUT.append('    Unable to get UUIDs of {0} and {1}, ret: {2}'
                              .format(vios1, vios2, ret))
                module.log("[WARNING] Unable to get UUIDs of {0} and {1}, ret: {2}"
                           .format(vios1, vios2, ret))
                health_tab[vios_key] = 'FAILURE-HC'
                continue

        if 'vios_uuid' not in NIM_NODE['nim_vios'][vios1] \
           or tup_len == 2 and 'vios_uuid' not in NIM_NODE['nim_vios'][vios2]:
            # vios uuid's not found
            OUTPUT.append('    One VIOS UUID not found')
            module.log("[WARNING] Unable to find one vios_uuid in NIM_NODE")
            health_tab[vios_key] = 'FAILURE-HC'

        else:
            # run the vios_health check for the vios tuple
            vios_uuid.append(NIM_NODE['nim_vios'][vios1]['vios_uuid'])
            if tup_len == 2:
                vios_uuid.append(NIM_NODE['nim_vios'][vios2]['vios_uuid'])

            mgmt_uuid = NIM_NODE['nim_vios'][vios1]['cec_uuid']

            OUTPUT.append('    Checking if we can update the VIOS')
            ret = vios_health(module, mgmt_uuid, hmc_ip, vios_uuid)

            if ret == 0:
                OUTPUT.append('    Health check succeeded')
                module.log("Health check succeeded for {0}".format(vios_key))
                health_tab[vios_key] = 'SUCCESS-HC'
            else:
                OUTPUT.append('    Health check failed')
                module.log("Health check failed for {0}".format(vios_key))
                health_tab[vios_key] = 'FAILURE-HC'

    module.debug('health_tab: {0}'. format(health_tab))
    return health_tab


def main():
    global results
    global OUTPUT
    global NIM_NODE
    global vioshc_cmd

    module = AnsibleModule(
        argument_spec=dict(
            targets=dict(required=True, type='list', elements='str'),
            action=dict(required=True, choices=['health_check'], type='str'),
            vars=dict(type='dict'),
        )
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    # =========================================================================
    # Get module params
    # =========================================================================
    targets = module.params['targets']

    OUTPUT.append('VIOS Health Check operation for {0}'.format(targets))

    target_list = []
    targets_health_status = {}

    # =========================================================================
    # Build nim node info
    # =========================================================================
    build_nim_node(module)

    ret = check_vios_targets(module, targets)
    if (ret is None) or (not ret):
        OUTPUT.append('    Warning: Empty target list')
        module.log('[WARNING] Empty target list: "{0}"'.format(targets))
    else:
        target_list = ret
        OUTPUT.append('    Targets list: {0}'.format(target_list))
        module.debug('Targets list: {0}'.format(target_list))

        # Check vioshc script is present, fail_json if not
        vioshc_cmd = module.get_bin_path('vioshc.py', required=True)
        module.debug('Using vioshc.py script at {0}'.format(vioshc_cmd))

        targets_health_status = health_check(module, target_list)

        OUTPUT.append('VIOS Health Check status:')
        module.log('VIOS Health Check status:')
        for vios_key in targets_health_status.keys():
            OUTPUT.append("    {0} : {1}".format(vios_key, targets_health_status[vios_key]))
            module.log('    {0} : {1}'.format(vios_key, targets_health_status[vios_key]))

    results['targets'] = target_list
    results['nim_node'] = NIM_NODE
    results['status'] = targets_health_status
    results['output'] = OUTPUT
    results['msg'] = "VIOS Health Check completed successfully"
    module.exit_json(**results)


if __name__ == '__main__':
    main()
