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
short_description: Check if a pair of VIOSes can be updated.
description:
- Uses the Network Installation Management (NIM) and the VIOS health check tool to check several
  settings required to update a pair of Virtual I/O Servers (VIOS).
- In the current version, it validates the vSCSI, NPIv, SEA mappings configurations and vNIC
  configurations (when set) so the update of the VIOS pair can be attempted. The SSP configuration
  is not checked yet, that is not required so far.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- The B(vioshc.py) script must be installed on the NIM master.
- 'Privileged user with authorizations: B(aix.system.install,aix.system.nim.config.server)'
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
    - Specifies the NIM clients to perform the action on.
    - To perform a health check on dual VIOSes specify a tuple with the following format
      I("vios1,vios2").
    type: list
    elements: str
    required: true
notes:
  - Use the B(power_aix_vioshc) role to install the required B(vioshc.py) script on the NIM master.
  - The default log directory for the B(vioshc.py) script is B(/tmp/vios_maint).
  - The B(vioshc.py) script uses Curl to get information through the REST API of the VIOSes' HMC.
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
import os

from ansible.module_utils.basic import AnsibleModule

OUTPUT = []
NIM_NODE = {}
results = None


def get_hmc_info(module):
    """
    Get the hmc info on the nim master.

    return a dictionary with hmc info
    """
    info_hash = {}

    cmd = ['/usr/sbin/lsnim', '-t', 'hmc', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = f'Failed to get HMC NIM info, lsnim returned {ret}: {stderr}'
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

    cmd = ['/usr/sbin/lsnim', '-t', 'cec', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = f'Failed to get CEC NIM info, lsnim returned {ret}: {stderr}'
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

    cmd = ['/usr/sbin/lsnim', '-t', lpar_type, '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = f'Failed to get NIM clients info, lsnim returned: {stderr}'
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

    # Build hmc info list
    nim_hmc = get_hmc_info(module)
    NIM_NODE['nim_hmc'] = nim_hmc
    module.debug(f'NIM HMC: {nim_hmc}')

    # Build CEC info list
    nim_cec = get_nim_cecs_info(module)

    # Build vios info list
    nim_vios = get_nim_clients_info(module, 'vios')

    # Complete the CEC serial in nim_vios dict
    for key, nimvios in nim_vios.items():
        mgmt_cec = nimvios['mgmt_cec']
        if mgmt_cec in nim_cec:
            nimvios['mgmt_cec_serial'] = nim_cec[mgmt_cec]['serial']

    NIM_NODE['nim_vios'] = nim_vios
    module.debug(f'NIM VIOS: {nim_vios}')


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - ret     return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

    cmd = ' '.join(command)
    rcmd = f'( LC_ALL=C {cmd} ); echo rc=$?'
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    module.debug(f'exec command:{cmd}')

    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        return (ret, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        ret = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug(f'exec command rc:{ret}, output:{stdout}, stderr:{stderr}')

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

    vios_list = {}
    vios_list_tuples_res = []

    # Build target list
    for vios_tuple in targets:

        module.debug(f'vios_tuple: {vios_tuple}')

        tuple_elts = list(set(vios_tuple.split(',')))
        tuple_len = len(tuple_elts)

        if tuple_len != 1 and tuple_len != 2:
            module.log(f'Malformed VIOS targets {targets}. Tuple {tuple_elts} should have one or two elements.')
            return None

        # check vios not already exists in the target list
        if tuple_elts[0] in vios_list or (tuple_len == 2 and (tuple_elts[1] in vios_list
                                                              or tuple_elts[0] == tuple_elts[1])):
            module.log(f'Malformed VIOS targets {targets}. Duplicated VIOS')
            return None

        # check vios is known by the NIM master - if not ignore it
        if tuple_elts[0] not in NIM_NODE['nim_vios'] or \
           (tuple_len == 2 and tuple_elts[1] not in NIM_NODE['nim_vios']):
            module.log(f'skipping {vios_tuple} as VIOS not known by the NIM master.')
            continue

        # check vios connectivity
        res = 0
        for vios in tuple_elts:
            cmd = ['true']
            ret, stdout, stderr = nim_exec(module, NIM_NODE['nim_vios'][vios]['vios_ip'], cmd)
            if ret != 0:
                res = 1
                msg = f'skipping {vios_tuple}: cannot reach {vios} with c_rsh: {res}, {stdout}, {stderr}'
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
    module.debug(f'hmc_ip: {hmc_ip} vios_uuids: {vios_uuids}')
    # Build the vioshc cmd
    cmd = [vioshc_interpreter, vioshc_cmd, '-i', hmc_ip, '-m', mgmt_sys_uuid]
    for uuid in vios_uuids:
        cmd.extend(['-U', uuid])
    if module._verbosity > 0:
        cmd.extend(['-' + 'v' * module._verbosity])
        if module._verbosity >= 3:
            cmd.extend(['-D'])
    # path prefix is used here to ensure the dependent module paths are present.
    # In this case, curl module.
    ret, stdout, stderr = module.run_command(cmd, path_prefix=os.path.dirname(vioshc_interpreter))
    if ret != 0:
        OUTPUT.append(f'    VIOS Health check failed, vioshc returned: {stderr}')
        module.log(f'VIOS Health check failed, vioshc returned: {ret} {stderr}')
        OUTPUT.append('    VIOS can NOT be updated')
        module.log(f'vioses {vios_uuids} can NOT be updated')
        ret = 1
    elif re.search(r'Pass rate of 100%', stdout, re.M):
        OUTPUT.append('    VIOS Health check passed')
        module.log(f'vioses {vios_uuids} can be updated')
        ret = 0
    else:
        OUTPUT.append('    VIOS can NOT be updated')
        module.log(f'vioses {vios_uuids} can NOT be updated')
        ret = 1

    return ret


def vios_health_init(module, hmc_id, hmc_ip):
    """
    Collect CEC and VIOS UUIDs using vioshc.py script for a given HMC.

    return: True if ok,
            False otherwise
    """

    module.debug(f'hmc_id: {hmc_id}, hmc_ip: {hmc_ip}')

    # Call the vioshc.py script a first time to collect UUIDs
    cmd = [vioshc_interpreter, vioshc_cmd, '-i', hmc_ip, '-l', 'a']
    if module._verbosity > 0:
        cmd.extend(['-' + 'v' * module._verbosity])
        if module._verbosity >= 3:
            cmd.extend(['-D'])
    # path prefix is used here to ensure the dependent module paths are present.
    # In this case, curl module.
    ret, stdout, stderr = module.run_command(cmd, path_prefix=os.path.dirname(vioshc_interpreter))
    if ret != 0:
        OUTPUT.append(f'    Failed to get the VIOS information, vioshc returned: {stderr}')
        module.log(f'Failed to get the VIOS information, vioshc returned: {ret} {stderr}')
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = f'Failed to get the VIOS information, vioshc returned: {ret}'
        module.fail_json(**results)

    # Parse the output and store the UUIDs
    data_start = 0
    vios_section = 0
    cec_uuid = ''
    cec_serial = ''
    for line in stdout.split('\n'):
        line = line.rstrip()
        # TBC - remove?
        module.debug(f'-- vioshc stdout line: {line}')
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

                module.debug(f'New managed system section:{cec_uuid},{cec_serial}')
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
            module.debug(f'new vios partitionsection:{vios_uuid},{vios_part_id}')

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

        OUTPUT.append(f'    Bad command output for the hmc: {hmc_id}')
        module.log(f'vioshc command, bad output line: {line}')
        results['msg'] = f'Health init check failed. Bad vioshc.py command output for the {hmc_id} hmc - output: {line}'
        module.fail_json(**results)

    module.debug(f'vioshc output: {line}')
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

    module.debug(f'targets: {targets}')

    health_tab = {}
    vios_key = []
    for target_tuple in targets:
        OUTPUT.append(f'Checking: {target_tuple}')
        module.debug(f'target_tuple: {target_tuple}')

        tup_len = len(target_tuple)
        vios1 = target_tuple[0]
        if tup_len == 2:
            vios2 = target_tuple[1]
            vios_key = f"{vios1}-{vios2}"
        else:
            vios_key = vios1

        module.debug(f'vios1: {vios1}')
        # cec_serial = NIM_NODE['nim_vios'][vios1]['mgmt_cec_serial']
        hmc_id = NIM_NODE['nim_vios'][vios1]['mgmt_hmc_id']

        if hmc_id not in NIM_NODE['nim_hmc']:
            OUTPUT.append(f'    VIOS {vios1} refers to an inexistant hmc {hmc_id}')
            module.log(f"[WARNING] VIOS {vios1} refers to an inexistant hmc {hmc_id}")
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
                OUTPUT.append(f'    Unable to get UUIDs of {vios1} and {vios2}, ret: {ret}')
                module.log(f"[WARNING] Unable to get UUIDs of {vios1} and {vios2}, ret: {ret}")
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
                module.log(f"Health check succeeded for {vios_key}")
                health_tab[vios_key] = 'SUCCESS-HC'
            else:
                OUTPUT.append('    Health check failed')
                module.log(f"Health check failed for {vios_key}")
                health_tab[vios_key] = 'FAILURE-HC'

    module.debug(f'health_tab: {health_tab}')
    return health_tab


def get_vioshc_interpreter(module):
    """
    Provide the right python interpreter to be used for vioshc command.
    return: Right python interpreter if ok,
            Null string otherwise
    """
    """
    Check whether the python interpreter is in the list.
    if that path exists on the system , then continue with that
    else proceed to the next interpreter in the list.
    """
    is_interpreter_found = False
    is_pycurl_found = False
    python_interpreter_list = ['/usr/bin/python', '/opt/freeware/bin/python3', '/usr/bin/python3']

    for interpreter in python_interpreter_list:
        # Reinitialize these values for every loop
        is_interpreter_found = False
        is_pycurl_found = False
        # check if that path exists. Add check for pycurl module.
        if os.path.isfile(interpreter):
            is_interpreter_found = True
            cmd = interpreter + '  -c "import pycurl"'
            ret, stdout, stderr = module.run_command(cmd)
            if ret == 0:
                return interpreter
            else:
                is_pycurl_found = False

    """
    If we have exhausted the list, that means no interpreter or no pycurl module
    in the list was found. So give a error message.The interpreter will be found
    always because without the ansible module will not run anyway.
    """
    if is_interpreter_found is True:
        if is_pycurl_found is False:
            msg = 'Unable to find the right python interpreter with the dependent module pycurl.'
            OUTPUT.append('    Warning: Dependent module pycurl is not found  ')
            results['stdout'] = stdout
            results['stderr'] = stderr
    else:
        msg = 'Unable to find the python interpreter for vioshc command. '
        OUTPUT.append('    Warning: No python interpreter found. ')

    results['msg'] = msg
    return None


def main():
    global results
    global vioshc_cmd
    global vioshc_interpreter

    module = AnsibleModule(
        argument_spec=dict(
            targets=dict(required=True, type='list', elements='str'),
            action=dict(required=True, choices=['health_check'], type='str'),
        )
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    # Get module params
    targets = module.params['targets']

    OUTPUT.append(f'VIOS Health Check operation for {targets}')

    target_list = []
    targets_health_status = {}

    # Build nim node info
    build_nim_node(module)

    ret = check_vios_targets(module, targets)
    if (ret is None) or (not ret):
        OUTPUT.append('    Warning: Empty target list')
        module.log(f'[WARNING] Empty target list: "{targets}"')
    else:
        target_list = ret
        OUTPUT.append(f'    Targets list: {target_list}')
        module.debug(f'Targets list: {target_list}')
        """
        Get the interpreter for vioshc command.  If unable to find a
        proper interpreter, then fail.
        """
        vioshc_interpreter = get_vioshc_interpreter(module)
        if vioshc_interpreter is None:
            module.fail_json(**results)

        # Get the vioshc command path
        vioshc_cmd = module.get_bin_path('vioshc.py', required=True)
        module.debug(f'Using vioshc.py script at {vioshc_interpreter}:{vioshc_cmd}')

        targets_health_status = health_check(module, target_list)

        OUTPUT.append('VIOS Health Check status:')
        module.log('VIOS Health Check status:')
        for vios_key, vios_health_status in targets_health_status.items():
            OUTPUT.append(f"    {vios_key} : {vios_health_status}")
            module.log(f'    {vios_key} : {vios_health_status}')

    results['targets'] = target_list
    results['nim_node'] = NIM_NODE
    results['status'] = targets_health_status
    results['output'] = OUTPUT
    results['msg'] = "VIOS Health Check completed successfully"
    module.exit_json(**results)


if __name__ == '__main__':
    main()
