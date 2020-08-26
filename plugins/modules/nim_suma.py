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
module: nim_suma
short_description: Download fixes, SP or TL on an AIX server
description:
- Creates a task to automate the download of technology level (TL) and
  service pack (SP) from a fix server using the Service Update Management
  Assistant (SUMA). It can create the NIM resource.
- Log file is /var/adm/ansible/nim_suma_debug.log.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Controls what is performed.
    - C(download) to download fixes and define the NIM resource.
    - C(preview)  to execute all the checks without downloading the fixes.
    type: str
    choices: [ download, preview ]
    default: preview
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - C(foo*) designates all the NIM clients with name starting by C(foo).
    - C(foo[2:4]) designates the NIM clients among foo2, foo3 and foo4.
    - C(*) or C(all) designates all the NIM clients.
    type: list
    elements: str
    required: true
  oslevel:
    description:
    - Specifies the Operating System level to update to;
    - C(Latest) indicates the latest SP suma can update the targets to.
    - C(xxxx-xx(-00-0000)) sepcifies a TL.
    - C(xxxx-xx-xx-xxxx) or C(xxxx-xx-xx) specifies a SP.
    - Required when I(action=download) or I(action=preview).
    type: str
    default: Latest
  lpp_source_name:
    description:
    - Name of the lpp_source NIM resource.
    - Required when I(action=download) or I(action=preview).
    type: str
  download_dir:
    description:
    - Absolute directory path where to download the packages on the NIM server.
    - If not set it looks for existing NIM ressource matching I(lpp_source_name) and use its location.
    - If no NIM ressource is found, the path is set to /usr/sys/inst.images
    - Can be used if I(action=download) or I(action=preview).
    type: path
  download_only:
    description:
    - Download only. Do not create the NIM resource.
    - Can be used if I(action=download)
    type: bool
    default: no
  extend_fs:
    description:
    - Specifies to automatically extends the filesystem if needed. If no is specified and additional space is required for the download, no download occurs.
    - Can be used if I(action=download) or I(action=preview).
    type: bool
    default: yes
  description:
    description:
    - Display name for SUMA task.
    - If not set the will be labelled 'I(action) request for oslevel I(oslevel)'
    - Can be used for I(action=download) or I(action=preview).
    type: str
  metadata_dir:
    description:
    - Directory where metadata files are downloaded.
    - Can be used if I(action=download) or I(action=preview) when I(oslevel) is not exact, for example I(oslevel=Latest).
    type: path
    default: /var/adm/ansible/metadata
'''

EXAMPLES = r'''
- name: Check for, and install, system updates
  nim_suma:
    action: download
    targets: nimclient01
    oslevel: latest
    download_dir: /usr/sys/inst.images
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
    sample: 'Suma preview completed successfully'
lpp_source_name:
    description: Name of the NIM Lpp Source resource used.
    returned: always
    type: str
    sample: 'quimby01_lpp_source'
target_list:
    description: Status information.
    returned: always
    type: list
    elements: str
    sample: [nimclient01, nimclient02, ...]
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
            sample: "Unavailable client: nimclient02"
    sample:
        "meta": {
            "messages": [
                "Unavailable client: nimclient02",
                "The latest SP of 7200-02 is: 7200-02-01-1732",
                ...,
            ]
        }
