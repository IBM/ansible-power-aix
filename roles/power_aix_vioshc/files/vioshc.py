#!/usr/bin/python
#
# Copyright 2017, International Business Machines Corporation
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

###############################################################################

from datetime import datetime
import os
import sys
import getopt
import subprocess
import threading
import re
import pycurl
import xml.etree.cElementTree as ET
import socket
import cStringIO
import shutil

# TODO: Use Standard logger instead of log routine

###############################################################################
# Initialize variables
###############################################################################
# Constants
LOG_DIR = "/tmp"
C_RSH = "/usr/lpp/bos.sysmgt/nim/methods/c_rsh"

action = ""     # (user provided -l present?)
list_arg = ""   # (user provided -l)

# Target HMC
hmc_ip = ""         # (user provided)
hmc_user_id = ""    # (user provided -u or retrieved)
hmc_password = ""   # (user provided -p or retrieved)
hmc_info = {}

managed_system_info = {}

# Dual VIOS pair
vios_info = {}
vios1_name = ""
vios2_name = ""
vios_num = 0        # number of VIOS UUID provided (-U option)
vios1_uuid = ""     # (user provided -U)
vios2_uuid = ""     # (user provided -U)
managed_system_uuid = ""    # (user provided -m)

lpar_info = {}

# Flags & Counters used by program
rc = 0
verbose = 0         # (user provided -v)
num_hc_fail = 0
num_hc_pass = 0
total_hc = 0


###############################################################################
# Define functions
###############################################################################
# File manipulation functions #

def touch(path):
    """
    Create file

    Input: (str) file path
    Output: none
    """
    log("creating file: {0}\n".format(path))
    try:
        open(path, 'a')
    except IOError as e:
        write('ERROR: Failed to create file {0}: {1}.'
              .format(path, e.strerror), lvl=0)
        sys.exit(3)
    os.utime(path, None)


def log(txt, debug='no'):
    """
    Write debug trace in the log file

    Input: (str) text to write
    Input: (str) level of the trace, writes if set to 'debug'
    Output: none
    """
    global log_file
    global mode
    if mode == 'debug' or mode == debug:
        log_file.write(txt)


def write(txt, lvl=1):
    """
    Write provided text on stdout and in log file depneding of the level

    Input: (str) text to write
    Input: (int) level, if 0 then prints out, used for: ERROR, WARNING, etc.
                          >0, verbose needs to be greater than lvl to see it
    Output: none
    """
    global verbose
    log(txt + '\n')
    if verbose >= lvl:
        print(txt)


def remove(path):
    """
    Remove file

    Input: (str) file path
    Output: none
    """
    try:
        if os.path.exists(path):
            os.remove(path)
        else:
            log('file {0} does not exists.\n'.format(path))
    except OSError as e:
        write('ERROR: Failed to remove file {0}: {1}.'.format(path, e.strerror), lvl=0)


def format_xml_file(filename):
    """
    Remove extra headers from top of XML file

    Input: (str) file name
    Output: none
    """
    try:
        f = open(filename, 'r+')
    except IOError as e:
        write('ERROR: Failed to create file {0}: {1}.'.format(filename, e.strerror), lvl=0)
        sys.exit(3)
    lines = f.readlines()
    f.seek(0)
    start_writing = False
    for i in lines:
        if i[0] == '<':
            start_writing = True
        if start_writing:
            f.write(i)
    f.truncate()
    f.close()


def exec_cmd(cmd):
    """
    Execute the given command

    Input: (str) return code of command
    Output:(int) stdout of the command
    Output:(str) stderr of the command
    """
    global log_dir
    rc = 0
    output = ''
    errout = ''
    th_id = threading.current_thread().ident
    stderr_file = os.path.join(log_dir, 'cmd_stderr_{0}'.format(th_id))
    try:
        myfile = open(stderr_file, 'w')
        output = subprocess.check_output(cmd, stderr=myfile)
        myfile.close()
        s = re.search(r'rc=([-\d]+)$', output)
        if s:
            rc = int(s.group(1))
            output = re.sub(r'rc=[-\d]+\n$', '', output)  # remove the rc of c_rsh with echo $?

    except subprocess.CalledProcessError as exc:
        myfile.close()
        errout = re.sub(r'rc=[-\d]+\n$', '', exc.output)  # remove the rc of c_rsh with echo $?
        rc = exc.returncode
        write('Command: {0} failed: {1}'.format(cmd, exc.args), lvl=0)

    except (OSError, IOError) as exc:
        myfile.close
        if exc.args:
            match = re.match(r'rc=[-\d]+\n$', exc.args[1])
            if match:
                errout = re.sub(r'rc=[-\d]+\n$', '', exc.args[1])  # remove the rc of c_rsh with echo $?
                rc = exc.args[0]
            else:
                rc = 1
                write('Command: {0} failed, exception: {1}'.format(cmd, exc), lvl=0)
        else:
            rc = 1
            write('Command: {0} failed, exception: {1}'.format(cmd, exc), lvl=0)

    except Exception as exc:
        rc = 1
        write('Command: {0} failed, exception: {1}'.format(cmd, exc.args), lvl=0)

    # check for error message
    if os.path.getsize(stderr_file) > 0:
        myfile = open(stderr_file, 'r')
        errout += ''.join(myfile)
        myfile.close()
    os.remove(stderr_file)

    log('command {0} returned:\n'.format(cmd))
    log(' rc:{0}\n'.format(rc))
    log(' stdout:{0}\n'.format(output))
    log(' stderr:{0}\n'.format(errout))
    return (rc, output, errout)


###############################################################################
# Interfacing functions
###############################################################################

def retrieve_usr_pass(hmc_info):
    """
    Retrieve the username and password

    Input: (str) hmc internet address
    Output:(str) username
    Output:(str) password
    """
    if hmc_info is None or 'type' not in hmc_info or 'passwd_file' not in hmc_info:
        write('ERROR: Failed to retrieve user ID and password for {0}'
              .format(hmc_info['hostname']), lvl=0)
        return ("", "")

    decrypt_file = get_decrypt_file(hmc_info['passwd_file'],
                                    hmc_info['type'],
                                    hmc_info['hostname'])
    if decrypt_file != '':
        (user, passwd) = get_usr_passwd(decrypt_file)
    return (user, passwd)


def get_nim_info(obj_name):
    """
    Get detailed on the provided Network Installation Management (NIM) object

    Input: (str) NIM object name to look for
    Output:(str) hash with NIM info, the associated value can be a list
    """
    info = {0}

    cmd = ['/usr/sbin/lsnim', '-l', obj_name]
    (rc, output, errout) = exec_cmd(cmd)
    if rc != 0:
        write('ERROR: Failed to get {0} NIM info: {1} {2}'.format(obj_name, output, errout), lvl=0)
        return None

    for line in output.split('\n'):
        match = re.match(r'^\s*(\S+)\s*=\s*(\S+)\s*$', line)
        if match:
            if match.group(1) not in info:
                info[match.group(1)] = match.group(2)
            elif type(info[match.group(1)]) is list:
                info[match.group(1)].append(match.group(2))
            else:
                info[match.group(1)] = [info[match.group(1)]]
                info[match.group(1)].append(match.group(2))
    return info


def get_nim_name(hostname):
    """
    Get NIM client name associated with the given hostname

    Input: (str) hostname of the NIM client to look for
    Output:(str) NIM object name
    """
    name = ""

    cmd = ['lsnim', '-a', 'if1']
    (rc, output, errout) = exec_cmd(cmd)
    if rc != 0:
        write('ERROR: Failed to get NIM name for {0}: {1} {2}'
              .format(hostname, output, errout), lvl=0)
        return ""

    for line in output.split('\n'):
        match = re.match(r'^\s*(\S+)\s*:\s*$', line)
        if match:
            name = match.group(1)
            continue
        match = re.match(r'^\s*if1\s*=\s*\S+\s+(\S+).*$', line)
        if match and match.group(1) != hostname:
            name = ""
            continue
        else:
            break
    if name == "":
        write('ERROR: Failed to get NIM name for {0}: Not Found'
              .format(hostname), lvl=0)
    return name


def get_hostname(host):
    """
    Get network information from either IP address or hostname

    Input: (str) IP address or hostname
    Output:      a triple (hostname, aliaslist, ipaddrlist)
                 with
                 - hostname:   primary host name responding to the given ip_address
                 - aliaslist:  list of alternative host names for the same address (can be empty)
                 - ipaddrlist: list of IPv4 addresses for the same interface on the same host
    """
    try:
        match_key = re.match(r'^\d+.*$', host)
        if match_key:
            return socket.gethostbyaddr(host)
        else:
            return socket.gethostbyname_ex(host)
    except OSError as e:
        write("ERROR: Failed to get hostname for %s: %d %s." % (host, e.errno, e.strerror), lvl=0)
        sys.exit(3)


def get_decrypt_file(passwd_file, type, hostname):
    """
    Decrypt the encrypted password file

    Input: (str) password file
    Input: (str) managed type
    Input: (str) managed hostname
    Output:(str) decrypted file
    """
    log("getting decrypt file: {0} for {1} {2}\n".format(passwd_file, type, hostname))

    cmd = ["/usr/bin/dkeyexch", "-f", passwd_file, "-I", type, "-H", hostname, "-S"]
    (rc, output, errout) = exec_cmd(cmd)
    if rc != 0:
        write("ERROR: Failed to get the encrypted password file path for {0}: {1} {2}"
              .format(hostname, output, errout), lvl=0)
        return ""

    # dkeyexch output is like:
    # OpenSSH_6.0p1, OpenSSL 1.0.2h  3 May 2016
    # /var/ibm/sysmgt/dsm/tmp/dsm1608597933307771402.tmp
    return output.rstrip().split('\n')[1]


def get_usr_passwd(decrypt_file):
    """
    Read the decrypted file and returns the username and password

    Input: (str) decrypted file
    Output:(str) username
    Output:(str) password
    """
    try:
        f = open(decrypt_file, 'r')
    except IOError as e:
        write("ERROR: Failed to open file {0}: {1}.".format(decrypt_file, e.strerror), lvl=0)
        sys.exit(3)
    arr = f.read().split(' ')
    f.close()
    return arr


