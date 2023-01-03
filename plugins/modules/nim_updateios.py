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
module: nim_updateios
short_description: Use NIM to update a single or a pair of Virtual I/O Servers.
description:
- Uses the Network Installation Management (NIM) to perform updates and customization to Virtual I/O
  Server (VIOS) targets tuple.
- A tuple can be one VIOS or a pair of VIOSes to update together.
- Checks status of previous operation if provided before running operation on the tuple.
- When a cluster is configured, the VIOSes of a tuple must be on the same cluster and the node
  states must be OK.
- When updating VIOSes pair, it checks the cluster state, stop it before installing the VIOS, and
  restart it after installation. Then, it starts updating the second VIOS.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorizations: B(aix.system.install,aix.system.nim.config.server)'
options:
  action:
    description:
    - Specifies the action to perform.
    - C(install) installs new and supported filesets.
    - C(commit) commits all uncommitted updates.
    - C(cleanup) removes all incomplete pieces of the previous installation.
    - C(remove) removes the listed filesets from the system in C(filesets) or C(installp_bundle).
    type: str
    choices: [ install, commit, cleanup, remove ]
    required: true
  targets:
    description:
    - Specifies the list of VIOSes NIM targets tuple to update.
    - You can specify a list of a VIOS to update alone, or two VIOSes to update as a couple.
    type: list
    elements: str
    required: true
  filesets:
    description:
    - Specifies a list of file sets to remove from the targets.
    - Can be used with I(action=remove).
    type: str
  installp_bundle:
    description:
    - Specifies an I(installp_bundle) resource that lists filesets to remove on the targets.
    - Can be used with I(action=remove).
    type: str
  lpp_source:
    description:
    - Specifies the NIM I(lpp_source) resource that will provide the installation images for the
      operation.
    type: str
  accept_licenses:
    description:
    - Specifies whether the software licenses should be automatically accepted during the
      installation.
    type: bool
    default: True
  manage_cluster:
    description:
    - Specifies whether the cluster should be check and stop before updating the vios and restarted
      after the update.
    type: bool
    default: False
  preview:
    description:
    - Specifies to run the operations in preview operation. No action is actually performed.
    type: bool
    default: True
  time_limit:
    description:
    - Before starting the action on a VIOS tuple, the actual date is compared to this parameter
      value; if it is greater then the task is stopped.
    - The format is C(mm/dd/yyyy hh:mm).
    - The resulting status for tuples in this case will be I(SKIPPED-TIMEOUT).
    type: str
  vios_status:
    description:
    - Specifies the result of a previous operation.
    - If set then the I(vios_status) of a target tuple must contain C(SUCCESS) to attempt update.
    - If no I(vios_status) value is found for a tuple, then returned I(status) for this tuple is set
      to C(SKIPPED-NO-PREV-STATUS).
    type: dict
  nim_node:
    description:
    - Allows to pass along NIM node info from a task to another so that it discovers NIM info only
      one time for all tasks.
    type: dict
notes:
  - You can refer to the IBM documentation for additional information on the NIM concept and command
    at U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/install/nim_concepts.html),
    U(https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/install/nim_op_updateios.html).
'''

EXAMPLES = r'''
- name: Preview updateios on a pair of VIOSes
  nim_updateios:
    targets: 'nimvios01, nimvios02'
    action: install
    lpp_source: 723lpp_res
    preview: yes
- name: Update VIOSes as a pair and a VIOS alone discarding cluster
  nim_updateios:
    targets:
    - nimvios01,nimvios02
    - nimvios03
    action: install
    lpp_source: 723lpp_res
    time_limit: '07/21/2020 17:02'
    manage_cluster: no
    preview: no
- name: Remove a fileset of a VIOS
  nim_updateios:
    targets: 'nimvios01'
    action: remove
    filesets: openssh.base.server
    preview: yes
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'NIM updateios operation completed successfully'
targets:
    description: List of VIOSes actually targeted for the operation.
    returned: always
    type: list
    elements: str
    sample: [vios1, 'vios2, vios3', ...]
stdout:
    description: The standard output.
    returned: always
    type: str
