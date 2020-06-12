.. _nim_updateios_module:


nim_updateios -- Update a single or a pair of Virtual I/O Servers
=================================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Performs updates and customization to the Virtual I/O Server (VIOS).



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


  filesets (optional, str, None)
    Specifies a list of file sets to remove from the target.


  vars (optional, dict, None)
    Specifies additional parameters.


  lpp_source (optional, str, None)
    Identifies the *lpp_source* resource that will provide the installation images for the operation.


  installp_bundle (optional, str, None)
    Specifies an *installp_bundle* resource that lists file sets to remove on the target.


  action (True, str, None)
    Operation to perform on the targets.

    ``install``.

    ``commit``.

    ``reject``.

    ``cleanup``.

    ``remove``.


  preview (optional, str, None)
    Specifies a preview operation.


  accept_licenses (optional, str, None)
    Specifies whether the software licenses should be automatically accepted during the installation.


  vios_status (optional, dict, None)
    Specifies the result of a previous operation.


  log_file (optional, str, None)
    Specifies path to log file.


  targets (True, str, None)
    NIM targets.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Update a pair of VIOSes
      nim_updateios:
        targets: "(nimvios01, nimvios02)"
        action: install
        lpp_source: /lpp_source



Return Values
-------------

msg (always, str, NIM updateios operation completed successfully)
  The execution message.


output (always, str, )
  output of executed commands.


status (always, dict, { vios01: 'SUCCESS-UPDT', vios02: 'SUCCESS-ALTDC' })
  The execution message.


  <target> (when target is actually a NIM client, str, SUCCESS-UPDT)
    Status of the execution on the <target>.



targets (always, str, [nimclient01, nimclient02, ...])
  The execution message.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

