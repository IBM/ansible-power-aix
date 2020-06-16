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
module: nim_updateios
short_description: Update a single or a pair of Virtual I/O Servers
description:
- Performs updates and customization to the Virtual I/O Server (VIOS).
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  targets:
    description:
    - NIM targets.
    type: str
    required: true
  filesets:
    description:
    - Specifies a list of file sets to remove from the target.
    type: str
  installp_bundle:
    description:
    - Specifies an I(installp_bundle) resource that lists file sets to remove on the target.
    type: str
  lpp_source:
    description:
    - Identifies the I(lpp_source) resource that will provide the installation images for
      the operation.
    type: str
  accept_licenses:
    description:
    - Specifies whether the software licenses should be automatically accepted during the installation.
    type: str
  action:
    description:
    - Operation to perform on the targets.
    - C(install).
    - C(commit).
    - C(reject).
    - C(cleanup).
    - C(remove).
    type: str
    choices: [ install, commit, reject, cleanup, remove ]
    required: true
  preview:
    description:
    - Specifies a preview operation.
    type: str
  time_limit:
    description:
    - Before starting the action, the actual date is compared to this parameter value;
      if it is greater then the task is stopped; the format is C(mm/dd/yyyy hh:mm).
    type: str
  vars:
    description:
    - Specifies additional parameters.
    type: dict
  vios_status:
    description:
    - Specifies the result of a previous operation.
    type: dict
  nim_node:
    description:
    - Allows to pass along NIM node info from a task to another so that it
      discovers NIM info only one time for all tasks.
    type: dict
'''

EXAMPLES = r'''
- name: Update a pair of VIOSes
  nim_updateios:
    targets: "(nimvios01, nimvios02)"
    action: install
    lpp_source: /lpp_source
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'NIM updateios operation completed successfully'
targets:
    description: The execution message.
    returned: always
    type: str
    sample: '[nimclient01, nimclient02, ...]'
output:
    description: output of executed commands.
    returned: always
    type: str
status:
    description: The execution message.
    returned: always
    type: dict
    contains:
        <target>:
            description: Status of the execution on the <target>.
            returned: when target is actually a NIM client
            type: str
            sample: 'SUCCESS-UPDT'
    sample: "{ vios01: 'SUCCESS-UPDT', vios02: 'SUCCESS-ALTDC' }"
