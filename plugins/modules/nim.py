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
module: nim
short_description: Server setup, install packages, update SP or TL.
description:
- Server setup, install packages, update SP or TL.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the action to perform.
    - C(update) to update NIM clients with a specified C(lpp_source).
    - C(master_setup) to setup a NIM master.
    - C(check) to retrieve the C(Cstate) of each NIM client.
    - C(compare) to compare installation inventories of the NIM clients.
    - C(script) to apply a script to customize NIM clients.
    - C(allocate) to allocate a resource to specified NIM clients.
    - C(deallocate) to deallocate a resource for specified NIM clients.
    - C(bos_inst) to install a given list of NIM clients.
    - C(define_script) to define a script NIM resource.
    - C(remove) to remove a specified NIM resource.
    - C(reset) to reset the C(Cstate) of a NIM client.
    - C(reboot) to reboot the given NIM clients if they are running.
    - C(maintenance) to perform a maintenance operation on NIM clients.
    type: str
    choices: [ update, master_setup, check, compare, script, allocate, deallocate, bos_inst, define_script, remove, reset, reboot, maintenance ]
    required: true
  lpp_source:
    description:
    - Indicates the lpp_source to apply to the targets.
    - C(latest_tl), C(latest_sp), C(next_tl) and C(next_sp) can be specified;
      based on the NIM server resources, nim will determine
      the actual oslevel necessary to update the targets.
    type: str
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - C(foo*) designates all the NIM clients with name starting by C(foo).
    - C(foo[2:4]) designates the NIM clients among foo2, foo3 and foo4.
    - C(*) or C(ALL) designates all the NIM clients.
    type: list
    elements: str
  asynchronous:
    description:
    - If set to C(no), NIM client will be completely installed before starting
      the installation of another NIM client.
    type: bool
    default: no
  device:
    description:
    - The device (or directory) where to find the lpp source to install.
    type: str
  script:
    description:
    - NIM script resource.
    type: str
  resource:
    description:
    - NIM resource.
    type: str
  location:
    description:
    - Specifies the full path name of the script resource file.
    type: str
  group:
    description:
    - NIM group resource.
    type: str
  force:
    description:
    - Forces action.
    type: bool
    default: no
  operation:
    description:
    - NIM maintenance operation.
    type: str
  description:
    description:
    - Describes the NIM operation (informational only).
    type: str
'''

EXAMPLES = r'''
- name: Install using group resource
  nim:
    action: bos_inst
    targets: nimclient01
    group: basic_res_grp

- name: Check the Cstate of all NIM clients
  nim:
    action: check

- name: Define a script resource on NIM master
  nim:
    action: define_script
    resource: myscript
    location: /tmp/myscript.sh

- name: Execute a script on all NIM clients synchronously
  nim:
    action: script
    script: myscript
    asynchronous: no
    targets: all
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
nim_output:
    description: Output from nim commands.
    returned: always
    type: str
nim_node:
    description: NIM node info.
    returned: always
    type: dict
    contains:
        lpp_source:
            description: List of lpp sources.
            returned: always
            type: dict
        master:
            description: NIM master.
            returned: always
            type: dict
        standalone:
            description: List of standalone NIM resources.
            returned: always
            type: dict
        vios:
            description: List of VIOS NIM resources.
            returned: always
            type: dict
    sample:
        "nim_node": {
            "lpp_source": {
                "723lpp_res": "/export/nim/lpp_source/723lpp_res"
            },
            "master": {
                "cstate": "ready for a NIM operation",
                "type": "master"
            },
            "standalone": {
                "nimclient01": {
                    "cstate": "ready for a NIM operation",
                    "ip": "nimclient01.mydomain.com",
                    "type": "standalone"
                },
                "nimclient02": {
                    "cstate": "ready for a NIM operation",
                    "ip": "nimclient02.mydomain.com",
                    "type": "standalone"
                }
            },
            "vios": {}
        }
