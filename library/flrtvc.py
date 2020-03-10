#!/usr/bin/python
#
# Copyright:: 2020- IBM, Inc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#
######################################################################
"""AIX FLRTVC: generate flrtvc report, download and install efix"""

import logging
import os
import re
import csv
import subprocess
import threading
import urllib
import ssl
import shutil
import tarfile
import zipfile
import stat
import time
import calendar
from collections import OrderedDict

# Ansible module 'boilerplate'
from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
------
module: flrtvc
author: "Paul Finley"
version_added: "1.0.0"
requirements: [ AIX ]
"""

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
            logging.debug('Start thread {}'.format(func.__name__))
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
def download(src, dst):
    """
    Download efix from url to directory
    args:
        src (str): The url to download
        dst (str): The absolute destination filename
    return:
        True if download succeeded
        False otherwise
    """
    res = True
    wget = '/bin/wget'
    if not os.path.isfile(dst):
        logging.debug('downloading {} to {}...'.format(src, dst))
        if not os.path.exists(wget):
            logging.debug('Unable to locate {} ...'.format(wget))
        try:
            cmd = [wget, '--no-check-certificate', src, '-P', os.path.dirname(dst)]
            subprocess.check_output(args=cmd, stderr=subprocess.STDOUT)
        except subprocess.CalledProcessError as exc:
            logging.warning('EXCEPTION cmd={} rc={} output={}'
                            .format(exc.cmd, exc.returncode, exc.output))
            res = False
            if exc.returncode == 3:
                increase_fs(dst)
                os.remove(dst)
                res = download(src, dst)
    else:
        logging.debug('{} already exists'.format(dst))
    return res


@logged
def unzip(src, dst):
    """
    Unzip source into the destination directory
    args:
        src (str): The url to unzip
        dst (str): The absolute destination path
    """
    try:
        zfile = zipfile.ZipFile(src)
        zfile.extractall(dst)
    except (zipfile.BadZipfile, zipfile.LargeZipFile, RuntimeError) as exc:
        logging.warning('EXCEPTION {}'.format(exc))
        increase_fs(dst)
        unzip(src, dst)


@logged
def remove_efix(output):
    """
    Remove efix matching the given label
    args:
        output (dict): The result of the command
    return:
        0 if remove succeeded, 1 otherwise
    """
    res = 0
    logging.debug(': Removing all installed efix')

    cmd = ['"export LC_ALL=C; rc=0;'
            ' for i in `/usr/sbin/emgr -P |/usr/bin/tail -n +4 |/usr/bin/awk \'{print \$NF}\'`;'
            ' do /usr/sbin/emgr -r -L $i || (( rc = rc | $? )); done; echo rc=$rc"']

    (ret, stdout, stderr) = exec_cmd(cmd, output)

    for line in stdout.splitlines():
        match = re.match(r'^\d+\s+(\S+)\s+REMOVE\s+(\S+)\s*$', line)
        if match:
            if 'SUCCESS' in match.group(2):
                msg = 'efix {} removed, please check if you want to reinstall it'\
                      .format(match.group(1))
                logging.info(msg)
                output['messages'].append(msg)
            else:
                msg = 'Cannot remove efix {}, see logs for details'.format(match.group(1))
                output['messages'].append(msg)
                logging.warning(msg)
                res += 1
    if res:
        logging.warning('{} efix removal failed:'.format(res))
        logging.warning('stderr: {}, stdout: {}'.format(stdout, stderr))

    return res or ret


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
        date = '{} UTC {}'.format(match.group(1), match.group(2))
    else:
        match = re.match(r'^(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+)\s+(\S+)\s+(\d{4})$', date)
        if match:
            date = '{} UTC {}'.format(match.group(1), match.group(3))
            TZ = match.group(2)
        else:  # should not happen
            return (-1, 'bad packaging date format')

    try:
        datet = time.strptime(date, "%a %b %d %H:%M:%S %Z %Y")
        sec_from_epoch = calendar.timegm(datet)
    except ValueError as exc:
        return (-1, 'EXCEPTION: cannot parse packaging date')

    if TZ not in shift:
        msg = 'Unsuported Time Zone: "TZ", using "UTC"'
        TZ = 'UTC'

    sec_from_epoch = sec_from_epoch - (shift[TZ] * 3600)

    return (sec_from_epoch, msg)


@logged
def check_epkgs(epkg_list, lpps, efixes, output):
    """
    For each epkg get the label, packaging date, filset and check prerequisites
    based on fileset current level and build a list ordered by packaging date
    that should not be locked at its installation.

    Note: in case of parsing error, keep the epkg (best effort)

    args:
        epkg_list (list): The list of efixes to check
        lpps_lvl  (dict): The current lpps levels
        efixes    (dict): The current efixes info
        output    (dict): The result of the command (use only before exit)
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

    logging.debug('locked_files: {}'.format(locked_files))

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
        stdout = ''
        try:
            cmd = 'LC_ALL=C /usr/sbin/emgr -dXv3 -e {} | /bin/grep -p -e PREREQ -e PACKAG'\
                  .format(epkg['path'])
            stdout = subprocess.check_output(args=cmd, shell=True, stderr=subprocess.STDOUT)

        except subprocess.CalledProcessError as exc:
            logging.warning('EXCEPTION cmd={} rc={} output={}'
                            .format(exc.cmd, exc.returncode, exc.output))
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
                                 '(\S+\s+\S+\s+\d+\s+\d+:\d+:\d+\s+\S*\s*\S+).*$',
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
                epkg['reject'] = '{}: prerequisite missing: {}'.format(epkg['label'], prereq)
                logging.info('reject {}'.format(epkg['reject']))
                break  # stop parsing

            # check filseset prerequisite is present
            minlvl_i = list(map(int, epkg['prereq'][prereq]['minlvl'].split('.')))
            maxlvl_i = list(map(int, epkg['prereq'][prereq]['maxlvl'].split('.')))
            if lpps[prereq]['int'] < minlvl_i\
               or lpps[prereq]['int'] > maxlvl_i:
                epkg['reject'] = '{}: prerequisite {} levels do not match: {} < {} < {}'\
                                 .format(epkg['label'],
                                         prereq,
                                         epkg['prereq'][prereq]['minlvl'],
                                         lpps[prereq]['str'],
                                         epkg['prereq'][prereq]['maxlvl'])
                logging.info('reject {}'.format(epkg['reject']))
                break
        if epkg['reject']:
            epkgs_reject.append(epkg['reject'])
            continue

        # check file locked by efix already installed
        for file in epkg['files']:
            if file in locked_files:
                output['messages'].append('installed efix {} is locking {} preventing the '
                                          'installation of {}, remove it manually or set the '
                                          '"force" option.'
                                          .format(locked_files[file], file, epkg['label']))
                epkg['reject'] = '{}: installed efix {} is locking {}'\
                                 .format(epkg['label'], locked_files[file], file)
                logging.info('reject {}'.format(epkg['reject']))
                epkgs_reject.append(epkg['reject'])
                continue
        if epkg['reject']:
            continue

        # convert packaging date into time in sec from epoch
        if epkg['pkg_date']:
            (sec_from_epoch, msg) = to_utc_epoch(epkg['pkg_date'])
            if sec_from_epoch == -1:
                logging.warning('{}: "{}" for epkg:{} '
                                .format(msg, epkg['pkg_date'], epkg))
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
        lock_found = False
        if set(epkgs_info[epkg]['files']).isdisjoint(set(global_file_locks)):
            global_file_locks.extend(epkgs_info[epkg]['files'])
            logging.info('keep {}, files: {}'
                         .format(epkgs_info[epkg]['label'], epkgs_info[epkg]['files']))
        else:
            epkgs_info[epkg]['reject'] = '{}: locked by previous efix to install'\
                                         .format(epkgs_info[epkg]['label'])
            logging.info('reject {}'.format(epkgs_info[epkg]['reject']))
            epkgs_reject.append(epkgs_info[epkg]['reject'])
            removed_epkg.append(epkg)
    for epkg in removed_epkg:
        sorted_epkgs.remove(epkg)

    epkgs_reject = sorted(epkgs_reject)  # order the reject list by label

    return (sorted_epkgs, epkgs_reject)


