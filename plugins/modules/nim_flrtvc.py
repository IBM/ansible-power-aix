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
module: nim_flrtvc
short_description: Use NIM to generate FLRTVC report, download and install security and HIPER fixes.
description:
- Use the NIM master to apply known security and HIPER (High Impact PERvasive) fixes on target
  systems based on their inventory ensuring the systems are at supported and secure levels.
- It downloads and uses the Fix Level Recommendation Tool Vulnerability Checker script to generate
  a report. It parses this report, downloads the required fixes, extracts the files and checks their
  versions against installed software levels. It also checks for file locking preventing fix
  installation. It rejects fixes that do not match these requirements and installs the remaining.
- In case of inter-locking file(s) you might want run against the task.
- You will get the list of installed and rejected fixes in the results meta data.
version_added: '0.4.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorizations:
  B(aix.fs.manage.change,aix.system.install,aix.system.nim.config.server)'
options:
  targets:
    description:
    - Specifies the NIM clients to perform the action on.
    - C(foo*) specifies all the NIM clients with name starting by C(foo).
    - C(foo[2:4]) specifies the NIM clients among foo2, foo3 and foo4.
    - C(*) or C(ALL) specifies all the NIM clients.
    type: list
    elements: str
    required: true
  apar:
    description:
    - Type of APAR to check or download.
    - C(sec) stands for Security vulnerabilities.
    - C(hiper) stands for Corrections to High Impact PERvasive threats.
    - C(all) has the same behavior as C(None) hence both C(sec) and C(hiper) vulnerabilities.
    type: str
    choices: [ sec, hiper, all, None ]
  filesets:
    description:
    - Filter filesets for specific phrase. Only fixes that apply to filesets matching the specified
      phrase will be checked and so updated.
    type: str
  csv:
    description:
    - Path to a APAR CSV file containing the description of the C(sec) and C(hiper) fixes.
    - This file is usually transferred from the Fix Central server; you can avoid this rather big
      transfer by specifying the path to an already transferred file.
    type: str
  path:
    description:
    - Specifies the directory to save the FLRTVC report.
    - All temporary files such as installed filesets, fixes listings and downloaded fixes files are
      stored in the working subdirectory named 'I(path)/work'.
    type: str
    default: /var/adm/ansible
  save_report:
    description:
    - Specifies to save the FLRTVC report in file 'I(path)/flrtvc_<nim_client_name>.txt'.
    type: bool
    default: no
  verbose:
    description:
    - Generate full FLRTVC reporting (verbose mode).
    - It runs the FLRTVC script a second time to save the full report into file. So this option
      impacts the execution performance.
    type: bool
    default: no
  force:
    description:
    - Specifies to remove currently installed ifix before running the FLRTVC script.
    type: bool
    default: no
  clean:
    description:
    - Cleanup working directory 'I(path)/work' with all temporary and downloaded files
      at the end of execution.
    type: bool
    default: no
  check_only:
    description:
    - Specifies to only check if fixes are already applied on the targets.
    - B(No download or installation) operations will be performed.
    type: bool
    default: no
  download_only:
    description:
    - Specifies to perform check and download operation only.
    - B(No installation) will be performed.
    type: bool
    default: no
  extend_fs:
    description:
    - Specifies to increase filesystem size of the working directory when extra space is needed.
    - When set, a filesystem could have increased while the task returns I(changed=False).
    type: bool
    default: yes
