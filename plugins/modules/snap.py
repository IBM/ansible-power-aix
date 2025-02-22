#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2024- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
module: snap
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
  action:
    description:
    - Controls what snap-related action is performed.
    - C(snap) collects system information and logs using snap command.
    - C(snapcore) gathers core dumps and crash data using snapcore comamnd.
    - C(snapsplit) splits and processes collected snap data using snapsplt command.
    type: str
    choices: [ snap, snapcore, snapsplit ]
    default: snap
  all_info:
    description:
    - Gathers all available system information.
    - This is a comprehensive option that includes data across all categories, such as hardware, software, configuration files, and logs.
    type: bool
    default: false
    required: false
  compress:
    description:
    - Compresses the collected data into a single archive, typically snap.pax.gz.
    - This is useful for easier file management and transport of the snapshot
    type: bool
    default: false
  reset:
    description:
    - Removes the snap output directory (default /tmp/ibmsupt).
    - This cleans up previously gathered snapshot data, often to make room for a new snapshot
    type: bool
    default: false
  hacmp:
    description:
    - Gathers HACMP (High Availability Cluster Multiprocessing) error information.
    - This is specific to AIX high-availability cluster environments and helps troubleshoot HA-related errors
    type: bool
    default: false
  general_info:
    description:
    - Gathers general information.
    type: bool
    default: false
  file_system_info:
    description:
    - Gathers file system information, including details on disk usage, mount points, and file system integrity.
    - This is crucial for diagnosing storage and disk-related issues
    type: bool
    default: false
  live_kernel:
    description:
    - Collects Live kernel update information and saves it in the /tmp/ibmsupt/liveupdate directory.
    type: bool
    default: false
  collects_dump:
    description:
    - Collects dump and /unix files, along with any live dump data. This is valuable for diagnosing kernel and system crashes
    type: bool
    default: false
  installation_info:
    description:
    - Gathers installation information, such as installed software packages, patches, and configurations.
    - This helps diagnose installation-related issues.
    type: bool
    default: false
  kernel_info:
    description:
    - Collects kernel-related data, including kernel configuration and status.
    - This is essential for debugging kernel-specific issues.
    type: bool
    default: false
  security_info:
    description:
    - Gathers security information, including access controls, permissions, and user data.
    - This is important for diagnosing security issues and auditing.
    type: bool
    default: false
  workload_manager_info:
    description:
    - Gather workload manager (WLM) information, which includes data related to workload management on the system.
    type: bool
    default: false
  hardware_info:
    description:
    - Gather hardware information
    type: bool
    default: false
  ss_filename:
    description:
    - Specifies the filename for the snapsplit operation.
    - This determines the output file name used for storing snap data.
    type: str
  ss_timestamp:
    description:
    - Specifies the timestamp for the snapsplit operation.
    - This is useful for organizing and restoring snapshots based on time.
    type: str
  ss_machinename:
    description:
    - Specifies the machine name for the snapsplit operation.
    - Helps in identifying the source system for the collected data.
    type: str
  ss_size:
    description:
    - Defines the size limit for snap data storage.
    - Helps in controlling the disk space used by the snapsplit operation.
    type: str
  ss_rejoining:
    description:
    - Determines whether previously split snap files should be rejoined.
    - If set to C(true), snapsplit will attempt to reconstruct snap files.
    type: bool
    default: false
  sc_output_dir:
    description:
    - Specifies the directory where snapcore output files will be stored.
    - Helps in organizing collected core files.
    type: str
  sc_core_file:
    description:
    - Specifies the core file to be gather.
    - Used for diagnosing system debugging.
    type: str
  sc_program_name:
    description:
    - Defines the name of the program related to the core file.
    type: str
  sc_remove_core:
    description:
    - Determines whether the core file should be removed after processing.
    - If set to C(true), the core file will be deleted after analysis.
    type: bool
    default: false

notes:
  - You can refer to the IBM documentation for additional information on the snap command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/snap.html).
'''

EXAMPLES = r'''
- name: Collect hardware related data
  ibm.power_aix.snap:
    action: "snap"
    option: -h

- name: Clear old snap data
  ibm.power_aix.snap:
    action: "snap"
    option: -r

- name: Collect file system data
  ibm.power_aix.snap:
    action: "snap"
    option: -f

- name: Collect all system data
  ibm.power_aix.snap:
    action: "snap"
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


from ansible.module_utils.basic import AnsibleModule
import shutil
__metaclass__ = type


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


def build_snapsplit_command(module):
    """
    Build the snapsplit command with specified options
    arguments:
     module (AnsibleModule): The Ansible module instance.
    Returns:
        cmd - A successfully created snapsplit command
    """
    cmd = ['snapsplit']
    if module.params['ss_filename']:
        if module.params['ss_size']:
            cmd += [f" -s {module.params['ss_size']}"]
        if module.params['ss_machinename']:
            cmd += [f" -H {module.params['ss_machinename']}"]
        cmd += [f" -f {module.params['ss_filename']}"]
    elif module.params['ss_rejoining']:
        cmd += ['-u']
        if module.params['ss_timestamp']:
            cmd += [f" -T {module.params['ss_timestamp']}"]
        if module.params['ss_machinename']:
            cmd += [f" -H {module.params['ss_machinename']}"]
    return cmd


def build_snapcore_command(module):
    """
    Build the snapcore command with specified options
    arguments:
     module (AnsibleModule): The Ansible module instance.
    Returns:
        cmd - A successfully created snapcore command
    """
    cmd = ['snapcore']
    if module.params['sc_output_dir']:
        cmd.append(f"-d {module.params['sc_output_dir']}")
    # Check for the remove option (-r)
    if module.params['sc_remove_core']:
        cmd.append('-r')
    if module.params['sc_core_file']:
        cmd.append(module.params['sc_core_file'])
    if module.params['sc_program_name']:
        cmd.append(module.params['sc_program_name'])
    return cmd


def main():
    # Define the arguments the module accepts
    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', default='snap', choices=['snap', 'snapcore', 'snapsplit']),
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
            ss_filename=dict(type='str'),
            ss_timestamp=dict(type='str'),
            ss_machinename=dict(type='str'),
            ss_size=dict(type='str'),
            ss_rejoining=dict(type='bool', default=False),
            sc_output_dir=dict(type='str'),
            sc_core_file=dict(type='str'),
            sc_program_name=dict(type='str'),
            sc_remove_core=dict(type='bool', default=False),
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
    action = module.params['action']
    if action == 'snap':
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
                msg = f"Unable to run the snap command: {cmd}"
                module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
            else:
                result['changed'] = True
                result['msg'] = f"Snap command executed successfully with option {cmd}"

    elif action == 'snapsplit':
        cmd = build_snapsplit_command(module)
        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = ' '.join(cmd)
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            msg = f"Unable to run the snapsplit command: {cmd}"
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            result['changed'] = True
            result['msg'] = f"Snapsplit command executed successfully with option {cmd}"
    elif action == 'snapcore':
        cmd = build_snapcore_command(module)
        rc, stdout, stderr = module.run_command(cmd)
        result['cmd'] = ' '.join(cmd)
        result['rc'] = rc
        result['stdout'] = stdout
        result['stderr'] = stderr
        if rc != 0:
            msg = f"Unable to run the snapcore command: {cmd}"
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
        else:
            result['changed'] = True
            result['msg'] = f"Snapcore command executed successfully with option {cmd}"
    module.exit_json(**result)


if __name__ == '__main__':
    main()
