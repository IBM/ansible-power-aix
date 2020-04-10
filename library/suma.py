#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'IBM, Inc'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team
module: suma
short_description: Download fixes, SP or TL on an AIX server
description:
- Creates a task to automate the download of technology levels and
  service packs from a fix server.
version_added: '2.9'
requirements: [ AIX ]
options:
  oslevel:
    description:
    - Operating System level.
    type: str
  action:
    description:
    - Controls what is performed.
    - C(download) to download fixes.
    - C(preview).
    - C(list).
    - C(edit).
    - C(unschedule).
    - C(delete).
    - C(config).
    - C(default).
    type: str
    choices: [ download, preview, list, edit, unschedule, delete, config, default ]
    default: download
  download_dir:
    description:
    - Directory where updates are downloaded.
    type: str
  download_only:
    description:
    - Download only.
    type: bool
    default: no
  task_id:
    description:
    - SUMA task.
    type: str
  sched_time:
    description:
    - Schedule time.
    type: str
  description:
    description:
    - Display name for SUMA task.
    type: str
'''

EXAMPLES = r'''
- name: Check for, and install, system updates
  suma:
    oslevel: latest
    download_dir: /usr/sys/inst.images
'''

RETURN = r''' # '''

import os
import re
import glob
import shutil
import subprocess
import logging
# Ansible module 'boilerplate'
# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from ansible.module_utils.basic import AnsibleModule

SUMA_CHANGED = False
SUMA_OUTPUT = []
SUMA_ERROR = []
PARAMS = {}
LOGDIR = "/var/adm/ansible"


def exec_cmd(cmd, shell=False):
    """Execute a command.

    arguments:
        cmd    (str): The command to be executed
        shell (bool): execute cmd through the shell if set (vulnerable to shell
                      injection when cmd is from user inputs). If the cmd is a
                      string, the string specifies the command to execute through
                      the shell. If cmd is a list, the first item specifies the
                      command, and other items are arguments to the shell itself.

    return:
        ret code: 0 - OK
                  1 - CalledProcessError exception
                  2 - other exception
        both stdout and stderr of the command
    """
    out = ''

    logging.debug("exec command:{}".format(cmd))
    try:
        out = subprocess.check_output(cmd, stderr=subprocess.STDOUT, shell=shell)

    except subprocess.CalledProcessError as exc:
        logging.debug("exec command rc:{} out:{}"
                      .format(exc.returncode, exc.output))
        return exc.returncode, exc.output

    except OSError as exc:
        logging.debug("exec command rc:{} out:{}"
                      .format(exc.args[0], exc.args))
        return exc.args[0], exc.args

    except Exception as exc:
        msg = "Command: {} Exception:{} =>Data:{}"\
              .format(cmd, exc, out)
        logging.debug("exec command rc:2 out:{}".format(msg))
        return 2, msg

    logging.debug("exec command rc:0 out:{}".format(out))

    return 0, out


def compute_rq_type(oslevel):
    """Compute rq_type.

    return:
        Latest when oslevel is blank or latest (not case sensitive)
        Latest when oslevel is a TL (6 digits)
        TL     when oslevel is xxxx-xx(-00-0000)
        SP     when oslevel is xxxx-xx-xx(-xxxx)
        ERROR  when oslevel is not recognized
    """
    if oslevel is None or not oslevel.strip() or oslevel.upper() == 'LATEST':
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})$", oslevel):
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})(|-00|-00-0000)$", oslevel):
        return 'TL'
    if re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})(|-[0-9]{4})$", oslevel):
        return 'SP'

    return 'ERROR'


