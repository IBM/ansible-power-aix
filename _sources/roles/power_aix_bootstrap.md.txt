# Ansible Role: power_aix_bootstrap
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `power_aix_bootstrap`, which automatically loads and executes commands to install dependent software.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with if they are required, type and default values:

    pkgtype (True, str, none)

Specifies the package service requiring bootstrap installation.
pkgtype: [yum, python, dnf, wget, pycurl]
Bootstrap for yum and python is supported for AIX 7.1 and AIX 7.2.
Bootstrap for dnf is supported for AIX 7.3

-- pkgtype arguments
- yum
Uses the AIX toolsbox to install the yum package and dependencies.
- python
Install python2 using yum.
- dnf
Uses the AIX toolsbox to install dnf and dependencies on AIX 7.3 and above.
- wget
Uses dnf or yum to install wget.
-pycurl
Installs pycurl

    opt_free_size (optional, str, 500)

Specifies the free space in megabytes needed in the /opt folder. It is used by dnf, wget and pycurl bootstraps.

    var_free_size (optional, str, 200)

Specifies the free space in megabytes needed in the /var folder.

    download_dir (optional, str, ~)

Specifies the temporary download location for install scripts and packages. The location resides on the Ansbile control node.

    target_dir (optional, str, /tmp/.ansible.cpdir)

Specifies the target location (per inventory host) for copying and restoring package files and metadata. If the target location does not exist, then a temporary filesystem is created using the target_dir as the mount point.  Upon role completion, the target location is removed.

## Dependencies

None.

## Example Playbook

    - hosts: aix
      gather_facts: no
      include_role:
        name: power_aix_bootstrap
      vars:
        pkgtype: yum


    - hosts: aix
      gather_facts: no
      include_role:
        name: power_aix_bootstrap
      vars:
        pkgtype: wget
        opt_free_size: 1000

## Copyright
© Copyright IBM Corporation 2021
