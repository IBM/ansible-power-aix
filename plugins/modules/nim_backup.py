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
module: nim_backup
short_description: Use NIM to create, list and restore backup on LPAR and VIOS clients.
description:
- Uses the NIM define operation it creates mksysb or ios_backup resource on the NIM master
  depending on the type of the client.
- Lists the backup resources available on the NIM master and allows to filter results.
- Uses the NIM bos_inst and viosbr to restore backup images on LPAR or VIOS clients.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Controls what is performed.
    - C(create) performs an backup operation on targets trough NIM master.
    - C(restore) restores a backup on targets trough NIM master.
    - C(view) displays the content of a VIOS backup, only for I(type=backup).
    - C(list) lists backups for targets on the NIM master.
    type: str
    choices: [ create, restore, view, list ]
    required: yes
  type:
    description:
    - Specifies the type of backup object to operate.
    - C(mksysb) operates on backup of the operating system (that is, the root volume group) of a LPAR or VIOS target.
    - C(ios_mksysb) operates on VIOS backup of the operating system (that is, the root volume group).
    - C(ios_backup) operates on VIOS backup, that is all the relevant data to recover VIOS after a new installation.
    - Discarded for I(action=view) as this action only applies to ios_backup.
    type: str
    choices: [ mksysb, ios_mksysb, ios_backup ]
    default: mksysb
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - C(foo*) designates all the NIM clients with name starting by C(foo).
    - C(foo[2:4]) designates the NIM clients among foo2, foo3 and foo4.
    - C(*) or C(ALL) designates all the NIM clients.
    - C(vios) or C(standalone) designates all the NIM clients of this type.
    - Required if I(action=create) and I(action=restore).
    - If I(action=list) it filters the results on the source_image attribute of the NIM resource.
    type: list
    elements: str
    required: no
  nim_node:
    description:
    - Allows to pass along NIM node info from a task to another so that it
      discovers NIM info only one time for all tasks.
    type: dict
  location:
    description:
    - Specifies where to put the backup files on the NIM master.
    - If not specified default for LPAR targets is I(location=/export/nim/mksysb) and for
      VIOS targets it is I(location=/export/nim/ios_backup).
    - Required if I(action=create) and I(action=restore).
    type: path
  name:
    description:
    - Exact name of the backup NIM resource to act on.
    - If I(action=list) it filters the results on the name of the NIM resource.
    - Required if I(action=view).
    type: str
  name_prefix:
    description:
    - Prefix of the backup NIM resource name to act on.
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(name) is not specified.
    - If I(action=list) it filters the results on the name of the NIM resource.
    type: str
  name_postfix:
    description:
    - Specifies the postfix of the backup NIM resource name to act on.
    - If not specified default for LPAR targets is I(name_postfix=_sysb) and for
      VIOS targets it is I(name_postfix=_iosb).
    - The name format will be I(<prefix><target_name><postfix>).
    - Used only if C(name) is not specified.
    - If I(action=list) it filters the results on the name of the NIM resource.
    type: str
  group:
    description:
    - Specifies the resource group to use for restoration.
    - Can be used on a standalone client if I(action=restore).
    type: str
  spot_name:
    description:
    - Specifies the exact SPOT resource name to create to restore the backup on a standalone client.
    - Can be used on a standalone client if I(action=restore).
    type: str
  spot_prefix:
    description:
    - Specifies the prefix of SPOT resource name created to restore the backup on a standalone client.
    - The SPOT name format will be I(<spot_prefix><target_name><spot_postfix>).
    - Used only if C(spot_name) is not specified.
    - Can be used on a standalone client if I(action=restore).
    type: str
  spot_postfix:
    description:
    - Specifies the prostfix of SPOT resource name created to restore the backup on a standalone client.
    - The SPOT name format will be I(<spot_prefix><target_name><spot_postfix>).
    - Used only if C(spot_name) is not specified.
    - Can be used on a standalone client if I(action=restore).
    type: str
    default: _spot
  spot_location:
    description:
    - Specifies the location of SPOT resource on the NIM master created to restore the backup on a standalone client.
    - Can be used on a standalone client if I(action=restore).
    type: path
    default: /export/nim/spot
  oslevel:
    description:
    - Specifies the oslevel to filter results.
    - Can be used if I(action=list).
    type: str
  remove_spot:
    description:
    - Specifies to remove the SPOT resource created to restore the backup on a standalone client.
    - Can be used on a standalone client if I(action=restore).
    type: bool
    default: yes
  remove_backup:
    description:
    - Specifies to remove the backup resource created on the NIM master.
    - Can be used on a standalone client if I(action=restore).
    type: bool
    default: no
  accept_licenses:
    description:
    - Specifies to automatically accept all licenses during the restoration of the backup.
    - Can be used on a standalone client if I(action=restore).
    type: bool
    default: yes
  boot_target:
    description:
    - Specifies to boot the NIM client after restoration of the backup.
    - Can be used on a standalone client if I(action=restore).
    type: bool
    default: yes
