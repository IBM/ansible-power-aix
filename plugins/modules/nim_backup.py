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
- It uses the NIM define ooperation it creates mksysb or ios_backup resource on the NIM master
  depending on the type of the client.
- It lists the backup resources available on the NIM master and allows to filter results.
- It uses the NIM bos_inst and viosbr to restore backup on LPAR or VIOS clients.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Controls what is performed.
    - C(backup) performs an backup operation on targets trough NIM master
    - C(restore) restores a backup on targets trough NIM master
    - C(list) lists backups for targets on the NIM master
    type: str
    choices: [ backup, restore, list ]
    required: yes
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - Required if I(action=backup) and I(action=restore).
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
    - Specifies where ot put the backup files on the NIM master.
    - If not specified default for LPAR targets is I(location=/export/mksysb) and for
      VIOS targets it is I(location=/export/nim/ios_backup).
    - Required if I(action=backup) and I(action=restore).
    type: path
  name:
    description:
    - Exact name of the backup NIM resource to act on.
    - If I(action=list) it filters the results on the name of the NIM resource.
    type: str
  name_prefix:
    description:
    - Prefix of the backup NIM resource name to act on.
    - The name format will be I(<prefix><target_name><postfix>).
    - If I(action=list) it filters the results on the name of the NIM resource.
    type: str
  name_postfix:
    description:
    - Specifies the postfix of the backup NIM resource name to act on.
    - If not specified default for LAPR targets is I(name_postfix=_sysb) and for
      VIOS targets it is I(name_postfix=_iosb).
    - The name format will be I(<prefix><target_name><postfix>).
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
    - Can be used on a standalone client if I(action=restore).
    type: str
  spot_postfix:
    description:
    - Specifies the prostfix of SPOT resource name created to restore the backup on a standalone client.
    - If not specified default is I(spot_postfix=_spot).
    - The SPOT name format will be I(<spot_prefix><target_name><spot_postfix>).
    - Can be used on a standalone client if I(action=restore).
    type: str
  spot_location:
    description:
    - Specifies the location of SPOT resource on the NIM master created to restore the backup on a standalone client.
    - If not specified default is I(spot_location=/export/spot).
    - Can be used on a standalone client if I(action=restore).
    type: path
  oslevel:
    description:
    - Specifies the oslevel to filter results.
    - Can be used if I(action=list).
    type: str
  remove_spot:
    description: Specifies to remove the SPOT resource created to restore the backup on a standalone client.
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
- name: List backup resource targeting nimmclient1 at a specific level and name starting with ansible
  nim_backup:
    action: list
    targets: nimmclient1
    oslevel: "7200-03-02"
    name_prefix: ansible

- name: Create a mksysb backup of a LPAR
  nim_backup:
    action: backup
    targets: nimmclient1
    name_postfix: _mksysb
    spot_postfix: _spot
    remove_spot: yes
    boot_target: no
    accept_licenses: yes
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
    description: Satus of the operation for each C(target). It can be empty, SUCCESS or FAILURE.
    returned: always
    type: dict
    elements: str
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
                    "type": "standalone"
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
                    "type": "vios"
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
    Build nim_node dictionary containing nim clients info and lpp sources info.
    """
    global results

    types = ['standalone', 'vios']
    for type in types:
        results['nim_node'].update({type: get_nim_type_info(module, type)})


def get_nim_type_info(module, type):
    """
    Build the hash of nim client of type=lpar_type defined on the
           nim master and their associated key = value information.

    arguments:
        module      (dict): The Ansible module
    return:
        info_hash   (dict): hash information from the nim clients
    """
    global results

    cmd = ['lsnim', '-t', type, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Cannot get NIM Client information. Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.fail_json(**results)

    info_hash = {}
    for line in stdout.rstrip().split('\n'):
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            info_hash[obj_key]['type'] = type
            continue

        match_key = re.match(r"^\s+(\S+)\s+=\s+(.*)$", line)
        if match_key:
            info_hash[obj_key][match_key.group(1)] = match_key.group(2)
            continue

    return info_hash


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
            continue

        # Build target(s) from: quimby05 quimby08 quimby12
        if target in results['nim_node']['standalone'] or target in results['nim_node']['vios']:
            clients.append(target)

    return list(set(clients))


def build_name(target, name, prefix, postfix):
    """
    Build the name , if set returns params['name'],
    otherwise name will be formatted as: <prefix><target><postfix>

    args:
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
def nim_standalone_backup(module, target, params):
    """
    Perform a NIM define operation to create a backup of a LPAR

    args:
        module  (dict): the module variable
        target   (str): the standalone NIM Client to backup
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
    # nim -o define -t mksysb -a server=master -a location=file_path -a mk_image=yes  -a source=target mksysb_name
    # location default?
    # To ignore space requirements use the "-F" flag when defining the mksysb resource.
    cmd = ['nim', '-o', 'define', '-t', 'mksysb', '-a', 'server=master', '-a', 'mk_image=yes']
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

        results['meta'][target]['messages'].append('mksysb {0} created: {1}.'.format(name, location))
        results['meta'][target]['res_name'] = name
        results['status'][target] = 'SUCCESS'
        results['changed'] = True
    else:
        results['meta'][target]['messages'].append('Command \'{0}\' has no preview mode, execution skipped.'.format(' '.join(cmd)))

    return True


@start_threaded(THRDS)
def nim_standalone_restore(module, target, params):
    """
    Perform a bos_inst NIM operation to restore a LPAR backup

    args:
        module  (dict): the module variable
        target   (str): the standalone NIM Client to restore the backup on
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
def nim_viosbr_create(module, target, params):
    """
    Perform a define NIM operation to create a backup of a VIOS (ios_backup)

    args:
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
        if rc != 0:
            results['meta'][target]['stdout'] = stdout
            results['meta'][target]['stderr'] = stderr
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
def nim_viosbr_restore(module, target, params):
    """
    Perform a viosbr NIM operation to resote a VIOS backup

    args:
        module  (dict): the module variable
        target   (str): the VIOS NIM Client to restore the backup on
        params  (dict): the NIM command parameters
    note:
        set results['status'][target] with the status
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
        if rc != 0:
            results['meta'][target]['stdout'] = stdout
            results['meta'][target]['stderr'] = stderr
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


