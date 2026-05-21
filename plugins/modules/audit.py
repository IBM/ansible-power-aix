#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2025- IBM, Inc
# GNU General Public License v3.0+
# (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: audit
author:
  - AIX Development Team (@vivekpandeyibm)
short_description: Control the AIX auditing subsystem.
description:
  - Provides Ansible automation support for managing AIX audit subsystem using the audit command.
  - The module supports start, shutdown, on, off, and query operations with validation for WPAR and fullpath/panic options.
  - It reads configuration from /etc/security/audit/config and related audit configuration files.
version_added: "2.2.0"
requirements:
  - AIX >= 7.1
options:
  action:
    description:
      - Defines the audit operation to perform.
      - C(start) Starts the audit subsystem. This option reads the instructions in the configuration files and performs the auditing
      - C(shutdown) Stops the collection of audit records and resets the configuration information by removing the definition of classes from the kernel tables
      - C(off) Suspends the auditing system, but leaves the configuration valid. Data collection pauses until you give the 'audit on' command
      - C(on) Restarts the auditing system after a suspension.
      - C(query) Queries the auditing status of the audit subsystem.
    required: true
    type: str
    choices: [ 'start', 'shutdown', 'on', 'off', 'query' ]
  panic:
    description:
      - Used only with C(action=on). Enables panic mode (system halts if bin data cannot be written).
    type: bool
    default: false
  fullpath:
    description:
      - Used with C(action=on). Enables full path capture for FILE_* and PROC_* events.
    type: bool
    default: false
  recorded_output:
    description:
      - File path where audit logs will be saved using auditpr.
      - Log capture is only performed for C(query), C(shutdown), and C(off) actions.
      - Requires binary mode (binmode = on) in /etc/security/audit/config.
      - The output file will be overwritten on each run to avoid duplicate data.
    type: str
  audit_trail_path:
    description:
      - Path to audit trail file or directory. Overrides the path from /etc/security/audit/config.
      - If a specific file is provided, only that file will be processed.
      - If a directory is provided, all trail files (trail, bin1, bin2, auditb) in that directory will be processed.
    type: str
  capture_delay:
    description:
      - Seconds to wait before capturing logs (only for C(query) action).
      - Ensures recent events are flushed to disk before reading.
    type: int
    default: 2
  auditpr_verbose:
    description:
      - Enable verbose output in auditpr (-v flag).
    type: bool
    default: true
  auditpr_header_type:
    description:
      - Header display type for auditpr output.
      - 0 = no header, 1 = header once, 2 = header repeated.
    type: int
    default: 1
    choices: [0, 1, 2]
  auditpr_fields:
    description:
      - Comma-separated list of fields to display in auditpr output.
      - "Available fields: E(event), l(login), R(result), t(time), c(command), r(real_user), p(pid), P(ppid), T(tid), h(host), W(wpar)"
    type: str
    default: 'E,l,R,t,c,r,p,P,T,h,W'
  auditpr_message:
    description:
      - Custom message to display with each heading in auditpr output (-m flag).
    type: str
  auditpr_suppress_translation:
    description:
      - Suppress ID translation to symbolic names in auditpr output (-r flag).
    type: bool
    default: false
  auditpr_single_line:
    description:
      - Display trail and audit record in single line (-w flag). Mutually exclusive with auditpr_verbose.
    type: bool
    default: false
  auditpr_long_usernames:
    description:
      - Print long user names at end of audit record (-X flag).
    type: bool
    default: false
