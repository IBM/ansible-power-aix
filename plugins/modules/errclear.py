#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: errclear
short_description: Run the AIX errclear command to delete entries from the error log.
description:
  - Enables Ansible to invoke AIX's errclear utility to delete error log entries based on various filtering criteria.
  - The errclear command deletes error-log entries older than the number of days specified.
  - To delete all error-log entries, specify a value of 0 for the days parameter.
author:
  - AIX Development Team (@vivekpandeyibm)
version_added: "2.3.0"
requirements:
  - AIX >= 7.1
  - Root user privileges
options:
  days:
    description:
      - Number of days to keep in the error log. Entries older than this will be deleted.
      - Specify 0 to delete all entries.
    type: int
    required: true
  error_class:
    description:
      - Deletes error-log entries in the error classes specified.
      - The error records can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
      - C(H) hardware
      - C(S) software
      - C(O) errlogger command messages
      - C(U) undetermined
    type: str
  input_log:
    description:
      - Use specified error log file. If this flag is not specified, the value from the error log configuration database is used.
    type: str
  include_errids:
    description:
      - Deletes only the error-log entries specified by the ErrorID.
      - The ErrorID variables can be separated by a , (comma), or enclosed in " " (double quotation marks) and separated by a , (comma), or a space character.
    type: str
  exclude_errids:
    description:
      - Deletes all error-log entries except those specified by the ErrorID.
      - The ErrorID variable values can be separated by commas or enclosed in double-quotation marks and separated by commas or blanks.
    type: str
  include_labels:
    description:
      - Deletes only the error log entries specified by the ErrorLabel.
      - The ErrorLabel variable values can be separated by commas or enclosed in double-quotation marks and separated by commas or blanks.
    type: str
  exclude_labels:
    description:
      - Deletes all error log entries except those specified by the ErrorLabel.
      - The ErrorLabel variable values can be separated by commas or enclosed in double-quotation marks and separated by commas or blanks.
    type: str
  sequence_number:
    description:
      - Deletes error-log entries with the specified sequence numbers.
      - The sequence_number variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
    type: str
  machine:
    description:
      - Deletes error-log entries for the specified Machine variable.
      - The uname -m command returns the value of the Machine variable.
    type: str
  node:
    description:
      - Deletes error-log entries for the specified Node variable.
      - The uname -n command returns the value of the Node variable.
    type: str
  resource_names:
    description:
      - Deletes error-log entries for the resource names specified.
      - The resource_names is a list of names of resources that have detected errors.
      - The resource_names variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
    type: str
  resource_types:
    description:
      - Deletes error-log entries for the resource types specified.
      - For hardware errors, this is a device type. For software errors, the value is LPP.
      - The resource_types variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
    type: str
  resource_classes:
    description:
      - Deletes error-log entries for the resource classes specified.
      - For hardware errors, this is a device class.
      - The resource_classes variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
    type: str
  error_types:
    description:
      - Deletes error-log entries for error types specified.
      - The error types can be each separated by a , (comma), or enclosed in " " (double quotation marks) and separated by a , or a space character.
      - C(INFO) Information
      - C(PEND) Pending
      - C(PERF) Performance related entries
      - C(PERM) Permanent
      - C(TEMP) Temporary
      - C(UNKN) Unknown
    type: str
  template_file:
    description:
      - Uses the error-record template file specified.
    type: str

