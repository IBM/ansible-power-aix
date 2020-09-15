#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
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
module: mkfilt
short_description: Activates or deactivates the filter rules
description:
- Activates or deactivates the filter rules.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
options:
  action:
    description:
    - Specifies the action to perform.
    - C(add) to add filter rules.
    - C(check) to check the syntax of filter rules.
    - C(move) to move a filter rule.
    - C(change) to change a filter rule.
    - C(import) to import filter rules from an export file.
    - C(export) to export filter rules to an export file.
    type: str
    choices: [ add, check, move, change, import, export ]
    default: add
  directory:
    description:
    - When I(action=import) or I(action=export), specifies the directory where
      the text files are to be read.
    - When I(action=export), directory will be created if it does not exist.
    type: str
  ipv4:
    description:
    - Specifies the IPv4 filter module state and rules.
    type: dict
    suboptions: &ipcommon
      default:
        description:
        - Sets the action of the default filter rule.
        type: str
        choices: [ permit, deny ]
      log:
        description:
        - Enable the log functionality of the filter rule module.
        type: bool
        default: no
      force:
        description:
        - Force removal of auto-generated filter rules.
        type: bool
        default: no
      rules:
        description:
        - Specifies the list of filter rules.
        type: list
        elements: dict
        suboptions:
          action:
            description:
            - Specifies the action to perform.
            type: str
            choices: [ permit, deny, shun_host, shun_port, if, else, endif, remove ]
          id:
            description:
            - Specifies the filter rule ID.
            - C(all) specifies to remove all user-defined filter rules.
            type: str
          direction:
            description:
            - Specifies to what packets the rule applies.
            type: str
            choices: [ inbound, outbound, both ]
            default: both
          s_addr:
            description:
            - Specifies the source address. It can be an IP address or a host name.
            - If a host name is specified, the first IP address returned by the name server
              for that host will be used.
            type: str
          s_mask:
            description:
            - Specifies the source subnet mask.
            type: str
          s_opr:
            description:
            - Specifies the operation that will be used in the comparison between the source port
              of the packet and the source port I(s_port) specified in this filter rule.
            type: str
            choices: [ lt, le, gt, ge, eq, neq ]
          s_port:
            description:
            - Specifies the source port.
            type: str
          d_addr:
            description:
            - Specifies the destination address. It can be an IP address or a host name.
            - If a host name is specified, the first IP address returned by the name server
              for that host will be used.
            type: str
          d_mask:
            description:
            - Specifies the destination subnet mask.
            type: str
          d_opr:
            description:
            - Specifies the operation that will be used in the comparison between the destination port
              of the packet and the destination port I(d_port) specified in this filter rule.
            type: str
            choices: [ lt, le, gt, ge, eq, neq ]
          d_port:
            description:
            - Specifies the destination port.
            type: str
          icmp_type_opr:
            description:
            - Specifies the operation that will be used in the comparison between the ICMP type
              of the packet and the ICMP type I(icmp_type) specified in this filter rule.
            type: str
            choices: [ lt, le, gt, ge, eq, neq ]
          icmp_type:
            description:
            - Specifies the ICMP type.
            type: str
          icmp_code_opr:
            description:
            - Specifies the operation that will be used in the comparison between the ICMP code
              of the packet and the ICMP code I(icmp_code) specified in this filter rule.
            type: str
            choices: [ lt, le, gt, ge, eq, neq ]
          icmp_code:
            description:
            - Specifies the ICMP code.
            type: str
          tunnel:
            description:
            - Specifies the ID of the tunnel related to this filter rule.
            - All the packets that match this filter rule must go through the specified tunnel.
            - If this attribute is not specified, this rule will only apply to non-tunnel traffic.
            type: str
          log:
            description:
            - Specifies the log control. Packets that match this filter rule will be
              included in the filter log.
            type: bool
            default: no
          interface:
            description:
            - Specifies the name of the IP interface to which the filter rule applies.
            type: str
          fragment:
            description:
            - Specifies the fragmentation control.
            type: str
          timeout:
            description:
            - Specifies the expiration time. The expiration time is the amount
              of time the rule should remain active in seconds.
            type: str
          description:
            description:
            - A short description text for the filter rule.
            type: str
          protocol:
            description:
            - Specifies the protocol to which the filter rule applies.
            - The valid values are C(udp), C(icmp), C(icmpv6), C(tcp), C(tcp/ack), C(ospf), C(ipip), C(esp), C(ah), and C(all).
            - The protocol can also be specified numerically (between 1 and 252).
            type: str
          source_routing:
            description:
            - Specifies that this filter rule can apply to IP packets that use source routing.
            type: bool
            default: no
          routing:
            description:
            - Specifies whether the rule will apply to forwarded packets, packets
              destined or originated from the local host, or both.
            type: str
            choices: [ forwarded, local, both ]
          antivirus:
            description:
            - Specifies the antivirus file name.
            - Understands some versions of ClamAV Virus Database.
            type: str
  ipv6:
    description:
    - Specifies the IPv6 filter module state and rules.
    type: dict
    suboptions: *ipcommon