'''

import os
import re
import subprocess
import threading
import time

# Ansible module 'boilerplate'
# pylint: disable=wildcard-import,unused-wildcard-import,redefined-builtin
from ansible.module_utils.basic import AnsibleModule

DEBUG_DATA = []
OUTPUT = []
NIM_NODE = {}
CHANGED = False


def exec_cmd(cmd, module, exit_on_error=False, debug_data=True, shell=False):
    """
    Execute the given command

    Note: If executed in thread, fail_json does not exit the parent

    args:
        - cmd           array of the command parameters
        - module        the module variable
        - exit_on_error use fail_json if true and cmd return !0
        - debug_data    prints some trace in DEBUG_DATA if set
        - shell         execute cmd through the shell if set (vulnerable to shell
                        injection when cmd is from user inputs). If cmd is a string
                        string, the string specifies the command to execute through
                        the shell. If cmd is a list, the first item specifies the
                        command, and other items are arguments to the shell itself.
    return
        - ret    return code of the command
        - output output and stderr of the command
        - errout command stderr
    """

    global DEBUG_DATA
    global CHANGED
    global OUTPUT

    ret = 0
    output = ''
    errout = ''

    th_id = threading.current_thread().ident
    stderr_file = '/tmp/ansible_updateios_cmd_stderr_{0}'.format(th_id)

    module.debug('command:{0}'.format(cmd))
    if debug_data is True:
        DEBUG_DATA.append('exec_cmd:{0}'.format(cmd))
    try:
        myfile = open(stderr_file, 'w')
        output = subprocess.check_output(cmd, stderr=myfile, shell=shell)
        myfile.close()
        s = re.search(r'rc=([-\d]+)$', output)
        if s:
            ret = int(s.group(1))
            output = re.sub(r'rc=[-\d]+\n$', '', output)  # remove the rc of c_rsh with echo $?

    except subprocess.CalledProcessError as exc:
        myfile.close()
        errout = re.sub(r'rc=[-\d]+\n$', '', exc.output)  # remove the rc of c_rsh with echo $?
        ret = exc.returncode

    except (OSError, IOError) as exc:
        myfile.close()
        if exc.args:
            match = re.match(r'rc=[-\d]+\n$', exc.args[1])
            if match:
                errout = re.sub(r'rc=[-\d]+\n$', '', exc.args[1])  # remove the rc of c_rsh with echo $?
                ret = exc.args[0]
            else:
                msg = 'Command: {0} Exception: {1}'.format(cmd, exc)
                ret = 1
                module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT)
        else:
            msg = 'Command: {0} Exception: {1}'.format(cmd, exc)
            ret = 1
            module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT)

    # check for error message
    if os.path.getsize(stderr_file) > 0:
        myfile = open(stderr_file, 'r')
        errout += ''.join(myfile)
        myfile.close()
    os.remove(stderr_file)

    if debug_data is True:
        DEBUG_DATA.append('exec_cmd rc:{0}, output:{1} errout:{2}'.format(ret, output, errout))
        module.debug('retrun rc:{0}, output:{1} errout:{2}'.format(ret, output, errout))

    if ret != 0 and exit_on_error is True:
        msg = 'Command: {0} RetCode:{1} ... stdout:{2} stderr:{3}'.format(cmd, ret, output, errout)
        module.fail_json(changed=CHANGED, msg=msg, output=OUTPUT)

    return (ret, output, errout)


def get_nim_clients_info(module, lpar_type):
    """
    Get the list of the lpar (standalones or vios) defined on the nim master, and get their
    cstate.

    return the list of the name of the lpar objects defined on the
           nim master and their associated cstate value
    """
    global CHANGED
    global OUTPUT
    std_out = ''
    info_hash = {}

    cmd = 'LC_ALL=C lsnim -t {0} -l'.format(lpar_type)
    (ret, std_out, std_err) = exec_cmd(cmd, module, shell=True)
    if ret != 0:
        msg = 'Cannot list NIM {0} objects: {1}'.format(lpar_type, std_err)
        module.log(msg)
        module.fail_json(changed=CHANGED, msg=msg, meta=OUTPUT)

    # lpar name and associated Cstate
    obj_key = ""
    for line in std_out.split('\n'):
        line = line.rstrip()
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
            info_hash[obj_key] = {}
            continue

        match_cstate = re.match(r"^\s+Cstate\s+=\s+(.*)$", line)
        if match_cstate:
            cstate = match_cstate.group(1)
            info_hash[obj_key]['cstate'] = cstate
            continue

        # For VIOS store the management profile
        if lpar_type == 'vios':
            # Not used in this module so far
            # match_mgmtprof = re.match(r"^\s+mgmt_profile1\s+=\s+(.*)$", line)
            # if match_mgmtprof:
            #     mgmt_elts = match_mgmtprof.group(1).split()
            #     if len(mgmt_elts) >= 3:
            #         info_hash[obj_key]['mgmt_hmc_id'] = mgmt_elts[0]
            #         info_hash[obj_key]['mgmt_vios_id'] = mgmt_elts[1]
            #         info_hash[obj_key]['mgmt_cec_serial'] = mgmt_elts[2]
            #     else:
            #         module.log('WARNING: VIOS {0} management profile has not 3 elements: {1}'.
            #                    format(obj_key, match_mgmtprof.group(1)))
            #     continue

            # Get VIOS interface info in case we need c_rsh
            match_if = re.match(r"^\s+if1\s+=\s+\S+\s+(\S+)\s+.*$", line)
            if match_if:
                info_hash[obj_key]['vios_ip'] = match_if.group(1)
                continue

    return info_hash


def build_nim_node(module):
    """
    build the nim node containing the nim vios and hmcinfo.

    arguments:
        None

    return:
        None
    """

    global NIM_NODE

    # =========================================================================
    # Build vios info list
    # =========================================================================
    nim_vios = {}
    nim_vios = get_nim_clients_info(module, 'vios')

    NIM_NODE['nim_vios'] = nim_vios
    module.debug('NIM VIOS: {0}'.format(nim_vios))


def check_lpp_source(module, lpp_source):
    """
    Check to make sure lpp_source exists
        - module        the module variable
        - lpp_source    lpp_source param provided by module
    In case lpp_source does not exist fail the module
    return
        - exists        True
    """
    global OUTPUT
    global CHANGED

    # find location of lpp_source
    cmd = ['lsnim', '-a', 'location', lpp_source]
    (ret, std_out, std_err) = exec_cmd(cmd, module)
    if ret != 0:
        msg = 'Cannot find location of lpp_source {0}, lsnim returns: {1}'.format(lpp_source, std_err)
        module.log(msg)
        OUTPUT.append(msg)
        module.fail_json(changed=CHANGED, msg=msg, meta=OUTPUT)
    location = std_out.split()[3]

    # check to make sure path exists
    cmd = ['/bin/find', location]
    (ret, std_out, std_err) = exec_cmd(cmd, module)
    if ret != 0:
        msg = 'Cannot find location of lpp_source {0}: {1}'.format(lpp_source, std_err)
        module.log(msg)
        OUTPUT.append(msg)
        module.fail_json(changed=CHANGED, msg=msg, meta=OUTPUT)

    return True


def check_vios_targets(module, targets):
    """
    check the list of the vios targets.

    a target name could be of the following form:
        (vios1, vios2) (vios3)

    arguments:
        module (hash): the Ansible module
        targets (str): list of tuple of NIM name of vios machine

    return: the list of the existing vios tuple matching the target list
    """
    global NIM_NODE

    vios_list = {}
    vios_list_tuples_res = []
    vios_list_tuples = targets.replace(" ", "").replace("),(", ")(").split('(')

    # ===========================================
    # Build targets list
    # ===========================================
    for vios_tuple in vios_list_tuples[1:]:
        module.log('Checking vios_tuple: {0}'.format(vios_tuple))

        tuple_elts = list(vios_tuple[:-1].split(','))
        tuple_len = len(tuple_elts)

        if tuple_len != 1 and tuple_len != 2:
            OUTPUT.append('Malformed VIOS targets {0}. Tuple {1} should be a 1 or 2 elements.'
                          .format(targets, tuple_elts))
            module.log('Malformed VIOS targets {0}. Tuple {1} should be a 1 or 2 elements.'
                       .format(targets, tuple_elts))
            return None

        # check vios not already exists in the target list
        if tuple_elts[0] in vios_list or (tuple_len == 2 and (tuple_elts[1] in vios_list
                                                              or tuple_elts[0] == tuple_elts[1])):
            OUTPUT.append('Malformed VIOS targets {0}. Duplicated VIOS'.format(targets))
            module.log('Malformed VIOS targets {0}. Duplicated VIOS'.format(targets))
            return None

        # check vios is knowed by the NIM master - if not ignore it
        if tuple_elts[0] not in NIM_NODE['nim_vios']:
            msg = "VIOS {0} is not client of the NIM master, will be ignored".format(tuple_elts[0])
            OUTPUT.append(msg)
            module.log(msg)
            continue
        if tuple_len == 2 and tuple_elts[1] not in NIM_NODE['nim_vios']:
            msg = "VIOS {0} is not client of the NIM master, will be ignored".format(tuple_elts[1])
            OUTPUT.append(msg)
            module.log(msg)
            continue

        # check vios connectivity
        res = 0
        for elem in tuple_elts:
            cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', elem,
                   '"/usr/bin/ls /dev/null; echo rc=$?"']
            (ret, std_out, std_err) = exec_cmd(cmd, module)
            if ret != 0:
                res = 1
                msg = 'skipping {0}: cannot reach {1} with c_rsh: {2}, {3}, {4}'\
                      .format(vios_tuple, elem, res, std_out, std_err)
                module.log(msg)
                continue
        if res != 0:
            continue

        if tuple_len == 2:
            vios_list[tuple_elts[0]] = tuple_elts[1]
            vios_list[tuple_elts[1]] = tuple_elts[0]
            # vios_list = vios_list.extend([tuple_elts[0], tuple_elts[1]])
            my_tuple = (tuple_elts[0], tuple_elts[1])
            vios_list_tuples_res.append(tuple(my_tuple))
        else:
            vios_list[tuple_elts[0]] = tuple_elts[0]
            # vios_list.append(tuple_elts[0])
            my_tuple = (tuple_elts[0],)
            vios_list_tuples_res.append(tuple(my_tuple))

    return vios_list_tuples_res


def get_vios_ssp_status(module, target_tuple, vios_key, update_op_tab):
    """
    Check the SSP status of the VIOS tuple
    Update IOS can only be performed when both VIOSes in the tuple
         refer to the same cluster and have the same SSP status
    return
        0 if OK
        1 else
    """

    global NIM_NODE

    ssp_name = ''
    vios_name = ''
    vios_ssp_status = ''
    err_label = 'FAILURE-SSP'
    cluster_found = False
    tuple_len = len(target_tuple)

    for vios in target_tuple:
        NIM_NODE['nim_vios'][vios]['ssp_status'] = 'none'

    # get the SSP status
    for vios in target_tuple:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
               NIM_NODE['nim_vios'][vios]['vios_ip'],
               '"LC_ALL=C /usr/ios/cli/ioscli cluster -list &&'
               ' /usr/ios/cli/ioscli cluster -status -fmt : ; echo rc=$?"']

        (ret, std_out, std_err) = exec_cmd(cmd, module)
        if ret != 0:
            std_out = std_out.rstrip()
            if std_out.find('Cluster does not exist') != -1:
                module.debug('There is no cluster or the node {0} is DOWN'.format(vios))
                NIM_NODE['nim_vios'][vios]['vios_ssp_status'] = 'DOWN'
                if tuple_len == 1:
                    return 0
                else:
                    continue
            else:
                update_op_tab[vios_key] = err_label
                OUTPUT.append('    Failed to get the SSP status for {0}: {1} {2}'
                              .format(vios, std_out, std_err))
                module.log('Failed to get the SSP status for {0}: {1} {2} {3}'
                           .format(vios, ret, std_out, std_err))
                return 1
        cluster_found = True

        # check that the VIOSes belong to the same cluster and have the same satus
        #                  or there is no SSP
        # stdout is like:
        # gdr_ssp3:OK:castor_gdr_vios3:8284-22A0221FD4BV:17:OK:OK
        # gdr_ssp3:OK:castor_gdr_vios2:8284-22A0221FD4BV:16:OK:OK
        #  or
        # Cluster does not exist.
        #
        for line in std_out.split('\n'):
            line = line.rstrip()
            match_key = re.match(r"^(\S+):(\S+):(\S+):\S+:\S+:(\S+):.*", line)
            if not match_key:
                module.debug('cluster line: "{0}" does not match'.format(line))
                continue

            if match_key.group(3) not in target_tuple:
                continue

            cur_ssp_name = match_key.group(1)
            # cur_ssp_satus = match_key.group(2)
            cur_vios_name = match_key.group(3)
            cur_vios_ssp_status = match_key.group(4)

            NIM_NODE['nim_vios'][cur_vios_name]['vios_ssp_status'] = cur_vios_ssp_status
            NIM_NODE['nim_vios'][cur_vios_name]['ssp_name'] = cur_ssp_name
            # single VIOS case
            if tuple_len == 1:
                if cur_vios_ssp_status == 'OK':
                    err_msg = 'SSP is active for the single VIOS: {0}. VIOS cannot be updated'\
                              .format(cur_vios_name)
                    OUTPUT.append('    ' + err_msg)
                    module.log(err_msg)
                    update_op_tab[vios_key] = err_label
                    return 1
                return 0

            # first VIOS in the pair
            if ssp_name == '':
                ssp_name = cur_ssp_name
                vios_name = cur_vios_name
                vios_ssp_status = cur_vios_ssp_status
                continue

            # both VIOSes found
            if vios_ssp_status != cur_vios_ssp_status:
                err_msg = '{0} cannot be updated: SSP status differ: {1}:{2}, {3}:{4}'\
                          .format(vios_key, vios_name, vios_ssp_status,
                                  cur_vios_name, cur_vios_ssp_status)
                OUTPUT.append('    ' + err_msg)
                module.log(err_msg)
                update_op_tab[vios_key] = err_label
                return 1
            elif ssp_name != cur_ssp_name and cur_vios_ssp_status == 'OK':
                err_msg = '{0} cannot be updated: both VIOSes must belong to the same SSP'\
                          .format(vios_key)
                OUTPUT.append('    ' + err_msg)
                module.log(err_msg)
                update_op_tab[vios_key] = err_label
                return 1
            return 0

    if cluster_found is True:
        err_msg = '{0} cannot be updated: only one VIOS belongs to an SSP'.format(vios_key)
        OUTPUT.append('    ' + err_msg)
        module.log(err_msg)
        update_op_tab[vios_key] = err_label
        return 1
    return 0


def ssp_stop_start(module, target_tuple, vios, action):
    """
    stop/start the SSP for a VIOS
    return
        0 if OK
        1 else
    """

    global NIM_NODE
    global OUTPUT

    module.debug("ssp_start_stop {0},{1},{2}".format(target_tuple, vios, action))
    # if action is start SSP,  find the first node running SSP
    node = vios
    if action == "start":
        module.debug("search the vios runing ssp")
        for cur_node in target_tuple:
            module.debug("vios:{0} ssp status is {1}".
                         format(cur_node, NIM_NODE['nim_vios'][cur_node]['vios_ssp_status']))

            if NIM_NODE['nim_vios'][cur_node]['vios_ssp_status'] == "OK":
                node = cur_node
                break

    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
           NIM_NODE['nim_vios'][node]['vios_ip'],
           '"/usr/sbin/clctrl -{0} -n {1} -m {2}; echo rc=$?"'
           .format(action, NIM_NODE['nim_vios'][vios]['ssp_name'], vios)]

    (ret, std_out, std_err) = exec_cmd(cmd, module)
    if ret != 0:
        msg = 'Failed to {0} SSP cluster {1} on {2}: {3}'\
              .format(action, NIM_NODE['nim_vios'][vios]['ssp_name'], vios, std_err)
        OUTPUT.append('    ' + msg)
        module.log(msg)
        return 1

    if action == "stop":
        NIM_NODE['nim_vios'][vios]['vios_ssp_status'] = 'DOWN'
    else:
        NIM_NODE['nim_vios'][vios]['vios_ssp_status'] = 'OK'

    msg = '{0} SSP cluster {1} on {2} succeeded'\
          .format(action, NIM_NODE['nim_vios'][vios]['ssp_name'], vios)
    OUTPUT.append('    ' + msg)
    module.log(msg)
    return 0


def get_updateios_cmd(module):
    """
    Assemble the updateios command
        - module        the module variable
    return
        - cmd           array of the command parameters
    """
    global OUTPUT
    global CHANGED

    cmd = ['nim', '-o', 'updateios']

    # lpp source
    if module.params['lpp_source']:
        if check_lpp_source(module, module.params['lpp_source']):
            cmd += ['-a', 'lpp_source=%s' % (module.params['lpp_source'])]

    # accept licenses
    if module.params['accept_licenses']:
        cmd += ['-a', 'accept_licenses=%s' % (module.params['accept_licenses'])]
    else:  # default
        cmd += ['-a', 'accept_licenses=yes']

    # updateios flags
    cmd += ['-a', 'updateios_flags=-%s' % (module.params['action'])]

    if module.params['action'] == "remove":
        if module.params['filesets']:
            cmd += ['-a', 'filesets=%s' % (module.params['filesets'])]
        elif module.params['installp_bundle']:
            cmd += ['-a', 'installp_bundle=%s' % (module.params['installp_bundle'])]
        else:
            msg = '"filesets" parameter or "installp_bundle" parameter'\
                  ' is mandatory with the "remove" action'
            module.log('{0}'.format(msg))
            OUTPUT.append('{0}'.format(msg))
            module.fail_json(changed=CHANGED, msg=msg, meta=OUTPUT)
    else:
        if module.params['filesets'] or module.params['installp_bundle']:
            module.log('Discarding attribute filesets {0} and installp_bundle {1}'
                       .format(module.params['filesets'], module.params['installp_bundle']))
            OUTPUT.append('Discarding installp_bundle or filesets')

    # preview mode
    if module.params['preview']:
        cmd += ['-a', 'preview=%s' % (module.params['preview'])]
    else:  # default
        cmd += ['-a', 'preview=yes']

    return cmd


def nim_updateios(module, targets_list, vios_status, update_op_tab, time_limit):
    """
    Execute the updateios command
        - module        the Ansible module
    return
        - ret           return code of nim updateios command
    """
    global CHANGED
    global OUTPUT
    global NIM_NODE

    # build the updateios command from the playbook parameters
    updateios_cmd = get_updateios_cmd(module)

    vios_key = []
    for target_tuple in targets_list:
        OUTPUT.append('Processing tuple: {0}'.format(target_tuple))
        module.debug('Processing target_tuple: {0}'.format(target_tuple))

        tup_len = len(target_tuple)
        vios1 = target_tuple[0]
        if tup_len == 2:
            vios2 = target_tuple[1]
            vios_key = "{0}-{1}".format(vios1, vios2)
        else:
            vios_key = vios1

        module.debug('vios_key: {0}'.format(vios_key))

        # if health check status is known, check the vios tuple has passed
        # the health check successfuly
        if vios_status is not None:
            if vios_key not in vios_status:
                update_op_tab[vios_key] = "FAILURE-NO-PREV-STATUS"
                OUTPUT.append("    {0} vioses skipped (no previous status found)"
                              .format(vios_key))
                module.log("[WARNING] {0} vioses skipped (no previous status found)"
                           .format(vios_key))
                continue

            if vios_status[vios_key] != 'SUCCESS-ALTDC':
                update_op_tab[vios_key] = vios_status[vios_key]
                OUTPUT.append("    {0} vioses skipped (vios_status: {1})"
                              .format(vios_key, vios_status[vios_key]))
                module.log("[WARNING] {0} vioses skipped (vios_status: {1})"
                           .format(vios_key, vios_status[vios_key]))
                continue

        # check if there is time to handle this tuple
        if not (time_limit is None) and time.localtime(time.time()) >= time_limit:
            time_limit_str = time.strftime("%m/%d/%Y %H:%M", time_limit)
            OUTPUT.append("    Time limit {0} reached, no further operation"
                          .format(time_limit_str))
            module.log('Time limit {0} reached, no further operation'
                       .format(time_limit_str))
            return 0

        # check if SSP is defined for this VIOSes tuple.
        ret = get_vios_ssp_status(module, target_tuple, vios_key, update_op_tab)
        if ret == 1:
            OUTPUT.append("    {0} vioses skipped (bad SSP status)".format(vios_key))
            module.log('[WARNING] Update operation for {0} vioses skipped due to bad SSP status'
                       .format(vios_key))
            module.log('Update operation can only be done when both of the VIOSes have'
                       ' the same SSP status (or for a single VIOS, when the SSP status'
                       ' is inactive) and belong to the same SSP')
            continue

        # TBC - Begin: Uncomment for testing without effective update operation
        # OUTPUT.append('Warning: testing without effective update operation')
        # OUTPUT.append('NIM Command: {0} '.format(updateios_cmd))
        # ret = 0
        # std_out = 'NIM Command: {0} '.format(updateios_cmd)
        # update_op_tab[vios_key] = "SUCCESS-UPDT"
        # continue
        # TBC - End

        update_op_tab[vios_key] = "SUCCESS-UPDT"

        for vios in target_tuple:
            # Commit applied lpps if necessay
            if module.params['preview'] and module.params['preview'] == 'no':
                OUTPUT.append('    Commit all applied lpps before the update on {0}'
                              .format(vios))
                module.log('Commit all applied lpps before the update on {0}'
                           .format(vios))

                cmd_commit = 'LC_ALL=C /usr/sbin/nim -o updateios '\
                             '-a updateios_flags=-commit -a filesets=all {0} 2>&1'\
                             .format(vios)
                module.debug('NIM - Command:{0}'.format(cmd_commit))

                (ret, std_out, std_err) = exec_cmd(cmd_commit, module, shell=True)

                if ret != 0:
                    if std_err.find('There are no uncommitted updates') == -1:
                        msg = 'Failed to commit lpps on {0}'.format(vios)
                        module.log('[WARNING] {0}, {1} returned {2} {3}'.format(msg, cmd_commit, ret, std_err))
                        OUTPUT.append('    ' + msg)
                    else:
                        OUTPUT.append('    Nothing to commit on {0}'.format(vios))
                else:
                    module.debug('All applied updates are now committed: {0}'
                                 .format(std_out))
                    OUTPUT.append('    All applied updates are now committed')
                    CHANGED = True

                OUTPUT.append('    Updating VIOS: {0}'.format(vios))

            # set the error label to be used in sub routines
            err_label = "FAILURE-UPDT1"
            if vios != vios1:
                err_label = "FAILURE-UPDT2"

            # if needed stop the SSP for the VIOS
            restart_needed = False
            if NIM_NODE['nim_vios'][vios]['vios_ssp_status'] == 'OK':
                ret = ssp_stop_start(module, target_tuple, vios, 'stop')
                if ret == 1:
                    module.log('SSP stop operation failure for VIOS {0}'
                               .format(vios))
                    update_op_tab[vios_key] = err_label
                    module.log('VIOS update status for {0}: {1}'
                               .format(vios_key, update_op_tab[vios_key]))
                    break  # cannot continue
                restart_needed = True
                module.log(' {0}: {1}'.format(vios_key, update_op_tab[vios_key]))

            skip_next_target = False

            cmd = updateios_cmd + [vios]
            (ret, std_out, std_err) = exec_cmd(cmd, module)

            if ret != 0:
                module.log('NIM Command: {0} failed rc:{1} stdout:{2} stderr:{3}'
                           .format(cmd, ret, std_out, std_err))
                OUTPUT.append('    Failed to update VIOS {0} with NIM: {1} failed: {2}'
                              .format(vios, cmd, std_err))
                update_op_tab[vios_key] = err_label
                # in case of failure try to restart the SSP if needed
                skip_next_target = True
            else:
                module.log('VIOS {0} successfully updated'.format(vios))
                OUTPUT.append("    VIOS {0} successfully updated".format(vios))
                CHANGED = True

            # if needed restart the SSP for the VIOS
            if restart_needed:
                ret = ssp_stop_start(module, target_tuple, vios, 'start')
                if ret == 1:
                    module.log('SSP start operation failure for VIOS {0}'
                               .format(vios))
                    update_op_tab[vios_key] = err_label
                    module.log('VIOS update status for {0}: {1}'
                               .format(vios_key, update_op_tab[vios_key]))
                    break  # cannot continue

                module.log(' {0}: {1}'.format(vios_key, update_op_tab[vios_key]))

            if skip_next_target:
                break

    return 0


###################################################################################

def main():
    global CHANGED
    global NIM_NODE
    global OUTPUT
    global DEBUG_DATA

    MODULE = AnsibleModule(
        argument_spec=dict(
            targets=dict(required=True, type='str'),
            filesets=dict(required=False, type='str'),
            installp_bundle=dict(required=False, type='str'),
            lpp_source=dict(required=False, type='str'),
            accept_licenses=dict(required=False, type='str'),
            action=dict(choices=['install', 'commit', 'reject', 'cleanup', 'remove'],
                        required=True, type='str'),
            preview=dict(required=False, type='str'),
            time_limit=dict(required=False, type='str'),
            vars=dict(required=False, type='dict'),
            vios_status=dict(required=False, type='dict'),
            nim_node=dict(required=False, type='dict')
        ),
        required_if=[
            ['action', 'install', ['lpp_source']],
        ],
        mutually_exclusive=[
            ['filesets', 'installp_bundle'],
        ],
    )

    # =========================================================================
    # Get Module params
    # =========================================================================
    targets_update_status = {}
    vios_status = {}
    targets = MODULE.params['targets']

    if MODULE.params['vios_status']:
        vios_status = MODULE.params['vios_status']
    else:
        vios_status = None

    # build a time structure for time_limit attribute,
    time_limit = None
    if MODULE.params['time_limit']:
        match_key = re.match(r"^\s*\d{2}/\d{2}/\d{4} \S*\d{2}:\d{2}\s*$",
                             MODULE.params['time_limit'])
        if match_key:
            time_limit = time.strptime(MODULE.params['time_limit'], '%m/%d/%Y %H:%M')
        else:
            msg = 'Malformed time limit "{0}", please use mm/dd/yyyy hh:mm format.'\
                  .format(MODULE.params['time_limit'])
            MODULE.fail_json(msg=msg)

    MODULE.debug('*** START NIM UPDATE VIOS OPERATION ***')

    OUTPUT.append('Updateios operation for {0}'.format(MODULE.params['targets']))
    MODULE.log('Action {0} for {1} targets'.format(MODULE.params['action'], targets))

    # =========================================================================
    # build nim node info
    # =========================================================================
    if MODULE.params['nim_node']:
        NIM_NODE = MODULE.params['nim_node']
    else:
        build_nim_node(MODULE)

    # =========================================================================
    # Perfom checks
    # =========================================================================
    ret = check_vios_targets(MODULE, targets)
    if (not ret) or (ret is None):
        OUTPUT.append('Empty target list')
        MODULE.warn('Warning: Empty target list: "{0}"'.format(targets))
    else:
        targets_list = ret
        OUTPUT.append('Targets list:{0}'.format(targets_list))
        MODULE.debug('Target list: {0}'.format(targets_list))

        # =========================================================================
        # Perfom the update
        # =========================================================================
        ret = nim_updateios(MODULE, targets_list, vios_status,
                            targets_update_status, time_limit)

        if targets_update_status:
            OUTPUT.append('NIM updateios operation status:')
            MODULE.log('NIM updateios operation status:')
            for vios_key in targets_update_status:
                OUTPUT.append("    {0} : {1}".format(vios_key, targets_update_status[vios_key]))
                MODULE.log('    {0} : {1}'.format(vios_key, targets_update_status[vios_key]))
            MODULE.log('NIM updateios operation result: {0}'.format(targets_update_status))
        else:
            MODULE.log('NIM updateios operation: status table is empty')
            OUTPUT.append('NIM updateios operation: Error getting the status')
            targets_update_status = vios_status

    # =========================================================================
    # Exit
    # =========================================================================
    MODULE.exit_json(
        changed=CHANGED,
        msg="NIM updateios operation completed successfully",
        targets=MODULE.params['targets'],
        debug_output=DEBUG_DATA,
        output=OUTPUT,
        status=targets_update_status)


if __name__ == '__main__':
    main()
