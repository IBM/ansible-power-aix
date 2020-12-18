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
    - C(update) to update NIM standalone clients with a specified C(lpp_source).
    - C(master_setup) to setup a NIM master.
    - C(check) to retrieve the B(Cstate) and B(oslevel) of each NIM client; results in I(nim_node).
    - C(compare) to compare installation inventories of the NIM clients.
    - C(script) to apply a script to customize NIM clients.
    - C(allocate) to allocate a resource to specified NIM clients.
    - C(deallocate) to deallocate a resource for specified NIM clients.
    - C(bos_inst) to install BOS image to a given list of NIM clients.
    - C(define_script) to define a script NIM resource.
    - C(remove) to remove a specified NIM resource.
    - C(reset) to reset the B(Cstate) of a NIM client.
    - C(reboot) to reboot the given NIM clients if they are running.
    - C(maintenance) to perform a maintenance operation that commits filesets on NIM standalone
      clients.
    type: str
    choices: [ update, master_setup, check, compare, script, allocate, deallocate, bos_inst, define_script, remove, reset, reboot, maintenance ]
    required: true
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - C(foo*) specifies all the NIM clients with name starting by 'foo'.
    - C(foo[2:4]) specifies the NIM clients among foo2, foo3 and foo4.
    - C(*) or C(ALL) specifies all the NIM clients.
    - C(vios) or C(standalone) specifies all the NIM clients of this type.
    type: list
    elements: str
  lpp_source:
    description:
    - Indicates the name of the B(lpp_source) NIM resource to apply to the targets.
    - C(latest_tl), C(latest_sp), C(next_tl) and C(next_sp) can be specified; based on the NIM
      server resources, nim will determine the actual oslevel necessary to update the targets;
      the update operation will be synchronous independently from C(asynchronous) value.
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
targets:
    description: List of NIM client actually targeted for the operation.
    returned: if the operation requires a target list
    type: list
    elements: str
    sample: [nimclient01, nimclient02, ...]
status:
    description: Status of the operation for each C(target). It can be empty, SUCCESS or FAILURE.
    returned: if the operation requires a target list
    type: dict
    contains:
        <target>:
            description: Status of the execution on the <target>.
            returned: when target is actually a NIM client
            type: str
            sample: 'SUCCESS'
    sample: "{ nimclient01: 'SUCCESS', nimclient02: 'FAILURE' }"
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
meta:
    description: Detailed information on the module execution.
    returned: always
    type: dict
    contains:
        messages:
            description: Details on errors/warnings not related to a specific target.
            returned: always
            type: list
            elements: str
            sample: see below
        <target>:
            description: Detailed information on the execution on the C(target).
            returned: when target is actually a NIM client
            type: dict
            contains:
                messages:
                    description: Details on errors/warnings
                    returned: always
                    type: list
                    elements: str
                cmd:
                    description: Last command.
                    returned: If the command was run.
                    type: str
                rc:
                    description: The return codeof the last comman.
                    returned: If the command was run.
                    type: str
                stdout:
                    description: Standard output of the last command.
                    returned: If the command was run.
                    type: str
                stderr:
                    description: Standard error of the last command.
                    returned: If the command was run.
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
                    "ip": "vios1.aus.stglabs.ibm.com",
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
import socket
# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from ansible.module_utils.basic import AnsibleModule

results = None


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - rc      return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

    node = get_target_ipaddr(module, node)

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


