# Ansible Role: nim_alt_disk_migration
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `nim_alt_disk_migration`, which assists in migration of AIX 7.1/7.2 to AIX 7.3.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values:

| Variable           | Suboptions | Required | Default | Choices | Comments |
|--------------------|------------|----------|---------|---------|----------|
| **nim_client**     |            | true     |         |         | Specifies a NIM object name that is associated to the NIM client LPAR to be migrated. |
| **target_disk**    |            | true     |         |         |          |
|                    | **disk_name**  |          |         |         | Specifies the physical volume by name where the alternate disk will be created. |
|                    | **disk_size_policy** |    |         | minimize, upper, lower, nearest | Specifies the disk size policy to automatically determine a valid physical volume that fits the policy where the alternate disk will be created. If an alternate disk named '*altinst_rootvg*' or '*old_rootvg*' exists, the role will fail unless force option is used. |
|                    | **force**  |          | false   |         | If physical volume specified by I(target_disk.disk_name) belongs to 'altinst_rootvg', 'old_rootvg', or a varied on volume group then that physical volume will be cleaned up. If **target_disk.disk_size_policy** is specified and an alternate disk named '*altinst_rootvg*' or '*old_rootvg*' already exists, then it will clean up the physical volume it occupies. |
| **lpp_source**     |            | true     |         |         | Specifies a NIM object name associated to a LPP resource for the desired level of migration. |
| **spot**           |            | false    |         |         | Specifies a NIM object name associated to a SPOT resource associated to the specified **lpp_source**. |
| **reboot_client**  |            | false    | false   |         | Specifies if the NIM client LPAR will be automatically rebooted after successfully creating the alternate disk. |
| **control_phase**  |            | false    |         |         |            |
|                    | **validate_nim_resources** |  | true |    | if set to false, then it will skip validation of NIM resources |
|                    | **perform_migration** |  | true |         | if set to false, then it will skip the actual migration task |

**NOTES**:
- ***minimize*** disk size policy chooses smallest disk that can be selected.
- ***upper*** disk size policy chooses the first disk found bigger than the rootvg disk.
- ***lower*** disk size policy chooses a disk that is less than rootvg disk size but big
enough to contain the used PPs.
- ***nearest*** disk size policy chooses a disk closest to the rootvg disk in terms of size.
- if ***upper*** or ***lower*** cannot be satisfied, it will default to *minimize*.
- if you are using the role to ONLY validate the NIM resources then the **nim_client**
variable is not required.


## Dependencies

None.

## Example Playbook

    - name: Perfrom an alternate disk migration using hdisk1. Let the role build the spot.
      hosts: nim
      gather_facts: no
      tasks:
         - import_role:
              name: nim_alt_disk_migration
           vars:
              nim_client: p9zpa-ansible-test1
              target_disk:
              disk_name: hdisk1
              lpp_source: lpp_2134A_730

## Example Playbook

    - name: Perform an alternate disk migration and let the role choose the disk.
      hosts: nim
      gather_facts: no
      tasks:
         - import_role:
              name: nim_alt_disk_migration
           vars:
              nim_client: p9zpa-ansible-test1
              target_disk:
                 disk_size_policy: minimize
              lpp_source: lpp_2134A_730
              spot: spot_2134A_730

## Example Playbook

    # Useful when migrating multiple nodes concurrently. Use first the role to perform the
    # validation of the resources only once. Then you can migrate the nodes without doing verifications.

    - name: Validate the nim lpp and spot resources and exit the playbook.
      hosts: nim
      gather_facts: no
      tasks:
         - import_role:
              name: nim_alt_disk_migration
           vars:
              lpp_source: lpp_2134A_730
              spot: spot_2134A_730
              control_phases:
                 validate_nim_resources: true
                 perform_migration: false

## Example Playbook

    # Useful when migrating multiple nodes concurrently. The role will prevent the validation of 
    # of the resources and just perform the migration. The role will perform specific validations
    # for the nim client such as connectity, OS level and valid hardware platform for the OS.

    - name: Perform an alternate disk without the lpp or spot resources validation.
    - hosts: nim
      gather_facts: no
      tasks:
         - import_role:
              name: nim_alt_disk_migration
           vars:
              nim_client: p9zpa-ansible-test1
              target_disk:
                 disk_size_policy: minimize
              lpp_source: lpp_2134A_730
              spot: spot_2134A_730
              control_phases:
                 validate_nim_resources: false
                 perform_migration: true

## Example Playbook

    # Useful when adding the migration role into a play for the nim client.
    # Example, the user needs to perform automated actions to the nim client "aix".
    # Then the user wants to include a tasks to perform the nim migration.
    # By using the delegate_to: <nim server> , the tasks will be executed in the nim server.

    - name: Perform a migration but using a play for the nim client not the nim server.
    - hosts: aix
      gather_facts: no
      tasks:
         - import_role:
              name: nim_alt_disk_migration
           vars:
              nim_client: p9zpa-ansible-test1
              target_disk:
                 disk_size_policy: minimize
              lpp_source: lpp_2134A_730
              spot: spot_2134A_730
              control_phases:
                 validate_nim_resources: true
                 perform_migration: true
           delegate_to: nim1.company.com

## Example Playbook

    # For debugging purposes: debug_skip_nimadm: true
    # Similar to modules "check_mode". Useful to execute all the validations and just exit before
    # performing the migration. 

    - name: Preview an alternate disk migration. Exit before running nimadm
    - hosts: nim
      gather_facts: no
      tasks:
         - import_role:
              name: nim_alt_disk_migration
           vars:
              nim_client: p9zpa-ansible-test1
              target_disk:
                 disk_size_policy: minimize
              lpp_source: lpp_2134A_730
              spot: spot_2134A_730
              control_phases:
                 validate_nim_resources: true
                 perform_migration: true
              debug_skip_nimadm: true

## Copyright
© Copyright IBM Corporation 2022
