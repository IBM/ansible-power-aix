#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- Aiman Shaharuddin (@syahrul-aiman)
module: getconf
short_description: Reports system configuration variable values as facts.

description:
- List system configuration variable values.
- Will not list PathConfiguration or DeviceVariable by default
- U(https://www.ibm.com/docs/en/aix/7.3?topic=g-getconf-command)
version_added: '1.7.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
options:
  variable:
    description:
    - Specifies a system configuration variable (SystemwideConfiguration),
      a system path configuration variable (PathConfiguration),
      or a device variable (DeviceVariable)
    type: str
    default: ''
  path:
    description:
    - Specifies a path name for the PathConfiguration parameter (PathName),
      or a path name of a device (DeviceName)
    type: str
    default: ''

'''

EXAMPLES = r'''
- name: List all system configuration variable values.
  getconf:
- name: Get hdisk0 size
  getconf:
    variable: DISK_SIZE
    path: /dev/hdisk0
- name: Get ARG_MAX value
  getconf:
    variable: ARG_MAX
'''

RETURN = r'''
ansible_facts:
  description:
  - Facts to add to ansible_facts about the system configuration variable values.
  returned: always
  type: complex
  contains:
    conf:
      description:
      - Contains a list of system configuration variable key-values.
      returned: success
      type: dict
      elements: dict
'''


from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


result = None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            variable=dict(type='str', default=''),
            path=dict(type='str', default=''),
        ),
        supports_check_mode=True,
    )

    global result

    result = dict(
        changed=False,
        msg='',
        cmd='',
        stdout='',
        stderr='',
    )

    variable = module.params['variable']
    path = module.params['path']

    if not variable and path:
        result['msg'] = 'variable must not be empty if path is specified'
        module.fail_json(**result)

    cmd = ['getconf']
    if variable:
        cmd += [variable]
    if variable and path:
        cmd += [path]
    if not variable and not path:
        cmd += ['-a']

    rc, stdout, stderr = module.run_command(cmd)

    result['cmd'] = ' '.join(cmd)
    result['rc'] = rc
    result['stdout'] = stdout
    result['stderr'] = stderr

    if rc != 0:
        result['msg'] = 'getconf failed.'
        module.fail_json(**result)

    conf = {}
    if variable and path:
        conf[variable] = {}
        conf[variable][path] = stdout.strip()
        result['value'] = conf[variable][path]
    elif variable:
        conf[variable] = stdout.strip()
        result['value'] = conf[variable]
    else:
        for line in stdout.splitlines():
            if line.find(":") > -1:
                key_value = line.split(':', 1)
                key = key_value[0].strip()
                value = key_value[1].strip()
                conf[key] = value
            else:
                key = line.strip()
                if conf[key] is None:
                    conf[key] = ""

    result['msg'] = 'getconf successful.'
    module.exit_json(ansible_facts=dict(conf=conf), **result)


if __name__ == '__main__':
    main()
