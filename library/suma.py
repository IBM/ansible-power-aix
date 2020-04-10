#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team
module: suma
short_description: Download/Install fixes, SP or TL on an AIX server.
description:
- Creates a task to automate the download and installation of technology level (TL)
  and service packs (SP) from a fix server using the Service Update Management
  Assistant (SUMA). Log file is /var/adm/ansible/suma_debug.log.
version_added: '2.9'
requirements: [ AIX ]
options:
  action:
    description:
    - Controls the action to be performed.
    - C(download) to download and install all fixes.
    - C(preview) to execute all the checks without downloading the fixes.
    - C(list) to list all SUMA tasks.
    - C(edit) to edit an exiting SUMA task.
    - C(unschedule) to remove any scheduling information for the specified SUMA task.
    - C(delete) to delete a SUMA task and remove any schedules for this task.
    - C(config) to list global SUMA configuration settings.
    - C(default) to list default SUMA tasks.
    type: str
    choices: [ download, preview, list, edit, unschedule, delete, config, default ]
    default: download
  oslevel:
    description:
    - Specifies the Operating System level to update to;
    - C(latest) indicates the latest level suma can update the target to.
    - C(xxxx-xx(-00-0000)) sepcifies a TL.
    - C(xxxx-xx-xx-xxxx) or C(xxxx-xx-xx) specifies a SP.
    - Required when I(action=download) or I(action=preview).
    type: str
    default: Latest
  download_dir:
    description:
    - Directory where updates are downloaded.
    type: str
    default: /usr/sys/inst.images
  download_only:
    description:
    - Download only. Do not perform installation of updates.
    type: bool
    default: no
  task_id:
    description:
    - SUMA task identification number.
    - Required when I(action=edit) or I(action=delete) or I(action=unschedule).
    type: str
  sched_time:
    description:
    - Schedule time.
    type: str
  description:
    description:
    - Display name for SUMA task.
    type: str
    default: I(action) request for oslevel I(oslevel)
  metadata_dir:
    description:
    - Directory where metadata files are downloaded.
    - Used when I(oslevel) is not exact, for example I(oslevel=latest).
    type: path
    default: /var/adm/ansible/metadata/installp/ppc/
'''

EXAMPLES = r'''
- name: Check for, download and install system updates
  suma:
    oslevel: latest
    download_dir: /usr/sys/inst.images

- name: Check and download required to update to SP 7.2.3.2
  suma:
    oslevel: '7200-03-02'
    download_only: yes
    download_dir: /tmp/dl_updt_7200-03-02
  when: ansible_distribution == 'AIX'
'''

RETURN = r'''
msg:
    description: Depends on the result. Success message or details on errors/warnings.
    returned: always
    type: list
    elements: str
    sample: ["Suma download completed successfully"]
suma_output:
    description: Information on the SUMA action execution.
    returned: success
    type: list
    elements: str
    sample: ["SUMA - Command /usr/sbin/suma -x -a RqType=Latest -a Action=Preview -a DLTarget=/usr/sys/inst.images
                                                -a DisplayName=download request for oslevel latest",
             "Preview summary  3 to download, 0 failed, 365 skipped",
             "SUMA - Command /usr/sbin/suma -x -a RqType=Latest -a Action=Download -a DLTarget=/usr/sys/inst.images
                                                -a DisplayName=download request for oslevel latest",
             "Download summary  3 downloaded, 0 failed, 365 skipped"]