# TODO: change the xml parsing in build_managed_system?
def build_managed_system(hmc_info, vios_info, managed_system_info, xml_file):
    """
    Retrieve managed systems, VIOS UUIDs and machine SerialNumber information
    from provided XML file.

    Input: (dict) hmc_info hash
    Input:  (str) xml_file of managed systems to parse
    Output:(dict) VIOSes information
    Output:(dict) managed systems and their SerialNumbers and VIOSes
    """
    curr_managed_sys = ""  # string to hold current managed system being searched
    vios_num = 0

    log("Parse xml file: {0}\n".format(xml_file))
    try:
        tree = ET.ElementTree(file=xml_file)
    except IOError as e:
        write("ERROR: Failed to parse '{0}' file.".format(xml_file), lvl=0)
        sys.exit(3)
    except ET.ParseError as e:
        write("ERROR: Failed to parse '{0}' file.".format(xml_file), lvl=0)
        sys.exit(3)

    log("Get managed system serial numbers\n")
    iter_ = tree.getiterator()
    for elem in iter_:
        # Retrieving the current Managed System
        if re.sub(r'{[^>]*}', "", elem.tag) == "entry":
            elem_child = elem.getchildren()
            for child in elem_child:
                if re.sub(r'{[^>]*}', "", child.tag) != "id":
                    continue
                if child.text in managed_system_info:
                    continue
                curr_managed_sys = child.text
                log("get managed system UUID: {0}\n".format(curr_managed_sys))
                managed_system_info[curr_managed_sys] = {}
                managed_system_info[curr_managed_sys]['serial'] = "Not Found"
                managed_system_info[curr_managed_sys]['vios'] = []

        if re.sub(r'{[^>]*}', "", elem.tag) == "MachineTypeModelAndSerialNumber":
            # string to append to the managed system dict
            serial_string = ""
            elem_child = elem.getchildren()
            for serial_child in elem_child:
                if re.sub(r'{[^>]*}', "", serial_child.tag) == "MachineType":
                    serial_string += serial_child.text + "-"
                if re.sub(r'{[^>]*}', "", serial_child.tag) == "Model":
                    serial_string += serial_child.text + "*"
                if re.sub(r'{[^>]*}', "", serial_child.tag) == "SerialNumber":
                    serial_string += serial_child.text
            # Adding the serial to the current Managed System
            managed_system_info[curr_managed_sys]['serial'] = serial_string

        if re.sub(r'{[^>]*}', "", elem.tag) == "AssociatedVirtualIOServers":
            write("Retrieving the VIOS UUIDs", lvl=2)
            elem_child = elem.getchildren()

            # The VIOS UUIDs are in the "link" attribute
            for child in elem_child:
                if re.sub(r'{[^>]*}', "", child.tag) != "link":
                    continue
                match = re.match(r'^.*VirtualIOServer\/(\S+)$', child.attrib['href'])
                if match:
                    uuid = match.group(1)
                    vios_num += 1

                    write("Collect info on clients of VIOS{0}: {1}".format(vios_num, uuid), lvl=2)
                    filename = "{0}/vios{1}.xml".format(xml_dir, vios_num)
                    rc = get_vios_info(hmc_info, uuid, filename)
                    if rc != 0:
                        write("WARNING: Failed to collect vios {0} info: {1}"
                              .format(uuid, rc[1]), lvl=1)
                        continue

                    vios_name = build_vios_info(vios_info, filename, uuid)
                    if vios_name == "":
                        continue

                    vios_info[vios_name]['managed_system'] = curr_managed_sys
                    vios_info[vios_name]['filename'] = filename
                    for key in vios_info[vios_name].keys():
                        log("vios_info[{0}][{1}] = {2}\n"
                            .format(vios_name, key, vios_info[vios_name][key]))

                    managed_system_info[curr_managed_sys]['vios'].append(vios_name)

    for ms in managed_system_info.keys():
        for key in managed_system_info[ms].keys():
            log("managed_system_info[{0}][{1}]: {2}\n".format(ms, key, managed_system_info[ms][key]))

    return 0


def get_session_key(hmc_info, filename):
    """
    Get a session key from the HMC with a Curl request

    Input: (dict) hmc_info hash with HMC IP address, user ID, password
    Inputs: (str) file name to write the HMC answer
    Output: (str) session key
    """
    s_key = ""
    try:
        f = open(filename, 'wb')
    except IOError as e:
        write("ERROR: Failed to create file {0}: {1}.".format(filename, e.strerror), lvl=0)
        sys.exit(3)

    url = "https://{0}:12443/rest/api/web/Logon".format(hmc_info['hostname'])
    fields = '<LogonRequest schemaVersion=\"V1_0\" '\
             'xmlns=\"http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/\"  '\
             'xmlns:mc=\"http://www.ibm.com/xmlns/systems/power/firmware/web/mc/2012_10/\"> '\
             '<UserID>{0}</UserID>'\
             .format(hmc_info['user_id'])

    log("curl request on: {0}\n".format(url))
    log("curl request fields: {0} <Password>xxx</Password></LogonRequest>\n".format(fields))
    fields += ' <Password>{0}</Password></LogonRequest>'\
              .format(hmc_info['user_password'])
    hdrs = ['Content-Type: application/vnd.ibm.powervm.web+xml; type=LogonRequest']

    try:
        c = pycurl.Curl()
        c.setopt(c.HTTPHEADER, hdrs)
        c.setopt(c.CUSTOMREQUEST, "PUT")
        c.setopt(c.POST, 1)
        c.setopt(c.POSTFIELDS, fields)
        c.setopt(c.URL, url)
        c.setopt(c.SSL_VERIFYPEER, False)
        c.setopt(c.WRITEDATA, f)
        c.perform()
    except pycurl.error as e:
        write("ERROR: Curl request failed: {0}".format(e), lvl=0)
        return ""

    # Reopen the file in text mode
    f.close()
    try:
        f = open(filename, 'r')
    except IOError as e:
        write("ERROR: Failed to create file {0}: {1}.".format(filename, e.strerror), lvl=0)
        sys.exit(3)

    # Isolate session key
    for line in f:
        if re.search('<X-API-Session', line):
            s_key = re.sub(r'<[^>]*>', "", line)

    return s_key.strip()


def print_uuid(managed_system_info, vios_info, arg):
    """
    Print out managed system and VIOS UUIDs

    Input:(dict) HMC info to get: IP address, session key
    Input: (str) set arg flag to 'a' to print VIOS information
    Output:(int) 0 for success, !0 otherwise
    """
    write("\n%-37s    %-22s" % ("Managed Systems UUIDs", "Serial"), lvl=0)
    write("-" * 37 + "    " + "-" * 22, 0)
    for key in managed_system_info.keys():
        write("%-37s    %-22s" % (key, managed_system_info[key]['serial']), lvl=0)

        if arg == 'a':
            write("\n\t%-37s    %-14s" % ("VIOS", "Partition ID"), lvl=0)
            write("\t" + "-" * 37 + "    " + "-" * 14, lvl=0)
            for vios in managed_system_info[key]['vios']:
                write("\t%-37s    %-14s" % (vios_info[vios]['uuid'], vios_info[vios]['id']), lvl=0)
            write("", lvl=0)
    write("", lvl=0)

    return 0

###############################################################################
# Parsing functions
###############################################################################


def grep(filename, tag):
    """
    Parse through xml to find tag value

    Inputs: (str) XML file name to parse
    Inputs: (str) tag to look for
    Output: (str) value
    """
    format_xml_file(filename)
    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' tag.\n".format(filename, tag))
        return ""
    except ET.ParseError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' tag.\n".format(filename, tag))
        return ""

    iter_ = tree.getiterator()
    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == tag:
            return elem.text
    return ""


def grep_array(filename, tag):
    """
    Parse through xml file to create list of tag values

    Inputs: (str)   XML file name to parse
    Inputs: (str)   tag to look for
    Output: (array) values corresponding to given tag
    """
    format_xml_file(filename)
    arr = []
    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' tag.\n".format(filename, tag))
        return arr
    except ET.ParseError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' tag.\n".format(filename, tag))
        return arr
    iter_ = tree.getiterator()
    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == tag:
            arr.append(elem.text)
    return arr


def grep_check(filename, tag):
    """
    Check for existence of tag in file

    Inputs: (str)  XML file name to parse
    Inputs: (str)  tag to look for
    Output: (bool) True if the tag is present
    Output: True if tag exists, False otherwise
    """

    # format_xml_file(filename)
    found = False
    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' tag.\n".format(filename, tag))
        return found
    except ET.ParseError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' tag.\n".format(filename, tag))
        return found
    iter_ = tree.getiterator()
    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == tag:
            found = True
    return found


def awk(filename, tag1, tag2):
    """
    Parse through specific sections of xml file to create a list of tag values

    Inputs: (str)  XML file name to parse
    Inputs: (str)  outer tag
    Inputs: (str)  inner tag
    Output:(array) values corresponding to given tags
    """
    arr = []
    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' and '{2}' tags.\n"
            .format(filename, tag1, tag2))
        return arr
    except ET.ParseError as e:
        log("WARNING: Failed to parse '{0}' to find '{1}' and '{2}' tags.\n"
            .format(filename, tag1, tag2))
        return arr
    iter_ = tree.getiterator()
    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == tag1:
            elem_child = elem.getchildren()
            for child in elem_child:
                if re.sub(r'{[^>]*}', "", child.tag) == tag2:
                    arr.append(child.text)
    return arr


