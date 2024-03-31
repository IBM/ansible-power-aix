# Ansible Role: nim_alt_disk_migration
The [IBM Power Systems AIX](../../README.md) collection provides an 
[Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), 
referred to as `nim_alt_disk_migration`, which assists in automating in migration in 
migration of AIX 7.1/7.2 to AIX 7.3.

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
            <td><b> nim_alt_disk_migration_nim_client </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies a NIM object name that is associated to the 
                NIM client machine to be migrated.
            </td>
        </tr>
        <tr>
            <td><b> nim_alt_disk_migration_target_disk </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td>  </td>
        </tr>
        <tr>
            <td>  </td>
            <td><b> disk_name </b></td>
            <td>  </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies the physical volume by name where 
                the alternate disk will be created.
            </td>
        </tr>
        <tr>
            <td>  </td>
            <td><b> disk_size_policy </b></td>
            <td>  </td>
            <td>  </td>
            <td>
                minimize,
                upper,
                lower,
                nearest
            </td>
            <td> 
                Specifies the disk size policy to automatically 
                determine a valid physical volume that fits the 
                policy where the alternate disk will be created. 
                If an alternate disk named '<i>altinst_rootvg</i>' or 
                '<i>old_rootvg</i>' exists, the role will fail unless
                force option is used.
            </td>
        </tr>
        <tr>
            <td>  </td>
            <td><b> force </b></td>
            <td>  </td>
            <td> false </td>
            <td>  </td>
            <td> 
                If physical volume specified by <b>nim_alt_disk_migration_target_disk.disk_name</b> 
                belongs to '<i>altinst_rootvg</i>', '<i>old_rootvg</i>', or a 
                varied on volume group then that physical volume will be 
                cleaned up. 
                If <b>nim_alt_disk_migration_target_disk.disk_size_policy</b> is specified and an 
                alternate disk named '<i>altinst_rootvg</i>' or '<i>old_rootvg</i>'
                already exists, then it will clean up the physical volume 
                it occupies.
            </td>
        </tr>
        <tr>
            <td><b> nim_alt_disk_migration_lpp_source  </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies a NIM object name associated to a 
                LPP resource for the desired level of migration.
            </td>
        </tr>
        <tr>
            <td><b> nim_alt_disk_migration_spot  </b></td>
            <td>  </td>
            <td> false </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies a NIM object name associated to a SPOT 
                resource.
            </td>
        </tr>
        <tr>
            <td><b> nim_alt_disk_migration_reboot_client </b></td>
            <td>  </td>
            <td> false </td>
            <td> false </td>
            <td>  </td>
            <td> 
                Specifies if the NIM client LPAR will be 
                automatically rebooted after successfully 
                creating the alternate disk.
            </td>
        </tr>
        <tr>
            <td><b> nim_alt_disk_migration_control_phases </b></td>
            <td>  </td>
            <td> false </td>
            <td>  </td>
            <td>  </td>
            <td>  </td>
        </tr>
        <tr>
            <td>  </td>
            <td><b> validate_nim_resources </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>
                If set to false, then it will skip 
                validation of NIM resources.
            </td>
        </tr>
        <tr>
            <td>  </td>
            <td><b> perform_migration </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>
                If set to false, then it will skip 
                the actual migration task
            </td>
        </tr>
    </tbody>
</table>

**NOTES**:
- ***minimize*** disk size policy chooses smallest disk that can be selected.
- ***upper*** disk size policy chooses the first disk found bigger than the rootvg disk.
- ***lower*** disk size policy chooses a disk that is less than rootvg disk size but big 
enough to contain the used PPs.
- ***nearest*** disk size policy chooses a disk closest to the rootvg disk in terms of size.
- if ***upper*** or ***lower*** cannot be satisfied, it will default to *minimize*.
- if you are using the role to ONLY validate the NIM resources then the **nim_alt_disk_migration_nim_client**
variable is not required.
- if a **nim_alt_disk_migration_spot** is not specified, one will be automatically created using the specified
**nim_alt_disk_migration_lpp_source**.

## Dependencies

None.

## Example Playbook

```
- name: Perfrom an alternate disk migration using hdisk1. Let the role build the SPOT.
    hosts: aix
    gather_facts: no
    tasks:
      - include_role:
          name: nim_alt_disk_migration
        vars:
          nim_alt_disk_migration_nim_client: p9zpa-ansible-test1
          nim_alt_disk_migration_target_disk:
            disk_name: hdisk1
          nim_alt_disk_migration_lpp_source: lpp_2134A_730
```

```
- name: Perform an alternate disk migration and let the role choose the disk.
  hosts: aix
  gather_facts: no
  tasks:
    - include_role:
        name: nim_alt_disk_migration
      vars:
        nim_alt_disk_migration_nim_client: p9zpa-ansible-test1
        nim_alt_disk_migration_target_disk:
          disk_size_policy: minimize
        nim_alt_disk_migration_lpp_source: lpp_2134A_730
        nim_alt_disk_migration_spot: spot_2134A_730
```

```
# Useful when migrating multiple nodes concurrently. Use first the role to perform the
# validation of the resources only once. Then you can migrate the nodes without doing verifications.

- name: Validate the nim lpp and spot resources and exit the playbook.
  hosts: aix
  gather_facts: no
  tasks:
    - include_role:
        name: nim_alt_disk_migration
      vars:
        nim_alt_disk_migration_lpp_source: lpp_2134A_730
        nim_alt_disk_migration_spot: spot_2134A_730
        nim_alt_disk_migration_control_phases:
          validate_nim_resources: true
          perform_nim_migration: false
```

```
# Useful when migrating multiple nodes concurrently. The role will prevent the validation
# of the resources and just perform the migration. The role still will perform specific 
# validations for the nim client such as connectity, OS level and valid hardware platform
# for the OS.

- name: Perform an alternate disk without the lpp or spot resources validation.
  hosts: aix
  gather_facts: no
  tasks:
    - include_role:
        name: nim_alt_disk_migration
      vars:
        nim_alt_disk_migration_nim_client: p9zpa-ansible-test1
        nim_alt_disk_migration_target_disk:
          disk_size_policy: minimize
        nim_alt_disk_migration_lpp_source: lpp_2134A_730
        nim_alt_disk_migration_spot: spot_2134A_730
        nim_alt_disk_migration_control_phases:
          validate_nim_resources: false
          perform_nim_migration: true
```

```
# For debugging purposes: nim_alt_disk_migration_debug_skip_nimadm: true
# Similar to modules "check_mode". Useful to execute all the validations and just exit before
# performing the migration. 

- name: Preview an alternate disk migration. Exit before running nimadm
  hosts: aix
  gather_facts: no
  tasks:
    - include_role:
        name: nim_alt_disk_migration
      vars:
        nim_alt_disk_migration_nim_client: p9zpa-ansible-test1
        nim_alt_disk_migration_target_disk:
          disk_size_policy: minimize
        nim_alt_disk_migration_lpp_source: lpp_2134A_730
        nim_alt_disk_migration_spot: spot_2134A_730
        nim_alt_disk_migration_control_phases:
          validate_nim_resources: true
          perform_nim_migration: true
        nim_alt_disk_migration_debug_skip_nimadm: true
```

## Copyright
© Copyright IBM Corporation 2022
