.. _mktcpip_module:


mktcpip -- Sets the required values for starting TCP/IP on a host
=================================================================

.. contents::
   :local:
   :depth: 1


Synopsis
--------

This module sets the required minimal values required for using TCP/IP on a host machine.

These values are written to the configuration database.



Requirements
------------
The below requirements are needed on the host that executes this module.

- AIX >= 7.1 TL3
- Python >= 2.7



Parameters
----------

  domain (optional, str, None)
    Specifies the domain name of the name server the host should use for name resolution.


  hostname (True, str, None)
    Sets the name of the host.


  netmask (optional, str, None)
    Specifies the mask the gateway should use in determining the appropriate subnetwork for routing.


  address (True, str, None)
    Sets the Internet address of the host.


  interface (True, str, None)
    Specifies a particular network interface.


  nameserver (optional, str, None)
    Specifies the Internet address of the name server the host uses for name resolution.


  gateway (optional, str, None)
    Adds the default gateway address to the routing table.


  start_daemons (optional, bool, False)
    Starts the TCP/IP daemons.









Examples
--------

.. code-block:: yaml+jinja

    
    - name: Set the required values for starting TCP/IP
      mktcpip:
        hostname: fred.austin.century.com
        address: 192.9.200.4
        interface: en0
        nameserver: 192.9.200.1
        domain: austin.century.com
        start_daemons: yes



Return Values
-------------

msg (always, str, Command 'mktcpip -h quimby01.aus.stglabs.ibm.com -a 9.3.149.150 -i en1' successful.)
  The execution message.


stderr (always, str, en1\n x.x.x.x is an invalid address.\n /usr/sbin/mktcpip: Problem with command: hostent, return code = 1\n)
  The standard error.


stdout (always, str, en1\n quimby01.aus.stglabs.ibm.com\n inet0 changed\n en1 changed)
  The standard output.





Status
------




- This module is not guaranteed to have a backwards compatible interface. *[preview]*


- This module is maintained by community.



Authors
~~~~~~~

- AIX Development Team (@pbfinley1911)

