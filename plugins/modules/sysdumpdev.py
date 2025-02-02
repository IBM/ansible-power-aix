#!/usr/bin/python

# Copyright: (c) 2018, Terry Jones <terry.jones@example.org>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: sysdumpdev

short_description: Manage system dump settings

version_added: "2.1.0"

description: This module allows to update and display the system dump settings

author:
    - Oliver Stadler (@staoli)

requirements:
  - AIX
  - Python >= 3.6
  - 'Privileged user with authorizations'

options:
    state:
        description:
        - Specifies the action to be performed
        - C(present) specifies to update the system dump settings
        - C(fact) specifies to retrieve the current system dump settings
        choices: ['present', 'fact']
        default: present
        type: str
    primary:
        description:
            - Specifies the primary dump device
        type: path
    secondary:
        description:
            - Specifies the secondary dump device
        type: path
    permanent:
        description:
            - Makes updates to the O(primary) or O(secondary) dump device setting permanent
        default: False
        type: bool
    copy_directory:
        description:
            - Specifies the directory to where the dump is copied to at system boot
        type: path
    forced_copy_flag:
        description:
            - If set to V(true) specifies to copy the system dump to an external media if the copy fails at boot time.
            - If set to V(false) specifies to ignore the system dump if the copy fails at boot time.
            - Requires the O(copy_directory) option to be specified
        type: bool
    always_allow_dump:
        description:
            - If V(true) and machine has a key mode switch, the reset button or the dump key sequences will force a dump with the key in the normal position.
            - If V(false) and machine has a key mode switch, it is required to be in the service position before a dump can be forced.
        type: bool
    dump_type:
        description:
             - Specifies whether a V(traditional) or V(fw-assisted) system dump is performed
             - V(fw-assisted) will required a reboot to become active
        choices: ['traditional', 'fw-assisted']
        type: str
    dump_mode:
        description:
            - Specifies the dump mode. fw-assisted dump type must be active before this setting can be modified.
            - If the system was configured with traditional dump type it first must been rebooted in order to modify the dump_mode.
            - C(disallow) specifies that neither the full memory system dump mode nor the kernel memory system dump mode is allowed.
            - C(allow_full) specifies that the full memory system dump mode is allowed.
            - C(require_full) specifies that the full memory system dump mode is allowed and is always performed.
            - Requires the O(dump_type=fw-assisted) option to be specified
        choices: ['disallow', 'allow', 'allow_kernel', 'require_kernel', 'allow_full', 'require_full']
        type: str
    nx_gzip:
        description:
            - If set to V(true) enables the Nest Accelerators (NX) GZIP accelerated dump compression
            - If set to V(false) disables the Nest Accelerators (NX) GZIP dump compression
        type: bool

