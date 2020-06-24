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
module: suma
short_description: Download/Install fixes, SP or TL on an AIX server.
description:
- Creates a task to automate the download and installation of technology level (TL)
  and service packs (SP) from a fix server using the Service Update Management
  Assistant (SUMA).
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Controls the action to be performed.
    - C(download) to download and install all fixes.
    - C(preview) to execute all the checks without downloading the fixes.
    - C(list) to list all SUMA tasks.
    - C(edit) to edit an exiting SUMA task.
    - C(run) to run an exiting SUMA task.
    - C(unschedule) to remove any scheduling information for the specified SUMA task.
    - C(delete) to delete a SUMA task and remove any schedules for this task.
    - C(config) to list global SUMA configuration settings.
    - C(default) to list default SUMA tasks.
    type: str
    choices: [ download, preview, list, edit, run, unschedule, delete, config, default ]
    default: preview
  oslevel:
    description:
    - Specifies the Operating System level to update to;
    - C(Latest) indicates the latest SP suma can update the target to (for the current TL).
    - C(xxxx-xx(-00-0000)) sepcifies a TL.
    - C(xxxx-xx-xx-xxxx) or C(xxxx-xx-xx) specifies a SP.
    - Required when I(action=download) or I(action=preview).
    type: str
    default: Latest
  download_dir:
    description:
    - Directory where updates are downloaded.
    - Can be used if I(action=download) or I(action=preview).
    type: path
    default: /usr/sys/inst.images
  download_only:
    description:
    - Download only. Do not perform installation of updates.
    - Can be used if I(action=download) or I(action=preview).
    type: bool
    default: no
  last_sp:
    description:
    - Specifies to download the last SP of the TL specified in I(oslevel). If no is specified only the TL is downloaded.
    - Can be used if I(action=download) or I(action=preview).
    type: bool
    default: no
  extend_fs:
    description:
    - Specifies to automatically extends the filesystem if needed. If no is specified and additional space is required for the download, no download occurs.
    - Can be used if I(action=download) or I(action=preview).
    type: bool
    default: yes
  task_id:
    description:
    - SUMA task identification number.
    - Can be used if I(action=list) or I(action=edit) or I(action=delete) or I(action=run) or I(action=unschedule).
    - Required when I(action=edit) or I(action=delete) or I(action=run) or I(action=unschedule).
    type: str
  sched_time:
    description:
    - Schedule time. Specifying an empty or space filled string results in unscheduling the task. If not set, it saves the task.
    - Can be used if I(action=edit).
    type: str
  save_task:
    description:
    - Saves the SUMA task. The task is saved, allowing scheduling information to be added later.
    - Can be used if I(action=download) or I(action=preview).
    - If I(oslevel) is a TL and I(last_sp=yes) the task is saved with the last SP available at the saving time.
    type: bool
    default: no
  description:
    description:
    - Display name for SUMA task.
    - If not set the will be labelled 'I(action) request for oslevel I(oslevel)'
    - Can be used for I(action=download) or I(action=preview).
    type: str
  metadata_dir:
    description:
    - Directory where metadata files are downloaded.
    - Can be used if I(action=download) or I(action=preview) when I(last_sp=yes) or I(oslevel) is not exact, for example I(oslevel=Latest).
    type: path
    default: /var/adm/ansible/metadata
'''

EXAMPLES = r'''
- name: Check, download and install system updates for the current oslevel of the system
  suma:
    action: download
    oslevel: Latest
    download_dir: /usr/sys/inst.images

- name: Check and download required to update to SP 7.2.3.2
  suma:
    action: download
    oslevel: '7200-03-02'
    download_only: yes
    download_dir: /tmp/dl_updt_7200-03-02
  when: ansible_distribution == 'AIX'

- name: Check, download and install to latest SP of TL 7.2.4
  suma:
    action: download
    oslevel: '7200-04'
    last_sp: yes
    extend_fs: no

- name: Check, download and install to TL 7.2.3
  suma:
    action: download
    oslevel: '7200-03'
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Suma preview completed successfully'
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
            description: Details on errors/warnings/inforamtion
            returned: always
            type: list
            elements: str
            sample: "Parameter last_sp=yes is ignored when oslevel is a TL 7200-02-00"
    sample:
        "meta": {
            "messages": [
                "Parameter last_sp=yes is ignored when oslevel is a TL ",
                "Suma metadata: 7200-02-01-1732 is the latest SP of TL 7200-02",
                ...,
            ]
        }