'''

import os
import re
import glob
import shutil
import threading

from ansible.module_utils.basic import AnsibleModule

results = None


def min_oslevel(dic):
    """
    Find the minimun value of a dictionary.

    arguments:
        dict - Dictionary {machine: oslevel}
    return:
        minimun oslevel from the dictionary
    """
    oslevel_min = None

    for key, value in iter(dic.items()):
        if oslevel_min is None or value < oslevel_min:
            oslevel_min = value

    return oslevel_min


def max_oslevel(dic):
    """
    Find the maximum value of a the oslevel dictionary.

    arguments:
        dic - Dictionary {client: oslevel}
    return:
        maximum oslevel from the dictionary
    """
    oslevel_max = None

    for key, value in iter(dic.items()):
        if oslevel_max is None or value > oslevel_max:
            oslevel_max = value

    return oslevel_max


def run_oslevel_cmd(module, machine, oslevels):
    """
    Run the oslevel command on target machine.

    Stores the output in the dedicated slot of the oslevels dictionary.

    arguments:
        module      (dict): The Ansible module
        machine      (str): The name machine
        oslevels    (dict): The results of the command
    """
    oslevels[machine] = 'timedout'

    if machine == 'master':
        cmd = ['/usr/bin/oslevel', '-s']
    else:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh',
               machine,
               '"/usr/bin/oslevel -s; echo rc=$?"']

    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        module.debug('{0} oslevel stdout: "{1}"'.format(machine, stdout))
        if stderr.rstrip():
            module.log('[WARNING] "{0}" command stderr: {1}'.format(' '.join(cmd), stderr))

        # remove the rc of c_rsh with echo $?
        if machine != 'master':
            stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

        # return stdout only ... stripped!
        oslevels[machine] = stdout.rstrip()
    else:
        msg = 'Command: \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.log('Failed to get oslevel for {0}: {1}'.format(machine, msg))


def expand_targets(module, targets, nim_clients):
    """
    Expand the list of target patterns.

    A target pattern can be of the following form:
        target*       all the NIM client machines whose names start
                          with 'target'
        target[n1:n2] where n1 and n2 are numeric: target<n1> to target<n2>
        * or ALL      all the NIM client machines
        client_name   the NIM client named 'client_name'
        master        the NIM master

        example:  target[1:5] target12 other_target*

    arguments:
        module      (dict): The Ansible module
        targets     (list): The list of target patterns
        nim_clients (list): The list of existing NIM clients

    return: clients: the list of the existing machines matching the target list
    """
    clients = []
    if len(targets) == 0:
        return clients

    for target in targets:

        # Build target(s) from: range i.e. quimby[7:12]
        rmatch = re.match(r"(\w+)\[(\d+):(\d+)\]", target)
        if rmatch:
            name = rmatch.group(1)
            start = rmatch.group(2)
            end = rmatch.group(3)

            for i in range(int(start), int(end) + 1):
                curr_name = name + str(i)
                if curr_name in nim_clients:
                    clients.append(curr_name)
            continue

        # Build target(s) from: val*. i.e. quimby*
        rmatch = re.match(r"(\w+)\*$", target)
        if rmatch:
            name = rmatch.group(1)

            for curr_name in nim_clients:
                if re.match(r"^%s\.*" % name, curr_name):
                    clients.append(curr_name)
            continue

        # Build target(s) from: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = nim_clients
            continue

        # Build target(s) from full name: quimby05
        if (target in nim_clients) or (target == 'master'):
            clients.append(target)

    return list(set(clients))


def get_nim_clients(module):
    """
    Get the list of the standalones defined on the NIM master.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return the list of the name of the standlone objects defined on the
           NIM master.
    """
    global results

    clients_list = []

    cmd = ['lsnim', '-t', 'standalone']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), rc)
        module.fail_json(**results)

    for line in stdout.rstrip().splitlines():
        clients_list.append(line.strip().split()[0])

    return clients_list


def get_oslevels(module, targets):
    """
    Get the oslevel of the specified targets.

    arguments:
        module  (dict): The Ansible module
    return a dictionary of the oslevels
    """

    # Launch threads to collect information on targets
    threads = []
    oslevels = {}

    for machine in targets:
        process = threading.Thread(target=run_oslevel_cmd,
                                   args=(module, machine, oslevels))
        process.start()
        threads.append(process)

    for process in threads:
        process.join(300)  # wait 5 min for c_rsh to timeout
        if process.is_alive():
            module.log('[WARNING] {0} Not responding'.format(process))

    return oslevels


def get_nim_lpp_source(module):
    """
    Get the list of the lpp_source defined on the NIM master.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        lpp_source_list: dictionary key, value
                key = lpp source name
                value = lpp source location
    """
    global results

    lpp_source_list = {}

    cmd = ['lsnim', '-t', 'lpp_source', '-l']

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Cannot get the list of lpp source, command '{0}' failed with return code {1}".format(cmd, rc)
        module.log(msg)
        results['msg'] = msg
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)

    for line in stdout.rstrip().split('\n'):
        match_key = re.match(r"^(\S+):", line)
        if match_key:
            obj_key = match_key.group(1)
        else:
            match_loc = re.match(r"^\s+location\s+=\s+(\S+)$", line)
            if match_loc:
                loc = match_loc.group(1)
                lpp_source_list[obj_key] = loc

    return lpp_source_list


def compute_rq_type(module, oslevel, targets_list):
    """Compute rq_type.

    arguments:
        module          (dict): The Ansible module
        oslevel          (str): requested oslevel
        targets_list    (list): list of target NIM clients
    return:
        Latest when oslevel is blank or latest (not case sensitive)
        Latest when oslevel is a TL (6 digits) and target list is empty
        TL     when oslevel is xxxx-xx(-00-0000)
        SP     when oslevel is xxxx-xx-xx(-xxxx)
        ERROR  when oslevel is not recognized
    """
    if oslevel is None or not oslevel.strip() or oslevel == 'Latest':
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})$", oslevel) and not targets_list:
        return 'Latest'
    if re.match(r"^([0-9]{4}-[0-9]{2})(|-00|-00-0000)$", oslevel):
        return 'TL'
    if re.match(r"^([0-9]{4}-[0-9]{2}-[0-9]{2})(|-[0-9]{4})$", oslevel):
        return 'SP'

    return 'ERROR'


def find_sp_version(module, file):
    """
    Open and parse the provided file to find higher SP version
    arguments:
        module  (dict): The Ansible module
        file     (str): path of the file to parse
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


def compute_rq_name(module, suma_params, rq_type, oslevel, clients_target_oslevel):
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
        module                  (dict): The Ansible module
        suma_params             (dict): parameters to build the suma command
        rq_type                  (str): type of request, can be Latest, SP or TL
        oslevel                  (str): requested oslevel
        clients_target_oslevel  (dict): oslevel of each selected client
    note:
        Exits with fail_json in case of error
    return:
       rq_name value
    """
    global results

    rq_name = ''
    if rq_type == 'Latest':
        if not clients_target_oslevel:
            if oslevel == 'Latest':
                msg = "Cannot get oslevel from targets, check you can get the oslevel on targets"
                module.log(msg)
                results['msg'] = msg
                module.fail_json(**results)
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
            if re.match(r"^([0-9]{4})", tl_min).group(1) != re.match(r"^([0-9]{4})", tl_max).group(1):
                module.log("[WARNING] release level mismatch, only AIX {0} SP/TL will be downloaded\n\n".format(tl_max[:2]))

            # tl_max is used to get metadata then to get latest SP
            metadata_filter_ml = tl_max

        if not metadata_filter_ml:
            msg = "Cannot build minimum level filter based on the OS level of targets"
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

        # find latest SP build number for the highest TL
        sp_version = None
        file_name = suma_params['metadata_dir'] + "/installp/ppc/" + metadata_filter_ml + "*.xml"
        module.debug("searched files: {0}".format(file_name))
        files = glob.glob(file_name)
        module.debug("searching SP in files: {0}".format(files))
        for cur_file in files:
            version = find_sp_version(module, cur_file)
            if sp_version is None or version > sp_version:
                sp_version = version

        rq_name = sp_version
        shutil.rmtree(suma_params['metadata_dir'])

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

            # find SP build number
            sp_version = None
            cur_file = suma_params['metadata_dir'] + "/installp/ppc/" + oslevel + ".xml"
            sp_version = find_sp_version(module, cur_file)

            rq_name = sp_version
            shutil.rmtree(suma_params['metadata_dir'])

    if not rq_name or not rq_name.strip():  # should never happen
        msg = "OS level {0} does not match any fixes".format(oslevel)
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)

    return rq_name


def compute_filter_ml(module, clients_target_oslevel, rq_name):
    """
    Compute the suma filter ML.
    returns the TL part of rq_name if there is no target machine.
    returns the lowest Technical Level from the target client list
        (clients_oslevel) that is at the same release as the
        requested target os_level (rq_name).

    arguments:
        module                 (dict): The Ansible module
        clients_target_oslevel (list): oslevel of each selected client
        rq_name                 (str): SUMA request name based on metadata info
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


def compute_lpp_source_name(module, lpp_source, rq_name):
    """
    Compute lpp source name based on lpp_source and rq_name.
    When no lpp_source is specified the lpp_source_name is <rq_name>-lpp_source

    arguments:
        module     (dict): The Ansible module
        lpp_source  (str): lpp source name
        rq_name     (str): SUMA request name based on metadata info
    return:
        lpp_src     the name of the lpp_source
    """
    lpp_src = ''
    oslevel = rq_name
    if lpp_source and lpp_source.strip():
        lpp_src = lpp_source
    else:
        if re.match(r"^([0-9]{4}-[0-9]{2})$", oslevel):
            oslevel = oslevel + '-00-0000'
        lpp_src = "{0}-lpp_source".format(oslevel)

    return lpp_src


def compute_dl_target(module, download_dir, lpp_source, nim_lpp_sources):
    """
    Compute suma download target directory.

    Check if a lpp_source NIM resource already exists and check the location is the same.
    If download_dir is not set look for an existing NIM resource and return its location.
    Otherwise return the default location: /usr/sys/inst.images

    arguments:
        module          (dict): The Ansible module
        download_dir     (str): directory
        lpp_source       (str): lpp source name
        nim_lpp_sources (dict): NIM lpp_source list
    note:
        Exits with fail_json in case of error
    return:
        dl_target value or msg in case of error
    """
    global results

    if download_dir:
        dl_target = "{0}/{1}".format(download_dir, lpp_source)
        if lpp_source in nim_lpp_sources and nim_lpp_sources[lpp_source] != dl_target:
            msg = "lpp source location mismatch. A lpp source '{0}' already exists with a location different from '{1}'".format(lpp_source, dl_target)
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)
    else:
        if lpp_source in nim_lpp_sources:
            dl_target = nim_lpp_sources[lpp_source]
        else:
            dl_target = '/usr/sys/inst.images'

    return dl_target


def suma_command(module, action, suma_params):
    """
    Run a suma command.

    arguments:
        module      (dict): The Ansible module
        action       (str): preview or download
        suma_params (dict): parameters to build the suma command
    note:
        Exits with fail_json in case of error
    return:
       stdout  suma command output
    """
    global results

    rq_type = suma_params['RqType']
    if rq_type == 'Latest':
        rq_type = 'SP'

    cmd = ['/usr/sbin/suma', '-x']
    cmd += ['-a', 'RqType={0}'.format(rq_type)]
    cmd += ['-a', 'Action={0}'.format(action)]
    cmd += ['-a', 'FilterML={0}'.format(suma_params['FilterMl'])]
    cmd += ['-a', 'DLTarget={0}'.format(suma_params['DLTarget'])]
    cmd += ['-a', 'RqName={0}'.format(suma_params['RqName'])]
    cmd += ['-a', 'DisplayName={0}'.format(suma_params['description'])]
    cmd += ['-a', 'FilterDir={0}'.format(suma_params['DLTarget'])]

    if suma_params['extend_fs']:
        cmd += ['-a', 'Extend=y']
    else:
        cmd += ['-a', 'Extend=n']

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if rc != 0:
        msg = "Suma {0} command '{1}' failed with return code {2}".format(action, ' '.join(cmd), rc)
        module.log(msg + ", stderr: {0}, stdout:{1}".format(stderr, stdout))
        results['msg'] = msg
        module.fail_json(**results)

    return stdout


def suma_download(module, suma_params):
    """
    Dowload (or preview) action

    suma_params['action'] should be set to either 'preview' or 'download'.

    arguments:
        module      (dict): The Ansible module
        suma_params (dict): parameters to build the suma command
    note:
        Exits with fail_json in case of error
    """
    global results

    targets_list = suma_params['targets']
    req_oslevel = suma_params['req_oslevel']

    if not targets_list:
        if req_oslevel == 'Latest':
            msg = 'Oslevel target could not be empty or equal "Latest" when' \
                  ' target machine list is empty'
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)
        elif re.match(r"^([0-9]{4}-[0-9]{2})(-00|-00-0000)$", req_oslevel):
            msg = 'When no Service Pack is provided , a target machine list is required'
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)
    else:
        if re.match(r"^([0-9]{4})(|-00|-00-00|-00-00-0000)$", req_oslevel):
            msg = 'Specify a non 0 value for the Technical Level or the Service Pack'
            module.log(msg)
            results['msg'] = msg
            module.fail_json(**results)

    # Build NIM lpp_source list
    nim_lpp_sources = get_nim_lpp_source(module)
    module.debug("lpp source list: {0}".format(nim_lpp_sources))

    # Build nim_clients list
    nim_clients = get_nim_clients(module)
    nim_clients.append('master')
    module.debug("NIM Clients: {0}".format(nim_clients))

    # Build targets list from nim_clients list
    target_clients = expand_targets(module, targets_list, nim_clients)
    results['target_list'] = target_clients
    if targets_list and not target_clients:
        msg = 'No matching NIM client found for target \'{0}\'.'.format(suma_params['targets'])
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)
    module.debug('Target list: {0}'.format(target_clients))

    # Get the oslevels of the specified targets only
    clients_oslevel = get_oslevels(module, target_clients)
    module.debug("client oslevel dict: {0}".format(clients_oslevel))

    # Delete clients with no oslevel value
    removed_oslevel = []
    for key in [k for (k, v) in clients_oslevel.items() if not v]:
        removed_oslevel.append(key)
        del clients_oslevel[key]

    # Check we have at least one oslevel when a target is specified
    if targets_list and not clients_oslevel:
        msg = "Cannot retrieve oslevel for any NIM client of the target list"
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)
    module.debug("oslevel cleaned dict: {0}".format(clients_oslevel))

    if removed_oslevel:
        msg = "Unavailable client: {0}".format(removed_oslevel)
        module.log('[WARNING] ' + msg)
        results['meta']['messages'].append(msg)

    # compute SUMA request type based on oslevel property
    rq_type = compute_rq_type(module, suma_params['req_oslevel'], targets_list)
    if rq_type == 'ERROR':
        msg = "Invalid oslevel: '{0}'".format(suma_params['req_oslevel'])
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)
    suma_params['RqType'] = rq_type
    module.debug("SUMA req Type: {0}".format(rq_type))

    # compute SUMA request name based on metadata info
    rq_name = compute_rq_name(module, suma_params, rq_type, suma_params['req_oslevel'], clients_oslevel)
    suma_params['RqName'] = rq_name
    module.debug("Suma req Name: {0}".format(rq_name))

    # Compute the filter_ml i.e. the min oslevel from the clients_oslevel
    filter_ml = compute_filter_ml(module, clients_oslevel, rq_name)
    suma_params['FilterMl'] = filter_ml
    module.debug("SUMA req filter min Oslevel: {0}".format(filter_ml))

    if filter_ml is None:
        # no technical level found for the target machines
        msg = "There is no target machine matching the requested oslevel {0}.".format(rq_name[:10])
        module.log(msg)
        results['msg'] = msg
        module.fail_json(**results)

    # compute lpp source name based on request name
    lpp_source = compute_lpp_source_name(module, suma_params['lpp_source_name'], rq_name)
    suma_params['LppSource'] = lpp_source
    module.debug("Lpp source name: {0}".format(lpp_source))

    # compute suma dl target based on lpp source name
    dl_target = compute_dl_target(module, suma_params['download_dir'], lpp_source, nim_lpp_sources)
    suma_params['DLTarget'] = dl_target
    module.debug("DL target: {0}".format(dl_target))

    # user messages
    results['meta']['messages'].append("lpp_source will be: {0}.".format(lpp_source))
    results['meta']['messages'].append("lpp_source location will be: {0}.".format(dl_target))
    results['meta']['messages'].append("lpp_source will be available to update machines from {0}-00 to {1}.".format(filter_ml, rq_name))
    if rq_type == 'Latest':
        msg = 'The latest SP of {0} is: {1}'.format(filter_ml, rq_name)
        module.log(msg)
        results['meta']['messages'].append(msg)

    suma_params['comments'] = '"Updates from {0} to {1}, built by Ansible Aix Automate infrastructure updates tools"'.format(filter_ml, rq_name)

    if not os.path.exists(dl_target):
        os.makedirs(dl_target)

    # SUMA command for preview
    stdout = suma_command(module, 'Preview', suma_params)
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

    # SUMA command for download
    if downloaded != 0:
        stdout = suma_command(module, 'Download', suma_params)
        module.debug("SUMA dowload stdout:{0}".format(stdout))

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

    # Create the associated NIM resource if necessary
    if not suma_params['download_only'] and lpp_source not in nim_lpp_sources:
        # nim -o define command
        cmd = ['/usr/sbin/nim', '-o', 'define', '-t', 'lpp_source', '-a', 'server=master']
        cmd += ['-a', 'location={0}'.format(suma_params['DLTarget'])]
        cmd += ['-a', 'packages=all']
        cmd += ['-a', 'comments={0}'.format(suma_params['comments'])]
        cmd += ['{0}'.format(suma_params['LppSource'])]

        rc, stdout, stderr = module.run_command(cmd)
        results['stdout'] = stdout
        results['stderr'] = stderr
        if rc != 0:
            msg = "NIM command '{0}' failed with return code {1}".format(' '.join(cmd), rc)
            module.log(msg + ", stderr:{0}, stdout:{1}".format(stderr, stdout))
            results['msg'] = msg
            module.fail_json(**results)

        results['changed'] = True


##############################################################################

def main():
    global results
    suma_params = {}

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=False,
                        choices=['download', 'preview'],
                        type='str', default='preview'),
            targets=dict(required=True, type='list', elements='str'),
            oslevel=dict(required=False, type='str', default='Latest'),
            lpp_source_name=dict(required=False, type='str'),
            download_dir=dict(required=False, type='path'),
            download_only=dict(required=False, type='bool', default=False),
            extend_fs=dict(required=False, type='bool', default=True),
            description=dict(required=False, type='str'),
            metadata_dir=dict(required=False, type='path', default='/var/adm/ansible/metadata'),
        ),
        supports_check_mode=True
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
        meta={'messages': []},
        target_list=(),
    )

    module.debug('*** START ***')

    suma_params['LppSource'] = ''
    suma_params['target_clients'] = ()

    # Get Module params
    action = module.params['action']
    suma_params['action'] = action
    suma_params['targets'] = module.params['targets']
    suma_params['download_dir'] = module.params['download_dir']
    suma_params['download_only'] = module.params['download_only']
    suma_params['lpp_source_name'] = module.params['lpp_source_name']
    suma_params['extend_fs'] = module.params['extend_fs']
    if module.params['oslevel'].upper() == 'LATEST':
        suma_params['req_oslevel'] = 'Latest'
    else:
        suma_params['req_oslevel'] = module.params['oslevel']
    if module.params['description']:
        suma_params['description'] = module.params['description']
    else:
        suma_params['description'] = "{0} request for oslevel {1}".format(action, suma_params['req_oslevel'])
    suma_params['metadata_dir'] = module.params['metadata_dir']

    # Run Suma preview or download
    suma_download(module, suma_params)

    # Exit
    msg = 'Suma {0} completed successfully'.format(action)
    module.log(msg)
    results['msg'] = msg
    results['lpp_source_name'] = suma_params['LppSource']
    results['target_list'] = suma_params['target_clients']
    module.exit_json(**results)


if __name__ == '__main__':
    main()
