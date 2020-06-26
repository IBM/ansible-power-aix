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
module: flrtvc
short_description: Generate FLRTVC report, download and install efix.
description:
- Creates a task to check targets vulnerability against available fixes, and
  apply necessary fixes. It downloads and uses the Fix Level Recommendation Tool
  Vulnerability Checker Script to generates a report. It parses the report,
  downloads the fixes, checks their versions and if some files are locked. Then
  it installs the remaining fixes. In case of inter-locking file you could run
  this several times.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  apar:
    description:
    - Type of APAR to check or download.
    - C(sec) Security vulnerabilities.
    - C(hiper) Corrections to High Impact PERvasive threats.
    - C(all) Same behavior as None, both C(sec) and C(hiper) vulnerabilities.
    type: str
    choices: [ sec, hiper, all, None ]
  filesets:
    description:
    - Filter filesets for specific phrase. Only fixes on the filesets specified will be checked and updated.
    type: str
  csv:
    description:
    - Path to a APAR CSV file containing the description of the C(sec) and C(hiper) fixes.
    - This file is usually transferred from the fix server; this rather big transfer
      can be avoided by specifying an already transferred file.
    type: str
  path:
    description:
    - Specifies the directory to save the FLRTVC report. All temporary files such as
      previously installed filesets, fixes lists and downloaded fixes files will be
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
      No download or install operations.
    type: bool
    default: no
  download_only:
    description:
    - Specifies to perform check and download operation, do not install anything.
    type: bool
    default: no
  extend_fs:
    description:
    - Specifies to increase filesystem size of the working directory if needed.
    - If set a filesystem of the host could have increased even if it returns I(changed=False).
    type: bool
    default: yes
'''

EXAMPLES = r'''
- name: Download patches for security vulnerabilities
  flrtvc:
    path: /usr/sys/inst.images
    verbose: yes
    apar: sec
    download_only: yes

- name: Install both sec and hyper patches for all filesets starting with devices.fcp
  flrtvc:
    path: /usr/sys/inst
    filesets: devices.fcp.*
    verbose: yes
    force: no
    clean: no
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
            sample: see below
        0.report:
            description: Output of the FLRTVC script, report or details on flrtvc error if any.
            returned: if the FLRTVC script run succeeds
            type: list
            elements: str
            sample: see below
        1.parse:
            description: List of URLs to download or details on parsing error if any.
            returned: if the parsing succeeds
            type: list
            elements: str
            sample: see below
        2.discover:
            description: List of epkgs found in URLs.
            returned: if the discovery succeeds
            type: list
            elements: str
            sample: see below
        3.download:
            description: List of downloaded epkgs.
            returned: if download succeeds
            type: list
            elements: str
            sample: see below
        4.1.reject:
            description: List of epkgs rejected, refer to messages and log file for reason.
            returned: if check succeeds
            type: list
            elements: str
            sample: see below
        4.2.check:
            description: List of epkgs following prerequisites.
            returned: if check succeeds
            type: list
            elements: str
            sample: see below
        5.install:
            description: List of epkgs actually installed.
            returned: if install succeeds
            type: list
            elements: str
            sample: see below
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

