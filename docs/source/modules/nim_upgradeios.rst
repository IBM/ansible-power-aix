.. _nim_upgradeios_module:


nim_upgradeios -- Perform a VIOS upgrade with NIM
=================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Tool to upgrade one or a pair of VIOSes.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  backup_prefix (optional, str, None)
    Prefix of the ios_backup NIM resource.

    The name of the target VIOS is added to this prefix.


  boot_client (optional, str, no)
    Boots the clients of the target VIOS after the upgrade and restore operation.


  nim_node (optional, dict, None)
    Allows to pass along NIM node info from a task to another so that it discovers NIM info only one time for all tasks.


  force (optional, str, no)
    Removes any existing ios_backup NIM resource prior to creating the backup.


  bosinst_data_prefix (optional, str, None)
    Prefix of the bosinst_data NIM resource that contains the BOS installation program to use.

    The NIM name of the target VIOS is added to this prefix to find the actual NIM resource, like: "<bosinst_data_prefix>_<vios_name>".


  vars (optional, dict, None)
    Specifies additional parameters.


  time_limit (optional, str, None)
    Before starting the action, the actual date is compared to this parameter value; if it is greater then the task is stopped; the format is ``mm/dd/yyyy hh:mm``.


  resolv_conf (optional, str, None)
    NIM resource to use for the VIOS installation.


  targets (True, str, None)
    NIM target.

    To perform an action on dual VIOSes, specify the list as a tuple with the following format: "(vios1, vios2) (vios3, vios4)".

    To specify a single VIOS, use the following format: "(vios1)".


  action (True, str, None)
    Specifies the operation to perform.

    ``backup`` to create a backup.

    ``view_backup`` to view existing backups.

    ``restore_backup`` to restore an existing backup.

    ``upgrade_restore`` to upgrade and restore target VIOS.


  location (optional, str, None)
    Existing directory to store the ios_backup on the NIM master.


  spot_prefix (optional, str, None)
    Prefix of the Shared Product Object Tree (SPOT) NIM resource to use for the VIOS installation.

    The NIM name of the target VIOS is added to find the actual NIM resource, like: "<spot_prefix>_<vios_name>".


  vios_status (optional, dict, None)
    Specifies the result of a previous operation.


  mksysb_prefix (optional, str, None)
    Prefix of the mksysb NIM resource to use for the VIOS installation.

    The NIM name of the target VIOS is added to this prefix to find the actual NIM resource, like: "<mksysb_prefix>_<vios_name>".


  email (optional, str, None)
    Email address to set in the NIM master's /etc/niminfo file if not already set.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Perform a backup of nimvios01
      nim_upgradeios:
        targets: "(nimvios01)"
        action: backup



Return Values
-------------

msg (always, str, )
  Status information.


status (always, dict, )
  Status for each VIOS (dicionnary key).


nim_node (always, dict, )
  NIM node info.


targets (always, list, )
  List of VIOSes.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