'''

import re
import threading
# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from ansible.module_utils.basic import AnsibleModule

nim_node = {}


def run_oslevel_cmd(module, machine, result):
    """
    Run the oslevel command on target machine.

    Stores the output in the dedicated slot of the result dictionary.

    arguments:
        machine (str): The machine name
        result  (dict): The result of the oslevel command
    """

    result[machine] = 'timedout'

    if machine == 'master':
        cmd = ['oslevel', '-s']
    else:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
               machine,
               '"/usr/bin/oslevel -s; echo rc=$?"']

    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        module.debug('{0} oslevel stdout: "{1}"'.format(machine, stdout))
        if stderr.rstrip():
            module.log('"{0}" command stderr: {1}'.format(' '.join(cmd), stderr))

        # remove the rc of c_rsh with echo $?
        if machine != 'master':
            stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

        # return stdout only ... stripped!
        result[machine] = stdout.rstrip()
    else:
        msg = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.log('Failed to get oslevel for {0}: {1}'.format(machine, msg))


def get_nim_clients_info(module, lpar_type):
    """
    Return the list of nim lpar_type objects defined on the
           nim master and their associated Cstate value.
    """
    global results

    cmd = ['lsnim', '-t', lpar_type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.fail_json(**results)

    # client name and associated Cstate
    info_hash = {}
    for line in stdout.rstrip().split('\n'):
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            info_hash[obj_key]['type'] = lpar_type
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            cstate = match_cstate.group(1)
            info_hash[obj_key]['cstate'] = cstate
            continue

        match_mgmtprof = re.match(r"^\s+mgmt_profile1\s+=\s+(.*)$", line)
        if match_mgmtprof:
            mgmt_elts = match_mgmtprof.group(1).split()
            if len(mgmt_elts) >= 3:
                info_hash[obj_key]['mgmt_hmc_id'] = mgmt_elts[0]
                info_hash[obj_key]['mgmt_id'] = mgmt_elts[1]
                info_hash[obj_key]['mgmt_cec_serial'] = mgmt_elts[2]
            else:
                module.log('[WARNING] {0} management profile does not have 3 elements: {1}'
                           .format(obj_key, match_mgmtprof.group(1)))
            continue

        match_if = re.match(r"^\s+if1\s+=\s+\S+\s+(\S+)\s+.*$", line)
        if match_if:
            info_hash[obj_key]['ip'] = match_if.group(1)
            continue

    return info_hash


def get_nim_master_info(module):
    """
    Get the Cstate of the nim master.
    """
    global results

    cmd = ['lsnim', '-l', 'master']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.fail_json(**results)

    # Retrieve associated Cstate
    cstate = ''
    for line in stdout.rstrip().split('\n'):
        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            cstate = match_cstate.group(1)

    return cstate


def get_oslevels(module, targets):
    """
    Get the oslevel of the specified targets.

    return a dictionary of the oslevels
    """

    # =========================================================================
    # Launch threads to collect information on targets
    # =========================================================================
    threads = []
    oslevels = {}

    for machine in targets:
        process = threading.Thread(target=run_oslevel_cmd,
                                   args=(module, machine, oslevels))
        process.start()
        threads.append(process)

    for process in threads:
        process.join(300)  # wait 5 min for c_rsh to timeout
        if process.is_alive():
            module.log('[WARNING] {0} Not responding'.format(process))

    return oslevels


def get_nim_lpp_source(module):
    """
    Get the list of lpp_source defined on the nim master.
    """

    global results

    cmd = ['lsnim', '-t', 'lpp_source', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        module.log('NIM - Error getting the lpp_source list - rc:{0}, error:{1}'
                   .format(ret, stderr))
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    # lpp_source list
    lpp_source_list = {}
    for line in stdout.rstrip().split('\n'):
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
        else:
            match_loc = re.match(r"^\s+location\s+=\s+(\S+)$", line)
            if match_loc:
                loc = match_loc.group(1)
                lpp_source_list[obj_key] = loc

    return lpp_source_list


def build_nim_node(module):
    """
    Build nim_node dictionary containing nim clients info and lpp sources info.
    """

    global nim_node

    # =========================================================================
    # Build nim lpp_source list
    # =========================================================================
    nim_lpp_sources = get_nim_lpp_source(module)
    nim_node['lpp_source'] = nim_lpp_sources
    module.debug('lpp source list: {0}'.format(nim_lpp_sources))

    # =========================================================================
    # Build nim clients info
    # =========================================================================
    standalones = get_nim_clients_info(module, 'standalone')
    nim_node['standalone'] = standalones
    module.debug('NIM Clients: {0}'.format(standalones))

    vioses = get_nim_clients_info(module, 'vios')
    nim_node['vios'] = vioses
    module.debug('NIM VIOS Clients: {0}'.format(vioses))

    # =========================================================================
    # Build master info
    # =========================================================================
    cstate = get_nim_master_info(module)
    nim_node['master'] = {}
    nim_node['master']['type'] = 'master'
    nim_node['master']['cstate'] = cstate
    module.debug('NIM master: Cstate = {0}'.format(cstate))


def expand_targets(targets):
    """
    Expand the list of target patterns.

    A target pattern can be of the following form:
        target*       all the nim client machines whose names start
                          with 'target'
        target[n1:n2] where n1 and n2 are numeric: target<n1> to target<n2>
        * or ALL      all the nim client machines
        client_name   the nim client named 'client_name'
        master        the nim master

    arguments:
        targets (list): The list of target patterns

    return: the list of existing machines matching the target patterns
    """
    global nim_node

    # ===========================================
    # Build clients list
    # ===========================================
    clients = []
    for target in targets:

        # -----------------------------------------------------------
        # Build target(s) from: range i.e. quimby[7:12]
        # -----------------------------------------------------------
        rmatch = re.match(r"(\w+)\[(\d+):(\d+)\]", target)
        if rmatch:
            name = rmatch.group(1)
            start = rmatch.group(2)
            end = rmatch.group(3)

            for i in range(int(start), int(end) + 1):
                # target_results.append('{0}{1:02}'.format(name, i))
                curr_name = name + str(i)
                if curr_name in nim_node['standalone']:
                    clients.append(curr_name)

            continue

        # -----------------------------------------------------------
        # Build target(s) from: val*. i.e. quimby*
        # -----------------------------------------------------------
        rmatch = re.match(r"(\w+)\*$", target)
        if rmatch:

            name = rmatch.group(1)

            for curr_name in nim_node['standalone']:
                if re.match(r"^%s\.*" % name, curr_name):
                    clients.append(curr_name)

            continue

        # -----------------------------------------------------------
        # Build target(s) from: all or *
        # -----------------------------------------------------------
        if target.upper() == 'ALL' or target == '*':
            clients = list(nim_node['standalone'])
            continue

        # -----------------------------------------------------------
        # Build target(s) from: quimby05 quimby08 quimby12
        # -----------------------------------------------------------
        if (target in nim_node['standalone']) or (target == 'master'):
            clients.append(target)

    return list(set(clients))


def perform_async_customization(module, lpp_source, targets):
    """
    Perform an asynchronous customization of the given target clients,
    applying the given lpp_source.

    return: the return code of the command.
    """

    global results

    module.debug('NIM - perform_async_customization - lpp_spource: {0}, targets: {1} '
                 .format(lpp_source, targets))

    cmd = ['nim', '-o', 'cust',
           '-a', 'lpp_source=' + lpp_source,
           '-a', 'fixes=update_all',
           '-a', 'accept_licenses=yes',
           '-a', 'async=yes']
    cmd += targets

    module.debug('NIM - Command:{0}'.format(cmd))
    results['nim_output'].append('NIM - Command:{0}'.format(' '.join(cmd)))
    results['nim_output'].append('Start updating machine(s) {0} to {1}'
                                 .format(targets, lpp_source))

    do_not_error = False

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['nim_output'].append('{0}'.format(stderr))

    for line in stdout.rstrip().split('\n'):
        line = line.rstrip()
        matched = re.match(r"Either the software is already at the same level as on the media, or",
                           line)
        if matched:
            do_not_error = True

    results['nim_output'].append('NIM - Finish updating {0} asynchronously.'
                                 .format(targets))
    if ret != 0 or do_not_error:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['nim_output'].append('NIM - Error: Command {0} returns above error!'
                                     .format(cmd))

    module.log("Done nim customize operation {0}".format(cmd))

    return ret


def perform_sync_customization(module, lpp_source, target):
    """
    Perform a synchronous customization of the given target client,
    applying the given lpp_source.

    return: the return code of the command.
    """

    global results

    module.debug(
        'NIM - perform_sync_customization - lpp_spource: {0}, target: {1} '
        .format(lpp_source, target))

    cmd = ['nim', '-o', 'cust',
           '-a', 'lpp_source=' + lpp_source,
           '-a', 'fixes=update_all',
           '-a', 'accept_licenses=yes',
           '-a', 'async=no',
           target]

    module.debug('NIM - Command:{0}'.format(cmd))
    results['nim_output'].append('NIM - Command:{0}'.format(' '.join(cmd)))
    results['nim_output'].append('Start updating machine(s) {0} to {1}'
                                 .format(target, lpp_source))

    do_not_error = False

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    for line in stdout.rstrip().split('\n'):
        results['nim_output'].append('{0}'.format(line))
        line = line.rstrip()
        matched = re.match(r"^Filesets processed:.*?[0-9]+ of [0-9]+", line)
        if matched:
            results['nim_output'].append('\033[2K\r{0}'.format(line))
            continue
        matched = re.match(r"^Finished processing all filesets.", line)
        if matched:
            results['nim_output'].append('\033[2K\r{0}'.format(line))
            continue

    for line in stderr.rstrip().split('\n'):
        line = line.rstrip()
        matched = re.match(r"^Either the software is already at the same level as on the media, or",
                           line)
        if matched:
            do_not_error = True

    results['nim_output'].append('NIM - Finish updating {0} synchronously.'.format(target))
    if ret != 0 or do_not_error:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['nim_output'].append('NIM - Error: Command {0} returns above error!'
                                     .format(cmd))

    module.log("Done nim customize operation {0}".format(cmd))

    return ret


def list_fixes(target, module):
    """
    Get the list of interim fixes for a specified nim client.

    return: a return code (0 if OK)
            the list of fixes
    """

    global results

    fixes = []
    if target == 'master':
        cmd = ['emgr', '-l']
    else:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
               target,
               '"LC_ALL=C /usr/sbin/emgr -l; echo rc=$?"']

    module.debug('EMGR list - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    # remove the rc of c_rsh with echo $?
    if target != 'master':
        s = re.search(r'rc=([-\d]+)$', stdout)
        if s:
            if ret == 0:
                ret = int(s.group(1))
            stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    for line in stdout.rstrip().split('\n'):
        line = line.rstrip()
        line_array = line.split(' ')
        matched = re.match(r"[0-9]", line_array[0])
        if matched:
            module.debug('EMGR list - adding fix {0} to fixes list'
                         .format(line_array[2]))
            fixes.append(line_array[2])

    results['nim_output'].append('{0}'.format(stderr))

    if ret != 0:
        module.log("Error: Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['nim_output'].append('EMGR list - Error: Command {0} returns above error!'
                                     .format(cmd))

    return(ret, fixes)


def remove_fix(target, fix, module):
    """
    Remove an interim fix for a specified nim client.

    return: the return code of the command.
    """

    global results

    if target == 'master':
        cmd = ['emgr', '-r', '-L', fix]
    else:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
               target,
               '"/usr/sbin/emgr -r -L {0}; echo rc=$?"'.format(fix)]

    module.debug('EMGR remove - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    # remove the rc of c_rsh with echo $?
    if target != 'master':
        s = re.search(r'rc=([-\d]+)$', stdout)
        if s:
            if ret == 0:
                ret = int(s.group(1))
            stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    results['nim_output'].append('{0}'.format(stderr))

    if ret != 0:
        module.log("Error: Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['nim_output'].append('EMGR remove - Error: Command {0} returns above error!'
                                     .format(cmd))

    return ret


def find_resource_by_client(module, lpp_type, lpp_time, oslevel_elts):
    """
    Retrieve the good SP or TL resource to associate to the nim client oslevel.

    parameters: lpp_type   SP or TL
                lpp_time   next or latest

    return: the lpp_source found or the current oslevel if not found
    """
    global nim_node

    module.debug('NIM - find resource: {0} {1}'.format(lpp_time, lpp_type))

    lpp_source = ''
    lpp_source_list = sorted(nim_node['lpp_source'].keys())

    if lpp_type == 'tl':
        # reading lpp_source table until we have found the good tl
        for lpp in lpp_source_list:
            lpp_elts = lpp.split('-')
            if lpp_elts[0] != oslevel_elts[0] or lpp_elts[1] <= oslevel_elts[1]:
                continue
            lpp_source = lpp
            if lpp_time == 'next':
                break

    if lpp_type == 'sp':
        # reading lpp_source table until we have found the good sp
        for lpp in lpp_source_list:
            lpp_elts = lpp.split('-')
            if lpp_elts[0] != oslevel_elts[0] \
               or lpp_elts[1] != oslevel_elts[1] \
               or lpp_elts[2] <= oslevel_elts[2]:
                continue
            lpp_source = lpp
            if lpp_time == 'next':
                break

    if (lpp_source is None) or (not lpp_source.strip()):
        # setting lpp_source to current oslevel if not found
        lpp_source = '{0}-{1}-{2}-{3}-lpp_source'.format(oslevel_elts[0], oslevel_elts[1],
                                                         oslevel_elts[2], oslevel_elts[3])
        module.debug('NIM - find resource: server already to the {0} {1}, or no lpp_source were '
                     'found, {2} will be utilized'.format(lpp_time, lpp_type, lpp_source))
    else:
        module.debug('NIM - find resource: found the {0} lpp_source, {1} will be utilized'
                     .format(lpp_time, lpp_source))

    return lpp_source


def nim_update(module, params):
    """
    Update nim clients (targets) with a specified lpp_source.

    In case of updating to the latest TL or SP, the synchronous mode is forced.
    Interim fixes that could block the install are removed.
    """

    global results
    global nim_node

    lpp_source = params['lpp_source']

    async_update = 'no'
    if params['asynchronous']:
        async_update = 'yes'
        log_async = 'asynchronous'
    else:
        log_async = 'synchronous'

    module.log('NIM - {0} update operation on {1} with {2} lpp_source'
               .format(log_async, params['targets'], lpp_source))

    if (params['asynchronous'] and (lpp_source == 'latest_tl'
                                    or lpp_source == 'latest_sp'
                                    or lpp_source == 'next_tl'
                                    or lpp_source == 'next_sp')):
        module.log('[WARNING] Force customization synchronously')
        async_update = 'no'

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    # force interim fixes automatic removal
    if params['force']:
        for target in target_list:
            (ret, fixes) = list_fixes(target, module)
            if ret != 0:
                module.log("Continue to remove as many interim fixes we can")
            for fix in fixes:
                remove_fix(target, fix, module)
                module.log("[WARNING] Interim fix {0} has been automatically removed from {1}"
                           .format(fix, target))

    if async_update == 'yes':   # async update
        if lpp_source not in nim_node['lpp_source']:
            module.log('NIM - Error: cannot find lpp_source {0}'
                       .format(lpp_source))
            results['msg'] = 'NIM - Error: cannot find lpp_source {0}'\
                             .format(nim_node['lpp_source'])
            module.fail_json(**results)
        else:
            module.log('NIM - perform asynchronous software customization for client(s) {0} '
                       'with resource {1}'.format(' '.join(target_list), lpp_source))
            perform_async_customization(module, lpp_source, target_list)

    else:    # synchronous update

        # Get the oslevels of the specified targets only
        oslevels = get_oslevels(module, target_list)
        for (k, val) in oslevels.items():
            if k != 'master':
                nim_node['standalone'][k]['oslevel'] = val
            else:
                nim_node['master']['oslevel'] = val

        for target in target_list:
            # get current oslevel
            cur_oslevel = ''
            if target == 'master':
                cur_oslevel = nim_node['master']['oslevel']
            else:
                cur_oslevel = nim_node['standalone'][target]['oslevel']
            module.debug('NIM - current oslevel: {0}'.format(cur_oslevel))
            if (cur_oslevel is None) or (not cur_oslevel.strip()):
                module.log('[WARNING] Cannot get oslevel for machine {0}'.format(target))
                continue
            cur_oslevel_elts = cur_oslevel.split('-')

            # get lpp source
            new_lpp_source = ''
            if lpp_source == 'latest_tl' or lpp_source == 'latest_sp' \
               or lpp_source == 'next_tl' or lpp_source == 'next_sp':
                lpp_source_array = lpp_source.split('_')
                lpp_time = lpp_source_array[0]
                lpp_type = lpp_source_array[1]
                new_lpp_source = find_resource_by_client(module,
                                                         lpp_type, lpp_time,
                                                         cur_oslevel_elts)
                module.debug('NIM - new_lpp_source: {0}'.format(new_lpp_source))
            else:
                if lpp_source not in nim_node['lpp_source']:
                    module.log('NIM - Error: cannot find lpp_source {0}'
                               .format(lpp_source))
                    results['msg'] = 'NIM - Error: cannot find lpp_source {0}'\
                                     .format(nim_node['lpp_source'])
                    module.fail_json(**results)
                else:
                    new_lpp_source = lpp_source

            # extract oslevel from lpp source
            oslevel_elts = []
            matched = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})-lpp_source$",
                               new_lpp_source)
            if matched:
                oslevel_elts = matched.group(1).split('-')
            else:
                module.log('[WARNING] Cannot get oslevel from lpp source name {0}'
                           .format(new_lpp_source))
                continue

            if cur_oslevel_elts[0] != oslevel_elts[0]:
                module.log('[WARNING] Machine {0} has different release than {1}'
                           .format(target, oslevel_elts[0]))
                continue
            if (cur_oslevel_elts[1] > oslevel_elts[1] or cur_oslevel_elts[1] == oslevel_elts[1] and cur_oslevel_elts[2] >= oslevel_elts[2]):
                module.log('[WARNING] Machine {0} is already at same or higher level than {1}'
                           .format(target, '-'.join(oslevel_elts)))
                continue

            module.log('Machine {0} needs upgrade from {1} to {2}'
                       .format(target, cur_oslevel, '-'.join(oslevel_elts)))

            module.log('NIM - perform synchronous software customization for client(s) {0} '
                       'with resource {1}'.format(target, new_lpp_source))
            perform_sync_customization(module, new_lpp_source, target)

    results['changed'] = True


def nim_maintenance(module, params):
    """
    Apply a maintenance operation (commit) on nim clients (targets).
    """

    global results
    global nim_node

    module.log('NIM - {0} maintenance operation on {1}'
               .format(params['operation'], params['targets']))

    target_list = expand_targets(params['targets'])
    module.debug('NIM - Target list: {0}'.format(target_list))

    flag = '-c'  # initialized to commit flag

    for target in target_list:
        module.log('NIM - perform maintenance operation for client {0}'
                   .format(target))
        cmd = []
        if target in nim_node['standalone']:
            cmd = ['nim', '-o', 'maint',
                   '-a', 'installp_flags=' + flag,
                   '-a', 'filesets=ALL',
                   target]
        else:
            cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
                   target,
                   '"/usr/sbin/installp -c all; echo rc=$?"']

        module.debug('NIM - Command:{0}'.format(cmd))
        results['nim_output'].append('NIM - Command:{0}'.format(' '.join(cmd)))

        ret, stdout, stderr = module.run_command(cmd)

        module.log("[RC] {0}".format(ret))
        module.log("[STDOUT] {0}".format(stdout))
        module.log("[STDERR] {0}".format(stderr))

        # remove the rc of c_rsh with echo $?
        if target not in nim_node['standalone']:
            s = re.search(r'rc=([-\d]+)$', stdout)
            if s:
                if ret == 0:
                    ret = int(s.group(1))
                stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

        results['nim_output'].append('{0}'.format(stderr))

        results['nim_output'].append('NIM - Finished committing {0}.'.format(target))
        if ret != 0:
            module.log("Error: NIM Command: {0} failed with return code {1}"
                       .format(cmd, ret))
            results['nim_output'].append('NIM - Error: Command {0} returns above error!'
                                         .format(cmd))
        else:
            module.log("nim maintenance operation: {0} done".format(cmd))
            results['changed'] = True


def nim_master_setup(module, params):
    """
    Setup a nim master.

    parameter: the device (directory) where to find the lpp source to install
    """

    global results

    module.log('NIM - master setup operation using {0} device'
               .format(params['device']))

    cmd = ['nim_master_setup', '-B',
           '-a', 'mk_resource=no',
           '-a', 'device=' + params['device']]

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_check(module, params):
    """
    Retrieve the oslevel and the Cstate of each nim client
    """

    global results
    global nim_node

    module.log('NIM - check operation')

    if params['targets'] is None:
        # Get the oslevel of all NIM clients and master

        oslevels = get_oslevels(module, nim_node['standalone'])
        for (k, val) in oslevels.items():
            nim_node['standalone'][k]['oslevel'] = val

        oslevels = get_oslevels(module, nim_node['vios'])
        for (k, val) in oslevels.items():
            nim_node['vios'][k]['oslevel'] = val

        oslevels = get_oslevels(module, ['master'])
        nim_node['master']['oslevel'] = oslevels['master']
    else:
        # Get the oslevel for specified targets only

        target_list = expand_targets(params['targets'])
        oslevels = get_oslevels(module, target_list)
        for (k, val) in oslevels.items():
            if k != 'master':
                nim_node['standalone'][k]['oslevel'] = val
            else:
                nim_node['master']['oslevel'] = val


def nim_compare(module, params):
    """
    Compare installation inventory of the nim clients.
    """

    global results

    module.log('NIM - installation inventory comparison for {0} clients'
               .format(params['targets']))

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    cmd = ['niminv', '-o', 'invcmp',
           '-a', 'targets=' + ','.join(target_list),
           '-a', 'base=any']

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def nim_script(module, params):
    """
    Apply a script to customize nim client targets.
    """

    global results

    async_script = ''
    if params['asynchronous']:
        async_script = 'yes'
        log_async = 'asynchronous'
    else:
        async_script = 'no'
        log_async = 'synchronous'

    module.log('NIM - {0} customize operation on {1} with {2} script'
               .format(log_async, params['targets'], params['script']))

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    cmd = ['nim', '-o', 'cust',
           '-a', 'script=' + params['script'],
           '-a', 'async=' + async_script]
    cmd += target_list

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_allocate(module, params):
    """
    Allocate a resource to specified nim clients.
    """

    global results

    module.log('NIM - allocate operation on {0} for {1} lpp source'
               .format(params['targets'], params['lpp_source']))

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    cmd = ['nim', '-o', 'allocate',
           '-a', 'lpp_source=' + params['lpp_source']]
    cmd += target_list

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_deallocate(module, params):
    """
    Deallocate a resource for specified nim clients.
    """

    global results

    module.log('NIM - deallocate operation on {0} for {1} lpp source'
               .format(params['targets'], params['lpp_source']))

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    cmd = ['nim', '-o', 'deallocate',
           '-a', 'lpp_source=' + params['lpp_source']]
    cmd += target_list

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_bos_inst(module, params):
    """
    Install a given list of nim clients.
    A specified group resource is used to install the nim clients.
    If specified, a script is applied to customize the installation.
    """

    global results

    module.log('NIM - bos_inst operation on {0} using {1} resource group'
               .format(params['targets'], params['group']))

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    cmd = ['nim', '-o', 'bos_inst',
           '-a', 'source=mksysb',
           '-a', 'group=' + params['group']]
    if params['script'] and params['script'].strip():
        cmd += ['-a', 'script=' + params['script']]
    cmd += target_list

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_define_script(module, params):
    """
    Define a script nim resource.
    A script resource is defined using the specified script location.
    """

    global results

    module.log(
        'NIM - define script operation for {0} ressource with location {1}'
        .format(params['resource'], params['location']))

    cmd = ['nim', '-o', 'define', '-t', 'script',
           '-a', 'location=' + params['location'],
           '-a', 'server=master',
           params['resource']]

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_remove(module, params):
    """
    Remove a nim resource from the nim database.
    The location of the resource is not destroyed.
    """

    global results

    module.log('NIM - remove operation on {0} resource'
               .format(params['resource']))

    cmd = ['nim', '-o', 'remove', params['resource']]

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_reset(module, params):
    """
    Reset the Cstate of a nim client.
    If the Cstate of the nim client is already in ready state, a warning is
        issued and no operation is made for this client.
    """

    global results
    global nim_node

    module.log('NIM - reset operation on {0} resource'
               .format(params['targets']))

    module.debug('NIM - force is {0}'.format(params['force']))

    target_list = expand_targets(params['targets'])

    module.debug('NIM - Target list: {0}'.format(target_list))

    # remove from the list the targets that are already in "ready' state
    targets_to_reset = []
    targets_discarded = []
    for target in target_list:
        if nim_node['standalone'][target]['cstate'] != 'ready for a NIM operation':
            targets_to_reset.append(target)
        else:
            targets_discarded.append(target)

    if targets_discarded:
        module.log('[WARNING] The following targets are already in a correct state: {0}'
                   .format(','.join(targets_discarded)))

    if targets_to_reset:
        cmd = ['nim']
        if params['force']:
            cmd += ['-F']
        cmd += ['-o', 'reset']
        cmd += targets_to_reset

        module.debug('NIM - Command:{0}'.format(cmd))
        results['nim_output'].append('NIM - Command:{0}'.format(' '.join(cmd)))

        ret, stdout, stderr = module.run_command(cmd)

        module.log("[RC] {0}".format(ret))
        module.log("[STDOUT] {0}".format(stdout))
        module.log("[STDERR] {0}".format(stderr))
        results['stdout'] = stdout
        results['stderr'] = stderr

        if ret != 0:
            module.log("Error: NIM Command: {0} failed with return code {1}"
                       .format(cmd, ret))
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)

        results['changed'] = True


def nim_reboot(module, params):
    """
    Reboot the given nim clients if they are running.
    """

    global results

    module.log('NIM - reboot operation on {0}'.format(params['targets']))

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for {0}.'.format(params['targets'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(target_list))

    if 'master' in target_list:
        module.log('[WARNING] master can not be rebooted, master is discarded from the target list')
        target_list.remove('master')
        if not target_list:
            return

    cmd = ['nim', '-o', 'reboot']
    cmd += target_list

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))
    results['stdout'] = stdout
    results['stderr'] = stderr

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['msg'] = 'Command \'{0}\' successful.'.format(' '.join(cmd))
    results['changed'] = True


def main():
    global results
    global nim_node

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['update', 'master_setup', 'check', 'compare',
                                 'script', 'allocate', 'deallocate',
                                 'bos_inst', 'define_script', 'remove',
                                 'reset', 'reboot', 'maintenance']),
            description=dict(type='str'),
            lpp_source=dict(type='str'),
            targets=dict(type='list', elements='str'),
            asynchronous=dict(type='bool', default=False),
            device=dict(type='str'),
            script=dict(type='str'),
            resource=dict(type='str'),
            location=dict(type='str'),
            group=dict(type='str'),
            force=dict(type='bool', default=False),
            operation=dict(type='str'),
        ),
        required_if=[
            ['action', 'update', ['targets', 'lpp_source']],
            ['action', 'master_setup', ['device']],
            ['action', 'compare', ['targets']],
            ['action', 'script', ['targets', 'script']],
            ['action', 'allocate', ['targets', 'lpp_source']],
            ['action', 'deallocate', ['targets', 'lpp_source']],
            ['action', 'bos_inst', ['targets', 'group']],
            ['action', 'define_script', ['resource', 'location']],
            ['action', 'remove', ['resource']],
            ['action', 'reset', ['targets']],
            ['action', 'reboot', ['targets']],
            ['action', 'maintenance', ['targets']]
        ]
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        nim_output=[],
    )

    module.debug('*** START ***')

    # =========================================================================
    # Get module params
    # =========================================================================
    lpp_source = module.params['lpp_source']
    targets = module.params['targets']
    asynchronous = module.params['asynchronous']
    device = module.params['device']
    script = module.params['script']
    resource = module.params['resource']
    location = module.params['location']
    group = module.params['group']
    force = module.params['force']
    action = module.params['action']
    operation = module.params['operation']

    params = {}

    description = module.params['description']
    if description is None:
        description = "NIM operation: {0} request".format(action)
    params['description'] = description

    # =========================================================================
    # Build nim node info
    # =========================================================================
    build_nim_node(module)

    if action == 'update':
        params['targets'] = targets
        params['lpp_source'] = lpp_source
        params['asynchronous'] = asynchronous
        params['force'] = force
        nim_update(module, params)

    elif action == 'maintenance':
        params['targets'] = targets
        params['operation'] = operation
        nim_maintenance(module, params)

    elif action == 'master_setup':
        params['device'] = device
        nim_master_setup(module, params)

    elif action == 'check':
        params['targets'] = targets
        nim_check(module, params)

    elif action == 'compare':
        params['targets'] = targets
        nim_compare(module, params)

    elif action == 'script':
        params['targets'] = targets
        params['script'] = script
        params['asynchronous'] = asynchronous
        nim_script(module, params)

    elif action == 'allocate':
        params['targets'] = targets
        params['lpp_source'] = lpp_source
        nim_allocate(module, params)

    elif action == 'deallocate':
        params['targets'] = targets
        params['lpp_source'] = lpp_source
        nim_deallocate(module, params)

    elif action == 'bos_inst':
        params['targets'] = targets
        params['group'] = group
        params['script'] = script
        nim_bos_inst(module, params)

    elif action == 'define_script':
        params['resource'] = resource
        params['location'] = location
        nim_define_script(module, params)

    elif action == 'remove':
        params['resource'] = resource
        nim_remove(module, params)

    elif action == 'reset':
        params['targets'] = targets
        params['force'] = force
        nim_reset(module, params)

    elif action == 'reboot':
        params['targets'] = targets
        nim_reboot(module, params)

    else:
        results['msg'] = 'NIM - Error: Unknown action {0}'.format(action)
        module.fail_json(**results)

    results['nim_node'] = nim_node
    results['msg'] = 'NIM {0} completed successfully'.format(action)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
