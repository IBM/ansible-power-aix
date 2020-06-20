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