def build_vios_info(vios_info, filename, vios_uuid):
    """
    Parse VirtualIOServer XML file to build the vios_info hash

    Input:(dict) VIOS info to fill
    Input: (str) XML file name
    Input: (str) VIOS uuid to look for
    Output:(str) VIOS name use in dictionary if success,
           prints error message and exits upon error
    """
    ns = {'Atom': 'http://www.w3.org/2005/Atom',
          'vios': 'http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/'}
    try:
        e_tree = ET.parse(filename)
    except IOError as e:
        write("ERROR: Failed to parse {0} for {1}: {2}."
              .format(filename, vios_uuid, e), lvl=0)
        sys.exit(3)
    except ET.ParseError as e:
        write("ERROR: Failed to parse {0} for {1}: {2}".format(filename, vios_uuid, e), lvl=0)
        sys.exit(3)
    e_root = e_tree.getroot()

    # NOTE: Some VIOSes do not return PartitionName element
    #       so in that case we use the short hostname as hash
    #       key and replace partition name by this short hostname

    # Get element: ResourceMonitoringIPAddress
    e_RMIPAddress = e_root.find(
        "Atom:content/vios:VirtualIOServer/vios:ResourceMonitoringIPAddress",
        ns)
    if e_RMIPAddress is None:
        write("WARNING: ResourceMonitoringIPAddress element not found in file {0} for {1}"
              .format(filename, vios_uuid), lvl=1)
        return ""
        # sys.exit(3)

    # Get the hostname
    (hostname, aliases, ip_list) = get_hostname(e_RMIPAddress.text)
    vios_name = hostname.split(".")[0]

    vios_info[vios_name] = {}
    vios_info[vios_name]['uuid'] = vios_uuid
    vios_info[vios_name]['hostname'] = hostname
    vios_info[vios_name]['ip'] = e_RMIPAddress.text

    # Get element: PartitionName
    e_PartionName = e_root.find("Atom:content/vios:VirtualIOServer/vios:PartitionName", ns)
    if e_PartionName is None:
        write("ERROR: PartitionName element not found in file {0}".format(filename), lvl=0)
        del vios_info[vios_name]
        return ""
        # sys.exit(3)
    else:
        vios_info[vios_name]['partition_name'] = e_PartionName.text

    # Get element: PartitionID
    e_PartionID = e_root.find("Atom:content/vios:VirtualIOServer/vios:PartitionID", ns)
    if e_PartionID is None:
        write("ERROR: PartitionID element not found in file {0}".format(filename), lvl=0)
        del vios_info[vios_name]
        return ""
        # sys.exit(3)
    else:
        vios_info[vios_name]['id'] = e_PartionID.text

    # Get element: PartitionState
    e_PartitionState = e_root.find("Atom:content/vios:VirtualIOServer/vios:PartitionState", ns)
    if e_PartitionState is None:
        write("ERROR: PartitionState element not found in file {0}".format(filename), lvl=0)
        vios_info[vios_name]['partition_state'] = "none"
        # sys.exit(3)
    else:
        vios_info[vios_name]['partition_state'] = e_PartitionState.text

    # Get element: ResourceMonitoringControlState
    e_RMCState = e_root.find(
        "Atom:content/vios:VirtualIOServer/vios:ResourceMonitoringControlState",
        ns)
    if e_RMCState is None:
        write("ERROR: ResourceMonitoringControlState element not found in file {0}"
              .format(filename), lvl=0)
        vios_info[vios_name]['control_state'] = e_RMCState.text
        # sys.exit(3)
    else:
        vios_info[vios_name]['control_state'] = "none"

    return vios_name


def build_lpar_info(lpar_info, filename):
    """
    Parse the XML file to build the lpar_info hash. Retrieves partition ID

    Input:(dict) LPAR info to fill
    Input: (str) XML file name
    Output:(int) 0 if success,
           prints error message and exits upon error
    """
    ns = {'Atom': 'http://www.w3.org/2005/Atom',
          'lpar': 'http://www.ibm.com/xmlns/systems/power/firmware/uom/mc/2012_10/'}
    try:
        e_tree = ET.parse(filename)
    except IOError as e:
        write("ERROR: Failed to parse {0}: {1}.".format(filename, e.strerror), lvl=0)
        sys.exit(3)
    except ET.ParseError as e:
        write("ERROR: Failed to parse {0}: {1}".format(filename, e), lvl=0)
        sys.exit(3)
    e_root = e_tree.getroot()

    # Get partitions UUID: element: id
    e_Partitions = e_root.findall("Atom:entry", ns)
    if e_Partitions is None:
        write("ERROR: Cannot get entry element in file {0}".format(filename), lvl=0)
        sys.exit(3)
    elif len(e_Partitions) == 0:
        write("No partion found in file {0}".format(filename), lvl=1)
        return 0

    for e_Partition in e_Partitions:
        # Get element: PartitionID
        e_PartitionID = e_Partition.find("Atom:content/lpar:LogicalPartition/lpar:PartitionID", ns)
        if e_PartitionID is None:
            write("ERROR: PartitionID element not found in file {0}".format(filename), lvl=0)
            sys.exit(3)
        lpar_info[e_PartitionID.text] = {}

        e_PartitionUUID = e_Partition.find("Atom:id", ns)
        if e_PartitionUUID is None:
            write("ERROR: id element of PartitionID:{0} entry not found in file {1}"
                  .format(e_PartitionID.text, filename), lvl=0)
            sys.exit(3)
        lpar_info[e_PartitionID.text]['uuid'] = e_PartitionUUID.text

        # Get element: PartitionName
        e_PartionName = e_Partition.find("Atom:content/lpar:LogicalPartition/lpar:PartitionName",
                                         ns)
        if e_PartionName is None:
            write("ERROR: PartitionName element of PartitionID={0} not found in file {1}"
                  .format(e_PartitionID.text, filename), lvl=0)
            sys.exit(3)
        lpar_info[e_PartitionID.text]['name'] = e_PartionName.text

    return 0


###############################################################################
# c_rsh functions
###############################################################################


def get_vios_sea_state(vios_name, sea_device):
    """
    Parse an XML file to get the SEA device state

    Input:(dict) LPAR info to fill
    Input: (str) VIOS name
    Input: (str) SEA device name
    Output:(int) 0 if success
    Output:(str) SEA device state,
           prints error message and exits upon error
    """
    global vios_info
    global xml_dir

    state = ""

    # file to get all SEA info (debug)
    filename = "{0}/{1}_{2}.txt".format(xml_dir, vios_name, sea_device)
    try:
        f = open(filename, 'w+')
    except IOError as e:
        write("ERROR: Failed to create file {0}: {1}.".format(filename, e.strerror), lvl=0)
        f = None

    # ssh into vios1
    cmd = [C_RSH, vios_info[vios_name]['hostname'],
           "LC_ALL=C /bin/entstat -d {0}; echo rc=$?".format(sea_device)]
    log("SharedEthernetAdapter cmd='{0}'\n".format(cmd))
    (rc, output, errout) = exec_cmd(cmd)
    if rc != 0:
        write("ERROR: Failed to get the state of the {0} SEA adapter on {1}: {2} {3}"
              .format(sea_device, vios_name, output, errout), lvl=0)
        return (1, "")

    found_stat = False
    found_packet = False
    for line in output.rstrip().split('\n'):
        # file to get all SEA info (for debug)
        if not (f is None):
            f.write("{0}\n".format(line))

        if not found_stat:
            # Statistics for adapters in the Shared Ethernet Adapter entX
            match_key = re.match(r"^Statistics for adapters in the Shared Ethernet Adapter {0}"
                                 .format(sea_device), line)
            if match_key:
                found_stat = True
                continue

        if not found_packet:
            # Type of Packets Received:
            match_key = re.match(r"^Type of Packets Received(.*)$", line)
            if match_key:
                found_packet = True
                continue

        if found_packet:
            # State: PRIMARY | BACKUP | STANDBY | ......
            match_key = re.match(r"^\s+State:\s+(.*)$", line)
            if match_key:
                state = match_key.group(1)
                found_stat = False
                found_packet = False
                continue

    if state == "":
        write("ERROR: Failed to get the state of the {0} SEA adapter on {1}: State field not found."
              .format(sea_device, vios_name), lvl=0)
        return (1, "")

    log("VIOS {0} sea adapter {1} is in {2} state".format(vios_name, sea_device, state))
    return (0, state)


