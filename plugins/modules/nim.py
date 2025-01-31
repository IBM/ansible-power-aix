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
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- User with root authority to run the nim command.
- 'Privileged user with authorization:
  B(aix.system.install,aix.system.nim.config.server,aix.system.nim.stat)'
options:
  action:
    description:
    - Specifies the action to perform.
    - C(update) to update NIM standalone clients with a specified C(lpp_source).
    - C(master_setup) to setup a NIM master.
    - C(register_client) to register new nim client to nim master
    - C(check) to retrieve the B(Cstate) and B(oslevel) of each NIM client; results in I(nim_node).
    - C(compare) to compare installation inventories of the NIM clients.
    - C(script) to apply a script to customize NIM clients.
    - C(allocate) to allocate a resource to specified NIM clients.
    - C(deallocate) to deallocate a resource for specified NIM clients.
    - C(install_fileset) to install filesets from the provided installp bundle.
    - C(bos_inst) to install BOS image to a given list of NIM clients.
    - C(define_script) to define a script NIM resource.
    - C(remove) to remove a specified NIM resource.
    - C(reset) to reset the B(Cstate) of a NIM client.
    - C(reboot) to reboot the given NIM clients if they are running.
    - C(maintenance) to perform a maintenance operation that commits filesets on NIM standalone
      clients.
    - C(show) to perform a query on a NIM object.
    type: str
    choices: [ update,master_setup,check,compare,script,allocate,deallocate,bos_inst, define_script,remove, reset, reboot, maintenance, show, register_client ]
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
  new_targets:
    description:
    - Specifies the new targets to be registered as nim client.
    - Specifies <machine full name>-<login id>-<password> as a list in same format.
    - Required when I(action) is register_client
    type: list
    elements: str
  lpp_source:
    description:
    - Indicates the name of the B(lpp_source) NIM resource to apply to the targets.
    - C(latest_tl), C(latest_sp), C(next_tl) and C(next_sp) can be specified; based on the NIM
      server resources, nim will determine the actual oslevel necessary to update the targets;
      the update operation will be synchronous independently from C(asynchronous) value.
    type: str
  installp_bundle:
    description:
    - Specifies the installp bundle containing names of the filesets that need to be installed.
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
  boot_client:
    description:
    - If set to C(no), the NIM server will not attempt to reboot the client when the action is C(bos_inst).
    type: bool
    default: yes
  object_type:
    description:
    - Specifies which NIM object type to query for action C(show). Ignored for any other action.
    - If not set for C(show), then all NIM objects in the target machine will be queried.
    type: str
    default: all
  alt_disk_update_name:
    description:
    - Specifies name of the alternate disk where installation takes place
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
    asynchronous: false
    targets: all

