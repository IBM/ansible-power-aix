.. _flrtvc_module:


flrtvc -- Generate FLRTVC report, download and install efix.
============================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Creates a task to check targets vulnerability against available fixes, and apply necessary fixes. It downloads and uses the Fix Level Recommendation Tool Vulnerability Checker Script to generates a report. It parses the report, downloads the fixes, checks their versions and if some files are locked. Then it installs the remaining fixes. In case of inter-locking file you could run this several times.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  force (optional, bool, False)
    Specifies to remove currently installed ifix before running the FLRTVC script.


  verbose (optional, bool, False)
    Generate full FLRTVC reporting (verbose mode).


  save_report (optional, bool, False)
    Specifies to save the FLRTVC report in file '*path*/flrtvc.txt'.


  download_only (optional, bool, False)
    Specifies to perform check and download operation, do not install anything.


  extend_fs (optional, bool, True)
    Specifies to increase filesystem size of the working directory if needed.

    If set a filesystem of the host could have increased even if it returns *changed=False*.


  clean (optional, bool, False)
    Cleanup working directory '*path*/work' with all temporary and downloaded files at the end of execution.


  path (optional, str, /var/adm/ansible)
    Specifies the directory to save the FLRTVC report. All temporary files such as previously installed filesets, fixes lists and downloaded fixes files will be stored in the working subdirectory named '*path*/work'.


  csv (optional, str, None)
    Path to a APAR CSV file containing the description of the ``sec`` and ``hiper`` fixes.

    This file is usually transferred from the fix server; this rather big transfer can be avoided by specifying an already transferred file.


  check_only (optional, bool, False)
    Specifies to only check if fixes are already applied on the targets. No download or install operations.


  apar (optional, str, None)
    Type of APAR to check or download.

    ``sec`` Security vulnerabilities.

    ``hiper`` Corrections to High Impact PERvasive threats.

    ``all`` Same behavior as None, both ``sec`` and ``hiper`` vulnerabilities.


  filesets (optional, str, None)
    Filter filesets for specific phrase. Only fixes on the filesets specified will be checked and updated.









Examples
--------

.. code-block:: yaml+jinja

    
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



Return Values
-------------

msg (always, str, FLRTVC completed successfully)
  The execution message.


meta (always, dict, {'meta': {'0.report': ['Fileset|Current Version|Type|EFix Installed|Abstract|Unsafe Versions|APARs|Bulletin URL|Download URL|CVSS Base Score|Reboot Required| Last Update|Fixed In', 'bos.net.tcp.client_core|7.2.3.15|sec||NOT FIXED - There is a vulnerability in FreeBSD that affects AIX.|7.2.3.0-7.2.3.15| IJ09625 / CVE-2018-6922|http://aix.software.ibm.com/aix/efixes/security/freebsd_advisory.asc|ftp://aix.software.ibm.com/aix/efixes/security/freebsd_fix.tar|CVE-2018-6922:7.5|NO|11/08/2018|7200-03-03', '...'], '1.parse': ['ftp://aix.software.ibm.com/aix/efixes/security/ntp_fix12.tar', 'ftp://aix.software.ibm.com/aix/efixes/security/tcpdump_fix4.tar', '...'], 'messages': ['a previous efix to install will lock a file of IJ20785s3a preventing its installation, install it manually or run the task again.', '...'], '4.1.reject': ['102p_fix: prerequisite openssl.base levels do not match: 1.0.2.1600 < 1.0.2.1500 < 1.0.2.1600', '...', 'IJ12983m2a: locked by previous efix to install', '...', 'IJ17059m9b: prerequisite missing: ntp.rte', '...'], '2.discover': ['ntp_fix12/IJ17059m9b.190719.epkg.Z', 'ntp_fix12/IJ17060m9a.190628.epkg.Z', '...', 'tcpdump_fix4/IJ12978s9a.190215.epkg.Z', 'tcpdump_fix4/IJ12978sBa.190215.epkg.Z', '...'], '3.download': ['/usr/sys/inst.images/tardir/ntp_fix12/IJ17059m9b.190719.epkg.Z', '/usr/sys/inst.images/tardir/ntp_fix12/IJ17060m9a.190628.epkg.Z', '...', '/usr/sys/inst.images/tardir/tcpdump_fix4/IJ12978s9a.190215.epkg.Z', '/usr/sys/inst.images/tardir/tcpdump_fix4/IJ12978sBa.190215.epkg.Z', '...'], '4.2.check': ['/usr/sys/inst.images/tardir/tcpdump_fix5/IJ20785s2a.191119.epkg.Z', '...'], '5.install': ['/usr/sys/inst.images/tardir/tcpdump_fix5/IJ20785s2a.191119.epkg.Z', '...']}})
  Detailed information on the module execution.


  0.report (if the FLRTVC script run succeeds, list, see below)
    Output of the FLRTVC script, report or details on flrtvc error if any.


  1.parse (if the parsing succeeds, list, see below)
    List of URLs to download or details on parsing error if any.


  messages (always, list, see below)
    Details on errors/warnings


  4.1.reject (if check succeeds, list, see below)
    List of epkgs rejected, refer to messages and log file for reason.


  2.discover (if the discovery succeeds, list, see below)
    List of epkgs found in URLs.


  3.download (if download succeeds, list, see below)
    List of downloaded epkgs.


  4.2.check (if check succeeds, list, see below)
    List of epkgs following prerequisites.


  5.install (if install succeeds, list, see below)
    List of epkgs actually installed.






Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

