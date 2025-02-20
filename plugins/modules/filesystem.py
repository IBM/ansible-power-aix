#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule

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
- Python >= 3.6
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
    type: str
    choices: ['yes', 'no']
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
    type: str
    choices: ['yes', 'no']
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

result = None
crfs_specific_attributes = ["ag", "bf", "compress", "frag", "nbpi", "agblksize", "isnapshot"]


def is_nfs(module, filesystem):
    """
    Determines if a filesystem is NFS or not
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: True - filesystem is NFS type / False - filesystem is not NFS type
    """
    cmd = f"lsfs -l {filesystem}"
    rc, stdout = module.run_command(cmd)[:2]
    if rc != 0:
        return None

    ln = stdout.splitlines()[1:][0]
    type = ln.split()[3]

    if type == "nfs":
        return True
    return False


def valid_attributes(module):
    """
    Returns list of valid attributes for chfs command
    param:
        module - Ansible module argument spec.
    return:
        valid_attrs (list) - List of valid attributes among the provided ones.
    """
    attr = module.params['attributes']
    if attr is None:
        return True

    valid_attrs = []

    for attributes in attr:
        if attributes.split("=")[0] in crfs_specific_attributes:
            continue
        valid_attrs.append(attributes)

    return valid_attrs


def fs_state(module, filesystem):
    """
    Determines the current state of filesystem.
    param module: Ansible module argument spec.
    param filesystem: filesystem name.
    return: True - filesystem in mounted state / False - filesystem in unmounted state /
             None - filesystem does not exist
    """

    cmd = f"lsfs -l {filesystem}"
    rc = module.run_command(cmd)[0]
    if rc != 0:
        return None

    cmd = "df"
    rc, stdout = module.run_command(cmd)[:2]
    if rc != 0:
        module.fail_json(f"Command {cmd} failed.")

    if stdout:
        mdirs = []
        for ln in stdout.splitlines()[1:]:
            mdirs.append(ln.split()[6])
        if filesystem in mdirs:
            return True

    return False