- name: Query all standalone objects defined in a NIM master
  nim:
    action: show
    object_type: standalone
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
                    description: The return code of the last command.
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
        query:
            description: Queried information of all NIM objects of the specified type.
            returned: only for show action
            type: dict
            contains:
                <nim_object>:
                    description: Information for each individual NIM object fetched.
                    returned: if NIM object of this type exists
                    type: dict
            sample: see below
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

    cmd = ' '.join(command)
    rcmd = f'( LC_ALL=C { cmd } ); echo rc=$?'
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    module.debug(f'exec command:{ cmd }')

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return (rc, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        rc = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug(f'exec command rc:{ rc }, output:{ stdout }, stderr:{ stderr }')

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
                    matched = match_if.group(1)
                    module.log(f'NIM - Error: Cannot get FQDN for { matched }: { exc }')
            else:
                debug_ip = results['nim_node'][type][target]['ip']
                module.debug(f'Parsing of interface if1 failed, got: { debug_ip }')
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

    cmd = ['lsnim', '-t', lpar_type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = f'Cannot get NIM { lpar_type } client information.'

        module.log(f'rc: { rc }')
        module.log(f'stdout: { stdout }')
        module.log(f'stderr: { stderr }')
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

    cmd = ['lsnim', '-l', 'master']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot get NIM master information.'
        module.log('NIM - Error: ' + results['msg'])
        module.log(f'rc: {rc}')
        module.log(f'stdout: { stdout }')
        module.log(f'stderr: { stderr }')
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
            module.log(f'NIM - WARNING: { process } Not responding')

    module.log(f'NIM - oslevels: { oslevels }')
    return oslevels


def check_if_allocated(module, provided_lpp_source, targets):
    """
    Check if the lpp source is allocated to the provided targets.

    arguments:
        lpp_source (str) : LPP Source
        targtes (list) : list of targets that need to be checked

    returns:
        new_targets (list) : Updated list having only the targets that
        have the specified lpp_source allocated to them.
    """
    cmd = "lsnim -t lpp_source"

    targets = expand_targets(targets)

    if not targets:
        results['msg'] = f"No matching target found for targets \'{ module.params['targets'] }\'."
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    new_targets = []
    cmd_failed = []

    for target in targets:
        cmd += f" {target}"
        rc, stdout, stderr = module.run_command(cmd)
        results['cmd'] = cmd
        results['stderr'] = stderr
        results['stdout'] = stdout
        if rc:
            cmd_failed.append(target)
            continue
        stdout_lines = stdout.splitlines()
        stdout_list = ' '.join(stdout_lines).split()
        if provided_lpp_source in stdout_list:
            new_targets.append(target)

    results['msg'] += f"Could not get allocation information about the following targets: {cmd_failed}"

    if len(cmd_failed) == len(targets):
        module.fail_json(**results)

    return new_targets


def run_oslevel_cmd(module, target, levels):
    """
    Run the oslevel command on target target.
    Stores the output in the levels dictionary.

    arguments:
        target  (str): The NIM target name, can be 'master'
        levels (dict): The results of the oslevel command
    """

    levels[target] = 'timedout'

    cmd = ['/usr/bin/oslevel', '-s']
    if target == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, target, cmd)

    if rc == 0:
        module.debug(f'{ target } oslevel stdout: { stdout }')
        if stderr.rstrip():
            module.log(f'NIM command stderr: { stderr }')

        # return stdout only ... stripped!
        levels[target] = stdout.rstrip()
    else:
        command = ' '.join(cmd)
        msg = f'Failed to get oslevel on { target }. Command \'{ command }\' failed'
        results['meta']['messages'].append(msg + f', stderr: \'{ stderr }\'')
        module.log('NIM - Error: ' + msg)
        module.log(f'rc: { rc }')
        module.log(f'stdout: { stdout }')
        module.log(f'stderr: { stderr }')


def get_nim_lpp_source(module):
    """
    Get the list of lpp_source defined on the nim master.

    arguments:
        module      (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    """

    cmd = ['lsnim', '-t', 'lpp_source', '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['cmd'] = ' '.join(cmd)
        results['rc'] = rc
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot list lpp_source resource.'
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

    # Build nim lpp_source list
    results['nim_node']['lpp_source'] = get_nim_lpp_source(module)
    debug_lpp_src = results['nim_node']['lpp_source']
    module.debug(f'NIM lpp source list: { debug_lpp_src }')

    # Build nim clients info
    results['nim_node']['standalone'] = get_nim_type_info(module, 'standalone')
    debug_standalone = results['nim_node']['standalone']
    module.debug(f'NIM standalone clients: { debug_standalone }')

    results['nim_node']['vios'] = get_nim_type_info(module, 'vios')
    debug_vios = results['nim_node']['vios']
    module.debug(f'NIM VIOS clients: { debug_vios }')

    # Build master info
    cstate = get_nim_master_info(module)
    results['nim_node']['master'] = {}
    results['nim_node']['master']['type'] = 'master'
    results['nim_node']['master']['Cstate'] = cstate
    debug_master = results['nim_node']['master']
    module.debug(f'NIM master: { debug_master }')


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
                if re.match(rf"^{name}\.*", curr_name):
                    clients.append(curr_name)
            for curr_name in results['nim_node']['vios']:
                if re.match(rf"^{name}\.*", curr_name):
                    clients.append(curr_name)
            continue

        # Build target(s) from: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = list(results['nim_node']['standalone'])
            continue

        # Build target(s)
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

    alt_disk_update_name = module.params['alt_disk_update_name']

    if alt_disk_update_name:
        cmd = ['nim', '-o', 'alt_disk_install', '-a', 'source=rootvg', '-a', 'lpp_source=' + lpp_source,
               '-a', 'fixes=update_all', '-a', 'disk=' + alt_disk_update_name, '-a', 'installp_flags=\"-acNgXY\"',
               ]
    else:
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

    module.log(f'cmd: { cmd }')
    module.log(f'rc: { rc }')
    module.log(f'stdout: { stdout }')
    module.log(f'stderr: { stderr }')

    if not is_async:
        for line in stdout.rstrip().split('\n'):
            line = line.rstrip()
            matched = re.match(r"^Filesets processed:.*?[0-9]+ of [0-9]+", line)
            if matched:
                results['meta'][target]['messages'].append(f'\033[2K\r{line}')
                continue
            matched = re.match(r"^Finished processing all filesets.", line)
            if matched:
                results['meta'][target]['messages'].append(f'\033[2K\r{line}')
                continue
            if line:
                results['meta'][target]['messages'].append(f'{line}')

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


def install_filesets(module, params):
    """
    Install filesets on the specified nim client.

    arguments:
        module  (dict): The Ansible module.
        target   (str): The nim client on which installation needs to be performed.
    return:
        a return code (0 if OK)
    """

    module.debug('NIM install filesets')

    lpp_source = params['lpp_source']
    installp_bundle = params['installp_bundle']

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = f"No matching target found for targets \'{ params['targets'] }\'."
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    changed_val = 0

    for target in target_list:
        # Allocate the installp bundle

        alloc_cmd = ['nim', '-o', 'allocate',
                     '-a', 'lpp_source=' + lpp_source,
                     '-a', 'installp_bundle=' + installp_bundle]
        alloc_cmd.append(target)

        rc, stdout, stderr = module.run_command(alloc_cmd)

        results['meta'][target] = {}
        results['meta'][target]['cmd'] = ' '.join(alloc_cmd)
        results['meta'][target]['rc'] = rc
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr

        if rc:
            msg = f"Couldn't install filesets - Allocation operation failed on {target}."
            results['meta']['messages'].append(msg)
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
            continue

        # Perform customization

        cust_cmd = ['nim', '-o', 'cust',
                    '-a', 'accept_licenses=yes']
        cust_cmd.append(target)

        rc, stdout, stderr = module.run_command(cust_cmd)

        results['meta'][target]['cmd'] = ' '.join(cust_cmd)
        results['meta'][target]['rc'] = rc
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr

        if rc:
            msg = f"Couldn't install filesets - Customization operation failed on {target}."
            results['meta']['messages'].append(msg)
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
        else:
            if "SUCCESS" in stdout.split():
                changed_val = 1
            results['status'][target] = 'SUCCESS'

    # Set changed to true if the filesets were installed, and were not already present
    if changed_val:
        results['changed'] = True


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

    module.debug('NIM list fixes')

    fixes = []
    cmd = ['/usr/sbin/emgr', '-l']
    module.log(f'NIM - EMGR list on { target } - Command:{ cmd }')

    if target == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, target, cmd)

    module.log(f'cmd: { cmd }')
    module.log(f'rc: { rc }')
    module.log(f'stdout: { stdout }')
    module.log(f'stderr: { stderr }')

    # Best effort: let's try parsing
    for line in stdout.rstrip().split('\n'):
        line = line.rstrip()
        line_array = line.split(' ')
        matched = re.match(r"[0-9]", line_array[0])
        if matched:
            debug_fix = line_array[2]
            module.debug(f'EMGR list - adding fix { debug_fix } to fixes list')
            fixes.append(line_array[2])

    if rc != 0:
        msg = f'Failed to list fixes with emgr. Command \'{ cmd }\' failed.'
        module.log('NIM - Error: ' + msg)
        results['meta'][target]['messages'].append(msg)
        results['meta'][target]['messages'].append(f'rc: {rc}')
        results['meta'][target]['messages'].append(f'stdout: {stdout}')
        results['meta'][target]['messages'].append(f'stderr: {stderr}')

    return (rc, fixes)


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

    cmd = ['/usr/sbin/emgr', '-r', '-L', fix]
    cmd = ' '.join(cmd)
    module.log(f'EMGR remove - Command:{ cmd }')

    if target == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, target, cmd)

    if rc != 0:
        msg = f'Failed to remove fix: {fix}. Command: {cmd} failed.'
        results['meta']['target']['messages'].append(msg)
        results['meta']['target']['messages'].append(f'stdout: {stdout}')
        results['meta']['target']['messages'].append(f'stderr: {stderr}')
    else:
        msg = f'Fix successfully removed: {fix}.'
        results['meta']['target']['messages'].append(msg)
        results['changed'] = True

    module.log(f'stdout: { stdout }')
    module.log(f'stderr: { stderr }')

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

    module.debug(f'NIM - find resource: { lpp_time } { lpp_type}')

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
        part1 = oslevel_elts[0]
        part2 = oslevel_elts[1]
        part3 = oslevel_elts[2]
        part4 = oslevel_elts[3]
        lpp_source = f'{part1}-{part2}-{part3}-{part4}-lpp_source'
        module.debug(f'NIM - find resource: server already to the {lpp_time} {lpp_type}, or no lpp_source were found, {lpp_source} will be utilized')
    else:
        module.debug(f'NIM - find resource: found the {lpp_time} lpp_source, {lpp_source} will be utilized')

    return lpp_source


