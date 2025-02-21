#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: flrtvc
short_description: Generate FLRTVC report, download and install security and HIPER fixes.
description:
- Applies known security and HIPER (High Impact PERvasive) fixes on your system based on its
  inventory ensuring the systems are at supported and secure levels.
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
- 'Privileged user with authorizations: B(aix.fs.manage.change,aix.system.install)'
- 'set environment as PATH: "/usr/bin:/usr/sbin/:/opt/freeware/bin"'
options:
  apar:
    description:
    - Type of APAR to check against.
    - C(sec) stands for Security vulnerabilities.
    - C(hiper) stands for Corrections to High Impact PERvasive threats.
    - C(all) has the same behavior as C(None) hence both C(sec) and C(hiper) vulnerabilities.
    type: str
    choices: [ sec, hiper, all, None ]
    default: None
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
    - Specifies to save the FLRTVC report in file 'I(path)/flrtvc.txt'.
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
  protocol:
    description:
    - Optional setting which specifies preferred protocol to use for downloading files.
    - When set, downloads will be attempted using set protocol.
    type: str
    choices: [ https, http, ftp ]
  flrtvczip:
    description:
    - Specifies alternative location (local repository) hosting flrtvc.zip file.
    - When set, download of FLRTVC-Latest.zip will be attempted from this url.
    type: str
    default: "https://esupport.ibm.com/customercare/sas/f/flrt3/FLRTVC-latest.zip"
  localpatchserver:
    description:
    - Specifies local server ip/hostname containing ifix patches.
    - When set, urls from frltvc.ksh will replaced with localpatchserver to point to local server.
    type: str
    default: ''
  localpatchpath:
    description:
    - Specifies local server path containing ifix patches.
    - When set, sub paths from frltvc.ksh containing patches will replaced with localpatchpath to point to local path.
    type: str
    default: ''