module = None
results = None
workdir = ""

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
            module.debug('Start thread {0}'.format(func.__name__))
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
            module.debug('{0}: increased 100Mb: {1}'.format(mount_point, stdout))
            return True

    module.log('[WARNING] {0}: cmd:{1} failed rc={2} stdout:{3} stderr:{4}'
               .format(mount_point, cmd, rc, stdout, stderr))
    msg = 'Cannot increase filesystem for {0}.'.format(dest)
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
    wget = '/bin/wget'
    if not os.path.isfile(dst):
        module.debug('downloading {0} to {1}...'.format(src, dst))
        if os.path.exists(wget):
            cmd = [wget, '--no-check-certificate', src, '-P', os.path.dirname(dst)]
            rc, stdout, stderr = module.run_command(cmd)
            if rc == 3:
                if resize_fs and increase_fs(dst):
                    os.remove(dst)
                    return download(src, dst, resize_fs)
            elif rc != 0:
                msg = 'Cannot download {0}'.format(src)
                module.log(msg)
                module.log('cmd={0} rc={1} stdout:{2} stderr:{3}'
                           .format(cmd, rc, stdout, stderr))
                results['meta']['messages'].append(msg)
                res = False
        else:
            msg = 'Cannot locate {0}, please install related package.'.format(wget)
            module.log(msg)
            results['meta']['messages'].append(msg)
            res = False
    else:
        module.debug('{0} already exists'.format(dst))
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
        zfile = zipfile.ZipFile(src)
        zfile.extractall(dst)
    except (zipfile.BadZipfile, zipfile.LargeZipFile, RuntimeError) as exc:
        if resize_fs and increase_fs(dst):
            return unzip(src, dst, resize_fs)
        else:
            msg = 'Cannot unzip {0}'.format(src)
            module.log(msg)
            module.log('EXCEPTION {0}'.format(exc))
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
        module.log('cmd:{0} failed rc={1} stdout:{2} stderr:{3}'
                   .format(cmd, rc, stdout, stderr))
        results['meta']['messages'].append('{0}: {1}'.format(msg, stderr))
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
                if 'SUCCESS' in match.group(2):
                    msg = 'efix {0} removed, please check if you want to reinstall it'\
                          .format(match.group(1))
                    module.log(msg)
                    results['meta']['messages'].append(msg)
                else:
                    msg = 'Cannot remove efix {0}, see logs for details'.format(match.group(1))
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
        date = '{0} UTC {1}'.format(match.group(1), match.group(2))
    else:
        match = re.match(r'^(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\d{4})$', date)
        if match:
            date = '{0} UTC {1}'.format(match.group(1), match.group(3))
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
    module.debug('locked_files: {0}'.format(locked_files))

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
        cmd = '/usr/sbin/emgr -dXv3 -e {0} | /bin/grep -p -e PREREQ -e PACKAG'.format(epkg['path'])
        rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)
        if rc != 0:
            msg = 'Cannot get efix information {0}'.format(epkg['path'])
            module.log(msg)
            module.log('cmd:{0} failed rc={1} stdout:{2} stderr:{3}'
                       .format(cmd, rc, stdout, stderr))
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
                epkg['reject'] = '{0}: prerequisite missing: {1}'.format(os.path.basename(epkg['path']), prereq)
                module.log('reject {0}'.format(epkg['reject']))
                break  # stop parsing

            # check filseset prerequisite is present
            minlvl_i = list(map(int, epkg['prereq'][prereq]['minlvl'].split('.')))
            maxlvl_i = list(map(int, epkg['prereq'][prereq]['maxlvl'].split('.')))
            if lpps[prereq]['int'] < minlvl_i or lpps[prereq]['int'] > maxlvl_i:
                epkg['reject'] = '{0}: prerequisite {1} levels do not satisfy condition string: {2} =< {3} =< {4}'\
                                 .format(os.path.basename(epkg['path']),
                                         prereq,
                                         epkg['prereq'][prereq]['minlvl'],
                                         lpps[prereq]['str'],
                                         epkg['prereq'][prereq]['maxlvl'])
                module.log('reject {0}'.format(epkg['reject']))
                break
        if epkg['reject']:
            epkgs_reject.append(epkg['reject'])
            continue

        # check file locked by efix already installed
        for file in epkg['files']:
            if file in locked_files:
                results['meta']['messages'].append('installed efix {0} is locking {1} preventing the '
                                                   'installation of {2}, remove it manually or set the '
                                                   '"force" option.'
                                                   .format(locked_files[file], file, os.path.basename(epkg['path'])))
                epkg['reject'] = '{0}: installed efix {1} is locking {2}'\
                                 .format(os.path.basename(epkg['path']), locked_files[file], file)
                module.log('reject {0}'.format(epkg['reject']))
                epkgs_reject.append(epkg['reject'])
                continue
        if epkg['reject']:
            continue

        # convert packaging date into time in sec from epoch

        if epkg['pkg_date']:
            (sec_from_epoch, msg) = to_utc_epoch(epkg['pkg_date'])
            if sec_from_epoch == -1:
                module.log('{0}: "{1}" for epkg:{2}'.format(msg, epkg['pkg_date'], epkg))
            epkg['sec_from_epoch'] = sec_from_epoch

        epkgs_info[epkg['path']] = epkg.copy()

    # sort the epkg by packing date (sec from epoch)
    sorted_epkgs = OrderedDict(sorted(epkgs_info.items(),
                                      key=lambda t: t[1]['sec_from_epoch'],
                                      reverse=True)).keys()

    # exclude epkg that will be interlocked
    global_file_locks = []
    removed_epkg = []
    for epkg in sorted_epkgs:
        if set(epkgs_info[epkg]['files']).isdisjoint(set(global_file_locks)):
            global_file_locks.extend(epkgs_info[epkg]['files'])
            module.log('keep {0}, files: {1}'
                       .format(os.path.basename(epkgs_info[epkg]['path']), epkgs_info[epkg]['files']))
        else:
            results['meta']['messages'].append('a previous efix to install will lock a file of {0} '
                                               'preventing its installation, install it manually or '
                                               'run the task again.'
                                               .format(os.path.basename(epkgs_info[epkg]['path'])))
            epkgs_info[epkg]['reject'] = '{0}: locked by previous efix to install'\
                                         .format(os.path.basename(epkgs_info[epkg]['path']))
            module.log('reject {0}'.format(epkgs_info[epkg]['reject']))
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
    global workdir

    lpps_lvl = {}
    lslpp_file = os.path.join(workdir, 'lslpp.txt')

    with open(os.path.abspath(lslpp_file), 'r') as myfile:
        for myline in myfile:
            # beginning of line: "bos:bos.rte:7.1.5.0: : :C: :Base Operating System Runtime"
            mylist = myline.split(':')
            if len(mylist) < 3:
                msg = 'file {0} is malformed'.format(lslpp_file)
                module.log('{0}: got line: "{1}"'.format(msg, myline))
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
                        module.log('file {0}: got version "{1}", ignoring "{2}"'.format(lslpp_file, mylist[2], match_key.group(2)))
                else:
                    msg = 'file {0} is malformed'.format(lslpp_file)
                    module.log('{0}: got version: "{1}"'.format(msg, version))
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
    module.debug('{0}'.format(filename))
    cmd = ['/bin/lslpp', '-Lcq']
    module.debug('run cmd="{0}"'.format(' '.join(cmd)))
    rc, stdout, stderr = module.run_command(cmd)

    if rc == 0:
        with open(filename, 'w') as myfile:
            myfile.write(stdout)
        return True
    else:
        msg = 'Failed to list fileset'
        module.log(msg)
        module.log('cmd:{0} failed rc={1}'.format(cmd, rc))
        module.log('stdout:{0}'.format(stdout))
        module.log('stderr:{0}'.format(stderr))
        return False


