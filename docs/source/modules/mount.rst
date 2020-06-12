.. _mount_module:


mount -- Makes a file system available for use
==============================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

This module makes a file system available for use at a specified location.

Builds other file trees made up of directory and file mounts.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  read_only (optional, bool, False)
    Mounts a file system as a read-only file system


  mount_dir (optional, str, None)
    Directory path to be mounted.


  mount_over_dir (optional, str, None)
    Directory path on which the mount_dir should be mounted.


  vfsname (optional, str, None)
    Specifies that the file system is defined by the vfsname parameter in the /etc/vfs file


  fs_type (optional, str, None)
    Mounts all stanzas in the /etc/filesystems file that contain the type=fs_type attribute


  alternate_fs (optional, str, None)
    Mounts on a file of an alternate file system, other than the /etc/file systems file


  options (optional, str, None)
    Specifies options. Options should be of the form <option-name>=<value> and multiple options should be separated only by a comma.


  mount_all (optional, bool, False)
    Mounts all file systems in the /etc/filesystems file with stanzas that contain the true mount attribute


  removable_fs (optional, bool, False)
    Mounts a file system as a removable file system









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Specify the filesystems to be mounted
      mount:
        mount_dir=/dev/hd1
        mount_over_dir=/home



Return Values
-------------

msg (always, str, Command 'mount myfs' failed with return code 1)
  The execution message.


stderr (always, str, mount: myfs is not a known file system)
  The standard error.


stdout (always, str,   node       mounted        mounted over    vfs       date        options      \n -------- ---------------  ---------------  ------ ------------ --------------- \n /dev/hd4         /                jfs2   Jun 09 04:37 rw,log=/dev/hd8 \n /dev/hd2         /usr             jfs2   Jun 09 04:37 rw,log=/dev/hd8 \n /dev/hd9var      /var             jfs2   Jun 09 04:37 rw,log=/dev/hd8 \n /dev/hd3         /tmp             jfs2   Jun 09 04:37 rw,log=/dev/hd8 \n /dev/hd1         /home            jfs2   Jun 09 04:38 rw,log=/dev/hd8 \n /dev/hd11admin   /admin           jfs2   Jun 09 04:38 rw,log=/dev/hd8 \n /proc            /proc            procfs Jun 09 04:38 rw              \n /dev/hd10opt     /opt             jfs2   Jun 09 04:38 rw,log=/dev/hd8 \n /dev/fslv01      /tftpboot        jfs2   Jun 09 04:38 rw,log=/dev/hd8 \n)
  The standard output.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

