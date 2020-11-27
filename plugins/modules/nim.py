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
short_description: Performs NIM operations - server setup, install packages, update SP or TL.
description:
- Performs operations on Network Installation Management (NIM) objects.
- It allows to configure the NIM master server, manage NIM objects, perform various operations on
  NIM clients such as software or Base Operating System (BOS) installation, SP or TL updates using
  existing NIM resources, reboot, etc.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- User with root authority to run the nim command.
- 'Privileged user with authorization:
  B(aix.system.install,aix.system.nim.config.server,aix.system.nim.stat)'
options:
  action:
    description:
    - Specifies the action to perform.
    - C(update) to update NIM clients with a specified C(lpp_source).
    - C(master_setup) to setup a NIM master.
    - C(check) to retrieve the B(Cstate) and B(oslevel) of each NIM client.
    - C(compare) to compare installation inventories of the NIM clients.
    - C(script) to apply a script to customize NIM clients.
    - C(allocate) to allocate a resource to specified NIM clients.
    - C(deallocate) to deallocate a resource for specified NIM clients.
    - C(bos_inst) to install BOS image to a given list of NIM clients.
    - C(define_script) to define a script NIM resource.
    - C(remove) to remove a specified NIM resource.
    - C(reset) to reset the B(Cstate) of a NIM client.
    - C(reboot) to reboot the given NIM clients if they are running.
    - C(maintenance) to perform a maintenance operation on NIM clients.
    type: str
    choices: [ update, master_setup, check, compare, script, allocate, deallocate, bos_inst, define_script, remove, reset, reboot, maintenance ]
    required: true
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - C(foo*) specifies all the NIM clients with name starting by 'foo'.
    - C(foo[2:4]) specifies the NIM clients among foo2, foo3 and foo4.
    - C(*) or C(ALL) specifies all the NIM clients.
    type: list
    elements: str
  lpp_source:
    description:
    - Indicates the name of the B(lpp_source) NIM resource to apply to the targets.
    - C(latest_tl), C(latest_sp), C(next_tl) and C(next_sp) can be specified; based on the NIM
      server resources, nim will determine the actual oslevel necessary to update the targets.
    type: str
  device:
    description:
    - The device or directory where to find the lpp source to install.
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
  asynchronous:
    description:
    - If set to C(no), NIM client will be completely installed before starting the installation of
      another NIM client.
    type: bool
    default: no
  force:
    description:
    - Forces action.
    type: bool
    default: no
  description:
    description:
    - Describes the NIM operation (informational only).
    type: str
notes:
  - You can refer to the IBM documentation for additional information on the NIM concept and command
    at U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/install/nim_concepts.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/n_commands/nim.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/n_commands/nim_master_setup.html).
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
    description: Detail information on NIM commands.
    returned: always
    type: str
cmd:
    description: Command executed.
    returned: If the command was run.
    type: str
rc:
    description: The return code.
    returned: If the command was run.
    type: int
stdout:
    description: The standard output.
    returned: always
    type: str
stderr:
    description: The standard error.
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
                "Cstate": "ready for a NIM operation",
                "type": "master"
            },
            "standalone": {
                "nimclient01": {
                    "Cstate": "ready for a NIM operation",
                    "Cstate_result": "success",
                    "Mstate": "currently running",
                    "cable_type1": "N/A",
                    "class": "machines",
                    "comments": "object defined using nimquery -d",
                    "connect": "nimsh",
                    "cpuid": "00F600004C00",
                    "if1": "master_net nimclient01.aus.stglabs.ibm.com AED8E7E90202 ent0",
                    "installed_image": "ansible_img",
                    "mgmt_profile1": "p8-hmc 2 nimclient-cec nimclient-vios1",
                    "netboot_kernel": "64",
                    "platform": "chrp",
                    "prev_state": "customization is being performed",
                }
            },
            "vios": {
                "vios1": {
                    "Cstate": "ready for a NIM operation",
                    "Cstate_result": "success",
                    "Mstate": "currently running",
                    "cable_type1": "N/A",
                    "class": "management",
                    "connect": "nimsh",
                    "cpuid": "00F600004C00",
                    "if1": "master_net vios1.aus.stglabs.ibm.com 0",
                    "mgmt_profile1": "p8-hmc 1 vios-cec",
                    "netboot_kernel": "64",
                    "platform": "chrp",
                    "prev_state": "alt_disk_install operation is being performed",
                }
            }
        }