def check_alt_disk(module, alt_disk_update_name, target_list):
    """
    checks if the specified alt disk exists in the system or not.

    arguments:
        module                (dict): The Ansible module
        alt_disk_update_name  (str): Name of the alternate disk.
        target_list           (list): List of the targets
    returns:
        list of targets which does not have specified alternate disk.
        if all targets have specified alternate disk
    """

    cmd = ['/usr/sbin/lspv', '|/usr/bin/grep', '-w', alt_disk_update_name, '|/usr/bin/grep', '-E', '"None"']

    target_miss = []
    for target in target_list:
        rc = nim_exec(module, target, cmd)[0]
        if rc != 0:
            target_miss .append(target)

    return target_miss


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

    lpp_source = params['lpp_source']
    alt_disk_update_name = params['alt_disk_update_name']
    targets = params['targets']

    async_update = 'no'
    if params['asynchronous']:
        async_update = 'yes'
        log_async = 'asynchronous'
    else:
        log_async = 'synchronous'

    module.log(f'NIM - { log_async } update operation on { targets } with { lpp_source } lpp_source')

    if (params['asynchronous'] and (lpp_source == 'latest_tl'
                                    or lpp_source == 'latest_sp'
                                    or lpp_source == 'next_tl'
                                    or lpp_source == 'next_sp')):
        module.log('NIM - WARNING: Force customization synchronously')
        async_update = 'no'

    target_list = expand_targets(params['targets'])
    if not target_list:
        results['msg'] = f'No matching target found for targets \'{ targets }\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    if alt_disk_update_name:
        unavail_targets = check_alt_disk(module, alt_disk_update_name, target_list)
    else:
        unavail_targets = []

    results['targets'] = list(target_list)
    module.debug(f'NIM - Target list: { target_list }')
    for target in results['targets']:
        if target in results['nim_node']['vios']:
            target_list.remove(target)
            msg = 'update operation is not supported on VIOS. Use power_aix.nim_updateios module instead.'
            results['meta'][target] = {'messages': [msg]}
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
            continue
        if target in unavail_targets:
            target_list.remove(target)
            msg = 'alt_disk_update_name disk (' + alt_disk_update_name + ') not present or assigned to another VG.'
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
            msg = f'Will remove as many interim fixes we can: {fixes}'
            results['meta']['messages'].append(msg)
            for fix in fixes:
                remove_fix(module, target, fix)

    if async_update == 'yes':   # async update
        if lpp_source not in results['nim_node']['lpp_source']:
            debug_lpp_src = results['nim_node']['lpp_source']
            results['msg'] = f'Cannot find lpp_source \'{ debug_lpp_src }\'.'
            module.log('NIM - Error: ' + results['msg'])
            module.fail_json(**results)

        msg_target_list = ','.join(target_list)
        msg = f'Asynchronous software customization for client(s) { msg_target_list } with resource { lpp_source }.'
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
                msg = f'Invalid oslevel got: \'{ cur_oslevel }\'.'
                results['meta'][target]['messages'].append(msg)
                module.log(f'NIM - WARNING: On { target } with msg: { msg } ')
                results['msg'] += f"{target} - {results['meta'][target]['messages']}"
                results['status'][target] = 'FAILURE'
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
                msg = f'Using lpp_source: { new_lpp_source }'
                results['meta']['messages'].append(msg)
                module.debug('NIM - ' + msg)
            else:
                if lpp_source not in results['nim_node']['lpp_source']:
                    msg_lpp_src = results['nim_node']['lpp_source']
                    results['msg'] = f'Cannot find lpp_source \'{ lpp_source }\' in \'{ msg_lpp_src }\'.'
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
                msg = f'Cannot get oslevel from lpp source name: { new_lpp_source }'
                results['meta'][target]['messages'].append(msg)
                module.log(f'NIM - WARNING: On { target} with msg: { msg } ')
                results['msg'] += f"{target} - {results['meta'][target]['messages']}"
                results['status'][target] = 'FAILURE'
                continue

            full_elts = '-'.join(oslevel_elts)
            if cur_oslevel_elts[0] != oslevel_elts[0]:
                msg = f'Has a different release number than { full_elts }, got { cur_oslevel }'
                results['meta'][target]['messages'].append(msg)
                module.log(f'NIM - WARNING: { target } with msg: { msg } ')
                results['msg'] += f"{target} - {results['meta'][target]['messages']}"
                results['status'][target] = 'FAILURE'
                continue
            if (cur_oslevel_elts[1] > oslevel_elts[1] or cur_oslevel_elts[1] == oslevel_elts[1] and cur_oslevel_elts[2] >= oslevel_elts[2]):
                msg = f'Already at same or higher level: {full_elts}, got: {cur_oslevel_elts}'
                results['meta'][target]['messages'].append(msg)
                module.log(f'NIM - { target} with msg: { msg } ')
                results['msg'] += f"{target} - {results['meta'][target]['messages']}"
                continue

            msg = f'Synchronous software customization from {cur_oslevel} to {full_elts}.'
            results['meta'][target]['messages'].append(msg)
            module.log(f'NIM - On {target} ' + msg)

            rc = perform_customization(module, new_lpp_source, target, False)
            results['msg'] += f"{target} - {results['meta'][target]['messages']}"
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

    targets = params['targets']
    module.log(f'NIM - maintenance operation on { targets }')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{ targets }\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    debug_targets = results['targets']
    module.debug(f'NIM - Target list: {debug_targets}')

    flag = '-c'  # initialized to commit flag

    for target in results['targets']:
        module.log(f'NIM - perform maintenance operation for client { target }')
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
            msg = f'maintenance operation failed on {target}.'
            results['meta']['messages'].append(msg)
            module.log('NIM - Error: ' + msg)
            results['status'][target] = 'FAILURE'
        else:
            msg = f'maintenance operation successfull on {target}.'
            results['meta']['messages'].append(msg)
            module.log('NIM - ' + msg)
            results['changed'] = True
            results['status'][target] = 'SUCCESS'

        module.log(f'cmd: { cmd }')
        module.log(f'rc: { rc }')
        module.log(f'stdout: { stdout }')
        module.log(f'stderr: { stderr }')


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

    device = params['device']
    module.log(f'NIM - master setup operation using { device } device')

    cmd = ['nim_master_setup', '-B',
           '-a', 'mk_resource=no',
           '-a', 'device=' + params['device']]

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: { cmd }')
    module.log(f'rc: { rc }')
    module.log(f'stdout: { stdout }')
    module.log(f'stderr: { stderr }')

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
            msg_targets = params['targets']
            results['msg'] = f'No matching target found for targets \'{ msg_targets }\'.'
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

    targets = params['targets']
    module.log(f'NIM - installation inventory comparison for { targets } clients')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{ targets }\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    module.debug(f'NIM - Target list: { targets }')

    cmd = ['niminv', '-o', 'invcmp',
           '-a', 'targets=' + ','.join(results['targets']),
           '-a', 'base=any']

    module.debug(f'NIM - Command:{ cmd }')

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = ' '.join(cmd)
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: { cmd }')
    module.log(f'rc: { rc }')
    module.log(f'stdout: { stdout }')
    module.log(f'stderr: { stderr }')

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

    async_script = ''
    if params['asynchronous']:
        async_script = 'yes'
        log_async = 'asynchronous'
    else:
        async_script = 'no'
        log_async = 'synchronous'

    params_targets = params['targets']
    params_scripts = params['script']
    module.log(f'NIM - {log_async} customize operation on {params_targets} with {params_scripts} script')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{params_targets}\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    res_targets = results['targets']
    module.debug(f'NIM - Target list: {res_targets}')

    cmd = ['nim', '-o', 'cust',
           '-a', 'script=' + params['script'],
           '-a', 'async=' + async_script]
    cmd += results['targets']
    cmd = ' '.join(cmd)

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

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
    params_targets = params['targets']
    params_lpp_source = params['lpp_source']

    module.log(f'NIM - allocate operation on {params_targets} for {params_lpp_source} lpp source')

    alloc_targets = expand_targets(params['targets'])

    if not alloc_targets:
        results['msg'] = f'No matching target found for targets \'{params_targets}\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    already_allocated = check_if_allocated(module, params_lpp_source, params_targets)

    if len(already_allocated):
        results['msg'] += f"Resource is already allocated to: {already_allocated}."

    for target in already_allocated:
        alloc_targets.remove(target)

    if len(alloc_targets) == 0:
        results['msg'] += " No need to allocate again."
        module.exit_json(**results)

    res_targets = alloc_targets
    module.debug(f'NIM - Target list: {res_targets}')

    cmd = ['nim', '-o', 'allocate',
           '-a', 'lpp_source=' + params['lpp_source']]
    cmd += alloc_targets

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

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
    params_targets = check_if_allocated(module, params['lpp_source'], params['targets'])

    if not len(params_targets):
        results['msg'] += "Resource is not allocated to the provided targets, no need to deallocate."
        module.exit_json(**results)

    params_lpp_source = params['lpp_source']
    module.log(f'NIM - deallocate operation on {params_targets} for {params_lpp_source} lpp source')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{params_targets}\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    res_targets = results['targets']
    module.debug(f'NIM - Target list: {res_targets}')

    cmd = ['nim', '-o', 'deallocate',
           '-a', 'lpp_source=' + params['lpp_source']]
    cmd += params_targets

    cmd = ' '.join(cmd)
    module.debug(f'NIM - Command:{cmd}')

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

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

    params_targets = params['targets']
    params_group = params['group']
    module.log(f'NIM - bos_inst operation on {params_targets} using {params_group} resource group')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{params_targets}\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    res_targets = results['targets']
    module.debug(f'NIM - Target list: {res_targets}')

    cmd = ['nim', '-o', 'bos_inst',
           '-a', 'source=mksysb',
           '-a', 'group=' + params['group']]
    if params['script'] and params['script'].strip():
        cmd += ['-a', 'script=' + params['script']]
    cmd += ['-a', 'boot_client=' + ('yes' if params['boot_client'] else 'no')]
    cmd += results['targets']
    cmd = ' '.join(cmd)

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

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

    params_resource = params['resource']
    params_location = params['location']
    module.log(f'NIM - define script operation for {params_resource} resource with location {params_location}')

    # Check if the script already exists
    scripts = get_nim_type_info(module, 'script')

    if params['resource'] in scripts:
        if params['location'] == scripts[params['resource']]['location'] and scripts[params['resource']]['server'] == 'master':
            msg = f'script resource \'{params_resource}\' already exists.'
            results['meta']['messages'].append(msg)
            module.log('NIM - ' + msg)
            return

    # Best effort, try to define the resource
    cmd = ['nim', '-o', 'define', '-t', 'script',
           '-a', 'location=' + params['location'],
           '-a', 'server=master',
           params['resource']]

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

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

    params_resource = params['resource']
    module.log(f'NIM - remove operation on {params_resource} resource')

    cmd = ['nim', '-o', 'remove', params['resource']]

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

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

    params_targets = params['targets']
    params_force = params['force']
    module.log(f'NIM - reset operation on {params_targets} resource (force: {params_force})')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{params_targets}\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    res_targets = results['targets']
    module.debug(f'NIM - Target list: {res_targets}')

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

    discarded_targets = ','.join(targets_discarded)
    if targets_discarded:
        msg = f'The following targets are already ready for a NIM operation: {discarded_targets}'
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

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

    reset_targets = ','.join(targets_to_reset)
    if rc != 0:
        results['msg'] = f'Failed to reset current NIM state on {reset_targets}.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    msg = f'Successfully reset targets: {reset_targets}.'
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

    params_targets = params['targets']
    module.log(f'NIM - reboot operation on {params_targets}')

    results['targets'] = expand_targets(params['targets'])
    if not results['targets']:
        results['msg'] = f'No matching target found for targets \'{params_targets}\'.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    res_targets = results['targets']
    module.debug(f'NIM - Target list: {res_targets}')

    if 'master' in results['targets']:
        results['targets'].remove('master')
        msg = 'master can not be rebooted, master is discarded from the target list.'
        results['meta']['messages'].append(msg)
        module.log('NIM - ' + msg)
        if not results['targets']:
            return

    cmd = ['nim', '-o', 'reboot']
    cmd += results['targets']

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

    joined_targets = ','.join(results['targets'])
    if rc != 0:
        results['msg'] = f'Failed to reboot NIM clients: {joined_targets}.'
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)

    results['changed'] = True