@logged
def parse_lpps_info(out):
    """
    Parse the lslpp output and build a dictionary with lpps current levels
    args:
        output (dict): The result of the command (use only before exit)
    """
    lpps_lvl = {}
    lslpp_file = os.path.join(WORKDIR, 'lslpp.txt')

    with open(os.path.abspath(os.path.join(os.sep, lslpp_file)), 'r') as myfile:
        for myline in myfile:
            # beginning of line: "bos:bos.rte:7.1.5.0: : :C: :Base Operating System Runtime"
            mylist = myline.split(':')
            if len(mylist) < 3:
                logging.error('The file {} is malformed: got line: "{}"'
                              .format(lslpp_file, myline))
                continue
            lpps_lvl[mylist[1]] = {'str': mylist[2]}
            mylist[2] = re.sub(r'-', '.', mylist[2])
            lpps_lvl[mylist[1]]['int'] = list(map(int, mylist[2].split('.')))

    return lpps_lvl


@logged
def run_lslpp(filename, output):
    """
    Run command lslpp on a target system
    args:
        filename (str): The filename to store output
        output  (dict): The result of the command
    """
    cmd = ['/bin/lslpp', '-Lcq']
    (res, stdout, stderr) = exec_cmd(cmd, output)

    if res == 0:
        with open(filename, 'w') as myfile:
            myfile.write(stdout)
    else:
        msg = 'Failed to list fileset, command "{}" failed: "{} {}"'\
              .format(' '.join(cmd), stdout, stderr)
        logging.error(msg)
        output['messages'].append(msg)


