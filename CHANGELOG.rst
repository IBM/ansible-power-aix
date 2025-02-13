.. ...........................................................................
.. © Copyright IBM Corporation 2021                                          .
.. ...........................................................................

Releases
========

Version 2.0.3
-------------
Notes
   * New module: sysdumpdev to manage system dump settings.
   * New demo playbook for sysdumpdev module.
   * Fixed defects for DNF boostrap role.
   * Enhancement in lvm_facts to include information from lslv command for logical volumes.
   * Fixed sorting issue in flrtvc module.
   * Updated NIM module to accept license.
   * Crical fixes in tunable module to include -K option for live update flag in AIX 7.3

Availability
  * `Automation Hub v2.0.3`_
  * `Galaxy v2.0.3`_
  * `GitHub v2.0.3`_

.. _Automation Hub v2.0.3:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v2.0.3:
   https://galaxy.ansible.com/download/ibm-power_aix-2.0.3.tar.gz

.. _GitHub v2.0.3:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-2.0.3.tar.gz

Version 2.0.2
-------------
Notes
   * Fixed linting issues reported by Red hat automation hub.

Availability
  * `Automation Hub v2.0.2`_
  * `Galaxy v2.0.2`_
  * `GitHub v2.0.2`_

.. _Automation Hub v2.0.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v2.0.2:
   https://galaxy.ansible.com/download/ibm-power_aix-2.0.2.tar.gz

.. _GitHub v2.0.2:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-2.0.2.tar.gz

Version 2.0.1
-------------
Notes
   * Fixed linting issues reported by Red hat automation hub.
   * Defect: https://github.com/IBM/ansible-power-aix/issues/578

Availability
  * `Automation Hub v2.0.1`_
  * `Galaxy v2.0.1`_
  * `GitHub v2.0.1`_

.. _Automation Hub v2.0.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v2.0.1:
   https://galaxy.ansible.com/download/ibm-power_aix-2.0.1.tar.gz

.. _GitHub v2.0.1:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-2.0.1.tar.gz

Version 2.0.0
-------------
Notes
   * New module: route (Manage routes on IBM AIX systems.)
   * New module: snap (snap command to gather diagnostic data)
   * New role: live_kernel_update
   * New playbook: demo_aix_lku_role, demo_route, demo_snap.
   * Enhancement in NIM ADM role to support concurrent migration.
   * Enhancement in tunables module to support -K flag
   * Removed modify state from user module.
   * Enhancement in NIM module to support new fileset installation.
   * Defects: https://github.com/IBM/ansible-power-aix/pull/580
   * Defects: https://github.com/IBM/ansible-power-aix/pull/582
   * Enhancement in group module to support -R flag for LDAP
   * Updated nim-flrtvc module in accordance with the flrtvc script
   * Defects: https://github.com/IBM/ansible-power-aix/issues/193
   * Fixed idempotency issue in NIM module for allocation and deallocation.


Availability
  * `Automation Hub v2.0.0`_
  * `Galaxy v2.0.0`_
  * `GitHub v2.0.0`_

.. _Automation Hub v2.0.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v2.0.0:
   https://galaxy.ansible.com/download/ibm-power_aix-2.0.0.tar.gz

.. _GitHub v2.0.0:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-2.0.0.tar.gz

Version 1.9.2
-------------
Notes
   * Minimum required ansible version is 2.15.0 now.


Availability
  * `Automation Hub v1.9.2`_
  * `Galaxy v1.9.2`_
  * `GitHub v1.9.2`_

.. _Automation Hub v1.9.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.9.2:
   https://galaxy.ansible.com/download/ibm-power_aix-1.9.2.tar.gz

.. _GitHub v1.9.2:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.9.2.tar.gz

Version 1.9.1
-------------
Notes
   * Fixed documentation issue reported by Red Hat Automation Hub


Availability
  * `Automation Hub v1.9.1`_
  * `Galaxy v1.9.1`_
  * `GitHub v1.9.1`_

.. _Automation Hub v1.9.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.9.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.9.1.tar.gz

.. _GitHub v1.9.1:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.9.1.tar.gz