'''

EXAMPLES = r'''
- name: Allow SSH activity through interface en0
  mkfilt:
    ipv4:
      log: yes
      default: deny
      rules:
      - action: permit
        direction: inbound
        d_opr: eq
        d_port: 22
        interface: en0
        description: permit SSH requests from any clients
      - action: permit
        direction: outbound
        s_opr: eq
        s_port: 22
        interface: en0
        description: permit SSH answers to any clients

- name: Remove all user-defined and auto-generated filter rules
  mkfilt:
    ipv4:
      force: yes
      rules:
      - action: remove
        id: all
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'mkfilt completed successfully'
stdout:
    description: The standard output
    returned: always
    type: str
stderr:
    description: The standard error
    returned: always
    type: str
filter:
    description: The current filter settings
    returned: always
    type: dict
'''

from ansible.module_utils.basic import AnsibleModule


def list_rules(module, version):
    """
    Sample lsfilt output:

    1|permit|0.0.0.0|0.0.0.0|0.0.0.0|0.0.0.0|no|udp|eq|4001|eq|4001|both|both|no|all packets|0|all|0|||Default Rule
    2|permit|0.0.0.0|0.0.0.0|0.0.0.0|0.0.0.0|yes|all|any|0|eq|5989|both|inbound|no|all packets|0|all|0|||allow port 5989
    3|permit|0.0.0.0|0.0.0.0|0.0.0.0|0.0.0.0|yes|all|any|0|eq|5988|both|inbound|no|all packets|0|all|0|||allow port 5988
    4|permit|0.0.0.0|0.0.0.0|0.0.0.0|0.0.0.0|yes|all|any|0|eq|5987|both|inbound|no|all packets|0|all|0|||allow port 5987
    5|permit|0.0.0.0|0.0.0.0|0.0.0.0|0.0.0.0|yes|all|eq|657|any|0|both|inbound|no|all packets|0|all|0|||allow port 657
    6|permit|0.0.0.0|0.0.0.0|0.0.0.0|0.0.0.0|yes|all|any|0|eq|657|both|inbound|no|all packets|0|all|0|||allow port 657
    """
    global results

    vopt = '-v4' if version != 'ipv6' else '-v6'

    cmd = ['lsfilt', vopt, '-O']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        return None

    rules = []
    for line in stdout.split('\n'):
        fields = line.split('|', 22)
        if len(fields) < 22:
            continue
        rule = {}
        rule['id'] = fields[0]
        rule['action'] = fields[1]

        if (version == 'ipv4' and fields[2] != '0.0.0.0') or (version == 'ipv6' and fields[2] != '::'):
            rule['s_addr'] = fields[2]
        # Mask or prefix length
        if (version == 'ipv4' and fields[3] != '0.0.0.0') or (version == 'ipv6' and fields[3] != '0'):
            rule['s_mask'] = fields[3]
        if (version == 'ipv4' and fields[4] != '0.0.0.0') or (version == 'ipv6' and fields[4] != '::'):
            rule['d_addr'] = fields[4]
        # Mask or prefix length
        if (version == 'ipv4' and fields[5] != '0.0.0.0') or (version == 'ipv6' and fields[5] != '0'):
            rule['d_mask'] = fields[5]

        if fields[6] == 'yes':
            rule['source_routing'] = True
        if fields[7] != 'all':
            rule['protocol'] = fields[7]
        if fields[7] == 'icmp':
            if fields[8] != 'any':
                rule['icmp_type_opr'] = fields[8]
                rule['icmp_type'] = fields[9]
            if fields[10] != 'any':
                rule['icmp_code_opr'] = fields[10]
                rule['icmp_code'] = fields[11]
        else:
            if fields[8] != 'any':
                rule['s_opr'] = fields[8]
                rule['s_port'] = fields[9]
            if fields[10] != 'any':
                rule['d_opr'] = fields[10]
                rule['d_port'] = fields[11]
        rule['scope'] = fields[12]
        if fields[13] != 'both':
            rule['direction'] = fields[13]
        if fields[14] == 'yes':
            rule['log'] = True
        if fields[15] != 'all packets':
            rule['fragment'] = fields[15]
        if fields[16] != '0':
            rule['tunnel'] = fields[16]
        if fields[17] != 'all':
            rule['interface'] = fields[17]
        if fields[18] != '0':
            rule['timeout'] = fields[18]
        # XXX missing fields? routing? antivirus? pattern?
        rule['description'] = fields[21]
        rules += [rule]

    return rules


def add_rules(module, params, version):
    global results

    vopt = '-v4' if version == 'ipv4' else '-v6'

    if version not in params:
        return True
    if 'rules' not in params[version]:
        return True

    # Add rules
    for rule in params[version]['rules']:
        cmd = ['genfilt', vopt]
        if rule['action'] == 'permit':
            cmd += ['-aP']
        elif rule['action'] == 'deny':
            cmd += ['-aD']
        elif rule['action'] == 'shun_host':
            cmd += ['-aH']
        elif rule['action'] == 'shun_port':
            cmd += ['-aS']
        elif rule['action'] == 'if':
            cmd += ['-aI']
        elif rule['action'] == 'else':
            cmd += ['-aL']
        elif rule['action'] == 'endif':
            cmd += ['-aE']
        elif rule['action'] == 'remove':
            if not rule['id']:
                results['msg'] = 'Could not remove rule without rule id'
                module.fail_json(**results)
            cmd = ['rmfilt', vopt, '-n', rule['id']]
            if params[version]['force']:
                cmd += ['-f']
            ret, stdout, stderr = module.run_command(cmd)
            if ret != 0:
                results['stdout'] = stdout
                results['stderr'] = stderr
                results['msg'] = 'Could not remove rule: command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
                module.fail_json(**results)
            continue

        if rule['id']:
            cmd += ['-n', rule['id']]

        if rule['direction']:
            if rule['direction'] == 'inbound':
                cmd += ['-wI']
            elif rule['direction'] == 'outbound':
                cmd += ['-wO']
            else:
                cmd += ['-wB']

        if rule['icmp_type_opr'] and not rule['s_opr']:
            cmd += ['-o', rule['icmp_type_opr']]
        if rule['icmp_type'] and not rule['s_port']:
            cmd += ['-p', rule['icmp_type']]
        if rule['icmp_code_opr'] and not rule['d_opr']:
            cmd += ['-O', rule['icmp_code_opr']]
        if rule['icmp_code'] and not rule['d_port']:
            cmd += ['-P', rule['icmp_code']]

        # genfilt -s and -m flags are mandatory
        if rule['s_addr']:
            cmd += ['-s', rule['s_addr']]
        elif version == 'ipv4':
            cmd += ['-s', '0.0.0.0']
        else:
            cmd += ['-s', '::']
        if rule['s_mask']:
            cmd += ['-m', rule['s_mask']]
        elif version == 'ipv4':
            if rule['s_addr']:
                cmd += ['-m', '255.255.255.255']
            else:
                cmd += ['-m', '0.0.0.0']
        else:
            if rule['s_addr']:
                cmd += ['-m', '128']
            else:
                cmd += ['-m', '0']
        if rule['s_opr']:
            cmd += ['-o', rule['s_opr']]
        if rule['s_port']:
            cmd += ['-p', rule['s_port']]

        if rule['d_addr']:
            cmd += ['-d', rule['d_addr']]
        if rule['d_mask']:
            cmd += ['-M', rule['d_mask']]
        elif version == 'ipv4':
            # If -M not specified, it would be set to 255.255.255.255
            if not rule['d_addr']:
                cmd += ['-M', '0.0.0.0']
        else:
            if not rule['d_addr']:
                cmd += ['-M', '0']
        if rule['d_opr']:
            cmd += ['-O', rule['d_opr']]
        if rule['d_port']:
            cmd += ['-P', rule['d_port']]

        if rule['protocol']:
            cmd += ['-c', rule['protocol']]
        if rule['description']:
            cmd += ['-D', rule['description']]
        if rule['timeout']:
            cmd += ['-e', rule['timeout']]
        if rule['fragment']:
            cmd += ['-f', rule['fragment']]
        if rule['interface']:
            cmd += ['-i', rule['interface']]
        if not rule['source_routing']:
            cmd += ['-gN']

        if rule['routing']:
            if rule['routing'] == 'forwarded':
                cmd += ['-rR']
            elif rule['routing'] == 'local':
                cmd += ['-rL']
            else:
                cmd += ['-rB']

        if rule['tunnel']:
            cmd += ['-t', rule['tunnel']]
        if rule['antivirus']:
            cmd += ['-C', rule['antivirus']]
        if rule['log']:
            cmd += ['-lY']

        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            results['stdout'] = stdout
            results['stderr'] = stderr
            results['msg'] = 'Could not add rule: command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)

    # Should we call ckfilt here?

    # Activate the rules
    cmd = ['mkfilt', vopt, '-u']
    if 'default' in params[version] and params[version]['default'] == 'deny':
        cmd += ['-zD']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Could not activate filter: command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)

    if params[version]['log']:
        cmd = ['mkfilt', vopt, '-g', 'start']
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            results['stdout'] = stdout
            results['stderr'] = stderr
            results['msg'] = 'Could not activate logging: command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)

    return True


def import_rules(module, params):
    """
    Imports filter rules from an export file.
    """
    global results

    cmd = ['impfilt', '-f', params['directory']]
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def export_rules(module, params):
    """
    Exports filter rules to an export file.
    """
    global results

    cmd = ['expfilt', '-f', params['directory']]
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def check_rules(module):
    """
    Checks the syntax of filter rules.
    """
    global results

    cmd = ['ckfilt']
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def move_rule(module, version):
    """
    Moves a filter rule.
    """
    global results

    vopt = '-v4' if version == 'ipv4' else '-v6'
    cmd = ['mvfilt', vopt]
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def change_rule(module, version):
    """
    Changes a filter rule.
    """
    global results

    vopt = '-v4' if version == 'ipv4' else '-v6'
    cmd = ['chfilt', vopt]
    ret, stdout, stderr = module.run_command(cmd)
    if ret != 0:
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
        module.fail_json(**results)


def make_devices(module):
    """
    Make sure ipsec_v4 and ipsec_v6 devices are Available.
    """
    global results

    for version in ['4', '6']:
        cmd = ['mkdev', '-l', 'ipsec', '-t', version]
        ret, stdout, stderr = module.run_command(cmd)
        if ret != 0:
            results['stdout'] = stdout
            results['stderr'] = stderr
            results['msg'] = 'Command \'{0}\' failed with return code {1}.'.format(' '.join(cmd), ret)
            module.fail_json(**results)


def main():
    global results

    operations = ['lt', 'le', 'gt', 'ge', 'eq', 'neq']

    ipcommon = dict(
        type='dict',
        options=dict(
            default=dict(type='str', choices=['permit', 'deny']),
            log=dict(type='bool'),
            force=dict(type='bool'),
            rules=dict(
                type='list', elements='dict',
                options=dict(
                    action=dict(type='str', choices=['permit', 'deny', 'shun_host', 'shun_port', 'if', 'else', 'endif', 'remove']),
                    id=dict(type='str'),
                    direction=dict(type='str', choices=['inbound', 'outbound', 'both'], default='both'),
                    s_addr=dict(type='str'),
                    s_mask=dict(type='str'),
                    s_opr=dict(type='str', choices=operations),
                    s_port=dict(type='str'),
                    d_addr=dict(type='str'),
                    d_mask=dict(type='str'),
                    d_opr=dict(type='str', choices=operations),
                    d_port=dict(type='str'),
                    icmp_type_opr=dict(type='str', choices=operations),
                    icmp_type=dict(type='str'),
                    icmp_code_opr=dict(type='str', choices=operations),
                    icmp_code=dict(type='str'),
                    tunnel=dict(type='str'),
                    log=dict(type='bool'),
                    interface=dict(type='str'),
                    fragment=dict(type='str'),
                    timeout=dict(type='str'),
                    description=dict(type='str'),
                    protocol=dict(type='str'),
                    source_routing=dict(type='bool'),
                    routing=dict(type='str', choices=['forwarded', 'local', 'both']),
                    antivirus=dict(type='str'),
                )
            )
        )
    )

    module = AnsibleModule(
        argument_spec=dict(
            action=dict(type='str', choices=['add', 'check', 'move', 'change', 'import', 'export'], default='add'),
            directory=dict(type='str'),
            ipv4=ipcommon,
            ipv6=ipcommon
        ),
        required_if=[
            ['action', 'import', ['directory']],
            ['action', 'export', ['directory']],
        ]
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    make_devices(module)

    add_rules(module, module.params, 'ipv4')
    # add_rules(module, module.params, 'ipv6')

    results['filter'] = {}
    rules = list_rules(module, 'ipv4')
    results['filter']['ipv4'] = rules
    rules = list_rules(module, 'ipv6')
    results['filter']['ipv6'] = rules

    results['msg'] = 'mkfilt completed successfully'
    module.exit_json(**results)


if __name__ == '__main__':
    main()