def compute_rq_name(rq_type, oslevel):
    """
    Compute rq_name.
        if oslevel is a complete SP (12 digits) then return RqName = oslevel
        if oslevel is an incomplete SP (8 digits) or equal Latest then execute
        a metadata suma request to find the complete SP level (12 digits)
    Compute the suma rq_name
        - for Latest: return a SP value in the form xxxx-xx-xx-xxxx
        - for TL: return the TL value in the form xxxx-xx
        - for SP: return the SP value in the form xxxx-xx-xx-xxxx

    arguments:
        rq_type
        oslevel                  requested oslevel

    return:
       return code : 0 - OK
                     1 - CalledProcessError exception
                     2 - other exception
       rq_name value or stderr in case of error
    """
    global LOGDIR

    metadata_dir = LOGDIR + "/metadata"  # <TODO> get env variable for that
    rq_name = ''
    if rq_type == 'Latest':
        metadata_filter_ml = oslevel[:7]
        if len(metadata_filter_ml) == 4:
            metadata_filter_ml += "-00"

        if not metadata_filter_ml:
            logging.error(
                'Error: cannot discover filter ml based on the target client')
            raise Exception(
                'Error: cannot discover filter ml based on the target client')

        if not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir)

        # Build suma command to get metadata
        cmd = 'LC_ALL=C /usr/sbin/suma -x -a Action=Metadata '\
              '-a RqType=Latest -a DLTarget={} -a DisplayName="{}"'\
              .format(metadata_dir, PARAMS['Description'])

        logging.debug("SUMA command:{}".format(cmd))

        ret, stdout = exec_cmd(cmd, shell=True)
        if ret != 0:
            logging.error("SUMA command error rc:{}, error: {}"
                          .format(ret, stdout))
            return ret, stdout

        logging.debug("SUMA command rc:{}".format(ret))

        # find latest SP build number for the highest TL
        sp_version = None
        file_name = metadata_dir + "/installp/ppc/" + "*.xml"
        logging.debug("searched files: {}".format(file_name))
        files = glob.glob(file_name)
        logging.debug("found files: {}".format(files))
        for cur_file in files:
            logging.debug("open file: {}".format(cur_file))
            fic = open(cur_file, "r")
            for line in fic:
                logging.debug("line: {}".format(line))
                match_item = re.match(
                    r"^<SP name=\"([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})\">$",
                    line)
                if match_item:
                    version = match_item.group(1)
                    if sp_version is None or version > sp_version:
                        sp_version = version
                    break

        rq_name = sp_version
        shutil.rmtree(metadata_dir)

    elif rq_type == 'TL':
        # target version = TL part of the requested version
        rq_name = re.match(r"^([0-9]{4}-[0-9]{2})(|-00|-00-0000)$",
                           oslevel).group(1)

    elif rq_type == 'SP':
        if re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$", oslevel):
            rq_name = oslevel
        elif re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}$", oslevel):
            metadata_filter_ml = re.match(r"^([0-9]{4}-[0-9]{2})-[0-9]{2}$",
                                          oslevel).group(1)

            if not os.path.exists(metadata_dir):
                os.makedirs(metadata_dir)

            # =================================================================
            # Build suma command to get metadata
            # =================================================================
            cmd = 'LC_ALL=C /usr/sbin/suma -x -a Action=Metadata '\
                  '-a RqType=Latest -a DLTarget={} -a DisplayName="{}"'\
                  .format(metadata_dir, PARAMS['Description'])

            logging.debug("suma command: {}".format(cmd))

            ret, stdout = exec_cmd(cmd, shell=True)
            if ret != 0:
                logging.error("SUMA command error rc:{}, error: {}"
                              .format(ret, stdout))
                return ret, stdout

            # find SP build number
            sp_version = None
            cur_file = metadata_dir + "/installp/ppc/" + oslevel + ".xml"
            fic = open(cur_file, "r")
            for line in fic:
                match_item = re.match(
                    r"^<SP name=\"([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})\">$",
                    line)
                if match_item:
                    sp_version = match_item.group(1)
                    break

            rq_name = sp_version
            shutil.rmtree(metadata_dir)

    return 0, rq_name


def compute_filter_ml(rq_name):

    """
    Compute the suma filter ML.
    returns the TL part of rq_name.
    """
    filter_ml = rq_name[:7]
    if len(filter_ml) == 4:
        filter_ml += "-00"

    return filter_ml


def compute_dl_target(location):
    """
    When the location is empty, set the location path to
        /usr/sys/inst.images

    return:
        return code : 0 - OK
                      1 - if error
        dl_target value or msg in case of error
    """
    if not location or not location.strip():
        loc = "/usr/sys/inst.images"
    else:
        loc = location.rstrip('/')

    dl_target = loc

    return 0, dl_target


def suma_command(module, action):
    """
    Run a suma command.

    parameters
        action   preview, download or install

    return:
       ret     suma command return code
       stdout  suma command output
    """
    rq_type = PARAMS['RqType']
    if rq_type == 'Latest':
        suma_cmd = 'LC_ALL=C /usr/sbin/suma -x -a RqType={} -a Action={} '\
                   '-a DLTarget={} -a DisplayName="{}"'\
                   .format(rq_type, action, PARAMS['DLTarget'], PARAMS['Description'])
    else:
        suma_cmd = 'LC_ALL=C /usr/sbin/suma -x -a RqType={} -a Action={} '\
                   '-a DLTarget={} -a RqName={} -a DisplayName="{}"'\
                   .format(rq_type, action, PARAMS['DLTarget'], PARAMS['RqName'], PARAMS['Description'])

    logging.debug("SUMA - Command:{}".format(suma_cmd))
    SUMA_OUTPUT.append("SUMA - Command:{}".format(suma_cmd))

    ret, stdout = exec_cmd(suma_cmd, shell=True)
    if ret != 0:
        logging.error("Error: suma {} command failed with return code {}".format(action, ret))
        SUMA_ERROR.append("SUMA Command: {} => Error :{}"
                          .format(suma_cmd, stdout.split('\n')))
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    return ret, stdout


