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
module: viosbr
short_description: Backup/Restore the configuration of the VIOS
description:
- Performs the operations for backing up and restoring the virtual
  and logical configuration of the Virtual I/O Server (VIOS).
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the operation to perform on the VIOS.
    - C(backup) to perform a backup.
    - C(restore) to restore a backup file.
    - C(recoverdb) to recover from a corrupted shared storage pool (SSP) database.
    - C(migrate) to migrate a backup file from an older release level to a current
      release level. A new file is created with I(_MIGRATED) string appended to
      the given file name.
    - C(dr) to recover the cluster on another geographic location.
    - C(list) to view the listing of backup files.
    type: str
    choices: [ backup, restore, recoverdb, migrate, dr, list ]
    required: true
  file:
    description:
    - Specifies the file name of the file that has backup information.
    - For backup, compressed file is created with I(.tar.gz) extension.
    - For cluster backups, compressed file is created with I(<clustername>.tar.gz) extension.
    - If file name is a relative path, file is created under I(/home/padmin/cfgbackups).
    type: str
  dir:
    description:
    - User-specified location from where to list backup files when I(action=list).
    type: str
  devtype:
    description:
    - Only restore devices of the specified type.
    type: str
    choices: [ net, vscsi, npiv, cluster, vlogrepo, ams ]
  clustername:
    description:
    - Specifies the cluster name to back up or restore, including all of its associated nodes.
    type: str
  subfile:
    description:
    - Specifies the node configuration file to be restored.
    type: str
  currentdb:
    description:
    - Restores the cluster without restoring the database from the backup.
    - When restoring mapping, some of the mapping can fail if the mappings are not in the current database.
    type: str
  force:
    description:
    - Attempts to restore a device even if it has not been successfully validated.
    type: bool
    default: no
  repopvs:
    description:
    - List of hdisks to be used as repository disks for restoring the cluster.
    - The given disks must not contain a repository signature.
    type: list
    elements: str
  skipcluster:
    description:
    - Restores all local devices, except I(cluster0).
    type: bool
    default: no
  skipdevattr:
    description:
    - Skips the restore of the physical device attributes.
    - Does not modify the current system's physical device attributes.
    type: bool
    default: no
  validate:
    description:
    - Validates the devices on the server against the devices on the backed-up file.
    - Fails the restore operation if items do not validate successfully.
    type: bool
    default: no
notes:
  - The I(restore) action must be run on the same VIOS partition as the one where
    the backup was performed.
'''

EXAMPLES = r'''
- name: Back up all the device attributes and logical and virtual device mappings
        on the VIOS file /tmp/myserverbackuperform.tar.gz
  viosbr:
    action: backup
    file: /tmp/myserverbackuperform

- name: Restore all the possible devices and display a summary of deployed and nondeployed devices
  viosbr:
    action: restore
    file: /home/padmin/cfgbackups/myserverbackup.002.tar.gz

- name: Back up a cluster and all the nodes that are up
  viosbr:
    action: backup
    clustername: mycluster
    file: systemA

- name: Restore a particular node within the cluster
  viosbr:
    action: restore
    clustername: mycluster
    file: systemA.mycluster.tar.gz
    subfile: myclusterMTM8233-E8B02HV32001P3.xml

- name: Restore a cluster and its nodes
  viosbr:
    action: restore
    clustername: mycluster
    file: systemA.mycluster.tar.gz
    repopvs: hdisk5

- name: Restore only the shared storage pool database from a backup file
  viosbr:
    action: recoverdb
    clustername: mycluster
    file: systemA.mycluster.tar.gz

- name: Migrate an older cluster backup file
  viosbr:
    action: migrate
    file: systemA.mycluster.tar.gz

- name: Restore legacy device mappings on a node, which is in cluster using a cluster backup file
  viosbr:
    action: restore
    clustername: mycluster
    file: systemA.mycluster.tar.gz
    subfile: myclusterMTM8233-E8B02HV32001P3.xml
    skipcluster: yes

- name: Restore cluster from a backup file but use the database that exists on the system
  viosbr:
    action: restore
    clustername: mycluster
    file: systemA.mycluster.tar.gz
    repopvs: hdisk5
    currentdb: yes

- name: Recover the cluster on another geographic location
  viosbr:
    action: dr
    clustername: mycluster
    file: systemA.mycluster.tar.gz
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
stdout:
    description: The standard output
    returned: always
    type: str
    sample: 'Backup of this node (vios01) successful'
stderr:
    description: The standard error
    returned: always
    type: str
    sample: 'File /home/padmin/cfgbackups/myserverbackup.002.tar.gz does not exist.'
ioslevel:
    description: The latest installed maintenance level of the system
    returned: always
    type: str
    sample: '3.1.0.00'
file:
    description: The name of the backup file that has been created
    returned: if I(action=backup) or I(action=migrate)
    type: str
    sample: /home/padmin/cfgbackups/myserverbackup.002.tar.gz
