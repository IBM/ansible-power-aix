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
module: nim_viosupgrade
short_description: Perform an upgrade with the viosupgrade tool
description:
- Tool to upgrade VIOSes in NIM environment.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform.
    - C(bosinst) to perform and bosinst installation.
    - C(altdisk) to perform and alternate disk installation.
    - C(get_status) to get the status of the upgrade.
    type: str
    choices: [ altdisk, bosinst, get_status ]
    required: true
  targets:
    description:
    - NIM targets.
    type: list
    elements: str
  target_file:
    description:
    - Specifies the file name that contains the list of VIOS nodes.
    - The values and fields in the file must be specified in a particular sequence and format. The
      details of the format are specified in the /usr/samples/nim/viosupgrade.inst file and they
      are comma-separated. The maximum number of nodes that can be installed through the -f option
      is 30.
    - The VIOS images are installed on the nodes simultaneously.
    - For an SSP cluster, the viosupgrade command must be run on individual nodes. Out of the n
      number of nodes in the SSP cluster, maximum n-1 nodes can be upgraded at the same time.
      Hence, you must ensure that at least one node is always active in the cluster and is not part
      of the upgrade process.
    type: str
  mksysb_name:
    description:
    - mksysb name.
    type: dict
  spot_name:
    description:
    - SPOT name.
    type: dict
  backup_file:
    description:
    - Specifies the resource name of the VIOS configuration backup file.
    type: dict
  rootvg_clone_disk:
    description:
    - Clone disk name.
    type: dict
  rootvg_install_disk:
    description:
    - Install disk name.
    type: dict
  res_resolv_conf:
    description:
    - NIM resolv_conf resource name.
    type: dict
  res_script:
    description:
    - NIM script resource name.
    type: dict
  res_fb_script:
    description:
    - NIM fb_script resource name.
    type: dict
  res_file_res:
    description:
    - NIM file_res resource name.
    type: dict
  res_image_data:
    description:
    - NIM image_data resource name.
    type: dict
  res_log:
    description:
    - NIM log resource name.
    type: dict
  manage_cluster:
    description:
    - Specifies that cluster-level backup and restore operations are performed.
    - The -c flag is mandatory for the VIOS that is part of an SSP cluster.
    type: bool
    default: no
  preview:
    description:
    - Validates whether VIOS hosts are ready for the installation.
    - It must be specified only for validation and can be used for preview of the installation
      image only.
    type: bool
    default: no
  skip_rootvg_cloning:
    description:
    - Skips the cloning of current rootvg disks to alternative disks and continues with the VIOS
      installation on the current rootvg disk.
    - If the storage disks are not available, you can specify the -s flag to continue with the
      installation.
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
  - See IBM documentation about requirements for the viosupgrade command.
'''

EXAMPLES = r'''
- name: Perform an upgrade of nimvios01
  nim_viosupgrade:
    targets: nimvios01
    action: altdisk
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
nim_node:
    description: NIM node info.
    returned: always
    type: dict
status:
    description:
    - Status for each VIOS (dicionnary key).
    - When C(target_file) is set, then the key is 'all'.
    returned: always
    type: dict
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
import csv
import distutils.util
import socket

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule

# TODO Later, check SSP support (option -c of viosupgrade)
# TODO Later, check mirrored rootvg support for upgrade & upgrade all in one
# TODO Could we tune more precisly CHANGED (stderr parsing/analysis)?
# TODO Skip operation if vios_status is defined and not SUCCESS, set the vios_status after operation
# TODO a time_limit could be used in status to loop for a period of time (might want to add parameter for sleep period)


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


