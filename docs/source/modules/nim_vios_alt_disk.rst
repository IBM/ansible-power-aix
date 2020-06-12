.. _nim_vios_alt_disk_module:


nim_vios_alt_disk -- Create/Cleanup an alternate rootvg disk
============================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Copy the rootvg to an alternate disk or cleanup an existing one.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  time_limit (optional, str, None)
    Before starting the action, the actual date is compared to this parameter value; if it is greater then the task is stopped; the format is ``mm/dd/yyyy hh:mm``.


  nim_node (optional, dict, None)
    Allows to pass along NIM node info from a task to another so that it discovers NIM info only one time for all tasks.


  force (optional, bool, False)
    Forces action.


  vars (optional, dict, None)
    Specifies additional parameters.


  disk_size_policy (optional, str, nearest)
    Specifies how to choose the alternate disk if not specified.

    ``minimize`` smallest disk that can be selected.

    ``upper`` first disk found bigger than the rootvg disk.

    ``lower`` disk size less than rootvg disk size but big enough to contain the used PPs.

    ``nearest``


  action (True, str, None)
    Specifies the operation to perform on the VIOS.

    ``alt_disk_copy`` to perform and alternate disk copy.

    ``alt_disk_clean`` to cleanup an existing alternate disk copy.


  vios_status (optional, dict, None)
    Specifies the result of a previous operation.


  targets (True, list, None)
    NIM VIOS target.

    Use a tuple format with the 1st element the VIOS and the 2nd element the disk used for the alternate disk copy. "vios1,disk1,vios2,disk2" for dual VIOSes. "vios1,disk1" for single VIOS.





Notes
-----

.. note::
   - ``alt_disk_copy`` only backs up mounted file systems. Mount all file systems that you want to back up.
   - copy is performed only on one alternate hdisk even if the rootvg contains multiple hdisks
   - error if several ``altinst_rootvg`` exist for cleanup operation in automatic mode




Examples
--------

.. code-block:: yaml+jinja

    
    - name: Perform an alternate disk copy of the rootvg to hdisk1
      nim_vios_alt_disk:
        action: alt_disk_copy
        targets:
        - nimvios01,hdisk1

    - name: Perform an alternate disk copy of the rootvg to the smallest disk that can be selected
      nim_vios_alt_disk:
        action: alt_disk_copy
        disk_size_policy: minimize
        targets:
        - nimvios01,,nimvios02,
        - nimvios03,



Return Values
-------------

msg (always, str, )
  Status information.


status (always, dict, )
  Status for each VIOS (dicionnary key).


nim_node (always, dict, )
  NIM node info.


targets (always, list, )
  List of VIOS tuples.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

