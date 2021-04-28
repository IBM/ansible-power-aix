#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: filesystem
short_description: Local and NFS filesystems management.
description:
- This module allows to create, modify and remove local and NFS filesystems.
version_added: '2.9'
requirements:
- AIX
- Python >= 2.7
- 'Privileged user with authorizations:
  B(aix.fs.manage.list,aix.fs.manage.create,aix.fs.manage.change,aix.fs.manage.remove,aix.network.nfs.mount)'
options:
  filesystem:
    description:
    - Specifies the mount point that is the directory where the file system will be mounted.
    type: str
    required: true
  state:
    description:
    - Specifies the action to be performed on the filesystem.
    - C(present) specifies to create a filesystem if it does not exist, otherwise it changes the
      attributes of the specified filesystem.
    - C(absent) specifies to remove a filesystem.
    type: str
    choices: [ present, absent ]
    default: present
  rm_mount_point:
    description:
    - When I(state=absent), specifies to remove the mount directory along with the entry in
      the filesystem.
    type: bool
    default: false
  attributes:
    description:
    - When I(state=present), specifies comma separated 'attribute=value' pairs used to create or
      modify the local filesystem.
    - Refer to 'crfs' AIX command documentation for more details on the supported attributes.
    type: list
    elements: str
  device:
    description:
    - When I(state=present), for local filesystem, it specifies the logical volume to use to create
      the filesystem. If not specified, a new logical volume will be created.
    - When I(state=present), for NFS filesystem, it specifies the remote export device to use to
      create or modify the filesystem.
    type: str
  vg:
    description:
    - When I(state=present), specifies an existing volume group.
    type: str
  account_subsystem:
    description:
    - When I(state=present), for local filesystems, specifies whether the file system is to be
      processed by the accounting subsystem.
    type: bool
  fs_type:
    description:
    - Specifies the virtual filesystem type to create the local filesystem.
    type: str
    default: jfs2
  auto_mount:
    description:
    - Specifies whether to automatically mount the filesystem at system restart while creating or
      updating filesystem.
    type: bool
  permissions:
    description:
    - Specifies file system permissions while creation/updation of any filesystem.
    - C(rw) specifies read-write mode.
    - C(ro) specifies read-only mode.
    type: str
    choices: [ ro, rw ]
  mount_group:
    description:
    - Specifies the mount group to be set/modified for a filesystem.
    type: str
  nfs_server:
    description:
    - Specifies a Network File System (NFS) server for NFS filesystem.
    type: str
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chfsmnt.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chnfsmnt.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/crfs.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/m_commands/mknfsmnt.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmfs.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmnfsmnt.html).
'''

EXAMPLES = r'''
- name: Creation of a JFS2 filesystem
  ibm.power_aix.filesystem:
    state: present
    filesystem: /mnt3
    fs_type: jfs2
    attributes: size=32768,isnapshot='no'
    mount_group: test
    vg: rootvg
- name: Increase size of a filesystem
  ibm.power_aix.filesystem:
    filesystem: /mnt3
    state: present
    attributes: size=+5M
- name: Remove a NFS filesystem
  ibm.power_aix.filesystem:
    filesystem: /mnt
    state: absent
    rm_mount_point: true
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import re


def is_nfs(module, filesystem):
    """
    Determines if a filesystem is NFS or not
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: True - filesystem is NFS type / False - filesystem is not NFS type
    """
    cmd = "lsfs -l %s" % filesystem
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return None

    ln = stdout.splitlines()[1:][0]
    type = ln.split()[3]

    if type == "nfs":
        return True
    else:
        return False


def fs_state(module, filesystem):
    """
    Determines the current state of filesystem.
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: True - filesystem in mounted state / False - filesystem in unmounted state /
             None - filesystem does not exist
    """

    cmd = "lsfs -l %s" % filesystem
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        return None

    cmd = "df"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        module.fail_json("Command '%s' failed." % cmd)

    if stdout:
        mdirs = []
        for ln in stdout.splitlines()[1:]:
            mdirs.append(ln.split()[6])
        if filesystem in mdirs:
            return True

    return False