def get_vscsi_mapping(vios_name, vios_uuid):
    """
    Build vios_scsi_mapping dictionnary
    from an XML file: <vios_name>_vscsi_mapping.xml

    vios_scsi_mapping[UDID] = device_mapping dictionnary
        device_mapping["Backing_device_Name"] = Backing_device_Name
        device_mapping["Backing_device_Type"] = device_type
        device_mapping["Reserve_policy"] = ReservePolicy
        device_mapping["RemoteLParIDs"] = [] contains the list of client partition IDs

    print device mapping table

    Input:  (str) vios name
    Input:  (str) vios UUID
    Output:(dict) vios_scsi_mapping dictionnary
    """
    global filename_msg
    global hmc_info
    global xml_dir
    touch(filename_msg)

    write("\nRecovering vSCSI mapping for {0}:".format(vios_name), 2)
    filename = "{0}/{1}_vscsi_mapping.xml".format(xml_dir, vios_name)
    # Get vSCSI info, write data to file
    url = "https://{0}:12443/rest/api/uom/VirtualIOServer/{1}?group=ViosSCSIMapping"\
          .format(hmc_info['hostname'], vios_uuid)
    curl_request(hmc_info['session_key'], url, filename)

    # Check for error response in file
    if grep_check(filename, 'HttpErrorResponse'):
        write("ERROR: Request to {0} returned Error Response.".format(url), lvl=0)
        write("ERROR: Unable to detect vSCSI Information", lvl=0)

    # Parse for backup device info
    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        write("ERROR: Failed to parse {0}: {1}.".format(filename, e.strerror), lvl=0)
        sys.exit(2)
    except ET.ParseError as e:
        write("ERROR: Failed to parse {0}: {1}".format(filename, e), lvl=0)
        sys.exit(2)
    iter_ = tree.getiterator()
    device_target_mapping = {}
    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == 'ServerAdapter':
            backing_device_name = ""
            remote_logical_partition_id = ""
            elem_child = elem.getchildren()
            for child in elem_child:
                if re.sub(r'{[^>]*}', "", child.tag) == 'BackingDeviceName':
                    backing_device_name = re.sub(r'<[^>]*>', "", child.text)
                if re.sub(r'{[^>]*}', "", child.tag) == 'RemoteLogicalPartitionID':
                    remote_logical_partition_id = re.sub(r'<[^>]*>', "", child.text)
            if backing_device_name not in device_target_mapping:
                device_target_mapping[backing_device_name] = []
            device_target_mapping[backing_device_name].append(remote_logical_partition_id)

    for dev in device_target_mapping:
        device_target_mapping[dev].sort()

    vios_scsi_mapping = {}
    for elem in iter_:
        backing_device_name = ""
        backing_device_type = ""
        UDID = ""
        reserve_policy = ""
        if re.sub(r'{[^>]*}', "", elem.tag) == 'Storage':
            elem_child = elem.getchildren()
            for child in elem_child:
                str_tag = re.sub(r'{[^>]*}', "", child.tag)

                if str_tag == 'PhysicalVolume':
                    backing_device_type = "PhysicalVolume"
                if str_tag == 'LogicalUnit':
                    backing_device_type = "ssp"
                if str_tag == 'VirtualDisk':
                    backing_device_type = "LogicalVolume"
                if str_tag == "PhysicalVolume" or\
                   str_tag == "LogicalUnit" or str_tag == "VirtualDisk":
                    sub_children = child.getchildren()
                    for kid in sub_children:
                        if re.sub(r'{[^>]*}', "", kid.tag) == 'VolumeName':
                            backing_device_name = re.sub(r'<[^>]*>', "", kid.text)
                        if re.sub(r'{[^>]*}', "", kid.tag) == 'UnitName':
                            backing_device_name = re.sub(r'<[^>]*>', "", kid.text)
                        if re.sub(r'{[^>]*}', "", kid.tag) == 'DiskName':
                            backing_device_name = re.sub(r'<[^>]*>', "", kid.text)
                        if re.sub(r'{[^>]*}', "", kid.tag) == 'ReservePolicy':
                            reserve_policy = re.sub(r'<[^>]*>', "", kid.text)
                        if re.sub(r'{[^>]*}', "", kid.tag) == 'UniqueDeviceID':
                            UDID = re.sub(r'<[^>]*>', "", kid.text)
                else:
                    continue

            vios_scsi_mapping[UDID] = {}
            vios_scsi_mapping[UDID]["BackingDeviceName"] = backing_device_name
            vios_scsi_mapping[UDID]["BackingDeviceType"] = backing_device_type
            vios_scsi_mapping[UDID]["ReservePolicy"] = reserve_policy
            vios_scsi_mapping[UDID]["RemoteLParIDs"] = []
            if backing_device_name in device_target_mapping:
                vios_scsi_mapping[UDID]["RemoteLParIDs"] = \
                    device_target_mapping[backing_device_name]

    if len(vios_scsi_mapping) == 0:
        write("WARNING: no vSCSI disks configured on {0}.".format(vios_name), lvl=1)

    else:
        write("\nvSCSI mapping on {0}:".format(vios_name), lvl=1)
        vscsi_header = "Device Name     UDID                                             "\
                       "                        Disk Type       Reserve Policy    Client LPar ID"
        divider = "-----------------------------------------------------------------"\
                  "------------------------------------------------------------------------"
        format_string = "%-15s %-72s %-16s %-18s %-15s"
        write(vscsi_header, lvl=1)
        write(divider, lvl=1)

        msg_txt = open(filename_msg, 'w+')

        for udid in vios_scsi_mapping:
            write(format_string % (vios_scsi_mapping[udid]["BackingDeviceName"],
                  udid, vios_scsi_mapping[udid]["BackingDeviceType"],
                  vios_scsi_mapping[udid]["ReservePolicy"],
                  vios_scsi_mapping[udid]["RemoteLParIDs"]), lvl=1)
        for udid in vios_scsi_mapping:
            if vios_scsi_mapping[udid]["ReservePolicy"] == "SinglePath":
                msg = "WARNING: You have single path for {0} on VIOS {1} which is likely an issue"\
                      .format(vios_scsi_mapping[udid]["BackingDeviceName"], vios_name)
                write(msg, lvl=1)
                msg_txt.write(msg)
            elif vios_scsi_mapping[udid]["BackingDeviceType"] == "Other":
                msg = "WARNING: {0} is not supported by both VIOSes because it is of type {1}"\
                      .format(vios_scsi_mapping[udid]["BackingDeviceName"],
                              vios_scsi_mapping[udid]["BackingDeviceType"])
                write(msg, lvl=1)
                msg_txt.write(msg)
            elif vios_scsi_mapping[udid]["BackingDeviceType"] == "LogicalVolume":
                msg = "WARNING: This backing device: {0} is not accessible via both VIOSes"\
                      .format(vios_scsi_mapping[udid]["BackingDeviceName"])
                write(msg, lvl=1)
                msg_txt.write(msg)

    return vios_scsi_mapping


def build_fc_mapping(vios_name, vios_uuid, fc_mapping):
    """
    Build fc_mapping dictionnary
    from an XML file: <vios_name>__fc_mapping.xml

    fc_mapping[server_name] = {}
              [server_name][client_name] = {}
              [server_name][client_name]["VirtualSlotsNumber"] = local slot number
              [server_name][client_name]["ConnectingVirtualSlotsNumber"] = remote slot number

    Input:  (str) vios name
    Input:  (str) vios UUID
    Input: (dict) FC mapping to fill
    Output: none
    """
    global hmc_info
    global vios_info
    global lpar_info

    write("\nRecovering Fiber Chanel mapping for {0}:".format(vios_name), 2)
    filename = "{0}/{1}_fc_mapping.xml".format(xml_dir, vios_name)

    # build xml file using hmc curl reques
    url = "https://{0}:12443/rest/api/uom/VirtualIOServer/{1}?group=ViosFCMapping"\
          .format(hmc_info['hostname'], vios_uuid)
    curl_request(hmc_info['session_key'], url, filename)  # Check for error response in file
    if grep_check(filename, 'HttpErrorResponse'):
        write("ERROR: Request to {0} returned Error Response.".format(url), lvl=0)
        write("ERROR: Unable to detect vSCSI Information", lvl=0)

    # Analize xml file
    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        write("ERROR: Failed to parse {0}: {1}.".format(filename, e.strerror), lvl=0)
        sys.exit(2)
    except ET.ParseError as e:
        write("ERROR: Failed to parse {0}: {1}".format(filename, e), lvl=0)
        sys.exit(2)
    iter_ = tree.getiterator()

    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == 'ServerAdapter':
            LocalPartitionID = ''
            VirtualSlotNumber = ''
            ConnectingPartitionID = ''
            ConnectingVirtualSlotNumber = ''
            elem_child = elem.getchildren()
            for child in elem_child:
                if re.sub(r'{[^>]*}', '', child.tag) == 'LocalPartitionID':
                    LocalPartitionID = re.sub(r'<[^>]*>', "", child.text)
                if re.sub(r'{[^>]*}', '', child.tag) == 'VirtualSlotNumber':
                    VirtualSlotNumber = re.sub(r'<[^>]*>', "", child.text)
                if re.sub(r'{[^>]*}', "", child.tag) == 'ConnectingPartitionID':
                    ConnectingPartitionID = re.sub(r'<[^>]*>', "", child.text)
                if re.sub(r'{[^>]*}', "", child.tag) == 'ConnectingVirtualSlotNumber':
                    ConnectingVirtualSlotNumber = re.sub(r'<[^>]*>', "", child.text)
            if vios_info[vios_name]['id'] == LocalPartitionID:
                if ConnectingPartitionID in lpar_info:
                    lpar_name = lpar_info[ConnectingPartitionID]["name"]
                else:
                    lpar_name = ConnectingPartitionID
                fc_mapping[vios_name] = {}
                fc_mapping[vios_name][lpar_name] = {}
                fc_mapping[vios_name][lpar_name]['VirtualSlotNumber'] = VirtualSlotNumber
                fc_mapping[vios_name][lpar_name]['ConnectingVirtualSlotNumber'] = \
                    ConnectingVirtualSlotNumber


