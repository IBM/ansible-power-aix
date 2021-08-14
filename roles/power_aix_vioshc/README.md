# Ansible Role: power_aix_vioshc
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `power_aix_vioshc`, which installs a Virtual I/O Server health assessment tool on a NIM master.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.
## Dependencies

None.

## Example Playbook

    - hosts: nimmaster
      gather_facts: no
      include_role:
        name: power_aix_vioshc

## Copyright
© Copyright IBM Corporation 2020