stderr:
    description: The standard error.
    returned: always
    type: str
status:
    description:
    - Status of the execution on each target <tuple>.
    - If the operation status is not avalaible, the I(vios_status) passed in parameter is returned.
    returned: always
    type: dict
    contains:
        <tuple>:
            description:
            - Status of the execution on the <tuple>.
            - The <tuple> elements are sorted to form the key of the dictionary.
            - I(SKIPPED-NO-PREV-STATUS) when no I(vios_status) value is found for the tuple.
            - Previous I(vios_status) when the tuple status does not contains SUCCESS.
            - I(SKIPPED-TIMEOUT) when the I(time_limit) is reached before updating the 1st VIOS of the tuple.
            - I(FAILURE-CLUSTER) when cluster checks or operation failed.
            - I(FAILURE-UPDT1) when update of first VIOS of the tuple failed.
            - I(FAILURE-UPDT2) when update of second VIOS of the tuple failed.
            returned: when tuple are actually a NIM client and reachable with c_rsh.
            type: str
            sample: 'SUCCESS-UPDT'
    sample:
        "status": {
            "vios1-vios2": "SUCCESS-UPDT",
            "vios3": "SUCCESS-ALTDC",
            "vios4-vios5": "FAILURE-CLUSTER",
            "vios6-vios7": "FAILURE-UPDT1"
        }
nim_node:
    description: NIM node info. It can contains more information if passed as option I(nim_node).
    returned: always
    type: dict
    contains:
        vios:
            description: List of VIOS NIM resources.
            returned: always
            type: dict
    sample:
        "nim_node": {
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
                    "hostname": "vios1.aus.stglabs.ibm.com",
                    "cluster": {
                        "vios1": {
                            "repos_state": "",
                            "state": "DOWN"
                        },
                        "vios2": {
                            "repos_state": "OK",
                            "state": "OK"
                        },
                        "name": "mycluster",
                        "nodes": [
                            "vios1",
                            "vios2"
                        ],
                        "state": "DEGRADED"
                    },
                }
            }
        }
meta:
    description: Detailed information on the module execution.
    returned: always
    type: dict
    contains:
        messages:
            description: Details on errors/warnings not related to a specific tuple.
            returned: always
            type: list
            elements: str
            sample: see below
        <tuple>:
            description: Detailed information on the execution on the target tuple.
            returned: when target is actually a NIM client
            type: dict
            contains:
                messages:
                    description: Details on errors/warnings.
                    returned: always
                    type: list
                    elements: str
                <vios>:
                    description: updateios information for a specific vios.
                    returned: when target is actually a NIM client.
                    type: dict
                    contains:
                        cmd:
                            description: Command executed.
                            returned: If the command was run.
                            type: str
                        stdout:
                            description: Standard output of the command.
                            returned: If the command was run.
                            type: str
                        stderr:
                            description: Standard error of the command.
                            returned: If the command was run.
                            type: str