def build_sea_config(vios_name, vios_uuid, sea_config):
    """
    Build sea_config dictionnary
    from an XML file: <vios_name>_network.xml

    sea_config[vios_name] = {}
              [vios_name][VLAN_IDs] = {}
              [vios_name][VLAN_IDs]["BackingDeviceName"] = "entx"
              [vios_name][VLAN_IDs]["BackingDeviceState"] = "Inactive/Disconnected/...."
              [vios_name][VLAN_IDs]["SEADeviceName"] = "entx"
              [vios_name][VLAN_IDs]["SEADeviceState"] = ""
              [vios_name][VLAN_IDs]["HighAvailabilityMode"] = "auto/sharing"
              [vios_name][VLAN_IDs]["Priority"] = priority

    Input:  (str) vios name
    Input:  (str) vios UUID
    Input: (dict) SEA config to fill
    Output: none
    """
    global hmc_info
    global vios_info
    global lpar_info

    write("\nRecovering SEA configuration for {0}:".format(vios_name), 2)

    sea_config[vios_name] = {}
    filename = "{0}/{1}_network.xml".format(xml_dir, vios_name)

    url = "https://{0}:12443/rest/api/uom/VirtualIOServer/{1}?group=ViosNetwork"\
          .format(hmc_info['hostname'], vios_uuid)
    curl_request(hmc_info['session_key'], url, filename)

    if grep_check(filename, 'HttpErrorResponse'):
        write("ERROR: Request to {0} returned Error Response."
              .format(url), lvl=0)
        write("ERROR: Unable to detect vSCSI Information", lvl=0)

    try:
        tree = ET.ElementTree(file=filename)
    except IOError as e:
        write("ERROR: Failed to parse {0}: {1}.".format(filename, e.strerror), lvl=0)
        sys.exit(2)
    except ET.ParseError as e:
        write("ERROR: Failed to parse {0}: {1}".format(filename, e), lvl=0)
        sys.exit(2)
    iter_ = tree.getiterator()

    for elem in iter_:
        if re.sub(r'{[^>]*}', "", elem.tag) == 'SharedEthernetAdapter':
            HighAvailabilityMode = ""
            VLANIDs = []
            VLAN_IDs = ""
            BackingDeviceName = "none"
            BackingDeviceState = "none"
            SEADeviceName = "none"
            Priority = ""
            elem_child = elem.getchildren()
            for child in elem_child:
                if re.sub(r'{[^>]*}', "", child.tag) == 'BackingDeviceChoice':
                    sub_child = child.getchildren()
                    for child in sub_child:
                        if re.sub(r'{[^>]*}', "", child.tag) == 'EthernetBackingDevice':
                            sub_child2 = child.getchildren()
                            for child in sub_child2:
                                if re.sub(r'{[^>]*}', "", child.tag) == 'DeviceName':
                                    BackingDeviceName = child.text
                                if re.sub(r'{[^>]*}', "", child.tag) == 'IPInterface':
                                    sub_child3 = child.getchildren()
                                    for child in sub_child3:
                                        if re.sub(r'{[^>]*}', "", child.tag) == 'State':
                                            BackingDeviceState = child.text
                # if re.sub(r'{[^>]*}', "", child.tag) == 'PortVLANID':
                    # VLANID = child.text
                if re.sub(r'{[^>]*}', "", child.tag) == 'HighAvailabilityMode':
                    HighAvailabilityMode = child.text
                if re.sub(r'{[^>]*}', "", child.tag) == 'DeviceName':
                    SEADeviceName = child.text
                if re.sub(r'{[^>]*}', "", child.tag) == 'TrunkAdapters':
                    sub_child = child.getchildren()
                    for child in sub_child:
                        if re.sub(r'{[^>]*}', "", child.tag) == 'TrunkAdapter':
                            sub_child2 = child.getchildren()
                            for child in sub_child2:
                                if re.sub(r'{[^>]*}', "", child.tag) == 'PortVLANID':
                                    VLANIDs.append(child.text)
                                if re.sub(r'{[^>]*}', "", child.tag) == 'TrunkPriority':
                                    Priority = child.text
            VLANIDs.sort()
            for id in VLANIDs:
                VLAN_IDs = VLAN_IDs + id + ","
            VLAN_IDs = VLAN_IDs[:-1]
            sea_config[vios_name][VLAN_IDs] = {}
            sea_config[vios_name][VLAN_IDs]["BackingDeviceName"] = BackingDeviceName
            sea_config[vios_name][VLAN_IDs]["BackingDeviceState"] = BackingDeviceState
            sea_config[vios_name][VLAN_IDs]["SEADeviceName"] = SEADeviceName
            sea_config[vios_name][VLAN_IDs]["SEADeviceState"] = ""
            sea_config[vios_name][VLAN_IDs]["HighAvailabilityMode"] = HighAvailabilityMode
            sea_config[vios_name][VLAN_IDs]["Priority"] = Priority
    for vlan_id in sea_config[vios_name]:
        (rc, state) = get_vios_sea_state(vios_name, sea_config[vios_name][vlan_id]["SEADeviceName"])
        if rc == 0:
            sea_config[vios_name][vlan_id]["SEADeviceState"] = state


###############################################################################
# Pycurl
###############################################################################

def curl_request(sess_key, url, filename):
    """
    Perform a Curl request with given URL and write the result in file

    Input: (str) HMC session key
    Input: (str) URL for the request
    Input: (str) URL for the request
    Output:(int) O if success, !0 in case of error
    Output:(str) error message in case of error (can be None)
    """
    log("Curl request, sess_key: {0}, file: {1}, url: {2}\n".format(sess_key, filename, url))
    try:
        f = open(filename, 'wb')
    except IOError as e:
        write('ERROR: Failed to create file {0}: {1}.'.format(filename, e.strerror), lvl=0)
        sys.exit(3)

    hdrs = ['X-API-Session:{0}'.format(sess_key)]
    hdr = cStringIO.StringIO()

    try:
        c = pycurl.Curl()
        c.setopt(c.HTTPHEADER, hdrs)
        c.setopt(c.URL, url)
        c.setopt(c.SSL_VERIFYPEER, False)
        c.setopt(c.WRITEDATA, f)
        c.setopt(pycurl.HEADERFUNCTION, hdr.write)
        # for debug:
        log("c.URL:'{0}' url:'{1}'\n".format(c.URL, url))
        log(" c.HTTPHEADER='{0}' hdrs:'{1}'\n".format(c.HTTPHEADER, hdrs))
        log(" c.SSL_VERIFYPEER='{0}'\n".format(c.SSL_VERIFYPEER))
        log(" c.WRITEDATA='{0}' f:'{1}'\n".format(c.WRITEDATA, f))
        log(" headerfunction='{0} {1}'\n".format(pycurl.HEADERFUNCTION, hdr.write))

        c.perform()

    except pycurl.error as e:
        write("ERROR: Request to {0} failed: {1}.".format(url, e), lvl=0)
        f.close()
        return 1, e.strerror

    f.close()
    # TBC - uncomment the 2 following lines for debug
    # f = open(filename, 'r')
    # log("\n### File %s content ###{0}### End of file {1} ###\n"
    #     .format(filename, f.read(), filename))

    # Get the http code and message to precise the error
    status_line = hdr.getvalue().splitlines()[0]
    m = re.match(r'HTTP\/\S*\s*(\d+)\s*(.*)\s*$', status_line)
    if m:
        http_code = str(m.group(1))
        http_message = " %s" % (str(m.group(2)))
    else:
        http_code = c.getinfo(pycurl.HTTP_CODE)
        http_message = ""

    if http_code != "200":
        log("Curl returned '{0}{1}' for request '{2}'\n".format(http_code, http_message, url))
        return http_code, http_message

    return 0


def get_vios_info(hmc_info, vios_uuid, filename):
    """
    Get VIOS information given its UUID

    Input:(dict) HMC information to get its hostname and session key
    Input: (str) vios UUID
    Input: (str) file name to put the result
    Output:(int) O if success, !0 in case of error
    Output:(str) error message in case of error (can be None)
    """
    url = "https://{0}:12443/rest/api/uom/VirtualIOServer/{1}"\
          .format(hmc_info['hostname'], vios_uuid)
    return curl_request(hmc_info['session_key'], url, filename)


def get_managed_system(hmc_info, filename):
    """
    Get managed systems information

    Input:(dict) HMC information to get its hostname and session key
    Input: (str) file name to put the result
    Output:(int) O if success, !0 in case of error
    Output:(str) error message in case of error (can be None)
    """
    url = "https://{0}:12443/rest/api/uom/ManagedSystem".format(hmc_info['hostname'])
    return curl_request(hmc_info['session_key'], url, filename)


def get_managed_system_lpar(hmc_info, managed_system_uuid, filename):
    """
    Get LPARs of a managed system

    Input:(dict) HMC information to get its hostname and session key
    Input: (str) managed system UUID
    Input: (str) file name to put the result
    Output:(int) O if success, !0 in case of error
    Output:(str) error message in case of error (can be None)
    """
    url = "https://{0}:12443/rest/api/uom/ManagedSystem/{1}/LogicalPartition"\
          .format(hmc_info['hostname'], managed_system_uuid)
    return curl_request(hmc_info['session_key'], url, filename)


def get_vfc_client_adapter(hmc_info, lpar, filename):
    """
    Get information on LPAR to see network connections

    Input:(dict) HMC information to get its hostname and session key
    Input: (str) managed system UUID
    Input: (str) file name to put the result
    Output:(int) O if success, !0 in case of error
    Output:(str) error message in case of error (can be None)
    """
    url = "https://{0}:12443/rest/api/uom/LogicalPartition/{1}/VirtualFibreChannelClientAdapter"\
          .format(hmc_info['hostname'], lpar)
    return curl_request(hmc_info['session_key'], url, filename)


def get_vnic_info(hmc_info, uuid, filename):
    """
    Get information on VIOS Virtual NIC Dedicated adapter

    Input:(dict) HMC information to get its hostname and session key
    Input: (str) VIOS UUID
    Input: (str) file name to put the result
    Output:(int) O if success, !0 in case of error
    Output:(str) error message in case of error (can be None)
    """
    url = "https://{0}:12443/rest/api/uom/LogicalPartition/{1}/VirtualNICDedicated"\
          .format(hmc_info['hostname'], uuid)
    return curl_request(hmc_info['session_key'], url, filename)


def usage():
    """
    Display the usage:

    Input:  none
    Output: none
    """
    global USAGE
    write(USAGE, lvl=0)


###############################################################################
# MAIN
###############################################################################
USAGE = "Usage: \n\
  vioshc -h\n\
  vioshc [-u id] [-p pwd] -i hmc_ip_addr -l {a | m} [-v] [-L log_dir]\n\
  vioshc [-u id] [-p pwd] -i hmc_ip_addr -m managed_system\n\
        -U vios_uuid [-U vios_uuid] [-v] [-L log_dir] [-D]\n\
  \n\
   -h : display this help message\n\
   -i : hmc ip address or hostname\n\
   -u : hmc user ID\n\
   -p : hmc user password\n\
   -U : vios UUID, use flag twice for two UUIDs\n\
   -m : managed system UUID\n\
   -v : verbose\n\
   -l : list managed system information\n\
      a : list managed system and vios UUIDs\n\
      m : list managed system UUIDs\n\
   -L : specify a log directory\n\
   -D : debug mode: keep the xml directory\n"

# Establish a log file
today = datetime.now()
# Default log directory
log_dir = "/tmp/vios_maint"
mode = "no"  # no debug

try:
    opts, args = getopt.getopt(
        sys.argv[1:],
        'hi:u:p:U:m:vDL:l:',
        ["help", 'HMC IP=', 'User ID=', 'Password=',
         'VIOS UUID=', 'Managed System UUID=', 'Verbose',
         'Debug', 'Log Directory=', 'List'])
