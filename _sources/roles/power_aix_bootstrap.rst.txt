.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Ansible Role: power_aix_bootstrap
=================================

Ansible role for automatically loading and executing the commands necessary to
install dependent software for services: yum | python.

Requirements
------------

Openssh

Role Variables
--------------

Available variables along with their default values:

.. code-block:: sh

   pkgtype (True, str, yum)

Specifies the package service requiring bootstrap installation. There are two package names
currently supported:  yum | python.

.. code-block:: sh

   download_dir (optional, str, ~)

Specifies the temporary download location for install scripts and packages. The location resides
on the Ansbile control node. Downloading of the files requires a public network interface connection.

.. code-block:: sh

   target_dir (optional, str, /tmp/.ansible.cpdir)

Specifies the target location (per inventory host) for copying and restoring package files and
metadata. If the target location does not exist, then a temporary filesystem is created using the
target_dir as the mount point.  Upon role completion, the target location is removed.

Dependencies
------------

None.

Example Playbook
----------------

.. code-block:: yaml

   - hosts: aix
     gather_facts: no
     import_role:
       name: power_aix_bootstrap
     vars:
       pkgtype: yum


For more examples, see `playbooks`_.

.. _playbooks:
   https://ibm.github.io/ansible-power-aix/playbooks.html