notes:
  - Refer to the FLRTVC page for detail on the sctipt
    U(https://esupport.ibm.com/customercare/flrt/sas?page=../jsp/flrtvc.jsp)
  - The FLRTVC ksh script is packaged as a ZIP file with the FLRTVC.ksh script and LICENSE.txt file.
    It is downloaded from U(https://esupport.ibm.com/customercare/sas/f/flrt3/FLRTVC-latest.zip).
  - The script requires ksh93 to use.
  - B(v0.8.1) is the current version of the script, depending on changes, this module might need to
    be updated.
'''

EXAMPLES = r'''
- name: Download patches for security vulnerabilities
  nim_flrtvc:
    targets: nimclient01
    apar: sec
    path: /usr/sys/inst.images
    download_only: true

- name: Install both sec and hyper patches for all filesets starting with devices.fcp
  nim_flrtvc:
    targets: nimclient02
    filesets: devices.fcp.*
    path: /usr/sys/inst
    save_report: true
    verbose: true
    force: false
    clean: false
'''

RETURN = r'''
msg:
    description: Status information.
    returned: always
    type: str
    sample: 'exit on download only'
targets:
    description: List of NIM clients actually targeted for the operation.
    returned: always
    type: list
    elements: str
    sample: [nimclient01, nimclient02, ...]
status:
    description:
    - Status for each C(target). It can be empty, SUCCESS or FAILURE.
    - If I(download_only=True), refer to C(meta[<target>][messages]) and
      C(meta[<target>][4.1.reject]) for error checking.
    returned: always
    type: dict
    elements: str
meta:
    description: Detailed information on the module execution.
    returned: always
    type: dict
    contains:
        messages:
            description: Details on errors/warnings not related to a specific machine
            returned: always
            type: list
            elements: str
            sample: see sample of meta
        <target>:
            description: Detailed information on the execution on the <target>.
            returned: when target is actually a NIM client or master
            type: dict
            contains:
                messages:
                    description: Details on errors/warnings
                    returned: always
                    type: list
                    elements: str
                    sample: see sample of meta
                0.report:
                    description: Output of the FLRTVC script, report or details on flrtvc error if any.
                    returned: if the FLRTVC script succeeds
                    type: list
                    elements: str
                    sample: see sample of meta
                1.parse:
                    description: List of URLs to download and details on parsing error if any.
                    returned: if the FLRTVC report parsing succeeds
                    type: list
                    elements: str
                    sample: see sample of meta
                2.discover:
                    description:
                    - List of epkgs found in URLs.
                    - URLs can be eFix or tar files or directories needing parsing.
                    returned: if the URL downloads and epkgs listing succeed
                    type: list
                    elements: str
                    sample: see sample of meta
                3.download:
                    description: List of downloaded epkgs.
                    returned: if download operation succeeds
                    type: list
                    elements: str
                    sample: see sample of meta
                4.1.reject:
                    description:
                    - List of epkgs rejected. Can be because installed levels do not match ifix required
                      levels or because a file is or will be locked by an other ifix installation.
                    - You should refer to messages or to log file for very detailed reason.
                    returned: if check succeeds
                    type: list
                    elements: str
                    sample: see sample of meta
                4.2.check:
                    description: List of epkgs matching the prerequisites and trying to install.
                    returned: if check succeeds
                    type: list
                    elements: str
                    sample: see sample of meta
                5.install:
                    description: List of epkgs actually installed on the <target> system.
                    returned: if install succeeds
                    type: list
                    elements: str
                    sample: see sample of meta
    sample:
        "meta": {
            "messages": [
                "Exception removing /usr/bin/flrtvc.ksh, exception=Access is denied",
                ...,
            ],
            "nimclient01": {
                "0.report": [
                    "Fileset|Current Version|Type|EFix Installed|Abstract|Unsafe Versions|APARs|Bulletin URL|Download URL|CVSS Base Score|Reboot Required|
                     Last Update|Fixed In",
                    "bos.net.tcp.client_core|7.2.3.15|sec||NOT FIXED - There is a vulnerability in FreeBSD that affects AIX.|7.2.3.0-7.2.3.15|
                     IJ09625 / CVE-2018-6922|http://aix.software.ibm.com/aix/efixes/security/freebsd_advisory.asc|\
                     ftp://aix.software.ibm.com/aix/efixes/security/freebsd_fix.tar|CVE-2018-6922:7.5|NO|11/08/2018|7200-03-03",
                    ...,
                ],
                "1.parse": [
                    "ftp://aix.software.ibm.com/aix/efixes/security/ntp_fix12.tar",
                    "ftp://aix.software.ibm.com/aix/efixes/security/tcpdump_fix4.tar",
                    ...,
                ],
                "2.discover": [
                    "ntp_fix12/IJ17059m9b.190719.epkg.Z",
                    "ntp_fix12/IJ17060m9a.190628.epkg.Z",
                    ...,
                    "tcpdump_fix4/IJ12978s9a.190215.epkg.Z",
                    "tcpdump_fix4/IJ12978sBa.190215.epkg.Z",
                    ...,
                ],
                "3.download": [
                    "/usr/sys/inst.images/tardir/ntp_fix12/IJ17059m9b.190719.epkg.Z",
                    "/usr/sys/inst.images/tardir/ntp_fix12/IJ17060m9a.190628.epkg.Z",
                    ...,
                    "/usr/sys/inst.images/tardir/tcpdump_fix4/IJ12978s9a.190215.epkg.Z",
                    "/usr/sys/inst.images/tardir/tcpdump_fix4/IJ12978sBa.190215.epkg.Z",
                    ...,
                ],
                "4.1.reject": [
                    "102p_fix: prerequisite openssl.base levels do not satisfy condition string: 1.0.2.1600 =< 1.0.2.1500 =< 1.0.2.1600",
                    ...,
                    "IJ12983m2a: locked by previous efix to install",
                    ...,
                    "IJ17059m9b: prerequisite missing: ntp.rte",
                    ...,
                ],
                "4.2.check": [
                    "/usr/sys/inst.images/tardir/tcpdump_fix5/IJ20785s2a.191119.epkg.Z",
                    ...,
                ],
                "5.install": [
                    "/usr/sys/inst.images/tardir/tcpdump_fix5/IJ20785s2a.191119.epkg.Z",
                    ...,
                ],
                "messages": [
                    "a previous efix to install will lock a file of IJ20785s3a preventing its installation, install it manually or run the task again.",
                    ...,
                ]
            },
            "nimclient02": {
                ...,
            }
        }
'''

import os
import re
import csv
import threading
import shutil
import tarfile
import zipfile
import stat
import time
import calendar

from collections import OrderedDict
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import open_url

module = None
results = None
workdir = ''

# Threading
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
            module.debug(f'Start thread {func.__name__}')
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


def compute_c_rsh_rc(machine, rc, stdout):
    """
    Extract the rc of c_rsh command from the stdout.

    When running a remote command over c_rsh, we can echo rc=$? to get
    the actual return code on the nim master (not the c_rsh return code).

    args:
        machine (str): The NIM host we executed run_command against
        rc      (int): The run_command return code
        stdout  (str): The run_command stdout
    return:
        rc      (int): The return code of the actual command
        stdout  (str): The command stdout without the "rc=$?" string
    """
    if machine != 'master':
        s = re.search(r'rc=([-\d]+)$', stdout)
        if s:
            if rc == 0:
                rc = int(s.group(1))
            stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)
    return rc, stdout


def nim_exec(module, node, command):
    """
    Execute the specified command on the specified nim client using c_rsh.

    return
        - rc      return code of the command
        - stdout  stdout of the command
        - stderr  stderr of the command
    """

    command = ' '.join(command)
    rcmd = f'( LC_ALL=C {command} ); echo rc=$?'
    cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', node, rcmd]

    module.debug(f'exec command:{cmd}')

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return (rc, stdout, stderr)

    s = re.search(r'rc=([-\d]+)$', stdout)
    if s:
        rc = int(s.group(1))
        # remove the rc of c_rsh with echo $?
        stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)

    module.debug(f'exec command rc:{rc}, output:{stdout}, stderr:{stderr}')

    return (rc, stdout, stderr)


def increase_fs(module, output, dest):
    """
    Increase filesystem by 100Mb
    args:
        module  (dict): The Ansible module
        output (dict): The result of the execution for the target host
        dst      (str): The absolute filename
    return:
        True if increase succeeded
        False otherwise
    """
    cmd = ['/bin/df', '-c', dest]
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        mount_point = stdout.splitlines()[1].split(':')[6]
        cmd = ['chfs', '-a', 'size=+100M', mount_point]
        rc, stdout, stderr = module.run_command(cmd)
        if rc == 0:
            module.debug(f'{mount_point}: increased 100Mb: {stdout}')
            return True

    module.log(f'[WARNING] {mount_point}: cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
    msg = f'Cannot increase filesystem: {mount_point}.'
    output['messages'].append(msg)
    return False


def download(module, output, src, dst, resize_fs=True):
    """
    Download efix from url to directory
    args:
        module (dict): The Ansible module
        output (dict): The result of the execution for the target host
        src     (str): The url to download
        dst     (str): The absolute destination filename
        resize_fs (bool): Increase the filesystem size if needed
    return:
        True if download succeeded
        False otherwise
    """
    res = True
    wget = module.get_bin_path("wget", required=False, opt_dirs=['/opt/freeware/bin'])
    if not os.path.isfile(dst):
        module.debug(f'downloading {src} to {dst}...')
        if wget is not None:
            cmd = [wget, '--no-check-certificate', src, '-P', os.path.dirname(dst)]
            rc, stdout, stderr = module.run_command(cmd)
            if rc == 3:
                if resize_fs and increase_fs(module, output, dst):
                    os.remove(dst)
                    return download(module, output, src, dst, resize_fs)
            elif rc != 0:
                msg = f'Cannot download {src}'
                module.log(msg)
                module.log(f'cmd={cmd} rc={rc} stdout:{stdout} stderr:{stderr}')
                output['messages'].append(msg)
                res = False
        else:
            msg = f'Cannot locate wget, please install related package.'
            module.log(msg)
            output['messages'].append(msg)
            res = False
    else:
        module.debug(f'{dst} already exists')
    return res


def unzip(module, output, src, dst, resize_fs=True):
    """
    Unzip source into the destination directory
    args:
        module (dict): The Ansible module
        output (dict): The result of the execution for the target host
        src     (str): The url to unzip
        dst     (str): The absolute destination path
    """
    try:
        with zipfile.ZipFile(src) as zfile:
            zfile.extractall(dst)
    except (zipfile.BadZipfile, zipfile.LargeZipFile, RuntimeError) as exc:
        if resize_fs and increase_fs(module, output, dst):
            return unzip(module, output, src, dst, resize_fs)
        else:
            msg = f'Cannot unzip {src}, exception:{exc}'
            module.log(msg)
            output['messages'].append(msg)
            return False
    return True


def remove_efix(module, output, machine):
    """
    Remove efix with the given label on the machine
    args:
        module (dict): The Ansible module
        output (dict): The result of the execution for the target host
        machine (str): The target machine
    return:
        0 if remove succeeded, 1 otherwise
    """
    failed_rm = 0
    module.debug(f'{machine}: Removing all installed efix')

    if 'master' in machine:
        cmd = []
    else:
        cmd = ['/usr/lpp/bos.sysmgt/nim/methods/c_rsh', machine]

    cmd += ['"export LC_ALL=C; rc=0;'
            r' for i in `/usr/sbin/emgr -P |/usr/bin/tail -n +4 |/usr/bin/awk \'{print \$NF}\'`;'
            ' do /usr/sbin/emgr -r -L $i || (( rc = rc | $? )); done; echo rc=$rc"']

    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
    if rc != 0:
        msg = f'Cannot remove efix on {machine}, command \'{cmd}\' returned rc: {rc}'
        output['messages'].append(msg)
        module.log('[WARNING] ' + machine + ': ' + msg)
        return rc
    rc, stdout = compute_c_rsh_rc(machine, rc, stdout)

    for line in stdout.splitlines():
        match = re.match(r'^\d+\s+(\S+)\s+REMOVE\s+(\S+)\s*$', line)
        if match:
            match_grp = match.group(1)
            if 'SUCCESS' in match.group(2):
                msg = f'efix {match_grp} removed, please check if you want to reinstall it'
                module.log(machine + ': ' + msg)
                output['messages'].append(msg)
            else:
                msg = f'Cannot remove efix {match_grp}, see logs for details'
                output['messages'].append(msg)
                module.log('[WARNING] ' + machine + ': ' + msg)
                failed_rm += 1
    if failed_rm or rc:
        msg = f'failed to remove {failed_rm} efix(es)'
        output['messages'].append(msg)
        module.log(f'[WARNING] {machine}: {msg}')
        module.log(f'[WARNING] {machine}: stderr: {stderr}, stdout: {stdout}')

    return failed_rm or rc


def to_utc_epoch(date):
    """
    Return the time (UTC time zone) in second from unix epoch (int)

    args:
        date (str) : time to convert in sec from epoch with the format:
                     'Mon Oct 9 23:35:09 CDT 2017'
    returns: (epoch, msg)
        The value in sec from epoch , ''
        -1,  'error message in case of error'
    """

    TZ = 'UTC'
    msg = ''
    sec_from_epoch = -1
    # supported TZ translation
    shift = {'CDT': -5, 'CEST': 2, 'CET': 1, 'CST': -6, 'CT': -6,
             'EDT': -4, 'EET': 2, 'EST': -5, 'ET': -5,
             'IST': 5.5,
             'JST': 9,
             'MSK': 3, 'MT': 2,
             'NZST': 12,
             'PDT': -7, 'PST': -8,
             'SAST': 2,
             'UTC': 0,
             'WEST': 1, 'WET': 0}

    # if no time zone, consider it's UTC
    match = re.match(r'^(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+)\s+(\d{4})$', date)
    if match:
        match_grp1 = match.group(1)
        match_grp2 = match.group(2)
        date = f'{match_grp1} UTC {match_grp2}'
    else:
        match = re.match(r'^(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\d{4})$', date)
        if match:
            match_grp1 = match.group(1)
            match_grp3 = match.group(3)
            date = f'{match_grp1} UTC {match_grp3}'
            TZ = match.group(2)
        else:  # should not happen
            return (-1, 'bad packaging date format')

    try:
        datet = time.strptime(date, "%a %b %d %H:%M:%S %Z %Y")
        sec_from_epoch = calendar.timegm(datet)
    except ValueError:
        return (-1, 'EXCEPTION: cannot parse packaging date')

    if TZ not in shift:
        msg = 'Unsuported Time Zone: "TZ", using "UTC"'
        TZ = 'UTC'

    sec_from_epoch = sec_from_epoch - (shift[TZ] * 3600)

    return (sec_from_epoch, msg)


def check_epkgs(module, output, machine, epkg_list, lpps, efixes):
    """
    For each epkg get the label, packaging date, filset and check prerequisites
    based on fileset current level and build a list ordered by packaging date
    that should not be locked at its installation.

    Note: in case of parsing error, keep the epkg (best effort)

    args:
        module (dict): The Ansible module
        output    (dict): The result of the command
        machine   (str) : The target machine
        epkg_list (list): The list of efixes to check
        lpps      (dict): The current lpps levels
        efixes    (dict): The current efixes info
    returns:
        The list of epkg to install (ordered by packaging date)
        The list of epkg to rejected with the reason (ordered by label)
    """

    epkgs_info = {}
    epkgs_reject = []

    # Installed efix could lock some files we will try to modify,
    # build a dictionary indexed upon file location
    locked_files = {}
    for efix in efixes:
        for file in efixes[efix]['files']:
            if file not in locked_files:
                locked_files[file] = efix
    module.debug(f'{machine}: locked_files: {locked_files}')

    # Get information on efix we want to install
    # and check it could be installed
    for epkg_path in epkg_list:
        epkg = {'path': epkg_path,
                'label': '',
                'pkg_date': None,
                'sec_from_epoch': -1,
                'filesets': [],
                'files': [],
                'prereq': {},
                'reject': False}

        # get efix information
        epkg_path = epkg['path']
        cmd = f'/usr/sbin/emgr -dXv3 -e {epkg_path} | /bin/grep -p -e PREREQ -e PACKAG'
        rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
        if rc != 0:
            msg = f'Cannot get efix information {epkg_path}'
            module.log(msg)
            module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
            output['messages'].append(msg)
            # do not break or continue, we keep this efix, will try to install it anyway

        # ordered parsing: expecting the following line order:
        # LABEL, PACKAGING DATE, then PACKAGE, then prerequisites levels
        for line in stdout.splitlines():
            # skip comments and empty lines
            line = line.rstrip()
            if not line or line.startswith('+'):
                continue  # skip blank and comment line

            if not epkg['label']:
                # match: "LABEL:            IJ02726s8a"
                match = re.match(r'^LABEL:\s+(\S+)$', line)
                if match:
                    epkg['label'] = match.group(1)
                    continue

            if not epkg['pkg_date']:
                # match: "PACKAGING DATE:   Mon Oct  9 09:35:09 CDT 2017"
                match = re.match(r'^PACKAGING\s+DATE:\s+'
                                 r'(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+\s+\S*\s*\S+).*$',
                                 line)
                if match:
                    epkg['pkg_date'] = match.group(1)
                    continue

            # match: "   PACKAGE:       devices.vdevice.IBM.vfc-client.rte"
            match = re.match(r'^\s+PACKAGE:\s+(\S+)\s*?$', line)
            if match:
                if match.group(1) not in epkg['filesets']:
                    epkg['filesets'].append(match.group(1))
                continue

            # match: "   LOCATION:      /usr/lib/boot/unix_64"
            match = re.match(r'^\s+LOCATION:\s+(\S+)\s*?$', line)
            if match:
                if match.group(1) not in epkg['files']:
                    epkg['files'].append(match.group(1))
                continue

            # match and convert prerequisite levels
            # line like: "bos.net.tcp.server 7.1.3.0 7.1.3.49"
            match = re.match(r'^(\S+)\s+([\d+\.]+)\s+([\d+\.]+)\s*?$', line)
            if match is None:
                continue
            (prereq, minlvl, maxlvl) = match.groups()
            epkg['prereq'][prereq] = {}
            epkg['prereq'][prereq]['minlvl'] = minlvl
            epkg['prereq'][prereq]['maxlvl'] = maxlvl

            # parsing done
            # check filseset prerequisite is present
            if prereq not in lpps:
                basename_epkg_path = os.path.basename(epkg['path'])
                epkg['reject'] = f'{basename_epkg_path}: prerequisite missing: {prereq}'
                epkg_reject = epkg['reject']
                module.log(f'{machine}: reject {epkg_reject}')
                break  # stop parsing

            # check filseset prerequisite is present
            minlvl_i = list(map(int, epkg['prereq'][prereq]['minlvl'].split('.')))
            maxlvl_i = list(map(int, epkg['prereq'][prereq]['maxlvl'].split('.')))
            basename_epkg_path = os.path.basename(epkg['path'])
            pre_req = prereq
            prereq_minlvl = epkg['prereq'][prereq]['minlvl']
            lpps_prereq = lpps[prereq]['str']
            epkg_maxlvl = epkg['prereq'][prereq]['maxlvl']
            if lpps[prereq]['int'] < minlvl_i or lpps[prereq]['int'] > maxlvl_i:
                epkg_reject = f'{basename_epkg_path}: prerequisite {pre_req} levels do not satisfy condition string: '
                epkg_reject += f'{prereq_minlvl} =< {lpps_prereq} =< {epkg_maxlvl}'
                epkg['reject'] = epkg_reject
                epkg_reject = epkg['reject']
                module.log(f'{machine}: reject {epkg_reject}')
                break
        if epkg['reject']:
            epkgs_reject.append(epkg['reject'])
            continue

        # check file locked by efix already installed on the machine
        for file in epkg['files']:
            if file in locked_files:
                locked_files_file = locked_files[file]
                basename_epkg_path = os.path.basename(epkg['path'])
                op_msg = f"installed efix {locked_files_file} is locking {file} preventing the installation of {basename_epkg_path},"
                op_msg += " remove it manually or set the 'force' option."
                output['messages'].append(op_msg)
                locked_files_file = locked_files[file]
                epkg['reject'] = f'{basename_epkg_path}: installed efix {locked_files_file} is locking {file}'
                epkg_reject = epkg['reject']
                module.log(f'{machine}: reject {epkg_reject}')
                epkgs_reject.append(epkg['reject'])
                continue
        if epkg['reject']:
            continue

        # convert packaging date into time in sec from epoch
        if epkg['pkg_date']:
            (sec_from_epoch, msg) = to_utc_epoch(epkg['pkg_date'])
            if sec_from_epoch == -1:
                epkg_date = epkg['pkg_date']
                module.log(f'[WARNING] {machine}: {msg}: "{epkg_date}" for epkg:{epkg} ')
            epkg['sec_flogepoch'] = sec_from_epoch

        epkgs_info[epkg['path']] = epkg.copy()

    # sort the epkg by packing date (sec from epoch)
    sorted_epkgs = list(
        OrderedDict(
            sorted(
                epkgs_info.items(),
                key=lambda t: t[1]['sec_from_epoch'],
                reverse=True
            )
        ).keys()
    )

    # exclude epkg that will be interlocked
    global_file_locks = []
    removed_epkg = []
    for epkg in sorted_epkgs:
        if set(epkgs_info[epkg]['files']).isdisjoint(set(global_file_locks)):
            global_file_locks.extend(epkgs_info[epkg]['files'])
            basename_epkgs_info = os.path.basename(epkgs_info[epkg]['path'])
            epkg_info_files = epkgs_info[epkg]['files']
            module.log(f'{machine}: keep {basename_epkgs_info}, files: {epkg_info_files}')
        else:
            basename_epkg_path = os.path.basename(epkgs_info[epkg]['path'])
            output['messages'].append(f'a previous efix to install will lock a file of {0} '
                                      'preventing its installation, install it manually or '
                                      'run the task again.')
            epkgs_info[epkg]['reject'] = f'{basename_epkg_path}: locked by previous efix to install'
            epkg_info_reject = epkgs_info[epkg]['reject']
            module.log(f'{machine}: reject {epkg_info_reject}')
            epkgs_reject.append(epkgs_info[epkg]['reject'])
            removed_epkg.append(epkg)
    for epkg in removed_epkg:
        sorted_epkgs.remove(epkg)

    epkgs_reject = sorted(epkgs_reject)  # order the reject list by label

    return (sorted_epkgs, epkgs_reject)


def parse_lpps_info(module, output, machine):
    """
    Parse the lslpp output and build a dictionary with lpps current levels
    args:
        module (dict): The Ansible module
        machine (str): The remote machine name
    returns:
        The list of epkg to install (ordered by packaging date)
    """

    lpps_lvl = {}
    lslpp_file = os.path.join(workdir, f'lslpp_{machine}.txt')

    with open(os.path.abspath(os.path.join(os.sep, lslpp_file)), mode='r', encoding="utf-8") as myfile:
        for myline in myfile:
            # beginning of line: "bos:bos.rte:7.1.5.0: : :C: :Base Operating System Runtime"
            mylist = myline.split(':')
            if len(mylist) < 3:
                msg = f'file {lslpp_file} is malformed: got line: "{myline}"'
                module.log(f'{machine}: {msg}')
                output['messages'].append(msg)
                continue
            lpps_lvl[mylist[1]] = {'str': mylist[2]}
            mylist[2] = re.sub(r'-', '.', mylist[2])

            lpps_lvl[mylist[1]]['int'] = []
            for version in mylist[2].split('.'):
                match_key = re.match(r"^(\d+)(\D+\S*)?$", version)
                if match_key:
                    lpps_lvl[mylist[1]]['int'].append(int(match_key.group(1)))
                    if match_key.group(2):
                        mylist_2 = mylist[2]
                        match_key_group2 = match_key.group(2)
                        module.log(f'file {lslpp_file}: got version "{mylist_2}", ignoring "{match_key_group2}"')
                else:
                    msg = f'file {lslpp_file} is malformed'
                    module.log(f'{msg}: got version: "{version}"')
                    results['meta']['messages'].append(msg)
                    continue

    return lpps_lvl


@start_threaded(THRDS)
def run_lslpp(module, output, machine, filename):
    """
    Use lslpp on a target system to list filesets and write into provided file.
    args:
        module  (dict): The Ansible module
        output  (dict): The result of the command
        machine  (str): The remote machine name
        filename (str): The filename to store output
    """
    cmd = ['/bin/lslpp', '-Lcq']

    if machine == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, machine, cmd)

    if rc == 0:
        with open(filename, mode='w', encoding="utf-8") as myfile:
            myfile.write(stdout)
        return rc

    msg = 'Failed to list fileset'
    module.log(msg)
    module.log(f'cmd:{cmd} failed rc={rc}')
    module.log(f'stdout:{stdout}')
    module.log(f'stderr:{stderr}')
    output['messages'].append(msg)
    return rc


def parse_stdout(stdout):
    """
    Utility function to parse the output so as to exclude certificate information from stdout
    args:
        stdout      (str): standard output obtained
    return:
        parsed_list (list): List of all the Fixes without certificate information
    """

    stdout = stdout.splitlines()

    header = "Fileset|Current Version|Type|EFix Installed|Abstract|Unsafe Versions|APARs"
    header += "|Bulletin URL|Download URL|CVSS Base Score|Reboot Required|Last Update|Fixed In"

    index = 0

    while stdout[index] != header:
        index += 1

    parsed_list = stdout[index:]

    return parsed_list


def parse_emgr(machine):
    """
    Parse the emgr output and build a dictionary with efix data
    args:
        machine (str): The remote machine name
    return:
        The dictionary with efixe data as the following structure:
            efixes[label]['files'][file]
            efixes[label]['packages'][package]
    """

    efixes = {}
    emgr_file = os.path.join(workdir, f'emgr_{machine}.txt')
    label = ''
    file = ''
    package = ''

    with open(os.path.abspath(os.path.join(os.sep, emgr_file)), mode='r', encoding="utf-8") as myfile:
        for line in myfile:
            line = line.rstrip()
            if not line or line.startswith('+') or line.startswith('='):
                continue

            # "EFIX ID: 1" triggers a new efix
            match_key = re.match(r"^EFIX ID:\s+\S+$", line)
            if match_key:
                label = ''
                file = ''
                package = ''
                continue

            if not label:
                match_key = re.match(r"^EFIX LABEL:\s+(\S+)$", line)
                if match_key:
                    label = match_key.group(1)
                    efixes[label] = {}
                    efixes[label]['files'] = {}
                    efixes[label]['packages'] = {}
                continue

            # "   LOCATION:      /usr/sbin/tcpdump" triggers a new file
            match_key = re.match(r"^\s+LOCATION:\s+(\S+)$", line)
            if match_key:
                package = ''
                file = match_key.group(1)
                efixes[label]['files'][file] = file
                continue

            # "   PACKAGE:            bos.net.tcp.client
            match_key = re.match(r"^\s+PACKAGE:\s+(\S+)$", line)
            if match_key:
                file = ''
                package = match_key.group(1)
                efixes[label]['packages'][package] = package
                continue
    return efixes


@start_threaded(THRDS)
def run_emgr(module, output, machine, f_efix):
    """
    Use the interim fix manager to list detailed information of
    installed efix and locked packages on the target machine
    and write into provided file.
    args:
        module  (dict): The Ansible module
        output  (dict): The result of the command
        machine      (str): The remote machine name
        f_efix       (str): The filename to store output of emgr -lv3
    return:
        True if emgr succeeded
        False otherwise
    """
    # list efix information
    cmd = ['/usr/sbin/emgr', '-lv3']

    if machine == 'master':
        rc, stdout, stderr = module.run_command(cmd)
    else:
        rc, stdout, stderr = nim_exec(module, machine, cmd)

    if rc == 0:
        with open(f_efix, mode='w', encoding="utf-8") as myfile:
            myfile.write(stdout)
        return True

    msg = 'Failed to list interim fix information'
    module.log(msg)
    module.log(f'cmd:{cmd} failed rc={rc}')
    module.log(f'stdout:{stdout}')
    module.log(f'stderr:{stderr}')
    output['messages'].append(msg)
    return False


def run_flrtvc(module, output, machine, flrtvc_path, params, force):
    """
    Run command flrtvc on a target system
    args:
        module     (dict): The Ansible module
        output     (dict): The result of the execution for the target host
        machine     (str): The remote machine name
        flrtvc_path (str): The path to the flrtvc script to run
        params     (dict): The parameters to pass to flrtvc command
        force      (bool): The flag to automatically remove efixes
    note:
        Create and build output['0.report']
    return:
        True if flrtvc succeeded
        False otherwise
    """

    if force:
        remove_efix(module, output, machine)

    # Run 'lslpp -Lcq' on the remote machine and save to file
    lslpp_file = os.path.join(workdir, f'lslpp_{machine}.txt')
    if os.path.exists(lslpp_file):
        os.remove(lslpp_file)
    run_lslpp(module, output, machine, lslpp_file)

    # Run 'emgr -lv3' on the remote machine and save to file
    emgr_file = os.path.join(workdir, f'emgr_{machine}.txt')
    if os.path.exists(emgr_file):
        os.remove(emgr_file)
    run_emgr(module, output, machine, emgr_file)

    # Wait threads to finish
    wait_all()

    if not os.path.exists(lslpp_file) or not os.path.exists(emgr_file):
        if not os.path.exists(lslpp_file):
            output['messages'].append(f'Failed to list filsets (lslpp), {lslpp_file} does not exist')
        if not os.path.exists(emgr_file):
            output['messages'].append(f'Failed to list fixes (emgr), {emgr_file} does not exist')
        return False

    # Prepare flrtvc command
    cmd = [flrtvc_path, '-e', emgr_file, '-l', lslpp_file]
    if params['apar_type'] and params['apar_type'] != 'all':
        cmd += ['-t', params['apar_type']]
    if params['apar_csv']:
        cmd += ['-f', params['apar_csv']]
    if params['filesets']:
        cmd += ['-g', params['filesets']]

    cmd = ' '.join(cmd)
    # Run flrtvc in compact mode
    module.debug(f'{machine}: run flrtvc in compact mode: cmd="{cmd}"')
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0 and rc != 2:
        msg = f'Failed to get flrtvc report, rc={rc}'
        module.log(msg)
        module.log(f'cmd:{cmd} failed rc={rc}')
        module.log(f'stdout:{stdout}')
        module.log(f'stderr:{stderr}')
        output['messages'].append(msg + f" stderr: {stderr}")
        return False

    parsed_out = parse_stdout(stdout)
    output.update({'0.report': parsed_out})

    # Save to file
    if params['save_report']:
        filename = os.path.join(params['dst_path'], f'flrtvc_{machine}.txt')
        with open(filename, mode='w', encoding="utf-8") as myfile:
            if params['verbose']:
                cmd += ['-v']
                cmd = ' '.join(cmd)
                module.debug(f'{machine}: write flrtvc report to file, cmd "{cmd}"')
                rc, stdout, stderr = module.run_command(cmd)
                # quick fix as flrtvc.ksh returns 2 if vulnerabities with some fixes found
                if rc != 0 and rc != 2:
                    msg = f'Failed to save flrtvc report in file, rc={rc}'
                    module.log(machine + ': ' + msg)
                    module.log(f'cmd:{cmd} failed rc={rc}')
                    module.log(f'stdout:{stdout}')
                    module.log(f'stderr:{stderr}')
                    output['messages'].append(msg)
            myfile.write(stdout)

    return True


def run_parser(module, machine, output, report):
    """
    Parse report by extracting URLs
    note:
        Create and build output['1.parse']
    args:
        module (dict): The Ansible module
        machine (str): The remote machine name
        output (dict): The result of the command
        report  (str): The compact report
    """
    dict_rows = csv.DictReader(report, delimiter='|')
    pattern = re.compile(r'^(http|https|ftp)://(aix.software.ibm.com|public.dhe.ibm.com)'
                         r'/(aix/ifixes/.*?/|aix/efixes/security/.*?.tar)$')
    rows = []
    for row in dict_rows:
        rows.append(row['Download URL'])
    selected_rows = [row for row in rows if pattern.match(row) is not None]

    rows = list(set(selected_rows))  # remove duplicates
    module.debug(f'{machine}: extract {len(rows)} urls in the report')
    output.update({'1.parse': rows})


@start_threaded(THRDS)
def run_downloader(module, machine, output, urls, resize_fs=True):
    """
    Download URLs and check efixes
    args:
        module (dict): The Ansible module
        machine    (str): The remote machine name
        output    (dict): The result of the command
        urls      (list): The list of URLs to download
        resize_fs (bool): Increase the filesystem size if needed
    note:
        Create and build
            output['2.discover']
            output['3.download']
            output['4.1.reject']
            output['4.2.check']
        for the provided machine.
    """

    out = {'messages': output['messages'],
           '2.discover': [],
           '3.download': [],
           '4.1.reject': [],
           '4.2.check': []}

    for url in urls:
        protocol, srv, rep, name = re.search(r'^(.*?)://(.*?)/(.*)/(.*)$', url).groups()
        module.debug(f'{machine}: protocol={protocol}, srv={srv}, rep={rep}, name={name}')

        if '.epkg.Z' in name:  # URL as an efix file
            module.debug(f'{machine}: treat url as an epkg file')
            out['2.discover'].append(name)

            # download epkg file
            epkg = os.path.abspath(os.path.join(workdir, name))
            if download(module, out, url, epkg, resize_fs):
                out['3.download'].append(epkg)

        elif '.tar' in name:  # URL as a tar file
            module.debug(f'{machine}: treat url as a tar file')
            dst = os.path.abspath(os.path.join(workdir, name))

            # download and open tar file
            if download(module, out, url, dst, resize_fs):
                with tarfile.open(dst, mode='r', encoding="utf-8") as tar:

                    # find all epkg in tar file
                    epkgs = [epkg for epkg in tar.getnames() if re.search(r'(\b[\w.-]+.epkg.Z\b)$', epkg)]
                    out['2.discover'].extend(epkgs)
                    module.debug(f'{machine}: found {len(epkgs)} epkg.Z file in tar file')
                    # extract epkg
                    tar_dir = os.path.join(workdir, 'tardir')
                    if not os.path.exists(tar_dir):
                        os.makedirs(tar_dir)
                    for epkg in epkgs:
                        for attempt in range(3):
                            try:
                                tar.extract(epkg, tar_dir)
                            except (OSError, IOError, tarfile.TarError) as exc:
                                if resize_fs:
                                    increase_fs(module, out, tar_dir)
                                else:
                                    msg = f'Cannot extract tar file {epkg} to {tar_dir}'
                                    module.log(msg)
                                    module.log(f'EXCEPTION {exc}')
                                    results['meta']['messages'].append(msg)
                                    break
                            else:
                                break
                        else:
                            msg = f'Cannot extract tar file {epkg} to {tar_dir}'
                            module.log(f'[WARNING] {machine}: {msg}')
                            results['meta']['messages'].append(msg)
                            continue
                        out['3.download'].append(os.path.abspath(os.path.join(tar_dir, epkg)))

        else:  # URL as a Directory
            module.debug(f'{machine}: treat url as a directory')

            response = open_url(url, validate_certs=False)

            # find all epkg in html body
            epkgs = re.findall(r'(\b[\w.-]+.epkg.Z\b)', response.read().decode('utf-8'))

            epkgs = list(set(epkgs))

            out['2.discover'].extend(epkgs)
            debug_len = len(epkgs)
            module.debug(f'found {debug_len} epkg.Z file in html body')

            # download epkg
            epkgs = [os.path.abspath(os.path.join(workdir, epkg)) for epkg in epkgs
                     if download(module, out, os.path.join(url, epkg),
                                 os.path.abspath(os.path.join(workdir, epkg)), resize_fs)]
            out['3.download'].extend(epkgs)

    # Get installed filesets' levels
    lpps_lvl = parse_lpps_info(module, output, machine)

    # Build the dict of current fileset with their level
    curr_efixes = parse_emgr(machine)

    # check prerequisite
    (out['4.2.check'], out['4.1.reject']) = check_epkgs(module, out, machine,
                                                        out['3.download'],
                                                        lpps_lvl, curr_efixes)
    output.update(out)


@start_threaded(THRDS)
def run_installer(module, machine, output, epkgs, resize_fs=True):
    """
    Install epkgs efixes
    args:
        module (dict): The Ansible module
        machine (str): The remote machine name
        output (dict): The result of the command
        epkgs  (list): The list of efixes to install
        resize_fs (bool): Increase the filesystem size if needed
    return:
        True if install succeeded
        False otherwise
    note:
        epkgs should be results['meta']['4.2.check'] which is
        sorted against packaging date. Do not change the order.
        Create and build results['meta']['5.install'].
    """

    if not epkgs:
        msg = 'Nothing to install'
        results['status'][machine] = 'SUCCESS'
        output['messages'].append(msg)
        return True

    destpath = os.path.abspath(os.path.join(workdir))
    destpath = os.path.join(destpath, 'flrtvc_lpp_source', machine, 'emgr', 'ppc')
    # create lpp source location
    if not os.path.exists(destpath):
        os.makedirs(destpath)
    # copy efix destpath lpp source
    epkgs_base = []
    for epkg in epkgs:
        for attempt in range(3):
            try:
                shutil.copy(epkg, destpath)
            except (IOError, shutil.Error) as exc:
                if resize_fs:
                    increase_fs(module, output, destpath)
                else:
                    msg = f'Cannot copy file {epkg} to {destpath}: {exc}'
                    module.log(f'[WARNING] {machine}: {msg}')
                    output['messages'].append(msg)
                    break
            else:
                break
        else:
            msg = f'Cannot copy file {epkg} to {destpath}'
            module.log(f'[WARNING] {machine}: {msg}')
            output['messages'].append(msg)
            continue
        epkgs_base.append(os.path.basename(epkg))

    # return error if we have nothing to install
    if not epkgs_base:
        msg = 'Nothing to install, see syslog for details'
        output['messages'].append(msg)
        results['status'][machine] = 'FAILURE'
        return False

    efixes = ' '.join(epkgs_base)
    lpp_source = machine + '_lpp_source'

    # define lpp source
    cmd = ['/usr/sbin/lsnim', '-l', lpp_source]
    rc, stdout, stderr = module.run_command(cmd)
    if rc > 0:
        cmd = ['/usr/sbin/nim', '-o', 'define', '-t', 'lpp_source', '-a', 'server=master']
        cmd += ['-a', f'location={destpath}']
        cmd += ['-a', 'packages=all', lpp_source]
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = f'Cannot define NIM lpp_source resource {lpp_source} for location \'{destpath}\''
            module.log(f'[WARNING] {machine}: {msg}')
            output['messages'].append(msg)
            results['status'][machine] = 'FAILURE'
            return False

    # perform customization
    install_ok = False
    cmd = ['/usr/sbin/lsnim', machine]
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        nimtype = stdout.split()[2]
        if 'master' in nimtype:
            cmd = f'/usr/sbin/geninstall -d {destpath} {efixes}'
        elif 'standalone' in nimtype:
            cmd = f'/usr/sbin/nim -o cust -a lpp_source={lpp_source} -a filesets="{efixes}" {machine}'
        elif 'vios' in nimtype:
            cmd = f'/usr/sbin/nim -o updateios -a preview=no -a lpp_source={lpp_source} {machine}'

        rc, stdout, stderr = module.run_command(cmd)
        module.debug(f'{machine}: customization result is {stdout}')
        if rc == 0:
            install_ok = True

        output.update({'5.install': stdout.splitlines()})
        results['status'][machine] = 'SUCCESS'
        results['changed'] = True
    else:
        msg = f'Cannot list NIM resource for \'{machine}\''
        module.log(f'[WARNING] {msg}')
        module.log(f'[WARNING] cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
        output['messages'].append(msg)
        results['status'][machine] = 'FAILURE'

    # remove lpp source
    cmd = ['/usr/sbin/lsnim', '-l', lpp_source]
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        cmd = ['/usr/sbin/nim', '-o', 'remove', lpp_source]
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = f'Cannot remove NIM resource \'{lpp_source}\''
            module.log(f'[WARNING] {msg}')
            module.log(f'[WARNING] cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')

    return install_ok


def get_nim_clients_info(module):
    """
    Build client list (standalone and vios) with
    all NIM info from lsnim -c machines -l command
    args:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    returns:
        NIM client dictionary

    """
    info = {}

    cmd = ['lsnim', '-c', 'machines', '-l']
    cmd = ' '.join(cmd)
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = f'Cannot get NIM Client information. Command \'{cmd}\' failed with return code {rc}.'
        module.log(msg)
        results['msg'] = msg
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)

    info = build_dict(module, stdout)
    info['master'] = {}

    return info


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


def expand_targets(module, targets, nim_clients):
    """
    Expand the list of target patterns.

    A taget name can be of the following form:
        target*       all the nim client machines whose name starts
                          with 'target'
        target[n1:n2] where n1 and n2 are numeric: target<n1> to target<n2>
        * or ALL      all the nim client machines
        client_name   the nim client named 'client_name'
        master        the nim master

        sample:  target[1:5] target12 other_target*

    arguments:
        module       (dict): The Ansible module
        targets      (list): List of requested target partterns
        nim_clients  (list): List of NIM clients

    return: the list of the existing NIM client matching the target list
    """
    clients = []

    for target in targets:

        # Build target(s) from: range i.e. quimby[7:12]
        rmatch = re.match(r"(\w+)\[(\d+):(\d+)\]", target)
        if rmatch:
            name = rmatch.group(1)
            start = rmatch.group(2)
            end = rmatch.group(3)

            for i in range(int(start), int(end) + 1):
                # target_results.append('{0}{1:02}'.format(name, i))
                curr_name = name + str(i)
                if curr_name in nim_clients:
                    clients.append(curr_name)
            continue

        # Build target(s) from: val*. i.e. quimby*
        rmatch = re.match(r"(\w+)\*$", target)
        if rmatch:
            name = rmatch.group(1)

            for curr_name in nim_clients:
                if re.match(rf"^{name}\.*", curr_name):
                    clients.append(curr_name)
            continue

        # Build target(s) from: all or *
        if target.upper() == 'ALL' or target == '*':
            clients = nim_clients
            continue

        # Build target(s) from: quimby05 quimby08 quimby12
        if (target in nim_clients) or (target == 'master'):
            clients.append(target)

    return list(set(clients))


def check_targets(module, output, targets, nim_clients):
    """
    Check if each target in the target list can be reached.
    Build a new target list with reachable target only.

    arguments:
        module       (dict): The Ansible module
        output      (dict): result of the command
        targets      (str): list of existing machines
        nim_clients (dict): nim info of all clients

    """
    targets_ok = []

    for machine in targets:
        if machine == 'master':
            targets_ok.append(machine)
            continue

        if nim_clients[machine]['Cstate'] != 'ready for a NIM operation':
            module.log(f'[WARNING] {machine} is not ready for NIM operation')
            continue

        # check vios connectivity
        cmd = ['true']
        rc, stdout, stderr = nim_exec(module, machine, cmd)
        if rc != 0:
            msg = f'Cannot reach {machine} with c_rsh, rc:{rc}, stderr:{stderr}'
            module.log('[WARNING] ' + msg)
            output[machine]['messages'].append(msg)
        else:
            targets_ok.append(machine)

    return list(set(targets_ok))


###################################################################################################


def main():
    global module
    global results
    global workdir

    module = AnsibleModule(
        argument_spec=dict(
            targets=dict(required=True, type='list', elements='str'),
            apar=dict(required=False, type='str', choices=['sec', 'hiper', 'all', None], default=None),
            filesets=dict(required=False, type='str'),
            csv=dict(required=False, type='str'),
            path=dict(required=False, type='str', default='/var/adm/ansible'),
            save_report=dict(required=False, type='bool', default=False),
            verbose=dict(required=False, type='bool', default=False),
            force=dict(required=False, type='bool', default=False),
            clean=dict(required=False, type='bool', default=False),
            check_only=dict(required=False, type='bool', default=False),
            download_only=dict(required=False, type='bool', default=False),
            extend_fs=dict(required=False, type='bool', default=True),
        ),
        supports_check_mode=True
    )

    results = dict(
        changed=False,
        msg='',
        targets=[],
        meta={'messages': []},
        # meta structure will be updated as follow:
        # meta={
        #   target_name:{
        #       'messages': [],     detail execution messages
        #       '0.report': [],     run_flrtvc reports the vulnerabilities
        #       '1.parse': [],      run_parser builds the list of URLs
        #       '2.discover': [],   run_downloader builds the list of epkgs found in URLs
        #       '3.download': [],   run_downloader builds the list of downloaded epkgs
        #       '4.1.reject': [],   check_epkgs builds the list of rejected epkgs
        #       '4.2.check': [],    check_epkgs builds the list of epkgs checking prerequisites
        #       '5.install': [],    run_installer builds the list of installed epkgs
        #   }
        # }
        status={},
        # status structure will be updated as follow:
        # status={
        #   target_name: 'SUCCESS' or 'FAILURE'
        # }
    )

    module.debug('*** START ***')
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    # ===========================================
    # Get module params
    # ===========================================
    module.debug('*** INIT ***')
    targets = module.params['targets']
    flrtvc_params = {'apar_type': module.params['apar'],
                     'apar_csv': module.params['csv'],
                     'filesets': module.params['filesets'],
                     'dst_path': module.params['path'],
                     'save_report': module.params['save_report'],
                     'verbose': module.params['verbose']}
    force = module.params['force']
    clean = module.params['clean']
    check_only = module.params['check_only']
    download_only = module.params['download_only']
    resize_fs = module.params['extend_fs']

    workdir = os.path.abspath(os.path.join(flrtvc_params['dst_path'], 'work'))
    if not os.path.exists(workdir):
        os.makedirs(workdir, mode=0o744)

    # ===========================================
    # Compute targets
    # ===========================================
    # Get client list and keep targets that are part of it
    module.debug('*** OHAI ***')
    module.debug(f'requested targets are: "{targets}"')
    nim_clients = get_nim_clients_info(module)
    module.debug(f'Nim clients are: {nim_clients}')
    targets = expand_targets(module, targets, list(nim_clients.keys()))
    module.debug(f'Nim client targets are:{targets}')

    # Init metadata dictionary
    results['meta'] = {'messages': []}
    for machine in targets:
        results['meta'][machine] = {'messages': []}  # first time init
        results['status'][machine] = ''     # first time init

    # Check connectivity
    targets = check_targets(module, results['meta'], targets, nim_clients)
    module.debug(f'Available target machines are:{targets}')
    if not targets:
        msg = 'Empty target list'
        results['meta']['messages'].append(msg)
        module.log(msg)
    results['targets'] = list(targets)

    # ===========================================
    # Install flrtvc script
    # ===========================================
    module.debug('*** INSTALL ***')
    flrtvc_dir = os.path.abspath(os.path.join(os.sep, 'usr', 'bin'))
    flrtvc_path = os.path.abspath(os.path.join(flrtvc_dir, 'flrtvc.ksh'))

    # remove previous version if any
    if os.path.exists(flrtvc_path):
        try:
            os.remove(flrtvc_path)
        except OSError as exc:
            msg = f'Cannot remove {flrtvc_path}, exception:{exc}'
            module.log('[WARNING] ' + msg)
            results['meta']['messages'].append(msg)

    flrtvc_dst = os.path.abspath(os.path.join(workdir, 'FLRTVC-latest.zip'))
    if not download(module, results['meta'],
                    'https://esupport.ibm.com/customercare/sas/f/flrt3/FLRTVC-latest.zip',
                    flrtvc_dst, resize_fs):
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'Failed to download FLRTVC-latest.zip'
        module.fail_json(**results)

    if not unzip(module, results['meta'], flrtvc_dst,
                 os.path.abspath(os.path.join(os.sep, 'usr', 'bin')), resize_fs):
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'Failed to unzip FLRTVC-latest.zip'
        module.fail_json(**results)

    flrtvc_stat = os.stat(flrtvc_path)
    if not flrtvc_stat.st_mode & stat.S_IEXEC:
        os.chmod(flrtvc_path, flrtvc_stat.st_mode | stat.S_IEXEC)

    # ===========================================
    # Run flrtvc script
    # ===========================================
    module.debug('*** REPORT ***')
    wrong_targets = []
    for machine in targets:
        if not run_flrtvc(module, results['meta'][machine], machine, flrtvc_path, flrtvc_params, force):
            wrong_targets.append(machine)
    for machine in wrong_targets:
        msg = f'Failed to get vulnerabilities report, {machine} will not be updated'
        module.log('[WARNING] ' + msg)
        results['meta'][machine]['messages'].append(msg)
        results['status'][machine] = 'FAILURE'
        targets.remove(machine)
    if check_only:
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'exit on check only'
        for machine in targets:
            results['status'][machine] = 'SUCCESS'
        module.exit_json(**results)

    # ===========================================
    # Parse flrtvc report
    # ===========================================
    module.debug('*** PARSE ***')
    for machine in targets:
        run_parser(module, machine, results['meta'][machine], results['meta'][machine]['0.report'])
    wait_all()

    # ===========================================
    # Download and check efixes
    # ===========================================
    module.debug('*** DOWNLOAD ***')
    for machine in targets:
        run_downloader(module, machine, results['meta'][machine], results['meta'][machine]['1.parse'], resize_fs)
        if '4.2.check' not in results['meta'][machine]:
            msg = f'Error downloading some fixes, {machine} will not be updated'
            results['meta'][machine]['messages'].append(msg)
            results['status'][machine] = 'FAILURE'
    wait_all()

    if download_only:
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'exit on download only'
        module.exit_json(**results)

    # ===========================================
    # Install efixes
    # ===========================================
    module.debug('*** UPDATE ***')
    for machine in targets:
        if '4.2.check' in results['meta'][machine]:
            run_installer(module, machine, results['meta'][machine], results['meta'][machine]['4.2.check'], resize_fs)
    wait_all()

    if clean and os.path.exists(workdir):
        shutil.rmtree(workdir, ignore_errors=True)

    results['msg'] = 'FLRTVC completed, see status for details.'
    module.log(results['msg'])
    module.exit_json(**results)


if __name__ == '__main__':
    main()
