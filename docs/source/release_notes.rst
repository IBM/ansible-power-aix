.. ...........................................................................
.. © Copyright IBM Corporation 2021                                          .
.. ...........................................................................

Releases
========


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