except getopt.GetoptError:
    print(USAGE)
    sys.exit(2)

# first search the log file parameter
for opt, arg in opts:
    if opt in ('-L'):
        log_dir = arg

# Establish a log file
if not os.path.exists(log_dir):
    os.makedirs(log_dir)

# Log file format is vios_maint_YYYY-mm-dd_HHMMSS.log
# TBC - for debugging it could be easier to have a fixed file name
log_path = "%s/vioshc_%04d_%02d_%d_%02d%02d%02d.log" \
           % (log_dir, today.year, today.month, today.day, today.hour, today.minute, today.second)
xml_dir = "%s/xml_dir_%04d_%02d_%d_%02d%02d%02d" \
          % (log_dir, today.year, today.month, today.day, today.hour, today.minute, today.second)
os.makedirs(xml_dir)
try:
    log_file = open(log_path, 'a+', 1)
except IOError as e:
    print("ERROR: Failed to create log file {0}: {1}.".format(log_path, e.strerror))
    sys.exit(3)

log("################################################################################\n")
log("vioshc log file for command:\n{0}\n".format(sys.argv[0:]))
log("################################################################################\n")

###############################################################################
# Parse command line arguments & Curl requirement
###############################################################################
log("\nParsing command line arguments\n")
log("PID=%(thread)d")
action = "check"

for opt, arg in opts:
    if opt in ('-h', "--help"):
        usage()
        sys.exit(0)
    elif opt in ('-i'):
        hmc_ip = arg
    elif opt in ('-u'):
        hmc_user_id = arg
    elif opt in ('-p'):
        hmc_password = arg
    elif opt in ('-U'):
        # Check if VIOS UUID is valid
        if re.match(r"^[a-zA-Z0-9-]*$", arg):
            if vios1_uuid == "":
                vios1_uuid = arg
            elif vios2_uuid == "":
                vios2_uuid = arg
            else:
                write("Warning: more than 2 UUID specified. They will be ignored.", lvl=1)
            vios_num += 1
        else:
            write("Invalid UUID. Please try again.", lvl=0)
            sys.exit(2)
    elif opt in ('-m'):
        # Check if managed system UUID is valid
        if re.match(r"^[a-zA-Z0-9-]*$", arg):
            managed_system_uuid = arg
        else:
            write("Invalid UUID format. Please try again.", lvl=0)
            sys.exit(2)
    elif opt in ('-v'):
        verbose += 1
        if verbose == 1:
            print("Log file is: {0}\n".format(log_path))  # no need to log in file here
    elif opt in ('-l'):
        action = "list"
        list_arg = arg
    elif opt in ('-D'):
        mode = "debug"

# Check mandatory arguments
log("\nChecking mandatory arguments\n")
rc = 0
if hmc_ip == "":
    write("Missing HMC information.", lvl=0)
    rc += 1
if action == "check":
    if vios1_uuid == "":
        write("Missing VIOS UUID.", lvl=0)
        rc += 1
    if managed_system_uuid == "":
        write("Missing Managed System UUID.", lvl=0)
        rc += 1
elif action == "list":
    if list_arg != 'a' and list_arg != 'm':
        write("Invalid argument '%s' for list flag." % (list_arg), lvl=0)
        rc += 1
else:
    write("ERROR: Unknown action {0}.".format(action), lvl=0)
    rc += 1
if rc != 0:
    usage()
    sys.exit(2)

###############################################################################
# Set xml files path names
###############################################################################
filename_session_key = "{0}/sessionkey.xml".format(xml_dir)
filename_systems = "{0}/systems.xml".format(xml_dir)
filename_lpar_info = "{0}/lpar_info.xml".format(xml_dir)

# filename_network1 = "{0}/network1.xml".format(xml_dir)
# filename_network2 = "{0}/network2.xml".format(xml_dir)
filename_vnic_info = "{0}/vnic_info.xml".format(xml_dir)
filename_msg = "{0}/msg.txt".format(xml_dir)

# Checks for curl on the system: return status is 0 if successful, else failed
os.system('command -v curl >/dev/null 2>&1 || '
          '{ echo "ERROR: Curl not installed on this system. Exiting now." >&2; exit 2; }')


###############################################################################
# Get HMC credentials
###############################################################################
write("Getting HMC {0} info".format(hmc_ip), lvl=2)
# Get the HMC hostname in case user provided the short name or an IP address
(hostname, aliases, ip_list) = get_hostname(hmc_ip)
log("hmc {0} hostname: {1}\n".format(hmc_ip, hostname))

###############################################################################
# Retrieve the NIM object name matching the hostname
###############################################################################
nim_name = get_nim_name(hostname)
log("hmc {0} nim_name: {1}\n".format(hostname, nim_name))
if nim_name == "":
    sys.exit(3)

###############################################################################
# Gets all NIM attributes for the HMC
###############################################################################
hmc_info = get_nim_info(nim_name)
if hmc_info is None:
    write("ERROR: Failed to retrieve HMC info.", lvl=0)
    sys.exit(3)
hmc_info['nim_name'] = nim_name
hmc_info['hostname'] = hostname
hmc_info['ip'] = ip_list[0]

for key in hmc_info.keys():
    log("hmc_info[%-13s] = %s\n" % (key, hmc_info[key]))

write("Getting HMC credentials", lvl=2)
# If either username or password are empty, try to retrieve them
if (hmc_password == "") or (hmc_user_id == ""):
    write("Retrieving HMC user id and password", lvl=2)
    (hmc_user_id, hmc_password) = retrieve_usr_pass(hmc_info)
if (hmc_user_id != ""):
    hmc_info['user_id'] = hmc_user_id
if (hmc_password != ""):
    hmc_info['user_password'] = hmc_password

write("Getting HMC session key", lvl=2)
session_key = get_session_key(hmc_info, filename_session_key)
if session_key == "":
    write("ERROR: Failed to get {0} session key.".format(hmc_ip), lvl=0)
    sys.exit(3)
hmc_info['session_key'] = session_key


###############################################################################
# Get managed system info
###############################################################################
log("\nGet Managed System info\n")
rc = get_managed_system(hmc_info, filename_systems)
if rc != 0:
    write("ERROR: Failed to collect managed system info: {0}".format(rc[1]), lvl=0)
    sys.exit(2)
build_managed_system(hmc_info, vios_info, managed_system_info, filename_systems)


###############################################################################
# List UUIDs
###############################################################################
if action == "list":
    log("\nListing UUIDs\n")
    rc = print_uuid(managed_system_info, vios_info, list_arg)
    # Clean up
    if mode != "debug":
        shutil.rmtree(xml_dir, ignore_errors=True)
    sys.exit(rc)


###############################################################################
# REST Call to /rest/api/uom/VirtualIOServer
# Get name and partition ID of each VIOS then filters
#  the ones of interest
###############################################################################
write("Find VIOS(es) Name from specified UUID(s)", lvl=2)
for name in vios_info.keys():
    if vios_info[name]['uuid'] == vios1_uuid:
        vios1_name = name
        vios_info[name]['role'] = 'primary'
    elif vios_num > 1 and vios_info[name]['uuid'] == vios2_uuid:
        vios2_name = name
        vios_info[name]['role'] = 'secondary'
    else:
        del vios_info[name]
for name in vios_info.keys():
    for key in vios_info[name].keys():
        log("vios_info[{0}][{1}] = {2}\n".format(name, key, vios_info[name][key]))
rc = 0
if vios1_name == "":
    write("ERROR: Failed to find VIOS1 {0} info.".format(vios1_uuid), lvl=0)
    rc = 1
if vios_num > 1 and vios2_name == "":
    write("ERROR: Failed to find VIOS2 {0} info.".format(vios2_uuid), lvl=0)
    rc = 1
if rc != 0:
    sys.exit(2)

primary_header = "\nPrimary VIOS Name         IP Address      ID         UUID                "
backup_header = "\nBackup VIOS Name          IP Address      ID         UUID                "
divider = "-----------------------------------------------------------------------------------" \
          "--------------"
format = "%-25s %-15s %-10s %-40s "

for vios in vios_info.keys():
    # If Resource Monitoring Control State is inactive, it will throw off our UUID/IP pairing
    if (vios_info[vios]['control_state'] == "inactive"):
        continue

    # If VIOS is not running, skip it otherwise it will throw off our UUID/IP pairing
    if vios_info[vios]['partition_state'] == "not running":
        continue

    # Get VIOS1 info (original VIOS)
    if vios_info[vios]['role'] == "primary":
        write(primary_header, lvl=0)
    else:
        write(backup_header, lvl=0)

    write(divider, lvl=0)
    write(format % (vios_info[vios]['partition_name'], vios_info[vios]['ip'],
                    vios_info[vios]['id'], vios_info[vios]['uuid']), lvl=0)

# Check both vios are in the same CEC
if vios_info[vios1_name]['managed_system'] != managed_system_uuid:
    write("ERROR: VIOS1 {0} (UUID: {1}) is on Managed System {2}, not {3}\n"
          .format(vios1_name, vios_info[vios1_name]['uuid'],
                  vios_info[vios1_name]['managed_system'],
                  managed_system_uuid), lvl=0)
    sys.exit(2)
if vios_num > 1 and vios_info[vios2_name]['managed_system'] != managed_system_uuid:
    write("ERROR: VIOS2 {0} (UUID: {1}) is on Managed System {2}, not {3}\n"
          .format(vios2_name, vios_info[vios2_name]['uuid'],
                  vios_info[vios2_name]['managed_system'],
                  managed_system_uuid), lvl=0)
    sys.exit(2)


###############################################################################
# Get UUIDs of all LPARs that belong to the managed
# system that we are interested in
###############################################################################
# Get managed system LPAR info, write data to file
write("Collect LPAR info for managed system: {0}".format(managed_system_uuid), 2)
rc1 = get_managed_system_lpar(hmc_info, managed_system_uuid, filename_lpar_info)
if rc1 != 0:
    write("ERROR: Failed to collect managed system {0} info: {1}"
          .format(managed_system_uuid, rc1[1]), lvl=0)
    sys.exit(2)

