# Ansible Role: power_aix_bootstrap
The [IBM Power Systems AIX](../../README.md) collection provides an [Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), referred to as `power_aix_bootstrap`, which automatically loads and executes commands to install dependent software.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables

Available variables are listed below, along with if they are required, type and default values:


    pkgtype (True, str, none)

Specifies the package service requiring bootstrap installation.
pkgtype: [dnf]
Bootstrap for dnf is supported for all AIX versions.
yum is not supported now on any AIX version.

-- pkgtype arguments
- dnf

Specifies the free space in megabytes needed in the /var folder.

    power_aix_bootstrap_download_dir (optional, str, ~)

Specifies the temporary download location for install scripts and packages. The location resides on the Ansbile control node.

    power_aix_bootstrap_target_dir (optional, str, /tmp/.ansible.cpdir)

Specifies the target location (per inventory host) for copying and restoring package files and metadata. If the target location does not exist, then a temporary filesystem is created using the power_aix_bootstrap_target_dir as the mount point.  Upon role completion, the target location is removed.

## Dependencies

None.

## Example Playbook

    - hosts: aix
      gather_facts: no
      include_role:
        name: power_aix_bootstrap
      vars:
        pkgtype: dnf

**NOTES**: 
- For using local repo to setup dnf, you need to set ***power_aix_bootstrap_local_repo*** to True. In this case, local repo should already be set up.
- In case of local repo, you need to provide the path where the local repo has been mounted to using ***power_aix_bootstrap_dnf_repo_mount_path***
- The provided local repo should have AIX_Toolbox, AIX_Toolbox_noarch, and other version specific repos with naming and structure as /mount_path/AIX_Toolbox, /mount_path/AIX_Toolbox_noarch etc.
- In case of local repo, you need to provide the mount path where the required tar ball resides using ***power_aix_bootstrap_dnf_bundle_mount_path***
- When python is not available on the system (Inside usr/bin), the module picks the hostnames from the inventory file and copies the required script to the target nodes using scp command. For this to happen, hosts should be listed as root@hostname inside inventory.
- Refer [Configuring DNF and creating local repositories on IBM AIX](https://developer.ibm.com/tutorials/awb-configuring-dnf-create-local-repos-ibm-aix/) for additional information about dnf local repo setup on AIX.

## Copyright
© Copyright IBM Corporation 2021
