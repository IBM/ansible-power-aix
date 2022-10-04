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
version_added: '1.0.0'
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
  nfs_soft_mount:
    description:
    - Creates a soft mount, which means the system returns an error if the server does not respond.
    type: bool
    default: False
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


result = None


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


def nfs_opts(module):
    """
    Helper function to build NFS parameters for mknfsmnt and chnfsmnt.
    """
    amount = module.params["auto_mount"]
    perms = module.params["permissions"]
    mgroup = module.params["mount_group"]
    nfs_soft_mount = module.params["nfs_soft_mount"]

    opts = ""
    if amount is True:
        opts += "-A "
    elif amount is False:
        opts += "-a "

    if nfs_soft_mount:
        opts += "-S "

    if perms:
        opts += "-t %s " % perms

    if mgroup:
        opts += "-m %s " % mgroup

    return opts


def fs_opts(module):
    """
    Helper function to build filesystem parameters for crfs and chfs.
    """
    amount = module.params["auto_mount"]
    perms = module.params["permissions"]
    mgroup = module.params["mount_group"]
    attrs = module.params["attributes"]
    acct_sub_sys = module.params["account_subsystem"]

    opts = ""
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

    return opts


def get_fs_props(module, filesystem):
    """
    Fetches the current attributes of a specified filesystem
    using lsfs.
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: fs_props - output of lsfs -cq <fs>
    """
    global result

    cmd = "lsfs -cq %s" % filesystem
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Failed to fetch current attributes of '%s'. cmd - '%s'" % (filesystem, cmd)
        result["rc"] = rc
        result["msg"] = msg
        result["stdout"] = stdout
        result["stderr"] = stderr
        module.fail_json(**result)

    fs_props = stdout
    # for in NFS we are only concerned about limited properties
    props = stdout.splitlines()[1]
    props = props.split(":")
    # currently we are only interested in:
    # props[4] - mount group
    # props[6] - options - only interested in permissions here
    # props[7] - automount
    mnt_grp = props[4]
    perms = "rw" if "rw" in props[6].split(",") else "ro"
    amount = props[7]
    nfs_props = "%s:%s:%s" % (mnt_grp, perms, amount)
    return fs_props, nfs_props


def chfs(module, filesystem):
    """
    Changes the attributes of the filesystem.
    param module: Ansible module argument spec.
    param device: Filesystem name.
    return: changed - True/False(filesystem state modified or not),
            msg - message
    """
    global result

    # fetch initial attributes
    init_props_fs, init_props_nfs = get_fs_props(module, filesystem)

    # build command to run
    opts = ""
    nfs = is_nfs(module, filesystem)
    if nfs:
        init_props = init_props_nfs
        opts = nfs_opts(module)
        device = module.params["device"]
        nfs_server = module.params["nfs_server"]
        cmd = "chnfsmnt %s -f %s -d %s -h %s" % (opts, filesystem, device, nfs_server)
    else:
        # Modify Local Filesystem
        init_props = init_props_fs
        opts = fs_opts(module)
        cmd = "chfs %s %s" % (opts, filesystem)

    result["cmd"] = cmd
    rc, stdout, stderr = module.run_command(cmd)
    result["rc"] = rc

    # fetch the final properties of the filesystem after running command
    final_props_fs, final_props_nfs = get_fs_props(module, filesystem)
    if nfs:
        final_props = final_props_nfs
    else:
        final_props = final_props_fs

    if init_props == final_props:
        result["msg"] = "No changes needed in %s" % filesystem
        # if no changes are needed, make sure to report zero return code
        result["rc"] = 0
        return
    elif rc != 0:
        msg = "Modification of filesystem '%s' failed. cmd - '%s'" % (filesystem, cmd)
        result["msg"] = msg
        result["stdout"] = stdout
        result["stderr"] = stderr
        module.fail_json(**result)

    msg = "Modification of filesystem '%s' completed" % filesystem
    result["msg"] = msg
    result["changed"] = True


def mkfs(module, filesystem):
    """
    Create filesystem.
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: changed - True/False(filesystem state created or not),
            msg - message
    """
    global result

    nfs_server = module.params['nfs_server']
    perm = module.params['permissions']
    device = module.params['device']
    if device:
        device = "-d %s " % device
    else:
        device = ""

    if nfs_server:
        # Create NFS Filesystem
        opts = nfs_opts(module)
        if perm is None:
            opts += "-t rw"

        cmd = "mknfsmnt -f '%s' %s -h '%s' %s -w bg " % \
            (filesystem, device, nfs_server, opts)
    else:
        # Create a local filesystem
        opts = fs_opts(module)
        if perm is None:
            opts += "-p rw"

        fs_type = module.params['fs_type']

        vg = module.params['vg']
        if vg:
            vg = "-g %s " % vg
        else:
            vg = ""

        cmd = "crfs -v %s %s%s-m %s %s" % \
            (fs_type, vg, device, filesystem, opts)

    result["cmd"] = cmd

    rc, stdout, stderr = module.run_command(cmd)
    result["rc"] = rc
    if rc != 0:
        if nfs_server:
            msg = "Creation of NFS filesystem %s failed. cmd - '%s'" % (filesystem, cmd)
        else:
            msg = "Creation of filesystem %s failed. cmd - '%s'" % (filesystem, cmd)
        result["stdout"] = stdout
        result["stderr"] = stderr
        module.fail_json(**result)
    else:
        if nfs_server:
            msg = "Creation of NFS filesystem '%s' succeeded" % filesystem
        else:
            msg = "Creation of filesystem '%s' succeeded" % filesystem
        result["msg"] = msg
    result["changed"] = True


def rmfs(module, filesystem):
    """
    Remove the filesystem
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: changed - True/False(filesystem state modified or not),
            msg - message
    """
    global result

    rm_mount_point = module.params["rm_mount_point"]

    if is_nfs(module, filesystem):
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
    result["cmd"] = cmd

    rc, stdout, stderr = module.run_command(cmd)
    result["rc"] = rc
    if rc != 0:
        msg = "Filesystem Removal for '%s' failed. cmd - '%s'" % (filesystem, cmd)
        result["msg"] = msg
        result["stdout"] = stdout
        result["stderr"] = stderr
        module.fail_json(**result)

    msg = "Filesystem '%s' has been removed." % filesystem
    result["changed"] = True
    result["msg"] = msg


def main():
    global result

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
            nfs_soft_mount=dict(type='bool', default='False'),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            rm_mount_point=dict(type='bool', default='false'),
            filesystem=dict(type='str', required=True),
        ),
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    attributes = module.params['attributes']
    fs_type = module.params['fs_type']
    nfs_soft_mount = module.params['nfs_soft_mount']

    if attributes and fs_type == "nfs":
        result['msg'] = "Attributes are not supported with this filesystem."
        module.exit_json(**result)

    if fs_type != "nfs" and nfs_soft_mount:
        result['msg'] = "Soft mount is not supported with this filesystem."
        module.exit_json(**result)

    state = module.params['state']
    filesystem = module.params['filesystem']

    if state == 'present':
        # Create/Modify filesystem
        if fs_state(module, filesystem) is None:
            mkfs(module, filesystem)
        else:
            chfs(module, filesystem)
    elif state == 'absent':
        # Remove filesystem
        if fs_state(module, filesystem) is None:
            result["msg"] = "No action needed as filesystem does not exist."
            result["rc"] = 0
        else:
            rmfs(module, filesystem)
    else:
        result["msg"] = "Invalid state '%s'" % state

    module.exit_json(**result)


if __name__ == '__main__':
    main()