'''

import os
import re
import glob
import shutil

from ansible.module_utils.basic import AnsibleModule

module = None
results = None
suma_params = {}


def compute_rq_type(oslevel, last_sp):
    """
    Compute rq_type to use in a suma request based on provided oslevel.
    arguments:
        oslevel level of the OS
        last_sp boolean specifying if we should get the last SP
    return:
        Latest when oslevel is blank or latest (not case sensitive)
        SP     when oslevel is a TL (6 digits: xxxx-xx) and last_sp==True
        TL     when oslevel is xxxx-xx(-00-0000)
        SP     when oslevel is xxxx-xx-xx(-xxxx)
        ERROR  when oslevel is not recognized
    """
    global results

    if oslevel is None or not oslevel.strip() or oslevel == 'Latest':
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})$", oslevel) and last_sp:
        return 'SP'
    if re.match(r"^([0-9]{4}-[0-9]{2})(|-00|-00-0000)$", oslevel):
        if last_sp:
            msg = "Parameter last_sp={0} is ignored when oslevel is a TL {1}.".format(last_sp, oslevel)
            module.log(msg)
            results['meta']['messages'].append(msg)
        return 'TL'
    if re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})(|-[0-9]{4})$", oslevel):
        return 'SP'

    return 'ERROR'


def find_sp_version(file):
    """
    Open and parse the provided file to find higher SP version
    arguments:
        file    path of the file to parse
    return:
       sp_version   value found or None
    """
    sp_version = None
    module.debug("opening file: {0}".format(file))
    myfile = open(file, "r")
    for line in myfile:
        # module.debug("line: {0}".format(line.rstrip()))
        match_item = re.match(
            r"^<SP name=\"([0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4})\">$",
            line.rstrip())
        if match_item:
            version = match_item.group(1)
            module.debug("matched line: {0}, version={1}".format(line.rstrip(), version))
            if sp_version is None or version > sp_version:
                sp_version = version
            break
    myfile.close()

    return sp_version


def compute_rq_name(rq_type, oslevel, last_sp):
    """
    Compute rq_name.
        if oslevel is a TL then return the SP extratced from it
        if oslevel is a complete SP (12 digits) then return RqName = oslevel
        if oslevel is an incomplete SP (8 digits) or equal Latest then execute
        a metadata suma request to find the complete SP level (12 digits).
    The return format depends on rq_type value,
        - for Latest: return None
        - for TL: return the TL value in the form xxxx-xx
        - for SP: return the SP value in the form xxxx-xx-xx-xxxx

    arguments:
        rq_type     type of request, can be Latest, SP or TL
        oslevel     requested oslevel
        last_sp     if set get the latest SP level for specified oslevel
    note:
        Exits with fail_json in case of error
    return:
       rq_name value
    """
    global results
    global suma_params

    rq_name = ''
    if rq_type == 'Latest':
        return None

    elif rq_type == 'TL':
        rq_name = re.match(r"^([0-9]{4}-[0-9]{2})(|-00|-00-0000)$",
                           oslevel).group(1)

    elif rq_type == 'SP' and re.match(r"^[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]{4}$", oslevel):
        rq_name = oslevel

    else:
        # oslevel has either a TL format (xxxx-xx) or a short SP format (xxxx-xx-xx)

        # Build the FilterML for metadata request from the oslevel
        metadata_filter_ml = oslevel[:7]
        if not metadata_filter_ml:
            msg = "Cannot build minimum level filter based on the target OS level {0}".format(oslevel)
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)

        if not os.path.exists(suma_params['metadata_dir']):
            os.makedirs(suma_params['metadata_dir'])

        # Build suma command to get metadata
        cmd = ['/usr/sbin/suma', '-x', '-a', 'Action=Metadata', '-a', 'RqType=Latest']
        cmd += ['-a', 'DLTarget={0}'.format(suma_params['metadata_dir'])]
        cmd += ['-a', 'FilterML={0}'.format(metadata_filter_ml)]
        cmd += ['-a', 'DisplayName="{0}"'.format(suma_params['description'])]
        cmd += ['-a', 'FilterDir={0}'.format(suma_params['metadata_dir'])]

        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "Suma metadata command '{0}' failed with return code {1}".format(' '.join(cmd), rc)
            module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
            results['stdout'] = stdout
            results['stderr'] = stderr
            results['msg'] = msg
            module.fail_json(**results)
        module.debug("SUMA command '{0}' rc:{1}, stdout:{2}".format(' '.join(cmd), rc, stdout))

        sp_version = None
        if len(oslevel) == 10:
            # find latest SP build number for the SP
            file_name = suma_params['metadata_dir'] + "/installp/ppc/" + oslevel + ".xml"
            sp_version = find_sp_version(file_name)
        else:
            # find latest SP build number for the TL
            file_name = suma_params['metadata_dir'] + "/installp/ppc/" + "*.xml"
            files = glob.glob(file_name)
            module.debug("searching SP in files: {0}".format(files))
            for cur_file in files:
                version = find_sp_version(cur_file)
                if sp_version is None or version > sp_version:
                    sp_version = version

        if sp_version is None or not sp_version.strip():
            msg = "Cannot determine SP version for OS level {0}: 'SP name' not found in metadata files {1}".format(oslevel, files)
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)

        shutil.rmtree(suma_params['metadata_dir'])

        rq_name = sp_version
        msg = 'Suma metadata: {0} is the latest SP of {1}'.format(rq_name, oslevel)
        module.log(msg)
        results['meta']['messages'].append(msg)

    if not rq_name or not rq_name.strip():  # should never happen
        msg = "OS level {0} does not match any fixes".format(oslevel)
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)

    return rq_name


def suma_command(action):
    """
    Run a suma command.

    arguments:
        action   preview, download or install
    note:
        Exits with fail_json in case of error
    return:
       stdout  suma command output
    """
    global results
    global suma_params

    rq_type = suma_params['RqType']
    cmd = ['/usr/sbin/suma', '-x', '-a', 'RqType={0}'.format(rq_type)]
    cmd += ['-a', 'Action={0}'.format(action)]
    cmd += ['-a', 'DLTarget={0}'.format(suma_params['DLTarget'])]
    cmd += ['-a', 'DisplayName={0}'.format(suma_params['description'])]
    cmd += ['-a', 'FilterDir={0}'.format(suma_params['DLTarget'])]

    if rq_type != 'Latest':
        cmd += ['-a', 'RqName={0}'.format(suma_params['RqName'])]

    if suma_params['extend_fs']:
        cmd += ['-a', 'Extend=y']
    else:
        cmd += ['-a', 'Extend=n']

    # save the task only if that's the last action
    if suma_params['action'].upper() == action.upper() and suma_params['save_task']:
        cmd += ['-w']

    module.debug("SUMA - Command:{0}".format(' '.join(cmd)))
    results['meta']['messages'].append("SUMA - Command: {0}".format(' '.join(cmd)))

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if rc != 0:
        msg = "Suma {0} command '{1}' failed with return code {2}".format(action, ' '.join(cmd), rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)

    return stdout


def suma_list():
    """
    List all SUMA tasks or the task associated with the given task ID

    note:
        Exits with fail_json in case of error
    """
    global results

    task = suma_params['task_id']
    if task is None or not task.strip():
        cmd = ['/usr/sbin/suma', '-L']
    else:
        cmd = ['/usr/sbin/suma', '-L', task]

    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma list command '{0}' failed with return code {1}".format(' '.join(cmd), rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


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


def suma_edit():
    """
    Edit a SUMA task associated with the given task ID

    Depending on the shed_time parameter value, the task wil be scheduled,
        unscheduled or saved

    note:
        Exits with fail_json in case of error
    """
    global results

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

            cmd += ' -s "{0}"'.format(suma_params['sched_time'])
        else:
            msg = "Suma edit command '{0}' failed: Bad schedule time '{1}'".format(' '.join(cmd), suma_params['sched_time'])
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)

    cmd += ' {0}'.format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma edit command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


def suma_unschedule():
    """
    Unschedule a SUMA task associated with the given task ID

    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = "/usr/sbin/suma -u {0}".format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma unschedule command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


def suma_delete():
    """
    Delete the SUMA task associated with the given task ID

    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = "/usr/sbin/suma -d {0}".format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma delete command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


def suma_run():
    """
    Run the SUMA task associated with the given task ID

    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = "/usr/sbin/suma -x {0}".format(suma_params['task_id'])
    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma run command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


def suma_config():
    """
    List the SUMA global configuration settings

    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = '/usr/sbin/suma -c'
    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma config command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


def suma_default():
    """
    List default SUMA tasks

    note:
        Exits with fail_json in case of error
    """
    global results

    cmd = '/usr/sbin/suma -D'
    rc, stdout, stderr = module.run_command(cmd)

    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc != 0:
        msg = "Suma list default command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)


def suma_download():
    """
    Download / Install (or preview) action

    suma_params['action'] should be set to either 'preview' or 'download'.

    First compute all Suma request options. Then preform a Suma preview, parse
    output to check there is something to download, if so, do a suma download
    if needed (if action is Download). If suma download output mentions there
    is downloaded items, then use install_all_updates command to install them.

    note:
        Exits with fail_json in case of error
    """
    global results
    global suma_params

    # Check oslevel format
    if not suma_params['oslevel'].strip() or suma_params['oslevel'].upper() == 'LATEST':
        suma_params['oslevel'] = 'Latest'
    else:
        if re.match(r"^[0-9]{4}(|-00|-00-00|-00-00-0000)$", suma_params['oslevel']):
            msg = "Bad parameter: oslevel is '{0}', specify a non 0 value for the Technical Level or the Service Pack"\
                  .format(suma_params['oslevel'])
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)
        elif not re.match(r"^[0-9]{4}-[0-9]{2}(|-[0-9]{2}|-[0-9]{2}-[0-9]{4})$", suma_params['oslevel']):
            msg = "Bad parameter: oslevel is '{0}', should repect the format: xxxx-xx or xxxx-xx-xx or xxxx-xx-xx-xxxx"\
                  .format(suma_params['oslevel'])
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)

    # =========================================================================
    # compute SUMA request type based on oslevel property
    # =========================================================================
    rq_type = compute_rq_type(suma_params['oslevel'], suma_params['last_sp'])
    if rq_type == 'ERROR':
        msg = "Bad parameter: oslevel is '{0}', parsing error".format(suma_params['oslevel'])
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)

    suma_params['RqType'] = rq_type
    module.debug("SUMA req Type: {0}".format(rq_type))

    # =========================================================================
    # compute SUMA request name based on metadata info
    # =========================================================================
    suma_params['RqName'] = compute_rq_name(rq_type, suma_params['oslevel'], suma_params['last_sp'])
    module.debug("Suma req Name: {0}".format(suma_params['RqName']))

    # =========================================================================
    # compute suma dl target
    # =========================================================================
    if not suma_params['download_dir']:
        msg = "Bad parameter: action is {0} but download_dir is '{1}'".format(suma_params['action'], suma_params['download_dir'])
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)
    else:
        suma_params['DLTarget'] = suma_params['download_dir'].rstrip('/')

    module.log("The download location will be: {0}.".format(suma_params['DLTarget']))
    if not os.path.exists(suma_params['DLTarget']):
        os.makedirs(suma_params['DLTarget'])

    # ========================================================================
    # SUMA command for preview
    # ========================================================================
    rc, stdout = suma_command('Preview')
    module.debug("SUMA preview stdout:{0}".format(stdout))

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

    msg = "Preview summary : {0} to download, {1} failed, {2} skipped"\
          .format(downloaded, failed, skipped)
    module.log(msg)

    # If action is preview or nothing is available to download, we are done
    if suma_params['action'] == 'preview':
        results['meta']['messages'].append(msg)
        return
    if downloaded == 0 and skipped == 0:
        return
    # else continue
    results['meta']['messages'].extend(stdout.rstrip().splitlines())
    results['meta']['messages'].append(msg)

    # ================================================================
    # SUMA command for download
    # ================================================================
    if downloaded != 0:
        rc, stdout = suma_command('Download')
        module.debug("SUMA dowload stdout:{0}".format(stdout))

        # parse output to see if something has been downloaded
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

        msg = "Download summary : {0} downloaded, {1} failed, {2} skipped"\
              .format(downloaded, failed, skipped)

        if downloaded == 0 and skipped == 0:
            # All expected download have failed
            module.log(msg)
            results['meta']['messages'].append(msg)
            return

        module.log(msg)
        results['meta']['messages'].extend(stdout.rstrip().splitlines())
        results['meta']['messages'].append(msg)

        if downloaded != 0:
            results['changed'] = True

    # ===========================================================
    # Install updates
    # ===========================================================
    if not suma_params['download_only']:
        cmd = "/usr/sbin/install_all_updates -Yd {0}".format(suma_params['DLTarget'])

        module.debug("SUMA command:{0}".format(cmd))
        results['meta']['messages'].append(msg)

        rc, stdout, stderr = module.run_command(cmd)

        results['stdout'] = stdout
        results['stderr'] = stderr
        results['changed'] = True

        if rc != 0:
            msg = "Suma install command '{0}' failed with return code {1}.".format(cmd, rc)
            module.log(msg + ", stderr:{0}, stdout:{1}".format(stderr, stdout))
            results['msg'] = msg
            module.fail_json(**results)

        module.log("Suma install command output: {0}".format(stdout))


##############################################################################

def main():
    global module
    global results
    global suma_params

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=False,
                        choices=['download', 'preview', 'list', 'edit', 'run',
                                 'unschedule', 'delete', 'config', 'default'],
                        type='str', default='preview'),
            oslevel=dict(required=False, type='str', default='Latest'),
            last_sp=dict(required=False, type='bool', default=False),
            extend_fs=dict(required=False, type='bool', default=True),
            download_dir=dict(required=False, type='path', default='/usr/sys/inst.images'),
            download_only=dict(required=False, type='bool', default=False),
            save_task=dict(required=False, type='bool', default=False),
            task_id=dict(required=False, type='str'),
            sched_time=dict(required=False, type='str'),
            description=dict(required=False, type='str'),
            metadata_dir=dict(required=False, type='path', default='/var/adm/ansible/metadata'),
        ),
        required_if=[
            ['action', 'edit', ['task_id']],
            ['action', 'delete', ['task_id']],
            ['action', 'run', ['task_id']],
            ['action', 'download', ['oslevel']],
            ['action', 'preview', ['oslevel']],
            ['action', 'unschedule', ['task_id']],
        ],
        supports_check_mode=True
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        meta={'messages': []},
    )

    module.debug('*** START ***')
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    action = module.params['action']

    # switch action
    if action == 'list':
        suma_params['task_id'] = module.params['task_id']
        suma_list()

    elif action == 'edit':
        suma_params['task_id'] = module.params['task_id']
        suma_params['sched_time'] = module.params['sched_time']
        suma_edit()

    elif action == 'unschedule':
        suma_params['task_id'] = module.params['task_id']
        suma_unschedule()

    elif action == 'delete':
        suma_params['task_id'] = module.params['task_id']
        suma_delete()

    elif action == 'run':
        suma_params['task_id'] = module.params['task_id']
        suma_run()

    elif action == 'config':
        suma_config()

    elif action == 'default':
        suma_default()

    elif action == 'download' or action == 'preview':
        suma_params['oslevel'] = module.params['oslevel']
        suma_params['download_dir'] = module.params['download_dir']
        suma_params['metadata_dir'] = module.params['metadata_dir']
        suma_params['download_only'] = module.params['download_only']
        suma_params['save_task'] = module.params['save_task']
        suma_params['last_sp'] = module.params['last_sp']
        suma_params['extend_fs'] = module.params['extend_fs']
        if module.params['description']:
            suma_params['description'] = module.params['description']
        else:
            suma_params['description'] = "{0} request for oslevel {1}".format(action, module.params['oslevel'])

        suma_params['action'] = action
        suma_download()

    # Exit
    msg = 'Suma {0} completed successfully'.format(action)
    module.log(msg)
    results['msg'] = msg
    module.exit_json(**results)


if __name__ == '__main__':
    main()