# Check for error response in file
if grep_check(filename_lpar_info, 'HttpErrorResponse'):
    write("ERROR: Request to https://{0}:12443/rest/api/uom/ManagedSystem/{1}/LogicalPartition \
returned Error Response.".format(hmc_ip, managed_system_uuid), lvl=0)
    write("Unable to detect LPAR information.", lvl=0)

build_lpar_info(lpar_info, filename_lpar_info)

# Log VIOS information
for id in lpar_info.keys():
    log("lpar[{0}]: {1}\n".format(id, str(lpar_info[id])))


###############################################################################
# Check active clients are the same for VIOS1 and VIOS2
###############################################################################
write("Check active client(s):", lvl=2)
active_client_id = []
active_client = {}
diff_clients = []

# Find configured clients of VIOS1
# TBC - ConnectingPartitionID is present in VirtualFibreChannelMapping elem
active_client['vios1'] = awk(vios_info[vios1_name]['filename'], 'ServerAdapter',
                             'ConnectingPartitionID')
log("active_client['vios1']: " + str(active_client['vios1']) + "\n")

if vios_num > 1:
    # Find configured clients of VIOS2
    active_client['vios2'] = awk(vios_info[vios2_name]['filename'], 'ServerAdapter',
                                 'ConnectingPartitionID')
    log("active_client['vios2']: " + str(active_client['vios2']) + "\n")

    # Check that both VIOSes have the same clients
    # if they do not, all health-checks will fail and we cannot continue the program
    for id in active_client['vios1']:
        if (id not in active_client['vios2']) and (id not in diff_clients):
            diff_clients.append(id)
    diff_clients.sort()
    log("diff_clients: " + str(diff_clients) + "\n")

# Check for error response in file
if grep_check(filename_lpar_info, 'HttpErrorResponse'):
    write("FAIL: Unable to detect active clients", lvl=0)
    num_hc_fail += 1
elif len(diff_clients) == 0:
    if vios_num > 1:
        write("PASS: Active client lists are the same for both VIOSes", lvl=0)
    active_client_id = active_client['vios1']
    num_hc_pass += 1
else:
    write("FAIL: Active clients lists are not the same for {0} and {1}, check these clients:"
          .format(vios1_name, vios2_name), lvl=0)
    write(str(diff_clients), lvl=1)
    num_hc_fail += 1

write("\nActive clients information:", lvl=1)

header = "LPAR                      ID         UUID                            "
divider = "---------------------------------------------------------------------------"
format = "%-25s %-10s %-40s "
write(header, lvl=1)
write(divider, lvl=1)

# Print active clients, IDs, and UUIDs
for id in active_client_id:
    for keys, values in lpar_info.items():
        log("lpar_info: " + keys + "\n")
        # og("lpar_info: " + values + "\n")
    if id in lpar_info:
        write(format % (lpar_info[id]['name'], id, lpar_info[id]['uuid']), lvl=1)
    else:
        log("active_client_id '{0}' not lpar_info dictionary\n".format(id))


###############################################################################
# Get vSCSI mappings
###############################################################################
write("\nvSCSI validation:", lvl=1)
vscsi1_mapping = get_vscsi_mapping(vios1_name, vios1_uuid)

# Get vSCSI mappings for VIOS2 if VIOS tuple
if vios_num > 1:
    vscsi2_mapping = get_vscsi_mapping(vios2_name, vios2_uuid)

    # Compare the both vSCSI mapping
    if vscsi1_mapping == vscsi2_mapping:
        write("PASS: same vSCSI configuration on both VIOSes.", lvl=0)
        num_hc_pass += 1
    else:
        write("FAIL: vSCSI configurations are not identical on both VIOSes.", lvl=0)
        num_hc_fail += 1


#######################################################
# Fibre Channel mappings
#######################################################
fc_mapping = {}
# fc_mapping[server_name] = {}
# fc_mapping[server_name][client_name] = {}
# fc_mapping[server_name][client_name]["VirtualSlotsNumber"] = local virtual slot number
# fc_mapping[server_name][client_name]["ConnectingVirtualSlotsNumber"] = remote virtual slot number
build_fc_mapping(vios1_name, vios1_uuid, fc_mapping)
if vios_num > 1:
    # Fibre Channel mapping for VIOS2
    build_fc_mapping(vios2_name, vios2_uuid, fc_mapping)

write("\nNPIV Path Validation:", lvl=1)

fc_header = "VIOS Name               Local VSlot   Remote VSlot     Client"
divider = "---------------------------------------------------------------------------"
format = "%-28s %-12s %-12s %-20s "
write(fc_header, lvl=1)
write(divider, lvl=1)

i = 0  # index for looping through all partition mappings
for server in fc_mapping:
    for client in fc_mapping[server]:
        write(format
              % (server, fc_mapping[server][client]["VirtualSlotNumber"],
                 fc_mapping[server][client]["ConnectingVirtualSlotNumber"], client),
              lvl=1)

# Compares the both VIOS Fiber Channel mapping
if vios_num > 1:
    if vios1_name not in fc_mapping and vios2_name not in fc_mapping:
        write("PASS: no FC mapping configuration on both VIOSes.", lvl=0)
        num_hc_pass += 1
    elif vios1_name not in fc_mapping or vios2_name not in fc_mapping:
        write("FAIL: FC configurations are not identical on both VIOSes.", lvl=0)
        num_hc_fail += 1
    else:
        vios1_client_list = fc_mapping[vios1_name].keys().sort()
        vios2_client_list = fc_mapping[vios2_name].keys().sort()
        if vios1_client_list == vios2_client_list:
            write("PASS: same FC mapping configuration on both VIOSes.", lvl=0)
            num_hc_pass += 1
        else:
            write("FAIL: FC configurations are not identical on both VIOSes.", lvl=0)
            num_hc_fail += 1

###############################################################################
# NPIV PATH VALIDATION
# TBC - remove this section when we validate checks
#       made here are already done in FC mapping part
#       here above
###############################################################################

# fc_ids = []
# drc_list = []
# WWPN_list = []

# write("\nNPIV Path Validation:")

# # Check for path validation by running mig_vscsi to check for notzoned tag
# # for each active partition, get notzoned info for both vios and check if false
# notzoned = ""
# notzoned_value = ""
for id in active_client_id:
    if id in lpar_info:
        # Get LPAR info, write data to xml file
        filename_npiv_mapping = "{0}/{1}_npiv_mapping.xml".format(xml_dir, lpar_info[id]['name'])
        get_vfc_client_adapter(hmc_info, lpar_info[id]['uuid'], filename_npiv_mapping)
    # # TBC - uncomment the 2 following lines for debug
    # #f = open(filename_npiv_mapping, 'r')
    # #log("\n### File %s content ###%s### End of file %s ###\n"
    #      % (filename_npiv_mapping, f.read(), filename_npiv_mapping))

    # # Create a list of fibre channel IDs
    # fc_ids = grep_array(filename_npiv_mapping, 'LocalPartitionID')
    # if len(fc_ids) == 0:
    #     write("No vFC client adapter ID for lpar: %s (%s)"
    #           % (lpar_info[id]['name'], lpar_info[id]['uuid']))
    #     #remove(filename_npiv_mapping)
    #     continue

    # # Create a list of dynamic reconfiguration connectors
    # drc_list = grep_array(filename_npiv_mapping, 'DynamicReconfigurationConnectorName')
    # # Create a list of WWPN
    # WWPN_list = grep_array(filename_npiv_mapping, 'WWPN')

    # touch(filename_adapter1)
    # touch(filename_adapter2)

    # # Cannot get mig_vscsi to stdout so need to use another file to get info
    # j = 0
    # for partition_id in fc_ids:
    #     if vios_info[vios1_name]['id'] == partition_id:
    #         lower_WWPN = WWPN_list[j]
    #         j += 1  # get the higher WWPN
    #         higher_WWPN = WWPN_list[j]
    #         DRC = drc_list[j]
    #         j += 1  # one more increment bc we skip clients, and drc_list repeats itself twice

    #         cmd = [C_RSH, vios_info[vios1_name]['hostname'],
    #                "LC_ALL=C /usr/lib/methods/mig_vscsi -f get_adapter "
    #                "-t vscsi -s %s -a ACTIVE_LPM -c RPA  -M 1 -d 5 -W 0x%s -w 0x%s -F %s; "
    #                "echo rc=$?"
    #                % (DRC, lower_WWPN, higher_WWPN, filename_adapter1)]
    #         (rc, output, errout) = exec_cmd(cmd)
    #         if rc != 0 or re.match(r'.*ERROR.*', output.rstrip()):
    #             write("ERROR: Cannot get vSCSI adapter info on %s, mig_vscsi command: %s %s"
    #                   % (vios1_name, output.rstrip(), errout), lvl=0)
    #             num_hc_fail += 1
    #             continue

    #         if os.path.exists(filename_adapter1):
    #             notzoned_value = grep(filename_adapter1, 'notZoned')
    #             notzoned = re.match(r'.*false.*', notzoned_value)

    #     if vios_num > 1 and vios_info[vios2_name]['id'] == partition_id:
    #         lower_WWPN = WWPN_list[j]
    #         j += 1  # get the higher WWPN
    #         higher_WWPN = WWPN_list[j]
    #         DRC = drc_list[j]
    #         j += 1  # one more increment bc we skip clients, and drc_list repeats itself twice

    #         cmd = [C_RSH, vios_info[vios2_name]['hostname'],
    #                "LC_ALL=C /usr/lib/methods/mig_vscsi -f get_adapter "
    #                "-t vscsi -s %s -a ACTIVE_LPM -c RPA  -M 1 -d 5 -W 0x%s -w 0x%s -F %s; "
    #                "echo rc=$?"
    #                % (DRC, lower_WWPN, higher_WWPN, filename_adapter2)]
    #         (rc, output, errout) = exec_cmd(cmd)
    #         if rc != 0 or re.match(r'.*ERROR.*', output.rstrip()):
    #             write("ERROR: Cannot get vSCSI adapter info on %s, mig_vscsi command: %s %s"
    #                   % (vios2_name, output.rstrip(), errout), lvl=0)
    #             num_hc_fail += 1
    #             continue

    #         if os.path.exists(filename_adapter2):
    #             notzoned_value = grep(filename_adapter2, 'notZoned')
    #             notzoned = notzoned and re.match(r'.*false.*', notzoned_value)

    #     if notzoned:
    #         if vios_num > 1:
    #             write("PASS: %s has a NPIV path through both VIOSes." % (lpar_info[id]['name']))
    #         else:
    #             write("PASS: %s has a NPIV path through the VIOS." % (lpar_info[id]['name']))
    #         num_hc_pass += 1
    #     else:
    #         if vios_num > 1:
    #             write("FAIL: %s doesn't have a NPIV path through both VIOSes."
    #                   % (lpar_info[id]['name']), lvl=0)
    #         else:
    #             write("FAIL: %s doesn't have a NPIV path through the VIOS."
    #                   % (lpar_info[id]['name']))
    #         num_hc_fail += 1

