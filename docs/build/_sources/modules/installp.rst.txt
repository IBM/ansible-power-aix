.. _installp_module:


installp -- Installs and updates software
=========================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Installs available software products in a compatible installation package.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  save (optional, bool, True)
    Saves existing files that are replaced when installing or updating.


  force (optional, bool, False)
    Forces the installation of a software product even if there exists a previously installed version of the software product that is the same as or newer than the version currently being installed.


  platform (optional, str, all)
    Specifies the platform.

    ``POWER`` specifies POWER processor-based platform packages only.

    ``neutral`` specifies neutral packages, that is, packages that are not restricted to the POWER processor-based platform.

    ``all`` specifies all packages.


  agree_licenses (optional, bool, False)
    Agrees to required software license agreements for software to be installed.


  extend_fs (optional, bool, True)
    Attempts to resize any file systems where there is insufficient space to do the installation.


  delete_image (optional, bool, False)
    Deletes the installation image file after the software product or update has been successfully installed.


  base_only (optional, bool, False)
    Limits the requested action to base level filesets.


  parts (optional, list, None)
    Installs the specified part of the software product.

    ``root``

    ``share``

    ``usr``


  device (optional, str, None)
    The name of the device or directory containing installation images.


  dependencies (optional, bool, False)
    Automatically installs any software products or updates that are requisites of the specified software product.

    Automatically removes or rejects dependents of the specified software.


  bosboot (optional, bool, True)
    Performs a bosboot in the event that one is needed.


  install_list (optional, list, None)
    List of products to install

    ``all`` installs all products


  commit (optional, bool, False)
    Commit after apply.


  updates_only (optional, bool, False)
    Indicates that the requested action should be limited to software updates.


  action (optional, str, apply)
    Controls what is performed.

    ``apply`` to install with apply.

    ``commit`` to commit applied updates.

    ``reject`` to reject applied updates.

    ``deinstall`` to deinstall (remove) installed software.

    ``cleanup`` to clean up a failed installation.

    ``list`` to list all installable software on media.

    ``list_fixes`` to obtain a list of the Authorized Program Analysis Report (APAR) numbers and summaries.

    ``list_applied`` to list all software products and updates that have been applied but not committed.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: List all software products and installable options contained on an installation cartridge tape
      installp:
        action: list
        device: /dev/rmt0.1

    - name: List all customer-reported problems fixed by all software products on an installation tape
      installp:
        action: list_fixes
        device: /dev/rmt0.1
        install_list: all

    - name: Install all filesets within the bos.net software package and expand file systems if necessary
      installp:
        extend_fs: yes
        device: /usr/sys/inst.images
        install_list: bos.net

    - name: Reinstall and commit the NFS software product option that is already installed on the system at the same level
      installp:
        commit: yes
        force: yes
        device: /dev/rmt0.1
        install_list: bos.net.nfs.client:4.1.0.0

    - name: Remove a fileset named bos.net.tcp.server
      installp:
        action: deinstall
        install_list: bos.net.tcp.server



Return Values
-------------

msg (always, str, Command 'installp' failed with return code 1)
  The execution message.


stderr (always, str, installp: Device /dev/rfd0 could not be accessed.
Specify a valid device name.)
  The standard error.


stdout (always, str,  *******************************************************************************
 installp PREVIEW:  deinstall operation will not actually occur.
 *******************************************************************************
 
 +-----------------------------------------------------------------------------+
 Pre-deinstall Verification...
 +-----------------------------------------------------------------------------+
 Verifying selections...done
 Verifying requisites...done
 Results...
 
 WARNINGS
 --------
 Problems described in this section are not likely to be the source of any
 immediate or serious failures, but further actions may be necessary or
 desired.
 
 Not Installed
 -------------
 No software could be found on the system that could be deinstalled for the
 following requests:
 
 bos.sysmgt.nim.master                    
 
 (The fileset may not be currently installed, or you may have made a
 typographical error.)
 
 << End of Warning Section >>
 
 FILESET STATISTICS 
 ------------------
 1  Selected to be deinstalled, of which:
 1  FAILED pre-deinstall verification
 ----
 0  Total to be deinstalled
 
 
 ******************************************************************************
 End of installp PREVIEW.  No deinstall operation has actually occurred.
 ******************************************************************************)
  The standard output.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