def get_target_ipaddr(module, target):
    """
    Find the hostname or IP address in the nim_node dict.
    If not found, get the fqdn of the 2nd field of if1 attribute and save it.

    arguments:
        targets (str): The target name.
    return:
        the target hostname or IP address
        the target name if not found
    """
    global results

    ipaddr = target
    for type in results['nim_node']:
        if target not in results['nim_node'][type]:
            continue
        if 'ip' in results['nim_node'][type][target] and results['nim_node'][type][target]['ip']:
            return results['nim_node'][type][target]['ip']

        if 'if1' in results['nim_node'][type][target]:
            match_if = re.match(r"\S+\s+(\S+)\s+.*$", results['nim_node'][type][target]['if1'])
            if match_if:
                try:
                    ipaddr = socket.getfqdn(match_if.group(1))
                except OSError as exc:
                    module.log('NIM - Error: Cannot get FQDN for {0}: {1}'.format(match_if.group(1), exc))
            else:
                module.debug('Parsing of interface if1 failed, got: \'{0}\''.format(results['nim_node'][type][target]['ip']))
        results['nim_node'][type][target]['ip'] = ipaddr

    return ipaddr


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
        results['msg'] = 'Cannot get NIM {0} client information.'.format(lpar_type)

        module.log('NIM - Error: ' + results['msg'])
        module.log('cmd: {0}'.format(results['cmd']))
        module.log('rc: {0}'.format(rc))
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))
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
        results['msg'] = 'Cannot get NIM master information.'
        module.log('NIM - Error: ' + results['msg'])
        module.log('rc: {0}'.format(rc))
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))
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
        module  (dict): The Ansible module
        targets (list): The list of target

    return:
        oslevels (dict): The oslevel of each target
    """
    global results

    # Launch threads to collect information on targets
    threads = []
    oslevels = {}

    for target in targets:
        process = threading.Thread(target=run_oslevel_cmd,
                                   args=(module, target, oslevels))
        process.start()
        threads.append(process)

    for process in threads:
        process.join(300)  # wait 5 min for c_rsh to timeout
        if process.is_alive():
            module.log('NIM - WARNING: {0} Not responding'.format(process))

    module.log('NIM - oslevels: {0}'.format(oslevels))
    return oslevels


def run_oslevel_cmd(module, target, levels):
    """
    Run the oslevel command on target target.
    Stores the output in the levels dictionary.

    arguments:
        target  (str): The NIM target name, can be 'master'
        levels (dict): The results of the oslevel command
    """
    global results
    levels[target] = 'timedout'

    cmd = ['/usr/bin/oslevel', '-s']
    if target == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, target, cmd)

    if rc == 0:
        module.debug('{0} oslevel stdout: {1}'.format(target, stdout))
        if stderr.rstrip():
            module.log('NIM - \'{0}\' command stderr: {1}'.format(' '.join(cmd), stderr))

        # return stdout only ... stripped!
        levels[target] = stdout.rstrip()
    else:
        msg = 'Failed to get oslevel on {0}. Command \'{1}\' failed'.format(target, ' '.join(cmd))
        results['meta']['messages'].append(msg + ', stderr: \'{0}\''.format(stderr))
        module.log('NIM - Error: ' + msg)
        module.log('rc: {0}'.format(rc))
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))


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
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot list lpp_source resource.'
        module.log('NIM - Error: ' + results['msg'])
        module.log('rc: {0}'.format(rc))
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))
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
    global results

    # Build nim lpp_source list
    results['nim_node']['lpp_source'] = get_nim_lpp_source(module)
    module.debug('NIM lpp source list: {0}'.format(results['nim_node']['lpp_source']))

    # Build nim clients info
    results['nim_node']['standalone'] = get_nim_type_info(module, 'standalone')
    module.debug('NIM standalone clients: {0}'.format(results['nim_node']['standalone']))

    results['nim_node']['vios'] = get_nim_type_info(module, 'vios')
    module.debug('NIM VIOS clients: {0}'.format(results['nim_node']['vios']))

    # Build master info
    cstate = get_nim_master_info(module)
    results['nim_node']['master'] = {}
    results['nim_node']['master']['type'] = 'master'
    results['nim_node']['master']['Cstate'] = cstate
    module.debug('NIM master: {0}'.format(results['nim_node']['master']))


def expand_targets(targets):
    """
    Expand the list of target patterns.

    A target pattern can be of the following form:
        target*       all the nim client machines whose names start
                          with 'target'
        target[n1:n2] where n1 and n2 are numeric: target<n1> to target<n2>
        * or ALL      all the nim client machines
        vios          all the nim clients type=vios
        standalone    all the nim clients type=standalone
        client_name   the nim client named 'client_name'
        master        the nim master

    arguments:
        targets (list): The list of target patterns.
    return:
        the list of existing machines matching the target patterns
    """
    global results

    # Build clients list
    clients = []
    for target in targets:
        # Build target(s) from keywords: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = list(results['nim_node']['standalone'])
            clients.extend(list(results['nim_node']['vios']))
            continue

        # Build target(s) from keywords: standalone or vios
        if target.lower() == 'standalone' or target.lower() == 'vios':
            clients.extend(list(results['nim_node'][target.lower()]))
            continue

        # Build target(s) from: range i.e. quimby[7:12]
        rmatch = re.match(r"(\w+)\[(\d+):(\d+)\]", target)
        if rmatch:
            name = rmatch.group(1)
            start = rmatch.group(2)
            end = rmatch.group(3)

            for i in range(int(start), int(end) + 1):
                # target_results.append('{0}{1:02}'.format(name, i))
                curr_name = name + str(i)
                if curr_name in results['nim_node']['standalone']:
                    clients.append(curr_name)
            continue

        # Build target(s) from: val*. i.e. quimby*
        rmatch = re.match(r"(\w+)\*$", target)
        if rmatch:

            name = rmatch.group(1)

            for curr_name in results['nim_node']['standalone']:
                if re.match(r"^%s\.*" % name, curr_name):
                    clients.append(curr_name)
            for curr_name in results['nim_node']['vios']:
                if re.match(r"^%s\.*" % name, curr_name):
                    clients.append(curr_name)
            continue

        # Build target(s) from: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = list(results['nim_node']['standalone'])
            continue

        # Build target(s) from: quimby05 quimby08 quimby12
        if target in results['nim_node']['standalone'] or target in results['nim_node']['vios'] or target == 'master':
            clients.append(target)

    return list(set(clients))


def perform_customization(module, lpp_source, target, is_async):
    """
    Perform a customization of the given target client, applying the given lpp_source.

    arguments:
        module     (dict): The Ansible module.
        lpp_source  (str): The lpp_source NIM resource name.
        target (str|list): The list of NIM clients. Can contain 'master'.
        is_async   (bool): The update mode (sync or async)
    return:
        the return code of the command.
    """
    global results

    cmd = ['nim', '-o', 'cust',
           '-a', 'lpp_source=' + lpp_source,
           '-a', 'fixes=update_all',
           '-a', 'accept_licenses=yes']
    cmd += ['-a', 'async=yes' if is_async else 'async=no']
    if is_async:
        cmd += target
    else:
        cmd += [target]

    do_not_error = False

    rc, stdout, stderr = module.run_command(cmd)

    if is_async:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
    else:
        results['meta'][target]['cmd'] = ' '.join(cmd)
        results['meta'][target]['rc'] = rc
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr

    module.log('cmd: {0}'.format(cmd))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if not is_async:
        for line in stdout.rstrip().split('\n'):
            line = line.rstrip()
            matched = re.match(r"^Filesets processed:.*?[0-9]+ of [0-9]+", line)
            if matched:
                results['meta'][target]['messages'].append('\033[2K\r{0}'.format(line))
                continue
            matched = re.match(r"^Finished processing all filesets.", line)
            if matched:
                results['meta'][target]['messages'].append('\033[2K\r{0}'.format(line))
                continue
            if line:
                results['meta'][target]['messages'].append('{0}'.format(line))

    for line in stdout.rstrip().split('\n'):
        line = line.rstrip()
        matched = re.match(r"^Either the software is already at the same level as on the media, or", line)
        if matched:
            do_not_error = True

    # Log and set proper message
    if rc != 0 or do_not_error:
        if do_not_error:
            msg = 'Cannot update the currently installed software.'
            module.log('NIM - Info: ' + msg)
            rc = 0
        else:
            msg = 'Failed to update installed software.'
            module.log('NIM - Error: ' + msg)
    else:
        msg = 'Successfully updated installed software.'
        results['changed'] = True

    if is_async:
        results['meta']['messages'].append(msg)
    else:
        results['meta'][target]['messages'].append(msg)
    return rc


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
    module.debug('NIM list fixes')

    fixes = []
    cmd = ['/usr/sbin/emgr', '-l']
    module.log('NIM - EMGR list on {0} - Command:{1}'.format(target, cmd))

    if target == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, target, cmd)

    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    # Best effort: let's try parsing
    for line in stdout.rstrip().split('\n'):
        line = line.rstrip()
        line_array = line.split(' ')
        matched = re.match(r"[0-9]", line_array[0])
        if matched:
            module.debug('EMGR list - adding fix {0} to fixes list'.format(line_array[2]))
            fixes.append(line_array[2])

    if rc != 0:
        msg = 'Failed to list fixes with emgr. Command \'{0}\' failed.'.format(cmd)
        module.log('NIM - Error: ' + msg)
        results['meta'][target]['messages'].append(msg)
        results['meta'][target]['messages'].append('rc: {0}'.format(rc))
        results['meta'][target]['messages'].append('stdout: {0}'.format(stdout))
        results['meta'][target]['messages'].append('stderr: {0}'.format(stderr))

    return(rc, fixes)


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

    cmd = ['/usr/sbin/emgr', '-r', '-L', fix]
    module.log('EMGR remove - Command:{0}'.format(cmd))

    if target == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, target, cmd)

    if rc != 0:
        msg = 'Failed to remove fix: {0}. Command: {1} failed.'.format(fix, ' '.join(cmd))
        module.log('NIM - Error: On {0} '.format(target) + msg)
        module.log('rc: {0}'.format(rc))
        results['meta']['target']['messages'].append(msg)
        results['meta']['target']['messages'].append('stdout: {0}'.format(stdout))
        results['meta']['target']['messages'].append('stderr: {0}'.format(stderr))
    else:
        msg = 'Fix successfully removed: {0}.'.format(fix)
        module.log('NIM - On {0} '.format(target) + msg)
        results['meta']['target']['messages'].append(msg)
        results['changed'] = True

    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    return rc


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
    global results

    module.debug('NIM - find resource: {0} {1}'.format(lpp_time, lpp_type))

    lpp_source = ''
    lpp_source_list = sorted(results['nim_node']['lpp_source'].keys())

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
            if lpp_elts[0] != oslevel_elts[0] or lpp_elts[1] != oslevel_elts[1] or lpp_elts[2] <= oslevel_elts[2]:
                continue
            lpp_source = lpp
            if lpp_time == 'next':
                break

    if (lpp_source is None) or (not lpp_source.strip()):
        # setting lpp_source to current oslevel if not found
        lpp_source = '{0}-{1}-{2}-{3}-lpp_source'.format(oslevel_elts[0], oslevel_elts[1], oslevel_elts[2], oslevel_elts[3])
        module.debug('NIM - find resource: server already to the {0} {1}, or no lpp_source were found, {2} will be utilized'
                     .format(lpp_time, lpp_type, lpp_source))
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
        module.log('NIM - WARNING: Force customization synchronously')
        async_update = 'no'

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    results['targets'] = list(target_list)
    module.debug('NIM - Target list: {0}'.format(target_list))
    for target in results['targets']:
        if target in results['nim_node']['vios']:
            target_list.remove(target)
            msg = 'update operation is not supported on VIOS. Use power_aix.nim_updateios module instead.'
            results['meta'][target] = {'messages': [msg]}
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
            continue

    if async_update == 'no' or params['force']:
        for target in results['targets']:
            if target not in results['meta']:
                results['meta'][target] = {'messages': []}  # first time init
                results['status'][target] = ''  # first time init

    # force interim fixes automatic removal
    if params['force']:
        msg = 'Force automatic removal of installed fixes: best effort'
        results['meta']['messages'].append(msg)
        module.log('NIM - ' + msg)
        for target in target_list:
            rc, fixes = list_fixes(module, target)
            msg = 'Will remove as many interim fixes we can: {0}'.format(fixes)
            results['meta']['messages'].append(msg)
            module.log('NIM - On {0} '.format(target) + msg)
            for fix in fixes:
                remove_fix(module, target, fix)

    if async_update == 'yes':   # async update
        if lpp_source not in results['nim_node']['lpp_source']:
            results['msg'] = 'Cannot find lpp_source \'{0}\'.'.format(results['nim_node']['lpp_source'])
            module.log('NIM - Error: ' + results['msg'])
            module.fail_json(**results)

        msg = 'Asynchronous software customization for client(s) {0} with resource {1}.'.format(','.join(target_list), lpp_source)
        results['meta']['messages'].append(msg)
        module.log('NIM - ' + msg)

        rc = perform_customization(module, lpp_source, target_list, True)
        if rc:
            results['msg'] = 'Asynchronous software customization operation failed. See status and meta for details.'
            module.log('NIM - Error: ' + results['msg'])
            module.fail_json(**results)

    else:    # synchronous update
        # Get the oslevels of the specified targets only
        oslevels = get_oslevels(module, target_list)
        for (k, val) in oslevels.items():
            if k != 'master':
                results['nim_node']['standalone'][k]['oslevel'] = val
            else:
                results['nim_node']['master']['oslevel'] = val

        for target in target_list:
            # get current oslevel
            cur_oslevel = ''
            if target == 'master':
                cur_oslevel = results['nim_node']['master']['oslevel']
            else:
                cur_oslevel = results['nim_node']['standalone'][target]['oslevel']
            if (cur_oslevel is None) or (not cur_oslevel.strip()) or cur_oslevel == 'timedout':
                msg = 'Invalid oslevel got: \'{0}\'.'.format(cur_oslevel)
                results['meta'][target]['messages'].append(msg)
                module.log('NIM - WARNING: On {0} '.format(target) + msg)
                continue
            cur_oslevel_elts = cur_oslevel.split('-')

            # get lpp source
            new_lpp_source = ''
            if lpp_source == 'latest_tl' or lpp_source == 'latest_sp' \
               or lpp_source == 'next_tl' or lpp_source == 'next_sp':
                lpp_source_array = lpp_source.split('_')
                lpp_time = lpp_source_array[0]
                lpp_type = lpp_source_array[1]

                new_lpp_source = find_resource_by_client(module, lpp_type, lpp_time, cur_oslevel_elts)
                msg = 'Using lpp_source: {0}'.format(new_lpp_source)
                results['meta']['messages'].append(msg)
                module.debug('NIM - ' + msg)
            else:
                if lpp_source not in results['nim_node']['lpp_source']:
                    results['msg'] = 'Cannot find lpp_source \'{0}\' in \'{1}\'.'.format(lpp_source, results['nim_node']['lpp_source'])
                    module.log('NIM - Error: ' + results['msg'])
                    module.fail_json(**results)
                else:
                    new_lpp_source = lpp_source

            # extract oslevel from lpp source
            oslevel_elts = []
            matched = re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})-lpp_source$", new_lpp_source)
            if matched:
                oslevel_elts = matched.group(1).split('-')
            else:
                msg = 'Cannot get oslevel from lpp source name: {0}'.format(new_lpp_source)
                results['meta'][target]['messages'].append(msg)
                module.log('NIM - WARNING: On {0} '.format(target) + msg)
                continue

            if cur_oslevel_elts[0] != oslevel_elts[0]:
                msg = 'Has a different release number than {0}, got {1}'.format('-'.join(oslevel_elts), cur_oslevel_elts)
                results['meta'][target]['messages'].append(msg)
                module.log('NIM - WARNING: {0} '.format(target) + msg)
                continue
            if (cur_oslevel_elts[1] > oslevel_elts[1] or cur_oslevel_elts[1] == oslevel_elts[1] and cur_oslevel_elts[2] >= oslevel_elts[2]):
                msg = 'Already at same or higher level: {0}, got: {1}'.format('-'.join(oslevel_elts), cur_oslevel_elts)
                results['meta'][target]['messages'].append(msg)
                module.log('NIM - {0} '.format(target) + msg)
                continue

            msg = 'Synchronous software customization from {0} to {1}.'.format(cur_oslevel, '-'.join(oslevel_elts))
            results['meta'][target]['messages'].append(msg)
            module.log('NIM - On {0} '.format(target) + msg)

            rc = perform_customization(module, new_lpp_source, target, False)
            if rc:
                results['status'][target] = 'FAILURE'
            else:
                results['status'][target] = 'SUCCESS'


def nim_maintenance(module, params):
    """
    Apply a maintenance operation (commit) on nim clients (targets).

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    """

    global results

    module.log('NIM - maintenance operation on {0}'.format(params['targets']))

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    flag = '-c'  # initialized to commit flag

    for target in results['targets']:
        module.log('NIM - perform maintenance operation for client {0}'.format(target))
        results['meta'][target] = {'messages': []}  # first time init
        results['status'][target] = ''  # first time init

        if target in results['nim_node']['vios']:
            msg = 'maintenance operation is not supported on VIOS.'
            results['meta'][target]['messages'].append(msg)
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
            continue

        if target in results['nim_node']['standalone']:
            cmd = ['nim', '-o', 'maint',
                   '-a', 'installp_flags=' + flag,
                   '-a', 'filesets=ALL',
                   target]
            rc, stdout, stderr = module.run_command(cmd)
        else:
            cmd = ['/usr/sbin/installp', '-c', 'all']
            rc, stdout, stderr = nim_exec(module, target, cmd)

        results['meta'][target]['cmd'] = ' '.join(cmd)
        results['meta'][target]['rc'] = rc
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr

        if rc != 0:
            msg = 'maintenance operation failed on {0}.'.format(target)
            results['meta']['messages'].append(msg)
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
        else:
            msg = 'maintenance operation successfull on {0}.'.format(target)
            results['meta']['messages'].append(msg)
            module.log('NIM - ' + msg)
            results['changed'] = True
            results['status'][target] = 'SUCCESS'

        module.log('cmd: {0}'.format(results['cmd']))
        module.log('rc: {0}'.format(rc))
        module.log('stdout: {0}'.format(stdout))
        module.log('stderr: {0}'.format(stderr))


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

    module.log('NIM - master setup operation using {0} device'.format(params['device']))

    cmd = ['nim_master_setup', '-B',
           '-a', 'mk_resource=no',
           '-a', 'device=' + params['device']]

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to setup the NIM master.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    results['changed'] = True


def nim_check(module, params):
    """
    Retrieve the oslevel and the Cstate of each nim client

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    """
    global results

    module.log('NIM - check operation')

    if params['targets'] is None:
        # Get the oslevel of all NIM clients and master
        oslevels = get_oslevels(module, results['nim_node']['standalone'])
        for (k, val) in oslevels.items():
            results['nim_node']['standalone'][k]['oslevel'] = val

        oslevels = get_oslevels(module, results['nim_node']['vios'])
        for (k, val) in oslevels.items():
            results['nim_node']['vios'][k]['oslevel'] = val

        oslevels = get_oslevels(module, ['master'])
        results['nim_node']['master']['oslevel'] = oslevels['master']

    else:
        # Get the oslevel for specified targets only
        results['targets'] = expand_targets(params['targets'])
        if not results['targets']:
            results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
            module.log('NIM - Error: ' + results['msg'])
            module.fail_json(**results)

        oslevels = get_oslevels(module, results['targets'])
        for (k, val) in oslevels.items():
            if k == 'master':
                results['nim_node']['master']['oslevel'] = val
            elif k in results['nim_node']['standalone']:
                results['nim_node']['standalone'][k]['oslevel'] = val
            else:
                results['nim_node']['vios'][k]['oslevel'] = val


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

    module.log('NIM - installation inventory comparison for {0} clients'.format(params['targets']))

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    cmd = ['niminv', '-o', 'invcmp',
           '-a', 'targets=' + ','.join(results['targets']),
           '-a', 'base=any']

    module.debug('NIM - Command:{0}'.format(cmd))

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to compare installation inventories.'
        module.log('NIM - Error: ' + results['msg'])
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

    module.log('NIM - {0} customize operation on {1} with {2} script'.format(log_async, params['targets'], params['script']))

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    cmd = ['nim', '-o', 'cust',
           '-a', 'script=' + params['script'],
           '-a', 'async=' + async_script]
    cmd += results['targets']

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to apply script.'
        module.log('NIM - Error: ' + results['msg'])
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

    module.log('NIM - allocate operation on {0} for {1} lpp source'.format(params['targets'], params['lpp_source']))

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    cmd = ['nim', '-o', 'allocate',
           '-a', 'lpp_source=' + params['lpp_source']]
    cmd += results['targets']

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to allocate resource.'
        module.log('NIM - Error: ' + results['msg'])
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

    module.log('NIM - deallocate operation on {0} for {1} lpp source'.format(params['targets'], params['lpp_source']))

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    cmd = ['nim', '-o', 'deallocate',
           '-a', 'lpp_source=' + params['lpp_source']]
    cmd += results['targets']

    module.debug('NIM - Command:{0}'.format(cmd))

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to deallocate resource.'
        module.log('NIM - Error: ' + results['msg'])
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

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    cmd = ['nim', '-o', 'bos_inst',
           '-a', 'source=mksysb',
           '-a', 'group=' + params['group']]
    if params['script'] and params['script'].strip():
        cmd += ['-a', 'script=' + params['script']]
    cmd += results['targets']

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to BOS install.'
        module.log('NIM - Error: ' + results['msg'])
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

    module.log('NIM - define script operation for {0} resource with location {1}'.format(params['resource'], params['location']))

    # Check if the script already exists
    scripts = get_nim_type_info(module, 'script')

    if params['resource'] in scripts:
        if params['location'] == scripts[params['resource']]['location'] and scripts[params['resource']]['server'] == 'master':
            msg = 'script resource \'{0}\' already exists.'.format(params['resource'])
            results['meta']['messages'].append(msg)
            module.log('NIM - ' + msg)
            return

    # Best effort, try to define the resource
    cmd = ['nim', '-o', 'define', '-t', 'script',
           '-a', 'location=' + params['location'],
           '-a', 'server=master',
           params['resource']]

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to define script resource.'
        module.log('NIM - Error: ' + results['msg'])
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

    module.log('NIM - remove operation on {0} resource'.format(params['resource']))

    cmd = ['nim', '-o', 'remove', params['resource']]

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to remove resource.'
        module.log('NIM - Error: ' + results['msg'])
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

    module.log('NIM - reset operation on {0} resource (force: {1})'.format(params['targets'], params['force']))

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    # remove from the list the targets that are already in 'ready' state
    targets_to_reset = []
    targets_discarded = []
    for target in results['targets']:
        if target in results['nim_node']['standalone'] and results['nim_node']['standalone'][target]['Cstate'] != 'ready for a NIM operation':
            targets_to_reset.append(target)
        elif target in results['nim_node']['vios'] and results['nim_node']['vios'][target]['Cstate'] != 'ready for a NIM operation':
            targets_to_reset.append(target)
        else:
            targets_discarded.append(target)

    if targets_discarded:
        msg = 'The following targets are already ready for a NIM operation: {0}'.format(','.join(targets_discarded))
        results['meta']['messages'].append(msg)
        module.log('NIM - ' + msg)

    if not targets_to_reset:
        msg = 'No target to reset.'
        results['meta']['messages'].append(msg)
        module.log('NIM - ' + msg)
        return

    cmd = ['nim']
    if params['force']:
        cmd += ['-F']
    cmd += ['-o', 'reset']
    cmd += targets_to_reset

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to reset current NIM state on {0}.'.format(','.join(targets_to_reset))
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    msg = 'Successfully reset targets: {0}.'.format(','.join(targets_to_reset))
    results['meta']['messages'].append(msg)
    module.log('NIM - ' + msg)

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

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = 'No matching target found for targets \'{0}\'.'.format(params['targets'])
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug('NIM - Target list: {0}'.format(results['targets']))

    if 'master' in results['targets']:
        results['targets'].remove('master')
        msg = 'master can not be rebooted, master is discarded from the target list.'
        results['meta']['messages'].append(msg)
        module.log('NIM - ' + msg)
        if not results['targets']:
            return

    cmd = ['nim', '-o', 'reboot']
    cmd += results['targets']

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log('cmd: {0}'.format(results['cmd']))
    module.log('rc: {0}'.format(rc))
    module.log('stdout: {0}'.format(stdout))
    module.log('stderr: {0}'.format(stderr))

    if rc != 0:
        results['msg'] = 'Failed to reboot NIM clients: {0}.'.format(','.join(results['targets']))
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    results['changed'] = True


def main():
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['update', 'master_setup', 'check', 'compare',
                                 'script', 'allocate', 'deallocate',
                                 'bos_inst', 'define_script', 'remove',
                                 'reset', 'reboot', 'maintenance']),
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
        status={},
        stdout='',
        stderr='',
        meta={'messages': []},
        # meta structure will be updated as follow:
        # meta={
        #   target_name:{
        #       'messages': [],     detail execution messages
        #       'cmd': '',
        #       'rc': '',
        #       'stdout': '',
        #       'stderr': '',
        #   }
        # }
        nim_node={},
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

    module.debug('*** START NIM operation {0} ***'.format(action))

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

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

    # Exit
    if results['status']:
        target_errored = [key for key, val in results['status'].items() if 'FAILURE' in val]
        if len(target_errored):
            results['msg'] = 'NIM {0} operation failed for {1}. See status and meta for details.'.format(action, target_errored)
            module.log(results['msg'])
            module.fail_json(**results)

    results['msg'] = 'NIM {0} operation successfull. See status and meta for details.'.format(action)
    module.log(results['msg'])
    module.exit_json(**results)


if __name__ == '__main__':
    main()
