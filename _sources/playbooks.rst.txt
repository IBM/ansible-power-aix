.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Playbooks
=========

The sample playbooks that are **included** in the **IBM Power Systems AIX collection**
demonstrate how to use the collection content.

Playbook Documentation
----------------------

An `Ansible playbook`_ consists of organized instructions that define work for
a managed node (host) to be managed with Ansible.

A `playbooks directory`_ that contains a sample playbook is included in the
**IBM Power Systems AIX collection**. The sample playbook can be run with the
``ansible-playbook`` command with some modification to the **inventory**
and **group_vars**.

You can find the playbook content that is included with the collection in the
same location where the collection is installed. For more information, refer to
the `installation documentation`_. In the following examples, this document will
refer to the installation path as ``~/.ansible/collections/ansible_collections/ibm/power_aix``.

.. _Ansible playbook:
   https://docs.ansible.com/ansible/latest/user_guide/playbooks_intro.html#playbooks-intro
.. _playbooks directory:
   https://github.com/IBM/ansible-power-aix/tree/dev-collection/playbooks
.. _installation documentation:
   installation.html


Sample Configuration and Setup
------------------------------
Each release of Ansible provides options in addition to the ones identified in
the sample configurations that are included with this collection. These options
allow you to customize how Ansible operates in your environment. Ansible
supports several sources to configure its behavior and all sources follow the
Ansible `precedence rules`_.

The Ansible configuration file `ansible.cfg` can override almost all
``ansible-playbook`` configurations.

You can specify the SSH port used by Ansible and instruct Ansible where to
write the temporary files on the target. This can be easily done by adding the
options to your inventory or `ansible.cfg`.

For more information about available configurations for ``ansible.cfg``, read
the Ansible documentation on `Ansible configuration settings`_.


.. _precedence rules:
   https://docs.ansible.com/ansible/latest/reference_appendices/general_precedence.html#general-precedence-rules
.. _Ansible configuration settings:
   https://docs.ansible.com/ansible/latest/reference_appendices/config.html#ansible-configuration-settings-locations

Inventory
---------

Ansible works with multiple managed nodes (hosts) at the same time, using a
list or group of lists known as an `inventory`_. Once the inventory is defined,
you can use `patterns`_ to select the hosts or groups that you want Ansible to
run against.

Included in the `playbooks directory`_ is a `sample inventory file`_ that can be
used to manage your nodes with a little modification. This inventory file
should be included when running the sample playbook.

.. code-block:: yaml

   nimserver:
     hosts:
       nim:
         ansible_host: aix_target_address
         ansible_user: aix_target_username
         ansible_python_interpreter: path_to_python_interpreter_binary_on_aix_target


The value for the property **ansible_host** is the hostname of the managed node;
for example, ``ansible_host: regency.aus.stglabs.ibm.com``

The value for the property **aix_target_username** is the user name to use when
connecting to the host; for example, ``ansible_user: padmin``.

The value for the property **ansible_python_interpreter** is the target host
Python path. This is useful for systems with more than one Python installation,
or when Python is not installed in the default location **/usr/bin/python**;
for example, ``ansible_python_interpreter: /usr/lpp/rsusr/python36/bin/python``

.. _inventory:
   https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
.. _patterns:
   https://docs.ansible.com/ansible/latest/user_guide/intro_patterns.html#intro-patterns
.. _sample inventory file:
   https://github.com/IBM/ansible-power-aix/blob/dev-collection/playbooks/inventory.yml


Group_vars
----------

Although you can store variables in the inventory file, storing separate host
and group variables files may help you organize your variable values more
easily. Included with the sample playbook are sample variables files `all.yml`_
and `nimserver.yml`_.

.. _all.yml:
   https://github.com/IBM/ansible-power-aix/blob/dev-collection/playbooks/group_vars/all.yml

.. _nimserver.yml:
   https://github.com/IBM/ansible-power-aix/blob/dev-collection/playbooks/group_vars/nimserver.yml



Run the playbooks
-----------------

The sample playbooks must be run from the `playbooks directory`_ of the installed
collection: ``~/.ansible/collections/ansible_collections/ibm/power_aix/playbooks/``.

Access the sample Ansible playbook and ensure that you are within the collection
playbooks directory where the sample files are included:
``~/.ansible/collections/ansible_collections/ibm/power_aix/playbooks/``.

Use the Ansible command ``ansible-playbook`` to run the sample playbooks.  The
command syntax is ``ansible-playbook -i <inventory> <playbook>``; for example,
``ansible-playbook -i inventory demo_flrtvc.yml``.

This command assumes that the controller's public SSH key has been shared with
the managed node. If you want to avoid entering a username and password each
time, copy the SSH public key to the managed node using the ``ssh-copy-id``
command; for example, ``ssh-copy-id -i ~/.ssh/mykey.pub user@<hostname>``.

Alternatively, you can use the ``--ask-pass`` option to be prompted for the
user's password each time a playbook is run; for example,
``ansible-playbook -i inventory demo_flrtvc.yml --ask-pass``.

.. note::
   * Using ``--ask-pass`` is not recommended because it will hinder performance.
   * Using ``--ask-pass`` requires ``sshpass`` be installed on the controller.
     For further reference, see the `ask-pass documentation`_.

Optionally, you can configure the console logging verbosity during playbook
execution. This is helpful in situations where communication is failing and
you want to obtain more details. To adjust the logging verbosity, append more
letter `v`'s; for example, `-v`, `-vv`, `-vvv`, or `-vvvv`.

Each letter `v` increases logging verbosity similar to traditional logging
levels INFO, WARN, ERROR, DEBUG.

.. note::
   It is a good practice to review the playbook samples before executing them.
   It will help you understand what requirements in terms of space, location,
   names, authority, and artifacts will be created and cleaned up. Although
   samples are always written to operate without the need for the user's
   configuration, flexibility is written into the samples because it is not
   easy to determine if a sample has access to the host's resources.
   Review the playbook notes sections for additional details and
   configuration.

.. _playbooks directory:
   https://github.com/IBM/ansible-power-aix/tree/dev-collection/playbooks

.. _ask-pass documentation:
   https://linux.die.net/man/1/sshpass



Log and debug
-------------

The **IBM Power Systems AIX collection** uses the standard Ansible log system
that is using the syslog subsystem on the managed nodes.

To activate AIX syslog you can update the configuration file `/etc/syslog.conf`
with a selector `user.info` (or `user.debug` for more details) such as:

.. code-block:: sh

   $ vi /etc/syslog.conf
   user.info /var/log/syslog.user.info rotate size 1m files 4 compress

and restarting syslogd subsystem and look for Ansible logs:

.. code-block:: sh

   $ >/var/log/syslog.user.info
   $ refresh -s syslogd

   $ grep ansible /var/log/syslog.user.info
   May  6 03:28:27 nimmaster user:info ansible-nim: Invoked with resource=None force=False description=None script=damien_script lpp_source=None action=script asynchronous=True location=None device=None group=None operation=None targets=['nimclient01']
   May  6 03:28:27 nimmaster user:info ansible-nim: *** START ***
   ...

To see the full debug log messages you should set the selector field to
`user.debug` and run the playbook with the environment variable
`ANSIBLE_DEBUG=1`

.. code-block:: sh

   $ vi /etc/syslog.conf
   user.debug /var/log/syslog.user.debug rotate size 1m files 4 compress
   $ >/var/log/syslog.user.debug
   $ refresh -s syslogd
   $ ANSIBLE_DEBUG=1 ansible-playbook -M plugins/modules ./demo_nim.yml -vvv

