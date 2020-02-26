#!/usr/bin/python
#
# Copyright 2018, International Business Machines Corporation
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

############################################################################
"""AIX NIM viosupgrade: tool to upgrade VIOSes in NIM environment"""

import logging
import csv
import distutils.util

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = """
---
module: nim_upgradeios
authors: Vianney Robin, Alain Poncet, Pascal Oliva
short_description: Perform a upgrade with the viosupgrade tool
"""

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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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
        cmd = '/usr/sbin/viosupgrade -q -f {}'\
              .format(module.param['target_file_name'])
        (ret, stdout, stderr) = module.run_command(cmd)

        logging.info("[STDOUT] {}".format(stdout))
        if ret == 0:
            logging.info("[STDERR] {}".format(stderr))
        else:
            logging.error("command {} failed: {}".format(stderr))
            ret = 1
    else:
        for target in module.param['targets']:
            cmd = '/usr/sbin/viosupgrade -q -n {}'.format(target)
            (rc, stdout, stderr) = module.run_command(cmd)

            logging.info("[STDOUT] {}".format(stdout))
            if rc == 0:
                logging.info("[STDERR] {}".format(stderr))
            else:
                logging.error("command {} failed: {}".format(stderr))
                ret += 1
    return ret


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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

    CHANGED=True  # don't really know
    logging.info("[STDOUT] {}".format(stdout))
    if ret == 0:
        logging.info("[STDERR] {}".format(stderr))
    else:
        logging.error("command {} failed: {}".format(stderr))

    return ret


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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
                cmd += ' -e {}:{}'.format(res, module.param[res][target])
            elif 'all' in module.param[res]:
                cmd += ' -e {}:{}'.format(res, module.param[res]['all'])

        # run the command
        (rc, stdout, stderr) = module.run_command(cmd)

        CHANGED=True  # don't really know
        logging.info("[STDOUT] {}".format(stdout))
        if rc == 0:
            logging.info("[STDERR] {}".format(stderr))
        else:
            logging.error("command {} failed: {}".format(stderr))
            ret += 1

    return ret


###################################################################################

if __name__ == '__main__':
    DEBUG_DATA = []
    OUTPUT = []
    CHANGED = False
    VARS = {}

    MODULE = AnsibleModule(
        # TODO: remove not needed attributes
        argument_spec=dict(
            description=dict(required=False, type='str'),

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
            targets=dict(required=False, type='list'),
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
        # TODO: VRO determine mandatory attributes
        required_if=[],
    )

    # =========================================================================
    # Get Module params
    # =========================================================================
    MODULE.status = {}
    MODULE.targets = []
    MODULE.nim_node = {}
    nb_error = 0

    # Handle playbook variables
    LOGNAME = '/tmp/ansible_upgradeios_debug.log'
    if MODULE.params['vars']:
        VARS = MODULE.params['vars']
    if VARS is not None and 'log_file' not in VARS:
        VARS['log_file'] = LOGNAME

    # Open log file
    OUTPUT.append('Log file: {}'.format(VARS['log_file']))
    LOGFRMT = '[%(asctime)s] %(levelname)s: [%(funcName)s:%(thread)d] %(message)s'
    logging.basicConfig(filename='{}'.format(VARS['log_file']), format=LOGFRMT, level=logging.DEBUG)

    logging.debug('*** START NIM VIOSUPGRADE OPERATION ***')

    OUTPUT.append('VIOSUpgrade operation for {}'.format(MODULE.params['targets']))
    logging.info('Action {} for {} targets'
                 .format(MODULE.params['action'], MODULE.params['targets']))

    # build NIM node info (if needed)
    if MODULE.params['nim_node']:
        MODULE.nim_node = MODULE.params['nim_node']
    # TODO: remove this, not needed, except maybe for hostname
    # if 'nim_vios' not in MODULE.nim_node:
    #     MODULE.nim_node['nim_vios'] = get_nim_clients_info(MODULE, 'vios')
    # logging.debug('NIM VIOS: {}'.format(MODULE.nim_node['nim_vios']))

    if MODULE.params['target_file_name']:
        try:
            myfile = open(MODULE.params['target_file_name'], 'r')
            csvreader = csv.reader(myfile, delimiter=':')
            for line in csvreader:
                MODULE.targets.append(line[0].strip())
            myfile.close()
        except IOError as e:
            msg = 'Failed to parse file {}: {}.'.format(e.filename, e.strerror)
            logging.error(msg)
            MODULE.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                             debug_output=DEBUG_DATA, status=MODULE.status)
    else:
        MODULE.params['target_file_name'] = ""
        MODULE.targets = MODULE.params['targets']

    if not MODULE.targets:
        msg = 'Empty target list'
        OUTPUT.append(msg)
        logging.warn(msg + ': {}'.format(MODULE.params['targets']))
        MODULE.exit_json(
            changed=False,
            msg=msg,
            nim_node=MODULE.nim_node,
            debug_output=DEBUG_DATA,
            output=OUTPUT,
            status=MODULE.status)

    OUTPUT.append('Targets list:{}'.format(MODULE.targets))
    logging.debug('Target list: {}'.format(MODULE.targets))

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
        logging.error(msg)
        MODULE.fail_json(changed=CHANGED, msg=msg, output=OUTPUT,
                         debug_output=DEBUG_DATA, status=MODULE.status)

    # # Prints status for each targets
    # msg = 'VIOSUpgrade {} operation status:'.format(MODULE.params['action'])
    # if MODULE.status:
    #     OUTPUT.append(msg)
    #     logging.info(msg)
    #     for vios_key in MODULE.status:
    #         OUTPUT.append('    {} : {}'.format(vios_key, MODULE.status[vios_key]))
    #         logging.info('    {} : {}'.format(vios_key, MODULE.status[vios_key]))
    #         if not re.match(r"^SUCCESS", MODULE.status[vios_key]):
    #             nb_error += 1
    # else:
    #     logging.error(msg + ' MODULE.status table is empty')
    #     OUTPUT.append(msg + ' Error getting the status')
    #     MODULE.status = MODULE.params['vios_status']  # can be None

    # # Prints a global result statement
    # if nb_error == 0:
    #     msg = 'VIOSUpgrade {} operation succeeded'\
    #           .format(MODULE.params['action'])
    #     OUTPUT.append(msg)
    #     logging.info(msg)
    # else:
    #     msg = 'VIOSUpgrade {} operation failed: {} errors'\
    #           .format(MODULE.params['action'], nb_error)
    #     OUTPUT.append(msg)
    #     logging.error(msg)

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