def suma_list(module):
    """
    List all SUMA tasks or the task associated with the given task ID
    """
    task = PARAMS['task_id']
    if task is None or task.strip() == '':
        task = ''
    cmde = "/usr/sbin/suma -l {}".format(task)
    ret, stdout, stderr = module.run_command(cmde)

    if ret != 0:
        msg = "SUMA Error: list command: '{}' failed with return code {}" \
              .format(cmde, ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    SUMA_OUTPUT.append('List SUMA tasks:')
    SUMA_OUTPUT.append(stdout.split('\n'))


def check_time(val, mini, maxi):
    """
    Check a value is equal to '*' or is a numeric value in the
    [mini, maxi] range
    """
    if val == '*':
        return True

    if val.isdigit() and mini <= int(val) and maxi >= int(val):
        return True

    return False


def suma_edit(module):
    """
    Edit a SUMA task associated with the given task ID

    Depending on the shed_time parameter value, the task wil be scheduled,
        unscheduled or saved
    """
    cmde = '/usr/sbin/suma'
    if PARAMS['sched_time'] is None:
        # save
        cmde += ' w'

    elif not PARAMS['sched_time'].strip():
        # unschedule
        cmde += ' u'

    else:
        # schedule
        minute, hour, day, month, weekday = PARAMS['sched_time'].split(' ')

        if check_time(minute, 0, 59) and check_time(hour, 0, 23) \
           and check_time(day, 1, 31) and check_time(month, 1, 12) \
           and check_time(weekday, 0, 6):

            cmde += ' -s "{}"'.format(PARAMS['sched_time'])
        else:
            msg = "Error: SUMA edit command: '{}' Bad schedule time".format(cmde)
            logging.error(msg)
            SUMA_ERROR.append(msg)
            module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    cmde += ' {}'.format(PARAMS['task_id'])
    ret, stdout, stderr = module.run_command(cmde)

    if ret != 0:
        msg = "SUMA Error: edit command: '{}' failed with return code {}" \
              .format(cmde, ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    SUMA_OUTPUT.append("Edit SUMA task {}".format(PARAMS['task_id']))
    SUMA_OUTPUT.append(stdout.split('\n'))


def suma_unschedule(module):
    """
    Unschedule a SUMA task associated with the given task ID
    """
    cmde = "/usr/sbin/suma -u {}".format(PARAMS['task_id'])
    ret, stdout, stderr = module.run_command(cmde)

    if ret != 0:
        msg = "SUMA Error: unschedule command: '{}' failed with return code {}" \
              .format(cmde, ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    SUMA_OUTPUT.append("Unschedule suma task: {}".format(PARAMS['task_id']))
    SUMA_OUTPUT.append(stdout.split('\n'))


def suma_delete(module):
    """
    Delete the SUMA task associated with the given task ID
    """
    cmde = "/usr/sbin/suma -d {}".format(PARAMS['task_id'])
    ret, stdout, stderr = module.run_command(cmde)

    if ret != 0:
        msg = "SUMA Error: delete command: '{}' failed with return code {}" \
              .format(cmde, ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    SUMA_OUTPUT.append("Delete SUMA task {}".format(PARAMS['task_id']))
    SUMA_OUTPUT.append(stdout.split('\n'))


def suma_config(module):
    """
    List the SUMA global configuration settings
    """
    cmde = '/usr/sbin/suma -c'
    ret, stdout, stderr = module.run_command(cmde)

    if ret != 0:
        msg = "SUMA Error: config command: '{}' failed with return code {}" \
              .format(cmde, ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    SUMA_OUTPUT.append('SUMA global configuration settings:')
    SUMA_OUTPUT.append(stdout.split('\n'))


def suma_default(module):
    """
    List default SUMA tasks
    """
    cmde = '/usr/sbin/suma -D'
    ret, stdout, stderr = module.run_command(cmde)

    if ret != 0:
        msg = "SUMA Error: default command: '{}' failed with return code {}" \
              .format(cmde, ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    SUMA_OUTPUT.append('SUMA default task:')
    SUMA_OUTPUT.append(stdout.split('\n'))


def suma_download(module):
    """
    Download / Install (or preview) action
    """

    global SUMA_CHANGED
    global PARAMS
    global LOGDIR

    req_oslevel = PARAMS['req_oslevel']
    if req_oslevel is None \
       or not req_oslevel.strip() \
       or req_oslevel.upper() == 'LATEST':
        req_oslevel = 'Latest'
        PARAMS['req_oslevel'] = req_oslevel

    if re.match(r"^([0-9]{4})(|-00|-00-00|-00-00-0000)$", req_oslevel):
        msg = 'Specify a non 0 value for the Technical Level or the Service Pack'
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    # =========================================================================
    # compute SUMA request type based on oslevel property
    # =========================================================================
    rq_type = compute_rq_type(PARAMS['req_oslevel'])
    if rq_type == 'ERROR':
        msg = "SUMA Error: Invalid oslevel: '{}'".format(PARAMS['req_oslevel'])
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    PARAMS['RqType'] = rq_type

    logging.debug("SUMA req Type: {}".format(rq_type))

    # =========================================================================
    # compute SUMA request name based on metadata info
    # =========================================================================
#    ret, rq_name = compute_rq_name(rq_type, PARAMS['req_oslevel'])
#    if ret != 0:
#        msg = "SUMA Error: compute_rq_name - rc:{}, error:{}" \
#              .format(ret, rq_name)
#        logging.error(msg)
#        SUMA_OUTPUT.append(msg)
#        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    rq_name = PARAMS['req_oslevel']
    PARAMS['RqName'] = rq_name

    logging.debug("Suma req Name: {}".format(rq_name))

    # =========================================================================
    # Compute the filter_ml i.e. the min oslevel
    # =========================================================================
    filter_ml = compute_filter_ml(rq_name)

    logging.debug("{} <= Min Oslevel".format(filter_ml))

    if filter_ml is None:
        # no technical level found for the target machines
        msg = "SUMA Error: There is no target machine matching the requested oslevel {}." \
              .format(rq_name[:10])
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    # =========================================================================
    # metadata does not match any fixes
    # =========================================================================
    if not rq_name or not rq_name.strip():
        msg = "SUMA - Error: oslevel {} doesn't match any fixes" \
              .format(PARAMS['req_oslevel'])
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    logging.debug("Suma req Name: {}".format(rq_name))

    # =========================================================================
    # compute suma dl target
    # =========================================================================
    ret, dl_target = compute_dl_target(PARAMS['download_dir'])
    if ret != 0:
        msg = "SUMA Error: compute_dl_target - {}".format(dl_target)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    PARAMS['DLTarget'] = dl_target

    # display user message
    logging.debug("DL target: {}".format(dl_target))
    logging.info("The download location will be: {}.".format(dl_target))

    if rq_type == 'Latest':
        logging.info("{} is the Latest SP of TL {}."
                     .format(rq_name, filter_ml))

    PARAMS['Comments'] = '"Packages for updates from {} to {}"'\
                         .format(filter_ml, rq_name)

    # ========================================================================
    # Create download path/dir
    # ========================================================================
    if not os.path.exists(dl_target):
        os.makedirs(dl_target)

    logging.debug("mkdir command:{}".format(dl_target))

    # ========================================================================
    # SUMA command for preview
    # ========================================================================
    ret, stdout = suma_command(module, 'Preview')
    logging.debug("SUMA preview stdout:{}".format(stdout))

    # parse output to see if there is something to download
    downloaded = 0
    failed = 0
    skipped = 0
    for line in stdout.rstrip().split('\n'):
        line = line.rstrip()
        matched = re.match(r"^\s+(\d+)\s+downloaded$", line)
        if matched:
            downloaded = int(matched.group(1))
            continue
        matched = re.match(r"^\s+(\d+)\s+failed$", line)
        if matched:
            failed = int(matched.group(1))
            continue
        matched = re.match(r"^\s+(\d+)\s+skipped$", line)
        if matched:
            skipped = int(matched.group(1))

    msg = "Preview summary : {} to download, {} failed, {} skipped"\
          .format(downloaded, failed, skipped)
    logging.info(msg)
    SUMA_OUTPUT.append(msg)

    # ========================================================================
    # If action is preview or nothing is available to download, we are done
    # else dowload what is found (and install if necessary)
    # ========================================================================
    if PARAMS['action'] == 'download':
        if downloaded != 0:

            # ================================================================
            # SUMA command for download
            # ================================================================
            ret, stdout = suma_command(module, 'Download')
            logging.debug("SUMA dowload stdout:{}".format(stdout))

            # parse output to see if there is something downloaded
            downloaded = 0
            failed = 0
            skipped = 0
            for line in stdout.rstrip().split('\n'):
                line = line.rstrip()
                matched = re.match(r"^\s+(\d+)\s+downloaded$", line)
                if matched:
                    downloaded = int(matched.group(1))
                    continue
                matched = re.match(r"^\s+(\d+)\s+failed$", line)
                if matched:
                    failed = int(matched.group(1))
                    continue
                matched = re.match(r"^\s+(\d+)\s+skipped$", line)
                if matched:
                    skipped = int(matched.group(1))

            msg = "Download summary : {} downloaded, {} failed, {} skipped"\
                  .format(downloaded, failed, skipped)
            logging.info(msg)
            SUMA_OUTPUT.append(msg)

            if downloaded != 0:
                SUMA_CHANGED = True
                # ===========================================================
                #   Install updates
                # ===========================================================
                if not PARAMS['download_only']:
                    cmde = "LC_ALL=C /usr/sbin/install_all_updates -Yd {}"\
                           .format(PARAMS['DLTarget'])
                    logging.debug("SUMA command:{}".format(cmde))
                    SUMA_OUTPUT.append("SUMA command:{}".format(cmde))
                    ret, stdout = exec_cmd(cmde, shell=True)

                    if ret != 0:
                        msg = "SUMA Error: install_all_updates command failed with return code {}. \
                               Review {}/suma_debug.log for status." \
                              .format(ret, LOGDIR)
                        logging.error(msg)
                        SUMA_ERROR.append(msg)
                        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

##############################################################################


def main():

    global SUMA_CHANGED
    global SUMA_OUTPUT
    global SUMA_ERROR
    global PARAMS
    global LOGDIR

    module = AnsibleModule(
        argument_spec=dict(
            oslevel=dict(required=False, type='str'),
            action=dict(required=False,
                        choices=['download', 'preview', 'list', 'edit',
                                 'unschedule', 'delete', 'config', 'default'],
                        type='str', default='download'),
            download_dir=dict(required=False, type='str'),
            download_only=dict(required=False, type='bool', default=False),
            task_id=dict(required=False, type='str'),
            sched_time=dict(required=False, type='str'),
            description=dict(required=False, type='str'),
        ),
        required_if=[
            ['action', 'edit', ['task_id']],
            ['action', 'delete', ['task_id']],
            ['action', 'download', ['oslevel']],
            ['action', 'preview', ['oslevel']],
            ['action', 'unschedule', ['task_id']],
        ],
        supports_check_mode=True
    )

    SUMA_CHANGED = False

    # Open log file
    if not os.path.exists(LOGDIR):
        os.makedirs(LOGDIR)
    logging.basicConfig(
        filename=LOGDIR + "/suma_debug.log",
        format='[%(asctime)s] %(levelname)s: [%(funcName)s:%(thread)d] %(message)s',
        level=logging.DEBUG)
    logging.debug('*** START ***')

    # ========================================================================
    # Get Module params
    # ========================================================================
    req_oslevel = module.params['oslevel']

    if module.params['action']:
        action = module.params['action']
    else:
        action = "download"

    download_dir = module.params['download_dir']
    if download_dir and download_dir.upper() == 'DEFAULT':
        download_dir = ''

    download_only = module.params['download_only']

    task_id = module.params['task_id']

    sched_time = module.params['sched_time']

    if module.params['description']:
        description = module.params['description']
    else:
        description = "{} request for oslevel {}".format(action, req_oslevel)

    PARAMS['action'] = action
    PARAMS['download_only'] = download_only
    PARAMS['Description'] = description

    # ========================================================================
    # switch action
    # ========================================================================
    if action == 'list':
        PARAMS['task_id'] = task_id
        suma_list(module)

    elif action == 'edit':
        PARAMS['task_id'] = task_id
        PARAMS['sched_time'] = sched_time
        suma_edit(module)

    elif action == 'unschedule':
        PARAMS['task_id'] = task_id
        suma_unschedule(module)

    elif action == 'delete':
        PARAMS['task_id'] = task_id
        suma_delete(module)

    elif action == 'config':
        suma_config(module)

    elif action == 'default':
        suma_default(module)

    elif action == 'download' or action == 'preview':
        PARAMS['req_oslevel'] = req_oslevel
        PARAMS['download_dir'] = download_dir
        suma_download(module)

    # ========================================================================
    # Exit
    # ========================================================================
    module.exit_json(
        changed=SUMA_CHANGED,
        msg="Suma {} completed successfully".format(action),
        suma_output=SUMA_OUTPUT)


if __name__ == '__main__':
    main()
