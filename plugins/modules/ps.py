#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025 IBM
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: ps
author:
  - Vivek Pandey (@vivekpandeyibm)
short_description: Gather process, thread, and workload partition information using ps on AIX
description:
  - This module runs the AIX ps command to collect detailed information about running processes and kernel threads.
  - It provides multiple filtering and formatting options including PID, user, group, workload class, and thread-level details.
  - Supports mutual exclusiveness validation among key display modes and ensures correctness of flag combinations.
version_added: "2.2.0"
requirements:
  - AIX >= 7.1
options:
  all_processes:
    description:
      - Displays all processes currently on the system (-A).
      - Includes both system and user processes.
      - Useful for a complete view of system activity.
    type: bool
    default: false

  processes_on_terminals:
    description:
      - Displays all processes associated with a terminal except session leaders (-a).
      - Excludes background daemons or non-terminal processes.
      - Helpful for viewing user-interactive processes only.
    type: bool
    default: false

  exclude_session_leaders:
    description:
      - Writes information to standard output about all processes, except the session leaders.
      - Excludes session leaders from the process list (-d).
    type: bool
    default: false

  exclude_kernel:
    description:
      - Writes information to standard output about all processes, except kernel processes (-e).
    type: bool
    default: false

  full_list:
    description:
      - Generates a full-format listing (-f).
      - Displays UID, PID, PPID, C, STIME, TTY, TIME, and CMD columns.
    type: bool
    default: false

  long_list:
    description:
      - Generates a long listing (-l).
      - Provides extended columns such as F, s, UID, PID, PPID, C, PRI, NI, ADDR, SZ, PSS, WCHAN, TTY, TIME, and CMD fields..
    type: bool
    default: false

  kernel_processes:
    description:
      - Displays only kernel processes (-k).
    type: bool
    default: false

  kernel_threads_processes:
    description:
      - Displays kernel threads and associated processes (-m).
      - Output lines for processes are followed by an extra output line for each kernel thread.
      - Use with "-o THREAD" for thread-specific columns like TID, PRI, and SC.
    type: bool
    default: false

  all_64bit:
    description:
      - Lists all 64-bit processes (-M).
      - Allows performance analysis specific to 64-bit applications.
    type: bool
    default: false

  no_thread_stats:
    description:
      - Gathers no thread statistics (-N).
      - With this flag, 'ps' reports those statistics that can be obtained by not traversing through the threads chain for the process.
      - Useful when thread enumeration causes performance overhead.
    type: bool
    default: false

  groups:
    description:
      - Displays processes belonging to specific effective groups (-G Glist).
      - Accepts group names or numeric GIDs (comma- or space-separated).
      - Useful for filtering process ownership by Unix group.
    type: str

  process_groups:
    description:
      - Writes information only about processes that are in the process groups that are listed for the Glist variable (-g Glist).
      - The Glist variable is either a comma-separated list of process group identifiers or a list of process group identifiers .
    type: str

  pids:
    description:
      - Displays only processes with specified PIDs (-p Plist).
      - Accepts one or more comma-separated process IDs.
      - Provides focused information on specific target processes.
    type: str

  descendants:
    description:
      - Generates a list of descendants of every pid that has been passed to it in the 'pidlist' variable (-L pidlist).
      - The list of descendants from all the given pid is printed in the order in which they appear in the process table.
    type: str

  ttys:
    description:
      - Displays processes associated with specific TTY devices (-t Tlist).
      - Accepts comma-separated or quoted terminal identifiers.
    type: str

  users_in_current_env:
    description:
      - Displays processes owned by specific users in the current environment (-u Ulist).
      - Accepts user names or numeric UIDs.
      - Supports comma- or space-separated values up to 128 entries.
    type: str

  all_users:
    description:
      - Displays only information about processes with the user ID numbers or login names that are specified for the Ulist variable(-U Ulist).
      - The '-U' flag only applies to the current operating environment
      - In the listing, the ps command displays the numerical user ID unless the '-f ' flag is used; then the command displays the login name.
      - Lists numeric or textual user identifiers.
    type: str

  alt_name_list:
    description:
      - Specifies an alternate system name list file (-n NameList).
      - The operating system does not use the '-n' flag because information is supplied directly to the kernel..
    type: str

  project:
    description:
      - Displays the Project name, Project origin, and subproject identifier for the project. (-P).
      - If the stick bit is set for the process, the project name is preceded by an asterisk '*' character.
      - The Project origin field designates the currently loaded project repository (LOCAL or LDAP).
    type: bool
    default: false

  full_names:
    description:
      - Prints all available characters of each user/group name instead of truncating to the first eight characters.(-X).
    type: bool
    default: false

  page_sizes_settings:
    description:
      - Displays data, text, stack, and shared memory page size settings (-Z).
      - Provides insight into page usage for memory analysis.
    type: bool
    default: false

  output_format:
    description:
      - Customizes output columns using a user-defined format string (-o Format).
      - Accepts multiple field specifiers such as pid, user, pcpu, pmem, comm.
    type: str

  sysv_format:
    description:
      - Displays information in the System V format (-F format).
      - Functions similar to the -o option but uses traditional System V field naming.
    type: str

  tree_pid:
    description:
      - Displays the process hierarchy rooted at the given PID (-T pid).
      - Uses ASCII art to show parent-child relationships.
      - Commonly used for visualizing process trees.
    type: int

  recorded_output:
    description:
      - Specifies a file path to save the ps command output.
      - If not provided, results are only returned in stdout.
    type: str

  concatenated_output:
    description:
      - Determines whether to append or overwrite the output file.
      - When true, new output is appended to existing logs.
    type: bool
    required: true

