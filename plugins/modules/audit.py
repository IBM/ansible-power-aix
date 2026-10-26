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
      - C(add_events) Adds the events given in C(audit_events) to the audit class C(audit_class) in /etc/security/audit/config.
        Events that are already present are not added again.
      - C(remove_events) Removes the events given in C(audit_events) from the audit class C(audit_class) in /etc/security/audit/config.
        Events that are not present are skipped.
    required: true
    type: str
    choices: [ 'start', 'shutdown', 'on', 'off', 'query', 'add_events', 'remove_events' ]
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
      - "Available fields: C(E) (event), C(l) (login), C(R) (result), C(t) (time), C(c) (command), C(r) (real_user), C(p) (pid), C(P) (ppid), C(T) (tid),
         C(h) (host), C(W) (wpar)"
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
  audit_events:
    description:
      - List of audit event names to add to or remove from the audit class.
      - Required when C(action=add_events) or C(action=remove_events), and allowed only with these two actions.
      - For C(add_events), every event must be defined in /etc/security/audit/events, otherwise the task fails and nothing is changed.
      - Event names are case-sensitive and can contain only letters, digits and underscore.
      - Duplicate names in the list are ignored.
    type: list
    elements: str
  audit_class:
    description:
      - Name of the audit class in the C(classes) stanza of /etc/security/audit/config.
      - Used only with C(action=add_events) or C(action=remove_events).
      - If the class does not exist, C(add_events) creates it.
      - Removing all events from a class is not allowed, because at least one event must remain.
    type: str
    default: general
  backup:
    description:
      - Create a backup copy of /etc/security/audit/config before changing it.
      - The backup file name includes a timestamp, so older configuration can be restored if needed.
      - A backup is created only when the file is actually changed.
      - Used only with C(action=add_events) or C(action=remove_events).
    type: bool
    default: false