def nim_show(module, params):
    """
    Query information on existing NIM objects in the NIM server.

    arguments:
        module  (dict): The Ansible module
        params  (dict): The module parameters for the command.
    note:
        Exits with fail_json in case of error
    """

    module.log('NIM - show operation')
    cmd = ['lsnim', '-l', '-Z']
    if params['object_type'] != 'all':
        cmd += ['-t', params['object_type']]
    results['changed'] = False

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = "see meta.query"
    results['stderr'] = stderr

    module.log(f'cmd: {cmd}')
    module.log(f'rc: {rc}')
    module.log(f'stdout: {stdout}')
    module.log(f'stderr: {stderr}')

    params_obj_type = params['object_type']

    # check if any info was fetched
    if not stdout and rc == 0:
        results['meta']['messages'] = f"There are no defined NIM objects of type '{params_obj_type}'"
        return

    if rc != 0:
        results['meta']['messages'] = f"Failed to fetch '{params_obj_type}' NIM objects types"
        module.log('NIM - Error: ' + results['msg'])
        module.fail_json(**results)
    else:
        # parse output
        info = {}
        labels, values = stdout.strip().split('\n')
        labels = labels[1:]  # remote token '#' at the begining of the string
        labels = labels.split(':')
        values = values.split(':')
        for label, value in zip(labels, values):
            if label == "name":
                info[value] = {}
                entry_name = value
            else:
                info[entry_name][label] = value
        results['meta']['query'] = info


