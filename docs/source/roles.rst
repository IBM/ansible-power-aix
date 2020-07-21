.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

Roles
=====

The **IBM Power Systems AIX collection** contains roles that can be used in a playbook
to automate tasks on AIX. Ansible executes each role, usually on the remote target node,
and collects return values.

Roles in Ansible build on the idea of include files and combine them to form clean,
reusable abstractions. While different roles perform different tasks, their interfaces
and responses follow similar patterns.

Role reference
--------------

Reference material for each role contains documentation on what parameters certain roles
accept and what values they expect those parameters to be.

.. toctree::
   :maxdepth: 1
   :caption: Contents:
   :glob:

   roles/*

