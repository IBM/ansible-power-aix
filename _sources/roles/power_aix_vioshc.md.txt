# Ansible Role: power_aix_vioshc
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `power_aix_vioshc`, which installs a Virtual I/O Server health assessment tool along with its dependent tools on a NIM master.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with default values:

    vioshc_opt_free_size (optional, str, 500)

Specifies the free space in megabytes required in the /opt folder.  
This size is used to install dependent tools required for Virtual I/O Server health assessment tool.

## Dependencies

None.

## Example Playbook

    - hosts: aix
      gather_facts: no
      include_role:
        name: power_aix_vioshc
      vars:
        vioshc_opt_free_size: 1000

## Copyright
© Copyright IBM Corporation 2021
