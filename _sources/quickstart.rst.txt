.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Quickstart
==========

After installing the collection outlined in the  `installation`_ guide, you
can access the collection and the ansible-doc covered in the following topics:

.. _installation:
   installation.html

ibm.power_aix
--------------

After the collection is installed, you can access the collection content for a
playbook by referencing the namespace ``ibm`` and the collection's fully
qualified name ``power_aix``. For example:

.. code-block:: yaml

    - hosts: all

    tasks:
    - name: Query and install latest updates
      ibm.power_aix.suma:
          oslevel: 'latest'


In Ansible 2.9, the ``collections`` keyword was added to reduce the need
to refer to the collection repeatedly. For example, you can use the
``collections`` keyword in your playbook:

.. code-block:: yaml

    - hosts: all
      collections:
      - ibm.power_aix

    tasks:
    - name: Query and install latest updates
      suma:
          oslevel: 'latest'

ansible user
------------

Some modules included in this collection perform privileged operations. Only
authorized users can run privileged operations.
It is recommended to create an ``ansible`` user with a the proper roles on the
system.

For example the ``alt_disk`` module runs ``alt_disk_copy`` and
``alt_rootvg_op`` commands that require ``aix.system.install`` authorization,
and ``chpv`` command that requires ``aix.lvm.manage.change`` authorization.

You can get the list of commands run as part of the ``alt_disk`` module with:

.. code-block:: shell-session

   # awk -F\' '/cmd =/ {print $2}' .ansible/collections/ansible_collections/ibm/power_aix/plugins/modules/alt_disk.py | sort -u

Then on your managed node running AIX, you can use the following to define an
``ansible_backup`` role with the proper authorizations and create an
``ansible`` user owning this role:

.. code-block:: shell-session

   # cmds="alt_disk_copy getconf lquerypv lspv lsvg /usr/sbin/alt_rootvg_op /usr/sbin/chpv"
   # for cmd in $cmds; do lssecattr -c `which $cmd`; done
   # mkrole authorizations=aix.system.install,aix.lvm.manage.change dfltmsg="Ansible Role for bakcup" ansible_backup
   # mkuser roles=ansible_backup default_roles=ansible_backup ansible
   # setkst

Note that the ``mkrole`` command is itself a privileged command. Hence you
must assume a role that has the ``aix.security.role.create`` authorization to
run the command successfully.

To connect to the endpoint using this ``ansible`` user, specify
``user: ansible`` in the playbook or ``ansible_user=ansible`` in the
inventory.

For more information on using authorizations and privileges, refer to the
`IBM RBAC documentation`_.

When a user is not authorized to run a privileged operations, it will get a
error message such as: ``alt_disk_copy: cannot execute``.


ansible-doc
-----------

Modules included in this collection provide additional documentation that is
similar to a UNIX-like operating system man page (manual page). This
documentation can be accessed from the command line by using the
``ansible-doc`` command.

Here's how to use the ``ansible-doc`` command after you install the
**IBM Power Systems AIX collection**: ``ansible-doc ibm.power_aix.suma``

.. code-block:: sh

    > SUMA    (/Users/user/.ansible/collections/ansible_collections/ibm/power_aix/plugins/modules/suma.py)

        Creates a task to automate the download and installation of
        technology level (TL) and service packs (SP) from a fix server
        using the Service Update Management Assistant (SUMA).

    * This module is maintained by The Ansible Community
    OPTIONS (= is mandatory):


For more information on using the ``ansible-doc`` command, refer
to the `Ansible guide`_.

.. _Ansible guide:
   https://docs.ansible.com/ansible/latest/cli/ansible-doc.html#ansible-doc

.. _IBM RBAC documentation:
   https://www.ibm.com/support/knowledgecenter/ssw_aix_72/security/rbac.html
