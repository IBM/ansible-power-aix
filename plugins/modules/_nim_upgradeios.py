#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['deprecated'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: _nim_upgradeios
short_description: Use NIM to update a single or a pair of Virtual I/O Servers.
description:
- Uses the NIM to perform upgrade to Virtual I/O Server (VIOS) targets tuple.
- Checks status of previous operation if provided before running its operations.
- VIOSes of a tuple must be on the same cluster and the node states must be OK.
- When upgrading VIOSes pair, it checks the cluster state, stop it before installing
  the VIOS, and restart it after installation.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform on the target VIOSes.
    - C(migrate) to use migvios NIM operation to migrate the system software.
    - C(viosupgrade) to use the viosupgrade command to upgrade. Not supported yet.
    type: str
    choices: [ migrate ]
    default: migrate
  targets:
    description:
    - Specifies the list of VIOSes NIM targets to update.
    - You can specify a list of a VIOS to update alone, or two VIOSes to update as a couple. There are called tuple.
    type: list
    elements: str
    required: yes
  time_limit:
    description:
    - Before starting the action on a VIOS tuple, the actual date is compared to this parameter value; if it is greater then the task is stopped.
    - The format is C(mm/dd/yyyy hh:mm).
    - The resulting status for tuples in this case will be I(SKIPPED-TIMEOUT).
    type: str
  mksysb_name:
    description:
    - Specifies the NIM mksysb resource name that will provide the system backup image created using the mksysb command.
    - Can be used with I(action=migrate).
    type: str
  mksysb_prefix:
    description:
    - Prefix of the NIM mksysb resource.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(mksysb_name) is not specified.
    - Can be used with I(action=migrate).
    type: str
  mksysb_postfix:
    description:
    - Postfix of the NIM mksysb resource.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(mksysb_name) is not specified.
    - Can be used with I(action=migrate).
    type: str
  backup_name:
    description:
    - Specifies the NIM ios_backup resource name that will provide the VIOS backup configuration created using the viosbr command.
    - Can be used with I(action=migrate).
    type: str
  backup_prefix:
    description:
    - Prefix of the NIM ios_backup resource.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(backup_name) is not specified.
    - Can be used with I(action=migrate).
    type: str
  backup_postfix:
    description:
    - Postfix of the NIM ios_backup resource.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(backup_name) is not specified.
    - Can be used with I(action=migrate).
    type: str
  spot_name:
    description:
    - Specifies the NIM Shared product Object Tree (SPOT) resource name that is a fundamental resource in the NIM environment.
    - It is required to install or initialize all types of machine configurations.
    - It provides a /usr file system for diskless and dataless clients, as well as the network boot support for all clients.
    - Can be used with I(action=migrate).
    type: str
  spot_prefix:
    description:
    - Prefix of the NIM SPOT resource.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(spot_name) is not specified.
    - Can be used with I(action=migrate).
    type: str
  spot_postfix:
    description:
    - Postfix of the NIM SPOT resource.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(spot_name) is not specified.
    - Can be used with I(action=migrate).
    type: str
  lpp_source:
    description:
    - Specifies the NIM lpp_source resource that will provide the minimum set of support images required for the BOS installation.
    - Can be used with I(action=migrate).
    type: str
  bosinst_data:
    description:
    - Specifies the NIM bosinst_data resource that contains information for the BOS installation program.
    - Installation information is specified in a NIM resource prior to the installation to prevent the need for prompting at the console.
    - If not provided, missing information must be specified manually for the BOS installation to proceed.
    - Can be used with I(action=migrate).
    type: str
  resolv_conf:
    description:
    - Specifies the NIM bosinst_data resource that contains valid /etc/resolv.conf entries that define Domain Name Protocol name-server
      information for local resolver routines.
    - Can be used with I(action=migrate).
    type: str
  image_data:
    description:
    - Specifies the NIM image_data resource that contains information for the BOS installation program.
    - It describes how physical disks and file systems should be configured in the root volume group during installation.
    - Can be used with I(action=migrate).
    type: str
  log:
    description:
    - TODO document log parameter.
    - Can be used with I(action=migrate).
    type: str
  file_resource:
    description:
    - TODO document file_resource parameter.
    - Can be used with I(action=migrate).
    type: str
  group:
    description:
    - Specifies the NIM resource group that contains NIM resources.
    - Can be used with I(action=migrate).
    type: str
  disk:
    description:
    - Specifies the disk to migrate the VIOS to.
    - Can be used with I(action=migrate).
    type: str
  cluster:
    description:
    - Specifies the name of the cluster the VIOS is a member of.
    - Can be used with I(action=migrate).
    type: str
  current_database:
    description:
    - Specifies the VIOS current database name.
    - Can be used with I(action=migrate).
    type: str
  command_flags:
    description:
    - Specifies additional flags to pass to the command.
    - Can be used with I(action=migrate).
    type: str
  viosbr_flags:
    description:
    - Specifies additional flags to pass to the viosbr command.
    - Can be used with I(action=migrate).
    type: str
  mk_image:
    description:
    - Specifies to create the system backup image (mksysb) and create the NIM resource.
    - Can be used with I(action=migrate).
    type: bool
    default: no
  boot_client:
    description:
    - Specifies to boot the NIM client after the operation.
    - Can be used with I(action=migrate).
    type: bool
    default: no
  set_boot_list:
    description:
    - Specifies to set the boot list on the NIM client.
    - Can be used with I(action=migrate).
    type: bool
    default: no
  concurrent:
    description:
    - Specifies the upgrade operation can be run in parallel on NIM clients.
    - Can be used with I(action=migrate).
    type: bool
    default: no
  manage_cluster:
    description:
    - Specifies to manage the cluster if the NIM client is part of one.
    - Can be used with I(action=migrate).
    type: bool
    default: yes
  debug:
    description:
    - Specifies the operation to execute in debug mode that is more verbose.
    - Can be used with I(action=migrate).
    type: bool
    default: no
  vios_status:
    description:
    - Specifies the result of a previous operation.
    - If set then the I(vios_status) of a target tuple must contain I(SUCCESS) to attempt update.
    - If no I(vios_status) value is found for a tuple, then returned I(status) for this tuple is set to I(SKIPPED-NO-PREV-STATUS).
    type: dict
  nim_node:
    description:
    - Allows to pass along NIM node info from a task to another so that it
      discovers NIM info only one time for all tasks.
    type: dict