def get_nim_info(module, stdout):
    """
    Build dictionary with the NIM info
    args:
        module  (dict): The Ansible module
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


def nim_list_backup(module, target, params):
    """
    Perform a viosbr NIM operation to resote a VIOS backup

    args:
        module  (dict): the module variable
        target  (list): the NIM Clients to filter backup list
        params  (dict): the NIM command parameters
    return:
        backup_info (dict): the backups information
    """
    global results

    # lsnim -l -t mksysb
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
        backup_info.update(get_nim_info(module, stdout))

    else:
        cmd = ['lsnim', '-l', '-t', 'mksysb']
        rc, stdout, stderr = module.run_command(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        if rc != 0:
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
            module.fail_json(**results)

        backup_info.update(get_nim_info(module, stdout))

        cmd = ['lsnim', '-l', '-t', 'ios_backup']
        rc, stdout, stderr = module.run_command(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        if rc != 0:
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
            module.fail_json(**results)

        backup_info.update(get_nim_info(module, stdout))

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


def main():
    global module
    global results

    module = AnsibleModule(
        supports_check_mode=True,
        argument_spec=dict(
            action=dict(required=True, type='str', choices=['backup', 'restore', 'list']),
            targets=dict(required=False, type='list', elements='str'),
            nim_node=dict(required=False, type='dict'),
            location=dict(type='path'),
            name=dict(type='str'),
            name_prefix=dict(type='str'),
            name_postfix=dict(type='str'),
            group=dict(type='str'),
            spot_name=dict(type='str'),
            spot_prefix=dict(type='str'),
            spot_postfix=dict(type='str'),
            spot_location=dict(type='path'),
            remove_spot=dict(type='bool', default=True),
            remove_backup=dict(type='bool', default=False),
            boot_target=dict(type='bool', default=True),
            accept_licenses=dict(type='bool', default=True),
            oslevel=dict(type='str'),
        ),
        required_if=[
            ['action', ['backup', 'restore'], ['location', 'name']],
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
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    # Build nim node info
    if module.params['nim_node']:
        results['nim_node'] = module.params['nim_node']
    build_nim_node(module)

    # check targets are valid NIM clients
    if module.params['targets']:
        targets = expand_targets(module.params['targets'])

    for target in targets:
        results['status'][target] = ''  # first time init
        results['meta'][target] = {'messages': []}  # first time init

    params = {}
    if action == 'backup':
        for target in targets:
            params['name'] = module.params['name']
            params['name_prefix'] = module.params['name_prefix']
            if target in results['nim_node']['standalone']:
                if not params['name'] and not module.params['name_postfix']:
                    params['name_postfix'] = '_sysb'
                else:
                    params['name_postfix'] = module.params['name_postfix']
                if not module.params['location']:
                    params['location'] = '/export/mksysb'
                else:
                    params['location'] = module.params['location']

                nim_standalone_backup(module, target, params)
            else:
                if not params['name'] and not module.params['name_postfix']:
                    params['name_postfix'] = '_iosb'
                else:
                    params['name_postfix'] = module.params['name_postfix']
                if not module.params['location']:
                    params['location'] = '/export/nim/ios_backup'
                else:
                    params['location'] = module.params['location']

                nim_viosbr_create(module, target, params)
        wait_all()

    elif action == 'restore':
        for target in targets:
            params['name'] = module.params['name']
            params['name_prefix'] = module.params['name_prefix']
            params['remove_backup'] = module.params['remove_backup']
            if target in results['nim_node']['standalone']:
                if not params['name'] and not module.params['name_postfix']:
                    params['name_postfix'] = '_sysb'
                else:
                    params['name_postfix'] = module.params['name_postfix']
                params['group'] = module.params['group']
                params['spot_name'] = module.params['spot_name']
                params['spot_prefix'] = module.params['spot_prefix']
                if not params['spot_name'] and not module.params['spot_postfix']:
                    params['name_postfix'] = '_spot'
                else:
                    params['spot_postfix'] = module.params['spot_postfix']
                if not module.params['spot_location']:
                    params['spot_location'] = '/export/spot'
                else:
                    params['spot_location'] = module.params['spot_location']
                params['remove_spot'] = module.params['spot_postfix']
                params['accept_licenses'] = module.params['accept_licenses']
                params['boot_target'] = module.params['boot_target']

                nim_standalone_restore(module, target, params)
            else:
                if not params['name'] and not module.params['name_postfix']:
                    params['name_postfix'] = '_iosb'
                else:
                    params['name_postfix'] = module.params['name_postfix']
                nim_viosbr_restore(module, target, params)
        wait_all()

    elif action == 'list':
        params['name'] = module.params['name']
        params['name_prefix'] = module.params['name_prefix']
        params['name_postfix'] = module.params['name_postfix']
        params['oslevel'] = module.params['oslevel']
        results['backup_info'] = nim_list_backup(module, targets, params)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