# TODO: test viosupgrade_query
def viosupgrade_query(module):
    """
    Query to get the status of the upgrade for each target
    runs: viosupgrade -q [-n hostname | -f filename] }

    args:
        module        (dict): The Ansible module

    module.param used:
        target_file   (optional) filename with targets info
        targets       (required if not target_file)

    note:
        set results['status'][target] with the status

    return:
        ret     (int) the number of error
    """
    ret = 0

    cmd = ['/usr/sbin/viosupgrade', '-q']
    if module.param['target_file']:
        cmd += ['-f', module.param['target_file']]

        rc, stdout, stderr = module.run_command(cmd)

        results['changed'] = True  # don't really know
        results['cmd'] = ' '.join(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr

        if rc == 0:
            msg = 'Command \'{0}\' successful'.format(' '.join(cmd))
        else:
            msg = 'Command \'{0}\' failed with rc: {1}'.format(' '.join(cmd), rc)
            ret += 1
        module.log(msg)
        results['meta']['messages'].append(msg)
    else:
        for vios in module.param['targets']:
            cmd += ['-n', vios]
            rc, stdout, stderr = module.run_command(cmd)

            results['changed'] = True  # don't really know
            results['cmd'] = ' '.join(cmd)
            results['meta'][vios]['stdout'] = stdout
            results['meta'][vios]['stderr'] = stderr
            if rc == 0:
                msg = 'Command \'{0}\' successful: {1}'.format(' '.join(cmd), stdout)
                results['status'][vios] = 'SUCCESS'
            else:
                msg = 'Command \'{0}\' failed with rc: {1}'.format(' '.join(cmd), rc)
                ret += 1
            module.log(msg)
            results['meta'][vios]['messages'].append(msg)
            results['status'][vios] = 'FAILURE'
    return ret


# TODO: test viosupgrade
def viosupgrade(module):
    """
    Upgrade each VIOS specified in the provided file
    runs one of:
        viosupgrade -t bosinst -n hostname -m mksysb_name -p spotname
                    {-a rootvg_vg_clone_disk | -r rootvg_inst_disk | -s}
                    [-b backupFile] [-c] [-v]
        viosupgrade -t altdisk -n hostname -m mksysb_name
                    -a rootvg_vg_clone_disk [-b backup_file] [-c] [-v]
        viosupgrade -t {bosinst | altdisk} -f [filename] [-v]

    args:
        module        (dict): The Ansible module

    module.param used:
        target_file   (optional) filename with targets info
        targets       (required if not target_file)
        resources     resource require to run the command

    note:
        set results['status'][target] with the status
        when target_file is set, the key is 'all'

    return:
        ret     (int) the number of error
    """
    global results
    ret = 0

    cmd = '/usr/sbin/viosupgrade'

    if module.param['target_file']:
        if 'altdisk' in module.param['action']:
            cmd += ' -t altdisk'
        elif 'bosinst' in module.param['action']:
            cmd += ' -t bosinst'
        cmd += ['-f', module.param['target_file']]

        rc, stdout, stderr = module.run_command(cmd)

        results['changed'] = True  # don't really know
        results['cmd'] = ' '.join(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr

        if rc == 0:
            msg = 'Command \'{0}\' successful'.format(' '.join(cmd))
            results['status']['all'] = 'SUCCESS'
        else:
            msg = 'Command \'{0}\' failed with rc: {1}'.format(' '.join(cmd), rc)
            ret += 1
            results['status']['all'] = 'FAILURE'
        module.log(msg)
        results['meta']['messages'].append(msg)
        return ret

    for vios in module.param['targets']:
        if 'altdisk' in module.param['action']:
            cmd += ' -t altdisk'
        elif 'bosinst' in module.param['action']:
            cmd += ' -t bosinst'

        # get the fqdn hostname because short hostname can match several NIM objects
        # and require user input to select the right one.
        target_fqdn = socket.getfqdn(vios)
        cmd += ['-n ', target_fqdn]

        if vios in module.param['mksysb_name']:
            cmd += ' -m ' + module.param['mksysb_name'][vios]
        elif 'all' in module.param['mksysb_name']:
            cmd += ' -m ' + module.param['mksysb_name']['all']

        if vios in module.param['spot_name']:
            cmd += ' -p ' + module.param['spot_name'][vios]
        elif 'all' in module.param['spot_name']:
            cmd += ' -p ' + module.param['spot_name']['all']

        if vios in module.param['rootvg_clone_disk']:
            cmd += ' -a ' + module.param['rootvg_clone_disk'][vios]
        elif 'all' in module.param['rootvg_clone_disk']:
            cmd += ' -a ' + module.param['rootvg_clone_disk']['all']

        if vios in module.param['rootvg_install_disk']:
            cmd += ' -r ' + module.param['rootvg_install_disk'][vios]
        elif 'all' in module.param['rootvg_install_disk']:
            cmd += ' -r ' + module.param['rootvg_install_disk']['all']

        if vios in module.param['skip_rootvg_cloning']:
            if distutils.util.strtobool(module.param['skip_rootvg_cloning'][vios]):
                cmd += ' -s'
        elif 'all' in module.param['skip_rootvg_cloning']:
            if distutils.util.strtobool(module.param['skip_rootvg_cloning']['all']):
                cmd += ' -s'

        if vios in module.param['backup_file']:
            cmd += ' -b ' + module.param['backup_file'][vios]
        elif 'all' in module.param['backup_file']:
            cmd += ' -b ' + module.param['backup_file']['all']

        if vios in module.param['manage_cluster']:
            if distutils.util.strtobool(module.param['manage_cluster'][vios]):
                cmd += ' -c'
        elif 'all' in module.param['manage_cluster']:
            if distutils.util.strtobool(module.param['manage_cluster']['all']):
                cmd += ' -c'

        if vios in module.param['preview']:
            if distutils.util.strtobool(module.param['preview'][vios]):
                cmd += ' -v'
        elif 'all' in module.param['preview']:
            if distutils.util.strtobool(module.param['preview']['all']):
                cmd += ' -v'

        supported_res = ['res_resolv_conf', 'res_script', 'res_fb_script',
                         'res_file_res', 'res_image_data', 'res_log']
        for res in supported_res:
            if vios in module.param[res]:
                cmd += ' -e {0}:{1}'.format(res, module.param[res][vios])
            elif 'all' in module.param[res]:
                cmd += ' -e {0}:{1}'.format(res, module.param[res]['all'])

        # run the command
        rc, stdout, stderr = module.run_command(cmd)

        results['changed'] = True  # don't really know
        results['cmd'] = ' '.join(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr

        if rc == 0:
            module.log("[STDERR] {0}".format(stderr))
            results['status'][vios] = 'SUCCESS'
        else:
            module.log("command {0} failed: {1}".format(cmd, stderr))
            ret += 1
            results['status'][vios] = 'FAILURE'

    return ret


###################################################################################

def main():
    global module
    global results

    module = AnsibleModule(
        # TODO: remove not needed attributes
        argument_spec=dict(
            # description=dict(required=False, type='str'),

            # IBM automation generic attributes
            action=dict(required=True, type='str',
                        choices=['altdisk', 'bosinst', 'get_status']),
            vios_status=dict(type='dict'),
            nim_node=dict(type='dict'),

            # mutually exclisive
            targets=dict(type='list', elements='str'),
            target_file=dict(type='str'),

            # following attributes are dictionaries with
            # key: 'all' or hostname and value: a string
            # example:
            # mksysb_name={"tgt1": "hdisk1", "tgt2": "hdisk1"}
            # mksysb_name={"all": "hdisk1"}
            mksysb_name=dict(type='dict'),
            spot_name=dict(type='dict'),
            backup_file=dict(type='dict'),
            rootvg_clone_disk=dict(type='dict'),
            rootvg_install_disk=dict(type='dict'),
            # Resources (-e option):
            res_resolv_conf=dict(type='dict'),
            res_script=dict(type='dict'),
            res_fb_script=dict(type='dict'),
            res_file_res=dict(type='dict'),
            res_image_data=dict(type='dict'),
            res_log=dict(type='dict'),

            # dictionaries with key: 'all' or hostname and value: bool
            manage_cluster=dict(type='bool', default=False),
            preview=dict(type='bool', default=False),
            skip_rootvg_cloning=dict(type='bool', default=False),
        ),
        mutually_exclusive=[['targets', 'target_file']],
        # TODO: determine mandatory attributes
        required_if=[],
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
        #   target:{
        #       'messages': [],
        #       'stdout': '',
        #       'stderr': '',
        #   }
        # }
        nim_node={},
        status={},
    )

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    param_one_of(['installp_bundle', 'filesets'])

    module.debug('*** START NIM VIOSUPGRADE OPERATION ***')

    # build NIM node info (if needed)
    refresh_nim_node(module, 'vios')

    # get targests and check they are valid NIM clients
    if module.params['target_file']:
        try:
            myfile = open(module.params['target_file'], 'r')
            csvreader = csv.reader(myfile, delimiter=':')
            for line in csvreader:
                results['targets'].append(line[0].strip())
            myfile.close()
        except IOError as e:
            msg = 'Failed to parse file {0}: {1}. Check the file content is '.format(e.filename, e.strerror)
            module.log(msg)
            module.fail_json(**results)
    else:
        results['targets'] = module.params['targets']

    if not results['targets']:
        module.log('Warning: Empty target list, targets: \'{0}\''.format(module.params['targets']))
        results['msg'] = 'Empty target list, please check their NIM states and they are reacheable.'
        module.exit_json(**results)

    results['targets'] = check_vios_targets(module, module.params['targets'])

    module.debug('Target list: {0}'.format(results['targets']))

    # initialize the results dictionary for target tuple keys
    for vios in results['targets']:
        results['status'][vios] = ''
        results['meta'][vios] = {'messages': []}

    # perfom the operation
    if 'get_status' in module.params['action']:
        viosupgrade_query(module)
    else:
        viosupgrade(module)

    # # Prints status for each targets
    # nb_error = 0
    # msg = 'VIOSUpgrade {0} operation status:'.format(module.params['action'])
    # if module.status:
    #     OUTPUT.append(msg)
    #     module.log(msg)
    #     for vios_key in module.status:
    #         OUTPUT.append('    {0} : {1}'.format(vios_key, module.status[vios_key]))
    #         module.log('    {0} : {1}'.format(vios_key, module.status[vios_key]))
    #         if not re.match(r"^SUCCESS", module.status[vios_key]):
    #             nb_error += 1
    # else:
    #     module.log(msg + ' module.status table is empty')
    #     OUTPUT.append(msg + ' Error getting the status')
    #     module.status = module.params['vios_status']  # can be None

    # # Prints a global result statement
    # if nb_error == 0:
    #     msg = 'VIOSUpgrade {0} operation succeeded'\
    #           .format(module.params['action'])
    #     OUTPUT.append(msg)
    #     module.log(msg)
    # else:
    #     msg = 'VIOSUpgrade {0} operation failed: {1} errors'\
    #           .format(module.params['action'], nb_error)
    #     OUTPUT.append(msg)
    #     module.log(msg)

    # # =========================================================================
    # # Exit
    # # =========================================================================
    # if nb_error == 0:
    #     module.exit_json(**results)

    module.fail_json(**results)


if __name__ == '__main__':
    main()