Version 1.9.0
-------------
Notes
   * New module: lku. (Live Kernel Update, PowerVC support)
   * New module: password_rules_policies, allows the user to manage password rules and policies.
   * New module: hdcrypt_facts, useful for displaying encryption/decryption related information.
   * New module: hdcrypt_pks, which allows the user to add PKS authentication method and manage PKS keys.
   * New playbook: install_all_updates
   * New playbook: lvg
   * New playbook: chsec
   * New playbook: lku, hdcrypt_facts, hdcrypt_pks, password_rules_policies.
   * Updated demo playbook for backing up rootvg.
   * Enhancement: Local patch server can be used to download the fixes though FLRTVC module.
   * Enhancement: Empty attributes are now allowed in filesystem module.
   * Defect: Fixed parsing of emgr -l output for AIX 7.3.
   * Defect: Fixed indexing error for int data type in filesystem module.
   * Defect: Fixed linting issues for latest ansible-lint version.
   * Defect: Fixed pylint issues according to latest requirements.
   * Defect: Fixed incorrect check of inetd services.
   * Defect: Fixed idempotency issue in filesystem module.
   * Defect: Fixed idempotency issue in EMGR module.
   * Defect: Fixed FLRTVC module in accordance with the new version of the script.
   * Defect: Fixed boolean value error in chsec module.
   * Defect: Updated chsec module to show custom error messages.
   * Defect: Updated mkfilt module to show custom messages.
   * Defect: Updated MPIO module - erroneous cases are now dealt with.
   * Defect: Modified Mktun module to show proper messages.
   * Made minor documentation changes in most of the modules.


Availability
  * `Automation Hub v1.9.0`_
  * `Galaxy v1.9.0`_
  * `GitHub v1.9.0`_

.. _Automation Hub v1.9.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.9.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.9.0.tar.gz

.. _GitHub v1.9.0:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.9.0.tar.gz

Version 1.8.3
-------------
Notes
   * Fixed linting issue reported by Red Hat Automation Hub.


Availability
  * `Automation Hub v1.8.3`_
  * `Galaxy v1.8.3`_
  * `GitHub v1.8.3`_

.. _Automation Hub v1.8.3:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.8.3:
   https://galaxy.ansible.com/download/ibm-power_aix-1.8.3.tar.gz

.. _GitHub v1.8.3:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.8.3.tar.gz

Version 1.8.2
-------------
Notes
   * Enhancement to handle mirrored rootvg in case of alt_disk_copy.
   * Fixed LDAP check before running mkuser.
   * Enhancements in nim_adm role: check for CacheVG, eFix bundle, pre/post migration.
   * Expanded nimadm_options to include Pre-,Post-, and Phases_to_run and set_fact for them.
   * Add output from "lsrsrc IBM.MCP" to lpar_facts to make the controlling HMC details readily
     available from within a playbook.
   * Fixed idempotency issue for specific attributes in filesystem module.
   * New demo_getconf.py playbook.

Availability
  * `Automation Hub v1.8.2`_
  * `Galaxy v1.8.2`_
  * `GitHub v1.8.2`_

.. _Automation Hub v1.8.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.8.2:
   https://galaxy.ansible.com/download/ibm-power_aix-1.8.2.tar.gz

.. _GitHub v1.8.2:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.8.2.tar.gz

Version 1.8.1
-------------
Notes
   * Fixed documentation in install_all_updates

Availability
  * `Automation Hub v1.8.1`_
  * `Galaxy v1.8.1`_
  * `GitHub v1.8.1`_

.. _Automation Hub v1.8.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.8.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.8.1.tar.gz

.. _GitHub v1.8.1:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.8.1.tar.gz

Version 1.8.0
-------------
Notes
   * New module: install_all_upates
   * New Module: getconf to generate system configuration variable values as facts.
   * Enhancement: Mount module is updated to use mount command instead of df.
   * Enhancement: Enhanced parsing of nim_resource module stdout.
   * Enhancement: Updated emgr module to remove ifix.
   * Enhancement: Updated flrtvc module to list system specific fixes, AIX/VIOS.
   * Enhancement: Updated lvm_facts module to include PVs without VG or unvaried VG.
   * Enahncement: Updated documentations.
   * Defect: Fix nim module to update from lpp source.
   * Defect: Fix nim module fo unavail_targets.
   * Defect: alt_disk module is fixed for alt_rootvg_op operation, install action.
   * Defect: Group module is fixed for creating group with group id.
   * Defect: Fix filesystem module which used to set "options=rw" when creating filesystem.
   * Defect: Fix lvol module to allow renaming without specifying size.