def check_machine_details_validity(module, targets):
    """
    Checking the machine details format.

    arguments:
        module  (dict): The Ansible module
        targets  (list): The targets credential details.
    note:
        Exits with fail_json in case of error
    """

    failed_targets = []
    successful_details = []

    for target in targets:
        target_details = target.split('-')
        if len(target_details) != 3:
            failed = 1
            failed_targets.append(target_details[0])
        else:
            successful_details.append[target_details]

    if failed:
        msg = f"Following machine details are not in the proper format {failed_targets}"
        msg += "Please provide the details in <full.host.name>-<login id>-<password> format."
        results['msg'] = msg
        module.fail_json(**results)

    return successful_details


def confirm_netrc_file(module):
    """
    Confirms the netrc file

    arguments:
        module  (dict): The Ansible module
    """

    cmd = 'ls /.netrc'
    rc, stdout, stderr = module.run_command(cmd)

    if rc:
        module.run_command('touch /.netrc')
        module.run_command('chmod 600 /.netrc')


def register_client(module, targets):
    """
    register new clients to the NIM master.

    arguments:
        module  (dict): The Ansible module
        targets  (list): The targets credential details.
    note:
        Exits with fail_json in case of error
    """

    target_details = check_machine_details_validity(module, targets)
    confirm_netrc_file(module)

    for target_detail in target_details:
        target_host_name = target_detail[0]
        target_login_id = target_detail[1]
        target_password = target_detail[2]
        machine_name = target_host_name.split('.')[0]
        cmd_body = f'machine {machine_name} login {target_login_id} password {target_password}'
        cmd = f'echo {cmd_body} >> /.netrc'
        module.run_command(cmd)
        cmd_body = f'machine {target_host_name} login {target_login_id} password {target_password}'
        cmd = f'echo {cmd_body} >> /.netrc'
        module.run_command(cmd)
        cmd = "netstat -rn"
        rc, stdout, stderr = module.run_command(cmd)
        gateway_line = stdout.split("\n")[4].split(' ')
        for item in gateway_line:
            if item != "" and item != "default":
                client_gateway = item
                break

        cmd = "host " + machine_name
        rc, stdout, stderr = module.run_command(cmd)

        # check if machine is already defined in the system
        cmd = "lsnim"
        rc, stdout, stderr = module.run_command(cmd)
        resources = stdout.split('\n')
        flag = 0
        for resource_line in resources:
            resource = resource_line.split(" ")[0]
            if resource == machine_name:
                msg = f'Machine {machine_name} is already defined'
                results['msg'] += msg
                flag = 1
                break

        if flag == 0:
            cmd = f"nim -o define -t standalone -a platform=chrp -a if1=\"find_net {machine_name} 0\" "
            cmd += f"cable_type1=bnc -a net_definition=\"ent 255.255.255.0 {client_gateway}\" -a netboot_kernel=64 "
            cmd += machine_name
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                msg = f"Client definition failed for machine {machine_name}"
                results['msg'] += msg
                module.fail_json(**results)
            else:
                rc, stdout, stderr = module.run_command("rexec $CLIENT_HN \"rm /etc/niminfo\"")
                if rc != 0:
                    msg = f'Failed to remove niminfo file from {machine_name}'
                    results['msg'] += msg
                    module.fail_json(**results)
                rc_hn, stdout_hn, stderr_hn = module.run_command("hostname")
                if rc_hn != 0:
                    msg = 'Failed to get hostname of NIM master.'
                    results['msg'] += msg
                    module.fail_json(**results)
                cmd = f'rexec {target_host_name} \" niminit -a name={machine_name} -a master={stdout_hn}\"'
                rc, stdout, stderr = module.run_command(cmd)
                if rc != 0:
                    msg = f"Client definition failed for machine {machine_name}"
                    results['msg'] += msg
                    module.fail_json(**results)

    msg += "Client setup is completed successfully"
    results['msg'] += msg
    module.exit_json(**results)