@logged
def parse_emgr(out):
    """
    Parse the emgr output and build a dictionary with efix data
    args:
        output (dict): The result of the command (use only before exit)
    """
    global WORKDIR

    efixes = {}
    emgr_file = os.path.join(WORKDIR, 'emgr.txt')
    label = ''
    file = ''
    package = ''

    with open(os.path.abspath(os.path.join(os.sep, emgr_file)), 'r') as myfile:
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


@logged
def run_emgr(f_efix, output):
    """
    Use the interim fix manager to list detailed information of
    installed efix and locked packages on the target machine
    args:
        f_efix       (str): The filename to store output of emgr -lv3
        f_locked_pkg (str): The filename to store output of emgr -P
        output      (dict): The result of the command
    """

    # list efix information
    cmd = ['/usr/sbin/emgr', '-lv3']
    (res, stdout, stderr) = exec_cmd(cmd, output)
    if res == 0:
        with open(f_efix, 'w') as myfile:
            myfile.write(stdout)
    else:
        msg = 'Failed to list interim fix information, command "{}" failed: "{} {}"'\
              .format(' '.join(cmd), stdout, stderr)
        logging.error('{}'.format(msg))
        output['messages'].append(msg)


# @start_threaded(THRDS)
@logged
def run_flrtvc(output, params, force):
    """
    Run command flrtvc on a target system
    args:
        output  (dict): The result of the command
        params  (dict): The parameters to pass to flrtvc command
        force   (bool): The flag to automatically remove efixes
    note: exit_json if flrtvc fails
    return:
        0 if flrtvc succeeded
        1 otherwise
    """

    global WORKDIR

    if force:
        remove_efix(output)

    # Run 'lslpp -Lcq' on the system and save to file
    lslpp_file = os.path.join(WORKDIR, 'lslpp.txt')
    if os.path.exists(lslpp_file):
        os.remove(lslpp_file)
    thd1 = threading.Thread(target=run_lslpp, args=(lslpp_file, output))
    thd1.start()

    # Run 'emgr -lv3' on the system and save to file
    emgr_file = os.path.join(WORKDIR, 'emgr.txt')
    if os.path.exists(emgr_file):
        os.remove(emgr_file)
    thd2 = threading.Thread(target=run_emgr, args=(emgr_file, output))
    thd2.start()

    # Wait until threads finish
    thd1.join()
    thd2.join()

    if not os.path.exists(lslpp_file) or not os.path.exists(emgr_file):
        if not os.path.exists(lslpp_file):
            output.update({'0.report': 'Failed to list filsets (lslpp), {} does not exist'
                                       .format(lslpp_file)})
        if not os.path.exists(emgr_file):
            output.update({'0.report': 'Failed to list fixes (emgr), {} does not exist'
                                       .format(emgr_file)})
        return 1

    try:
        # Prepare flrtvc command
        cmd = ['LC_ALL=C /usr/bin/flrtvc.ksh', '-e', emgr_file, '-l', lslpp_file]
        if params['apar_type'] and params['apar_type'] != 'all':
            cmd += ['-t', params['apar_type']]
        if params['apar_csv']:
            cmd += ['-f', params['apar_csv']]
        if params['filesets']:
            cmd += ['-g', params['filesets']]

        # Run flrtvc in compact mode
        logging.debug('run cmd "{}"'.format(' '.join(cmd)))
        (res, stdout, errout) = exec_cmd(' '.join(cmd), output, False, True)
        if res != 0:
            msg = 'flrtvc failed: "{}"'.format(errout)
            logging.error('{}'.format(msg))
            output['messages'].append(msg)
        output.update({'0.report': stdout.splitlines()})

        # flrtvc_stderr = os.path.join(WORKDIR, 'flrtvc_stderr.txt')
        # myfile = open(flrtvc_stderr, 'w')
        # stdout_c = subprocess.check_output(args=cmd, stderr=myfile, shell=True)
        # output.update({'0.report': stdout_c.splitlines()})
        # myfile.close()
        # # check for error message
        # if os.path.getsize(flrtvc_stderr) > 0:
        #     with open(flrtvc_stderr, 'r') as myfile:
        #         msg = ' '.join([line.rstrip('\n') for line in myfile])
        #         msg = '{}'.format(msg)
        #         logging.error(msg)
        #         output['messages'].append(msg)
        # os.remove(flrtvc_stderr)

        # Save to file
        if params['dst_path']:
            if not os.path.exists(params['dst_path']):
                os.makedirs(params['dst_path'])
            filename = os.path.join(params['dst_path'], 'flrtvc.txt')
            with open(filename, 'w') as myfile:
                if params['verbose']:
                    cmd += ['-v']
                    logging.debug('run cmd "{}"'.format(' '.join(cmd)))
                    (res, stdout, errout) = exec_cmd(' '.join(cmd), output, False, True)
                    if res != 0:
                        msg = 'flrtvc failed: "{}"'.format(errout)
                        logging.error('{}'.format(msg))
                        output['messages'].append(msg)
                myfile.write(stdout)

    except subprocess.CalledProcessError as exc:
        logging.warning('EXCEPTION cmd={} rc={} output={}'
                        .format(exc.cmd, exc.returncode, exc.output))
        output['messages'].append(exc.output)
        output.update({'0.report': []})
        MODULE.exit_json(changed=CHANGED, msg='error executing flrtvc', meta=output)

    except OSError as exc:
        logging.warning('EXCEPTION cmd={} Exception={}'
                        .format(cmd, exc))
        output['messages'].append(exc)
        output.update({'0.report': []})
        MODULE.exit_json(changed=CHANGED, msg='error executing flrtvc', meta=output)
    return 0


