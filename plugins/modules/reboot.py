#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: reboot
short_description: Reboot AIX machines.
description:
- Reboot a machine and validate by runnning a test command once the system comes back up.
version_added: '2.9'
requirements:
- Python >= 2.7
- 'Privileged user with authorization: B(aix.system.boot.shutdown)'
- In ansible.cfg file, ensure that ssh_args are properly set, so that ssh connection does not end up in a hang.
  For example, ssh_args = -o ForwardAgent=yes -o ControlPersist=30m -o ServerAliveInterval=45 -o ServerAliveCountMax=10
options:
  pre_reboot_delay:
    description:
      - Seconds to wait before reboot. Passed as a parameter to the reboot command.
    type: int
    default: 0
  post_reboot_delay:
    description:
      - Seconds to wait for validation after reboot command was successful
    type: int
    default: 0
  reboot_timeout:
    description:
      - Maximum seconds to wait for machine to reboot and respond to a test command.
    type: int
    default: 300
  test_command:
    description:
      - Command to run on the rebooted host to validate system running status.
    type: str
    default: whoami
'''

EXAMPLES = r'''
- name: "Reboot a machine"
  reboot:
    pre_reboot_delay: 20
    post_reboot_delay: 20
    connect_timeout: 10
    reboot_timeout: 300
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'System has been rebooted SUCCESSFULLY'
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
