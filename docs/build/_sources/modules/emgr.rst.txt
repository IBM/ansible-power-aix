.. _emgr_module:


emgr -- The interim fix manager installs and manages system interim fixes.
==========================================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

The interim fix manager installs packages created with the epkg command and maintains a database containing interim fix information.

It can perform the following operations install, commit, check, mount, unmount, remove, list interim fix and view package locks.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  force (optional, bool, False)
    Forces action.

    Can be used if *action* has one of following values ``install``, ``remove``.

    When used *action=install*, it specifies the interim fix installation can overwrite an existing package.

    When used *action=remove*, it should be considered an emergency procedure because this method can create inconsistencies on the system.


  verbose (optional, int, None)
    Specifies the verbosity level. The verbosity increases with the value.

    Can be used if *action* has one of following values ``list``, ``check``, ``view_package``.


  extend_fs (optional, bool, False)
    Attempts to resize any file systems where there is insufficient space.


  ifix_package (optional, path, None)
    Specifies the path of the interim fix package file.

    If *from_epkg=yes*, then the file must be created with the epkg command and must end with the 16-bit compression extension, .Z. Otherwise the file is manage as a concurrent update ifix package file.

    Can be used if *action* has one of following values ``install``, ``display_ifix``.

    Mutually exclusive with *list_file*.


  action (optional, str, list)
    Controls what is performed.

    ``install`` performs an install of specified interim fix package

    ``commit`` performs a commit operation of the specified interim fix.

    ``check`` performs a check operation on installed interim fix.

    ``mount`` mounts specified interim fix that have been mount-installed

    ``unmount`` unmounts specified interim fix that have been mount-installed

    ``remove`` performs an uninstall of the specified interim fix.

    ``view_package`` displays all packages that are locked, their installer, and the locking label or labels.

    ``display_ifix`` displays the contents and topology of specified interim fix. This option is useful with ``verbose``.

    ``list`` lists interim fix data


  mount_install (optional, bool, False)
    Perform a mount installation. When and interim fix is mount-installed, the interim fix files are mounted over the target files.

    This option is not supported for interim fix packages that require rebooting.

    Can be used if *action=install*. Cannot be set when *from_epkg=no*.


  bosboot (optional, str, None)
    Controls the bosboot process.

    ``skip`` skip the usual bosboot process for Ifix that require rebooting.

    ``load_debugger`` loads the low-level debugger during AIX bosboot.

    ``invoke_debugger`` invoke the low-level debugger for AIX bosboot.

    Can be used if *action* has one of following values ``install``, ``commit``, ``remove``.


  ifix_label (optional, str, None)
    Specifies the interim fix label.

    Can be used if *action* has one of following values ``list``, ``commit``, ``remove``, ``check``, ``mount``, ``unmount``, ``remove``.

    Required if *action==remove* and *force=True*.

    Mutually exclusive with *ifix_number*, *ifix_vuid*, *list_file*.


  ifix_vuid (optional, str, None)
    Specifies the interim fix VUID.

    Can be used if *action* has one of following values ``list``, ``remove``, ``check``, ``mount``, ``unmount``.

    Mutually exclusive with *ifix_label*, *ifix_number*, *list_file*.


  package (optional, str, None)
    Specifies the package to view.

    Can be used if *action==view_package*


  from_epkg (optional, bool, False)
    Specifies to install an interim fix package file created with the epkg command.

    Can be used if *action=install*.


  quiet (optional, bool, False)
    Suppresses all output other than errors and strong warnings.

    Can be used if *action* has one of following values ``install``, ``commit``, ``remove``.


  working_dir (optional, path, None)
    Specifies an alternative working directory path instead of the default /tmp directory.

    If not specified the emgr command will use the /tmp directory.

    Can be used if *action* has one of following values ``install``, ``remove``, ``check``, ``mount``, ``unmount``, ``display_ifix``.


  alternate_dir (optional, path, None)
    Specifies an alternative directory path.

    Can be used if *action* has one of following values ``list``, ``install``, ``remove``, ``check``, ``mount``, ``unmount``, ``view_package``.


  ifix_number (optional, str, None)
    Specifies the interim fix ID.

    Can be used if *action* has one of following values ``list``, ``remove``, ``check``, ``mount``, ``unmount``, ``remove``.

    Mutually exclusive with *ifix_label*, *ifix_vuid*, *list_file*.


  list_file (optional, path, None)
    Specifies a file that contains a list of package locations if *action=install* or a list of interim fix labels for the remove, mount, unmount and check operations.

    The file must have one item per line, blank lines or starting with

    Can be used if *action* has one of following values ``install``, ``remove``, ``check``, ``mount``, ``unmount``, ``display_ifix``.

    Mutually exclusive with *ifix_label*, *ifix_number*, *ifix_vuid*, *ifix_package*.


  commit (optional, bool, False)
    Commits interim fix containing concurrent updates to disk after its installation.

    Can be used if *action=install*.


  preview (optional, bool, False)
    Perform a preview that runs all of the check operations but does not make any changes.

    Can be used if *action* has one of following values ``install``, ``commit``, ``remove``.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: List interim fix on the system
      emgr:
        action: list

    - name: Install ifix package from file generated with epkg
      emgr:
        action: install
        ifix_package: /usr/sys/inst.images/IJ22714s1a.200212.AIX72TL04SP00-01.epkg.Z
        working_dir: /usr/sys/inst.images
        from_epkg: yes
        extend_fs: yes

    - name: List a specific ifix data in details
      emgr:
        action: list
        ifix_label: IJ22714s1a
        verbosity: 3

    - name: Check an ifix
      emgr:
        action: check
        ifix_label: IJ22714s1a

    - name: Preview ifix commit and display only errors and warnings
      emgr:
        action: commit
        ifix_label: IJ22714s1a
        preview: True
        quiet: True

    - name: Remove an installed ifix based on its VUID
      emgr:
        action: remove
        ifix_vuid: 00F7CD554C00021210023020

    - name: Display contents and topology of an ifix
      emgr:
        action: display_ifix
        ifix_package: /usr/sys/inst.images/IJ22714s1a.200212.AIX72TL04SP00-01.epkg.Z



Return Values
-------------

msg (always, str, Missing parameter: force remove requires: ifix_label)
  The execution message.


stderr (always, str, There is no efix data on this system.)
  The standard error


stdout (always, str,  ID  STATE LABEL      INSTALL TIME      UPDATED BY ABSTRACT\n === ===== ========== ================= ========== ======================================\n 1    S    IJ20785s2a 04/30/20 11:03:46            tcpdump CVEs fixed                    \n 2    S    IJ17065m3a 04/30/20 11:03:57            IJ17065 is for AIX 7.2 TL03           \n 3   *Q*   IJ09625s2a 04/30/20 11:04:14            IJ09624 7.2.3.2                       \n 4    S    IJ11550s0a 04/30/20 11:04:34            Xorg Security Vulnerability fix       \n \n STATE codes:\n S = STABLE\n M = MOUNTED\n U = UNMOUNTED\n Q = REBOOT REQUIRED\n B = BROKEN\n I = INSTALLING\n R = REMOVING\n T = TESTED\n P = PATCHED\n N = NOT PATCHED\n SP = STABLE + PATCHED\n SN = STABLE + NOT PATCHED\n QP = BOOT IMAGE MODIFIED + PATCHED\n QN = BOOT IMAGE MODIFIED + NOT PATCHED\n RQ = REMOVING + REBOOT REQUIRED)
  The standard output





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