def check_attr_change(module, filesystem):
    """
    Determines if changes will be made on the filesystem.
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: True - changes will be made on the filesystem / False = filesystem will remain unchanged
    """

    cmd = "lsfs -cq %s" % filesystem
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Failed to fetch current attributes of '%s'. cmd - '%s'" % (filesystem, cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    all_attr = stdout.splitlines()

    # list of items used in old_attr
    # old_attr[4] - mount group
    # old_attr[5] - size
    # old_attr[6] - permissions
    # old_attr[7] - automount
    # old_attr[8] - accounting subsystem
    old_attr = all_attr[1].split(":")

    # check for extended attributes
    old_ext_attr = dict()
    if len(all_attr) == 3:
        attrs = re.sub(r"[()]", "", all_attr[2]).strip()
        attrs = attrs.split(":")
        for attr in attrs:
            attr = attr.rsplit(" ", 1)
            key = re.sub(" ", "_", attr[0]).lower()
            old_ext_attr[key] = attr[1]

    new_attr = dict()
    attrs = module.params["attributes"]
    if attrs:
        for attr in attrs:
            attr = attr.strip()
            attr = attr.split("=")
            new_attr[attr[0]] = attr[1]

    # check if mount group changed
    new_mnt_grp = module.params["mount_group"]
    if new_mnt_grp:
        old_mnt_grp = old_attr[4]
        if new_mnt_grp != old_mnt_grp:
            return True

    # check if permissions changed
    new_perms = module.params["permissions"]
    if new_perms:
        old_perms = old_attr[6].split(",")[0]
        if new_perms != old_perms:
            return True

    # check if automount changed
    new_amount = module.params["auto_mount"]
    if new_amount is not None:
        old_amount = old_attr[7]
        new_amount = "yes" if new_amount else "no"
        if new_amount != old_amount:
            return True

    # check in account subsystem changed
    new_acct_sub_sys = module.params["account_subsystem"]
    if new_acct_sub_sys is not None:
        old_acct_sub_sys = old_attr[8]
        new_acct_sub_sys = "yes" if new_acct_sub_sys else "no"
        if new_acct_sub_sys != old_acct_sub_sys:
            return True

    # check filesystem size changes
    if "size" in new_attr:
        old_size = int(old_attr[5]) * 512
        new_size = new_attr["size"]
        if new_size[0] == "+" or new_size[0] == "-":
            return True
        if new_size[-1] == "M":
            pass
        elif new_size[-1] == "G":
            new_size = int(new_size[:-1])
            new_size *= 1073741824
        if new_size != old_size:
            return True

    # check if ea format changes
    if "ea" in new_attr and "eaformat" in old_ext_attr:
        old_ea = old_ext_attr["eaformat"]
        new_ea = new_attr["ea"]
        if new_ea != old_ea:
            return True

    if "efs" in new_attr and "efs" in old_ext_attr:
        old_efs = old_ext_attr["efs"]
        new_efs = new_attr["efs"]
        if new_efs != old_efs:
            return True

    if "managed" in new_attr and "dmapi" in old_ext_attr:
        old_managed = old_ext_attr["dmapi"]
        new_managed = new_attr["managed"]
        if new_managed != old_managed:
            return True

    if "maxext" in new_attr and "maxext" in old_ext_attr:
        old_maxext = old_ext_attr["maxext"]
        new_maxext = new_attr["maxext"]
        if new_maxext != old_maxext:
            return True

    if "mountguard" in new_attr and "mountguard" in old_ext_attr:
        old_mountguard = old_ext_attr["mountguard"]
        new_mountguard = new_attr["mountguard"]
        if new_mountguard != old_mountguard:
            return True

    if "vix" in new_attr and "vix" in old_ext_attr:
        old_vix = old_ext_attr["vix"]
        new_vix = new_attr["vix"]
        if new_vix != old_vix:
            return True

    return False


def chfs(module, filesystem):
    """
    Changes the attributes of the filesystem.
    param module: Ansible module argument spec.
    param device: Filesystem name.
    return: changed - True/False(filesystem state modified or not),
            msg - message
    """
    # check initial attributes
    changed = check_attr_change(module, filesystem)
    if not changed:
        msg = "No changes needed in %s" % filesystem
        return False, msg

    attrs = module.params["attributes"]
    acct_sub_sys = module.params["account_subsystem"]
    amount = module.params["auto_mount"]
    device = module.params["device"]
    perms = module.params["permissions"]
    mgroup = module.params["mount_group"]
    nfs_server = module.params["nfs_server"]

    opts = ""

    # check initial attributes
    changed = check_attr_change(module, filesystem)
    if not changed:
        msg = "No changes needed in %s" % filesystem
        return False, msg

    if is_nfs(module, filesystem):
        # Modify NFS filesystem
        if amount is True:
            opts += "-A "
        elif amount is False:
            opts += "-a "

        if perms:
            opts += "-t %s " % perms

        if mgroup:
            opts += "-m %s " % mgroup

        cmd = "chnfsmnt %s -f %s -d %s -h %s" % (opts, filesystem, device, nfs_server)

    else:
        # Modify Local Filesystem
        if amount is True:
            opts += "-A yes "
        elif amount is False:
            opts += "-A no "

        if attrs:
            opts += "-a " + ' -a '.join(attrs) + " "
        else:
            opts += ""

        if mgroup:
            opts += "-u %s " % mgroup

        if perms:
            opts += "-p %s " % perms

        if acct_sub_sys:
            opts += "-t yes "
        elif acct_sub_sys is False:
            opts += "-t no "

        cmd = "chfs %s %s" % (opts, filesystem)

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Modification of filesystem '%s' failed. cmd - '%s'" % (filesystem, cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    msg = "Modification of Filesystem '%s' completed" % filesystem
    return True, msg