'''

import os.path
import re

from ansible.module_utils.basic import AnsibleModule


ioscli_cmd = 'ioscli'


def get_ioslevel(module):
    """
    Return the latest installed maintenance level of the system.
    """
    global results

    cmd = [ioscli_cmd, 'ioslevel']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Could not retrieve ioslevel, return code {0}.'.format(ret)
        module.fail_json(**results)

    ioslevel = stdout.split('\n')[0]

    if not re.match(r"^\d+.\d+.\d+.\d+$", ioslevel):
        results['msg'] = 'Could not parse ioslevel output {0}.'.format(ioslevel)
        module.fail_json(**results)

    results['ioslevel'] = ioslevel

    return ioslevel


def viosbr_backup(module, params):
    """
    Takes the backup of VIOS configurations.
    """
    global results

    filename = params['file']

    cmd = [ioscli_cmd, 'viosbr', '-backup']
    cmd += ['-file', filename]
    if params['clustername']:
        cmd += ['-clustername', params['clustername']]

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    if not os.path.isabs(filename):
        filename = os.path.join('/home/padmin/cfgbackups', filename)
    results['file'] = filename + '.tar.gz'
    results['changed'] = True


def viosbr_restore(module, params):
    """
    Takes backup file as input and brings the VIOS partition to the same
    state when the backup was taken.
    """
    global results

    cmd = [ioscli_cmd, 'viosbr', '-restore']
    cmd += ['-file', params['file']]
    if params['devtype']:
        cmd += ['-type', params['devtype']]
    if params['clustername']:
        cmd += ['-clustername', params['clustername']]
        if params['subfile']:
            cmd += ['-subfile', params['subfile']]
        if params['repopvs']:
            cmd += ['-repopvs', ' '.join(params['repopvs'])]
        # option has changed to -db in latest version? check ioslevel?
        if params['currentdb']:
            cmd += ['-currentdb']

    if params['force']:
        cmd += ['-force']
    elif params['validate']:
        cmd += ['-validate']
    if params['skipcluster']:
        cmd += ['-skipcluster']

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def viosbr_recoverdb(module, params):
    """
    Recovers from the shared storage pool database corruption,
    either from the backup file or from the solid database backup.
    """
    global results

    cmd = [ioscli_cmd, 'viosbr', '-recoverdb']
    cmd += ['-clustername', params['clustername']]
    if params['file']:
        cmd += ['-file', params['file']]

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['changed'] = True


def viosbr_migrate(module, params):
    """
    Migrates earlier cluster version of backup file to the current version.
    """
    global results

    cmd = [ioscli_cmd, 'viosbr', '-migrate']
    cmd += ['-file', params['file']]

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    results['file'] = params['file'] + '_MIGRATED'
    results['changed'] = True


def viosbr_dr(module, params):
    """
    Recovers the cluster on another geographic location.
    """
    global results

    results['msg'] = 'Disaster recovery is currently not implemented'
    module.fail_json(**results)


def viosbr_list(module, params):
    """
    Displays backup files from either the default location /home/padmin/cfgbackups or
    a user-specified location.
    """
    global results

    cmd = [ioscli_cmd, 'viosbr', '-view', '-list']
    # Directory defaults to /home/padmin/cfgbackups
    if params['dir']:
        cmd += [params['dir']]

    ret, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['stderr'] = stderr
    if ret != 0:
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def main():
    global results

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(required=True, type='str',
                        choices=['backup', 'restore', 'recoverdb', 'migrate', 'dr', 'list']),
            file=dict(type='str'),
            dir=dict(type='str'),
            devtype=dict(type='str',
                         choices=['net', 'vscsi', 'npiv', 'cluster', 'vlogrepo', 'ams']),
            clustername=dict(type='str'),
            subfile=dict(type='str'),
            currentdb=dict(type='str'),
            force=dict(type='bool', default=False),
            repopvs=dict(type='list', elements='str'),
            skipcluster=dict(type='bool', default=False),
            skipdevattr=dict(type='bool', default=False),
            validate=dict(type='bool', default=False),
        ),
        required_if=[
            ['action', 'backup', ['file']],
            ['action', 'restore', ['file']],
            ['action', 'recoverdb', ['clustername']],
            ['action', 'migrate', ['file']],
        ],
        mutually_exclusive=[
            ['force', 'validate']
        ]
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    get_ioslevel(module)

    action = module.params['action']

    if action == 'backup':
        viosbr_backup(module, module.params)
    elif action == 'restore':
        viosbr_restore(module, module.params)
    elif action == 'recoverdb':
        viosbr_recoverdb(module, module.params)
    elif action == 'migrate':
        viosbr_migrate(module, module.params)
    elif action == 'dr':
        viosbr_dr(module, module.params)
    elif action == 'list':
        viosbr_list(module, module.params)

    results['msg'] = 'viosbr completed successfully'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