Availability
  * `Automation Hub v1.8.0`_
  * `Galaxy v1.8.0`_
  * `GitHub v1.8.0`_

.. _Automation Hub v1.8.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.8.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.8.0.tar.gz

.. _GitHub v1.8.0:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.8.0.tar.gz

Version 1.7.2
-------------
Notes
   * Fixed ansible-lint issue for various playbooks.

Availability
  * `Automation Hub v1.7.2`_
  * `Galaxy v1.7.2`_
  * `GitHub v1.7.2`_

.. _Automation Hub v1.7.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.7.2:
   https://galaxy.ansible.com/download/ibm-power_aix-1.7.2.tar.gz

.. _GitHub v1.7.2:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.7.2.tar.gz

Version 1.7.1
-------------
Notes
   * Minimim ansible version is changed to 2.14.0
   * Fixed dnf bootstrap issue for python3 in AIX 7.1 and 7.2

Availability
  * `Automation Hub v1.7.1`_
  * `Galaxy v1.7.1`_
  * `GitHub v1.7.1`_

.. _Automation Hub v1.7.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.7.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.7.1.tar.gz

.. _GitHub v1.7.1:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.7.1.tar.gz

Version 1.7.0
-------------
Notes
   * New Role: NIM Master Migration.
   * New module: Physical and Logical volume encryption.
   * New demo playbook: NIM Master migration and PV/LV Encryption.
   * NIM module enhanced to register new client.
   * Included link to Power research program in the galaxy page.
   * Fix for parsing lspv, lsvg header to get LV attribute indexes.
   * Updated dnf bootstrap installer.
   * Fix for minimum space issue to setup dnf/python.
   * dnf setup is enhanced to support proxy servers.
   * Fixed ansible-lint issue in demo_yum_install_DB.yml.
   * Updated flrtvc link in nim_flrtvc module.
   * emgr module is fixed and idempotent now.
   * Fixed user module to support idempotency.
   * alt_disk module has now support for install operations.
   * Fixed utf-8 encoding issue in flrtvc module.
   * Fixed inittab module to modify entry and is idempotent now.
   * Fixed the logic of disk_size_policy in alt_disk module. 

Availability
  * `Automation Hub v1.7.0`_
  * `Galaxy v1.7.0`_
  * `GitHub v1.7.0`_

.. _Automation Hub v1.7.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.7.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.7.0.tar.gz

.. _GitHub v1.7.0:
   https://github.com/IBM/ansible-power-aix/raw/dev-collection/builds/ibm-power_aix-1.7.0.tar.gz

Version 1.6.4
-------------
Notes
   * Fixed documentation for release platform

Availability
  * `Automation Hub v1.6.4`_
  * `Galaxy v1.6.4`_
  * `Github v1.6.4`_

. _Automation Hub v1.6.4:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.6.4:
   https://galaxy.ansible.com/download/ibm-power_aix-1.6.4.tar.gz

.. _GitHub v1.6.4:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.6.4/ibm-power_aix-1.6.4.tar.gz

Version 1.6.3
-------------
Notes
   * Fixed pylint, shellcheck and shebang issues for a clean build.

Availability
  * `Automation Hub v1.6.3`_
  * `Galaxy v1.6.3`_
  * `Github v1.6.3`_

. _Automation Hub v1.6.3:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.6.3:
   https://galaxy.ansible.com/download/ibm-power_aix-1.6.3.tar.gz

.. _GitHub v1.6.3:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.6.3/ibm-power_aix-1.6.3.tar.gz