notes:
  - Only the root user can run this command.
  - The errclear command clears the specified entries, but does not decrease the error log file size.
  - You can refer to the IBM documentation for additional information on the errclear command at
    U(https://www.ibm.com/docs/en/aix/7.3?topic=e-errclear-command).
'''

EXAMPLES = r'''
- name: Delete all entries from the error log
  errclear:
    days: 0

- name: Delete all entries older than 30 days
  errclear:
    days: 30

- name: Delete all software error entries
  errclear:
    days: 0
    error_class: "S"

- name: Delete specific error IDs
  errclear:
    days: 0
    include_errids: "A924A5FC,DEADBEEF"

- name: Clear all entries from alternate error log file
  errclear:
    days: 0
    input_log: "/var/adm/ras/errlog.alternate"

- name: Clear all hardware entries from alternate error log
  errclear:
    days: 0
    input_log: "/var/adm/ras/errlog.alternate"
    error_class: "H"

- name: Delete entries older than 7 days for specific resource
  errclear:
    days: 7
    resource_names: "hdisk0"
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'errclear executed successfully with command: errclear 0'
cmd:
    description: The command executed.
    returned: always
    type: str
    sample: 'errclear 0'
rc:
    description: The command return code.
    returned: When the command is executed.
    type: int
    sample: 0
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
'''

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule
from datetime import datetime, timedelta

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def build_errclear_command(module):
    '''
    Build the errclear command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created errclear command
    '''

    cmd = ['errclear']

    # Fail: -j cannot be used with -k
    if module.params['include_errids'] and module.params['exclude_errids']:
        module.fail_json(msg="The -j option cannot be used with -k")

    # Fail: -J cannot be used with -K
    if module.params['include_labels'] and module.params['exclude_labels']:
        module.fail_json(msg="The -J option cannot be used with -K")

    if module.params['error_class']:
        cmd.extend(['-d', module.params['error_class']])

    if module.params['input_log']:
        cmd.extend(['-i', module.params['input_log']])

    if module.params['include_errids']:
        cmd.extend(['-j', module.params['include_errids']])

    if module.params['exclude_errids']:
        cmd.extend(['-k', module.params['exclude_errids']])

    if module.params['include_labels']:
        cmd.extend(['-J', module.params['include_labels']])

    if module.params['exclude_labels']:
        cmd.extend(['-K', module.params['exclude_labels']])

    if module.params['sequence_number']:
        cmd.extend(['-l', module.params['sequence_number']])

    if module.params['machine']:
        cmd.extend(['-m', module.params['machine']])

    if module.params['node']:
        cmd.extend(['-n', module.params['node']])

    if module.params['resource_names']:
        cmd.extend(['-N', module.params['resource_names']])

    if module.params['resource_types']:
        cmd.extend(['-R', module.params['resource_types']])

    if module.params['resource_classes']:
        cmd.extend(['-S', module.params['resource_classes']])

    if module.params['error_types']:
        cmd.extend(['-T', module.params['error_types']])

    if module.params['template_file']:
        cmd.extend(['-y', module.params['template_file']])

    # Days parameter is required and must be at the end
    cmd.append(str(module.params['days']))

    return cmd


def check_errors_exist(module):
    '''
    Check if errors matching the criteria exist before attempting to clear them
    Returns: (exists, count, check_cmd)
    '''
    # Build errpt command to check for matching errors
    check_cmd = ['errpt']

    # CRITICAL: Add input_log parameter to errpt command
    if module.params['input_log']:
        check_cmd.extend(['-i', module.params['input_log']])

    # For EXCLUDE operations (-k, -K), we need to check if ANY errors exist
    # because exclude means "clear everything EXCEPT these"
    if module.params['exclude_errids'] or module.params['exclude_labels']:
        # Don't add -k or -K to the check command
        # We just want to know if there are ANY errors in the log
        # The actual filtering will be done by errclear command
        pass
    else:
        # For INCLUDE operations, check for specific errors
        if module.params['include_errids']:
            check_cmd.extend(['-j', module.params['include_errids']])

        if module.params['include_labels']:
            check_cmd.extend(['-J', module.params['include_labels']])

    if module.params['sequence_number']:
        check_cmd.extend(['-l', module.params['sequence_number']])

    if module.params['machine']:
        check_cmd.extend(['-m', module.params['machine']])

    if module.params['node']:
        check_cmd.extend(['-n', module.params['node']])

    if module.params['resource_names']:
        check_cmd.extend(['-N', module.params['resource_names']])

    if module.params['resource_types']:
        check_cmd.extend(['-R', module.params['resource_types']])

    if module.params['resource_classes']:
        check_cmd.extend(['-S', module.params['resource_classes']])

    if module.params['error_types']:
        check_cmd.extend(['-T', module.params['error_types']])

    if module.params['template_file']:
        check_cmd.extend(['-y', module.params['template_file']])

    # Add date filter ONLY if days > 0
    # When days=0, we want to check ALL errors (no date filter)
    if module.params['days'] > 0:
        cutoff_date = datetime.now() - timedelta(days=module.params['days'])
        # Format: MMddhhmmyy
        end_date = cutoff_date.strftime('%m%d%H%M%y')
        check_cmd.extend(['-e', end_date])
    # When days=0, no date filter is added, so errpt returns ALL matching errors

    rc, stdout, stderr = module.run_command(check_cmd)

    if rc != 0:
        # Error running errpt - might be invalid parameters
        # Include stderr in the message for debugging
        error_msg = f"errpt check failed: {stderr.strip()}" if stderr else "errpt check failed"
        return False, 0, ' '.join(check_cmd), error_msg

    # Count lines (subtract 1 for header)
    lines = stdout.strip().split('\n') if stdout.strip() else []
    count = len(lines) - 1 if len(lines) > 1 else 0

    return count > 0, count, ' '.join(check_cmd)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            days=dict(type='int', required=True),
            error_class=dict(type='str'),
            input_log=dict(type='str'),
            include_errids=dict(type='str'),
            exclude_errids=dict(type='str'),
            include_labels=dict(type='str'),
            exclude_labels=dict(type='str'),
            sequence_number=dict(type='str'),
            machine=dict(type='str'),
            node=dict(type='str'),
            resource_names=dict(type='str'),
            resource_types=dict(type='str'),
            resource_classes=dict(type='str'),
            error_types=dict(type='str'),
            template_file=dict(type='str')
        ),
        supports_check_mode=False
    )

    result = dict(
        changed=False,
        msg='',
        cmd='',
        check_cmd='',
        errors_found=0,
        stdout='',
        stderr='',
    )

    # Check if errors exist before attempting to clear
    check_result = check_errors_exist(module)

    if len(check_result) == 4:
        # Error occurred during check
        errors_exist, error_count, check_cmd, error_msg = check_result
        result['check_cmd'] = check_cmd
        result['errors_found'] = error_count
        result['msg'] = f"Error checking for errors: {error_msg}. Check command: {check_cmd}"
        module.fail_json(**result)
    else:
        # Normal check result
        errors_exist, error_count, check_cmd = check_result
        result['check_cmd'] = check_cmd
        result['errors_found'] = error_count

    if not errors_exist:
        result['msg'] = f"No errors found matching criteria. Nothing to clear. Check command: {check_cmd}"
        module.exit_json(**result)

    # Build errclear command
    cmd = build_errclear_command(module)
    result['cmd'] = ' '.join(cmd)

    # Execute errclear command
    rc, stdout, stderr = module.run_command(cmd)

    result['rc'] = rc
    result['stdout'] = stdout

    if rc != 0:
        result['stderr'] = stderr
        result['msg'] = f"errclear failed with command: {result['cmd']}"
        module.fail_json(**result)
    else:
        result['changed'] = True
        result['msg'] = f"Successfully cleared {error_count} error(s) with command: {result['cmd']}"

    module.exit_json(**result)


if __name__ == '__main__':
    main()