def parse_emgr():
    """
    Parse the emgr file and build a dictionary with efix data
    return:
        The dictionary with efixe data as the following structure:
            efixes[label]['files'][file]
            efixes[label]['packages'][package]
    """
    global workdir

    efixes = {}
    emgr_file = os.path.join(workdir, 'emgr.txt')
    label = ''
    file = ''
    package = ''

    with open(os.path.abspath(emgr_file), 'r') as myfile:
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
    module.debug('run cmd="{0}"'.format(' '.join(cmd)))
    rc, stdout, stderr = module.run_command(cmd)
    if rc == 0:
        with open(f_efix, 'w') as myfile:
            myfile.write(stdout)
        return True
    else:
        msg = 'Failed to list interim fix information'
        module.log(msg)
        module.log('cmd:{0} failed rc={1}'.format(cmd, rc))
        module.log('stdout:{0}'.format(stdout))
        module.log('stderr:{0}'.format(stderr))
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
    global workdir

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
            results['meta']['message'].append('Failed to list filsets (lslpp), {0} does not exist'
                                              .format(lslpp_file))
        if not os.path.exists(emgr_file):
            results['meta']['message'].append('Failed to list fixes (emgr), {0} does not exist'
                                              .format(emgr_file))
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
    module.debug('run flrtvc in compact mode: cmd="{0}"'.format(' '.join(cmd)))
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0 and rc != 2:
        msg = 'Failed to get flrtvc report, rc={0}'.format(rc)
        module.log(msg)
        module.log('cmd:{0} failed rc={1}'.format(cmd, rc))
        module.log('stdout:{0}'.format(stdout))
        module.log('stderr:{0}'.format(stderr))
        results['meta']['messages'].append(msg + " stderr: {0}".format(stderr))
        return False

    results['meta'].update({'0.report': stdout.splitlines()})

    # Save to file
    if params['save_report']:
        filename = os.path.join(params['dst_path'], 'flrtvc.txt')
        with open(filename, 'w') as myfile:
            if params['verbose']:
                cmd += ['-v']

            module.debug('write flrtvc report to file, cmd "{0}"'.format(' '.join(cmd)))
            rc, stdout, stderr = module.run_command(cmd)
            # quick fix as flrtvc.ksh returns 2 if vulnerabities with some fixes found
            if rc != 0 and rc != 2:
                msg = 'Failed to save flrtvc report in file, rc={0}'.format(rc)
                module.log(msg)
                module.log('cmd:{0} failed rc={1}'.format(cmd, rc))
                module.log('stdout:{0}'.format(stdout))
                module.log('stderr:{0}'.format(stderr))
                results['meta']['messages'].append(msg)
            myfile.write(stdout)

    return True


