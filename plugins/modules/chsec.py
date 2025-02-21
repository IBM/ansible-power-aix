#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2018, Christian Tremel (@flynn1973)
# Additional changes 2021, David Little (@d-little)
# Additional changes 2022, Stephen Ulmer (@stephenulmer)
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

# AIX 7.3: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_73/c_commands/chsec.html
# AIX 7.2: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/c_commands/chsec.html
# AIX 7.1: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_71/c_commands/chsec.html
# AIX 6.1 PDF: https://public.dhe.ibm.com/systems/power/docs/aix/61/aixcmds1_pdf.pdf

from __future__ import absolute_import, division, print_function

DOCUMENTATION = r'''
---
module: chsec
short_description: Modify AIX stanza files
version_added: 1.4.0
description:
  - Modify stanza attributes to AIX config files using the C(chsec) command.
author:
  - Christian Tremel (@flynn1973)
  - David Little (@d-little)
  - Stephen Ulmer (@stephenulmer)
requirements:
  - AIX
  - Python >= 3.6
  - 'Privileged user with authorizations'
options:
  file:
    description:
      - File path to the stanza file.
    type: path
    required: true
    aliases: [ path, dest ]
  stanza:
    description:
      - Name of stanza to modify attributes of
    type: str
    required: true
  attrs:
    description:
      - A dict of key/value pairs to be changed
      - If the value is true/false, ensure to quote it to avoid bool interpretation.
    type: raw
    required: true
    aliases: [ options ]
  state:
    description:
      - If set to C(present) all given attrs values will be set.
      - If set to C(absent) all attrs provided will be un-set, regardless of value provided.
        - NB, this does not remove the entire stanza, only the provided attrs will be removed.
        - To remove a single attribute from the stanza set to C(present) and set key to an empty value (key=).
      - All rules/allowed file-stanza combos/allowed files for the AIX C(chsec) command apply here.
    type: str
    choices: [ absent, present ]
    default: present
seealso:
  - name: The chsec manual page from the IBM Knowledge Center
    description: Changes the attributes in the security stanza files.
    link: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/c_commands/chsec.html
  - name: The lssec manual page from the IBM Knowledge Center
    description: Lists attributes in the security stanza files.
    link: https://www.ibm.com/support/knowledgecenter/en/ssw_aix_72/l_commands/lssec.html
'''

EXAMPLES = r'''
- name: Add an LDAP user stanza
  chsec:
    file: /etc/security/user
    stanza: ldapuser
    attrs:
      SYSTEM: LDAP
      registry: LDAP
    state: present
- name: Change login times for user
  chsec:
    file: /etc/security/user
    stanza: ldapuser
    attrs:
      logintimes: :0800-1700
    state: present
- name: Remove registry attribute from stanza
  chsec:
    file: /etc/security/user
    stanza: ldapuser
    attrs:
      SYSTEM: LDAP
      registry: null
    state: present
- name: Lock System User Accounts
  chsec:
    path: /etc/security/user
    stanza: "{{ item }}"
    attrs:
      account_locked: "true"
      login: "false"
      rlogin: "false"
    state: present
  loop:
    - "adm"
    - "guest"
    - "invscout"
    - "ipsec"
    - "snapp"
    - "srvproxy"
    - "uucp"
'''

RETURN = r'''
changed:
  description: Was this value changed
  returned: always
  type: bool
  sample: False
msg:
  description: The execution message.
  returned: always
  type: str
  sample: 'Invalid parameter: install_list cannot be empty'
file:
  description: The file being modified
  returned: always
  type: str
stanza:
  description: The stanza in file being modified
  returned: always
  type: str
attrs:
  description: For each attribute provided in the 'attrs' section, an entry (below) is returned
  type: dict
  returned: always
  contains:
    cmd:
      description: Command that is run to update attr
      returned: Only if attr requires change
      type: str
    stdout:
      description: The standard output of the command.
      returned: only when cmd is run
      type: str
    stderr:
      description: The standard error of the command.
      returned: only when cmd is run
      type: str
    rc:
      description: The command return code.
      returned: only when cmd is run
      type: int
'''


from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


def set_attr_value(module, filename, stanza, attr, target_value):
    # -> dict:
    """ Sets the selected file->stanza->attr=target_value.
    If command fails, exits using module.fail_json.
    Returns a dict of:
        cmd: string of command run
        rc: int of return code
        stdout: stdout
        stderr: stderr
    """
    chsec_command = module.get_bin_path('chsec', required=True)
    if str(target_value) in ["True", "False"]:
        if str(target_value) == "True":
            target_value = "true"
        else:
            target_value = "false"
    cmd = [
        chsec_command,
        '-f', filename,
        '-s', stanza,
        '-a', '='.join(map(str, [attr, target_value]))
    ]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run chsec command: ' + ' '.join(cmd)
        if "3004-692" in stderr:
            msg += f"Invalid value provided - {target_value}"
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    return_dict = {
        'cmd': ' '.join(cmd),
        'rc': rc,
        'stdout': stdout,
        'stderr': stderr,
    }
    return return_dict


def get_current_attr_value(module, filename, stanza, attr):
    """ Given single filename+stanza+attr, returns str(attr_value) """
    lssec_command = module.get_bin_path('lssec', required=True)
    cmd = [lssec_command, '-c', '-f', filename, '-s', stanza, '-a', attr]
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = 'Failed to run lssec command: ' + ' '.join(cmd)
        if "3004-725" in stderr:
            msg += f" Invalid stanza: '{stanza}'"
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)
    # Strip newline and double-quotation marks that are sometimes added
    lssec_out = stdout.splitlines()[1].split(':', 1)[1].strip('\\\"\n')
    return str(lssec_out)


def run_chsec(module):
    # -> (bool, dict):
    """ Returns (bool(changed), dict(msg)) """
    filename = module.params["file"]
    stanza = module.params["stanza"]
    attrs = module.params["attrs"]
    state = module.params["state"]

    results = {
        'changed': False,
        'file': filename,
        'stanza': stanza,
        'attrs': {},
    }

    changed_attrs = 0
    for attr, target_value in attrs.items():
        if state == 'absent':
            # 'absent' sets all of the given attrs to None, regardless of given value
            target_value = ''
        else:
            # target_value needs to be a string for comparisons later
            # We cant allot bools/ints to be interpreted as anything other than strings
            target_value = str(target_value)
        current_value = get_current_attr_value(module, filename, stanza, attr)

        # Start our msg dict for this particular key+value
        msg_attr = {
            'status': 'unchanged',
            'desired_value': target_value,
            'existing_value': current_value,
        }
        if current_value != target_value:
            if module.check_mode:
                msg_attr["check_mode"] = True
            else:
                cmd_return = set_attr_value(module, filename, stanza, attr, target_value)
                msg_attr.update(cmd_return)
            results['changed'] = True
            msg_attr['status'] = 'changed'
            changed_attrs += 1
        results['attrs'][attr] = msg_attr
    return results


def main():
    module = AnsibleModule(
        argument_spec=dict(
            file=dict(type='path', required=True, aliases=['dest', 'path']),
            stanza=dict(type='str', required=True),
            attrs=dict(type='raw', required=True, aliases=['options']),
            state=dict(type='str', default='present', choices=['absent', 'present']),
        ),
        supports_check_mode=True,
    )

    results = run_chsec(module)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