notes:
  - Refer to IBM documentation for more details U(https://www.ibm.com/docs/en/aix/7.3?topic=a-audit-command)
  - Changes made by C(add_events) and C(remove_events) are written only to /etc/security/audit/config.
    To load them into the kernel, run C(action=shutdown) and then C(action=start).
  - A new audit class created by C(add_events) is audited only after it is assigned to users in the C(users) stanza.
  - A custom event must first be defined in /etc/security/audit/events before it can be added to an audit class.
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

- name: Add audit events to the general class
  audit:
    action: add_events
    audit_events:
      - FILE_Open
      - FILE_Read
      - USER_SU

- name: Add audit events to a custom class
  audit:
    action: add_events
    audit_class: security_watch
    audit_events:
      - PASSWORD_Change
      - USER_Login

- name: Add audit events and keep a backup of the old config
  audit:
    action: add_events
    backup: true
    audit_events:
      - FILE_Open

- name: Remove audit events from the general class
  audit:
    action: remove_events
    audit_events:
      - FS_Chdir

- name: Stop audit to apply the new event configuration
  audit:
    action: shutdown

- name: Start audit with the new event configuration
  audit:
    action: start
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
    returned: when action is start, shutdown, on, off or query
    type: str
    sample: 'audit query'
rc:
    description: Return code from audit command.
    returned: when action is start, shutdown, on, off or query
    type: int
stdout:
    description: Standard output from audit command.
    returned: when action is start, shutdown, on, off or query
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
audit_class:
    description: Audit class that was checked or updated.
    returned: when action is add_events or remove_events
    type: str
    sample: 'general'
events_added:
    description: Events that were newly added to the audit class.
    returned: when action is add_events
    type: list
    elements: str
    sample: ['FILE_Open', 'FILE_Read']
events_already_present:
    description: Requested events that were already in the audit class, so they were not added again.
    returned: when action is add_events
    type: list
    elements: str
    sample: ['USER_SU']
events_removed:
    description: Events that were removed from the audit class.
    returned: when action is remove_events
    type: list
    elements: str
    sample: ['FS_Chdir']
events_not_present:
    description: Requested events that were not in the audit class, so nothing was removed for them.
    returned: when action is remove_events
    type: list
    elements: str
    sample: ['FS_Rmdir']
audit_class_events:
    description: Final list of events in the audit class after the task.
    returned: when action is add_events or remove_events
    type: list
    elements: str
    sample: ['USER_SU', 'PASSWORD_Change', 'FILE_Open', 'FILE_Read']
backup_file:
    description: Name of the backup file created before the audit config file was changed.
    returned: when backup is true and the config file was changed
    type: str
    sample: '/etc/security/audit/config.12345.2026-10-24@11:40:12~'
'''

from ansible.module_utils.basic import AnsibleModule
import os
import re
import time
import tempfile

# Module-level constants
AUDIT_TRAIL_FILES = ['trail', 'bin1', 'bin2', 'auditb']
MIN_CAPTURE_DELAY = 0
MAX_CAPTURE_DELAY = 300
AUDIT_CONFIG_FILE = '/etc/security/audit/config'
AUDIT_EVENTS_FILE = '/etc/security/audit/events'
EVENT_ACTIONS = ['add_events', 'remove_events']
VALID_NAME_PATTERN = r'^[A-Za-z0-9_]+$'


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
        module.fail_json(msg="Config file not found: {0}".format(config_file))

    try:
        binmode_on, config_trail_path = read_audit_config(config_file)
    except Exception as e:
        module.fail_json(msg="Cannot read config file: {0}".format(str(e)))

    if not binmode_on:
        module.fail_json(msg="Binary mode is off. Set 'binmode = on' in {0}".format(config_file))

    trail_path = user_trail_path if user_trail_path else config_trail_path

    if not trail_path:
        module.fail_json(msg="Trail path not configured. Add 'trail = /path' in {0}".format(config_file))

    if not os.path.exists(trail_path):
        module.fail_json(msg="Trail path does not exist: {0}".format(trail_path))

    if not os.access(trail_path, os.R_OK):
        module.fail_json(msg="Trail path not readable: {0}".format(trail_path))

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
            result['msg'] = "Failed to create directory {0}: {1}".format(output_dir, str(e))
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
                    f.write("Error reading {0}: {1}\n".format(trail_file, stderr))

        result['msg'] += " Audit logs from {0} trail file(s) {1} to '{2}' using command: '{3}'.".format(
            successful_files, mode_text, output_file, auditpr_cmd
        )
        # Add auditpr command to result
        if auditpr_cmd:
            result['auditpr_cmd'] = auditpr_cmd

        if failed_files:
            result['msg'] += " Warning: {0} file(s) failed: {1}".format(
                len(failed_files), ', '.join([os.path.basename(f) for f in failed_files])
            )

    except Exception as e:
        result['msg'] += " Error saving logs: {0}".format(str(e))

    return result


def validate_event_options(module):
    '''
    Validate the options used with add_events / remove_events.

    Arguments:
        module (dict): The Ansible module

    Returns:
        requested_events - Clean list of event names (no spaces, no duplicates, user order kept)
    '''
    action = module.params['action']
    audit_class = module.params['audit_class']

    # panic and fullpath belong to 'audit on' only
    if module.params['panic'] or module.params['fullpath']:
        module.fail_json(msg="'panic' and 'fullpath' options are not allowed with action: '{0}'.".format(action))

    # Class name must be a simple name, for example: general, security_watch
    if not re.match(VALID_NAME_PATTERN, audit_class):
        module.fail_json(
            msg="Invalid audit class name: '{0}'. Use only letters, digits and underscore.".format(audit_class)
        )

    requested_events = []
    invalid_event_names = []

    for event_name in module.params['audit_events']:
        event_name = event_name.strip()

        # Skip empty names, for example '' or '   '
        if not event_name:
            continue

        if not re.match(VALID_NAME_PATTERN, event_name):
            invalid_event_names.append(event_name)
        elif event_name not in requested_events:
            # Add only once, so duplicates are ignored
            requested_events.append(event_name)

    if invalid_event_names:
        module.fail_json(
            msg="Invalid audit event names: {0}. Use only letters, digits and underscore.".format(
                ', '.join(invalid_event_names)
            )
        )

    if not requested_events:
        module.fail_json(msg="Parameter 'audit_events' must contain at least one event name.")

    return requested_events


def get_defined_audit_events(module):
    '''
    Read all event names defined in /etc/security/audit/events.

    Arguments:
        module (dict): The Ansible module

    Returns:
        defined_events - Set of event names known to the system
    '''
    defined_events = set()

    try:
        with open(AUDIT_EVENTS_FILE, 'r') as events_file:
            for line in events_file:
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith('*') or line.startswith('#'):
                    continue

                # Event lines look like: USER_SU = printf "%s"
                match = re.match(r'^([A-Za-z0-9_]+)\s*=', line)
                if match:
                    defined_events.add(match.group(1))
    except (IOError, OSError) as error:
        module.fail_json(msg="Cannot read {0}: {1}".format(AUDIT_EVENTS_FILE, str(error)))

    return defined_events


def read_audit_config_lines(module):
    '''
    Read the audit config file as a list of lines (line endings are kept).

    Arguments:
        module (dict): The Ansible module

    Returns:
        config_lines - List of lines from /etc/security/audit/config
    '''
    try:
        with open(AUDIT_CONFIG_FILE, 'r') as config_file:
            return config_file.readlines()
    except (IOError, OSError) as error:
        module.fail_json(msg="Cannot read {0}: {1}".format(AUDIT_CONFIG_FILE, str(error)))


def write_audit_config(module, config_lines):
    '''
    Safely write the audit config file.

    How it works:
      1. Create a temporary file in the same directory as the config file.
      2. Register it with add_cleanup_file, so Ansible deletes it automatically
         when the module ends (success or failure) if it still exists.
      3. Write all lines into the temporary file.
      4. atomic_move renames the temporary file to the config file.
         After the rename, the temporary file no longer exists, so nothing is left behind.
         atomic_move also keeps the owner and permissions of the original config file.

    Arguments:
        module (dict): The Ansible module
        config_lines (list): Lines to write
    '''
    config_dir = os.path.dirname(AUDIT_CONFIG_FILE)

    try:
        temp_fd, temp_path = tempfile.mkstemp(dir=config_dir)
    except (IOError, OSError) as error:
        module.fail_json(msg="Cannot create temporary file in {0}: {1}".format(config_dir, str(error)))

    # Ansible removes this file on exit_json / fail_json if it still exists
    module.add_cleanup_file(temp_path)

    try:
        with os.fdopen(temp_fd, 'w') as temp_file:
            temp_file.writelines(config_lines)
    except (IOError, OSError) as error:
        module.fail_json(msg="Cannot write temporary audit config file: {0}".format(str(error)))

    module.atomic_move(temp_path, AUDIT_CONFIG_FILE)


def find_classes_stanza(config_lines):
    '''
    Find the 'classes:' stanza header.

    Arguments:
        config_lines (list): Lines of the audit config file

    Returns:
        line index of 'classes:' or None if not found
    '''
    for line_index, line in enumerate(config_lines):
        if line.strip() == 'classes:':
            return line_index
    return None


def find_audit_class(config_lines, class_name):
    '''
    Find the class line inside the 'classes:' stanza and read its events.

    Example line:  general = USER_SU,PASSWORD_Change,FILE_Unlink

    Arguments:
        config_lines (list): Lines of the audit config file
        class_name (str): Audit class to look for

    Returns:
        tuple: (line_index, current_events)
               line_index is None when the class does not exist
    '''
    inside_classes_stanza = False

    for line_index, line in enumerate(config_lines):
        stripped_line = line.strip()

        # Skip empty lines and comments
        if not stripped_line or stripped_line.startswith('*') or stripped_line.startswith('#'):
            continue

        # A line ending with ':' starts a new stanza
        if stripped_line.endswith(':'):
            inside_classes_stanza = (stripped_line[:-1].strip() == 'classes')
            continue

        if inside_classes_stanza and '=' in stripped_line:
            name, value = stripped_line.split('=', 1)

            if name.strip() == class_name:
                # Value looks like: USER_SU,PASSWORD_Change,FILE_Unlink
                current_events = []
                for event_name in value.split(','):
                    event_name = event_name.strip()
                    if event_name:
                        current_events.append(event_name)
                return line_index, current_events

    return None, []


def update_class_line(config_lines, class_name, event_names, class_line_index, classes_header_index):
    '''
    Put the new event list of the class into config_lines.
      - If the class line exists, it is replaced (indentation is kept).
      - If the class does not exist, a new line is added just below 'classes:'.

    Arguments:
        config_lines (list): Lines of the audit config file
        class_name (str): Audit class name
        event_names (list): Final list of events for the class
        class_line_index (int): Index of the class line, or None for a new class
        classes_header_index (int): Index of the 'classes:' line

    Returns:
        config_lines - Updated list of lines
    '''
    events_text = ','.join(event_names)

    if class_line_index is not None:
        old_line = config_lines[class_line_index]

        # Keep the same leading spaces/tab as the old line.
        # Example: old_line = '\tgeneral = USER_SU\n'  ->  indentation = '\t'
        indentation = old_line[:len(old_line) - len(old_line.lstrip())]

        config_lines[class_line_index] = "{0}{1} = {2}\n".format(indentation, class_name, events_text)
    else:
        # Make sure the 'classes:' line ends with a newline before inserting below it
        if not config_lines[classes_header_index].endswith('\n'):
            config_lines[classes_header_index] += '\n'

        config_lines.insert(classes_header_index + 1, "\t{0} = {1}\n".format(class_name, events_text))

    return config_lines


def format_event_list(event_names):
    '''
    Return event names as text for messages, or 'none' if the list is empty.
    '''
    if not event_names:
        return 'none'
    return ', '.join(event_names)


def manage_audit_events(module):
    '''
    Add or remove audit events in an audit class of /etc/security/audit/config.
    This function always ends the module run (exit_json or fail_json).

    Idempotency:
      - add_events    : events already in the class are not added again.
      - remove_events : events not in the class are skipped.
      - If nothing changes, the module returns changed=False.

    Arguments:
        module (dict): The Ansible module
    '''
    action = module.params['action']
    class_name = module.params['audit_class']
    apply_hint = "Run 'audit shutdown' and then 'audit start' to load the new configuration."

    # Step 1: Validate options and clean the event list
    requested_events = validate_event_options(module)

    # Step 2: Read the config file and find the class
    config_lines = read_audit_config_lines(module)

    classes_header_index = find_classes_stanza(config_lines)
    if classes_header_index is None:
        module.fail_json(msg="'classes:' stanza not found in {0}.".format(AUDIT_CONFIG_FILE))

    class_line_index, current_events = find_audit_class(config_lines, class_name)

    result = {
        'changed': False,
        'audit_class': class_name,
    }

    # ---------------- add_events ----------------
    if action == 'add_events':
        # Every requested event must be defined in /etc/security/audit/events.
        # Unknown names (for example 'Ram_Event' or a typo like 'FILE_Opne')
        # stop the task here, before the config file is touched.
        defined_events = get_defined_audit_events(module)

        undefined_events = []
        for event_name in requested_events:
            if event_name not in defined_events:
                undefined_events.append(event_name)

        if undefined_events:
            module.fail_json(
                msg="Audit events not defined in {0}: {1}. Check the event name and its case. "
                    "A custom event must be defined in {0} before it can be added to an audit class.".format(
                        AUDIT_EVENTS_FILE, ', '.join(undefined_events)
                    ),
                **result
            )

        # Split requested events into "already in the class" and "new"
        events_already_present = []
        events_to_add = []
        for event_name in requested_events:
            if event_name in current_events:
                events_already_present.append(event_name)
            else:
                events_to_add.append(event_name)

        result['events_added'] = events_to_add
        result['events_already_present'] = events_already_present

        # Idempotent case: nothing new to add
        if not events_to_add:
            result['audit_class_events'] = current_events
            result['msg'] = "All requested events are already present in audit class '{0}': {1}. No change needed.".format(
                class_name, format_event_list(events_already_present)
            )
            module.exit_json(**result)

        # New events are added at the end, old order is kept
        updated_events = current_events + events_to_add

        if class_line_index is None:
            class_status = "Audit class '{0}' created in {1}.".format(class_name, AUDIT_CONFIG_FILE)
        else:
            class_status = "Audit class '{0}' updated in {1}.".format(class_name, AUDIT_CONFIG_FILE)

        result['msg'] = "{0} New events added: {1}. Events already present: {2}. {3}".format(
            class_status, format_event_list(events_to_add), format_event_list(events_already_present), apply_hint
        )

    # ---------------- remove_events ----------------
    else:
        # Split requested events into "in the class" (to remove) and "not in the class"
        events_to_remove = []
        events_not_present = []
        for event_name in requested_events:
            if event_name in current_events:
                events_to_remove.append(event_name)
            else:
                events_not_present.append(event_name)

        result['events_removed'] = events_to_remove
        result['events_not_present'] = events_not_present

        # Idempotent case: nothing to remove
        if not events_to_remove:
            result['audit_class_events'] = current_events
            if class_line_index is None:
                result['msg'] = "Audit class '{0}' does not exist in {1}. No change needed.".format(
                    class_name, AUDIT_CONFIG_FILE
                )
            else:
                result['msg'] = "None of the requested events are present in audit class '{0}': {1}. No change needed.".format(
                    class_name, format_event_list(events_not_present)
                )
            module.exit_json(**result)

        # Keep every current event that the user did not ask to remove
        updated_events = []
        for event_name in current_events:
            if event_name not in events_to_remove:
                updated_events.append(event_name)

        # A class with no events is not valid
        if not updated_events:
            module.fail_json(
                msg="Cannot remove all events from audit class '{0}'. At least one event must remain.".format(class_name),
                **result
            )

        result['msg'] = "Audit class '{0}' updated in {1}. Events removed: {2}. Events not present: {3}. {4}".format(
            class_name, AUDIT_CONFIG_FILE, format_event_list(events_to_remove),
            format_event_list(events_not_present), apply_hint
        )

    # ---------------- save the change ----------------
    # Backup is taken only here, so it happens only when the file really changes
    if module.params['backup']:
        result['backup_file'] = module.backup_local(AUDIT_CONFIG_FILE)

    config_lines = update_class_line(config_lines, class_name, updated_events, class_line_index, classes_header_index)
    write_audit_config(module, config_lines)

    result['changed'] = True
    result['audit_class_events'] = updated_events
    module.exit_json(**result)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', required=True,
                        choices=['start', 'shutdown', 'on', 'off', 'query', 'add_events', 'remove_events']),
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
            audit_events=dict(type='list', elements='str'),
            audit_class=dict(type='str', default='general'),
            backup=dict(type='bool', default=False),
        ),
        mutually_exclusive=[
            ['auditpr_verbose', 'auditpr_single_line']
        ],
        required_if=[
            ['action', 'add_events', ['audit_events']],
            ['action', 'remove_events', ['audit_events']],
        ],
        supports_check_mode=False
    )

    action = module.params['action']
    recorded_output = module.params['recorded_output']
    capture_delay = module.params['capture_delay']

    # Validate capture_delay range
    if capture_delay < MIN_CAPTURE_DELAY or capture_delay > MAX_CAPTURE_DELAY:
        module.fail_json(
            msg="Parameter 'capture_delay' must be between {0} and {1} seconds. Got: {2}".format(
                MIN_CAPTURE_DELAY, MAX_CAPTURE_DELAY, capture_delay
            )
        )

    # Early validation: fail if recorded_output is used with non-capturable actions
    if recorded_output and not should_capture_logs(action):
        module.fail_json(
            msg="Parameter 'recorded_output' is only supported with actions: 'query', 'shutdown', or 'off'. "
                "Current action '{0}' does not support log capture.".format(action)
        )

    # audit_events is allowed only with add_events / remove_events
    if module.params['audit_events'] and action not in EVENT_ACTIONS:
        module.fail_json(
            msg="Parameter 'audit_events' is only supported with actions: 'add_events' or 'remove_events'. "
                "Current action '{0}' does not support it.".format(action)
        )

    # backup is allowed only with add_events / remove_events
    if module.params['backup'] and action not in EVENT_ACTIONS:
        module.fail_json(
            msg="Parameter 'backup' is only supported with actions: 'add_events' or 'remove_events'. "
                "Current action '{0}' does not support it.".format(action)
        )

    # Audit event management only edits the config file and does not run the 'audit' command.
    # manage_audit_events() always ends the module run.
    if action in EVENT_ACTIONS:
        check_audit_config_file(module)
        manage_audit_events(module)

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