'''

import re
import time

from ansible.module_utils.basic import AnsibleModule

module = None
results = None


def param_one_of(one_of_list, required=True, exclusive=True):
    """
    Check at parameter of one_of_list is defined in module.params dictionary.

    arguments:
        one_of_list (list) list of parameter to check
        required    (bool) at least one parameter has to be defined.
        exclusive   (bool) only one parameter can be defined.
    note:
        Ansible might have this embedded in some version: require_if 4th parameter.
        Exits with fail_json in case of error
    """

    count = 0
    for param in one_of_list:
        if module.params[param] is not None and module.params[param]:
            count += 1
            break
    if count == 0 and required:
        results['msg'] = 'Missing parameter: action is {0} but one of the following is missing: '.format(module.params['action'])
        results['msg'] += ','.join(one_of_list)
        module.fail_json(**results)
    if count > 1 and exclusive:
        results['msg'] = 'Invalid parameter: action is {0} supports only one of the following: '.format(module.params['action'])
        results['msg'] += ','.join(one_of_list)
        module.fail_json(**results)


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    arguments:
        module      (dict): The Ansible module
        node        (dict): nim client to execute the command on to
        command     (list): command to execute
    return:
        rc      (int) return code of the command
        stdout  (str) stdout of the command
        stderr  (str) stderr of the command
    """

    rcmd = '( LC_ALL=C {0} ); echo rc=$?'.format(' '.join(command))
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return (rc, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        rc = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug('nim_exec command \'{0}\': rc:{1}, output:{2}, stderr:{3}'.format(' '.join(cmd), rc, stdout, stderr))

    return (rc, stdout, stderr)


def refresh_nim_node(module, type):
    """
    Get nim client information of provided type and update nim_node dictionary.

    arguments:
        module  (dict): The Ansible module
        type     (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        none
    """

    if module.params['nim_node']:
        results['nim_node'] = module.params['nim_node']

    nim_info = get_nim_type_info(module, type)

    if type not in results['nim_node']:
        results['nim_node'].update({type: nim_info})
    else:
        for elem in nim_info.keys():
            if elem in results['nim_node']:
                results['nim_node'][type][elem].update(nim_info[elem])
            else:
                results['nim_node'][type][elem] = nim_info[elem]
    module.debug("results['nim_node'][{0}]: {1}".format(type, results['nim_node'][type]))


def get_nim_type_info(module, type):
    """
    Build the hash of nim client of type=lpar_type defined on the
    nim master and their associated key = value information.

    arguments:
        module  (dict): The Ansible module
        type     (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        info_hash   (dict): information from the nim clients
    """

    cmd = ['lsnim', '-t', type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Cannot get NIM Client information. Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.log(msg)
        results['msg'] = msg
        results['stdout'] = stdout
        results['stderr'] = stderr
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


def check_lpp_source(module, lpp_source):
    """
    Check to make sure lpp_source exists

    arguments:
        module      (dict): The Ansible module
        lpp_source   (str): The NIM lpp_source resource name parameter
    note:
        Exits with fail_json in case of error or if lpp_source does not exist
    return
        True if the lpp_source location exists
    """

    # find location of lpp_source
    cmd = ['lsnim', '-a', 'location', lpp_source]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Cannot find location of lpp_source {0}, lsnim returns: {1}'.format(lpp_source, stderr)
        module.log(msg)
        results['msg'] = msg
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)
    location = stdout.split()[3]

    # check to make sure path exists
    cmd = ['/bin/find', location]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Cannot find location of lpp_source {0}: {1}'.format(lpp_source, stderr)
        module.log(msg)
        results['msg'] = msg
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)

    return True


def check_vios_targets(module, targets):
    """
    Check the list of VIOS targets.
    Check that each target can be reached.

    A target name can be of the following form:
        vios1,vios2 or vios3

    arguments:
        module  (dict): the Ansible module
        targets (list): list of tuple of NIM name of vios machine
    return:
        res_list    (list): The list of the existing vios tuple matching the target list
    """

    vios_list = []
    res_list = []

    # Build targets list
    for elems in targets:
        module.debug('Checking elems: {0}'.format(elems))

        tuple_elts = list(set(elems.replace(" ", "").replace("[", "").replace("]", "").replace("(", "").replace(")", "").split(',')))
        tuple_len = len(tuple_elts)
        module.debug('Checking tuple: {0}'.format(tuple_elts))

        if tuple_len == 0:
            continue

        if tuple_len > 2:
            msg = 'Malformed VIOS targets \'{0}\'. Tuple {1} should be a 1 or 2 elements.'.format(targets, elems)
            module.log(msg)
            results['msg'] = msg
            module.exit_json(**results)

        error = False
        for elem in tuple_elts:
            if len(elem) == 0:
                msg = 'Malformed VIOS targets tuple {0}: empty string.'.format(elems)
                module.log(msg)
                results['msg'] = msg
                module.exit_json(**results)

            # check vios not already exists in the target list
            if elem in vios_list:
                msg = 'Malformed VIOS targets \'{0}\': Duplicated VIOS: {1}'.format(targets, elem)
                module.log(msg)
                results['msg'] = msg
                error = True
                continue

            # check vios is knowed by the NIM master - if not ignore it
            if elem not in results['nim_node']['vios']:
                msg = "VIOS {0} is not client of the NIM master, tuple {1} will be ignored".format(elem, elems)
                module.log(msg)
                results['meta']['messages'].append(msg)
                error = True
                continue

            # Get VIOS interface info in case we need to connect using c_rsh
            if 'if1' not in results['nim_node']['vios'][elem]:
                msg = "VIOS {0} has no interface set, check its configuration in NIM, tuple {1} will be ignored".format(elem, elems)
                module.log(msg)
                results['meta']['messages'].append(msg)
                error = True
                continue
            fields = results['nim_node']['vios'][elem]['if1'].split(' ')
            if len(fields) < 2:
                msg = "VIOS {0} has no hostname set, check its configuration in NIM, tuple {1} will be ignored".format(elem, elems)
                module.log(msg)
                results['meta']['messages'].append(msg)
                error = True
                continue
            results['nim_node']['vios'][elem]['hostname'] = fields[1]

            # check vios connectivity
            rc, stdout, stderr = nim_exec(module, results['nim_node']['vios'][elem]['hostname'], ['true'])
            if rc != 0:
                msg = 'skipping {0}: cannot reach {1} with c_rsh, rc:{2}, stderr:{3}, stdout:{4}'.format(elems, elem, rc, stderr, stdout)
                module.log('[WARNING] ' + msg)
                results['meta']['messages'].append(msg)
                error = True
                continue

        if not error:
            vios_list.extend(tuple_elts)
            res_list.append(tuple_elts)

    return res_list


def tuple_str(tuple_list):
    """
    Build a string with tuple elements separated by '-'.
    arguments:
        tuple_list  (list): The list of element(s)
    return
        tuple_str   (str): string of
    """
    tuple_str = ''
    tuple_list.sort()
    for elem in tuple_list:
        if tuple_str:
            tuple_str += '-{0}'.format(elem)
        else:
            tuple_str = '{0}'.format(elem)
    return tuple_str


def check_vios_cluster_status(module, target_tuple):
    """
    Check the cluster status of the VIOS tuple.
    Update IOS can only be performed when both VIOSes in the tuple
    refer to the same cluster and the node states is OK.
    For a single VIOS, when the cluster status is inactive.

    arguments:
        module          (dict): The Ansible module
        target_tuple    (list): The tuple of VIOS(es) to check
    return:
        True if the cluster status is valid for update.
        False otherwise.
    """

    vios_key = tuple_str(target_tuple)
    tuple_len = len(target_tuple)

    for vios in target_tuple:
        results['nim_node']['vios'][vios]['cluster'] = {}

    # get the cluster status
    for vios in target_tuple:
        cmd = ['/usr/ios/cli/ioscli cluster -list && /usr/ios/cli/ioscli cluster -status -fmt :']
        rc, stdout, stderr = nim_exec(module, results['nim_node']['vios'][vios]['hostname'], cmd)
        if rc != 0:
            # Check a cluster is configured
            stdout = stdout.rstrip()
            if stdout.find('Cluster does not exist') != -1:
                msg = 'There is no cluster on vios {0}'.format(vios)
                module.log(msg)
                continue
            # the command failed and stdout contains command's stderr
            msg = 'Cannot get cluster status on {0}: command \'{1}\', rc:{2}, stderr:{3}'.format(vios, ' '.join(cmd), rc, stdout)
            module.log('[WARNING] ' + msg)
            results['meta']['messages'].append(msg)
            results['meta'][vios_key][vios]['stdout'] = stdout
            results['meta'][vios_key][vios]['stderr'] = stderr
            return False

        # stdout is like:
        # CLUSTER_NAME:    porthos_cl1
        # CLUSTER_ID:      adf01bd81de611ea8012be6aa4a49d02
        #
        # porthos_cl1:OK:porthos-vios1:8286-42A02103341V:2:OK:OK
        # porthos_cl1:OK:porthos-vios2:8286-42A02103341V:3:OK:OK
        #
        # with the following:
        # Cluster Name:Cluster State:Node Name:Node MTM:Node Partition Num:Node State:Node Repos State
        # Let's remove the first 3 lines
        lines = stdout.rstrip().splitlines()[3:]
        for line in lines:
            line = line.strip()
            if not line:
                continue
            fields = line.split(':')
            if len(fields) != 7:
                msg = 'Expecting 7 fields for cluster status, got {0}.'.format(len(line))
                module.log('[WARNING] ' + msg)
                results['meta']['messages'].append(msg)
                continue
            if 'name' not in results['nim_node']['vios'][vios]['cluster']:
                results['nim_node']['vios'][vios]['cluster']['name'] = fields[0]
                results['nim_node']['vios'][vios]['cluster']['state'] = fields[1]
                results['nim_node']['vios'][vios]['cluster']['nodes'] = []
            results['nim_node']['vios'][vios]['cluster']['nodes'].append(fields[2])
            results['nim_node']['vios'][vios]['cluster'][fields[2]] = {}
            results['nim_node']['vios'][vios]['cluster'][fields[2]]['state'] = fields[5]
            results['nim_node']['vios'][vios]['cluster'][fields[2]]['repos_state'] = fields[6]

    # TODO Improvement: cluster_name is a short hostname. But hostname here after is from 'if1' definition and can
    # be an IP address. Moreover tuple is NIM client name can differ from hostname. We could get the actual hostname.

    # check cluster state on nodes
    vios = target_tuple[0]
    cluster = results['nim_node']['vios'][vios]['cluster']
    if tuple_len == 1:
        module.debug('cluster: {0}'.format(cluster))
        if not cluster or len(cluster['nodes']) == 1 and cluster[cluster['nodes'][0]]['state'] == 'DOWN':
            return True
        if len(cluster['nodes']) != 1:
            msg = 'VIOS {0} is member of cluster {1}: {2}.'.format(vios, cluster['name'], cluster['nodes'])
            module.log(msg)
            results['meta'][vios_key]['messages'].append(msg)
        else:
            msg = 'Cluster {0} node {1} status is: {2}, need to be stopped.'\
                  .format(cluster['name'], cluster['nodes'][0], cluster[cluster['nodes'][0]]['state'])
            module.log(msg)
            results['meta'][vios_key]['messages'].append(msg)
            return False

    vios2 = target_tuple[1]
    cluster2 = results['nim_node']['vios'][vios2]['cluster']
    if not cluster and not cluster2:
        msg = 'No cluster defined on both vios of the tuple {0}.'.format(target_tuple)
        module.log(msg)
        return True
    if cluster and not cluster2 or not cluster and cluster2:
        msg = 'No cluster defined on one vios of the vios: {0}.'.format(target_tuple)
        module.log(msg)
        results['meta'][vios_key]['messages'].append(msg)
        return False
    if cluster['name'] != cluster2['name']:
        msg = 'Cluster must be the same on both vios: {0}: {1}, {2}: {3}.'.format(vios, cluster['name'], vios2, cluster2['name'])
        module.log(msg)
        results['meta'][vios_key]['messages'].append(msg)
        return False

    for vios in target_tuple:
        cluster = results['nim_node']['vios'][vios]['cluster']
        module.debug('cluster on vios {0}: {1}'.format(vios, cluster))
        if cluster['state'] != 'OK':
            msg = 'Cluster {0} state on vios {1} must be OK, got: {2}.'.format(cluster['name'], vios, cluster['state'])
            module.log(msg)
            results['meta'][vios_key]['messages'].append(msg)
            return False
        found = False
        for node in cluster['nodes']:
            if vios in node:
                found = True
                if cluster[node]['state'] != 'OK':
                    msg = 'Cluster {0} node {1} state must be OK, got: {2}'.format(cluster['name'], node, cluster['nodes'][node]['state'])
                    module.log(msg)
                    results['meta'][vios_key]['messages'].append(msg)
                    return False
        if not found:
            msg = 'VIOS {0} not found in cluster {1} nodes: {2}'.format(vios, cluster['name'], cluster['nodes'])
            module.log(msg)
            results['meta'][vios_key]['messages'].append(msg)
            return False

    return True


def cluster_stop_start(module, target_tuple, vios_key, vios, action):
    """
    Stop/start the cluster for a VIOS

    arguments:
        module         (dict): The Ansible module
        target_tuple    (str): list of existing machines
        vios_key    (str): list of existing machines
        vios           (dict): nim info of all clients
    return:
        True if operation succeeded
        False otherwise
    """

    node = vios
    if action == 'start':
        # if action is start, find the first node running cluster
        for cur_node in target_tuple:
            if results['nim_node']['vios'][vios]['cluster'][cur_node]['state'] == "OK":
                node = cur_node
                break

    module.log('{0}-ing cluster {1} for node {2} from {3}'.format(action, results['nim_node']['vios'][vios]['cluster']['name'], vios, node))
    cmd = ['/usr/sbin/clctrl -{0} -n {1} -m {2}'.format(action, results['nim_node']['vios'][vios]['cluster']['name'], vios)]
    rc, stdout, stderr = nim_exec(module, results['nim_node']['vios'][node]['hostname'], cmd)
    if rc != 0:
        msg = 'Failed to {0} cluster {1} on {2}: {3}'\
              .format(action, results['nim_node']['vios'][vios]['cluster']['name'], node, stdout)
        results['meta'][vios_key]['messages'].append(msg)
        module.log(msg)
        return False

    # update the cluster status
    if action == 'stop':
        results['nim_node']['vios'][vios]['cluster'][vios]['state'] = 'DOWN'
    else:
        results['nim_node']['vios'][vios]['cluster'][vios]['state'] = 'OK'

    msg = '{0} cluster {1} on {2} succeeded'\
          .format(action, results['nim_node']['vios'][vios]['cluster']['name'], vios)
    module.log(msg)
    results['meta'][vios_key]['messages'].append(msg)
    return True


def get_updateios_cmd(module):
    """
    Build the updateios command based of module.params.

    arguments:
        module  (dict): The Ansible module
    return:
        cmd      (list): command parameters
    """

    cmd = ['nim', '-o', 'updateios']
    cmd += ['-a', 'updateios_flags=-{0}'.format(module.params['action'])]

    if module.params['action'] == 'remove':
        if module.params['filesets']:
            cmd += ['-a', 'filesets={0}'.format(module.params['filesets'])]
        if module.params['installp_bundle']:
            cmd += ['-a', 'installp_bundle={0}'.format(module.params['installp_bundle'])]

    if module.params['lpp_source']:
        if check_lpp_source(module, module.params['lpp_source']):
            cmd += ['-a', 'lpp_source={0}'.format(module.params['lpp_source'])]

    cmd += ['-a', 'accept_licenses=yes' if module.params['accept_licenses'] else 'accept_licenses=no']
    cmd += ['-a', 'preview=yes' if module.params['preview'] else 'preview=no']

    return cmd


def nim_updateios(module, targets_list, vios_status, time_limit):
    """
    Execute the updateios command
    For each VIOS tuple,
    - retrieve the previous status if any (looking for SUCCESS-HC and SUCCESS-UPDT)
    - for each VIOS of the tuple, check the cluster name and node status
    - stop the cluster if necessary
    - perform the updateios operation
    - wait for the copy to finish
    - start the cluster if necessary

    arguments:
        module          (dict): The Ansible module
        targets_list    (list): Target tuple list of VIOS
        vios_status     (dict): provided previous status for each tuple
        time_limit       (str): Date and time to perform tuple update
    note:
        Set the update status in results['status'][vios_key].
    return:
        none
    """

    # build the updateios command from the playbook parameters
    updateios_cmd = get_updateios_cmd(module)

    got_cluster_status = False
    for target_tuple in targets_list:
        module.debug('Processing target_tuple: {0}'.format(target_tuple))

        tuple_len = len(target_tuple)
        vios_key = tuple_str(target_tuple)

        # if previous status (health check) is known, check the vios tuple has passed
        if vios_status is not None:
            if vios_key not in vios_status:
                msg = '{0} VIOSes skipped (no previous status found)'.format(vios_key)
                module.log('[WARNING] ' + msg)
                results['meta'][vios_key]['messages'].append(msg)
                results['status'][vios_key] = "SKIPPED-NO-PREV-STATUS"
                continue

            if 'SUCCESS' not in vios_status[vios_key]:
                msg = '{0} tuple skipped (vios_status: {1})'.format(vios_key, vios_status[vios_key])
                module.log('[WARNING] ' + msg)
                results['status'][vios_key] = vios_status[vios_key]
                results['meta'][vios_key]['messages'].append(msg)
                results['status'][vios_key] = vios_status[vios_key]
                continue

        # check if there is time to handle this tuple
        if time_limit is not None and time.localtime(time.time()) >= time_limit:
            time_limit_str = time.strftime("%m/%d/%Y %H:%M", time_limit)
            msg = 'Time limit {0} reached, no further operation'.format(time_limit_str)
            module.log('[WARNING] ' + msg)
            results['meta'][vios_key]['messages'].append(msg)
            results['status'][vios_key] = "SKIPPED-TIMEOUT"
            return

        if module.params['action'] in ['install', 'cleanup'] and module.params['manage_cluster'] and not got_cluster_status:
            # check if cluster is defined for this VIOSes tuple.
            cluster_ok = check_vios_cluster_status(module, target_tuple)
            if not cluster_ok:
                msg = "{0} VIOSes skipped (bad cluster status)".format(vios_key)
                module.log('[WARNING] ' + msg)
                results['meta'][vios_key]['messages'].append(msg)
                msg = 'Update operation can only be done when both VIOSes belong to the'\
                      ' same cluster and their node state is OK, or for a single VIOS,'\
                      ' when the cluster status is inactive.'
                module.log(msg)
                results['meta'][vios_key]['messages'].append(msg)
                results['status'][vios_key] = 'FAILURE-CLUSTER'
                continue
            got_cluster_status = True

        results['status'][vios_key] = "SUCCESS-UPDT"
        # DEBUG-Begin : Uncomment for testing without effective update operation
        # results['meta'][vios_key]['messages'].append('Warning: testing without effective update operation')
        # results['meta'][vios_key]['messages'].append('NIM Command: {0} '.format(updateios_cmd))
        # rc = 0
        # stdout = 'NIM Command: {0} '.format(updateios_cmd)
        # continue
        # DEBUG-End

        for vios in target_tuple:
            module.log('Updating VIOS: {0}'.format(vios))

            # set the error label to be used in sub routines
            if vios == target_tuple[0]:
                err_label = "FAILURE-UPDT1"
            else:
                err_label = "FAILURE-UPDT2"

            # if needed stop the cluster for the VIOS
            restart_needed = False
            if tuple_len == 2 and module.params['action'] in ['install', 'cleanup'] and module.params['manage_cluster']:
                if not cluster_stop_start(module, target_tuple, vios_key, vios, 'stop'):
                    results['status'][vios_key] = err_label
                    break  # cannot continue
                restart_needed = True

            # Perform the updateios operation
            cmd = updateios_cmd + [vios]
            rc, stdout, stderr = module.run_command(cmd)
            results['meta'][vios_key][vios]['cmd'] = ' '.join(cmd)
            results['meta'][vios_key][vios]['stdout'] = stdout
            results['meta'][vios_key][vios]['stderr'] = stderr
            skip_next_target = False
            if rc != 0:
                msg = 'Failed to perform {0} updateios operation on {1}, cmd:\'{2}\', rc:{3}'\
                      .format(module.params['action'], vios, ' '.join(cmd), rc)
                module.log(msg + ', stdout: {0}'.format(stdout) + ', stderr: {0}'.format(stderr))
                results['meta'][vios_key]['messages'].append(msg)
                results['status'][vios_key] = err_label
                # in case of failure try to restart the cluster if needed
                skip_next_target = True
            else:
                msg = 'VIOS {0} updateios {1} successfull'.format(vios, module.params['action'])
                module.log(msg)
                results['meta'][vios_key]['messages'].append(msg)
                results['changed'] = True

            # if needed restart the cluster for the VIOS
            # TODO check if updateios returns before it finishes
            if restart_needed:
                if not cluster_stop_start(module, target_tuple, vios_key, vios, 'start'):
                    results['status'][vios_key] = err_label
                    break  # cannot continue

            if skip_next_target:
                break


def main():
    global module
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(choices=['install', 'commit', 'cleanup', 'remove'], required=True, type='str'),
            targets=dict(required=True, type='list', elements='str'),
            filesets=dict(type='str'),
            installp_bundle=dict(type='str'),
            lpp_source=dict(type='str'),
            accept_licenses=dict(type='bool', default=True),
            manage_cluster=dict(type='bool', default=False),
            preview=dict(type='bool', default=True),
            time_limit=dict(type='str'),
            vios_status=dict(type='dict'),
            nim_node=dict(type='dict')
        ),
        required_if=[
            ['action', 'install', ['lpp_source']],
        ],
        mutually_exclusive=[
            ['filesets', 'installp_bundle'],
        ],
    )

    results = dict(
        changed=False,
        msg='',
        targets=[],
        stdout='',
        stderr='',
        meta={'messages': []},
        # meta structure will be updated as follow:
        # meta={
        #   'messages': [],
        #   tuple:{
        #       'messages': [],
        #       vios:{
        #           'stdout': '',
        #           'stderr': '',
        #       }
        #   }
        # }
        nim_node={},
        status={},
        # status structure will be updated as follow:
        # status={
        #   target_name: 'SUCCESS' or 'FAILURE'
        # }
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    vios_status = {}

    # Get and check parameters
    if module.params['vios_status']:
        vios_status = module.params['vios_status']
    else:
        vios_status = None
    if module.params['action'] == 'remove':
        param_one_of(['installp_bundle', 'filesets'])
    else:
        if module.params['filesets'] or module.params['installp_bundle']:
            msg = 'action is {0}: discarding installp_bundle and filesets attribute'.format(module.params['action'])
            module.log(msg + ', got: filesets:"{0}" and installp_bundle:"{1}"'
                       .format(module.params['filesets'], module.params['installp_bundle']))
            results['meta']['messages'].append(msg)

    # build a time structure for time_limit attribute,
    time_limit = None
    if module.params['time_limit']:
        match_key = re.match(r"^\s*\d{2}/\d{2}/\d{4} \S*\d{2}:\d{2}\s*$",
                             module.params['time_limit'])
        if match_key:
            time_limit = time.strptime(module.params['time_limit'], '%m/%d/%Y %H:%M')
        else:
            results['msg'] = 'Malformed time limit "{0}", please use mm/dd/yyyy hh:mm format.'.format(module.params['time_limit'])
            module.fail_json(**results)

    module.debug('*** START UPDATEIOS OPERATION ***')

    # build_nim_node
    refresh_nim_node(module, 'vios')

    # check targets are valid NIM clients
    results['targets'] = check_vios_targets(module, module.params['targets'])

    if not results['targets']:
        module.log('Warning: Empty target list, targets: \'{0}\''.format(module.params['targets']))
        results['msg'] = 'Empty target list, please check their NIM states and they are reacheable.'
        module.exit_json(**results)

    module.debug('Target list: {0}'.format(results['targets']))
    # initialize the results dictionary for target tuple keys
    for target in results['targets']:
        vios_key = tuple_str(target)
        results['status'][vios_key] = ''  # first time init
        results['meta'][vios_key] = {'messages': []}  # first time init
        for vios in target:
            results['meta'][vios_key][vios] = {}    # first time init

    # Perfom the update
    nim_updateios(module, results['targets'], vios_status, time_limit)

    # set status and exit
    if not results['status']:
        module.log('NIM updateios operation: status table is empty')
        results['meta']['messages'].append('Warning: status table is empty, returning initial vios_status.')
        results['status'] = module.params['vios_status']
        results['msg'] = "NIM updateios operation completed. See meta data for details."
        module.log(results['msg'])
    else:
        target_errored = [key for key, val in results['status'].items() if 'FAILURE' in val]
        if len(target_errored):
            results['msg'] = "NIM updateios operation failed for {0}. See status and meta for details.".format(target_errored)
            module.log(results['msg'])
            module.fail_json(**results)
        else:
            results['msg'] = "NIM updateios operation completed. See status and meta for details."
            module.log(results['msg'])
            module.exit_json(**results)


if __name__ == '__main__':
    main()