notes:
  - Debug on NIM master could be done using the following command
    B(nim -o showlog -a full_log=yes -a log_type=script vios_target)
'''

EXAMPLES = r'''
- name: Perform a backup of nimvios01
  _nim_upgradeios:
    targets: "(nimvios01)"
    action: backup
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'NIM upgradeios operation completed. See status and meta for details.'
targets:
    description: List of VIOSes actually targeted for the operation.
    returned: always
    type: list
    elements: str
    sample: [vios1, 'vios2, vios3', ...]
stdout:
    description: Standard output of the command.
    returned: If the command was run.
    type: str
stderr:
    description: Standard error of the command.
    returned: If the command was run.
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
            - Previous I(vios_status) when the tuple status does not contains SUCCESS.
            - I(SKIPPED-NO-PREV-STATUS) when no I(vios_status) value is found for the tuple.
            - I(SUCCESS-UPGR1) when upgrade of first VIOS of the tuple succeeded.
            - I(SUCCESS-UPGR2) when upgrade of second VIOS of the tuple succeeded.
            - I(SKIPPED-TIMEOUT) when the I(time_limit) is reached before updating the 1st VIOS of the tuple.
            - I(FAILURE-CLUSTER) when cluster checks or operation failed.
            - I(FAILURE-UPGR1-INIT) when upgrade of first VIOS of the tuple failed to start.
            - I(FAILURE-UPGR2-INIT) when upgrade of second VIOS of the tuple failed to start.
            - I(FAILURE-UPGR1-WAIT) when an error occured waiting for the upgrade of first VIOS of the tuple to complete.
            - I(FAILURE-UPGR2-WAIT) when an error occured waiting for the upgrade of second VIOS of the tuple to complete.
            - I(FAILURE-UPGR1) when upgrade of first VIOS of the tuple failed.
            - I(FAILURE-UPGR2) when upgrade of second VIOS of the tuple failed.
            returned: when tuple are actually a NIM client.
            type: str
            sample: 'SUCCESS-UPGR2'
    sample:
        "status": {
            "vios1-vios2": "SUCCESS-UPGR2",
            "vios3": "SUCCESS-ALTDC",
            "vios4-vios5": "FAILURE-CLUSTER",
            "vios6": "FAILURE-UPGR1-INIT",
            "vios7-vios8": "SKIPPED-TIMEOUT",
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
                            description: Command exectued.
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
import threading

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule

# TODO check and add SSP support
# TODO add mirrored rootvg support


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
    global results

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
        module      (dict): The Ansible module
        type     (str): type of the nim object to get information
    note:
        Exits with fail_json in case of error
    return:
        info_hash   (dict): information from the nim clients
    """
    global results

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
    global results

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


def build_name(target, name, prefix, postfix):
    """
    Build the name , if set returns it,
    otherwise name will be formatted as: <prefix><target><postfix>

    arguments:
        target  (str): the NIM Client
        name    (str): name of the resource (can be empty)
        prefix  (str): prefix of the name (can be empty)
        postfix (str): postfix of the name (can be empty)
    return:
        name     (str): resulting name
    """
    if name:
        return name

    name = ''
    if prefix:
        name += prefix
    name += target
    if postfix:
        name += postfix
    return name


# TODO: test MigviosThread class
class MigviosThread(threading.Thread):
    """
    Class use for the migration of a VIOS tuple

    module.param used:
        time_limit    (optional) to limit the operation in time
    """

    def __init__(self, module, target_tuple, time_limit):
        vios_key = tuple_str(target_tuple)
        self._stop_event = threading.Event()
        self._module = module
        self._target_tuple = target_tuple
        self._time_limit = time_limit
        threading.Thread.__init__(self, name='MigviosThread({0})'.format(vios_key))

    def run(self):
        self._module.debug('Strating {0}'.format(self.getName()))
        nim_migvios_tuple(self._module, self._target_tuple, self._stop_event)
        self._module.debug('End of {0}'.format(self.getName()))

    def join(self, timeout=None):
        while self.isAlive():
            t = time.time()
            if self._time_limit and t >= self._time_limit:
                break
            time.sleep(60)
        self._stop_event.set()
        self._module.debug('Asking {0} to terminate, waiting for timeout={1}'
                           .format(self.getName(), timeout))
        threading.Thread.join(self, timeout)


# TODO: test nim_migvios_all function
def nim_migvios_all(module, targets, time_limit):
    """
    Execute the migvios operation on the first vios of each tuples,
    wait for completion, if succeeded execute the migvios operation
    for second vios and wait for completion.

    args:
        module     (dict): The Ansible module
        targets    (list): list of target tuples
        time_limit  (str): date to limit the operation in time
    return:
        none
    """
    global results

    # threads = []

    for target_tuple in targets:
        # TODO: test and activate multi threading
        module.debug('Start nim_migvios_tuple for {0}'.format(target_tuple))
        nim_migvios_tuple(module, target_tuple, None)
        module.debug('End nim_migvios_tuple for {0}'.format(target_tuple))
    #     # Spawn a thread running nim_migvios_tuple(module, target_tuple, time_limit)
    #     module.debug('Spawning MigviosThread for {0} terminated'.format(target_tuple))

    #     th = MigviosThread(module=module,
    #                        target_tuple=target_tuple,
    #                        time_limit=time_limit)
    #     threads.append(th)
    #     th.start()

    # for th in threads:
    #     module.debug('Waiting for {0} termination...'.format(th.getName()))
    #     # No timeout in this join() as
    #     # - the user can set a time_limit
    #     # - there is a timeout when NIM states show no progress
    #     th.join()
    #     module.debug('{0} terminated'.format(th.getName()))

    # for th in threads:
    #     if th.isAlive():
    #         module.log('{0} is still alive'.format(th.getName()))


# TODO: test nim_migvios_tuple function
def nim_migvios_tuple(module, target_tuple, stop_event):
    """
    Handle the migvios execution in a thread for the tuple.
    Watch for stop_event (set by join() if time_limit is reached).
    Set results['status'][vios_key] with the migration status.

    args:
        module          (dict): The Ansible module
        target_tuple    (list): tuple of target to run migvios
        stop_event      (bool): flag set if time_limit is reached

    module.param used:
        action      (for logging only)
        vios_status (optional)
        time_limit  (optional) to limit the operation in time

    return:
        none
    """
    global results

    # build the key from the tuple
    vios_key = tuple_str(target_tuple)
    vios1 = target_tuple[0]

    module.log('migvios operation for tuple: {0}'.format(target_tuple))

    for vios in target_tuple:
        module.log('migvios operation for VIOS: {0}'.format(vios))

        # Check previous status if known
        if module.params['vios_status'] is not None:
            if vios_key not in module.params['vios_status']:
                msg = '{0} vioses skipped (no previous status found)'.format(vios_key)
                module.log('[WARNING] ' + msg)
                results['meta'][vios_key]['messages'].append(msg)
                results['status'][vios_key] = 'SKIPPED-NO-PREV-STATUS'
                continue

            if 'SUCCESS' not in module.params['vios_status'][vios_key]:
                msg = '{0} VIOSes skipped (vios_status: {1})'.format(vios_key, module.params['vios_status'][vios_key])
                module.log(msg)
                results['meta'][vios_key]['messages'].append(msg)
                results['status'][vios_key] = module.params['vios_status'][vios_key]
                continue

        # check if we are asked to stop (time_limit might be reached)
        if stop_event and stop_event.isSet():
            msg = 'Time limit {0} reached, no further operation'.format(time.strftime('%m/%d/%Y %H:%M', module.params['time_limit']))
            module.log('[WARNING] ' + msg)
            results['meta'][vios_key]['messages'].append(msg)
            results['status'][vios_key] = "SKIPPED-TIMEOUT"
            return

        rc = nim_migvios(module, target_tuple, vios_key, vios)
        if rc == 0:
            if vios == vios1:
                results['status'][vios_key] = 'SUCCESS-UPGR1-INIT'
            else:
                results['status'][vios_key] = 'SUCCESS-UPGR2-INIT'
        else:
            if vios == vios1:
                results['status'][vios_key] = 'FAILURE-UPGR1-INIT'
            else:
                results['status'][vios_key] = 'FAILURE-UPGR2-INIT'
            return

        # check if we are asked to stop (time_limit might be reached)
        if stop_event and stop_event.isSet():
            msg = 'Time limit {0} reached, no further operation'.format(time.strftime('%m/%d/%Y %H:%M', module.params['time_limit']))
            module.log('[WARNING] ' + msg)
            results['meta'][vios_key]['messages'].append(msg)
            return

        # check the operation progress, wait the completion and set the status
        rc = nim_wait_migvios(module, vios_key, vios)
        if rc == 0:
            if vios == vios1:
                module.status[vios_key] = 'SUCCESS-UPGR1'
            else:
                module.status[vios_key] = 'SUCCESS-UPGR2'
        elif rc == -1:
            if vios == vios1:
                module.status[vios_key] = 'FAILURE-UPGR1-WAIT'
            else:
                module.status[vios_key] = 'FAILURE-UPGR2-WAIT'
            # will not migrate the next vios
            return
        else:
            if vios == vios1:
                module.status[vios_key] = 'FAILURE-UPGR1'
            else:
                module.status[vios_key] = 'FAILURE-UPGR2'
            # will not migrate the next vios
            return
    return


# TODO: test nim_migvios function
def nim_migvios(module, target_tuple, vios_key, vios):
    """
    NIM migvios operation against the specified vios

    args:
        module          (dict): The Ansible module
        target_tuple    (list): tuple of target to run migvios
        vios_key         (str): key of the results dictionary matching the target_tuple
        vios             (str): the VIOS to run the command against

    return:
        rc      the return code of the command
    """
    global results

    module.log('Starting migvios on VIOS: {0}'.format(vios))

    # get the backup name
    mksysb_name = build_name(vios, module.params['mksysb_name'], module.params['mksysb_prefix'], module.params['mksysb_postfix'])
    backup_name = build_name(vios, module.params['backup_name'], module.params['backup_prefix'], module.params['backup_postfix'])

    # Note: the option -a time_limit is not yet supported by migvios
    # time_limit attribute is only valid with the following operations: bos_inst, cust, and alt_disk_install.
    # nim -o migvios -a spot=jaguar12_ios_mksysb_spot -a ios_mksysb=jaguar12_ios_mksysb -a ios_backup=fake
    #                -a resolv_conf=resolv_conf -a bosinst_data=bosinst_data_jaguar12_new
    #                -a boot_client=no -a mk_image=yes jaguar12
    cmd = ['nim', '-Fo', 'migvios']

    cmd += ['-a', 'ios_mksysb={0}'.format(mksysb_name)]
    cmd += ['-a', 'ios_backup={0}'.format(backup_name)]

    if module.params['group']:
        cmd += ['-a', 'group={0}'.format(module.params['group'])]

    if module.params['spot_name'] or module.params['spot_prefix'] or module.params['spot_postfix']:
        if not module.params['spot_name'] and module.params['spot_postfix'] is None:
            module.params['spot_postfix'] = '_spot'
        spot_name = build_name(vios, module.params['spot_name'], module.params['spot_prefix'], module.params['spot_postfix'])
        cmd += ['-a', 'spot={0}'.format(spot_name)]

    if module.params['lpp_source']:
        cmd += ['-a', 'lpp_source={0}'.format(module.params['lpp_source'])]
    if module.params['bosinst_data']:
        cmd += ['-a', 'bosinst_data={0}'.format(module.params['bosinst_data'])]
    if module.params['resolv_conf']:
        cmd += ['-a', 'resolv_conf={0}'.format(module.params['resolv_conf'])]
    if module.params['image_data']:
        cmd += ['-a', 'image_data={0}'.format(module.params['image_data'])]
    if module.params['log']:
        cmd += ['-a', 'log={0}'.format(module.params['log'])]
    if module.params['file_resource']:
        cmd += ['-a', 'file_res={0}'.format(module.params['file_resource'])]

    if module.params['disk']:
        cmd += ['-a', 'disk={0}'.format(module.params['disk'])]
    if module.params['cluster']:
        cmd += ['-a', 'cluster={0}'.format(module.params['cluster'])]
    if module.params['current_database']:
        cmd += ['-a', 'current_db={0}'.format(module.params['current_database'])]
    if module.params['command_flags']:
        cmd += ['-a', 'cmd_flags={0}'.format(module.params['command_flags'])]
    if module.params['viosbr_flags']:
        cmd += ['-a', 'viosbr_flags={0}'.format(module.params['viosbr_flags'])]

    cmd += ['-a', 'mk_image=yes' if module.params['mk_image'] else 'mk_image=no']
    cmd += ['-a', 'boot_client=yes' if module.params['boot_client'] else 'boot_client=no']
    cmd += ['-a', 'set_bootlist=yes' if module.params['set_boot_list'] else 'set_bootlist=no']
    # TODO check when concurrent=no we get an error:
    # time_limit attribute is only valid with the following operations: bos_inst, cust, and alt_disk_install
    if module.params['concurrent']:
        cmd += ['-a', 'concurrent=yes']
    cmd += ['-a', 'skipcluster=no' if module.params['manage_cluster'] else 'skipcluster=yes']
    # TODO should we get debug settings from Ansible to set migvios -a debug
    cmd += ['-a', 'debug=yes' if module.params['debug'] else 'debug=no']
    cmd += [vios]

    # DEBUG - Begin: Uncomment for testing without effective migvios operation
    # results['meta'][vios_key]['messages'].append('Warning: testing without effective migvios command')
    # results['meta'][vios_key]['messages'].append('NIM Command: {0} '.format(cmd))
    # rc = 0
    # sleep(30)
    # msg = 'VIOS {0} migration successfully initiated'.format(vios)
    # module.log(msg)
    # results['meta'][vios_key]['messages'].append(msg)
    # results['meta'][vios_key][vios]['stdout'] = 'No stdout: DEBUG testing.'
    # results['meta'][vios_key][vios]['stderr'] = 'No stderr: DEBUG testing.'
    # results['changed'] = True
    # return rc
    # DEBUG - End

    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = 'Failed to migrate {0} VIOS, migvios returned {1}'.format(vios, rc)
        module.log(msg)
        module.log('cmd \'{0}\' failed, stdout: {1}, stderr:{2}'.format(' '.join(cmd), stdout, stderr))
        results['meta'][vios_key]['messages'].append(msg)
        results['meta'][vios_key][vios]['cmd'] = ' '.join(cmd)
        results['meta'][vios_key][vios]['stdout'] = stdout
        results['meta'][vios_key][vios]['stderr'] = stderr
    else:
        # update the nim
        if 'backup' in module.nim_node['vios'][vios]:
            module.nim_node['vios'][vios]['backup']['name'] = backup_name
        else:
            module.nim_node['vios'][vios]['backup'] = {}
            module.nim_node['vios'][vios]['backup']['name'] = backup_name
        msg = 'VIOS {0} migration successfully initiated'.format(vios)
        module.log(msg)
        results['meta'][vios_key]['messages'].append(msg)
        results['changed'] = True

    return rc


# TODO: test nim_check_migvios function
def nim_wait_migvios(module, vios_key, vios):
    """
    Wait for the migvios to finish for the specified VIOS

    args:
        module     (dict): The Ansible module
        vios_key    (str): key of the results dictionary matching the target_tuple
        vios        (str): the VIOS to wait for

    return:
        -1 if timed out,
        0  if migvios succeeded,
        1  if migvios failed,
        2  if internal or command error,
    """
    global results

    module.log('Waiting completion of migvios on {0}...'
               .format(vios))

    cmd = ['lsnim', '-a', 'info', '-a', 'Cstate', '-a', 'Cstate_result', '-a', 'Mstate', '-a', 'prev_state', vios]

    # TODO: can we reduce the timeout (3 hours without states change)?
    # Time out if nim states do not change for more than 3 hours
    # check every 30 seconds
    # log debug every state change or every 5 minutes
    # (360 * 30s = 180 min)
    _TIMEOUT_NIMSTATE = 360 * 30
    wait_time = _TIMEOUT_NIMSTATE
    prev_states = {}
    curr_states = {}
    while wait_time >= 0:
        time.sleep(30)
        wait_time -= 30

        # TODO: remove time_limit for wait migvios? no limit there.
        #           only timeout when no nim states progress for a long time
        # if time_limit is not None and time.localtime(time.time()) >= time_limit:
        #     msg = 'Time limit {0} reached, no further operation'\
        #           .format(time_limit_str)
        #     module.log(msg)
        #     results['meta'][vios_key]['messages'].append(msg)
        #     return -1

        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = 'Failed to get the NIM state for {0}, rc: {1}'.format(vios, rc)
            module.log(msg)
            module.log('cmd {0}, stdout: {1}, stderr:{2}'.format(' '.join(cmd), stdout, stderr))
            results['meta'][vios_key]['messages'].append(msg)
            results['meta'][vios_key][vios]['cmd'] = ' '.join(cmd)
            results['meta'][vios_key][vios]['stdout'] = stdout
            results['meta'][vios_key][vios]['stderr'] = stderr
            return 2

        if len(curr_states) >= 0:
            prev_states = curr_states.copy()
            curr_states = {}

        # TODO Should we also get NIM 'info' state to trace migvios progress in NIM?
        # Retrieve the NIM states
        # <vios>:
        #    Cstate = ready for a NIM operation
        #    prev_state = customization is being performed
        #    Mstate = ready for use
        #    Cstate_result = success
        curr_states = build_dict(module, stdout)

        if len(curr_states) <= 0:
            msg = 'Failed to retrieve NIM states for {0} from lsnim output: unexpected format.'.format(vios)
            module.log(msg)
            module.log('cmd {0} stdout: {1}'.format(' '.join(cmd), stdout))
            results['meta'][vios_key]['messages'].append(msg)
            results['meta'][vios_key][vios]['stdout'] = stdout
            results['meta'][vios_key][vios]['stderr'] = stderr
            return 2
        elif curr_states == prev_states:
            if wait_time % 300 == 0:
                # log only every 5 minutes
                msg = 'VIOS {0}, waiting for migvios completion... {1} minute(s)'.format(vios, wait_time / 60)
                module.log(msg)
            continue

        # NIM states have changed
        wait_time = _TIMEOUT_NIMSTATE
        module.debug('VIOS {0}, NIM states: {1}'.format(vios, stdout))

        # TODO can migvios be ongoing if Cstate_result != 'success'? should we wait?
        if curr_states[vios]['Cstate_result'] != 'success':
            msg = 'VIOS {0} migration failed, NIM states:'.format(vios)
            module.log(msg)
            module.log(curr_states)
            results['meta'][vios_key]['messages'].append(msg)
            results['meta'][vios_key]['messages'].append(stdout.split('\n'))
            return 1

        # Check if it's the end of the operation
        if curr_states[vios]['Mstate'] != 'ready for use' and \
           curr_states[vios]['Cstate'] != 'ready for a NIM operation' and \
           curr_states[vios]['prev_state'] != 'customization is being performed':
            prev_states = curr_states.copy()
            continue

        msg = 'VIOS {0} successfully upgraded'.format(vios)
        module.log(msg)
        results['meta'][vios_key]['messages'].append(msg)
        results['changed'] = True
        return 0

    msg = 'Migration operation on {0} has shown no progress for {1} hours, NIM state:'\
          .format(vios, _TIMEOUT_NIMSTATE % 3600)
    module.log(msg)
    results['meta'][vios_key]['messages'].append(msg)
    results['meta'][vios_key]['messages'].append(stdout.split('\n'))
    return -1


###################################################################################

def main():
    global module
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(choices=['migrate'], required=False, type='str', default='migrate'),
            targets=dict(required=True, type='list', elements='str'),
            time_limit=dict(required=False, type='str'),
            vios_status=dict(required=False, type='dict'),
            nim_node=dict(required=False, type='dict'),

            # migrate operation
            mksysb_name=dict(type='str'),
            mksysb_prefix=dict(type='str'),
            mksysb_postfix=dict(type='str'),
            backup_name=dict(type='str'),
            backup_prefix=dict(type='str'),
            backup_postfix=dict(type='str'),
            spot_name=dict(type='str'),
            spot_prefix=dict(type='str'),
            spot_postfix=dict(type='str'),

            lpp_source=dict(type='str'),
            bosinst_data=dict(type='str'),
            resolv_conf=dict(type='str'),
            image_data=dict(type='str'),
            log=dict(type='str'),
            file_resource=dict(type='str'),
            group=dict(type='str'),

            disk=dict(type='str'),
            cluster=dict(type='str'),
            current_database=dict(type='str'),
            command_flags=dict(type='str'),
            viosbr_flags=dict(type='str'),

            mk_image=dict(type='bool', default=False),
            boot_client=dict(type='bool', default=False),
            set_boot_list=dict(type='bool', default=False),
            concurrent=dict(type='bool', default=False),
            manage_cluster=dict(type='bool', default=True),
            debug=dict(type='bool', default=False),
        ),
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
        #   target_key:{
        #       'messages': [],
        #       vios:{
        #           'stdout': '',
        #           'stderr': '',
        #       }
        #   }
        # }
        nim_node={},
        status={},
    )
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    # build a time structure for time_limit attribute,
    time_limit = None
    if module.params['time_limit']:
        match_key = re.match(r"^\s*\d{2}/\d{2}/\d{4} \S*\d{2}:\d{2}\s*$",
                             module.params['time_limit'])
        if match_key:
            time_limit = time.strptime(module.params['time_limit'], '%m/%d/%Y %H:%M')
            module.time_limit = time_limit
        else:
            results['msg'] = 'Malformed time limit "{0}", please use mm/dd/yyyy hh:mm format.'.format(module.params['time_limit'])
            module.fail_json(**results)

    module.debug('*** START NIM UPGRADE VIOS OPERATION ***')

    results['meta']['messages'].append('Upgradeios operation for {0}'.format(module.params['targets']))
    module.log('Upgradeios operation {0} for targets: {1}'.format(module.params['action'], module.params['targets']))

    # build nim_node
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
        results['status'][vios_key] = ''
        results['meta'][vios_key] = {'messages': []}
        for vios in target:
            results['meta'][vios_key][vios] = {}

    # set default postfix
    if not module.params['mksysb_name'] and module.params['mksysb_postfix'] is None:
        module.params['mksysb_postfix'] = '_sysb'
    if not module.params['backup_name'] and module.params['backup_postfix'] is None:
        module.params['backup_postfix'] = '_iosb'

    # perfom the operation
    if module.params['action'] == 'migrate':
        nim_migvios_all(module, results['targets'], time_limit)

    # set status and exit
    if not results['status']:
        module.log('NIM upgradeios operation: status table is empty')
        results['meta']['messages'].append('Warning: status table is empty, returning initial vios_status.')
        results['status'] = module.params['vios_status']
        results['msg'] = "NIM upgradeios operation completed. See meta data for details."
        module.log(results['msg'])
    else:
        target_errored = [key for key, val in results['status'].items() if 'FAILURE' in val]
        if len(target_errored):
            results['msg'] = "NIM upgradeios operation failed for {0}. See status and meta for details.".format(target_errored)
            module.log(results['msg'])
            module.fail_json(**results)
        else:
            results['msg'] = "NIM upgradeios operation completed. See status and meta for details."
            module.log(results['msg'])
            module.exit_json(**results)


if __name__ == '__main__':
    main()