def run_parser(report):
    """
    Parse report by extracting URLs
    args:
        report  (str): The compact report
    note:
        Create and build results['meta']['1.parse']
    """
    dict_rows = csv.DictReader(report, delimiter='|')
    pattern = re.compile(r'^(http|https|ftp)://(aix.software.ibm.com|public.dhe.ibm.com)'
                         r'/(aix/ifixes/.*?/|aix/efixes/security/.*?.tar)$')
    rows = []
    for row in dict_rows:
        rows.append(row['Download URL'])
    selected_rows = [row for row in rows if pattern.match(row) is not None]

    rows = list(set(selected_rows))  # remove duplicates
    module.debug('extracted {0} urls in the report'.format(len(rows)))
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
        module.debug('protocol={0}, srv={1}, rep={2}, name={3}'
                     .format(protocol, srv, rep, name))

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
                tar = tarfile.open(dst, 'r')

                # find all epkg in tar file
                epkgs = [epkg for epkg in tar.getnames() if re.search(r'(\b[\w.-]+.epkg.Z\b)$', epkg)]
                out['2.discover'].extend(epkgs)
                module.debug('found {0} epkg.Z file in tar file'.format(len(epkgs)))

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
                                msg = 'Cannot extract tar file {0} to {1}'.format(epkg, tar_dir)
                                module.log(msg)
                                module.log('EXCEPTION {0}'.format(exc))
                                results['meta']['messages'].append(msg)
                                break
                        else:
                            break
                    else:
                        msg = 'Cannot extract tar file {0} to {1}'.format(epkg, tar_dir)
                        module.log(msg)
                        results['meta']['messages'].append(msg)
                        continue
                    out['3.download'].append(os.path.abspath(os.path.join(tar_dir, epkg)))

        else:  # URL as a Directory
            module.debug('treat url as a directory')

            response = open_url(url, validate_certs=False)

            # find all epkg in html body
            epkgs = re.findall(r'(\b[\w.-]+.epkg.Z\b)', response.read())

            epkgs = list(set(epkgs))

            out['2.discover'].extend(epkgs)
            module.debug('found {0} epkg.Z file in html body'.format(len(epkgs)))

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
                    msg = 'Cannot copy file {0} to {1}'.format(epkg, destpath)
                    module.log(msg)
                    module.log('EXCEPTION {0}'.format(exc))
                    results['meta']['messages'].append(msg)
                    break
            else:
                break
        else:
            msg = 'Cannot copy file {0} to {1}'.format(epkg, destpath)
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
    module.debug('Perform customization, cmd "{0}"'.format(' '.join(cmd)))
    rc, stdout, stderr = module.run_command(cmd)
    module.debug('geninstall stdout:{0}'.format(stdout))

    results['changed'] = True   # Some efixes might be installed
    results['meta'].update({'5.install': stdout.splitlines()})

    if rc != 0:
        msg = 'Cannot perform customization, rc={0}'.format(rc)
        module.log(msg)
        module.log('cmd={0} rc={1} stdout:{2} stderr:{3}'
                   .format(cmd, rc, stdout, stderr))
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
            msg = 'Exception removing {0}, exception={1}'.format(flrtvc_path, exc)
            module.log(msg)
            results['meta']['messages'].append(msg)

    flrtvc_dst = os.path.abspath(os.path.join(workdir, 'FLRTVC-latest.zip'))
    if not download('https://www-304.ibm.com/webapp/set2/sas/f/flrt3/FLRTVC-latest.zip',
                    flrtvc_dst, resize_fs):
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
    run_parser(results['meta']['0.report'])

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