notes:
  - Refer to the FLRTVC page for detail on the script.
    U(https://esupport.ibm.com/customercare/flrt/sas?page=../jsp/flrtvc.jsp)
  - The FLRTVC ksh script is packaged as a ZIP file with the FLRTVC.ksh script and LICENSE.txt file.
    It is downloaded from U(https://esupport.ibm.com/customercare/sas/f/flrt3/FLRTVC-latest.zip).
  - The script requires ksh93 to use.
  - B(v0.8.1) is the current version of the script, depending on changes, this module might need to
    be updated.
  - When the FLRTVC ksh script cannot execute the emgr command, it tries with B(sudo), so you can
    try installing B(sudo) on the managed system.
  - When use local patch server settings  localpatchserver and localpatchpath must be both set
    in order to have a complete full url with patches, for example the local url
    192.168.1.100/ifix should become in module localpatchserver 192.168.1.100 and localpatchpath ifix.
  - Using this module with Python version 3.9.20 can lead to erroneous conditions. It is recommended
    to use Python version 3.11 or later.
'''

EXAMPLES = r'''
- name: Download patches for security vulnerabilities
  flrtvc:
    apar: sec
    path: /usr/sys/inst.images
    download_only: true

- name: Install both sec and hyper patches for all filesets starting with devices.fcp
  flrtvc:
    filesets: devices.fcp.*
    path: /usr/sys/inst
    save_report: true
    verbose: true
    force: false
    clean: false

- name: Install patches from local patch server
  flrtvc:
    apar: sec
    protocol: https
    localpatchserver: 192.168.1.1
    localpatchpath: ifix
    flrtvczip: https://192.168.1.1/ifix/flrtvc.zip
    csv: https://192.168.1.1/ifix/apar.csv
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'FLRTVC completed successfully'
meta:
    description: Detailed information on the module execution.
    returned: always
    type: dict
    contains:
        messages:
            description: Details on errors/warnings
            returned: always
            type: list
            elements: str
            sample: see sample of meta
        0.report:
            description: Output of the FLRTVC script, report and details on flrtvc error if any.
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
            description: List of epkgs actually installed on the system.
            returned: if install succeeds
            type: list
            elements: str
            sample: see sample of meta
    sample:
        "meta": {
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
__metaclass__ = type


module = None
results = None
workdir = ""
system_type = ""

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
            thd = threading.Thread(target=func, args=args)
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


def get_system_type(module):
    """
    Utility function to determine the type of system
    args:
        module: Ansible module
    return:
        Nothing
    """
    global system_type

    cmd = "ls /usr/ios/cli/ioscli >/dev/null 2>&1"

    rc = module.run_command(cmd, use_unsafe_shell=True)[0]

    if not rc:
        system_type = "VIOS"
    else:
        system_type = "AIX"


def increase_fs(dest):
    """
    Increase filesystem by 100Mb
    args:
        dst (str): The absolute filename
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
    msg = f'Cannot increase filesystem for {dest}.'
    results['meta']['messages'].append(msg)
    return False


def download(src, dst, resize_fs=True):
    """
    Download efix from url to directory
    args:
        src       (str): The url to download
        dst       (str): The absolute destination filename
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
                if resize_fs and increase_fs(dst):
                    os.remove(dst)
                    return download(src, dst, resize_fs)
            elif rc != 0:
                msg = f'Cannot download {src}'
                module.log(msg)
                module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
                results['meta']['messages'].append(msg)
                res = False
        else:
            msg = 'Cannot locate wget package, please install related package.'
            module.log(msg)
            results['meta']['messages'].append(msg)
            res = False
    else:
        module.debug(f'{dst} already exists')
    return res


def unzip(src, dst, resize_fs=True):
    """
    Unzip source into the destination directory
    args:
        src       (str): The url to unzip
        dst       (str): The absolute destination path
        resize_fs (bool): Increase the filesystem size if needed
    return:
        True if unzip succeeded
        False otherwise
    """
    try:
        with zipfile.ZipFile(src) as zfile:
            zfile.extractall(dst)
    except (zipfile.BadZipfile, zipfile.LargeZipFile, RuntimeError) as exc:
        if resize_fs and increase_fs(dst):
            return unzip(src, dst, resize_fs)
        else:
            msg = f'Cannot unzip {src}'
            module.log(msg)
            module.log(f'EXCEPTION {exc}')
            results['meta']['messages'].append(msg)
            return False
    return True


def remove_efix():
    """
    Remove efix matching the given label
    return:
        True if remove succeeded
        False otherwise
    """
    res = True
    module.debug('Removing all installed efix')

    # List epkg on the system
    cmd = ['/usr/sbin/emgr', '-P']
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
    if rc != 0:
        msg = 'Cannot list interim fix to remove'
        module.log(msg)
        module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
        results['meta']['messages'].append(f'{msg}: {stderr}')
        return False

    # Create a list of unique epkg label
    # stdout is either empty (if there is no epkg data on the system) or contains
    # the following
    # PACKAGE                                                  INSTALLER   LABEL
    # ======================================================== =========== ==========
    # X11.base.rte                                             installp    IJ11547s0a
    # bos.net.tcp.client_core                                  installp    IJ09623s2a
    # bos.perf.perfstat                                        installp    IJ09623s2a
    epkgs = [epkg.strip().split()[-1] for epkg in stdout.strip().splitlines()]
    if len(epkgs) >= 2:
        del epkgs[0:2]
    epkgs = list(set(epkgs))

    # Remove each epkg from their label
    for epkg in epkgs:
        cmd = ['/usr/sbin/emgr', '-r', '-L', epkg]
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            res = False
            continue
        for line in stdout.strip().splitlines():
            match = re.match(r'^\d+\s+(\S+)\s+REMOVE\s+(\S+)\s*$', line)
            if match:
                msg_efix = match.group(1)
                if 'SUCCESS' in match.group(2):
                    msg = f'efix {msg_efix} removed, please check if you want to reinstall it'
                    module.log(msg)
                    results['meta']['messages'].append(msg)
                else:
                    msg = f'Cannot remove efix {msg_efix}, see logs for details'
                    module.log(msg)
                    results['meta']['messages'].append(msg)
                    res = False
    return res


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
        part1 = match.group(1)
        part2 = match.group(2)
        date = f'{part1} UTC {part2}'
    else:
        match = re.match(r'^(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\d{4})$', date)
        if match:
            part1 = match.group(1)
            part2 = match.group(3)
            date = f'{part1} UTC {part2}'
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


def check_epkgs(epkg_list, lpps, efixes):
    """
    For each epkg get the label, packaging date, filset and check prerequisites
    based on fileset current level and build a list ordered by packaging date
    that should not be locked at its installation.

    Note: in case of parsing error, keep the epkg (best effort)

    args:
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
    # let's build a dictionary indexed upon file location
    locked_files = {}
    for efix in efixes:
        for file in efixes[efix]['files']:
            if file not in locked_files:
                locked_files[file] = efix
    module.debug(f'locked_files: {locked_files}')

    # Get information on efix we want to install and check it can be installed
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
        cmd_path = epkg['path']
        cmd = f'/usr/sbin/emgr -dXv3 -e {cmd_path} | /bin/grep -p -e PREREQ -e PACKAG'
        rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
        if rc != 0:
            msg = f'Cannot get efix information {cmd_path}'
            module.log(msg)
            module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
            results['meta']['messages'].append(msg)
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
                log_epkg_path = os.path.basename(epkg['path'])
                epkg['reject'] = f'{log_epkg_path}: prerequisite missing: {prereq}'
                module.log(f'{log_epkg_path}: prerequisite missing: {prereq}')
                break  # stop parsing

            # check filseset prerequisite is present
            minlvl_i = list(map(int, epkg['prereq'][prereq]['minlvl'].split('.')))
            maxlvl_i = list(map(int, epkg['prereq'][prereq]['maxlvl'].split('.')))
            if lpps[prereq]['int'] < minlvl_i or lpps[prereq]['int'] > maxlvl_i:
                msg_path = os.path.basename(epkg['path'])
                msg_minlvl = epkg['prereq'][prereq]['minlvl']
                msg_str = lpps[prereq]['str']
                msg_maxlevel = epkg['prereq'][prereq]['maxlvl']
                epkg_msg = f'{msg_path}: prerequisite {prereq} levels do not satisfy condition string: \
                    {msg_minlvl} =< {msg_str} =< {msg_maxlevel}'
                epkg['reject'] = epkg_msg
                module.log(f'reject: {epkg_msg}')
                break
        if epkg['reject']:
            epkgs_reject.append(epkg['reject'])
            continue

        # check file locked by efix already installed
        for file in epkg['files']:
            if file in locked_files:
                msg_files = locked_files[file]
                msg_path = os.path.basename(epkg['path'])
                results['meta']['messages'].append(f'installed efix {msg_files} is locking {file} preventing the '
                                                   f'installation of {msg_path}, remove it manually or set the '
                                                   '"force" option.')
                reject_msg = f'{msg_path}: installed efix {msg_files} is locking {file}'
                epkg['reject'] = reject_msg
                module.log(f'reject {reject_msg}')
                epkgs_reject.append(epkg['reject'])
                continue
        if epkg['reject']:
            continue

        # convert packaging date into time in sec from epoch

        if epkg['pkg_date']:
            (sec_from_epoch, msg) = to_utc_epoch(epkg['pkg_date'])
            if sec_from_epoch == -1:
                log_date = epkg['pkg_date']
                module.log(f'{msg}: "{log_date}" for epkg:{epkg}')
            epkg['sec_from_epoch'] = sec_from_epoch

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
        else:
            msg_path = os.path.basename(epkgs_info[epkg]['path'])
            results['meta']['messages'].append(f'a previous efix to install will lock a file of {msg_path} '
                                               'preventing its installation, install it manually or '
                                               'run the task again.')
            msg_reject = f'{msg_path}: locked by previous efix to install'
            epkgs_info[epkg]['reject'] = msg_reject
            module.log(f'reject: {msg_reject}')
            epkgs_reject.append(epkgs_info[epkg]['reject'])
            removed_epkg.append(epkg)
    for epkg in removed_epkg:
        sorted_epkgs.remove(epkg)

    epkgs_reject = sorted(epkgs_reject)  # order the reject list by label

    return (sorted_epkgs, epkgs_reject)


def parse_lpps_info():
    """
    Parse the lslpp file and build a dictionary with installed lpps current levels
    returns:
        The list of epkg to install (ordered by packaging date)
    """

    lpps_lvl = {}
    lslpp_file = os.path.join(workdir, 'lslpp.txt')

    with open(os.path.abspath(lslpp_file), mode='r', encoding="utf-8") as myfile:
        for myline in myfile:
            # beginning of line: "bos:bos.rte:7.1.5.0: : :C: :Base Operating System Runtime"
            mylist = myline.split(':')
            if len(mylist) < 3:
                msg = f'file {lslpp_file} is malformed'
                module.log(f'{msg}: got line: "{myline}"')
                results['meta']['messages'].append(msg)
                continue
            lpps_lvl[mylist[1]] = {'str': mylist[2]}
            mylist[2] = re.sub(r'-', '.', mylist[2])

            lpps_lvl[mylist[1]]['int'] = []
            for version in mylist[2].split('.'):
                match_key = re.match(r"^(\d+)(\D+\S*)?$", version)
                if match_key:
                    lpps_lvl[mylist[1]]['int'].append(int(match_key.group(1)))
                    if match_key.group(2):
                        log_list = mylist[2]
                        log_group = match_key.group(2)
                        module.log(f'file {lslpp_file}: got version "{log_list}", ignoring "{log_group}"')
                else:
                    msg = f'file {lslpp_file} is malformed'
                    module.log(f'{msg}: got version: "{version}"')
                    results['meta']['messages'].append(msg)
                    continue

    return lpps_lvl


@start_threaded(THRDS)
def run_lslpp(filename):
    """
    Use lslpp on a target system to list filesets and write into provided file.
    args:
        filename (str): The filename to store output
    return:
        True if lslpp succeeded
        False otherwise
    """
    module.debug(f'{filename}')
    cmd = ['/bin/lslpp', '-Lcq']
    debug_cmd = ' '.join(cmd)
    module.debug(f'run cmd="{debug_cmd}"')
    rc, stdout, stderr = module.run_command(cmd)

    if rc == 0:
        with open(filename, mode='w', encoding="utf-8") as myfile:
            myfile.write(stdout)
        return True
    else:
        msg = 'Failed to list fileset'
        module.log(msg)
        module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
        return False


def parse_stdout(stdout):
    """
    Utility function to parse the output in accordance with the system type
    args:
        stdout      (str): standard output obtained
    return:
        parsed_list (list): List of all the Fixes according to system type [AIX/VIOS]
    """

    # Fetch whether the system is AIX or VIOS
    get_system_type(module)

    stdout = stdout.splitlines()

    header = "Fileset|Current Version|Type|EFix Installed|Abstract|Unsafe Versions|APARs"
    header += "|Bulletin URL|Download URL|CVSS Base Score|Reboot Required|Last Update|Fixed In"

    index = 0

    while stdout[index] != header:
        index += 1

    parsed_list = [stdout[index]]

    for line in stdout[index:]:
        fixed_in_val = line.split("|")[-1]
        if "See Bulletin" in fixed_in_val:
            parsed_list.append(line)
        else:
            if "-" in fixed_in_val and system_type == "AIX":
                parsed_list.append(line)
            if "." in fixed_in_val and system_type == "VIOS":
                parsed_list.append(line)

    return parsed_list


def parse_emgr():
    """
    Parse the emgr file and build a dictionary with efix data
    return:
        The dictionary with efixe data as the following structure:
            efixes[label]['files'][file]
            efixes[label]['packages'][package]
    """

    efixes = {}
    emgr_file = os.path.join(workdir, 'emgr.txt')
    label = ''
    file = ''
    package = ''

    with open(os.path.abspath(emgr_file), mode='r', encoding="utf-8") as myfile:
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
def run_emgr(f_efix):
    """
    Use the interim fix manager to list detailed information of
    installed efix and locked packages on the target machine
    and write into provided file.
    args:
        f_efix       (str): The filename to store output of emgr -lv3
        f_locked_pkg (str): The filename to store output of emgr -P
    return:
        True if emgr succeeded
        False otherwise
    """

    # list efix information
    cmd = ['/usr/sbin/emgr', '-lv3']
    debug_cmd = ' '.join(cmd)
    module.debug(f'run cmd="{debug_cmd}"')
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        with open(f_efix, mode='w', encoding="utf-8") as myfile:
            myfile.write(stdout)
        return True
    else:
        msg = 'Failed to list interim fix information'
        module.log(msg)
        module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
        return False


def run_flrtvc(flrtvc_path, params, force):
    """
    Use the flrtvc script on target system to get the
    args:
        flrtvc_path (str): The path to the flrtvc script to run
        params     (dict): The parameters to pass to flrtvc command
        force      (bool): The flag to automatically remove efixes
    note:
        Create and build results['meta']['0.report']
    return:
        True if flrtvc succeeded
        False otherwise
    """

    if force:
        remove_efix()

    # Run 'lslpp -Lcq' on the system and save to file
    lslpp_file = os.path.join(workdir, 'lslpp.txt')
    if os.path.exists(lslpp_file):
        os.remove(lslpp_file)
    run_lslpp(lslpp_file)

    # Run 'emgr -lv3' on the system and save to file
    emgr_file = os.path.join(workdir, 'emgr.txt')
    if os.path.exists(emgr_file):
        os.remove(emgr_file)
    run_emgr(emgr_file)

    # Wait until threads finish
    wait_all()

    if not os.path.exists(lslpp_file) or not os.path.exists(emgr_file):
        if not os.path.exists(lslpp_file):
            results['meta']['messages'].append(f'Failed to list filsets (lslpp), {lslpp_file} \
                                              does not exist')
        if not os.path.exists(emgr_file):
            results['meta']['messages'].append(f'Failed to list fixes (emgr), {emgr_file} does not exist')
        return False

    # Prepare flrtvc command
    cmd = [flrtvc_path, '-e', emgr_file, '-l', lslpp_file]
    if params['apar_type'] and params['apar_type'] != 'all':
        cmd += ['-t', params['apar_type']]
    if params['apar_csv']:
        cmd += ['-f', params['apar_csv']]
    if params['filesets']:
        cmd += ['-g', params['filesets']]

    # Run flrtvc in compact mode
    debug_cmd = ' '.join(cmd)
    module.debug(f'run flrtvc in compact mode: cmd="{debug_cmd}"')
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0 and rc != 2:
        msg = f'Failed to get flrtvc report, rc={rc}'
        module.log(msg)
        module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
        results['meta']['messages'].append(msg + f" stderr: {stderr}")
        return False

    parsed_out = parse_stdout(stdout)

    results['meta'].update({'0.report': parsed_out})

    # Save to file
    if params['save_report']:
        filename = os.path.join(params['dst_path'], 'flrtvc.txt')
        with open(filename, mode='w', encoding="utf-8") as myfile:
            # rerun the command in verbose mode if needed
            if params['verbose']:
                cmd += ['-v']
                debug_cmd = ' '.join(cmd)
                module.debug(f'write flrtvc report to file, cmd "{debug_cmd}"')
                rc, stdout, stderr = module.run_command(cmd)
                # quick fix as flrtvc.ksh returns 2 if vulnerabities with some fixes found
                if rc != 0 and rc != 2:
                    msg = f'Failed to save flrtvc report in file, rc={rc}'
                    module.log(msg)
                    module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
                    results['meta']['messages'].append(msg)
            myfile.write(stdout)
    # There is no need to continue if there are no vulnerabilities.
    if re.search(r"No vulnerabilities", stdout):
        results['msg'] = 'There are no vulnerabities. \nFLRTVC completed successfully'
        module.log(results['msg'])
        module.exit_json(**results)
    return True


def run_parser(report, localpatchserver, localpatchpath):
    """
    Parse report by extracting URLs
    args:
        report  (str): The compact report
    note:
        Create and build results['meta']['1.parse']
    """

    protocol = module.params['protocol']
    dict_rows = csv.DictReader(report, delimiter='|')
    rule1 = r'^(http|https|ftp)://(aix.software.ibm.com|public.dhe.ibm.com)'
    rule2 = r'/(aix/ifixes/.*?/|aix/efixes/security/.*?.tar)$'
    if localpatchserver != "":
        rule1 = r'^(http|https|ftp)://(aix.software.ibm.com|public.dhe.ibm.com|' + localpatchserver + ')'
    if localpatchpath != "":
        rule2 = r'/(aix/ifixes/.*?/|aix/efixes/security/.*?.tar|' + localpatchpath + '/.*?.tar)$'

    pattern = re.compile(rule1 + rule2)

    rows = []
    for row in dict_rows:
        row = row['Download URL']
        if protocol:
            row = re.sub(r'^(https|http|ftp)', protocol, row, count=1)
        if localpatchserver:
            row = re.sub(r'://(aix.software.ibm.com|public.dhe.ibm.com)/', '://' + localpatchserver + '/', row, count=1)
        if localpatchpath:
            row = re.sub(r'/(aix/ifixes/|aix/efixes/security)/', '/' + localpatchpath + '/', row, count=1)
        rows.append(row)

    selected_rows = [row for row in rows if pattern.match(row) is not None]
    rows = list(set(selected_rows))  # remove duplicates
    debug_len = len(rows)
    module.debug(f'extracted {debug_len} urls in the report')
    results['meta'].update({'1.parse': rows})


def run_downloader(urls, dst_path, resize_fs=True):
    """
    Download URLs and check efixes
    args:
        urls      (list): The list of URLs to download
        dst_path   (str): Path directory where to download
        resize_fs (bool): Increase the filesystem size if needed
    note:
        Create and build
            results['meta']['2.discover']
            results['meta']['3.download']
            results['meta']['4.1.reject']
            results['meta']['4.2.check']
    """
    out = {'messages': results['meta']['messages'],
           '2.discover': [],
           '3.download': [],
           '4.1.reject': [],
           '4.2.check': []}

    for url in urls:
        protocol, srv, rep, name = re.search(r'^(.*?)://(.*?)/(.*)/(.*)$', url).groups()
        module.debug(f'protocol={protocol}, srv={srv}, rep={rep}, name={name}')

        if '.epkg.Z' in name:  # URL as an efix file
            module.debug('treat url as an epkg file')
            out['2.discover'].append(name)

            # download epkg file
            epkg = os.path.abspath(os.path.join(dst_path, name))
            if download(url, epkg, resize_fs):
                out['3.download'].append(epkg)

        elif '.tar' in name:  # URL as a tar file
            module.debug('treat url as a tar file')
            dst = os.path.abspath(os.path.join(dst_path, name))

            # download and open tar file
            if download(url, dst, resize_fs):
                with tarfile.open(dst, mode='r', encoding="utf-8") as tar:

                    # find all epkg in tar file
                    epkgs = [epkg for epkg in tar.getnames() if re.search(r'(\b[\w.-]+.epkg.Z\b)$', epkg)]
                    out['2.discover'].extend(epkgs)
                    debug_len = len(epkgs)
                    module.debug(f'found {debug_len} epkg.Z file in tar file')

                    # extract epkg
                    tar_dir = os.path.join(dst_path, 'tardir')
                    if not os.path.exists(tar_dir):
                        os.makedirs(tar_dir)
                    for epkg in epkgs:
                        for attempt in range(3):
                            try:
                                tar.extract(epkg, tar_dir)
                            except (OSError, IOError, tarfile.TarError) as exc:
                                if resize_fs:
                                    increase_fs(tar_dir)
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
                            module.log(msg)
                            results['meta']['messages'].append(msg)
                            continue
                        out['3.download'].append(os.path.abspath(os.path.join(tar_dir, epkg)))

        else:  # URL as a Directory
            module.debug('treat url as a directory')

            response = open_url(url, validate_certs=False)

            # find all epkg in html body
            epkgs = re.findall(r'(\b[\w.-]+.epkg.Z\b)', response.read().decode('utf-8'))

            epkgs = list(set(epkgs))

            out['2.discover'].extend(epkgs)
            debug_len = len(epkgs)
            module.debug(f'found {debug_len} epkg.Z file in html body')

            # download epkg
            epkgs = [os.path.abspath(os.path.join(dst_path, epkg)) for epkg in epkgs
                     if download(os.path.join(url, epkg),
                                 os.path.abspath(os.path.join(dst_path, epkg)),
                                 resize_fs)]
            out['3.download'].extend(epkgs)

    # Get installed filesets' levels
    lpps_lvl = parse_lpps_info()

    # Build the dict of current fileset with their level
    curr_efixes = parse_emgr()

    # check prerequisite
    (out['4.2.check'], out['4.1.reject']) = check_epkgs(out['3.download'],
                                                        lpps_lvl, curr_efixes)
    results['meta'].update(out)


def run_installer(epkgs, dst_path, resize_fs=True):
    """
    Install epkgs efixes
    args:
        epkgs     (list): The list of efixes to install
        dst_path   (str): Path directory where to install
        resize_fs (bool): Increase the filesystem size if needed
    return:
        True if geninstall succeeded
        False otherwise
    note:
        epkgs should be results['meta']['4.2.check'] which is
        sorted against packaging date. Do not change the order.
        Create and build results['meta']['5.install']
    """
    if not epkgs:
        # There were fixes downloaded but not interim fixes, which are the ones
        # the flrtvc module could install.
        msg = 'There are no interim fixes in epkg format to be installed.'
        results['meta']['messages'].append(msg)
        return True

    destpath = os.path.abspath(os.path.join(dst_path))
    destpath = os.path.join(destpath, 'flrtvc_lpp_source', 'emgr', 'ppc')
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
                    increase_fs(destpath)
                else:
                    msg = f'Cannot copy file {epkg} to {destpath}'
                    module.log(msg)
                    module.log(f'EXCEPTION {exc}')
                    results['meta']['messages'].append(msg)
                    break
            else:
                break
        else:
            msg = f'Cannot copy file {epkg} to {destpath}'
            module.log(msg)
            results['meta']['messages'].append(msg)
            continue
        epkgs_base.append(os.path.basename(epkg))

    # return error if we have nothing to install
    if not epkgs_base:
        return False

    efixes = ' '.join(epkgs_base)

    # perform customization
    cmd = ['/usr/sbin/geninstall', '-d', destpath, efixes]
    debug_cmd = ' '.join(cmd)
    module.debug(f'Perform customization, cmd "{debug_cmd}"')
    rc, stdout, stderr = module.run_command(cmd)
    module.debug(f'geninstall stdout:{stdout}')

    results['changed'] = True   # Some efixes might be installed
    results['meta'].update({'5.install': stdout.splitlines()})

    if rc != 0:
        msg = f'Cannot perform customization, rc={rc}'
        module.log(msg)
        module.log(f'cmd:{cmd} failed rc={rc} stdout:{stdout} stderr:{stderr}')
        results['meta']['messages'].append(msg)
        return False

    return True


###################################################################################################

def main():
    global module
    global results
    global workdir

    module = AnsibleModule(
        argument_spec=dict(
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
            protocol=dict(required=False, type='str', choices=['https', 'http', 'ftp']),
            localpatchserver=dict(required=False, type='str', default=""),
            localpatchpath=dict(required=False, type='str', default=""),
            flrtvczip=dict(required=False, type='str', default='https://esupport.ibm.com/customercare/sas/f/flrt3/FLRTVC-latest.zip'),
        ),
        supports_check_mode=True
    )

    results = dict(
        changed=False,
        msg='',
        meta={'messages': []}
        # meta structure will be updated as follow:
        # meta={'messages': [],     detail execution messages
        #       '0.report': [],     run_flrtvc reports the vulnerabilities
        #       '1.parse': [],      run_parser builds the list of URLs
        #       '2.discover': [],   run_downloader builds the list of epkgs found in URLs
        #       '3.download': [],   run_downloader builds the list of downloaded epkgs
        #       '4.1.reject': [],   check_epkgs builds the list of rejected epkgs
        #       '4.2.check': [],    check_epkgs builds the list of epkgs checking prerequisites
        #       '5.install': []}    run_installer builds the list of installed epkgs
    )

    module.debug('*** START ***')
    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C', LC_CTYPE='C')

    # ===========================================
    # Get module params
    # ===========================================
    module.debug('*** INIT ***')

    # Used for independence vs Ansible options
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
    flrtvczip = module.params['flrtvczip']
    localpatchserver = module.params['localpatchserver']
    localpatchpath = module.params['localpatchpath']

    # Create working directory if needed
    workdir = os.path.abspath(os.path.join(flrtvc_params['dst_path'], 'work'))
    if not os.path.exists(workdir):
        os.makedirs(workdir, mode=0o744)

    # ===========================================
    # Install flrtvc script
    # ===========================================
    module.debug('*** INSTALL ***')
    flrtvc_dir = os.path.abspath(os.path.join('usr', 'bin'))
    flrtvc_path = os.path.abspath(os.path.join(flrtvc_dir, 'flrtvc.ksh'))

    if os.path.exists(flrtvc_path):
        try:
            os.remove(flrtvc_path)
        except OSError as exc:
            msg = f'Exception removing {flrtvc_path}, exception={exc}'
            module.log(msg)
            results['meta']['messages'].append(msg)

    flrtvc_dst = os.path.abspath(os.path.join(workdir, 'FLRTVC-latest.zip'))
    if not download(flrtvczip, flrtvc_dst, resize_fs):
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'Failed to download FLRTVC-latest.zip'
        module.fail_json(**results)

    if not unzip(flrtvc_dst, flrtvc_dir, resize_fs):
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
    if not run_flrtvc(flrtvc_path, flrtvc_params, force):
        msg = 'Failed to get vulnerabilities report, system will not be updated'
        results['msg'] = msg
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        module.fail_json(**results)

    if check_only:
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'exit on check only'
        module.exit_json(**results)

    # ===========================================
    # Parse flrtvc report
    # ===========================================
    module.debug('*** PARSE ***')
    run_parser(results['meta']['0.report'], localpatchserver, localpatchpath)

    # ===========================================
    # Download and check efixes
    # ===========================================
    module.debug('*** DOWNLOAD ***')
    run_downloader(results['meta']['1.parse'], workdir, resize_fs)

    if download_only:
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        results['msg'] = 'exit on download only'
        module.exit_json(**results)

    # ===========================================
    # Install efixes
    # ===========================================
    module.debug('*** UPDATE ***')
    if not run_installer(results['meta']['4.2.check'], workdir, resize_fs):
        msg = 'Failed to install fixes, please check meta and log data.'
        results['msg'] = msg
        if clean and os.path.exists(workdir):
            shutil.rmtree(workdir, ignore_errors=True)
        module.fail_json(**results)

    if clean and os.path.exists(workdir):
        shutil.rmtree(workdir, ignore_errors=True)

    results['msg'] = 'FLRTVC completed successfully'
    module.log(results['msg'])
    module.exit_json(**results)


if __name__ == '__main__':
    main()