def main():
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['update', 'master_setup', 'check', 'compare',
                                 'script', 'allocate', 'deallocate',
                                 'bos_inst', 'define_script', 'remove',
                                 'reset', 'reboot', 'maintenance', 'show', 'register_client', 'install_fileset']),
            lpp_source=dict(type='str'),
            targets=dict(type='list', elements='str'),
            new_targets=dict(type='list', elements='str'),  # The elements format is <machine name>-<login id>-<password>
            asynchronous=dict(type='bool', default=False),
            device=dict(type='str'),
            installp_bundle=dict(type='str'),
            script=dict(type='str'),
            resource=dict(type='str'),
            location=dict(type='str'),
            group=dict(type='str'),
            force=dict(type='bool', default=False),
            boot_client=dict(type='bool', default=True),
            object_type=dict(type='str', default='all'),
            alt_disk_update_name=dict(type='str'),
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
            ['action', 'maintenance', ['targets']],
            ['action', 'install_fileset', ['targets', 'lpp_source', 'installp_bundle']],
            ['action', 'register_client', ['new_targets']]
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
        #  query:
        #    nim_obj_entry: {
        #      'Cstate': 'ready for a NIM operation',
        #      'Cstate_result': 'success',
        #      'Mstate': 'currently running',
        #      'cable_type': 'N/A',
        #      ...
        #    }
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
    boot_client = module.params['boot_client']
    object_type = module.params['object_type']
    alt_disk_update_name = module.params['alt_disk_update_name']
    installp_bundle = module.params['installp_bundle']

    params = {}

    module.debug(f'*** START NIM operation {action} ***')

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    # skip build nim node for actions: master_setup or show
    if action != 'master_setup' and action != 'show' and action != 'register_client':
        # Build nim node info
        build_nim_node(module)

    if action == 'register_client':
        targets = module.params['new_targets']
        register_client(module, targets)

    if action == 'update':
        params['targets'] = targets
        params['lpp_source'] = lpp_source
        params['asynchronous'] = asynchronous
        params['force'] = force
        params['alt_disk_update_name'] = alt_disk_update_name
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
        params['boot_client'] = boot_client
        nim_bos_inst(module, params)

    elif action == 'define_script':
        params['resource'] = resource
        params['location'] = location
        nim_define_script(module, params)

    elif action == 'install_fileset':
        params['targets'] = targets
        params['lpp_source'] = lpp_source
        params['installp_bundle'] = installp_bundle
        install_filesets(module, params)

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

    elif action == 'show':
        params['object_type'] = object_type
        nim_show(module, params)

    # Exit
    if results['status']:
        target_errored = [key for key, val in results['status'].items() if 'FAILURE' in val]
        if len(target_errored):
            results['msg'] += f' NIM {action} operation failed for {target_errored}. See status and meta for details.'
            module.log(results['msg'])
            module.fail_json(**results)

    results['msg'] += f' NIM {action} operation successful. See status and meta for details.'
    module.log(results['msg'])
    module.exit_json(**results)


if __name__ == '__main__':
    main()
