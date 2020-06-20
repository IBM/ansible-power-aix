.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Requirements
============

A control node is any machine with Ansible installed. From the control node,
you can run commands and playbooks from a laptop, desktop, or server.
However, you cannot run **IBM Power Systems AIX collection** on a Windows system.

A managed node is often referred to as a target node, or host, and it is managed
by Ansible. Ansible is not required on a managed node, but SSH must be enabled.

The nodes listed below require these specific versions of software:

Control node
------------

* `Ansible version`_: 2.9 or later
* `Python`_: 2.7 or later
* `OpenSSH`_

.. _Ansible version:
   https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html
.. _Python:
   https://www.python.org/downloads/release/latest
.. _OpenSSH:
   https://www.openssh.com/


Managed node
------------

* `Python on AIX`_: 2.7 or later
* `AIX OS`_: 7.1 or later
* `AIX OpenSSH`_

.. _Python on AIX:
   https://www.ibm.com/support/pages/aix-toolbox-linux-applications-overview

.. _AIX OS:
   https://www.ibm.com/it-infrastructure/power/os/aix

.. _AIX OpenSSH:
   https://www.ibm.com/support/pages/downloading-and-installing-or-upgrading-openssl-and-openssh

Python on AIX
--------------

AIX® Toolbox for Linux® Applications contains a collection of open source
and GNU software built for IBM Power Systems AIX (including Python).

These tools provide the basis of the development environment of choice for
many Linux application developers. All the tools are packaged using the
easy to install RPM format.

**Download information**

* This software is offered on an "as-is" basis. Refer to the
  `licensing and information instructons`_ for further information.
* These packages are available for installation using the rpm package
  manager. Download the `AIX install image for the rpm package manager for POWER`_.
* For further information, installation tips, and news, please refer to
  the `AIX Toolbox for Linux Applications ReadMe`_.

.. _licensing and information instructons:
   https://www.ibm.com/support/pages/node/883794
.. _AIX install image for the rpm package manager for POWER:
   https://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/INSTALLP/ppc/rpm.rte
.. _AIX Toolbox for Linux Applications ReadMe:
   https://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/README.txt

