#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: mpio
short_description: Returns information about MultiPath I/O capable devices.
description:
- Returns information about MultiPath I/O capable devices.
version_added: '1.1.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
options:
  device:
    description:
    - Specifies the logical device name of the target device whose
      path information is to be returned.
    type: str
  parent:
    description:
    - Indicates the logical device name of the parent device whose
      paths are to be returned.
    type: str
'''

EXAMPLES = r'''
- name: Gather paths to all MultiPath I/O capable devices
  mpio:
  register: mpio_info
- name: Print the paths
  debug:
    var: mpio_info.mpio_facts.paths
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: "Successfully retrieved mpio facts. Check mpio_facts for more details."
cmd:
    description: The command executed.
    returned: always
    type: str
    sample: /usr/bin/manage_disk_drivers -l
rc:
    description: The command return code.
    returned: always
    type: int
stdout:
    description: The standard output of the command.
    returned: always
    type: str
stderr:
    description: The standard error of the command.
    returned: In case of error
    type: str
    sample: 'lspath: 0514-546 Invalid parameter - ansibleNegativeTest.'
mpio_facts:
  description:
  - Facts about paths to MultiPath I/O capable devices.
  returned: always
  type: complex
  contains:
    mpio:
      description:
      - Contains information about drivers and paths.
      type: dict
      elements: dict
      contains:
        drivers:
          description:
          - Maps driver name to driver supported and selected options.
          returned: always
          type: dict
          elements: dict
          contains:
            option:
              description:
              - Option currently selected.
              returned: always
              type: str
            options:
              description:
              - Supported driver options.
              returned: always
              type: list
              elements: str
          sample:
            "drivers": {
                "IBMFlash": {
                    "option": "NO_OVERRIDE",
                    "options": [
                        "NO_OVERRIDE",
                        "AIX_AAPCM",
                        "AIX_non_MPIO"
                    ]
                }
            }
        paths:
          description:
          - Maps device name to parent devices and connections.
          returned: always
          type: dict
          elements: dict
          sample:
            "paths": {
                "hdisk0": {
                    "fscsi1": {
                        "500507680b215660,0": {
                            "path_id": 0,
                            "path_status": "Available",
                            "status": "Enabled"
                        },
                        "500507680b215661,0": {
                            "path_id": 1,
                            "path_status": "Available",
                            "status": "Enabled"
                        }
                    }
                }
            }
'''

results = None


def gather_facts(module):
    paths = {}
    drivers = {}

    lspath_path = module.get_bin_path('lspath', required=True)
    cmd = [lspath_path, '-F', 'name:parent:connection:path_id:path_status:status']
    if module.params['device']:
        cmd += ['-l', module.params['device']]
    if module.params['parent']:
        cmd += ['-p', module.params['parent']]

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['cmd'] = ' '.join(cmd)

    if rc:
        results['stderr'] = stderr
        results['rc'] = 1
        results['msg'] = f"The following command failed: {' '.join(cmd)}."
        if "0514-546" in stderr:
            results['msg'] += " Invalid device provided."
        module.fail_json(**results)

    for line in stdout.splitlines():
        fields = line.split(':')
        if len(fields) != 6:
            continue
        name = fields[0]
        if name not in paths:
            paths[name] = {}
        parent = fields[1]
        if parent not in paths[name]:
            paths[name][parent] = {}
        connection = fields[2]
        if connection not in paths[name][parent]:
            paths[name][parent][connection] = dict(path_id=int(fields[3]),
                                                   path_status=fields[4])
            if fields[5] != 'N/A':
                paths[name][parent][connection]['status'] = fields[5]

    manage_disk_drivers_path = module.get_bin_path('manage_disk_drivers')
    if not manage_disk_drivers_path:
        return dict(paths=paths, drivers=drivers)

    cmd = [manage_disk_drivers_path, '-l']

    rc, stdout, stderr = module.run_command(cmd)
    results['stdout'] = stdout
    results['cmd'] = ' '.join(cmd)

    if rc:
        results['stderr'] = stderr
        results['rc'] = 1
        results['msg'] = f"The following command failed: {' '.join(cmd)}"
        module.fail_json(**results)

    for line in stdout.splitlines():
        fields = line.split()
        if len(fields) != 3:
            continue
        if fields[0] == 'Device':
            continue
        driver = dict(option=fields[1])
        options = fields[2].split(',')
        driver['options'] = options
        drivers[fields[0]] = driver

    return dict(paths=paths, drivers=drivers)


def main():
    global results
    module = AnsibleModule(
        argument_spec=dict(
            device=dict(type='str'),
            parent=dict(type='str')
        )
    )

    results = dict(
        changed=False,
        rc=0,
        msg='',
        cmd='',
        stdout='',
        stderr='',
        mpio_facts={},
    )

    results['mpio_facts'] = gather_facts(module)
    results['msg'] = "Successfully retrieved mpio facts. Check mpio_facts for more details."
    results['ansible_facts'] = results['mpio_facts']
    module.exit_json(**results)


if __name__ == '__main__':
    main()