'''

EXAMPLES = r'''
- name: List mksysb targeting nimclient1 at a specific level and name starting with ansible
  nim_backup:
    action: list
    targets: nimclient1
    oslevel: "7200-03-02"
    name_prefix: ansible

- name: Create a mksysb backup of a LPAR
  nim_backup:
    action: create
    targets: nimclient1
    name_postfix: _mksysb

- name: Restore a mksysb backup on a LPAR
  nim_backup:
    action: restore
    targets: nimclient1
    name_postfix: _mksysb
    spot_postfix: _spot
    remove_backup: yes
    remove_spot: yes
    boot_target: no
    accept_licenses: yes

- name: Backup a VIOS configuration
  nim_backup:
    action: create
    type: ios_backup
    targets: vios1
    name_postfix: _iosbackup

- name: Get the backup configuration of a VIOS
  nim_backup:
    action: view
    targets: vios1

- name: Restore the backup configuration on a VIOS
  nim_backup:
    action: restore
    type: ios_backup
    targets: vios1
    name_postfix: _iosbackup
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
targets:
    description: List of VIOSes.
    returned: always
    type: list
    elements: str
    sample: [nimclient01, nimclient02, ...]
status:
    description: Status of the operation for each C(target). It can be empty, SUCCESS or FAILURE.
    returned: always
    type: dict
    contains:
        <target>:
            description: Status of the execution on the <target>.
            returned: when target is actually a NIM client
            type: str
            sample: 'SUCCESS'
    sample: "{ nimclient01: 'SUCCESS', nimclient02: 'FAILURE' }"
backup_info:
    description: The backup NIM resource information.
    returned: if I(action=list)
    type: dict
    contains:
        <backup_name>:
            description: Detailed information on the NIM resource.
            type: dict
            contains:
                <attribute>:
                    description: attribute of the <backup_name> resource
                    type: str
    sample:
        "backup_info": {
            "ansible_img": {
                "Rstate"        : "ready for use",
                "alloc_count"   : "0",
                "arch"          : "power",
                "class"         : "resources",
                "creation_date" : "Mon Feb 3 20:55:28 2020",
                "location"      : "/export/nim/mksysb/ansible.sysb",
                "mod"           : "3",
                "oslevel_r"     : "7200-03",
                "oslevel_s"     : "7200-03-02-1845",
                "prev_state"    : "unavailable for use",
                "release"       : "2",
                "server"        : "master",
                "source_image"  : "nimclient01",
                "type"          : "mksysb",
                "version"       : "7"
            },
            "nimclient2_sysb": {
                "class"        : "resources",
                "type"         : "mksysb",
                "creation_date": "Sun May 3 15:54:44 2020",
                "source_image" : "nimclient2",
                "arch"         : "power",
                "Rstate"       : "ready for use",
                "prev_state"   : "unavailable for use",
                "location"     : "/export/nim/mksysb/nimclient2_ansible.sysb",
                "version"      : "7",
                "release"      : "2",
                "mod"          : "3",
                "oslevel_r"    : "7200-03",
                "oslevel_s"    : "7200-03-04-1938",
                "alloc_count"  : "0",
                "server"       : "master",
            }
        }
