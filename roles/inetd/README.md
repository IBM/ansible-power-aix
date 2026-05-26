# Ansible Role: inetd
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `inetd`, which can be used to enable or disable inetd services, including ftpd, rlogind, rexecd, rshd, telnetd.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values:

<table>
    <thead>
        <tr>
            <th colspan="6"> Role Variables </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b> Variable </b></td>
            <td><b> Options </b></td>
            <td><b> Required </b></td>
            <td><b> Default </b></td>
            <td><b> Choices </b></td>
            <td><b> Comments </b></td>
        </tr>
        <tr>
            <td><b> inetd_services </b></td>
            <td>  </td>
            <td> false </td>
            <td> empty string </td>
            <td>  </td>
            <td> 
                Specifies a list of inetd services to enable or disable.
            </td>
        </tr>
        <tr>
            <td><b> inetd_state </b></td>
            <td>  </td>
            <td> false </td>
            <td> enabled </td>
            <td>  </td>
            <td>
                Specifies to enable or disable the services.
            </td>
        </tr>
        <tr>
            <td><b> inetd_backup </b></td>
            <td>  </td>
            <td> false </td>
            <td> false </td>
            <td>  </td>
            <td> 
                Specifies to back up the /etc/inetd.conf file.
            </td>
        </tr>
    </tbody>
</table>

**NOTES**:
- Refer to the [inetd.conf File Format for TCP/IP](https://www.ibm.com/docs/en/aix/7.3.0?topic=formats-inetdconf-file-format-tcpip) for additional information.

## Dependencies

None.

## Example Playbook

```
- name: Disable talk/ntalk, telnet and xmquery
  ansible.builtin.include_role:
    name: ibm.power_aix.inetd
  vars:
    inetd_services:
      - talk
      - ntalk
      - telnet
      - xmquery
    inetd_state: disabled
    inetd_backup: yes
```

## Copyright
© Copyright IBM Corporation 2026
