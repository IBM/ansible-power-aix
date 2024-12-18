#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
import shutil
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: snap_command
author:
- AIX Development Team (@vivekpandeyibm)
short_description: Run snap command on AIX.
description:
- This module facilitates running the AIX snap command to gather diagnostic data.
  Users can specify various options like collecting performance data, clearing old data,
  or generating a complete system report.
version_added: '1.0.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- Root user is required.
options:
  all_info:
    description:
    - Gathers all available system information.
    - This is a comprehensive option that includes data across all categories, such as hardware, software, configuration files, and logs.
    type: bool
    required: true
  compress:
    description:
    - Compresses the collected data into a single archive, typically snap.pax.gz.
    - This is useful for easier file management and transport of the snapshot
    type: bool
  reset:
    description:
    - Removes the snap output directory (default /tmp/ibmsupt).
    - This cleans up previously gathered snapshot data, often to make room for a new snapshot
    type: bool
  hacmp:
    description:
    - Gathers HACMP (High Availability Cluster Multiprocessing) error information.
    - This is specific to AIX high-availability cluster environments and helps troubleshoot HA-related errors
    type: bool
  file_system_info:
    description:
    - Gathers file system information, including details on disk usage, mount points, and file system integrity.
    - This is crucial for diagnosing storage and disk-related issues
    type: bool
  live_kernel:
    description:
    - Collects Live kernel update information and saves it in the /tmp/ibmsupt/liveupdate directory.
    type: bool
  collects_dump:
    description:
    - Collects dump and /unix files, along with any live dump data. This is valuable for diagnosing kernel and system crashes
    type: bool
  installation_info:
    description:
    - Gathers installation information, such as installed software packages, patches, and configurations.
    - This helps diagnose installation-related issues.
    type: bool
  kernel_info:
    description:
    - Collects kernel-related data, including kernel configuration and status.
    - This is essential for debugging kernel-specific issues.
    type: bool
  security_info:
    description:
    - Gathers security information, including access controls, permissions, and user data.
    - This is important for diagnosing security issues and auditing.
    type: bool
  workload_manager_info:
    description:
    - Gather workload manager (WLM) information, which includes data related to workload management on the system.
    type: bool
  hardware_info:
    description:
    - Gather hardware information
    type: bool
notes:
  - You can refer to the IBM documentation for additional information on the snap command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/snap.html).
'''

EXAMPLES = r'''
- name: Collect hardware related data
  ibm.power_aix.snap_command:
    option: -h

- name: Clear old snap data
  ibm.power_aix.snap_command:
    option: -r

- name: Collect file system data
  ibm.power_aix.snap_command:
    option: -f

- name: Collect all system data
  ibm.power_aix.snap_command:
    option: -a
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Snap command executed successfully with option -P'
rc:
    description: The return code.
    returned: if the command failed.
    type: int
stdout:
    description: The standard output.
    returned: if the command failed.
    type: str
stderr:
    description: The standard error.
    returned: if the command failed.
    type: str

'''
expectPrompts = {
    "reset": "/usr/bin/expect -c \"spawn snap -r; \
            expect \\\"Do you want me to remove these directories \\(y|n\\): \\\"; \
            send \\\"y\\r\\\"; \
            expect \\\"Nothing to clean up\\\";\""
}


def build_snap_command(module):
    """
    Called the build snap command and check memory greated than 8MB
    arguments:
     module (AnsibleModule): The Ansible module instance.
    return:
        CMD - command which is succesfully cretaed

    """
    if check_memory_availbilty():
        cmd = snap_general_option(module)
    else:
        msg = "Memory is less than 8 mb:"
        module.fail_json(msg=msg)
    return cmd


def snap_general_option(module):

    """
    Build the snap command with specified options
    arguments:
     module (AnsibleModule): The Ansible module instance.
    return:
        True - when command succesfully created
    """
    cmd = ['snap']
    if module.params['all_info']:
        cmd += ['-a']
    elif module.params['hacmp']:
        cmd += ['-e']
    else:
        if module.params['file_system_info']:
            cmd += ['-f']
        if module.params['live_kernel']:
            cmd += ['-U']
        if module.params['installation_info']:
            cmd += ['-i']
        if module.params['kernel_info']:
            cmd += ['-k']
        if module.params['workload_manager_info']:
            cmd += ['-w']
        if module.params['general_info']:
            if module.params['security_info']:
                cmd += ['-S']
            cmd += ['-g']
        elif module.params['hardware_info']:
            cmd += ['-H']
        if module.params['collects_dump']:
            cmd += ['-D']
        if module.params['compress']:
            cmd += ['-c']
    return cmd


def check_memory_availbilty():
    """
    Check the memory is greater than 8 MB
    arguments:
      None
    return:
        True - If the memory greater than 8 MB
        False - If the memory less than 8 MB.
    """

    stat = shutil.disk_usage("/")
    free_space_mb = stat.free // (1024 * 1024)
    if free_space_mb < 8:
        return False
    return True


def run_snap_command_with_expect(module):
    """
    Executes the `snap -r` command using an `expect` script to handle interactive prompts.

    arguments:
        module (AnsibleModule): The Ansible module instance.

    Returns:
        dict: A dictionary containing 'stdout', 'stderr', 'rc', and 'changed'.
    """
    try:
        cmd = expectPrompts['reset']
        rc, stdout, stderr = module.run_command(cmd)

        # Handle the outputs
        if "Nothing to clean up" in stdout:
            return {
                "changed": False,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "rc": rc,
                "cmd": "snap -r",
                "msg": "No cleanup was required."
            }
        elif rc == 0:
            return {
                "changed": True,
                "stdout": stdout.strip(),
                "stderr": stderr.strip(),
                "rc": rc,
                "cmd": "snap -r",
                "msg": "Command executed successfully."
            }
        else:
            module.fail_json(
                changed=False,
                stdout=stdout.strip(),
                stderr=stderr.strip(),
                rc=rc,
                msg="Command execution failed."
            )
    except Exception as e:
        module.fail_json(
            changed=False,
            msg=f"An error occurred while running the command: {str(e)}"
        )


def main():
    # Define the arguments the module accepts
    module = AnsibleModule(
        argument_spec=dict(
            all_info=dict(type='bool', default=False),
            compress=dict(type='bool', default=False),
            general_info=dict(type='bool', default=False),
            live_kernel=dict(type='bool', default=False),
            hacmp=dict(type='bool', default=False),
            reset=dict(type='bool', default=False),
            file_system_info=dict(type='bool', default=False),
            collects_dump=dict(type='bool', default=False),
            installation_info=dict(type='bool', default=False),
            kernel_info=dict(type='bool', default=False),
            security_info=dict(type='bool', default=False),
            workload_manager_info=dict(type='bool', default=False),
            hardware_info=dict(type='bool', default=False),
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )
    if module.params['reset']:
        result = run_snap_command_with_expect(module)
    else:
        cmd = build_snap_command(module)
        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = ' '.join(cmd)
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            msg = f"Unable to run the snap command: { cmd }"
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            result['changed'] = True
            result['msg'] = f"Snap command executed successfully with option {cmd}"
    module.exit_json(**result)


if __name__ == '__main__':
    main()
