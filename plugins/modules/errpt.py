#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: errpt
short_description: Run the AIX errpt command to report logged system errors.
description:
  - Enables Ansible to invoke AIX's errpt utility with extensive flag support for log filtering.
author:
  - AIX Development Team (@vivekpandeyibm)
version_added: "2.0.0"
requirements:
  - AIX >= 7.1
options:
  detailed:
    description:
      - Displays information about errors in the error log file in detailed format .
    type: bool
    default: false
  short_detail:
    description:
      - Show shortened version of detailed error .
    type: bool
    default: false
  error_class:
    description:
      - Limits the error report to certain types of error records specified by the valid ErrorClassList variable .
      - The error records in the ErrorClassList variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
      - C(H) hardware
      - C(S) software
      - C(O) errlogger command messages
      - C(U) undetermined
    type: str
  consolidate_duplicates:
    description:
      - Consolidate duplicate errors .The detailed error report, obtained with the -a flag, reports the number, and first and last times of the duplicates
    type: bool
    default: false
  end_date:
    description:
      - Specifies all records posted prior to and including the EndDate variable, where the EndDate variable has the form mmddhhmmyy.
    type: str
  ascii_format:
    description:
      - Displays the ASCII representation of unformatted error-log entries..
    type: bool
    default: false
  input_log:
    description:
      - Use specified error log file. If this flag is not specified, the value from the error log configuration database is used
    type: str
  diag_log:
    description:
      - Use specified diagnostic log file. If this flag is not specified, the default pathname, /var/adm/ras/diag_log, is used.
    type: str
  include_errids:
    description:
      - Includes only the error-log entries specified by the ErrorID.
      - The ErrorID variables can be separated by a , (comma), or enclosed in " " (double quotation marks) and separated by a , (comma), or a space character
    type: str
  exclude_errids:
    description:
      - Excludes the error-log entries specified by the ErrorID.
      - The ErrorLabel variable values can be separated by commas or enclosed in double-quotation marks and separated by commas or blanks
    type: str
  include_labels:
    description:
      - Includes the error log entries specified by the ErrorLabel.
      - The ErrorLabel variable values can be separated by commas or enclosed in double-quotation marks and separated by commas or blanks
    type: str
  exclude_labels:
    description:
      - Excludes the error log entries specified by the ErrorLabel.
      - The ErrorLabel variable values can be separated by commas or enclosed in double-quotation marks and separated by commas or blanks
    type: str
  sequence_number:
    description:
      - Selects a unique error-log entry specified by the sequence_number variable.
      - The sequence_number variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
    type: str
  machine:
    description:
      - Includes error-log entries for the specified Machine variable .
    type: str
  node:
    description:
      - Includes error-log entries for the specified Node variable .
    type: str
  resource_names:
    description:
      - Generates a report of resource names specified by the resource_names.
      - The resource_names is a list of names of resources that have detected errors.
      - The resource_names variable can be separated by a , (comma), or enclosed in " " (double quotation marks)
      - And separated by a , (comma), or a space character.
    type: str
  start_date:
    description:
      - Specifies all records posted on and after the StartDate, where the StartDate variable has the format mmddhhmmyy.
    type: str
  error_types:
    description:
      - Limits the error report to error types specified by the valid error_types variables.
      - The error types can be each separated by a , (comma), or enclosed in " " (double quotation marks) and separated by a , or a space character
      - C(INFO) Information
      - C(PEND) Pending
      - C(PERF) Performance related entries
      - C(PERM) Permanent
      - C(TEMP) Temporary
      - C(UNKN) Unknown
    type: str
  recorded_output:
    description:
      - Folder path to command output in machine.
    type: str
  concatenated_output:
    description:
      - Controls whether the output of the vmstat command is appended to the output file or is overwrited.
      - If set to true, output will be appended to the file.
      - If set to false, the file will be overwritten with fresh output.
    type: bool
    required: true