Version 1.6.2
-------------
Notes
   * Fix for mount module to handle umount state in case of existing NFS server directories.
   * User module is now able to create local user even if the user exists in active directory (LDAP)
   * demo_alt_disk playbook
   * Fix for emgr module in case of no efix data available
   * Fix for devices modules, handling runtime errors
   * Fixed nim_backup playbooks
   * Feature enhancement: Include alternate disk to update in nim module

Availability
  * `Automation Hub v1.6.2`_
  * `Galaxy v1.6.2`_
  * `GitHub v1.6.2`_

.. _Automation Hub v1.6.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.6.2:
   https://galaxy.ansible.com/download/ibm-power_aix-1.6.2.tar.gz

.. _GitHub v1.6.2:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.6.2/ibm-power_aix-1.6.2.tar.gz

Version 1.6.1
-------------
Notes
  * Fix pylint issues
  * Fix yamllint issue

Availability
  * `Automation Hub v1.6.1`_
  * `Galaxy v1.6.1`_
  * `GitHub v1.6.1`_

.. _Automation Hub v1.6.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.6.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.6.1.tar.gz

.. _GitHub v1.6.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.6.1/ibm-power_aix-1.6.1.tar.gz


Version 1.6.0
-------------
Notes
  * New module: Bosboot.
  * New Playbooks: mktun, mount,installp, user, mpio, mkfilt, 
  * New Playbooks: bosboot, group, tunables, filesystem, nim_suma, logical_volume
  * New Playbooks: tunfile_mgmt, mktcpip, inittab
  * Enhanced idempotency for devices module.
  * Enhancement in nim_alt_disk_migration:
  * - Target disk without PVID accepted
  * - Divide Used PVs by number of PVs to overcome multiple PVs in rootvg
  * - Allow install of AIX level lower than NIM master AIX level
  * - Reduce debug info after checking client OS level
  * - Add cache VG and Bundle to nimadm options
  * - Re-order nimadm flags and "quote" disk variable to allow multiple PVs in rootvg
  * - Correct {{ nim_client_v }} to {{ nim_client }}
  * Enhanced alt_disk module: allows to clean old_rootvg.
  * Improved parsing for emgr module output for ifix lists and details.
  * Fixed power_aix_bootstrap role dnf_installer.sh
  * Fixed power_aix_bootstrap role to support DNF installation for AIX-7.1 and above.
  * Yum is not supported anymore from ansible as a result of sunset of python 2.
  * Fixed power_aix_bootstrap role to show failure in case it is unable to install DNF.

Availability
  * `Automation Hub v1.6.0`_
  * `Galaxy v1.6.0`_
  * `GitHub v1.6.0`_

.. _Automation Hub v1.6.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.6.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.6.0.tar.gz

.. _GitHub v1.6.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.6.0/ibm-power_aix-1.6.0.tar.gz


Version 1.5.1
-------------
Notes
  * Various customer defects from public repository are fixed. 
  * Fixed broken download link for flrtvc module.
  * Added quorum to lvg module.
  * Fix for filesystem module which ignored attributes parameter for NFS filesystems.
  * Fix to be more strict on mount check.
  * Allow repository sources to be overridden for local mirrors, for yum.
  * Fix in suma module to prevent type comparison error in case the metadata file that is being searched does not specify an SP version.
  * Fix for idempotecy issue for installp module.
  * Updates to sanity tests.
  * Fixed python linting issue for various modules.

Availability
  * `Automation Hub v1.5.1`_
  * `Galaxy v1.5.1`_
  * `GitHub v1.5.1`_

.. _Automation Hub v1.5.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.5.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.5.1.tar.gz

.. _GitHub v1.5.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.5.1/ibm-power_aix-1.5.1.tar.gz


