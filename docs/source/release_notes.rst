.. ...........................................................................
.. © Copyright IBM Corporation 2021                                          .
.. ...........................................................................

Releases
========

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