nim_node:
    description: NIM node info. It can contains more information if passed as option I(nim_node).
    returned: always
    type: dict
    contains:
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
                res_name:
                    description:
                    - Name of the NIM resource created.
                    - If I(action=backup) it is the name of the backup resource.
                    - If I(action=restore) and the target is a standalone machine, then it is the name of the SPOT resource.
                    returned: if I(success=True)
                    type: str
                stdout:
                    description: Standard output of the last command.
                    returned: If the command was run.
                    type: str
                stderr:
                    description: Standard error of the last command.
                    returned: If the command was run.
                    type: str
'''

import os
import re
import threading

from ansible.module_utils.basic import AnsibleModule

module = None
results = None
THRDS = []


def start_threaded(thds):
    """
    Decorator for thread start
    """
    def start_threaded_wrapper(func):
        """
        Decorator wrapper for thread start
        """
        def start_threaded_inner_wrapper(*args):
            """
            Decorator inner wrapper for thread start
            """
            thd = threading.Thread(target=func, args=(args))
            module.debug('Start thread {0}'.format(func.__name__))
            thd.start()
            thds.append(thd)
        return start_threaded_inner_wrapper
    return start_threaded_wrapper


def wait_threaded(thds):
    """
    Decorator for thread join
    """
    def wait_threaded_wrapper(func):
        """
        Decorator wrapper for thread join
        """
        def wait_threaded_inner_wrapper(*args):
            """
            Decorator inner wrapper for thread join
            """
            func(*args)
            for thd in thds:
                thd.join()
        return wait_threaded_inner_wrapper
    return wait_threaded_wrapper


@wait_threaded(THRDS)
def wait_all():
    """
    Do nothing
    """
    pass


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
    global module
    global results

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


def build_nim_node(module):
    """
    Build nim_node dictionary containing nim clients info.

    arguments:
        module      (dict): The Ansible module
    """
    global results

    types = ['standalone', 'vios']
    for type in types:
        if type not in results['nim_node']:
            results['nim_node'].update({type: get_nim_type_info(module, type)})


def get_nim_type_info(module, type):
    """
    Build the hash of nim object of specified type defined on the
    nim master and their associated key = value information.

    arguments:
        module      (dict): The Ansible module
    return:
        info_hash   (dict): information from the nim clients
    """
    global results

    cmd = ['lsnim', '-t', type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot get NIM information for {0}. Command \'{1}\' failed with return code {2}.'\
                         .format(type, ' '.join(cmd), rc)
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
        NIM info dictionary
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


def expand_targets(targets):
    """
    Expand the list of target patterns.

    A target pattern can be of the following form:
        target*       all the nim client machines whose names start
                          with 'target'
        target[n1:n2] where n1 and n2 are numeric: target<n1> to target<n2>
        * or ALL      all the nim clients
        vios          all the nim clients type=vios
        standalone    all the nim clients type=standalone
        client_name   the nim client named 'client_name'
        master        the nim master

    arguments:
        targets (list): The list of target patterns

    return: the list of existing machines matching the target patterns
    """
    global results

    clients = []
    for target in targets:
        # Build target(s) from keywords: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = list(results['nim_node']['standalone'])
            clients.extend(list(results['nim_node']['vios']))
            break

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
                if curr_name in results['nim_node']['standalone'] or curr_name in results['nim_node']['vios']:
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

        # Build target(s) from: quimby05 quimby08 quimby12
        if target in results['nim_node']['standalone'] or target in results['nim_node']['vios']:
            clients.append(target)

    return list(set(clients))


def build_name(target, name, prefix, postfix):
    """
    Build the name , if set returns params['name'],
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


@start_threaded(THRDS)
def nim_mksysb_create(module, target, objtype, params):
    """
    Perform a NIM define operation to create a mksysb

    arguments:
        module  (dict): the module variable
        target   (str): the NIM Client to backup
        objtype  (str): the type of mksysb to create, can be mksysb or ios_mksysb
        params  (dict): the NIM command parameters
    note:
        set results['status'][target] with the status
    return:
        True if backup succeeded or skipped
        False otherwise
    """
    global results

    name = build_name(target, params['name'], params['name_prefix'], params['name_postfix'])

    # compute backup location
    if not os.path.exists(params['location']):
        os.makedirs(params['location'])
    location = os.path.join(params['location'], name)

    # Create the mksysb
    # To ignore space requirements use the "-F" flag when defining the mksysb resource.
    # nim -o define -t mksysb -a server=master -a mk_image=yes -a location=file_path -a source=vios mksysb_name
    # nim -o define -t ios_mksysb -a server=master -a mk_image=yes -a location=file_path -a source=vios ios_mksysb_name
    cmd = ['nim', '-o', 'define', '-a', 'server=master', '-a', 'mk_image=yes']
    cmd += ['-t', objtype]
    cmd += ['-a', 'location={0}'.format(location)]
    cmd += ['-a', 'source={0}'.format(target), name]

    if not module.check_mode:
        rc, stdout, stderr = module.run_command(cmd)
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr
        if rc != 0:
            results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
            results['status'][target] = 'FAILURE'
            return False

        results['meta'][target]['messages'].append('{0} {1} created: {2}.'.format(objtype, name, location))
        results['meta'][target]['res_name'] = name
        results['status'][target] = 'SUCCESS'
        results['changed'] = True
    else:
        results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    return True


@start_threaded(THRDS)
def nim_mksysb_restore(module, target, params):
    """
    Perform a bos_inst NIM operation to restore a mksysb

    arguments:
        module  (dict): the module variable
        target   (str): the NIM Client to restore the backup on
        params  (dict): the NIM command parameters
    note:
        set results['status'][target] with the status
    return:
        True if backup succeeded or skipped
        False otherwise
    """
    global results

    # build sysb and spot resource names
    name = build_name(target, params['name'], params['name_prefix'], params['name_postfix'])
    spot_name = build_name(target, params['spot_name'], params['spot_prefix'], params['spot_postfix'])

    cmd = ['lsnim', spot_name]
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        msg = 'SPOT {0} exists, using it to restore {1}'.format(spot_name, name)
        module.log(msg)
        results['meta'][target]['messages'].append(msg)
    else:
        # Create the SPOT from the mksysb for restore operation
        # nim -o define -t spot -a server=master -a source=mksysb_name -a location=/export/spot spot1
        cmd = ['nim', '-o', 'define', '-t', 'spot', '-a', 'server=master']
        cmd += ['-a', 'source={0}'.format(name)]
        cmd += ['-a', 'location={0}'.format(params['spot_location']), spot_name]

        if not module.check_mode:
            rc, stdout, stderr = module.run_command(cmd)
            results['meta'][target]['stdout'] = stdout
            results['meta'][target]['stderr'] = stderr
            if rc != 0:
                results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
                results['status'][target] = 'FAILURE'
                return False

            results['meta'][target]['messages'].append('SPOT {0} resource created: {1}.'.format(spot_name, params['spot_location']))
            results['meta'][target]['res_name'] = spot_name
            results['status'][target] = 'SUCCESS'
            results['changed'] = True
        else:
            results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    cmd = ['nim', '-o', 'bos_inst', '-a', 'source=mksysb']
    if params['group']:
        cmd += ['-a', 'group={0}'.format(params['group'])]
    else:
        cmd += ['-a', 'mksysb={0}'.format(name)]
        cmd += ['-a', 'spot={0}'.format(spot_name)]

    if not params['accept_licenses']:
        cmd += ['-a', 'accept_licenses=no']
    if not params['boot_target']:
        cmd += ['-a', 'boot_client=no']
    cmd += [target]

    if not module.check_mode:
        rc, stdout, stderr = module.run_command(cmd)
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr
        if rc != 0:
            results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
            results['status'][target] = 'FAILURE'
            return False

        results['meta'][target]['messages'].append('Backup {0} has been restored.'.format(name))
        results['status'][target] = 'SUCCESS'
        results['changed'] = True
    else:
        results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    # Remove NIM resources?
    if params['remove_spot']:
        cmd = ['nim', '-o', 'remove', spot_name]
        if not module.check_mode:
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                results['meta'][target]['stdout'] = stdout
                results['meta'][target]['stderr'] = stderr
                results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
                results['status'][target] = 'FAILURE'
                return False

            results['meta'][target]['messages'].append('SPOT resource {0} has been removed.'.format(spot_name))
        else:
            results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    if params['remove_backup']:
        cmd = ['nim', '-o', 'remove', name]
        if not module.check_mode:
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                results['meta'][target]['stdout'] = stdout
                results['meta'][target]['stderr'] = stderr
                results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
                results['status'][target] = 'FAILURE'
                return False

            results['meta'][target]['messages'].append('Backup {0} has been removed.'.format(name))
        else:
            results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    return True


@start_threaded(THRDS)
def nim_iosbackup_create(module, target, params):
    """
    Perform a define NIM operation to create a backup of a VIOS (ios_backup)

    arguments:
        module  (dict): the module variable
        target   (str): the VIOS NIM Client to backup
        params  (dict): the NIM command parameters
    note:
        set results['status'][target] with the status
    return:
        True if restore succeeded or skipped
        False otherwise
    """
    global results

    name = build_name(target, params['name'], params['name_prefix'], params['name_postfix'])

    # compute backup location
    if not os.path.exists(params['location']):
        os.makedirs(params['location'])
    location = os.path.join(params['location'], name)

    # nim -Fo define -t ios_backup -a mk_image=yes -a server=master
    #  -a source=<vios> -a location=/export/nim/ios_backup/<vio>_ios_backup <vios>_ios_backup
    cmd = ['nim', '-Fo', 'define', '-t', 'ios_backup', '-a', 'mk_image=yes', '-a', 'server=master']
    cmd += ['-a', 'source={0}'.format(target)]
    cmd += ['-a', 'location={0}'.format(location), name]
    if not module.check_mode:
        rc, stdout, stderr = module.run_command(cmd)
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr
        if rc != 0:
            results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
            results['status'][target] = 'FAILURE'
            return False

        results['meta'][target]['messages'].append('ios_backup {0} created: {1}.'.format(name, location))
        results['meta'][target]['res_name'] = name
        results['status'][target] = 'SUCCESS'
        results['changed'] = True
    else:
        results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    return True


@start_threaded(THRDS)
def nim_iosbackup_restore(module, target, params):
    """
    Perform a viosbr NIM operation to resote a VIOS backup

    arguments:
        module  (dict): the module variable
        target   (str): the VIOS NIM Client to restore the backup on
        params  (dict): the NIM command parameters
    note:
        Set results['status'][target] with the status
    return:
        True if restore succeeded or skipped
        False otherwise
    """
    global results
    name = build_name(target, params['name'], params['name_prefix'], params['name_postfix'])

    # nim -Fo viosbr -a ios_backup=ios_backup_<vios> <vios>
    cmd = ['nim', '-Fo', 'viosbr']
    cmd += ['-a', 'ios_backup={0}'.format(name), target]
    if not module.check_mode:
        rc, stdout, stderr = module.run_command(cmd)
        results['meta'][target]['stdout'] = stdout
        results['meta'][target]['stderr'] = stderr
        if rc != 0:
            results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
            results['status'][target] = 'FAILURE'
            return False

        results['meta'][target]['messages'].append('Backup {0} has been restored.'.format(name))
        results['status'][target] = 'SUCCESS'
        results['changed'] = True
    else:
        results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    if params['remove_backup']:
        cmd = ['nim', '-o', 'remove', name]
        if not module.check_mode:
            rc, stdout, stderr = module.run_command(cmd)
            results['meta'][target]['stdout'] = stdout
            results['meta'][target]['stderr'] = stderr
            if rc != 0:
                results['meta'][target]['messages'].append('Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc))
                results['status'][target] = 'FAILURE'
                return False

            results['meta'][target]['messages'].append('Backup {0} has been removed.'.format(name))
        else:
            results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    return True


def nim_list_backup(module, target, type, params):
    """
    Perform a viosbr NIM operation to resote a VIOS backup

    arguments:
        module  (dict): the module variable
        type     (str): the type of the object to list
        target  (list): the NIM Clients to filter backup list
        params  (dict): the NIM command parameters
    return:
        backup_info (dict): the backups information
    """
    global results

    backup_info = {}
    if module.params['name']:
        cmd = ['lsnim', '-l', module.params['name']]
        rc, stdout, stderr = module.run_command(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        if rc != 0:
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
            module.fail_json(**results)

        results['msg'] = 'List backup completed successfully.'
        backup_info.update(build_dict(module, stdout))
        return backup_info

    backup_info.update(get_nim_type_info(module, type))

    # Filter results
    for backup in backup_info.copy():
        # Filter results based on targets
        if target and 'source_image' not in backup_info[backup] or backup_info[backup]['source_image'] not in target:
            del backup_info[backup]
            continue

        # Filter results based on oslevel
        if params['oslevel'] and 'oslevel_s' in backup_info[backup] and params['oslevel'] not in backup_info[backup]['oslevel_s']:
            del backup_info[backup]
            continue

        # Filter results based on prefix/postfix
        if params['name_prefix'] and params['name_prefix'] not in backup:
            del backup_info[backup]
            continue
        if params['name_postfix'] and params['name_postfix'] not in backup:
            del backup_info[backup]
            continue

    return backup_info


def nim_view_backup(module, params):
    """
    List a VIOS backup and perform a viosbr NIM operation to view its content

    arguments:
        module  (dict): the module variable
        params  (dict): the NIM command parameters
    note:
        Set results['status'][target] with the status
        Exits with fail_json in case of error
    """
    global results

    cmd = ['lsnim', '-l', params['name']]
    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if rc != 0:
        results['msg'] = 'NIM resource \'{0}\' not found.'.format(params['name'])
        module.fail_json(**results)

    results.update({'backup_info': build_dict(module, stdout)})

    if 'source_image' not in results['backup_info'][params['name']]:
        results['msg'] = 'Attribute \'source_image\' not found in ios_backup resource {0}.'.format(params['name'])
        module.fail_json(**results)
    target = results['backup_info'][params['name']]['source_image']

    # nim -Fo viosbr -a viosbr_action=view -a ios_backup=quimby-vios1_iosb quimby-vios1
    cmd = ['nim', '-Fo', 'viosbr', '-a', 'viosbr_action=view']
    cmd += ['-a', 'ios_backup={0}'.format(params['name']), target]
    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if rc != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.fail_json(**results)

    results['status'][target] = 'SUCCESS'


def main():
    global module
    global results

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(required=True, type='str', choices=['create', 'restore', 'view', 'list']),
            type=dict(type='str', choices=['mksysb', 'ios_mksysb', 'ios_backup'], default='mksysb'),
            targets=dict(type='list', elements='str'),
            nim_node=dict(type='dict'),
            location=dict(type='path'),
            name=dict(type='str'),
            name_prefix=dict(type='str'),
            name_postfix=dict(type='str'),
            group=dict(type='str'),
            spot_name=dict(type='str'),
            spot_prefix=dict(type='str'),
            spot_postfix=dict(type='str', default='_spot'),
            spot_location=dict(type='path', default='/export/nim/spot'),
            remove_spot=dict(type='bool', default=True),
            remove_backup=dict(type='bool', default=False),
            boot_target=dict(type='bool', default=True),
            accept_licenses=dict(type='bool', default=True),
            oslevel=dict(type='str'),
        ),
        required_if=[
            ['action', ['view'], ['name']],
        ],
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        meta={'messages': []},
        # meta structure will be updated as follow:
        # meta={
        #   target_name:{
        #       'messages': [],     detail execution messages
        #       'res_name': '',     resource name create for backup creation
        #       'stdout': '',
        #       'stderr': '',
        #   }
        # }
        nim_node={},
        status={},
    )

    action = module.params['action']
    objtype = module.params['type']
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    # Build nim node info
    if module.params['nim_node']:
        results['nim_node'] = module.params['nim_node']
    build_nim_node(module)

    # check targets are valid NIM clients
    targets = []
    if module.params['targets']:
        targets = expand_targets(module.params['targets'])
    if not targets and action != 'list' and action != 'view':
        results['msg'] = 'Empty target list, please check their NIM states and they are reacheable.'
        module.log('Warning: Empty target list: "{0}"'.format(targets))
        module.exit_json(**results)

    for target in targets:
        results['status'][target] = ''  # first time init
        results['meta'][target] = {'messages': []}  # first time init

    # compute parameters & default value
    params = {}
    params['name'] = module.params['name']
    params['name_prefix'] = module.params['name_prefix']
    params['name_postfix'] = module.params['name_postfix']
    params['location'] = module.params['location']
    if objtype == 'mksysb':
        if not params['name'] and module.params['name_postfix'] is None:
            params['name_postfix'] = '_sysb'
        if not module.params['location']:
            params['location'] = '/export/nim/mksysb'

    elif objtype == 'ios_mksysb':
        if not params['name'] and module.params['name_postfix'] is None:
            params['name_postfix'] = '_sysb'
        if not module.params['location']:
            params['location'] = '/export/nim/ios_mksysb'

    elif objtype == 'ios_backup':
        if not params['name'] and module.params['name_postfix'] is None:
            params['name_postfix'] = '_iosb'
        if not module.params['location']:
            params['location'] = '/export/nim/ios_backup'

    if action == 'list':
        params['oslevel'] = module.params['oslevel']
        nim_list_backup(module, targets, objtype, params)

    elif action == 'view':
        nim_view_backup(module, params)

    elif action == 'create':
        for target in targets:
            if target in results['nim_node']['standalone']:
                if objtype != 'mksysb':
                    results['meta'][target]['messages'].append('Cannot {0} {1} on a standalone machine.'.format(action, type))
                    results['status'][target] = 'FAILURE'
                    continue

                nim_mksysb_create(module, target, objtype, params)

            elif target in results['nim_node']['vios']:
                if objtype == 'mksysb':
                    results['meta'][target]['messages'].append('Cannot {0} {1} on a VIOS.'.format(action, type))
                    results['status'][target] = 'FAILURE'
                    continue

                if objtype == 'ios_mksysb':
                    nim_mksysb_create(module, target, objtype, params)

                if objtype == 'ios_backup':
                    nim_iosbackup_create(module, target, params)
        wait_all()

    elif action == 'restore':
        for target in targets:

            if target in results['nim_node']['standalone'] and objtype != 'mksysb':
                results['meta'][target]['messages'].append('Cannot {0} {1} on a standalone machine.'.format(action, type))
                results['status'][target] = 'FAILURE'
                continue
            if target in results['nim_node']['vios'] and objtype == 'mksysb':
                results['meta'][target]['messages'].append('Cannot {0} {1} on a VIOS.'.format(action, type))
                results['status'][target] = 'FAILURE'
                continue

            if 'mksysb' in objtype:
                params['group'] = module.params['group']
                params['spot_name'] = module.params['spot_name']
                if not params['spot_name']:
                    params['spot_prefix'] = module.params['spot_prefix']
                    params['spot_postfix'] = module.params['spot_postfix']
                else:
                    params['spot_prefix'] = None
                    params['spot_postfix'] = None
                params['spot_location'] = module.params['spot_location']
                params['remove_spot'] = module.params['remove_spot']
                params['accept_licenses'] = module.params['accept_licenses']
                params['boot_target'] = module.params['boot_target']
                params['remove_backup'] = module.params['remove_backup']

                nim_mksysb_restore(module, target, params)

            else:
                nim_iosbackup_restore(module, target, params)

        wait_all()

    # Exit
    target_errored = [key for key, val in results['status'].items() if 'FAILURE' in val]
    if len(target_errored):
        results['msg'] = "NIM backup {0} operation failed for {1}. See status and meta for details.".format(action, target_errored)
    else:
        results['msg'] = 'NIM backup {0} operation successfull. See status and meta for details.'.format(action)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