'''

import os
import re
import glob
import shutil
import logging

from ansible.module_utils.basic import AnsibleModule

module = None
results = None
suma_error = []
suma_params = {}
logdir = "/var/adm/ansible"


def logged(func):
    """
    Decorator for logging
    """
    def logged_wrapper(*args):
        """
        Decorator wrapper for logging
        """
        logging.debug('ENTER {} with {}'.format(func.__name__, args))
        res = func(*args)
        logging.debug('EXIT {} with {}'.format(func.__name__, res))
        return res
    return logged_wrapper


@logged
def compute_rq_type(oslevel):
    """
    Compute rq_type to use in a suma request based on provided oslevel.
    arguments:
        oslevel level of the OS
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


@logged
def compute_rq_name(rq_type, oslevel):
    """
    Compute rq_name.
        if oslevel is a complete SP (12 digits) then return RqName = oslevel
        if oslevel is an incomplete SP (8 digits) or equal Latest then execute
        a metadata suma request to find the complete SP level (12 digits)
    The return format depends on rq_type value,
        - for Latest: return a SP value in the form xxxx-xx-xx-xxxx
        - for TL: return the TL value in the form xxxx-xx
        - for SP: return the SP value in the form xxxx-xx-xx-xxxx

    arguments:
        rq_type     type of request, can be Latest, SP or TL
        oslevel     requested oslevel

    return:
       return code : 0 - OK
                     1 - CalledProcessError exception
                     2 - other exception
       rq_name value or stderr in case of error
    """
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

        if not os.path.exists(suma_params['metadata_dir']):
            os.makedirs(suma_params['metadata_dir'])

        # Build suma command to get metadata
        cmd = ['/usr/sbin/suma', '-x', '-a', 'Action=Metadata', '-a', 'RqType=Latest']
        cmd += ['-a', 'DLTarget={}'.format(suma_params['metadata_dir'])]
        cmd += ['-a', 'DisplayName="{}"'.format(suma_params['description'])]

        logging.debug("SUMA command:{}".format(' '.join(cmd)))

        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            logging.error("SUMA command error rc:{}, error: {}, stdout:{}"
                          .format(rc, stderr, stdout))
            return rc, stderr

        logging.debug("SUMA command rc:{}".format(rc))

        # find latest SP build number for the highest TL
        sp_version = None
        file_name = suma_params['metadata_dir'] + "/installp/ppc/" + "*.xml"
        logging.debug("searched files: {}".format(file_name))
        files = glob.glob(file_name)
        logging.debug("found files: {}".format(files))
        for cur_file in files:
            logging.debug("open file: {}".format(cur_file))
            myfile = open(cur_file, "r")
            for line in myfile:
                # logging.debug("line: {}".format(line.rstrip()))
                match_item = re.match(
                    r"^<SP name=\"([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})\">$",
                    line.rstrip())
                if match_item:
                    version = match_item.group(1)
                    logging.debug("matched line: {}, version={}".format(line.rstrip(), version))
                    if sp_version is None or version > sp_version:
                        sp_version = version
                    break
        if sp_version is None:
            msg = "No 'SP name' found in files {}".format(files)
            logging.error(msg)
            return 1, msg

        rq_name = sp_version
        shutil.rmtree(suma_params['metadata_dir'])

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

            if not os.path.exists(suma_params['metadata_dir']):
                os.makedirs(suma_params['metadata_dir'])

            # =================================================================
            # Build suma command to get metadata
            # =================================================================
            cmd = ['/usr/sbin/suma', '-x', '-a', 'Action=Metadata', '-a', 'RqType=Latest']
            cmd += ['-a', 'DLTarget={}'.format(suma_params['metadata_dir'])]
            cmd += ['-a', 'DisplayName="{}"'.format(suma_params['description'])]

            logging.debug("SUMA command:{}".format(' '.join(cmd)))

            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                logging.error("SUMA command error rc:{}, error: {}, stdout: {}"
                              .format(rc, stderr, stdout))
                return rc, stderr

            # find SP build number
            sp_version = None
            cur_file = suma_params['metadata_dir'] + "/installp/ppc/" + oslevel + ".xml"
            myfile = open(cur_file, "r")
            for line in myfile:
                match_item = re.match(
                    r"^<SP name=\"([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})\">$",
                    line.rstrip())
                if match_item:
                    sp_version = match_item.group(1)
                    break
            if sp_version is None:
                msg = "No 'SP name' found in file {}".format(cur_file)
                logging.error(msg)
                return 1, msg

            rq_name = sp_version
            shutil.rmtree(suma_params['metadata_dir'])

    return 0, rq_name


@logged
def compute_filter_ml(rq_name):
    """
    Compute the suma filter Minimum OS Level.
    return:
        the TL part of rq_name.
    """
    filter_ml = rq_name[:7]
    if len(filter_ml) == 4:
        filter_ml += "-00"

    return filter_ml


@logged
def compute_dl_target(location):
    """
    Compute Suma download target path.
    When the location is empty, set the location path to
        /usr/sys/inst.images

    arguments:
        location    download directory
    return:
        return code : 0 - OK
                      1 - if error
        dl_target value or msg in case of error
    """
    if not location or not location.strip():
        loc = "/usr/sys/inst.images"
    else:
        loc = location.rstrip('/')

    return 0, loc


@logged
def suma_command(action):
    """
    Run a suma command.

    arguments:
        action   preview, download or install

    return:
       rc      suma command return code
       stdout  suma command output
    """
    rq_type = suma_params['RqType']
    cmd = ['/usr/sbin/suma', '-x', '-a', 'RqType={}'.format(rq_type)]
    cmd += ['-a', 'Action={}'.format(action)]
    cmd += ['-a', 'DLTarget={}'.format(suma_params['DLTarget'])]
    cmd += ['-a', 'DisplayName={}'.format(suma_params['description'])]

    if rq_type != 'Latest':
        cmd += ['-a', 'RqName={}'.format(suma_params['RqName'])]

    logging.debug("SUMA - Command:{}".format(' '.join(cmd)))
    results['msg'].append("SUMA - Command: {}".format(' '.join(cmd)))

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        logging.error("Error: suma {} command failed with return code {}, stderr:{}, stdout:{}"
                      .format(action, rc, stderr, stdout))
        suma_error.append("SUMA Command: {} => Error: {}".format(cmd, stderr.splitlines()))
        results['msg'] = suma_error
        module.fail_json(**results)

    return rc, stdout


@logged
def suma_list():
    """
    List all SUMA tasks or the task associated with the given task ID
    """
    task = suma_params['task_id']
    if task is None or not task.strip():
        task = ''
    cmd = ['/usr/sbin/suma', '-l', task]
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "SUMA Error: list command: '{}' failed with return code {}" \
              .format(cmd, rc)
        logging.error(msg + ', stderr:{}'.format(stderr))
        logging.error(msg)
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    results['msg'].append('List SUMA tasks:')
    results['msg'].append(stdout.splitlines())


@logged
def check_time(val, mini, maxi):
    """
    Check a value is equal to '*' or is a numeric value in the
    [mini, maxi] range

    arguments:
        val     value to check
        mini    range minimal value
        mini    range maximal value
    """
    if val == '*':
        return True

    if val.isdigit() and mini <= int(val) and maxi >= int(val):
        return True

    return False


@logged
def suma_edit():
    """
    Edit a SUMA task associated with the given task ID

    Depending on the shed_time parameter value, the task wil be scheduled,
        unscheduled or saved
    """
    cmd = '/usr/sbin/suma'
    if suma_params['sched_time'] is None:
        # save
        cmd += ' -w'

    elif not suma_params['sched_time'].strip():
        # unschedule
        cmd += ' -u'

    else:
        # schedule
        minute, hour, day, month, weekday = suma_params['sched_time'].split(' ')

        if check_time(minute, 0, 59) and check_time(hour, 0, 23) \
           and check_time(day, 1, 31) and check_time(month, 1, 12) \
           and check_time(weekday, 0, 6):

            cmd += ' -s "{}"'.format(suma_params['sched_time'])
        else:
            msg = 'Error: SUMA edit command: "{}" Bad schedule time "{}"' \
                  .format(cmd, suma_params['sched_time'])
            logging.error(msg)
            suma_error.append(msg)
            results['msg'] = suma_error
            module.fail_json(**results)

    cmd += ' {}'.format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "SUMA Error: edit command: '{}' failed with return code {}" \
              .format(cmd, rc)
        logging.error(msg + ', stderr:{}'.format(stderr))
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    results['msg'].append('Edit SUMA task {}'.format(suma_params['task_id']))
    results['msg'].append(stdout.splitlines())


@logged
def suma_unschedule():
    """
    Unschedule a SUMA task associated with the given task ID
    """
    cmd = "/usr/sbin/suma -u {}".format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "SUMA Error: unschedule command: '{}' failed with return code {}" \
              .format(cmd, rc)
        logging.error(msg + ', stderr:{}'.format(stderr))
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    results['msg'].append("Unschedule suma task: {}".format(suma_params['task_id']))
    results['msg'].append(stdout.splitlines())


@logged
def suma_delete():
    """
    Delete the SUMA task associated with the given task ID
    """
    cmd = "/usr/sbin/suma -d {}".format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "SUMA Error: delete command: '{}' failed with return code {}" \
              .format(cmd, rc)
        logging.error(msg + ', stderr:{}'.format(stderr))
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    results['msg'].append("Delete SUMA task {}".format(suma_params['task_id']))
    results['msg'].append(stdout.splitlines())


@logged
def suma_config():
    """
    List the SUMA global configuration settings
    """
    cmd = '/usr/sbin/suma -c'
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = "SUMA Error: config command: '{}' failed with return code {}" \
              .format(cmd, rc)
        logging.error(msg + ', stderr:{}'.format(stderr))
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    results['msg'].append('SUMA global configuration settings:')
    results['msg'].append(stdout.splitlines())


@logged
def suma_default():
    """
    List default SUMA tasks
    """
    cmd = '/usr/sbin/suma -D'
    rc, stdout, stderr = module.run_command(cmd)

    if rc != 0:
        msg = 'SUMA Error: default command: "{}" failed with return code {}' \
              .format(cmd, rc)
        logging.error(msg + ', stderr:{}'.format(stderr))
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    results['msg'].append('SUMA default task:')
    results['msg'].append(stdout.splitlines())


@logged
def suma_download():
    """
    Download / Install (or preview) action

    suma_params['action'] should be set to either 'preview' or 'download'.

    First compute all Suma request options. Then preform a Suma preview, parse
    output to check there is something to download, if so, do a suma download
    if needed (if action is Download). If suma download output mentions there
    is downloaded items, then use install_all_updates command to install them.
    """
    global logdir

    req_oslevel = suma_params['req_oslevel']
    if req_oslevel is None or not req_oslevel.strip() or req_oslevel.upper() == 'LATEST':
        req_oslevel = 'Latest'
        suma_params['req_oslevel'] = req_oslevel

    if re.match(r"^([0-9]{4})(|-00|-00-00|-00-00-0000)$", req_oslevel):
        msg = 'Specify a non 0 value for the Technical Level or the Service Pack'
        logging.error(msg)
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    # =========================================================================
    # compute SUMA request type based on oslevel property
    # =========================================================================
    rq_type = compute_rq_type(suma_params['req_oslevel'])
    if rq_type == 'ERROR':
        msg = "SUMA Error: Invalid oslevel: '{}'".format(suma_params['req_oslevel'])
        logging.error(msg)
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    suma_params['RqType'] = rq_type

    logging.debug("SUMA req Type: {}".format(rq_type))

    # =========================================================================
    # compute SUMA request name based on metadata info
    # =========================================================================
    # TODO why compute_rq_name was disabled?
    rc, rq_name = compute_rq_name(rq_type, suma_params['req_oslevel'])
    if rc != 0:
        msg = "SUMA Error: compute_rq_name - rc:{}, error:{}" \
              .format(rc, rq_name)
        logging.error(msg)
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    rq_name = suma_params['req_oslevel']
    suma_params['RqName'] = rq_name

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
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    # =========================================================================
    # metadata does not match any fixes
    # =========================================================================
    if not rq_name or not rq_name.strip():
        msg = "SUMA - Error: oslevel {} doesn't match any fixes" \
              .format(suma_params['req_oslevel'])
        logging.error(msg)
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    logging.debug("Suma req Name: {}".format(rq_name))

    # =========================================================================
    # compute suma dl target
    # =========================================================================
    rc, dl_target = compute_dl_target(suma_params['download_dir'])
    if rc != 0:
        msg = "SUMA Error: compute_dl_target - {}".format(dl_target)
        logging.error(msg)
        suma_error.append(msg)
        results['msg'] = suma_error
        module.fail_json(**results)

    suma_params['DLTarget'] = dl_target

    # display user message
    logging.debug("DL target: {}".format(dl_target))
    logging.info("The download location will be: {}.".format(dl_target))

    if rq_type == 'Latest':
        logging.info("{} is the Latest SP of TL {}."
                     .format(rq_name, filter_ml))

    suma_params['Comments'] = '"Packages for updates from {} to {}"'\
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
    rc, stdout = suma_command('Preview')
    logging.debug("SUMA preview stdout:{}".format(stdout))

    # parse output to see if there is something to download
    downloaded = 0
    failed = 0
    skipped = 0
    for line in stdout.rstrip().splitlines():
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
    results['msg'].append(msg)

    # If action is preview or nothing is available to download, we are done
    # else download what is found (and install if necessary)
    if suma_params['action'] == 'preview' or (downloaded == 0 and skipped == 0):
        return

    # ================================================================
    # SUMA command for download
    # ================================================================
    if downloaded != 0:
        rc, stdout = suma_command('Download')
        logging.debug("SUMA dowload stdout:{}".format(stdout))

        # parse output to see if there is something downloaded
        downloaded = 0
        failed = 0
        skipped = 0
        for line in stdout.rstrip().splitlines():
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
        if downloaded == 0 and skipped == 0:
            # All expected download have failed
            logging.error(msg)
            results['msg'].append(msg)
            return
        logging.info(msg)
        results['msg'].append(msg)

        if downloaded != 0:
            results['changed'] = True

    # ===========================================================
    # Install updates
    # ===========================================================
    if not suma_params['download_only']:
        cmd = "/usr/sbin/install_all_updates -Yd {}".format(suma_params['DLTarget'])

        logging.debug("SUMA command:{}".format(cmd))
        results['msg'].append("SUMA command:{}".format(cmd))

        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "SUMA Error: install_all_updates command failed with return code {}" \
                  .format(rc)
            logging.error(msg + ", stderr:{}, stdout:{}".format(stderr, stdout))
            msg += " Review {}/suma_debug.log for status.".format(logdir)
            suma_error.append(msg)
            results['msg'] = suma_error
            module.fail_json(**results)
        else:
            msg = "Install all updates output: {}".format(stdout)
            logging.info(msg)


##############################################################################

def main():
    global module
    global results
    global suma_params
    global logdir

    module = AnsibleModule(
        argument_spec=dict(
            oslevel=dict(required=False, type='str'),
            action=dict(required=False,
                        choices=['download', 'preview', 'list', 'edit',
                                 'unschedule', 'delete', 'config', 'default'],
                        type='str', default='download'),
            download_dir=dict(required=False, type='path'),
            download_only=dict(required=False, type='bool', default=False),
            task_id=dict(required=False, type='str'),
            sched_time=dict(required=False, type='str'),
            description=dict(required=False, type='str'),
            metadata_dir=dict(required=False, type='path', default=logdir + '/metadata'),
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

    results = dict(
        changed=False,
        meta={'messages': []}
    )

    # Open log file
    if not os.path.exists(logdir):
        os.makedirs(logdir, mode=0o744)
    logging.basicConfig(
        filename=logdir + "/suma_debug.log",
        format='[%(asctime)s] %(levelname)s: [%(funcName)s:%(thread)d] %(message)s',
        level=logging.DEBUG)

    logging.debug('*** START ***')
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

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

    suma_params['action'] = action
    suma_params['download_only'] = download_only
    suma_params['description'] = description
    suma_params['metadata_dir'] = module.params['metadata_dir']

    # ========================================================================
    # switch action
    # ========================================================================
    if action == 'list':
        suma_params['task_id'] = task_id
        suma_list()

    elif action == 'edit':
        suma_params['task_id'] = task_id
        suma_params['sched_time'] = sched_time
        suma_edit()

    elif action == 'unschedule':
        suma_params['task_id'] = task_id
        suma_unschedule()

    elif action == 'delete':
        suma_params['task_id'] = task_id
        suma_delete()

    elif action == 'config':
        suma_config()

    elif action == 'default':
        suma_default()

    elif action == 'download' or action == 'preview':
        suma_params['req_oslevel'] = req_oslevel
        suma_params['download_dir'] = download_dir
        suma_download()

    # ========================================================================
    # Exit
    # ========================================================================

    msg = 'Suma {} completed successfully'.format(action)
    logging.info(msg)
    results['suma_output'] = results['msg']
    results['msg'] = [msg]
    module.exit_json(**results)


if __name__ == '__main__':
    main()
