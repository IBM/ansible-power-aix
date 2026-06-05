# Ansible Role: ipsec
The [IBM Power Systems AIX](../../README.md) collection provides an 
[Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), 
referred to as `ipsec`, which assists in automating ipsec tunnel management.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

- AIX 7.1 or later
- Root or sudo access
- IPsec subsystem installed on AIX
- Valid IPsec configuration XML file

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
            <td><b> Suboptions </b></td>
            <td><b> Required </b></td>
            <td><b> Default </b></td>
            <td><b> Choices </b></td>
            <td><b> Comments </b></td>
        </tr>
        <tr>
            <td><b> ipsec_action </b></td>
            <td>  </td>
            <td> true </td>
            <td> status </td>
            <td> on, off, status </td>
            <td> 
                Action to perform: bringup the tunnel, bring down the tunnel, get tunnel status on a system
            </td>
        </tr>
        <tr>
            <td><b> ipsec_config_file </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td>
                Location of th IPsec configuration file path, where all the details are present.
            </td>
        </tr>
        <tr>
            <td><b> ipsec_ike_service_group </b></td>
            <td>  </td>
            <td> false </td>
            <td> ike </td>
            <td>  </td>
            <td> 
                IKE service group name.
            </td>
        </tr>
        <tr>
            <td><b> ipsec_ike_start_wait </b></td>
            <td>  </td>
            <td> false </td>
            <td> 5 </td>
            <td>  </td>
            <td> 
                Wait time after starting IKE service (seconds)
            </td>
        </tr>
        <tr>
            <td><b> ipsec_ike_activate_wait </b></td>
            <td>  </td>
            <td> false </td>
            <td> 5 </td>
            <td>  </td>
            <td> 
                Wait time after activating tunnel (seconds).
            </td>
        </tr>
    </tbody>
</table>

**NOTES**: 
- ***ipsec_action*** needs to be set to "up", when you want to create an ipsec tunnel on a system.
- ***ipsec_action*** needs to be set to "down", when you want to tear down an ipsec tunnel on a system.
- ***ipsec_action*** needs to be set to "status", when you want to check the status of ipsec tunnel(s) in a system.
- You need to set the ***ipsec_ike_start_wait*** and ***ipsec_ike_activate_wait*** values based on your environment, the default is set to 5 seconds.

## Dependencies

None

## Example Playbook

```
- name: Setup IPsec tunnel between machine a and b
  hosts: machine_a, machine_b
  gather_facts: false
  vars:
    ipsec_action: "up"
    ipsec_config_file: "/tmp/ipsec/ipsec.xml"
    ike_service_group: "ike"
    ike_start_wait: 5
    ike_activate_wait: 5
```

```
- name: Tear down IPsec tunnel between machine a and b
  hosts: machine_a, machine_b
  gather_facts: false
  vars:
    ipsec_action: "down"
    ipsec_config_file: "/tmp/ipsec/ipsec.xml"
    ike_service_group: "ike"
    ike_start_wait: 5
    ike_activate_wait: 5
```

```
- name: Verify IPsec tunnel status on both machines
  hosts: machine_a,machine_b
  gather_facts: false
  vars:
    ipsec_action: "status"
  
  tasks:
    - name: Check IPsec tunnel status
      ansible.builtin.include_role:
        name: ibm.power_aix.ipsec
```
## Copyright
© Copyright IBM Corporation 2022