# @start_threaded(THRDS)
@logged
def run_parser(output, report):
    """
    Parse report by extracting URLs
    args:
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
    logging.debug('extract {} urls in the report'.format(len(rows)))
    output.update({'1.parse': rows})


@start_threaded(THRDS)
@logged
def run_downloader(output, urls):
    """
    Download URLs and check efixes
    args:
        output (dict): The result of the command
        urls   (list): The list of URLs to download
    """

    global WORKDIR
    out = {'messages': output['messages'],
           '2.discover': [],
           '3.download': [],
           '4.1.reject': [],
           '4.2.check': []}

    for url in urls:
        protocol, srv, rep, name = re.search(r'^(.*?)://(.*?)/(.*)/(.*)$', url).groups()
        logging.debug('protocol={}, srv={}, rep={}, name={}'
                      .format(protocol, srv, rep, name))

        if '.epkg.Z' in name:  # URL as an efix file
            logging.debug('treat url as an epkg file')
            out['2.discover'].extend(name)

            # download epkg file
            epkg = os.path.abspath(os.path.join(WORKDIR, name))
            if download(url, epkg):
                out['3.download'].extend(epkg)

        elif '.tar' in name:  # URL as a tar file
            logging.debug('treat url as a tar file')
            dst = os.path.abspath(os.path.join(WORKDIR, name))

            # download and open tar file
            download(url, dst)
            tar = tarfile.open(dst, 'r')

            # find all epkg in tar file
            epkgs = [epkg for epkg in tar.getnames() if re.search(r'(\b[\w.-]+.epkg.Z\b)$', epkg)]
            out['2.discover'].extend(epkgs)
            logging.debug('found {} epkg.Z file in tar file'.format(len(epkgs)))

            # extract epkg
            tar_dir = os.path.join(WORKDIR, 'tardir')
            if not os.path.exists(tar_dir):
                os.makedirs(tar_dir)
            for epkg in epkgs:
                try:
                    tar.extract(epkg, tar_dir)
                except (OSError, IOError, tarfile.TarError) as exc:
                    logging.warning('EXCEPTION {}'.format(exc))
                    increase_fs(tar_dir)
                    tar.extract(epkg, tar_dir)
            epkgs = [os.path.abspath(os.path.join(tar_dir, epkg)) for epkg in epkgs]
            out['3.download'].extend(epkgs)

        else:  # URL as a Directory
            logging.debug('treat url as a directory')
            # pylint: disable=protected-access
            response = urllib.urlopen(url, context=ssl._create_unverified_context())

            # find all epkg in html body
            epkgs = [epkg for epkg in re.findall(r'(\b[\w.-]+.epkg.Z\b)', response.read())]

            epkgs = list(set(epkgs))

            out['2.discover'].extend(epkgs)
            logging.debug('found {} epkg.Z file in html body'.format(len(epkgs)))

            # download epkg
            epkgs = [os.path.abspath(os.path.join(WORKDIR, epkg)) for epkg in epkgs
                     if download(os.path.join(url, epkg),
                                 os.path.abspath(os.path.join(WORKDIR, epkg)))]
            out['3.download'].extend(epkgs)

    # Get installed filesets' levels
    lpps_lvl = parse_lpps_info(out)

    # Build the dict of current fileset with their level
    curr_efixes = parse_emgr(out)

    # check prerequisite
    (out['4.2.check'], out['4.1.reject']) = check_epkgs(out['3.download'],
                                                        lpps_lvl, curr_efixes, out)
    output.update(out)


@start_threaded(THRDS)
@logged
def run_installer(output, epkgs):
    """
    Install epkgs efixes
    args:
        output (dict): The result of the command
        epkgs  (list): The list of efixes to install
    note: epkgs should be output[machine]['4.2.check'] which is
          sorted against packaging date. Do not change the order.
    """

    global CHANGED
    global WORKDIR

    if not epkgs:
        return 0

    destpath = os.path.abspath(os.path.join(WORKDIR))
    destpath = os.path.join(destpath, 'flrtvc_lpp_source', 'emgr', 'ppc')
    # create lpp source location
    if not os.path.exists(destpath):
        os.makedirs(destpath)
    # copy efix destpath lpp source
    for epkg in epkgs:
        try:
            shutil.copy(epkg, destpath)
        except (IOError, shutil.Error) as exc:
            logging.warning('EXCEPTION {}'.format(exc))
            increase_fs(destpath)
            shutil.copy(epkg, destpath)
    epkgs_base = [os.path.basename(epkg) for epkg in epkgs]

    efixes = ' '.join(epkgs_base)

    # perform customization
    stdout = ''
    try:
        cmd = '/usr/sbin/geninstall -d {} {}'.format(destpath, efixes)
        stdout = subprocess.check_output(args=cmd, shell=True, stderr=subprocess.STDOUT)
        logging.debug('customization result is {}'.format(stdout))
        CHANGED = True
    except subprocess.CalledProcessError as exc:
        logging.warning('EXCEPTION cmd={} rc={} output={}'
                        .format(exc.cmd, exc.returncode, exc.output))
        stdout = exc.output
    output.update({'5.install': stdout.splitlines()})


@wait_threaded(THRDS)
def wait_all():
    """
    Do nothing
    """
    pass


@logged
def exec_cmd(cmd, output, exit_on_error=False, shell=False):
    """
    Execute the given command

    Note: If executed in thread, fail_json does not exit the parent

    args:
        cmd           (list or str): command with parameters
        output        (dict): result of the command to display in case of exception
        exit_on_error (bool): use fail_json if set and cmd failed
        shell         (bool): execute cmd through the shell if set (vulnerable to shell
                              injection when cmd is from user inputs). If cmd is a string
                              string, the string specifies the command to execute through
                              the shell. If cmd is a list, the first item specifies the
                              command, and other items are arguments to the shell itself.
    return:
        res      return code of the command
        stdout   command stdout
        errout   command stderr
    """
    global MODULE
    global CHANGED
    global WORKDIR
    res = 0
    stdout = ''
    errout = ''
    th_id = threading.current_thread().ident
    stderr_file = os.path.join(WORKDIR, 'cmd_stderr_{}'.format(th_id))

    try:
        myfile = open(stderr_file, 'w')
        stdout = subprocess.check_output(cmd, stderr=myfile, shell=shell)
        myfile.close()
        s = re.search(r'rc=([-\d]+)$', stdout)
        if s:
            res = int(s.group(1))
            stdout = re.sub(r'rc=[-\d]+\n$', '', stdout)  # remove the rc of c_rsh with echo $?

    except subprocess.CalledProcessError as exc:
        myfile.close()
        errout = re.sub(r'rc=[-\d]+\n$', '', exc.output)  # remove the rc of c_rsh with echo $?
        res = exc.returncode

    except OSError as exc:
        myfile.close
        errout = re.sub(r'rc=[-\d]+\n$', '', exc.args[1])  # remove the rc of c_rsh with echo $?
        res = exc.args[0]

    except IOError as exc:
        # generic exception
        myfile.close
        msg = 'Command: {} Exception: {}'.format(cmd, exc)
        MODULE.fail_json(changed=CHANGED, msg=msg, meta=output)

    # check for error message
    if os.path.getsize(stderr_file) > 0:
        myfile = open(stderr_file, 'r')
        errout += ''.join(myfile)
        myfile.close()
    os.remove(stderr_file)

    if res != 0 and exit_on_error is True:
        msg = 'Error executing command {} RetCode:{} ... stdout:{} stderr:{}'\
              .format(cmd, res, stdout, errout)
        MODULE.fail_json(changed=CHANGED, msg=msg, meta=output)

    return (res, stdout, errout)


def increase_fs(dest):
    """
    Increase filesystem by 100Mb
    """
    try:
        cmd = ['df', '-c', dest]
        stdout = subprocess.check_output(args=cmd, stderr=subprocess.STDOUT)
        mount_point = stdout.splitlines()[1].split(':')[6]
        cmd = ['chfs', '-a', 'size=+100M', mount_point]
        stdout = subprocess.check_output(args=cmd, stderr=subprocess.STDOUT)
        logging.debug('{}: {}'.format(mount_point, stdout))
    except subprocess.CalledProcessError as exc:
        logging.warning('EXCEPTION cmd={} rc={} output={}'
                        .format(exc.cmd, exc.returncode, exc.output))


###################################################################################################


if __name__ == '__main__':
    MODULE = AnsibleModule(
        argument_spec=dict(
            apar=dict(required=False, choices=['sec', 'hiper', 'all', None], default=None),
            filesets=dict(required=False, type='str'),
            csv=dict(required=False, type='str'),
            path=dict(required=False, type='str'),
            verbose=dict(required=False, type='bool', default=False),
            force=dict(required=False, type='bool', default=False),
            clean=dict(required=False, type='bool', default=False),
            check_only=dict(required=False, type='bool', default=False),
            download_only=dict(required=False, type='bool', default=False),
        ),
        supports_check_mode=True
    )

    CHANGED = False

    # Logging
    LOGNAME = '/var/adm/ansible/flrtvc_debug.log'
    LOGFRMT = '[%(asctime)s] %(levelname)s: [%(funcName)s:%(thread)d] %(message)s'
    logging.basicConfig(filename=LOGNAME, format=LOGFRMT, level=logging.DEBUG)

    logging.debug('*** START ***')

    # ===========================================
    # Get module params
    # ===========================================
    logging.debug('*** INIT ***')
    FLRTVC_PARAMS = {'apar_type': MODULE.params['apar'],
                     'apar_csv': MODULE.params['csv'],
                     'filesets': MODULE.params['filesets'],
                     'dst_path': MODULE.params['path'],
                     'verbose': MODULE.params['verbose']}
    FORCE = MODULE.params['force']
    CLEAN = MODULE.params['clean']
    CHECK_ONLY = MODULE.params['check_only']
    DOWNLOAD_ONLY = MODULE.params['download_only']

    if (FLRTVC_PARAMS['dst_path'] is None) or (not FLRTVC_PARAMS['dst_path'].strip()):
        FLRTVC_PARAMS['dst_path'] = '/var/adm/ansible'
    WORKDIR = os.path.join(FLRTVC_PARAMS['dst_path'], 'work')

    if not os.path.exists(WORKDIR):
        # not sure why flake8 complains against 'mode=0744' token in os.makedirs call
        os.makedirs(WORKDIR, mode=0744)  # noqa: E999

    # metadata
    OUTPUT = {}
    OUTPUT = {'messages': []}  # first time init

    # ===========================================
    # Install flrtvc script
    # ===========================================
    logging.debug('*** INSTALL ***')
    _FLRTVCPATH = os.path.abspath(os.path.join(os.sep, 'usr', 'bin'))
    _FLRTVCFILE = os.path.join(_FLRTVCPATH, 'flrtvc.ksh')
    if not os.path.exists(_FLRTVCFILE):
        _DESTNAME = os.path.abspath(os.path.join(os.sep, 'FLRTVC-latest.zip'))
        download('https://www-304.ibm.com/webapp/set2/sas/f/flrt3/FLRTVC-latest.zip', _DESTNAME)
        unzip(_DESTNAME, os.path.abspath(os.path.join(os.sep, 'usr', 'bin')))
    _STAT = os.stat(_FLRTVCFILE)
    if not _STAT.st_mode & stat.S_IEXEC:
        os.chmod(_FLRTVCFILE, _STAT.st_mode | stat.S_IEXEC)

    # ===========================================
    # Run flrtvc script
    # ===========================================
    logging.debug('*** REPORT ***')
    rc = run_flrtvc(OUTPUT, FLRTVC_PARAMS, FORCE)
    wait_all()
    if rc == 1:
        msg = 'Error: system will not be updated (flrtvc report failed)'
        logging.warning(msg)
        OUTPUT['messages'].append(msg)
    if CHECK_ONLY:
        if CLEAN and os.path.exists(WORKDIR):
            shutil.rmtree(WORKDIR, ignore_errors=True)
        MODULE.exit_json(changed=CHANGED, msg='exit on check only', meta=OUTPUT)

    # ===========================================
    # Parse flrtvc report
    # ===========================================
    logging.debug('*** PARSE ***')
    run_parser(OUTPUT, OUTPUT['0.report'])
    wait_all()

    # ===========================================
    # Download and check efixes
    # ===========================================
    logging.debug('*** DOWNLOAD ***')
    run_downloader(OUTPUT, OUTPUT['1.parse'])
    wait_all()

    if DOWNLOAD_ONLY:
        if CLEAN and os.path.exists(WORKDIR):
            shutil.rmtree(WORKDIR, ignore_errors=True)
        MODULE.exit_json(changed=CHANGED, msg='exit on download only', meta=OUTPUT)

    # ===========================================
    # Install efixes
    # ===========================================
    logging.debug('*** UPDATE ***')
    run_installer(OUTPUT, OUTPUT['4.2.check'])
    wait_all()

    if CLEAN and os.path.exists(WORKDIR):
        shutil.rmtree(WORKDIR, ignore_errors=True)

    MODULE.exit_json(
        changed=CHANGED,
        msg='FLRTVC completed successfully',
        meta=OUTPUT)
