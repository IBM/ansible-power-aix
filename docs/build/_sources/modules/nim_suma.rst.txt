.. _nim_suma_module:


nim_suma -- Download fixes, SP or TL on an AIX server
=====================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

Creates a task to automate the download of technology level (TL) and service pack (SP) from a fix server using the Service Update Management Assistant (SUMA). It can create the NIM resource.

Log file is /var/adm/ansible/nim_suma_debug.log.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  description (optional, str, None)
    Display name for SUMA task.

    If not set the will be labelled '*action* request for oslevel *oslevel*'

    Can be used for *action=download* or *action=preview*.


  download_only (optional, bool, False)
    Download only. Do not create the NIM resource.

    Can be used if *action=download*


  lpp_source_name (optional, str, None)
    Name of the lpp_source NIM resource.

    Required when *action=download* or *action=preview*.


  extend_fs (optional, bool, True)
    Specifies to automatically extends the filesystem if needed. If no is specified and additional space is required for the download, no download occurs.

    Can be used if *action=download* or ``action=preview``.


  oslevel (optional, str, Latest)
    Specifies the Operating System level to update to;

    ``Latest`` indicates the latest SP suma can update the targets to.

    ``xxxx-xx(-00-0000``) sepcifies a TL.

    ``xxxx-xx-xx-xxxx`` or ``xxxx-xx-xx`` specifies a SP.

    Required when *action=download* or *action=preview*.


  download_dir (optional, path, None)
    Absolute directory path where to download the packages on the NIM server.

    If not set it looks for existing NIM ressource matching *lpp_source_name* and use its location.

    If no NIM ressource is found, the path is set to /usr/sys/inst.images

    Can be used if *action=download* or ``action=preview``.


  action (optional, str, preview)
    Controls what is performed.

    ``download`` to download fixes and define the NIM resource.

    ``preview``  to execute all the checks without downloading the fixes.


  metadata_dir (optional, path, /var/adm/ansible/metadata)
    Directory where metadata files are downloaded.

    Can be used if *action=download* or ``action=preview`` when *oslevel* is not exact, for example *oslevel=Latest*.


  targets (True, list, None)
    Specifies the NIM clients to perform the action on.

    ``foo*`` designates all the NIM clients with name starting by ``foo``.

    ``foo[2:4]`` designates the NIM clients among foo2, foo3 and foo4.

    ``*`` or ``all`` designates all the NIM clients.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Check for, and install, system updates
      nim_suma:
        action: download
        targets: nimclient01
        oslevel: latest
        download_dir: /usr/sys/inst.images



Return Values
-------------

msg (always, str, Suma preview completed successfully)
  Status information.


lpp_source_name (always, str, quimby01_lpp_source)
  Name of the NIM Lpp Source resource used.


meta (always, dict, {'meta': {'messages': ['Unavailable client: nimclient02', 'The latest SP of 7200-02 is: 7200-02-01-1732', '...']}})
  Detailed information on the module execution.


  messages (always, list, Unavailable client: nimclient02)
    Details on errors/warnings/inforamtion



target_list (always, list, ['nimclient01', 'nimclient02', '...'])
  Status information.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