notes:
  - You can refer to the IBM documentation for additional information on the vmstat command at
    U(https://www.ibm.com/docs/en/aix/7.3.0?topic=v-vmstat-command).
'''

EXAMPLES = r'''
- name: Get detailed error report
  errpt:
    detailed: true

- name: Get error report for specific error IDs
  errpt:
    include_errids: "A924A5FC,DEADBEEF"
    recorded_output: "/tmp/errpt.log"
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Group: foo SUCCESSFULLY created.'
cmd:
    description: The command executed.
    returned: always
    type: str
rc:
    description: The command return code.
    returned: When the command is executed.
    type: int
stdout':
    description: The standard output.
    returned: If the command failed.
    type: str
stderr':
    description: The standard error.
    returned: If the command failed.
    type: str
'''

__metaclass__ = type

from ansible.module_utils.basic import AnsibleModule

ANSIBLE_METADATA = {
    'metadata_version': '1.1',
    'status': ['preview'],
    'supported_by': 'community'
}


def build_errpt_command(module):
    '''
    Build the errpt command with specified options
    arguments:
        module  (dict): The Ansible module
    Returns:
        cmd - A successfully created errpt command
    '''

    cmd = ['errpt']

    # Fail: -A  cannot be used with: -a
    if module.params['short_detail'] and module.params['detailed']:
        module.fail_json(msg="The -A option cannot be used with -a ")

    if module.params['ascii_format']:
        cmd.append('-g')
    elif module.params['consolidate_duplicates']:
        cmd.append('-D')
    # Fail: -j  cannot be used with: -k
    if module.params['include_errids'] and module.params['exclude_errids']:
        module.fail_json(msg="The -j option cannot be used with  -k ")
    # Fail: -J  cannot be used with: -K
    if module.params['include_labels'] and module.params['exclude_labels']:
        module.fail_json(msg="The -J option cannot be used with  -K ")

    if module.params['detailed']:
        cmd.append('-a')

    if module.params['short_detail']:
        cmd.append('-A')

    if module.params['error_class']:
        cmd.extend(['-d', module.params['error_class']])

    if module.params['end_date']:
        cmd.extend(['-e', module.params['end_date']])

    if module.params['input_log']:
        cmd.extend(['-i', module.params['input_log']])

    if module.params['diag_log']:
        cmd.extend(['-I', module.params['diag_log']])

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

    if module.params['start_date']:
        cmd.extend(['-s', module.params['start_date']])

    if module.params['error_types']:
        cmd.extend(['-T', module.params['error_types']])

    return cmd


def main():
    module = AnsibleModule(
        argument_spec=dict(
            detailed=dict(type='bool', default=False),
            short_detail=dict(type='bool', default=False),
            error_class=dict(type='str'),
            consolidate_duplicates=dict(type='bool', default=False),
            end_date=dict(type='str'),
            ascii_format=dict(type='bool', default=False),
            input_log=dict(type='str'),
            diag_log=dict(type='str'),
            include_errids=dict(type='str'),
            exclude_errids=dict(type='str'),
            include_labels=dict(type='str'),
            exclude_labels=dict(type='str'),
            sequence_number=dict(type='str'),
            machine=dict(type='str'),
            node=dict(type='str'),
            resource_names=dict(type='str'),
            start_date=dict(type='str'),
            error_types=dict(type='str'),
            recorded_output=dict(type='str'),
            concatenated_output=dict(type='bool', required=True)
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

    cmd = build_errpt_command(module)
    rc, stdout, stderr = module.run_command(cmd, use_unsafe_shell=True)

    result = {
        'changed': False,
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr
    }

    joined_cmd = ' '.join(cmd)

    if rc != 0:
        module.fail_json(msg=f'errpt failed with command: {joined_cmd}', **result)
    else:
        if stdout.strip():  # Only proceed if output is not empty
            should_concat = module.params['concatenated_output']
            mode = 'a' if should_concat else 'w'  # 'a' = append, 'w' = overwrite
            if module.params['recorded_output']:
                with open(module.params['recorded_output'], mode) as f:
                    f.write(stdout + '\n')
                result['changed'] = True
                result['msg'] = f"errpt executed successfully with command '{joined_cmd}' and Output written to {module.params['recorded_output']}"
            else:
                result['msg'] = f"errpt executed successfully with command '{joined_cmd}'."
        else:
            result['changed'] = False
            result['msg'] = f"No error records matched the specified errpt options. errpt executed successfully with command '{joined_cmd}'."
    module.exit_json(**result)


if __name__ == '__main__':
    main()