Version 1.5.0
-------------
Notes
  * New role, nim_alt_disk_migration, for automating AIX migration (upgrades) using nimadm ( Network Install Manager Alternate Disk Migration) utility.
  *  Information: https://github.com/IBM/ansible-power-aix/blob/dev-collection/roles/nim_alt_disk_migration/README.md
  * New module, nim_resource, to create, remove or display NIM resource objects such as lpp_source, spot, etc.
  * New enhanced nim module, with new option "show" to display NIM object information.
  * New module, tunables, for automating Kernel Tuning management of no, nfso, vmo, ioo, raso, and schedo.
  * New module, tunfile_mgnt, for automating Kernel Tuning using files with tuning parameter values: no, nfs, vmo, ioo, raso, and schedo.
  * Enhanced inventory for lpar_facts. Examples: facts for os level, inc_core_crypto, nxcrypto, processor type/implementation mode, and others.
  * Enhanced inventory for lpp_facts. Examples: facts for fixes (apar, SP, TL), version consistency (lppchk).
  * New module, chsec, for automating changes to attributes in the security stanza files.
  * Fix DNF bootstrap not to download the AIX Toolbox bundle if it exist in the controller.
  * Updates to sanity tests.

Availability
  * `Automation Hub v1.5.0`_
  * `Galaxy v1.5.0`_
  * `GitHub v1.5.0`_

.. _Automation Hub v1.5.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.5.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.5.0.tar.gz

.. _GitHub v1.5.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.5.0/ibm-power_aix-1.5.0.tar.gz


Version 1.4.1
-------------
Notes
  * Fix DNF bootstrap for AIX 7.3 in role power_aix_bootstrap role in supporting new AIX Linux toolbox changes.
  * Fix DNF bootstrap in role power_aix_bootstrap to run with Ansible Tower.
  * Fix devices module to support inet0 add/delete routes.
  * Fix installp module idempotency issue to show changes in case of at least one successful operation.
  * Fix flrtvc module messages if there are no interim fixes to install.
  * Fix flrtvc module to prevent failures after downloading compressed file fixes; there are no interim fixes to install.
  * Issue #184: Add missing file vioshc_dep_install.yml to the power_aix_vioshc role.
  * Fix user module idempotency issue by comparing current values to requested changes before executing any actions.


Availability
  * `Automation Hub v1.4.1`_
  * `Galaxy v1.4.1`_
  * `GitHub v1.4.1`_

.. _Automation Hub v1.4.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.4.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.4.1.tar.gz

.. _GitHub v1.4.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.4.1/ibm-power_aix-1.4.1.tar.gz


Version 1.4.0
-------------
Notes
  * Support for the new AIX 7.3 release.
  * Updates to multiple modules and roles to ensure python2/python3 compatibility.
  * Updates to the power_aix_bootstrap to install dnf on AIX 7.3.
  * Updates to the flrtc and nim_flrtvc modules to work with the new AIX toolsbox
    wget binary path: /opt/freeware/bin.
  * Multiple fixes to clean up ansible-lint and other sanity checks.
  * Fix issue #168. power_aix_bootstrap inventory_host variable problem.
  * Fix issue #157 for the mount.py module. Error while changing the state from mount to unmount while mounting/umounting for a NFSv4 filesytem.
  * Fix issue #151 for user.py. Fail to create/modify user if attribute "gecos" contains spaces.

Availability
  * `Automation Hub v1.4.0`_
  * `Galaxy v1.4.0`_
  * `GitHub v1.4.0`_

.. _Automation Hub v1.4.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.4.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.4.0.tar.gz

.. _GitHub v1.4.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.4.0/ibm-power_aix-1.4.0.tar.gz


Version 1.3.1
-------------
Notes
  * Fix issue #145: user module with non string attributes fails.
  * Fixes to pass sanity checks on Ansible minimum required version.

Availability
  * `Automation Hub v1.3.1`_
  * `Galaxy v1.3.1`_
  * `GitHub v1.3.1`_

.. _Automation Hub v1.3.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.3.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.3.1.tar.gz

.. _GitHub v1.3.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.3.1/ibm-power_aix-1.3.1.tar.gz


