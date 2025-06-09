# -*- coding: utf-8 -*-
# Copyright (c) 2025 eNFence GmbH
# GNU General Public License v3.0+ (see LICENSES/GPL-3.0-or-later.txt or https://www.gnu.org/licenses/gpl-3.0.txt)
# SPDX-License-Identifier: GPL-3.0-or-later

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = '''
module: password_hash
short_description: Encrypt password with AIX encryption methods
description:
  - Encrypt the provided password with the specified AIX encryption algorithm and provided salt.
  - If salt is not provided, a random salt is generated.
  - If algorithm is not provided, the default password encryption algorithm is used, as it set on AIX.
options:
  password:
    description: A password to encrypt.
    type: str
    required: true
  algorithm:
    description:
      - Password encryption algorithm from /etc/security/pwdalg.cfg.
      - If not specified, the filter tries to find the default encryption algorithm.
      - If it fails, crypt is used.
    type: str
    choices: [ smd5, ssha1, ssha256, ssha512, sblowfish, crypt ]
    required: false
  salt:
    description:
      - A string used to encrypt the password.
      - If no salt is provided, a new random salt is generated.
    required: false
    type: str

author:
  - Andrey Klyachkin (@aklyachkin)
'''

EXAMPLES = r'''
- name: Encrypt password with default encryption algorithm and random salt
  ibm.power_aix.password_hash:
    password: mypassword

- name: Encrypt password with ssha512
  ibm.power_aix.password_hash:
    password: mypassword
    algorithm: ssha512
'''

RETURN = r'''
  _value:
    description: The encrypted password
    returned: always
    type: str
'''

from ansible.module_utils.basic import AnsibleModule

import ctypes
import platform
import random
import string


def aix_crypt(password, salt):
    libc = "/usr/lib/libc.a(shr_64.o)"
    libc_fn = ctypes.CDLL(libc)
    libc_fn.crypt.argtypes = (ctypes.c_char_p, ctypes.c_char_p)
    libc_fn.crypt.restype = ctypes.c_char_p
    hash = libc_fn.crypt(password.encode('UTF-8'), salt.encode('UTF-8'))
    return hash.decode('UTF-8')


def aix_getstdalgo(module):
    rc, stdout, stderr = module.run_command("lssec -cf /etc/security/login.cfg -s usw -a pwd_algorithm")
    if rc != 0:
        return ''
    try:
        algo = stdout.splitlines()[1].split(':')[1]
    except Exception:
        return ''
    return algo


def aix_algorithm(algorithm):
    if algorithm == '':
        return ''
    if algorithm.startswith('ssha'):
        # standard cost for SHA algorithms is 06
        return f"{{{algorithm}}}06"
    if algorithm.startswith('sblowfish'):
        # standard cost for blowfish is 08
        return f"{{{algorithm}}}08"
    return f"{{{algorithm}}}"


def aix_password(module):
    if module.params['algorithm'] is None:
        algorithm = aix_getstdalgo(module)
    else:
        algorithm = module.params['algorithm']
    algorithm = aix_algorithm(algorithm)
    if module.params['salt'] is None:
        salt = ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.ascii_lowercase + string.digits) for i in range(16))
    else:
        salt = module.params['salt']
    mysalt = f"{algorithm}${salt}$"
    return aix_crypt(module.params['password'], mysalt)


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            password=dict(type='str', required=True, no_log=True),
            algorithm=dict(type='str', choices=['crypt', 'smd5', 'sblowfish', 'ssha1', 'ssha256', 'ssha512'], required=False),
            salt=dict(type='str', required=False)
        ),
        supports_check_mode=False
    )

    if platform.system() != 'AIX':
        module.fail_json(
            rc=1,
            msg=f"Invalid operating system ({platform.system()}). The module can be used only on AIX"
        )
    result = dict(
        changed=False,
        hash=aix_password(module),
        rc=0
    )
    module.exit_json(**result)


def main():
    run_module()


if __name__ == '__main__':
    main()