notes:
  - You can refer to the IBM documentation for additional information on the fcstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=p-ps-command).
'''

EXAMPLES = r'''
- name: Display all processes in long format
  ibm.power_aix.ps:
    all_processes: true
    long_list: true

- name: Display kernel threads with thread IDs
  ibm.power_aix.ps:
    kernel_threads_processes: true
    output_format: "pid,tid,user,pcpu,comm"

- name: Show process tree for PID 1000
  ibm.power_aix.ps:
    tree_pid: 1000
    full_list: true

- name: Save ps output to /tmp/ps_report.txt
  ibm.power_aix.ps:
    all_processes: true
    output_format: "pid,user,pcpu,pmem,comm"
    recorded_output: /tmp/ps_report.txt
    concatenated_output: true
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'ps comamnd executed SUCCESSFULLY'
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
import os


def validate_mutual_exclusiveness(module):
    '''
    Check the ps option mutually exclusiveness
    arguments:
        module  (dict): The Ansible module
    '''

    if module.params.get('output_format') and 'THREAD' in module.params['output_format'] and not module.params['kernel_threads_processes']:
        module.warn("Thread output is disabled. Use the -m flag to activate thread display before specifying -o THREAD for detailed thread information.")

    for opt in ['output_format', 'groups', 'process_groups', 'pids', 'ttys', 'all_users', 'users_in_current_env']:
        if module.params.get(opt):
            count = len([x for x in module.params[opt].replace('"', '').replace("'", '').replace(',', ' ').split() if x])
            if count > 128:
                module.fail_json(msg=f"The option '{opt}' exceeds AIX 128-item limit.")


