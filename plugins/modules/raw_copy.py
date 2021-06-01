#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2021- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: raw_copy
short_description: Copy a file to a target without Python installed.
description:
- Uses Ansible internal hooks to copy a file to the remote host without requiring that Python be installed on the target. Useful during the bootstrapping of Python.
- Because it uses Ansible's internals, it honors Ansible configuration and host variables like C(ansible_password) and C(ansible_host).
- Always use ansible.builtin.copy instead of this plugin!
version_added: '2.9'
requirements:
- Python >= 2.7
options:
  src:
    description:
    - The name of the file to copy.
    - If no absolute or relative path is specified, the plugin looks in C(files).
    type: str
    required: true
  dest:
    description:
    - The absolute path, including the file name, on the remote system into which to copy the file.
    type: str
    required: true
'''

EXAMPLES = r'''
- name: Transfer install images
  ibm.power_aix.raw_copy:
    src: "{{ download_dir }}/{{ yum_src }}"
    dest: "{{ target_dir }}/{{ yum_src }}"
'''

RETURN = r'''
'''
