# Ansible Role: alt_disk_migration
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `alt_disk_migration`, which automatically loads and executes commands to install dependent software.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values:

	nim_client (required)

Specifies a NIM object name that is associated to the NIM client LPAR to be migrated.

	target_disk (required)

Specifies the physical volume where the alternate disk will be created in the NIM client LPAR.

    lpp_source (required)

Specifies a NIM object name associated to a LPP resource for the desired level of migration.

	spot (required)

Specifies a NIM object name associated to a SPOT resource associated to the specified 
I(lpp_source).

## Dependencies

None.

## Example Playbook

    - hosts: aix
      gather_facts: no
      include_role:
        name: nim_alt_disk_migration
      vars:
		nim_client: p9zpa-ansible-test1
		pv: hdisk1
		lpp_source: lpp_2134A_730

## Copyright
© Copyright IBM Corporation 2021