###############################################################################
# Building SEA configuration for VIOSes
###############################################################################
sea_config = {}
build_sea_config(vios1_name, vios1_uuid, sea_config)
# sea_config[vios_name] = {}
#           [vios_name][VLANID] = {}
#           [vios_name][VLANID]["BackingDeviceName"] = "entx"
#           [vios_name][VLANID]["BackingDeviceState"] = "Inactive/Disconnected/...."
#           [vios_name][VLANID]["SEADeviceName"] = "entx"
#           [vios_name][VLANID]["SEADeviceState"] = "UNHEALTHY/PRIMARY/BACKUP/STANDBY"
#           [vios_name][VLANID]["HighAvailabilityMode"] = "auto/sharing"
#           [vios_name][VLANID]["Priority"] = priority
if vios_num > 1:
    build_sea_config(vios2_name, vios2_uuid, sea_config)

###############################################################################
# SEA validation
###############################################################################
write("\nSEA Validation:", lvl=1)
vios1_state = ""
vios2_state = ""

header = "VIOS                 VLAN(s)   HA MODE  SEA Dev   SEA State    Backing Dev  State     "
divider = "--------------------------------------------------------------------------------------"
format = "%-20s %-9s %-8s %-9s %-12s %-12s %-10s"

write(header, lvl=1)
write(divider, lvl=1)
for vlan_id in sea_config[vios1_name]:
    write(format % (vios1_name, vlan_id,
          sea_config[vios1_name][vlan_id]["HighAvailabilityMode"],
          sea_config[vios1_name][vlan_id]["SEADeviceName"],
          sea_config[vios1_name][vlan_id]["SEADeviceState"],
          sea_config[vios1_name][vlan_id]["BackingDeviceName"],
          sea_config[vios1_name][vlan_id]["BackingDeviceState"]), lvl=1)
if vios_num > 1:
    for vlan_id in sea_config[vios2_name]:
        write(format % (vios2_name, vlan_id,
              sea_config[vios2_name][vlan_id]["HighAvailabilityMode"],
              sea_config[vios2_name][vlan_id]["SEADeviceName"],
              sea_config[vios2_name][vlan_id]["SEADeviceState"],
              sea_config[vios2_name][vlan_id]["BackingDeviceName"],
              sea_config[vios2_name][vlan_id]["BackingDeviceState"]), lvl=1)

    for vlan_id in sea_config[vios1_name]:
        vios1_state = sea_config[vios1_name][vlan_id]["SEADeviceState"]
        if vlan_id in sea_config[vios2_name]:
            ha_mode1 = sea_config[vios1_name][vlan_id]["HighAvailabilityMode"]
            ha_mode2 = sea_config[vios2_name][vlan_id]["HighAvailabilityMode"]
            if ha_mode1 != "auto" and ha_mode1 != "sharing" or ha_mode1 != ha_mode2:
                write("FAIL: SEA(s) deserving VLAN(s) {0} are not configured for failover."
                      .format(vlan_id), lvl=0)
                num_hc_fail += 1
                continue

            vios2_state = sea_config[vios2_name][vlan_id]["SEADeviceState"]
            if ("PRIMARY" in vios1_state and ("BACKUP" in vios2_state or "STANDBY" in vios2_state))\
               or ("PRIMARY" in vios2_state and
                   ("BACKUP" in vios1_state or "STANDBY" in vios1_state)):
                write('PASS: SEA(s) deserving VLAN(s) {0} are configured for failover.'
                      .format(vlan_id), lvl=0)
                num_hc_pass += 1
                continue
            elif (vios1_state == "LIMBO") and (vios2_state == "LIMBO"):
                write('PASS: SEA(s) deserving VLAN(s) {0} are configured on both VIOSes but '
                      'not in usable state'.format(vlan_id), lvl=0)
                num_hc_pass += 1
                continue
            else:
                write('FAIL: SEA(s) deserving VLAN(s) {0} are not in the correct state for '
                      'HA operation.'.format(vlan_id), lvl=0)
                num_hc_fail += 1
                continue
        elif vios1_state == "LIMBO":
            write('PASS: SEA(s) deserving VLAN(s) {0} are not configured on both VIOSes but '
                  'not in usable state.'.format(vlan_id), lvl=0)
            continue
        elif vios1_state == "":
            write('PASS: SEA(s) deserving VLAN(s) {0} are not configured on both VIOSes but '
                  'not in usable state.'.format(vlan_id), lvl=0)
            continue
        else:
            write('FAIL: SEA(s) deserving VLAN(s) {0} are not configured on both VIOSes.'
                  .format(vlan_id), lvl=0)
            num_hc_fail += 1
            continue

    for vlan_id in sea_config[vios2_name]:
        if vlan_id not in sea_config[vios1_name]:
            vios2_state = sea_config[vios2_name][vlan_id]["SEADeviceState"]
            if vios2_state == "LIMBO":
                write('PASS: SEA(s) deserving VLAN(s) {0} are not configured on both VIOSes '
                      'but not in usable state.'.format(vlan_id), lvl=0)
                num_hc_fail += 1
                continue
            elif vios2_state == "":
                write('PASS: SEA(s) deserving VLAN(s) {0} are not configured on both VIOSes but '
                      'not in usable state.'.format(vlan_id), lvl=0)
                continue
            else:
                write('FAIL: SEA(s) deserving VLAN(s) {0} are not configured on both VIOSes.'
                      .format(vlan_id), lvl=0)
                num_hc_fail += 1
                continue
if len(sea_config[vios1_name].keys()) == 0 \
   and (vios_num == 1 or (vios_num > 1 and len(sea_config[vios2_name].keys()) == 0)):
    write('\nNo SEA Configuration Detected.', lvl=0)

#######################################################
# VNIC validation with REST API
#######################################################
vnic_fail_flag = 0
vnic_configured = 0

write("\nVNIC Validation:", lvl=1)

for id in active_client_id:
    # Get VNIC info, write data to file
    if id in lpar_info:
        get_vnic_info(hmc_info, lpar_info[id]['uuid'], filename_vnic_info)

    # grep_devnull
    if grep_check(filename_vnic_info, '200 OK'):
        vnic_configured = 1
        break

# If a VNIC configuration is detected, perform the validation
if vnic_configured == 0:
    write("No VNIC Configuration Detected.", lvl=0)
else:
    header = "Client Name           Client ID       VIOS1 VNIC Server           VIOS2 VNIC Server"
    divider = "-----------------------------------------------------------------------------------"\
              "----"
    format = "%-20s %-15s %-27s %-27s "
    write(header, lvl=0)
    write(divider, lvl=0)

    i = 0
    for id in active_client_id:
        vios1_associated = "DISCONNECTED"
        if vios_num > 1:
            vios2_associated = "DISCONNECTED"
        else:
            vios2_associated = "n/a"

        # Get VNIC info, write data to vnic_info.xml
        if id in lpar_info:
            get_vnic_info(hmc_info, lpar_info[id]['uuid'], filename_vnic_info)

        # Check to see if VNIC Server on VIOS1 is associated
        associated_vios = grep_array(filename_vnic_info, 'AssociatedVirtualIOServer')
        for vios in associated_vios:
            if vios1_uuid in vios:
                vios1_associated = "CONNECTED"
            if vios2_uuid in vios:
                vios2_associated = "CONNECTED"

        if id in lpar_info:
            write(format % (lpar_info[id]['name'], active_client_id[i],
                            vios1_associated, vios2_associated), lvl=0)
            write("\n", lvl=0)
            if vios1_associated == "DISCONNECTED":
                write('FAIL: {0} is not connected with VIOS1 VNIC Server.'
                      .format(lpar_info[id]['name']), lvl=0)
                vnic_fail_flag = 1
                num_hc_fail += 1
            if vios2_associated == "DISCONNECTED":
                write('FAIL: {0} is not connected with VIOS2 VNIC Server.'
                      .format(lpar_info[id]['name']), lvl=0)
                vnic_fail_flag = 1
                num_hc_fail += 1

        vios1_associated = 0
        vios2_associated = 0
        i += 1

    if vnic_fail_flag == 0:
        write("PASS: VNIC Configuration is Correct.", lvl=0)
        num_hc_pass += 1

###############################################################################
# End of Health Checks
###############################################################################
# Perform analysis on Pass and Fails
total_hc = num_hc_fail + num_hc_pass
pass_pct = num_hc_pass * 100 / total_hc
write("\n\n%d of %d Health Checks Passed" % (num_hc_pass, total_hc), lvl=0)
write("%d of %d Health Checks Failed" % (num_hc_fail, total_hc), lvl=0)
write("Pass rate of %d%%\n" % (pass_pct), lvl=0)

if mode != 'debug':
    shutil.rmtree(xml_dir, ignore_errors=True)

log_file.close()

# Should exit 0 if all health checks pass, exit 1 if any health check fails
if (num_hc_pass == total_hc):
    sys.exit(0)
else:
    sys.exit(1)