def mkfs(module, filesystem):
    """
    Create filesystem.
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: changed - True/False(filesystem state created or not),
            msg - message
    """
    device = module.params['device']
    if device:
        device = "-d %s " % device
    else:
        device = ""

    mgroup = module.params['mount_group']
    auto_mount = module.params['auto_mount']
    nfs_server = module.params['nfs_server']
    perm = module.params['permissions']
    if perm is None:
        perm = "rw"

    if nfs_server:
        # Create NFS Filesystem
        if auto_mount:
            auto_mount = "-A"
        else:
            auto_mount = "-a"
        if mgroup:
            mgroup = "-m %s  " % mgroup
        else:
            mgroup = ""

        cmd = "mknfsmnt -f '%s' %s -h '%s' -t %s %s -w bg %s " % (filesystem, device, nfs_server, perm, mgroup, auto_mount)
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "Creation of NFS filesystem %s failed. cmd - '%s'" % (filesystem, cmd)
            module.fail_json(msg=msg, stdout=stdout, stderr=stderr)
        else:
            msg = "Creation of NFS filesystem '%s' succeeded" % filesystem
    else:
        # Create a local filesystem
        attrs = module.params['attributes']
        if attrs:
            attr_str = "-a " + ' -a '.join(attrs)
        else:
            attr_str = ""

        acct_sub_sys_opt = {
            None: '',
            True: '-t yes ',
            False: '-t no '
        }
        acct_sub_sys = module.params['account_subsystem']
        acct_sub_sys = acct_sub_sys_opt[acct_sub_sys]

        vg = module.params['vg']
        if vg:
            vg = "-g %s " % vg
        else:
            vg = ""

        if auto_mount:
            auto_mount = "-A yes "
        else:
            auto_mount = "-A no "

        if mgroup:
            mgroup = "-u %s  " % mgroup
        else:
            mgroup = ""

        fs_type = "-v %s " % module.params['fs_type']

        cmd = "crfs %s%s%s-m %s %s%s-p %s %s%s" % (fs_type, vg, device, filesystem, mgroup, auto_mount, perm, acct_sub_sys, attr_str)
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "Creation of filesystem %s failed. cmd - '%s'" % (filesystem, cmd)
            module.fail_json(msg=msg, stdout=stdout, stderr=stderr)
        else:
            msg = "Creation of filesystem '%s' succeeded" % filesystem

    return True, msg


def rmfs(module, filesystem):
    """
    Remove the filesystem
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: changed - True/False(filesystem state modified or not),
            msg - message
    """
    rm_mount_point = module.params["rm_mount_point"]
    fs_type = is_nfs(module, filesystem)

    if fs_type:
        if rm_mount_point:
            cmd = "rmnfsmnt -B -f "
        else:
            cmd = "rmnfsmnt -I -f "
    else:
        if rm_mount_point:
            cmd = "rmfs -r "
        else:
            cmd = "rmfs "

    cmd += filesystem
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Filesystem Removal for '%s' failed. cmd - '%s'" % (filesystem, cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    msg = "Filesystem '%s' has been removed." % filesystem
    return True, msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            attributes=dict(type='list', elements='str'),
            account_subsystem=dict(type='bool'),
            auto_mount=dict(type='bool'),
            device=dict(type='str'),
            vg=dict(type='str'),
            fs_type=dict(type='str', default='jfs2'),
            permissions=dict(type='str', choices=['rw', 'ro']),
            mount_group=dict(type='str'),
            nfs_server=dict(type='str'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            rm_mount_point=dict(type='bool', default='false'),
            filesystem=dict(type='str', required=True),
        ),
    )

    state = module.params['state']
    filesystem = module.params['filesystem']

    if state == 'present':
        # Create/Modify filesystem
        if fs_state(module, filesystem) is None:
            changed, msg = mkfs(module, filesystem)
        else:
            changed, msg = chfs(module, filesystem)
    elif state == 'absent':
        # Remove filesystem
        changed, msg = rmfs(module, filesystem)
    else:
        changed = False
        msg = "Invalid state '%s'" % state

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
