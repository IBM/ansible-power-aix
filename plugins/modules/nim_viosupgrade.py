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
    - C(altdisk_install) to perform and alternate disk install.
    - C(alt_disk_clean) to cleanup an existing alternate disk install.
    - C(get_status) to get the status of the upgrade.
    type: str
    choices: [ altdisk_install, bos_install, get_status ]
    required: true
  vars:
    description:
    - Specifies additional parameters.
    type: dict
  vios_status:
    description:
    - Specifies the result of a previous operation.
    type: dict
  targets:
    description:
    - NIM targets.
    type: list
    elements: str
  target_file_name:
    description:
    - File name containing NIM targets in CSV format.
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
    - Backup file name.
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
  cluster_exists:
    description:
    - Check if cluster exists.
    type: dict
  validate_input_data:
    description:
    - Validate input data.
    type: dict
  skip_rootvg_cloning:
    description:
    - Skip rootvg cloning.
    type: dict
'''

EXAMPLES = r'''
- name: Perform an upgrade of nimvios01
  nim_viosupgrade:
    targets: nimvios01
    action: altdisk_install
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
    description: Status for each VIOS (dicionnary key).
    returned: always
    type: dict
'''

import csv
import distutils.util

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule


# TODO: -----------------------------------------------------------------------------
# TODO: Later, check SSP support (option -c of viosupgrade)
# TODO: Later, check mirrored rootvg support for upgrade & upgrade all in one
# TODO: Check if all debug section (TBC) are commented before commit
# TODO: Check flake8 complaints
# TODO: Add this module usage in README.md file
# TODO: -----------------------------------------------------------------------------
# TODO: Add message in OUTPUT
# TODO: Can we tune more precisly CHANGED (stderr parsing/analysis)?
# TODO: Skip operation if vios_status is defined and not SUCCESS, set the vios_status after operation
# TODO: Do we support viosupgrade without NIM environment (executed on the VIOS itself)? in another module?
# TODO: a time_limit could be used in get_status to loop for a period of time (might want to add parameter for sleep period)
# TODO: nim_migvios_setup not supported yet?
# TODO: -----------------------------------------------------------------------------

CHANGED = False


# TODO: test viosupgrade_query
def viosupgrade_query(module):
    """
    Query to get the status of the upgrade for each target
    runs: viosupgrade -q { [-n hostname | -f filename] }

    The caller must ensure either the filename or the target list is set.

    args:
        module  the Ansible module

    module.param used:
        target_file_name   (optional) filename with targets info
        targets            (required if not target_file_name)

    return:
        ret     the number of error
    """
    ret = 0

    if module.param['target_file_name']:
        cmd = '/usr/sbin/viosupgrade -q -f {0}'\
              .format(module.param['target_file_name'])
        (ret, stdout, stderr) = module.run_command(cmd)

        module.log("[STDOUT] {0}".format(stdout))
        if ret == 0:
            module.log("[STDERR] {0}".format(stderr))
        else:
            module.log("command {0} failed: {1}".format(cmd, stderr))
            ret = 1
    else:
        for target in module.param['targets']:
            cmd = '/usr/sbin/viosupgrade -q -n {0}'.format(target)
            (rc, stdout, stderr) = module.run_command(cmd)

            module.log("[STDOUT] {0}".format(stdout))
            if rc == 0:
                module.log("[STDERR] {0}".format(stderr))
            else:
                module.log("command {0} failed: {1}".format(cmd, stderr))
                ret += 1
    return ret


# TODO: test viosupgrade_file
def viosupgrade_file(module, filename):
    """
    Upgrade each VIOS specified in the provided file
    runs: viosupgrade -t {bosinst | altdisk} -f [filename] [-v]

    args:
        module      the Ansible module
        filename    filename with info for VIOS upgrade

    module.param used:
        targets

    return:
        ret     return code of the command
    """
    global CHANGED
    ret = 0

    # build the command
    cmd = '/usr/sbin/viosupgrade'
    if 'altdisk_install' in module.param['action']:
        cmd += ' -t altdisk'
    elif 'bos_install' in module.param['action']:
        cmd += ' -t bosinst'
    cmd += ' -f' + module.param['target_file_name']
    if module.param['validate_input_data']:
        cmd += ' -v'

    # run the command
    (ret, stdout, stderr) = module.run_command(cmd)

    CHANGED = True  # don't really know
    module.log("[STDOUT] {0}".format(stdout))
    if ret == 0:
        module.log("[STDERR] {0}".format(stderr))
    else:
        module.log("command {0} failed: {1}".format(cmd, stderr))

    return ret


# TODO: test viosupgrade_list
def viosupgrade_list(module, targets):
    """
    Upgrade each VIOS specified in the provided file
    runs one of:
        viosupgrade -t bosinst -n hostname -m mksysb_name -p spotname
                    {-a rootvg_vg_clone_disk | -r rootvg_inst_disk | -s}
                    [-b backupFile] [-c] [-v]
        viosupgrade -t altdisk -n hostname -m mksysb_name
                    -a rootvg_vg_clone_disk [-b backup_file] [-c] [-v]

    args:
        module        the Ansible module

    module.param used:
        target_file_name   (optional) filename with targets info
        targets            (required if not target_file_name)

    return:
        ret     the number of error
    """
    global CHANGED
    ret = 0

    for target in targets:
        # build the command
        cmd = '/usr/sbin/viosupgrade'
        if 'altdisk_install' in module.param['action']:
            cmd += ' -t altdisk'
        elif 'bos_install' in module.param['action']:
            cmd += ' -t bosinst'

        # TODO: check if NIM object name is supported, otherwise get it from lsnim
        #       NIM object name can be different from hostname
        #       3rd field of following cmd result 'lsnim -Z -a 'if1' <target>' (separated with ':')
        cmd += ' -n ' + target

        if target in module.param['mksysb_name']:
            cmd += ' -m ' + module.param['mksysb_name'][target]
        elif 'all' in module.param['mksysb_name']:
            cmd += ' -m ' + module.param['mksysb_name']['all']

        if target in module.param['spot_name']:
            cmd += ' -p ' + module.param['spot_name'][target]
        elif 'all' in module.param['spot_name']:
            cmd += ' -p ' + module.param['spot_name']['all']

        if target in module.param['rootvg_clone_disk']:
            cmd += ' -a ' + module.param['rootvg_clone_disk'][target]
        elif 'all' in module.param['rootvg_clone_disk']:
            cmd += ' -a ' + module.param['rootvg_clone_disk']['all']

        if target in module.param['rootvg_install_disk']:
            cmd += ' -r ' + module.param['rootvg_install_disk'][target]
        elif 'all' in module.param['rootvg_install_disk']:
            cmd += ' -r ' + module.param['rootvg_install_disk']['all']

        if target in module.param['skip_rootvg_cloning']:
            if distutils.util.strtobool(module.param['skip_rootvg_cloning'][target]):
                cmd += ' -s'
        elif 'all' in module.param['skip_rootvg_cloning']:
            if distutils.util.strtobool(module.param['skip_rootvg_cloning']['all']):
                cmd += ' -s'

        if target in module.param['backup_file']:
            cmd += ' -b ' + module.param['backup_file'][target]
        elif 'all' in module.param['backup_file']:
            cmd += ' -b ' + module.param['backup_file']['all']

        if target in module.param['cluster_exists']:
            if distutils.util.strtobool(module.param['cluster_exists'][target]):
                cmd += ' -c'
        elif 'all' in module.param['cluster_exists']:
            if distutils.util.strtobool(module.param['cluster_exists']['all']):
                cmd += ' -c'

        if target in module.param['validate_input_data']:
            if distutils.util.strtobool(module.param['validate_input_data'][target]):
                cmd += ' -v'
        elif 'all' in module.param['validate_input_data']:
            if distutils.util.strtobool(module.param['validate_input_data']['all']):
                cmd += ' -v'

        supported_res = ['res_resolv_conf', 'res_script', 'res_fb_script',
                         'res_file_res', 'res_image_data', 'res_log']
        for res in supported_res:
            if target in module.param[res]:
                cmd += ' -e {0}:{1}'.format(res, module.param[res][target])
            elif 'all' in module.param[res]:
                cmd += ' -e {0}:{1}'.format(res, module.param[res]['all'])

        # run the command
        (rc, stdout, stderr) = module.run_command(cmd)

        CHANGED = True  # don't really know
        module.log("[STDOUT] {0}".format(stdout))
        if rc == 0:
            module.log("[STDERR] {0}".format(stderr))
        else:
            module.log("command {0} failed: {1}".format(cmd, stderr))
            ret += 1

    return ret


###################################################################################

def main():
    global CHANGED
    DEBUG_DATA = []
    OUTPUT = []

    MODULE = AnsibleModule(
        # TODO: remove not needed attributes
        argument_spec=dict(
            # description=dict(required=False, type='str'),

            # IBM automation generic attributes
            action=dict(required=True, type='str',
                        choices=['altdisk_install', 'bos_install', 'get_status']),
            vars=dict(required=False, type='dict'),
            vios_status=dict(required=False, type='dict'),
            # not used so far, can be used to get if1 for hostname resolution
            # nim_node=dict(required=False, type='dict'),

            # nim_migvios_setup not supported yet?
            # nim_migvios_setup [ -a [ mk_resource={yes|no}] [ file_system=fs_name ]
            #                        [ volume_group=vg_name ] [ disk=disk_name ]
            #                        [device=device ]
            #                   ] [ -B ] [ -F ] [ -S ] [ -v ]

            # mutually exclisive
            targets=dict(required=False, type='list', elements='str'),
            target_file_name=dict(required=False, type='str'),

            # following attributes are dictionaries with
            # key: 'all' or hostname and value: a string
            # example:
            # mksysb_name={"tgt1": "hdisk1", "tgt2": "hdisk1"}
            # mksysb_name={"all": "hdisk1"}
            mksysb_name=dict(required=False, type='dict'),
            spot_name=dict(required=False, type='dict'),
            backup_file=dict(required=False, type='dict'),
            rootvg_clone_disk=dict(required=False, type='dict'),
            rootvg_install_disk=dict(required=False, type='dict'),
            # Resources (-e option):
            res_resolv_conf=dict(required=False, type='dict'),
            res_script=dict(required=False, type='dict'),
            res_fb_script=dict(required=False, type='dict'),
            res_file_res=dict(required=False, type='dict'),
            res_image_data=dict(required=False, type='dict'),
            res_log=dict(required=False, type='dict'),

            # dictionaries with key: 'all' or hostname and value: bool
            cluster_exists=dict(required=False, type='dict'),
            validate_input_data=dict(required=False, type='dict'),
            skip_rootvg_cloning=dict(required=False, type='dict'),
        ),
        mutually_exclusive=[['targets', 'target_file_name']],
        required_one_of=[['targets', 'target_file_name']],
        # TODO: determine mandatory attributes
        required_if=[],
    )

    # =========================================================================
    # Get Module params
    # =========================================================================
    MODULE.status = {}
    MODULE.targets = []
    MODULE.nim_node = {}

    MODULE.debug('*** START NIM VIOSUPGRADE OPERATION ***')

    OUTPUT.append('VIOSUpgrade operation for {0}'.format(MODULE.params['targets']))
    MODULE.log('Action {0} for {1} targets'
               .format(MODULE.params['action'], MODULE.params['targets']))

    # build NIM node info (if needed)
    if MODULE.params['nim_node']:
        MODULE.nim_node = MODULE.params['nim_node']
    # TODO: remove this, not needed, except maybe for hostname
    # if 'nim_vios' not in MODULE.nim_node:
    #     MODULE.nim_node['nim_vios'] = get_nim_clients_info(MODULE, 'vios')
    # MODULE.debug('NIM VIOS: {0}'.format(MODULE.nim_node['nim_vios']))

    if MODULE.params['target_file_name']:
        try:
            myfile = open(MODULE.params['target_file_name'], 'r')
            csvreader = csv.reader(myfile, delimiter=':')
            for line in csvreader:
                MODULE.targets.append(line[0].strip())
            myfile.close()
        except IOError as e:
            msg = 'Failed to parse file {0}: {1}.'.format(e.filename, e.strerror)
            MODULE.log(msg)
            MODULE.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                             debug_output=DEBUG_DATA, status=MODULE.status)
    else:
        MODULE.params['target_file_name'] = ""
        MODULE.targets = MODULE.params['targets']

    if not MODULE.targets:
        msg = 'Empty target list'
        OUTPUT.append(msg)
        MODULE.warn(msg + ': {0}'.format(MODULE.params['targets']))
        MODULE.exit_json(
            changed=False,
            msg=msg,
            nim_node=MODULE.nim_node,
            debug_output=DEBUG_DATA,
            output=OUTPUT,
            status=MODULE.status)

    OUTPUT.append('Targets list:{0}'.format(MODULE.targets))
    MODULE.debug('Target list: {0}'.format(MODULE.targets))

    if MODULE.params['target_file_name']:
        if MODULE.params['action'] != 'get_status':
            viosupgrade_file(MODULE, MODULE.params['target_file_name'])

        if 'get_status' in MODULE.params['action']:
            viosupgrade_query(MODULE)

    elif MODULE.params['targets']:
        if MODULE.params['action'] != 'get_status':
            viosupgrade_list(MODULE, MODULE.params['targets'])

        if 'get_status' in MODULE.params['action']:
            viosupgrade_query(MODULE)
    else:
        # should not happen
        msg = 'Please speficy one of "targets" or "target_file_name" parameters.'
        MODULE.log(msg)
        MODULE.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                         debug_output=DEBUG_DATA, status=MODULE.status)

    # # Prints status for each targets
    # nb_error = 0
    # msg = 'VIOSUpgrade {0} operation status:'.format(MODULE.params['action'])
    # if MODULE.status:
    #     OUTPUT.append(msg)
    #     MODULE.log(msg)
    #     for vios_key in MODULE.status:
    #         OUTPUT.append('    {0} : {1}'.format(vios_key, MODULE.status[vios_key]))
    #         MODULE.log('    {0} : {1}'.format(vios_key, MODULE.status[vios_key]))
    #         if not re.match(r"^SUCCESS", MODULE.status[vios_key]):
    #             nb_error += 1
    # else:
    #     MODULE.log(msg + ' MODULE.status table is empty')
    #     OUTPUT.append(msg + ' Error getting the status')
    #     MODULE.status = MODULE.params['vios_status']  # can be None

    # # Prints a global result statement
    # if nb_error == 0:
    #     msg = 'VIOSUpgrade {0} operation succeeded'\
    #           .format(MODULE.params['action'])
    #     OUTPUT.append(msg)
    #     MODULE.log(msg)
    # else:
    #     msg = 'VIOSUpgrade {0} operation failed: {1} errors'\
    #           .format(MODULE.params['action'], nb_error)
    #     OUTPUT.append(msg)
    #     MODULE.log(msg)

    # # =========================================================================
    # # Exit
    # # =========================================================================
    # if nb_error == 0:
    #     MODULE.exit_json(
    #         changed=CHANGED,
    #         msg=msg,
    #         targets=MODULE.targets,
    #         nim_node=MODULE.nim_node,
    #         debug_output=DEBUG_DATA,
    #         output=OUTPUT,
    #         status=MODULE.status)

    MODULE.fail_json(
        changed=CHANGED,
        msg=msg,
        targets=MODULE.targets,
        nim_node=MODULE.nim_node,
        debug_output=DEBUG_DATA,
        output=OUTPUT,
        status=MODULE.status)


if __name__ == '__main__':
    main()