Version 1.3.0
-------------
Notes
  * Change Ansible support from 2.0 to 2.9.
  * smtctl: new module to enables/disable simultaneous MultiThreading mode.
  * backup: Fix idempotency issues. Add new force option to overwrite a backup. Better examples.
  * alt_disk: fix failure with no free disk available. issue #61.
  * devices: Fix idempotency issues. Other issues: #59, #98.
  * emgr: Fix idempotency issues.
  * filesystem: Fix idempotency issues. Other issues: #76. Other improvements.
  * lvg: Fix idempotency issues.
  * lvm_facts: Display volume groups that are deactivated or varied off.
  * lvol: Fix idempotency issues.Fix the wrong interpretation for attribute size (issue #72). Issue #100.
  *  - Add strip_size attribute.
  *  - Allow users to re-size (increase) logical volumes by using +<size><suffix>,
  *    where suffix can be B/M/K/G or a bigger size value.
  * nim: Add new attribute boot_client option to prevent nim from rebooting the client. Other fixes
  * user: Fix issue #110: modify attributes was not working.
  * flrtvc: Allows user to specify the protocol (ftp/http) to download fixes(issue #70).
  * mount: Fix proper checking for remote fs (issue #111)
  * group: Fix idempotency issues. (issue #69)
  * reboot: Fix issue #78
  * Readme: Requirement change to Ansible 2.9 or newer from Ansible 2.0

Availability
  * `Automation Hub v1.3.0`_
  * `Galaxy v1.3.0`_
  * `GitHub v1.3.0`_

.. _Automation Hub v1.3.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.3.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.3.0.tar.gz

.. _GitHub v1.3.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.3.0/ibm-power_aix-1.3.0.tar.gz


Version 1.2.1
-------------
Notes
  * Minor fixes for playbook demo_nim_viosupgrade.yml
  * Minor fixes for plugin reboot.py

Availability
  * `Automation Hub v1.2.1`_
  * `Galaxy v1.2.1`_
  * `GitHub v1.2.1`_

.. _Automation Hub v1.2.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.2.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.2.1.tar.gz

.. _GitHub v1.2.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.2.1/ibm-power_aix-1.2.1.tar.gz


Version 1.2.0
-------------
Notes
  * Refresh of patch management capability (Update recommended)
  * Fixes in nim_flrtvc and nim_backup modules for Python2 compatibility
  * Documenting RBAC authorizations per module
  * Quickstart documentation: user creation with RBAC authorization
  * use nim_exec() instead of calling c_rsh command directly in nim, nim_flrtvc, nim_suma
  * new playbook examples / improvements
  * aixpert: new module for AIXPert
  * alt_disk: new options for alt_disk_copy
  * backup: add restore and view operation for mksysb + playbook
  * bootlist: new module
  * inittab: new module
  * lpar_facts: new module
  * lvm_facts: new module
  * lvol: new module for logical volume management
  * mkfilt: new module
  * mktun: new module to manage IPsec manual tunnels
  * mpio: new module
  * nim: uniformize logging and message, add 'meta' and command returns
  * nim_backup: fix multithreading for simultaneous mksysb creation with NIM
  * nim_updateios: major fixes and improvements for cluster management
  * nim_updateios: fix cluster -list that returns 7 fields if not verbose not 21 fields
  * nim_vios_alt_disk: rework logging and result reporting
  * reboot: new module
  * suma: fix issue #40 (unpack return value calling suma_command())
  * user: improvement (issues #56 and #57 )

Availability
  * `Automation Hub v1.2.0`_
  * `Galaxy v1.2.0`_
  * `GitHub v1.2.0`_

.. _Automation Hub v1.2.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.2.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.2.0.tar.gz

.. _GitHub v1.2.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.2.0/ibm-power_aix-1.2.0.tar.gz

Version 1.1.2
-------------
Notes
  * Beta: preview of the lpar_facts module
  * Beta: preview of the lvm_facts module
  * Beta: preview of the bootlist module
  * mkfilt: use run_command with check_rc=True when appropriate
  * nim_upgradeios: module has been deprecated (use nim_viosupgrade)
  * nim_viosupgrade: fixes for altdisk and bosinst operations
  * new playbook to demo nim_viosupgrade
  * new roles for inetd and bootptab
  * documentation revisions for several modules

Availability
  * `Automation Hub v1.1.2`_
  * `Galaxy v1.1.2`_
  * `GitHub v1.1.2`_

.. _Automation Hub v1.1.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.1.2:
   https://galaxy.ansible.com/download/ibm-power_aix-1.1.2.tar.gz

.. _GitHub v1.1.2:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.1.2/ibm-power_aix-1.1.2.tar.gz

Version 1.1.1
-------------
Notes
  * Beta: preview of the lpp_facts module
  * nim_upgradeios: fixes
  * nim_viosupgrade: fixes/ cleanup
  * user: fix change_passwd_on_login
  * user: don't log parameters related to passwords
  * filesystem and other modules: use FQDN in examples

Availability
  * `Automation Hub v1.1.1`_
  * `Galaxy v1.1.1`_
  * `GitHub v1.1.1`_

.. _Automation Hub v1.1.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.1.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.1.1.tar.gz

.. _GitHub v1.1.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.1.1/ibm-power_aix-1.1.1.tar.gz

Version 1.1.0
-------------
Notes
  * Refresh of patch management capability (Update recommended)
  * new modules: inittab, mkfilt
  * aixpert: new module for AIXPert
  * lvol: new module for logical volume management
  * alt_disk: new options for alt_disk_copy
  * backup: add restore and view operation for mksysb + playbook
  * nim_backup: fix multithreading for simultaneous mksysb creation with NIM
  * nim_updateios: major fixes and improvements for cluster management
  * nim_updateios: fix cluster -list that returns 7 fields if not verbose not 21 fields
  * suma: fix issue #40 (unpack return value calling suma_command())

Availability
  * `Automation Hub v1.1.0`_
  * `Galaxy v1.1.0`_
  * `GitHub v1.1.0`_

.. _Automation Hub v1.1.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.1.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.1.0.tar.gz

.. _GitHub v1.1.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.1.0/ibm-power_aix-1.1.0.tar.gz

Version 1.0.2
-------------
Notes
  * Includes Ansible Roles for bootstrap (yum/python) and VIOS health checker (early release)
  * NIM backup module (early release)
  * Filesystem module (early release)
  * Minor fixes for NIM updateios
  * Minor fixes for mount module

Availability
  * `Automation Hub v1.0.2`_
  * `Galaxy v1.0.2`_
  * `GitHub v1.0.2`_

.. _Automation Hub v1.0.2:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.0.2:
   https://galaxy.ansible.com/download/ibm-power_aix-1.0.2.tar.gz

.. _GitHub v1.0.2:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.0.2/ibm-power_aix-1.0.2.tar.gz

Version 1.0.1
-------------
Notes
  * Improvements to FLRTVC patch reporting

Availability
  * `Automation Hub v1.0.1`_
  * `Galaxy v1.0.1`_
  * `GitHub v1.0.1`_

.. _Automation Hub v1.0.1:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.0.1:
   https://galaxy.ansible.com/download/ibm-power_aix-1.0.1.tar.gz

.. _GitHub v1.0.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.0.1/ibm-power_aix-1.0.1.tar.gz

Version 1.0.0
-------------
Notes
  * Official release of patch management capability
  * Update recommended

Availability
  * `Automation Hub v1.0.0`_
  * `Galaxy v1.0.0`_
  * `GitHub v1.0.0`_

.. _Automation Hub v1.0.0:
   https://cloud.redhat.com/ansible/automation-hub/ibm/power_aix

.. _Galaxy v1.0.0:
   https://galaxy.ansible.com/download/ibm-power_aix-1.0.0.tar.gz

.. _GitHub v1.0.0:
   https://github.com/IBM/ansible-power-aix/releases/download/v1.0.0/ibm-power_aix-1.0.0.tar.gz

Version 0.4.2
-------------
Notes
  * Minor bug fixes for flrtvc and nim modules

Availability
  * `Galaxy v0.4.2`_
  * `GitHub v0.4.2`_

.. _Galaxy v0.4.2:
   https://galaxy.ansible.com/download/ibm-power_aix-0.4.2.tar.gz

.. _GitHub v0.4.2:
   https://github.com/IBM/ansible-power-aix/releases/download/v0.4.2/ibm-power_aix-0.4.2.tar.gz

Version 0.4.1
-------------
Notes
  * Initial beta release of IBM Power Systems AIX collection, referred to as power_aix

Availability
  * `GitHub v0.4.1`_

.. _GitHub v0.4.1:
   https://github.com/IBM/ansible-power-aix/releases/download/v0.4.1/ibm-power_aix-0.4.1.tar.gz