'''

import re
import threading
# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from ansible.module_utils.basic import AnsibleModule

results = None
nim_node = {}


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - rc      return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

    rcmd = '( LC_ALL=C {0} ); echo rc=$?'.format(' '.join(command))
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    module.debug('exec command:{0}'.format(cmd))

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return (rc, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        rc = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug('exec command rc:{0}, output:{1}, stderr:{2}'.format(rc, stdout, stderr))

    return (rc, stdout, stderr)


def run_oslevel_cmd(module, machine, result):
    """
    Run the oslevel command on target machine.

    Stores the output in the dedicated slot of the result dictionary.

    arguments:
        machine (str): The machine name
        result  (dict): The result of the oslevel command
    """

    result[machine] = 'timedout'

    cmd = ['oslevel', '-s']
    if machine == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, machine, cmd)

    if rc == 0:
        module.debug('{0} oslevel stdout: "{1}"'.format(machine, stdout))
        if stderr.rstrip():
            module.log('"{0}" command stderr: {1}'.format(' '.join(cmd), stderr))

        # return stdout only ... stripped!
        result[machine] = stdout.rstrip()
    else:
        msg = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.log('Failed to get oslevel for {0}: {1}'.format(machine, msg))


def get_nim_type_info(module, lpar_type):
    """
    Build the hash of nim client of type=lpar_type defined on the
    nim master and their associated key = value information.

    arguments:
        module      (dict): The Ansible module
        lpar_type    (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        info_hash   (dict): information from the nim clients
    """
    global results

    cmd = ['lsnim', '-t', lpar_type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        msg = 'Cannot get NIM Client information. Command \'{0}\' failed with return code {1}.'.format(results['cmd'], rc)
        module.log(msg)
        module.log("[STDOUT] {0}".format(stdout))
        module.log("[STDERR] {0}".format(stderr))
        module.fail_json(**results)

    info_hash = build_dict(module, stdout)

    return info_hash


def build_dict(module, stdout):
    """
    Build dictionary with the stdout info

    arguments:
        module  (dict): The Ansible module
        stdout   (str): stdout of the command to parse
    returns:
        info    (dict): NIM info dictionary
    """
    info = {}

    for line in stdout.rstrip().splitlines():
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info[obj_key] = {}
            continue
        rmatch_attr = re.match(r"^\s+(\S+)\s+=\s+(.*)$", line)
        if rmatch_attr:
            info[obj_key][rmatch_attr.group(1)] = rmatch_attr.group(2)
            continue
    return info


def get_nim_master_info(module):
    """
    Get the Cstate of the nim master.

    arguments:
        module      (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = ['lsnim', '-l', 'master']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot get NIM master information. Command \'{0}\' failed with return code {1}.'.format(results['cmd'], rc)
        module.log(results['msg'])
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

    arguments:
        module      (dict): The Ansible module

    return a dictionary of the oslevels
    """

    # Launch threads to collect information on targets
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

    arguments:
        module      (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = ['lsnim', '-t', 'lpp_source', '-l']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        msg = 'Cannot list lpp_source resource. Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.log(msg)
        results['cmd'] = ' '.join(cmd)
        results['rc'] = ret
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = msg
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

    arguments:
        module      (dict): The Ansible module
    """
    global nim_node

    # Build nim lpp_source list
    nim_lpp_sources = get_nim_lpp_source(module)
    nim_node['lpp_source'] = nim_lpp_sources
    module.debug('NIM lpp source list: {0}'.format(nim_lpp_sources))

    # Build nim clients info
    nim_node['standalone'] = get_nim_type_info(module, 'standalone')
    module.debug('NIM standalone clients: {0}'.format(nim_node['standalone']))

    nim_node['vios'] = get_nim_type_info(module, 'vios')
    module.debug('NIM VIOS clients: {0}'.format(nim_node['vios']))

    # Build master info
    cstate = get_nim_master_info(module)
    nim_node['master'] = {}
    nim_node['master']['type'] = 'master'
    nim_node['master']['Cstate'] = cstate
    module.debug('NIM master: {0}'.format(nim_node['master']))


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
        targets (list): The list of target patterns.
    return:
        the list of existing machines matching the target patterns
    """
    global nim_node

    # Build clients list
    clients = []
    for target in targets:

        # Build target(s) from: range i.e. quimby[7:12]
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

        # Build target(s) from: val*. i.e. quimby*
        rmatch = re.match(r"(\w+)\*$", target)
        if rmatch:

            name = rmatch.group(1)

            for curr_name in nim_node['standalone']:
                if re.match(r"^%s\.*" % name, curr_name):
                    clients.append(curr_name)
            continue

        # Build target(s) from: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = list(nim_node['standalone'])
            continue

        # Build target(s) from: quimby05 quimby08 quimby12
        if (target in nim_node['standalone']) or (target == 'master'):
            clients.append(target)

    return list(set(clients))


def perform_async_customization(module, lpp_source, targets):
    """
    Perform an asynchronous customization of the given target clients,
    applying the given lpp_source.

    arguments:
        module     (dict): The Ansible module.
        lpp_source  (str): The lpp_source NIM resource name.
        targets    (list): The list of NIM clients.
    return:
        the return code of the command.
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
    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
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

    arguments:
        module     (dict): The Ansible module.
        lpp_source  (str): The lpp_source NIM resource name.
        target      (str): The target name, can be 'master'.
    return:
        the return code of the command.
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
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


def list_fixes(module, target):
    """
    Get the list of interim fixes for a specified nim client.

    arguments:
        module  (dict): The Ansible module.
        target   (str): The target name, can be 'master'.
    return:
        a return code (0 if OK)
        the list of fixes
    """
    global results

    fixes = []
    cmd = ['emgr', '-l']
    module.debug('EMGR list - Command:{0}'.format(cmd))

    if target == 'master':
        ret, stdout, stderr = module.run_command(cmd)
    else:
        ret, stdout, stderr = nim_exec(module, target, cmd)

    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

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


def remove_fix(module, target, fix):
    """
    Remove an interim fix for a specified nim client.

    arguments:
        module  (dict): The Ansible module.
        target   (str): The target name, can be 'master'.
        fix      (str): The ifix to remove.
    return:
        the return code of the command.
    """
    global results

    cmd = ['emgr', '-r', '-L', fix]
    module.debug('EMGR remove - Command:{0}'.format(cmd))

    if target == 'master':
        ret, stdout, stderr = module.run_command(cmd)
    else:
        ret, stdout, stderr = nim_exec(module, target, cmd)

    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

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

    arguments:
        module          (dict): The Ansible module.
        lpp_type         (str): Type of the resource, can be sp or tl.
        lpp_time         (str): next or latest
        oslevel_elts    (list): List of oslevels to compare to.
    return:
        the lpp_source found or the current oslevel if not found
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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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
            (ret, fixes) = list_fixes(module, target)
            if ret != 0:
                module.log("Continue to remove as many interim fixes we can")
            for fix in fixes:
                remove_fix(module, target, fix)
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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    """

    global results
    global nim_node

    module.log('NIM - maintenance operation on {0}'.format(params['targets']))

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
            module.debug('NIM - Command:{0}'.format(cmd))
            results['nim_output'].append('NIM - Command:{0}'.format(' '.join(cmd)))
            ret, stdout, stderr = module.run_command(cmd)

        else:
            cmd = ['/usr/sbin/installp', '-c', 'all']
            module.debug('NIM - Command:{0}'.format(cmd))
            results['nim_output'].append('NIM - Command:{0}'.format(' '.join(cmd)))
            ret, stdout, stderr = nim_exec(module, target, cmd)

        results['cmd'] = ' '.join(cmd)
        results['rc'] = ret
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.log("[RC] {0}".format(ret))
        module.log("[STDOUT] {0}".format(stdout))
        module.log("[STDERR] {0}".format(stderr))
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
    Initializes the NIM master fileset, install the installation
    image in user specified device and configures the NIM master.

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
    """

    global results

    module.log('NIM - master setup operation using {0} device'
               .format(params['device']))

    cmd = ['nim_master_setup', '-B',
           '-a', 'mk_resource=no',
           '-a', 'device=' + params['device']]

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_check(module, params):
    """
    Retrieve the oslevel and the Cstate of each nim client

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    """
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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def nim_script(module, params):
    """
    Apply a script to customize nim client targets.

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_allocate(module, params):
    """
    Allocate a resource to specified nim clients.

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def nim_deallocate(module, params):
    """
    Deallocate a resource for specified nim clients.

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
    """
    global results

    module.log('NIM - remove operation on {0} resource'
               .format(params['resource']))

    cmd = ['nim', '-o', 'remove', params['resource']]

    module.debug('NIM - Command:{0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

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

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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
        if nim_node['standalone'][target]['Cstate'] != 'ready for a NIM operation':
            targets_to_reset.append(target)
        else:
            targets_discarded.append(target)

    if targets_discarded:
        module.log('[WARNING] The following targets are already in a correct state: {0}'
                   .format(','.join(targets_discarded)))

    if not targets_to_reset:
        return

    cmd = ['nim']
    if params['force']:
        cmd += ['-F']
    cmd += ['-o', 'reset']
    cmd += targets_to_reset

    module.log('Command: {0}'.format(cmd))

    ret, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    if ret != 0:
        msg = "Command: \'{0}\' failed with return code {1}".format(results['cmd'], ret)
        module.log("Error: " + msg)
        results['msg'] = msg
        module.fail_json(**results)

    results['changed'] = True


def nim_reboot(module, params):
    """
    Reboot the given nim clients if they are running.

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
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

    results['cmd'] = ' '.join(cmd)
    results['rc'] = ret
    results['stdout'] = stdout
    results['stderr'] = stderr
    module.log("[RC] {0}".format(ret))
    module.log("[STDOUT] {0}".format(stdout))
    module.log("[STDERR] {0}".format(stderr))

    if ret != 0:
        module.log("Error: NIM Command: {0} failed with return code {1}"
                   .format(cmd, ret))
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

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

    # Get module params
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

    params = {}

    description = module.params['description']
    if description is None:
        description = "NIM operation: {0} request".format(action)
    params['description'] = description
    module.debug('*** START {0} ***'.format(description))

    # Build nim node info
    build_nim_node(module)

    if action == 'update':
        params['targets'] = targets
        params['lpp_source'] = lpp_source
        params['asynchronous'] = asynchronous
        params['force'] = force
        nim_update(module, params)

    elif action == 'maintenance':
        params['targets'] = targets
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

    results['nim_node'] = nim_node
    results['msg'] = 'NIM {0} completed successfully'.format(action)
    module.log(results['msg'])
    module.exit_json(**results)


if __name__ == '__main__':
    main()
