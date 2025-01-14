# Ansible Role: live_kernel_update
The [IBM Power Systems AIX](../../README.md) collection provides an 
[Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), 
referred to as `live_kernel_update`, which assists in automating live kernel update 
on AIX systems running version 7.2 or higher.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

Minimum AIX version supported is 7.2.

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
            <td><b> live_kernel_update_hmc_name </b></td>
            <td>  </td>
            <td> false </td>
            <td> empty string </td>
            <td>  </td>
            <td> 
                Specifies HMC hostname in case the operation is
                not running in preview mode.
            </td>
        </tr>
        <tr>
            <td><b> live_kernel_update_hmc_password </b></td>
            <td>  </td>
            <td> false </td>
            <td> empty string </td>
            <td>  </td>
            <td>
                Specifies the HMC password for authentication purpose.
                For security purposes, it is highly recommended to store this
                sensitive information in an encrypted secret vault file.
            </td>
        </tr>
        <tr>
            <td><b> live_kernel_update_preview_mode </b></td>
            <td>  </td>
            <td> false </td>
            <td> true </td>
            <td>  </td>
            <td> 
                If true, the LKU operation will only run in preview mode
                and no fixes will be applied. It is highly recommended that
                user should first run this operation in preview mode.
            </td>
        </tr>
        <tr>
            <td> <b> live_kernel_update_directory </b> </td>
            <td> </td>
            <td> false </td>
            <td> empty string </td>
            <td> </td>
            <td> 
                Specifies the source directory of the fixes.
            </td>
        </tr>
        <tr>
            <td><b> live_kernel_update_file_name  </b></td>
            <td>  </td>
            <td> false </td>
            <td> all </td>
            <td>  </td>
            <td> 
                Specifies the space separated name of the fixes in the provided
                directory. If not specified, all the fix sources would be applied.
            </td>
        </tr>
    </tbody>
</table>

**NOTES**:
- AIX version should should be 7.2 or higher.
- /var/adm/ras/liveupdate/lvupdate.data file is created and has all the necessary details of attributes and stanza
- Refer [LKU documentation](https://www.ibm.com/docs/sr/aix/7.2?topic=updates-live-update) for additional information
related to live kernel update using HMC.

## Dependencies

None.

## Example Playbook

```
- name: Perfrom a LKU operation in preview mode
    hosts: aix
    gather_facts: no
    tasks:
      - include_role:
          name: live_kernel_update
        vars:
          live_kernel_update_directory: /tmp/source
          live_kernel_update_file_name: IZ12345.140806.epkg.Z
```

```
- name: Perform actual LKU operation
  hosts: aix
  gather_facts: no
  tasks:
    - include_role:
        name: live_kernel_update
      vars:
        live_kernel_update_hmc_name: test1.hmc.hostname
        live_kernel_update_hmc_password: password123
        live_kernel_update_directory: /tmp/source
        live_kernel_update_file_name: IZ12345.140806.epkg.Z
        live_kernel_update_preview_mode: false
```

## Copyright
© Copyright IBM Corporation 2022