notes:
  - Refer to IBM documentation for more details U(https://www.ibm.com/docs/en/aix/7.3?topic=a-audit-command)
'''

EXAMPLES = r'''
- name: Start the AIX audit subsystem
  audit:
    action: start

- name: Turn auditing off
  audit:
    action: 'off'

- name: Restart audit with panic mode
  audit:
    action: 'on'
    panic: true

- name: Query audit subsystem status
  audit:
    action: query

- name: Query audit and capture logs
  audit:
    action: query
    recorded_output: /var/log/audit.log

- name: Stop audit and capture complete logs
  audit:
    action: shutdown
    recorded_output: /var/log/audit_final.log

- name: Capture logs with custom fields
  audit:
    action: query
    recorded_output: /var/log/audit_custom.log
    auditpr_fields: 'E,l,t,c'

- name: Capture logs with custom auditpr options
  audit:
    action: query
    recorded_output: /var/log/audit_verbose.log
    auditpr_verbose: true
    auditpr_header_type: 1
    auditpr_fields: 'E,l,R,t,c,r,p,P,T,h,W'
    auditpr_long_usernames: true

- name: Stop and capture final logs
  audit:
    action: shutdown
    recorded_output: /var/log/audit_final.log
'''

RETURN = r'''
msg:
    description: Execution message indicating success or failure. Includes audit log capture details when recorded_output is specified.
    returned: always
    type: str
    sample: >
      Audit command executed successfully with cmd: 'audit query'
      Audit logs from 2 trail file(s) written to '/var/log/audit.log'
      using command: 'auditpr -i /audit/trail -v -t 1 -h E,l,R,t,c,r,p,P,T,h,W'.

cmd:
    description: Full audit command executed.
    returned: always
    type: str
    sample: 'audit query'
rc:
    description: Return code from audit command.
    returned: always
    type: int
stdout:
    description: Standard output from audit command.
    returned: always
    type: str
stderr:
    description: Error output from audit command (if any).
    returned: on failure
    type: str
log_capture_performed:
    description: Whether log capture was performed.
    returned: when recorded_output is specified
    type: bool
    sample: true
auditpr_cmd:
    description: The auditpr command used to capture audit logs.
    returned: when log capture is performed
    type: str
    sample: 'auditpr -i /audit/trail -v -t 1 -h E,l,R,t,c,r,p,P,T,h,W'
'''

from ansible.module_utils.basic import AnsibleModule
import os
import re
import time

# Module-level constants
AUDIT_TRAIL_FILES = ['trail', 'bin1', 'bin2', 'auditb']
MIN_CAPTURE_DELAY = 0
MAX_CAPTURE_DELAY = 300


def check_audit_config_file(module):
    """
    Check audit configuration file:
    arguments:
        module  (dict): The Ansible module
    Returns:
        True : If all the configration file is present
    """

    required_files = [
        "/etc/security/audit/config",
        "/etc/security/audit/events",
        "/etc/security/audit/objects",
        "/etc/security/audit/bincmds",
        "/etc/security/audit/streamcmds"
    ]

    missing = []
    unreadable = []

    for f in required_files:
        if not os.path.exists(f):
            missing.append(f)
        elif not os.access(f, os.R_OK):
            unreadable.append(f)

    if missing:
        module.fail_json(msg=f"Missing audit configuration files: {', '.join(missing)}")

    if unreadable:
        module.fail_json(msg=f"Unreadable audit configuration files: {', '.join(unreadable)}")

    return True


def validate_audit_status(module):
    """
    Applies REAL AIX audit state rules including:
      - No 'start' when auditing on
      - No 'on' when auditing on
      - No 'shutdown' when auditing off
      - No 'off' when system already fully shutdown
      - Check mutual exclusiveness of options
    """

    action = module.params['action']
    panic = module.params['panic']
    fullpath = module.params['fullpath']

    if panic and action != "on":
        module.fail_json(msg=f" 'panic' option is not allowed with action: '{action}'.")
    if fullpath and action != "on":
        module.fail_json(
            msg=f"'fullpath' option is not allowed with action: '{action}'."
        )

    # Query always executes
    if action == "query":
        return True

    rc, stdout, stderr = module.run_command(["audit", "query"])

    if rc != 0:
        module.fail_json(msg=f"Failed to run 'audit query': {stderr}", rc=rc)

    auditing_on = bool(re.search(r"auditing\s+on", stdout, re.IGNORECASE))
    auditing_off = bool(re.search(r"auditing\s+off", stdout, re.IGNORECASE))
    events_empty = bool(re.search(r"audit events:\s*none", stdout, re.IGNORECASE))

    if auditing_on and action == "start":
        module.exit_json(
            changed=False,
            msg="Audit already ON — cannot run 'audit start' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    if auditing_on and action == "on":
        module.exit_json(
            changed=False,
            msg="Audit already ON — cannot run 'audit on' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    if auditing_off and action == "shutdown":
        module.exit_json(
            changed=False,
            msg="Audit already OFF — cannot run 'audit shutdown' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    if (auditing_off or events_empty) and action == "off":
        module.exit_json(
            changed=False,
            msg="Audit already OFF — cannot run 'audit off' again.",
            stdout=stdout, stderr=stderr, rc=0
        )

    return True


def build_audit_command(module):
    '''
    Build the audit command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created audit command
    '''

    cmd = ['audit']
    action = module.params['action']
    panic = module.params['panic']
    fullpath = module.params['fullpath']

    if action == 'on':
        cmd.append('on')
        if panic:
            cmd.append('panic')
        if fullpath:
            cmd.append('fullpath')

    elif action == 'off':
        cmd.append('off')

    elif action == 'start':
        cmd.append('start')

    elif action == 'shutdown':
        cmd.append('shutdown')

    elif action == 'query':
        cmd.append('query')

    return cmd


def should_capture_logs(action):
    '''
    Check if we should capture logs for this action

    Arguments:
        action (str): The audit action

    Returns:
        bool - True if logs should be captured
    '''
    return action in ['shutdown', 'off', 'query']


def read_audit_config(config_file):
    '''
    Read audit configuration and return binmode and trail path

    Arguments:
        config_file (str): Path to audit config file

    Returns:
        tuple: (binmode_on, trail_path)
    '''
    binmode_on = False
    trail_path = None
    current_section = None

    with open(config_file, 'r') as f:
        for line in f:
            line = line.strip()

            # Skip empty lines and comments
            if not line or line.startswith('*') or line.startswith('#'):
                continue

            # Track which section we're in
            if line.endswith(':'):
                current_section = line[:-1].strip()
                continue

            # Look for binmode in start section
            if current_section == 'start' and 'binmode' in line and '=' in line:
                value = line.split('=')[1].strip()
                binmode_on = (value.lower() == 'on')

            # Look for trail path in bin section
            if current_section == 'bin' and 'trail' in line and '=' in line:
                trail_path = line.split('=')[1].strip()

    return binmode_on, trail_path


def validate_for_log_capture(module):
    '''
    Validate audit configuration for log capture

    Arguments:
        module (dict): The Ansible module

    Returns:
        trail_path - Valid trail path
    '''
    config_file = '/etc/security/audit/config'
    user_trail_path = module.params.get('audit_trail_path')

    if not os.path.exists(config_file):
        module.fail_json(msg="Config file not found: {}".format(config_file))

    try:
        binmode_on, config_trail_path = read_audit_config(config_file)
    except Exception as e:
        module.fail_json(msg="Cannot read config file: {}".format(str(e)))

    if not binmode_on:
        module.fail_json(msg="Binary mode is off. Set 'binmode = on' in {}".format(config_file))

    trail_path = user_trail_path if user_trail_path else config_trail_path

    if not trail_path:
        module.fail_json(msg="Trail path not configured. Add 'trail = /path' in {}".format(config_file))

    if not os.path.exists(trail_path):
        module.fail_json(msg="Trail path does not exist: {}".format(trail_path))

    if not os.access(trail_path, os.R_OK):
        module.fail_json(msg="Trail path not readable: {}".format(trail_path))

    return trail_path


def find_trail_files(trail_path):
    '''
    Find trail files based on user input

    Logic:
    - If trail_path is a FILE: return only that specific file
    - If trail_path is a DIRECTORY: return all trail files in that directory

    Arguments:
        trail_path (str): Path to specific trail file or directory containing trail files

    Returns:
        trail_files - List of trail file paths
    '''
    trail_files = []

    # Case 1: User specified a specific file
    if os.path.isfile(trail_path):
        try:
            if os.path.getsize(trail_path) > 0:
                return [trail_path]  # Return only this specific file
            else:
                return []  # Empty file, skip
        except OSError:
            return []  # Can't access file

    # Case 2: User specified a directory
    elif os.path.isdir(trail_path):
        directory = trail_path
        for name in AUDIT_TRAIL_FILES:
            file_path = os.path.join(directory, name)
            try:
                if os.path.isfile(file_path) and os.path.getsize(file_path) > 0:
                    trail_files.append(file_path)
            except OSError:
                # Skip files that can't be accessed
                continue
        return trail_files

    # Case 3: Path doesn't exist or is neither file nor directory
    else:
        return []


def build_auditpr_command(module, trail_file):
    '''
    Build the auditpr command with specified options

    Arguments:
        module (dict): The Ansible module
        trail_file (str): Path to the audit trail file

    Returns:
        cmd - A successfully created auditpr command
    '''

    cmd = ['/usr/sbin/auditpr', '-i', trail_file]

    # Mutually exclusive: -v (verbose) or -w (single-line)
    if module.params.get('auditpr_single_line'):
        cmd.append('-w')
    elif module.params.get('auditpr_verbose'):
        cmd.append('-v')

    # Header type: -t {0|1|2}
    if module.params.get('auditpr_header_type') is not None:
        cmd.extend(['-t', str(module.params['auditpr_header_type'])])

    # Fields to display: -h field[,field]*
    if module.params.get('auditpr_fields'):
        cmd.extend(['-h', module.params['auditpr_fields']])

    # Message: -m "Message"
    if module.params.get('auditpr_message'):
        cmd.extend(['-m', module.params['auditpr_message']])

    # Suppress ID translation: -r
    if module.params.get('auditpr_suppress_translation'):
        cmd.append('-r')

    # Long usernames: -X
    if module.params.get('auditpr_long_usernames'):
        cmd.append('-X')

    return cmd


def capture_audit_logs(module, result):
    '''
    Capture audit logs from trail files with improved error handling

    Arguments:
        module (dict): The Ansible module
        result (dict): The result dictionary

    Returns:
        result - Updated result dictionary
    '''
    output_file = module.params['recorded_output']
    trail_path = module.params['audit_trail_path']

    trail_files = find_trail_files(trail_path)
    if not trail_files:
        result['msg'] += " Warning: No trail files found."
        return result

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.exists(output_dir):
        try:
            os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            result['msg'] = "Failed to create directory {}: {}".format(output_dir, str(e))
            module.fail_json(**result)

    mode = 'w'  # Always overwrite to avoid duplicate data
    mode_text = 'written'
    auditpr_cmd = None
    failed_files = []
    successful_files = 0

    try:
        with open(output_file, mode) as f:
            for trail_file in trail_files:
                cmd = build_auditpr_command(module, trail_file)

                # Store first command for message
                if auditpr_cmd is None:
                    auditpr_cmd = ' '.join(cmd)

                rc, stdout, stderr = module.run_command(cmd)

                if rc == 0 and stdout:
                    f.write(stdout + '\n')
                    successful_files += 1
                else:
                    failed_files.append(trail_file)
                    f.write("Error reading {}: {}\n".format(trail_file, stderr))

        result['msg'] += " Audit logs from {} trail file(s) {} to '{}' using command: '{}'.".format(
            successful_files, mode_text, output_file, auditpr_cmd
        )
        # Add auditpr command to result
        if auditpr_cmd:
            result['auditpr_cmd'] = auditpr_cmd

        if failed_files:
            result['msg'] += " Warning: {} file(s) failed: {}".format(
                len(failed_files), ', '.join([os.path.basename(f) for f in failed_files])
            )

    except Exception as e:
        result['msg'] += " Error saving logs: {}".format(str(e))

    return result


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['start', 'shutdown', 'on', 'off', 'query']),
            panic=dict(type='bool', default=False),
            fullpath=dict(type='bool', default=False),
            recorded_output=dict(type='str'),
            audit_trail_path=dict(type='str'),
            capture_delay=dict(type='int', default=2),
            auditpr_verbose=dict(type='bool', default=True),
            auditpr_header_type=dict(type='int', default=1, choices=[0, 1, 2]),
            auditpr_fields=dict(type='str', default='E,l,R,t,c,r,p,P,T,h,W'),
            auditpr_message=dict(type='str'),
            auditpr_suppress_translation=dict(type='bool', default=False),
            auditpr_single_line=dict(type='bool', default=False),
            auditpr_long_usernames=dict(type='bool', default=False),
        ),
        mutually_exclusive=[
            ['auditpr_verbose', 'auditpr_single_line']
        ],
        supports_check_mode=False
    )

    action = module.params['action']
    recorded_output = module.params['recorded_output']
    capture_delay = module.params['capture_delay']

    # Validate capture_delay range
    if capture_delay < MIN_CAPTURE_DELAY or capture_delay > MAX_CAPTURE_DELAY:
        module.fail_json(
            msg="Parameter 'capture_delay' must be between {} and {} seconds. Got: {}".format(
                MIN_CAPTURE_DELAY, MAX_CAPTURE_DELAY, capture_delay
            )
        )

    # Early validation: fail if recorded_output is used with non-capturable actions
    if recorded_output and not should_capture_logs(action):
        module.fail_json(
            msg="Parameter 'recorded_output' is only supported with actions: 'query', 'shutdown', or 'off'. "
                "Current action '{}' does not support log capture.".format(action)
        )

    # Validate configuration if log capture is requested
    if recorded_output and should_capture_logs(action):
        trail_path = validate_for_log_capture(module)
        module.params['audit_trail_path'] = trail_path

    check_audit_config_file(module)
    validate_audit_status(module)

    cmd = build_audit_command(module)

    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=False)

    result = {
        'changed': True,
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout.strip(),
        'stderr': stderr.strip(),
    }

    if rc != 0:
        result['msg'] = f"audit command failing with command: '{' '.join(cmd)}'"
        module.fail_json(**result)

    if module.params['action'] == 'query' and not module.params['recorded_output']:
        result['changed'] = False

    result['msg'] = f"Audit command executed successfully with cmd: '{' '.join(cmd)}'"

    # Capture logs if requested (validation already done earlier)
    if recorded_output:
        # Wait only for query action
        if action == 'query':
            time.sleep(module.params['capture_delay'])

        result = capture_audit_logs(module, result)
        result['log_capture_performed'] = True

    module.exit_json(**result)


if __name__ == '__main__':
    main()