notes:
    - You can refer to the IBM documentation for additional information on the commands used at
      U(https://www.ibm.com/docs/en/aix/7.3?topic=s-sysdumpdev-command)
      U(https://www.ibm.com/docs/en/aix/7.2?topic=s-sysdumpdev-command)

'''

EXAMPLES = r'''
- name: Configure primary and secondary dump devices permanently
  ibm.power_aix.sysdumpdev:
      primary: /dev/sysdump0
      secondary: /dev/sysdump1
      permanent: True

- name: Configure system dump copy directory and set the forced copy flag to False
  ibm.power_aix.sysdumpdev:
       copy_directory: /var/adm/ras
       forced_copy_flag: True

- name: Retrieve the current dump configuration
  ibm.power_aix.sysdumpdev:
      state: fact

- name: Configure fw-assisted dump with full memory system dump mode
  ibm.power_aix.sysdumpdev:
       dump_type: fw-assisted
       dump_mode: require_full

'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
command:
    description: The sysdumpdev command which was executed to update the dump configuration
    type: str
    returned: always
    sample: 'sysdumpdev -D /var/adm/ras'
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: always
    type: str
stderr:
    description: The standard error.
    returned: always
    type: str
msg:
    description: The message if the module is exited with a failure or if no actions were required
    returned: when failed or no action required
    type: str
'''

from ansible.module_utils.basic import AnsibleModule


def get_dump_config(module):
    """
    Determines the current dump settings
    param module:
        Ansible module argument spec.
    return:
        dump_config (dict) - Parsed sysdumpdev -l output.
    """
    sysdumpdev_command = module.get_bin_path('sysdumpdev', required=True)
    cmd = [sysdumpdev_command, '-l']
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run sysdumpdev command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    dump_config = {}
    for line in stdout.splitlines():
        if line.startswith('primary'):
            dump_config['primary'] = line.split()[1]
        if line.startswith('secondary'):
            dump_config['secondary'] = line.split()[1]
        if line.startswith('copy directory'):
            dump_config['copy_directory'] = line.split()[2]
        if line.startswith('forced copy flag'):
            dump_config['forced_copy_flag'] = line.split()[3]
        if line.startswith('always allow dump'):
            dump_config['always_allow_dump'] = line.split()[3]
        if line.startswith('dump compression'):
            dump_config['dump_compression'] = line.split()[2]
        if line.startswith('type of dump'):
            dump_config['dump_type'] = line.split()[3]
        if line.startswith('full memory dump'):
            dump_config['dump_mode'] = line.split()[3]
        if line.startswith('enable NX GZIP'):
            dump_config['nx_gzip'] = line.split()[3]

    for key, value in dump_config.items():
        if isinstance(value, str) and value == 'TRUE':
            dump_config[key] = True
        if isinstance(value, str) and value == 'FALSE':
            dump_config[key] = False
        if isinstance(value, str) and value == 'ON':
            dump_config[key] = True
        if isinstance(value, str) and value == 'OFF':
            dump_config[key] = False

    return dict(dump_config)


def set_dump_config(module, cmd_args):
    """
    Set dump settings using sysdumpdev command
    param module:
        Ansible module argument spec.
    param cmd_args:
        Arguments for the sysdumpdev command.
    return:
        return_dict (dict) - Dict containing sysdumpdev command results.
    """
    sysdumpdev_command = module.get_bin_path('sysdumpdev', required=True)
    cmd = [sysdumpdev_command] + cmd_args
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run sysdumpdev command: ' + ' '.join(cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    return_dict = {
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }

    return dict(return_dict)


def update_dump_config(module, current_config):
    """
    Determine what dump settings need to be changed, create argument string for the sysdumpdev command and perform the update
    param module:
        Ansible module argument spec.
    param current_config:
        Current dump configuration.
    return:
        return_dict (dict) - Dict containing sysdumpdev command results and change flag.
    """
    return_dict = {
        'changed': False,
        'cmd': '',
        'rc': '',
        'stdout': '',
        'stderr': '',
    }

    cmd_args = []

    dump_device_changed = False
    if module.params['primary'] is not None and (module.params['primary'] != current_config['primary']):
        cmd_args.append('-p')
        cmd_args.append(module.params['primary'])
        dump_device_changed = True
        return_dict['changed'] = True

    if module.params['secondary'] is not None and (module.params['secondary'] != current_config['secondary']):
        cmd_args.append('-s')
        cmd_args.append(module.params['secondary'])
        dump_device_changed = True
        return_dict['changed'] = True

    if module.params['permanent'] and dump_device_changed:
        cmd_args.append('-P')

    target_copy_directory = current_config['copy_directory']
    target_forced_copy_flag = current_config['forced_copy_flag']
    copy_directory_change = False
    forced_copy_flag_change = False

    if module.params['copy_directory'] is not None and (module.params['copy_directory'] != current_config['copy_directory']):
        copy_directory_change = True
        target_copy_directory = module.params['copy_directory']

    if module.params['forced_copy_flag'] is not None and (module.params['forced_copy_flag'] != current_config['forced_copy_flag']):
        forced_copy_flag_change = True
        target_forced_copy_flag = module.params['forced_copy_flag']

    if copy_directory_change or forced_copy_flag_change:
        if target_forced_copy_flag is True:
            cmd_args.append('-D')
        else:
            cmd_args.append('-d')
        return_dict['changed'] = True
        cmd_args.append(target_copy_directory)

    if module.params['always_allow_dump'] is not None and (module.params['always_allow_dump'] != current_config['always_allow_dump']):
        if module.params['always_allow_dump']:
            cmd_args.append('-K')
        else:
            cmd_args.append('-k')
        return_dict['changed'] = True

    if module.params['nx_gzip'] is not None:
        # nx_gzip is not necessarily enabled so we check if the nx_gzip attribute is really defined
        if 'nx_gzip' in current_config.keys():
            if module.params['nx_gzip'] != current_config['nx_gzip']:
                if module.params['nx_gzip'] is True:
                    cmd_args.append('-N')
                else:
                    cmd_args.append('-n')
                return_dict['changed'] = True
        else:
            module.fail_json(msg='nx_gzip option not available on target system', **return_dict)

    if module.params['dump_type'] is not None and (module.params['dump_type'] != current_config['dump_type']):
        cmd_args.append('-t')
        cmd_args.append(module.params['dump_type'])
        return_dict['changed'] = True

    if module.params['dump_mode'] is not None:
        if current_config['dump_type'] != 'fw-assisted':
            module.fail_json(msg='dump_type must be fw-assisted before you configure dump_mode', **return_dict)
        elif (current_config['dump_type'] == 'fw-assisted') and (module.params['dump_mode'] != current_config['dump_mode']):
            cmd_args.append('-f')
            cmd_args.append(module.params['dump_mode'])
            return_dict['changed'] = True

    if return_dict['changed']:
        if module.check_mode:
            return_dict['cmd'] = 'sysdumpdev ' + ' '.join(cmd_args)
        else:
            set_dump_result = set_dump_config(module, cmd_args)
            return_dict['cmd'] = set_dump_result['cmd']
            return_dict['rc'] = set_dump_result['rc']
            return_dict['stdout'] = set_dump_result['stdout']
            return_dict['stderr'] = set_dump_result['stderr']
    else:
        return_dict['rc'] = 0
        return_dict['msg'] = 'No modification is required'
    return dict(return_dict)


def run_module():
    """
    Main module function. Exits with module.exit_json.
    """
    module_args = dict(
        state=dict(type='str', required=False, choices=['present', 'fact'], default='present'),
        primary=dict(type='path', required=False),
        secondary=dict(type='path', required=False),
        permanent=dict(type='bool', required=False, default=False),
        copy_directory=dict(type='path', required=False),
        forced_copy_flag=dict(type='bool', required=False),
        always_allow_dump=dict(type='bool', required=False),
        nx_gzip=dict(type='bool', required=False),
        dump_type=dict(type='str', required=False, choices=['traditional', 'fw-assisted']),
        dump_mode=dict(type='str', required=False, choices=['disallow', 'allow', 'allow_kernel', 'require_kernel', 'allow_full', 'require_full'])
    )

    result = dict(
        changed=False,
        cmd='',
        stdout='',
        stderr=''
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True,
        required_if=[
            ('permanent', True, ['primary', 'secondary'], True)
        ],
        required_together=[
            ['forced_copy_flag', 'copy_directory']
        ]
    )

    # Check if the 'dump_type' is 'fw-assisted' when 'dump_mode' is specified.
    if module.params.get('dump_mode') and module.params.get('dump_type') != 'fw-assisted':
        module.fail_json(msg="If 'dump_mode' is specified, 'dump_type' must be 'fw-assisted'.")

    current_config = get_dump_config(module)

    if module.params['state'] == 'fact':
        result['sysdumpdev_config'] = current_config
    else:
        result = update_dump_config(module, current_config)

    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
