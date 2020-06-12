.. _nim_viosupgrade_module:


nim_viosupgrade -- Perform an upgrade with the viosupgrade tool
===============================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Tool to upgrade VIOSes in NIM environment.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  skip_rootvg_cloning (optional, dict, None)
    Skip rootvg cloning.


  res_resolv_conf (optional, dict, None)
    NIM resolv_conf resource name.


  res_script (optional, dict, None)
    NIM script resource name.


  res_image_data (optional, dict, None)
    NIM image_data resource name.


  rootvg_clone_disk (optional, dict, None)
    Clone disk name.


  cluster_exists (optional, dict, None)
    Check if cluster exists.


  rootvg_install_disk (optional, dict, None)
    Install disk name.


  mksysb_name (optional, dict, None)
    mksysb name.


  targets (optional, list, None)
    NIM targets.


  target_file_name (optional, str, None)
    File name containing NIM targets in CSV format.


  res_fb_script (optional, dict, None)
    NIM fb_script resource name.


  vars (optional, dict, None)
    Specifies additional parameters.


  res_log (optional, dict, None)
    NIM log resource name.


  res_file_res (optional, dict, None)
    NIM file_res resource name.


  validate_input_data (optional, dict, None)
    Validate input data.


  action (True, str, None)
    Specifies the operation to perform.

    ``altdisk_install`` to perform and alternate disk install.

    ``alt_disk_clean`` to cleanup an existing alternate disk install.

    ``get_status`` to get the status of the upgrade.


  vios_status (optional, dict, None)
    Specifies the result of a previous operation.


  spot_name (optional, dict, None)
    SPOT name.


  backup_file (optional, dict, None)
    Backup file name.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Perform an upgrade of nimvios01
      nim_viosupgrade:
        targets: nimvios01
        action: altdisk_install



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