def compare_attrs(module):
    """
    Helper function to compare the provided and already existing attributes of a filesystem
    params:
        module - Ansible module argument spec.
    return:
        updated_attrs (list) - List of updated attributes and their values, that need to be changed
    """

    fs_mount_pt = module.params['filesystem']
    cmd1 = f"lsfs -c {fs_mount_pt}"
    cmd2 = f"lsfs -q {fs_mount_pt}"

    rc1, stdout1, stderr1 = module.run_command(cmd1)

    if rc1:
        result['stdout'] = stdout1
        result['cmd'] = cmd1
        result['stderr'] = stderr1
        result['msg'] = "Could not get information about the provided filesystem."
        module.fail_json(**result)

    rc2, stdout2, stderr2 = module.run_command(cmd2)

    if rc2:
        result['stdout'] = stdout2
        result['cmd'] = cmd2
        result['stderr'] = stderr2
        result['msg'] = "Could not get information about the provided filesystem."
        module.fail_json(**result)

    current_attributes = {}

    fs_attrs = ["mountpoint", "device", "vfs", "nodename", "type", "size", "options", "automount", "acct"]

    lines1 = stdout1.splitlines()
    line1 = lines1[1].replace("::", ":--:")
    line1 = line1.split(":")

    for it in range(9):
        current_attributes[fs_attrs[it]] = line1[it]

    lines2 = stdout2.splitlines()

    fs_attrs = ["name", "nodename", "mount pt", "vfs", "size", "options", "auto", "accounting"]

    line2 = lines2[1].split()
    for it in range(8):
        if fs_attrs[it] in current_attributes.keys() and current_attributes[fs_attrs[it]] != "--":
            continue
        current_attributes[fs_attrs[it]] = line2[it]

    mapped_key = {
        "dmapi": "managed",
        "fs size": "size",
        "eaformat": "ea",
        "inline log size": "logsize"
    }

    # In case of non-JFS/JFS2 fs, lsfs -q provides less information (no info inside brackets)
    if len(lines2) >= 3:
        for it in lines2[2].split(","):
            curr_attr = it.split(":")
            attr_key = curr_attr[0].strip().lower()
            attr_val = curr_attr[1].strip()
            if attr_key[0] == "(":
                attr_key = attr_key[1:]
            if attr_val[-1] == ")":
                attr_val = attr_val[:-1]
            if attr_key in mapped_key.keys():
                attr_key = mapped_key[attr_key]
            current_attributes[attr_key] = attr_val

    amount = module.params["auto_mount"]
    perms = module.params["permissions"]
    mgroup = module.params["mount_group"]
    acct_sub_sys = module.params["account_subsystem"]
    check_other_perms = 0

    if not amount or amount == current_attributes['auto']:
        module.params['auto_mount'] = ""
        check_other_perms += 1

    if not perms or perms == current_attributes['options']:
        module.params['permissions'] = ""
        check_other_perms += 1

    if not mgroup or mgroup == current_attributes['type']:
        module.params['mount_group'] = ""
        check_other_perms += 1

    if not acct_sub_sys or acct_sub_sys == current_attributes['accounting']:
        module.params['account_subsystem'] = ""
        check_other_perms += 1

    updated_attrs = []

    if module.params['attributes']:
        module.params['attributes'] = valid_attributes(module)
        provided_attributes = module.params['attributes']

        for attrs in provided_attributes:
            attrs = attrs.split("=")
            attr = attrs[0].strip()
            val = attrs[1].strip()
            val = val.strip('\"')  # For case when variables are used while providing values to attributes
            if attr == "log" or attr == "logname":
                if val == "INLINE":
                    val = "yes"
                if current_attributes['inline log'] and val != current_attributes['inline log']:
                    updated_attrs.append(f"{attr}={val}")
                continue

            prefix = ["+", "-"]
            if attr == "size" and val[0] not in prefix:
                if val[-1] == "M":
                    val = int(val[:-1])
                    if val % 64 != 0:
                        val = str(((val // 64) + 1) * 64)
                if str(val)[-1] == "G":
                    val = int(val[:-1])
                    val = str(val * 1024)
                block_size = int(current_attributes["block size"]) // 1024
                val = str(int(val) * block_size * 512)

            if attr not in current_attributes.keys() or val not in current_attributes[attr].split(','):
                updated_attrs.append(f"{attr}={val}")

    if check_other_perms == 4 and len(updated_attrs) == 0:
        result['msg'] = "No modification is required, exiting!"
        module.exit_json(**result)

    module.params['attributes'] = updated_attrs


def nfs_opts(module):
    """
    Helper function to build NFS parameters for mknfsmnt and chnfsmnt.
    """
    amount = module.params["auto_mount"]
    perms = module.params["permissions"]
    mgroup = module.params["mount_group"]
    nfs_soft_mount = module.params["nfs_soft_mount"]

    opts = ""
    if amount == "yes":
        opts += "-A "
    elif amount == "no":
        opts += "-a "

    if nfs_soft_mount:
        opts += "-S "

    if perms:
        opts += f"-t {perms} "

    if mgroup:
        opts += f"-m {mgroup} "

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
    if amount:
        opts += f"-A {amount} "

    if attrs:
        opts += "-a " + ' -a '.join(attrs) + " "
    else:
        opts += ""

    if mgroup:
        opts += f"-u {mgroup} "

    if perms:
        opts += f"-p {perms} "

    if acct_sub_sys:
        opts += f"-t {acct_sub_sys} "

    return opts


def chfs(module, filesystem):
    """
    Changes the attributes of the filesystem.
    param module: Ansible module argument spec.
    param filesystem: Filesystem name.
    return: changed - True/False(filesystem state modified or not),
            msg - message
    """
    amount = module.params["auto_mount"]
    perms = module.params["permissions"]
    mgroup = module.params["mount_group"]
    acct_sub_sys = module.params["account_subsystem"]

    # compare initial and the provided attributes. Exit if no change is required.
    if module.params['attributes'] or amount or perms or mgroup or acct_sub_sys:
        compare_attrs(module)

    opts = ""
    nfs = is_nfs(module, filesystem)
    if nfs:
        opts = nfs_opts(module)
        device = module.params["device"]
        nfs_server = module.params["nfs_server"]
        cmd = f"chnfsmnt {opts} -f {filesystem} -d {device} -h {nfs_server}"
    else:
        opts = fs_opts(module)
        cmd = f"chfs {opts} {filesystem}"

    result["cmd"] = cmd
    rc, stdout, stderr = module.run_command(cmd)
    result["rc"] = rc

    if rc != 0:
        msg = f"Modification of filesystem {filesystem} failed. cmd - {cmd}"
        result["msg"] = msg
        result["stdout"] = stdout
        result["stderr"] = stderr
        module.fail_json(**result)

    msg = f"Modification of filesystem {filesystem} completed"
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

    nfs_server = module.params['nfs_server']
    device = module.params['device']
    if device:
        device = f"-d {device} "
    else:
        device = ""

    if nfs_server:
        # Create NFS Filesystem
        opts = nfs_opts(module)

        cmd = f"mknfsmnt -f {filesystem} {device} -h {nfs_server} {opts} -w bg "
    else:
        # Create a local filesystem
        opts = fs_opts(module)

        fs_type = module.params['fs_type']

        vg = module.params['vg']
        if vg:
            vg = f"-g {vg} "
        else:
            vg = ""

        cmd = f"crfs -v {fs_type} {vg}{device}-m {filesystem} {opts}"

    result["cmd"] = cmd

    rc, stdout, stderr = module.run_command(cmd)
    result["rc"] = rc
    if rc != 0:
        if nfs_server:
            msg = f"Creation of NFS filesystem {filesystem} failed. cmd - {cmd}"
        else:
            msg = f"Creation of filesystem {filesystem} failed. cmd - {cmd}"
        result["stdout"] = stdout
        result["stderr"] = stderr
        result["msg"] = msg
        module.fail_json(**result)
    else:
        if nfs_server:
            msg = f"Creation of NFS filesystem {filesystem} succeeded"
        else:
            msg = f"Creation of filesystem {filesystem} succeeded"
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
        msg = f"Filesystem Removal for {filesystem} failed. cmd - {cmd}"
        result["msg"] = msg
        result["stdout"] = stdout
        result["stderr"] = stderr
        module.fail_json(**result)

    msg = f"Filesystem {filesystem} has been removed."
    result["changed"] = True
    result["msg"] = msg


def main():
    global result

    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            attributes=dict(type='list', elements='str'),
            account_subsystem=dict(type='str', choices=['yes', 'no']),
            auto_mount=dict(type='str', choices=['yes', 'no']),
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
        result["msg"] = f"Invalid state {state}"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
