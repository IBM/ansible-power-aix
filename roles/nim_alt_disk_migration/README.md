# Ansible Role: alt_disk_migration
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `alt_disk_migration`, which automatically loads and executes commands to install dependent software.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values:

	nim_client (required)

Specifies the NIM client object that represent the LPAR to be migrated.

	pv (required)

Specifies the physical volume where the alternate disk will be created.

    lpp_source (required)

Specifies the NIM LPP resource to use for migration.

	spot (required)

Specifies the NIM SPOT resource to use for migration.

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
		spot: spot_2134A_730

## Copyright
© Copyright IBM Corporation 2021