def build_ps_command(module):
    '''
    Build the ps command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created ps command
    '''

    cmd = ['/bin/ps']

    if module.params['all_processes']:
        cmd.append('-A')
    elif module.params['exclude_session_leaders']:
        cmd.append('-d')
    elif module.params['exclude_kernel']:
        cmd.append('-e')
    elif module.params['processes_on_terminals']:
        cmd.append('-a')

    if module.params['full_list']:
        cmd.append('-f')
    if module.params['long_list']:
        cmd.append('-l')

    if module.params['kernel_processes']:
        cmd.append('-k')
    elif module.params['kernel_threads_processes']:
        cmd.append('-m')
    elif module.params['all_64bit']:
        cmd.append('-M')

    if module.params['no_thread_stats']:
        cmd.append('-N')
    if module.params['project']:
        cmd.append('-P')
    if module.params['full_names']:
        cmd.append('-X')
    if module.params['page_sizes_settings']:
        cmd.append('-Z')
    if module.params.get('groups'):
        cmd.extend(['-G', module.params['groups']])
    if module.params.get('process_groups'):
        cmd.extend(['-g', module.params['process_groups']])
    if module.params.get('pids'):
        cmd.extend(['-p', module.params['pids']])
    if module.params.get('descendants'):
        cmd.extend(['-L', module.params['descendants']])
    if module.params.get('ttys'):
        cmd.extend(['-t', module.params['ttys']])

    if module.params.get('users_in_current_env'):
        cmd.extend(['-u', module.params['users_in_current_env']])
    if module.params.get('all_users'):
        cmd.extend(['-U', module.params['all_users']])

    if module.params.get('alt_name_list'):
        cmd.extend(['-n', module.params['alt_name_list']])

    if module.params.get('output_format'):
        cmd.extend(['-o', module.params['output_format']])
    if module.params.get('tree_pid'):
        cmd.extend(['-T', str(module.params['tree_pid'])])
    if module.params.get('sysv_format'):
        cmd.extend(['-F', module.params['sysv_format']])
    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            all_processes=dict(type='bool', default=False),
            processes_on_terminals=dict(type='bool', default=False),
            exclude_session_leaders=dict(type='bool', default=False),
            exclude_kernel=dict(type='bool', default=False),
            full_list=dict(type='bool', default=False),
            long_list=dict(type='bool', default=False),
            kernel_processes=dict(type='bool', default=False),
            kernel_threads_processes=dict(type='bool', default=False),
            all_64bit=dict(type='bool', default=False),
            no_thread_stats=dict(type='bool', default=False),
            groups=dict(type='str'),
            process_groups=dict(type='str'),
            pids=dict(type='str'),
            descendants=dict(type='str'),
            ttys=dict(type='str'),
            users_in_current_env=dict(type='str'),
            all_users=dict(type='str'),
            alt_name_list=dict(type='str'),
            output_format=dict(type='str'),
            sysv_format=dict(type='str'),
            project=dict(type='bool', default=False),
            full_names=dict(type='bool', default=False),
            page_sizes_settings=dict(type='bool', default=False),
            tree_pid=dict(type='int'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True),
        ),
        supports_check_mode=False
    )

    result = dict(changed=False, cmd='', rc=0, stdout='', stderr='', msg='')

    validate_mutual_exclusiveness(module)
    cmd = build_ps_command(module)
    result['cmd'] = " ".join(cmd)

    rc, stdout, stderr = module.run_command(result['cmd'], use_unsafe_shell=True)
    result.update({'rc': rc, 'stdout': stdout, 'stderr': stderr})

    if rc != 0:
        result['msg'] = f"ps command failing with command {' '.join(cmd)}"
        module.fail_json(**result)
    else:
        if module.params['recorded_output']:
            output_file = module.params['recorded_output']
            should_concat = module.params['concatenated_output']
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                try:
                    os.makedirs(output_dir, exist_ok=True)
                except Exception as e:
                    result['msg'] = f"Failed to create directory {output_dir}: {str(e)}"
                    module.fail_json(**result)

            mode = 'a' if should_concat else 'w'  # 'a' = append, 'w' = overwrite
            with open(output_file, mode) as f:
                f.write(stdout + '\n')
            result['changed'] = True
            result['msg'] = f"lparstat executed successfully with command '{cmd}' and Output written to {output_file}"
        else:
            result['changed'] = False
            result['msg'] = f"lparstat executed successfully with command '{cmd}'"
        module.exit_json(**result)


if __name__ == '__main__':
    main()
