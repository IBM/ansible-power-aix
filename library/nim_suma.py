#!/usr/bin/python
#
# Copyright 2016, International Business Machines Corporation
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
#

######################################################################
"""AIX SUMA: download fixes, SP or TL on a NIM server"""

import os
import re
import glob
import shutil
import subprocess
import threading
import logging
# Ansible module 'boilerplate'
# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = """
------
module: nim_suma
author: "Cyril Bouhallier, Patrice Jacquin"
version_added: "1.0.0"
requirements: [ AIX ]
"""


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def min_oslevel(dic):
    """
    Find the minimun value of a dictionnary.

    arguments:
        dict - Dictionnary {machine: oslevel}
    return:
        minimun oslevel from the dictionnary
    """
    oslevel_min = None

    for key, value in iter(dic.items()):
        if oslevel_min is None or value < oslevel_min:
            oslevel_min = value

    return oslevel_min


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def max_oslevel(dic):
    """
    Find the maximum value of a the oslevel dictionary.

    arguments:
        dic - Dictionnary {client: oslevel}
    return:
        maximum oslevel from the dictionnary
    """
    oslevel_max = None

    for key, value in iter(dic.items()):
        if oslevel_max is None or value > oslevel_max:
            oslevel_max = value

    return oslevel_max


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def run_cmd(machine, result):
    """Run command function, command to be 'threaded'.

    The thread then store the outpout in the dedicated slot of the result
    dictionnary.

    arguments:
        machine (str): The name machine
        result  (dict): The result of the command
    """
    if machine == 'master':
        cmd = ['/usr/bin/oslevel', '-s']
    else:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
               machine,
               '"/usr/bin/oslevel -s"']

    proc = subprocess.Popen(cmd, shell=False, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE)

    # return stdout only ... stripped!
    result[machine] = proc.communicate()[0].rstrip()


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def expand_targets(targets_list, nim_clients):
    """
    Expand the list of the targets.

    a taget name could be of the following form:
        target*       all the NIM client machines whose name starts
                          with 'target'
        target[n1:n2] where n1 and n2 are numeric: target<n1> to target<n2>
        * or ALL      all the NIM client machines
        client_name   the NIM client named 'client_name'
        master        the NIM master

        sample:  target[1:5] target12 other_target*

    arguments:
        machine (str): The name machine
        result  (dict): The result of the command

    return: the list of the existing machines matching the target list
    """
    clients = []
    if len(targets_list) == 0:
        return clients

    for target in targets_list:

        # -----------------------------------------------------------
        # Build target(s) from: range i.e. quimby[7:12]
        # -----------------------------------------------------------
        rmatch = re.match(r"(\w+)\[(\d+):(\d+)\]", target)
        if rmatch:

            name = rmatch.group(1)
            start = rmatch.group(2)
            end = rmatch.group(3)

            for i in range(int(start), int(end) + 1):
                # target_results.append("{0}{1:02}".format(name, i))
                curr_name = name + str(i)
                if curr_name in nim_clients:
                    clients.append(curr_name)

            continue

        # -----------------------------------------------------------
        # Build target(s) from: val*. i.e. quimby*
        # -----------------------------------------------------------
        rmatch = re.match(r"(\w+)\*$", target)
        if rmatch:

            name = rmatch.group(1)

            for curr_name in nim_clients:
                if re.match(r"^%s\.*" % name, curr_name):
                    clients.append(curr_name)

            continue

        # -----------------------------------------------------------
        # Build target(s) from: all or *
        # -----------------------------------------------------------
        if target.upper() == 'ALL' or target == '*':
            clients = nim_clients
            continue

        # -----------------------------------------------------------
        # Build target(s) from: quimby05 quimby08 quimby12
        # -----------------------------------------------------------
        if (target in nim_clients) or (target == 'master'):
            clients.append(target)

    return list(set(clients))


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def exec_cmd(cmd, shell=False):
    """Execute a command.

    arguments:
        cmd    (str): The command to be executed
        shell (bool): execute cmd through the shell if set (vulnerable to shell
                      injection when cmd is from user inputs). If cmd is a string
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def get_nim_clients(module):
    """
    Get the list of the standalones defined on the NIM master.

    return the list of the name of the standlone objects defined on the
           NIM master.
    """
    std_out = ''
    std_err = ''
    clients_list = []

    cmd = ['lsnim', '-t', 'standalone']

    try:
        proc = subprocess.Popen(cmd, shell=False, stdin=None,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (std_out, std_err) = proc.communicate()
    except Exception as excep:
        msg = "Command: {} Exception.Args{} =>Data:{} ... Error :{}"\
              .format(cmd, excep.args, std_out, std_err)
        SUMA_ERROR.append(msg)
        logging.error(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    # nim_clients list
    for line in std_out.rstrip().split('\n'):
        clients_list.append(line.split()[0])

    return clients_list


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def get_nim_lpp_source():
    """
    Get the list of the lpp_source defined on the NIM master.

    arguments:
        None

    return:
        ret code: 0 - OK
                  1 - CalledProcessError exception
                  2 - other exception
        lpp_source_list: dictionary key, value
                key = lpp source name
                value = lpp source location
    """
    std_out = ''
    lpp_source_list = {}

    cmd = 'LC_ALL=C lsnim -t lpp_source -l'

    logging.debug("SUMA command:{}".format(cmd))

    ret, std_out = exec_cmd(cmd, shell=True)
    if ret != 0:
        logging.error("SUMA command error rc:{}, error: {}"
                      .format(ret, std_out))
        return ret, std_out

    # lpp_source list
    for line in std_out.rstrip().split('\n'):
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
        else:
            match_loc = re.match(r"^\s+location\s+=\s+(\S+)$", line)
            if match_loc:
                loc = match_loc.group(1)
                lpp_source_list[obj_key] = loc

    return 0, lpp_source_list


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def compute_rq_type(oslevel, empty_list):
    """Compute rq_type.

    return:
        Latest when oslevel is blank or latest (not case sensitive)
        Latest when oslevel is a TL (6 digits) and target list is empty
        TL     when oslevel is xxxx-xx(-00-0000)
        SP     when oslevel is xxxx-xx-xx(-xxxx)
        ERROR  when oslevel is not recognized
    """
    if oslevel is None or not oslevel.strip() or oslevel.upper() == 'LATEST':
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})$", oslevel) and empty_list:
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})(|-00|-00-0000)$", oslevel):
        return 'TL'
    if re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})(|-[0-9]{4})$", oslevel):
        return 'SP'

    return 'ERROR'


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def compute_rq_name(rq_type, oslevel, clients_target_oslevel):
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
        clients_target__oslevel  oslevel of each selected client

    return:
       return code : 0 - OK
                     1 - CalledProcessError exception
                     2 - other exception
       rq_name value or stderr in case of error
    """
    metadata_dir = "/tmp/ansible/metadata"  # <TODO> get env variable for that
    rq_name = ''
    if rq_type == 'Latest':
        if not clients_target_oslevel:
            if clients_target_oslevel == 'Latest':
                logging.error('Error: target oslevel cannot be "Latest"'
                              'check you can get the oslevel on targets')
                return 2
            metadata_filter_ml = oslevel[:7]
            if len(metadata_filter_ml) == 4:
                metadata_filter_ml += "-00"
        else:
            # search first the bigest technical level from client list
            tl_max = re.match(
                r"^([0-9]{4}-[0-9]{2})(|-[0-9]{2}|-[0-9]{2}-[0-9]{4})$",
                max_oslevel(clients_target_oslevel)).group(1)

            # search also the lowest technical level from client list
            tl_min = re.match(
                r"^([0-9]{4}-[0-9]{2})(|-[0-9]{2}|-[0-9]{2}-[0-9]{4})$",
                min_oslevel(clients_target_oslevel)).group(1)

            # warn the user if bigest and lowest tl do not belong
            # to the same release
            if re.match(r"^([0-9]{4})", tl_min).group(1) \
               != re.match(r"^([0-9]{4})", tl_max).group(1):
                logging.warning("Error: Release level mismatch, "
                                "only AIX {} SP/TL will be downloaded\n\n"
                                .format(tl_max[:2]))

            # tl_max is used to get metadata then to get latest SP
            metadata_filter_ml = tl_max

        if not metadata_filter_ml:
            logging.error(
                'Error: cannot discover filter ml based on the list of targets')
            raise Exception(
                'Error: cannot discover filter ml based on the list of targets')

        if not os.path.exists(metadata_dir):
            os.makedirs(metadata_dir)

        # Build suma command to get metadata
        cmd = 'LC_ALL=C /usr/sbin/suma -x -a Action=Metadata '\
              '-a RqType=Latest -a FilterML={} -a DLTarget={} -a DisplayName="{}"'\
              .format(metadata_filter_ml, metadata_dir, PARAMS['Description'])

        logging.debug("SUMA command:{}".format(cmd))

        ret, stdout = exec_cmd(cmd, shell=True)
        if ret != 0:
            logging.error("SUMA command error rc:{}, error: {}"
                          .format(ret, stdout))
            return ret, stdout

        logging.debug("SUMA command rc:{}".format(ret))

        # find latest SP build number for the highest TL
        sp_version = None
        file_name = metadata_dir + "/installp/ppc/" \
                                 + metadata_filter_ml + "*.xml"
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
        # target verstion = TL part of the requested version
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
                  '-a RqType=Latest -a FilterML={} -a DLTarget={} -a DisplayName="{}"'\
                  .format(metadata_filter_ml, metadata_dir, PARAMS['Description'])

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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def compute_filter_ml(clients_target_oslevel, rq_name):

    """
    Compute the suma filter ML.
    returns the TL part of rq_name if there is no target machine.
    returns the lowest Technical Level from the target client list
        (clients_oslevel) that is at the same release as the
        requested target os_level (rq_name).
    """
    minimum_oslevel = None
    filter_ml = None
    if not clients_target_oslevel:
        filter_ml = rq_name[:7]
        if len(filter_ml) == 4:
            filter_ml += "-00"
    else:
        for key, value in iter(clients_target_oslevel.items()):
            if re.match(r"^([0-9]{4})", value).group(1) == rq_name[:4] \
               and re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})", value).group(1) < rq_name[:10] \
               and (minimum_oslevel is None or value < minimum_oslevel):
                minimum_oslevel = value

        if minimum_oslevel is not None:
            filter_ml = minimum_oslevel[:7]

    return filter_ml


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def compute_lpp_source_name(location, rq_name):
    """
    Compute lpp source name based on the location.
    return: the name of the lpp_source

    When no location is specified or the location is a path the
        lpp_source_name is the <rq_name>-lpp_source
    else le lpp_source_name is the location value
    if location contains a relative path it will be considered as a
    lpp_source, and will not be find in lpp source list
    because "/" is a wrong caracter fo lpp_source name
    """
    lpp_src = ''
    oslevel = rq_name
    if not location or not location.strip() or location[0] == '/':
        if re.match(r"^([0-9]{4}-[0-9]{2})$", oslevel):
            oslevel = oslevel + '-00-0000'
        lpp_src = "{}-lpp_source".format(oslevel)
    else:
        lpp_src = location.rstrip('/')

    return lpp_src


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def compute_dl_target(location, lpp_source, nim_lpp_sources):
    """
    Compute suma DL target based on lpp source name.

    When the location is empty, set the location path to
        /usr/sys/inst.images
    Check if a lpp_source NIM resource already exist and check the path is
        the same
    When the location is not a path, check that a NIM lpp_source
        corresponding to the location value exists, and returns the
        location path of this NIM ressource.

    return:
        return code : 0 - OK
                      1 - if error
        dl_target value or msg in case of error
    """
    if not location or not location.strip():
        loc = "/usr/sys/inst.images"
    else:
        loc = location.rstrip('/')

    if loc[0] == '/':
        dl_target = "{}/{}".format(loc, lpp_source)
        if lpp_source in nim_lpp_sources \
           and nim_lpp_sources[lpp_source] != dl_target:
            return 1, "SUMA Error: lpp source location mismatch. It already " \
                      "exists a lpp source '{}' with a location different as '{}'" \
                      .format(lpp_source, dl_target)
    else:
        if loc not in nim_lpp_sources:
            return 1, "SUMA Error: lpp_source: '{}' does not exist" \
                      .format(loc)

        dl_target = nim_lpp_sources[loc]

    return 0, dl_target


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def suma_command(module, action):
    """
    Run a suma command.

    parameters
        action   preview or download

    return:
       ret     suma command return code
       stdout  suma command output
    """
    rq_type = PARAMS['RqType']
    if rq_type == 'Latest':
        rq_type = 'SP'

    suma_cmd = 'LC_ALL=C /usr/sbin/suma -x -a RqType={} -a Action={} '\
               '-a FilterML={} -a DLTarget={} -a RqName={} -a DisplayName="{}"'\
               .format(rq_type, action,
                       PARAMS['FilterMl'], PARAMS['DLTarget'],
                       PARAMS['RqName'], PARAMS['Description'])

    logging.debug("SUMA - Command:{}".format(suma_cmd))
    SUMA_OUTPUT.append("SUMA - Command:{}".format(suma_cmd))

    ret, stdout = exec_cmd(suma_cmd, shell=True)
    if ret != 0:
        logging.error("Error: suma {} command failed with return code {}"
                      .format(action, ret))
        SUMA_ERROR.append("SUMA Command: {} => Error :{}".format(suma_cmd, stdout.split('\n')))
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    return ret, stdout


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def nim_command(module):
    """
    Run a 'nim -o define' command

    parameters
        action

    return:
       ret     NIM command return code
       stdout  NIM command output
    """
    nim_cmd = 'LC_ALL=C /usr/sbin/nim  -o define  -t lpp_source  -a server=master '\
              '-a location={} -a packages=all -a comments={} {}'\
              .format(PARAMS['DLTarget'], PARAMS['Comments'], PARAMS['LppSource'])

    logging.info("NIM - Command:{}".format(nim_cmd))
    SUMA_OUTPUT.append("NIM command:{}".format(nim_cmd))

    ret, stdout = exec_cmd(nim_cmd, shell=True)

    if ret != 0:
        msg = "NIM Command: {}".format(nim_cmd)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        msg = "NIM operation failed - rc:{}".format(ret)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        logging.error("{}".format(stdout))
        SUMA_ERROR.append("{}".format(stdout))
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    return ret, stdout


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
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


# ----------------------------------------------------------------
# ----------------------------------------------------------------
def suma_down_prev(module):
    """
    Dowload (or preview) action
    """

    global SUMA_CHANGED
    global PARAMS
    targets_list = []
    empty_list = False
    if PARAMS['targets'] != '':
        targets_list = PARAMS['targets'].split(' ')
    else:
        empty_list = True
    req_oslevel = PARAMS['req_oslevel']
    if req_oslevel is None \
       or not req_oslevel.strip() \
       or req_oslevel.upper() == 'LATEST':
        req_oslevel = 'Latest'
        PARAMS['req_oslevel'] = req_oslevel

    if not targets_list:
        if req_oslevel == 'Latest':
            msg = 'Oslevel target could not be empty or equal "Latest" when' \
                  ' target machine list is empty'
            logging.error(msg)
            SUMA_ERROR.append(msg)
            module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)
        elif re.match(r"^([0-9]{4}-[0-9]{2})(-00|-00-0000)$", req_oslevel):
            msg = 'When no Service Pack is provided , a target machine list is required'
            logging.error(msg)
            SUMA_ERROR.append(msg)
            module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)
    else:
        if re.match(r"^([0-9]{4})(|-00|-00-00|-00-00-0000)$", req_oslevel):
            msg = 'Specify a non 0 value for the Technical Level or the Service Pack'
            logging.error(msg)
            SUMA_ERROR.append(msg)
            module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    # =========================================================================
    # build NIM lpp_source list
    # =========================================================================
    nim_lpp_sources = {}
    ret, nim_lpp_sources = get_nim_lpp_source()
    if ret != 0:
        msg = "SUMA Error: Getting the lpp_source list - rc:{}, error:{}" \
              .format(ret, nim_lpp_sources)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    logging.debug("lpp source list: {}".format(nim_lpp_sources))

    # ===========================================
    # Build nim_clients list
    # ===========================================
    nim_clients = []
    nim_clients = get_nim_clients(module)
    nim_clients.append('master')

    logging.debug("NIM Clients: {}".format(nim_clients))

    # ===========================================
    # Build targets list
    # ===========================================
    target_clients = []
    target_clients = expand_targets(targets_list, nim_clients)
    PARAMS['target_clients'] = target_clients

    logging.info("SUMA - Target list: {}".format(len(targets_list)))
    logging.info("SUMA - Target clients: {}".format(len(target_clients)))

    if len(targets_list) != 0 and len(target_clients) == 0:
        # the tagets_list doesn't match any NIM clients
        msg = "SUMA Error: The target patern '{}' does not match any NIM client" \
              .format(PARAMS['targets'])
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    # =========================================================================
    # Launch threads to collect information on targeted nim clients
    # =========================================================================
    threads = []
    clients_oslevel = {}

    for machine in target_clients:
        process = threading.Thread(target=run_cmd,
                                   args=(machine, clients_oslevel))
        process.start()
        threads.append(process)

    for process in threads:
        process.join()

    logging.debug("oslevel unclean dict: {}".format(clients_oslevel))

    # =========================================================================
    # Delete empty value of dictionnary
    # =========================================================================
    removed_oslevel = []

    for key in [k for (k, v) in clients_oslevel.items() if not v]:
        removed_oslevel.append(key)
        del clients_oslevel[key]

    # Check we have at least one oslevel when a target is specified
    if len(targets_list) != 0 and len(clients_oslevel) == 0:
        msg = "SUMA Error: Cannot retrieve oslevel for any NIM client of the target list"
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    logging.debug("oslevel cleaned dict: {}".format(clients_oslevel))

    if len(removed_oslevel) != 0:
        msg = "SUMA - unavailable client list: {}".format(removed_oslevel)
        SUMA_ERROR.append(msg)
        SUMA_OUTPUT.append(msg)
        logging.warn(msg)

    # =========================================================================
    # compute SUMA request type based on oslevel property
    # =========================================================================
    rq_type = compute_rq_type(PARAMS['req_oslevel'], empty_list)
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
    ret, rq_name = compute_rq_name(rq_type, PARAMS['req_oslevel'], clients_oslevel)
    if ret != 0:
        msg = "SUMA Error: compute_rq_name - rc:{}, error:{}" \
              .format(ret, rq_name)
        logging.error(msg)
        SUMA_OUTPUT.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    PARAMS['RqName'] = rq_name

    logging.debug("Suma req Name: {}".format(rq_name))

    # =========================================================================
    # Compute the filter_ml i.e. the min oslevel from the clients_oslevel
    # =========================================================================
    filter_ml = compute_filter_ml(clients_oslevel, rq_name)
    PARAMS['FilterMl'] = filter_ml

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
    # compute lpp source name based on request name
    # =========================================================================
    lpp_source = compute_lpp_source_name(PARAMS['location'], rq_name)
    PARAMS['LppSource'] = lpp_source

    logging.debug("Lpp source name: {}".format(lpp_source))

    # =========================================================================
    # compute suma dl target based on lpp source name
    # =========================================================================
    ret, dl_target = compute_dl_target(PARAMS['location'], lpp_source,
                                       nim_lpp_sources)
    if ret != 0:
        msg = "SUMA Error: compute_dl_target - {}".format(dl_target)
        logging.error(msg)
        SUMA_ERROR.append(msg)
        module.fail_json(msg=SUMA_ERROR, suma_output=SUMA_OUTPUT)

    PARAMS['DLTarget'] = dl_target

    logging.debug("DL target: {}".format(dl_target))

    # display user message
    logging.info("The builded lpp_source will be: {}.".format(lpp_source))
    logging.info("The lpp_source location will be: {}.".format(dl_target))
    logging.info("The lpp_source will be available to update machines from {}-00 to {}."
                 .format(filter_ml, rq_name))
    if rq_type == 'Latest':
        logging.info("{} is the Latest SP of TL {}."
                     .format(rq_name, filter_ml))

    PARAMS['Comments'] = '"Updates from {} to {}, built by Ansible'\
                         'Aix Automate infrastructure updates tools"'\
                         .format(filter_ml, rq_name)

    # ========================================================================
    # Make lpp_source_dir='/usr/sys/inst.images/{}-lpp_source'.format(rq_name)
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
    # else dowload what is found and create associated NIM objects
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

        # ====================================================================
        # Create the associated NIM resource if necessary
        # ====================================================================
        if lpp_source not in nim_lpp_sources:

            # ================================================================
            # nim -o define command
            # ================================================================
            ret, stdout = nim_command(module)

            SUMA_CHANGED = True

            logging.info("NIM operation succeeded - output:{}".format(stdout))
            SUMA_OUTPUT.append("NIM operation succeeded - output:{}"
                               .format(stdout))


##############################################################################

if __name__ == '__main__':

    SUMA_CHANGED = False
    SUMA_OUTPUT = []
    SUMA_ERROR = []
    PARAMS = {}

    module = AnsibleModule(
        argument_spec=dict(
            oslevel=dict(required=False, type='str'),
            location=dict(required=False, type='str'),
            targets=dict(required=False, type='str'),
            task_id=dict(required=False, type='str'),
            sched_time=dict(required=False, type='str'),
            action=dict(required=False,
                        choices=['download', 'preview', 'list', 'edit',
                                 'unschedule', 'delete', 'config', 'default'],
                        type='str', default='preview'),
            description=dict(required=False, type='str'),
        ),
        required_if=[
            ['action', 'edit', ['task_id']],
            ['action', 'delete', ['task_id']],
            ['action', 'unschedule', ['task_id']],
            ['action', 'preview', ['location', 'oslevel']],
            ['action', 'download', ['location', 'oslevel']],
        ],
        supports_check_mode=True
    )

    SUMA_CHANGED = False

    # Open log file
    logging.basicConfig(
        filename='/tmp/ansible_suma_debug.log',
        format='[%(asctime)s] %(levelname)s: [%(funcName)s:%(thread)d] %(message)s',
        level=logging.DEBUG)
    logging.debug('*** START ***')

    # ========================================================================
    # Get Module params
    # ========================================================================
    req_oslevel = module.params['oslevel']
    location = module.params['location']
    if location.upper() == 'DEFAULT':
        location = ''
    targets = ''
    if 'targets' in module.params.keys():
        targets = module.params['targets']
        if targets is None:
            targets = ''

    task_id = module.params['task_id']
    sched_time = module.params['sched_time']
    action = module.params['action']

    if module.params['description']:
        description = module.params['description']
    else:
        description = "{} request for oslevel {}".format(action, req_oslevel)

    PARAMS['Description'] = description
    PARAMS['action'] = action
    PARAMS['LppSource'] = ''
    PARAMS['target_clients'] = ()
    PARAMS['targets'] = targets

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
        PARAMS['location'] = location
        PARAMS['targets'] = targets
        suma_down_prev(module)

    # ========================================================================
    # Exit
    # ========================================================================
    module.exit_json(
        changed=SUMA_CHANGED,
        msg="Suma {} completed successfully".format(action),
        suma_output=SUMA_OUTPUT,
        lpp_source_name=PARAMS['LppSource'],
        target_list=" ".join(PARAMS['target_clients']))
