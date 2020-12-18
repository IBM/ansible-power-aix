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
module: mktun
short_description: Creates, activates, deactivates and removes tunnels.
description:
- Creates a tunnel definition in the tunnel database.
- Activates tunnels.
- Deactivates operational tunnels and optionally removes tunnel definitions.
- Exports and imports tunnel definitions.
version_added: '2.9'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- 'Privileged user with authorizations: B(aix.security.network.vpn,aix.security.network.stat)'
options:
  manual:
    description:
    - List of manual tunnels.
    type: dict
    suboptions:
      import_ipv4:
        description:
        - Base64 encoding of IPv4 tunnels to be imported.
        type: str
      import_ipv6:
        description:
        - Base64 encoding of IPv6 tunnels to be imported.
        type: str
      ipv4:
        description:
        - IPv4 tunnels.
        type: list
        elements: dict
        suboptions: &ipcommon
          id:
            description:
            - Tunnel id.
            - Only used to deactivate or remove an existing tunnel.
            type: int
          src:
            description:
            - Source tunnel definition.
            type: dict
            suboptions: &tuncommon
              address:
                description:
                - Host IP address.
                - A host name is also valid and the first IP address returned
                  by name server for the host name will be used.
                type: str
                required: true
              ah_algo:
                description:
                - Authentication algorithm, used for IP packet authentication.
                type: str
              ah_key:
                description:
                - AH Key String.
                - The input must be a hexadecimal string.
                type: str
              ah_spi:
                description:
                -  Security Parameter Index for AH.
                type: int
              esp_algo:
                description:
                - Encryption algorithm, used for IP packet encryption.
                type: str
              esp_key:
                description:
                - ESP Key String.
                - The input must be a hexadecimal string.
                type: str
              esp_spi:
                description:
                - Security Parameter Index for ESP.
                type: int
              enc_mac_algo:
                description:
                - ESP Authentication Algorithm.
                - Only used when I(newheader=yes).
                type: str
              enc_mac_key:
                description:
                - ESP Authentication Key.
                - Only used when I(newheader=yes).
                type: str
              policy:
                description:
                - Identifies how the IP packet authentication and/or
                  encryption is to be used by this host.
                - C(encr/auth) specifies that IP packet gets encrypted before authentication.
                - C(auth/encr) specifies that IP packet gets encrypted after authentication.
                - C(encr) specifies that IP packet gets encrypted only.
                - C(auth) specifies that IP packet gets authenticated only.
                type: str
                choices: [ encr/auth, auth/encr, encr, auth ]
          dst:
            description:
            - Destination tunnel definition.
            type: dict
            suboptions: *tuncommon
          tunnel_only:
            description:
            - Only create  the tunnel definition. Do not automatically
              generate two filter rules for the tunnel.
            type: bool
            default: no
          key_lifetime:
            description:
            - Key Lifetime, specified in minutes.
            - Value 0 indicates that the manual tunnel will never expire.
            - The default value is 480.
            type: int
          newheader:
            description:
            - New header format.
            - The new header format preserves a field in the ESP and AH
              headers for replay prevention and also allows ESP authentication.
            type: bool
          replay:
            description:
            - Replay prevention.
            - Only used when I(newheader=yes).
            type: bool
            default: no
          tunnel_mode:
            description:
            - Tunnel mode will encapsulate the entire IP packet, while the
              transport mode only encapsulates the data portion of the IP packet.
            type: bool
            default: yes
          fw_address:
            description:
            - IP address of the firewall that is between the source and
              destination hosts. A tunnel will be established between this
              host and the firewall. Therefore the corresponding tunnel
              definition must be made on the firewall host.
            - A host name may also be used and the first IP address returned
              by the name server for that host name will be used.
            type: str
          dst_mask:
            description:
            - Network mask for the secure network behind a firewall.
            - Only used when I(fw_address) is specified.
            type: str
          state:
            description:
            - Tunnel state.
            type: str
            choices: [ active, defined, absent ]
            default: active
          export:
            description:
            - Export tunnel and associated filter rule definitions.
            type: bool
            default: no
      ipv6:
        description:
        - IPv6 tunnels.
        type: list
        elements: dict
        suboptions: *ipcommon
'''

EXAMPLES = r'''
- name: Create and activate a manual IPv4 tunnel
  mktun:
    manual:
      ipv4:
      - src:
          address: 10.10.11.72
          ah_algo: HMAC_MD5
          esp_algo: DES_CBC_8
        dst:
          address: 10.10.11.98
          esp_spi: 12345

- name: Export IPv4 tunnel definition for tunnel id 3 on srchost
  mktun:
    manual:
      ipv4:
        - id: 3
          export: yes
  register: export_result
  when: 'inventory_hostname == srchost'
- name: Import IPv4 tunnel definition on dsthost
  mktun:
    manual:
      import_ipv4: '{{ export_result.export_ipv4 }}'
  when: 'inventory_hostname == dsthost'

- name: Remove manual IPv4 tunnel with id 3 from tunnel database
  mktun:
    manual:
      ipv4:
        - id: 3
          state: absent

- name: Deactivate manual IPv4 tunnel with id 4
  mktun:
    manual:
      ipv4:
        - id: 4
          state: defined

- name: Activate manual IPv4 tunnel with id 5
  mktun:
    manual:
      ipv4:
        - id: 5
          state: active

- name: Gather the tunnel facts
  mktun:
- name: Print the tunnel facts
  debug:
    var: ansible_facts.tunnels
'''

RETURN = r'''
stdout:
    description: The standard output
    returned: always
    type: str
stderr:
    description: The standard error
    returned: always
    type: str
export_ipv4:
  description:
  - Base64 encoding of exported IPv4 tunnel definitions.
  returned: when export is true
  type: str
export_ipv6:
  description:
  - Base64 encoding of exported IPv6 tunnel definitions.
  returned: when export is true
  type: str
ansible_facts:
  description:
  - Facts to add to ansible_facts about tunnels.
  returned: always
  type: complex
  contains:
    tunnels:
      description: Tunnel definitions.
      returned: always
      type: dict
      contains:
        auth_algos:
          description: List of installed authentication algorithms.
          returned: always
          type: list
          elements: str
        encr_algos:
          description: List of installed encryption algorithms.
          returned: always
          type: list
          elements: str
        manual:
          description: Manual tunnel definitions.
          returned: always
          type: list
          elements: dict
'''

import base64
import os
import re
import tempfile

from ansible.module_utils.basic import AnsibleModule


def gentun(module, vopt, tun):
    """
    Create the manual tunnel definition in the tunnel database
    with gentun and return the tunnel id.
    """
    cmd = [gentun_path, vopt, '-t', 'manual', '-s', tun['src']['address'], '-d', tun['dst']['address']]

    # gentun options that use lowercase letters for source and uppercase for destination
    gentun_opts = {
        'ah_algo': '-a',
        'enc_mac_algo': '-b',
        'enc_mac_key': '-c',
        'esp_algo': '-e',
        'ah_key': '-h',
        'esp_key': '-k',
        'esp_spi': '-n',
        'ah_spi': '-u'
    }
    for key, opt in gentun_opts.items():
        if tun['src'][key]:
            cmd += [opt, str(tun['src'][key])]
        if tun['dst'][key]:
            cmd += [opt.upper(), str(tun['dst'][key])]

    if tun['src']['policy'] == 'encr/auth':
        cmd += ['-p', 'ea']
    elif tun['src']['policy'] == 'auth/encr':
        cmd += ['-p', 'ae']
    elif tun['src']['policy'] == 'auth':
        cmd += ['-p', 'a']
    elif tun['src']['policy'] == 'encr':
        cmd += ['-p', 'e']

    if tun['dst']['policy'] == 'encr/auth':
        cmd += ['-P', 'ea']
    elif tun['dst']['policy'] == 'auth/encr':
        cmd += ['-P', 'ae']
    elif tun['dst']['policy'] == 'auth':
        cmd += ['-P', 'a']
    elif tun['dst']['policy'] == 'encr':
        cmd += ['-P', 'e']

    if tun['fw_address']:
        cmd += ['-f', tun['fw_address']]
        if tun['dst_mask']:
            cmd += ['-x', tun['dst_mask']]
    if tun['tunnel_only']:
        cmd += ['-g']

    if tun['key_lifetime']:
        cmd += ['-l', str(tun['key_lifetime'])]
    if not tun['fw_address'] and tun['tunnel_mode']:
        cmd += ['-m', 'tunnel']

    if tun['newheader']:
        cmd += ['-z', 'Y']
        if tun['replay']:
            cmd += ['-y', 'Y']

    ret, stdout, stderr = module.run_command(cmd, check_rc=True)
    m = re.search(r"^Tunnel (\d+) for IPv\d has been added successfully", stdout, re.MULTILINE)
    if not m:
        return None
    return int(m.group(1))


def lstun(module):
    """
    List manual tunnel definitions from tunnel database.

    Fields returned by lstun -O for manual tunnels:
        tunnel|source|dest|policy|dpolicy|mask|fw|emode|tunlife|
        sspia|dspia|aalgo|daalgo|sakey|dakey|
        sspie|dspie|ealgo|dealgo|sekey|dekey|
        eaalgo|deaalgo|seakey|deakey|
        replay|header
    """
    tunnels = {}
    for version in ['ipv4', 'ipv6']:
        tunnels[version] = {}

        vopt = '-v4' if version != 'ipv6' else '-v6'

        # List tunnel definitions in tunnel database
        cmd = [lstun_path, vopt, '-p', 'manual', '-O']
        ret, stdout, stderr = module.run_command(cmd, check_rc=True)
        for line in stdout.splitlines():
            if line.startswith('#'):
                continue
            fields = line.split('|')
            if len(fields) != 27:
                continue
            tun = {}
            tun['state'] = 'defined'
            tun['src'] = {}
            tun['dst'] = {}
            tun['src']['address'] = fields[1]
            tun['dst']['address'] = fields[2]
            if fields[3] == 'auth only':
                tun['src']['policy'] = 'auth'
            elif fields[3] == 'encr only':
                tun['src']['policy'] = 'encr'
            else:
                tun['src']['policy'] = fields[3]
            if fields[4] == 'auth only':
                tun['dst']['policy'] = 'auth'
            elif fields[4] == 'encr only':
                tun['dst']['policy'] = 'encr'
            else:
                tun['dst']['policy'] = fields[4]
            if fields[5]:
                tun['dst_mask'] = fields[5]
            if fields[6]:
                tun['fw_address'] = fields[6]
            tun['tunnel_mode'] = fields[7] == 'Tunnel'
            tun['key_lifetime'] = int(fields[8])
            tun['src']['ah_spi'] = int(fields[9])
            tun['dst']['ah_spi'] = int(fields[10])
            tun['src']['ah_algo'] = fields[11]
            tun['dst']['ah_algo'] = fields[12]
            tun['src']['ah_key'] = fields[13]
            tun['dst']['ah_key'] = fields[14]
            tun['src']['esp_spi'] = int(fields[15])
            tun['dst']['esp_spi'] = int(fields[16])
            tun['src']['esp_algo'] = fields[17]
            tun['dst']['esp_algo'] = fields[18]
            tun['src']['esp_key'] = fields[19]
            tun['dst']['esp_key'] = fields[20]
            if fields[21]:
                tun['src']['enc_mac_algo'] = fields[21]
            if fields[22]:
                tun['dst']['enc_mac_algo'] = fields[22]
            if fields[23]:
                tun['src']['enc_mac_key'] = fields[23]
            if fields[24]:
                tun['dst']['enc_mac_key'] = fields[24]
            tun['replay'] = fields[25] == 'Y'
            tun['newheader'] = fields[26] == 'Y'

            tunnels[version][int(fields[0])] = tun

        # Mark active tunnels as active
        cmd = [lstun_path, vopt, '-p', 'manual', '-O', '-a']
        ret, stdout, stderr = module.run_command(cmd, check_rc=True)
        for line in stdout.splitlines():
            if line.startswith('#'):
                continue
            fields = line.split()
            if len(fields) >= 2:
                if int(fields[1]) in tunnels[version]:
                    tunnels[version][int(fields[1])]['state'] = 'active'

    return tunnels


def make_devices(module):
    """
    Make sure ipsec_v4 and ipsec_v6 devices are Available.
    """
    for version in ['4', '6']:
        cmd = ['mkdev', '-l', 'ipsec', '-t', version]
        module.run_command(cmd, check_rc=True)


def main():
    global gentun_path
    global lstun_path

    tuncommon = dict(
        type='dict',
        options=dict(
            address=dict(required=True, type='str'),
            ah_algo=dict(type='str'),
            ah_key=dict(type='str'),
            ah_spi=dict(type='int'),
            esp_algo=dict(type='str'),
            esp_key=dict(type='str'),
            esp_spi=dict(type='int'),
            enc_mac_algo=dict(type='str'),
            enc_mac_key=dict(type='str'),
            policy=dict(type='str', choices=['encr/auth', 'auth/encr', 'encr', 'auth'])
        )
    )

    ipcommon = dict(
        type='list', elements='dict', default=[],
        options=dict(
            id=dict(type='int'),
            src=tuncommon,
            dst=tuncommon,
            tunnel_only=dict(type='bool', default=False),
            key_lifetime=dict(type='int'),
            newheader=dict(type='bool'),
            replay=dict(type='bool', default=False),
            tunnel_mode=dict(type='bool', default=True),
            fw_address=dict(type='str'),
            dst_mask=dict(type='str'),
            state=dict(type='str', choices=['active', 'defined', 'absent'], default='active'),
            export=dict(type='bool', default=False)
        )
    )

    module = AnsibleModule(
        argument_spec=dict(
            manual=dict(
                type='dict',
                options=dict(
                    ipv4=ipcommon,
                    ipv6=ipcommon,
                    import_ipv4=dict(type='str'),
                    import_ipv6=dict(type='str')
                )
            )
        ),
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    ipsecstat_path = module.get_bin_path('ipsecstat', required=True)
    gentun_path = module.get_bin_path('gentun', required=True)
    lstun_path = module.get_bin_path('lstun', required=True)
    mktun_path = module.get_bin_path('mktun', required=True)
    rmtun_path = module.get_bin_path('rmtun', required=True)
    exptun_path = module.get_bin_path('exptun', required=True)
    imptun_path = module.get_bin_path('imptun', required=True)

    make_devices(module)

    results['ansible_facts'] = dict(tunnels=dict())

    # Retrieve the list of authentication algorithms
    ret, stdout, stderr = module.run_command([ipsecstat_path, '-A'], check_rc=True)
    results['ansible_facts']['tunnels']['auth_algos'] = stdout.splitlines()

    # Retrieve the list of encryption algorithms
    ret, stdout, stderr = module.run_command([ipsecstat_path, '-E'], check_rc=True)
    results['ansible_facts']['tunnels']['encr_algos'] = stdout.splitlines()

    tunnels = lstun(module)

    for version in ['ipv4', 'ipv6']:
        if not module.params['manual'] or version not in module.params['manual']:
            continue

        # Empty sets
        active_tid_list = set()
        defined_tid_list = set()
        absent_tid_list = set()
        export_tid_list = set()

        vopt = '-v4' if version != 'ipv6' else '-v6'
        for tun in module.params['manual'][version]:
            if tun['id']:
                tid = tun['id']
                # Ignore if tunnel is not defined
                if tid not in tunnels[version]:
                    continue
            else:
                if tun['state'] == 'absent':
                    continue
                tid = gentun(module, vopt, tun)
                results['changed'] = True

            if tun['state'] == 'active':
                if tid not in tunnels[version] or tunnels[version][tid]['state'] != 'active':
                    active_tid_list.add(str(tid))
            elif tun['state'] == 'defined':
                if tid in tunnels[version] and tunnels[version][tid]['state'] == 'active':
                    defined_tid_list.add(str(tid))
            elif tun['state'] == 'absent':
                if tid in tunnels[version]:
                    absent_tid_list.add(str(tid))

            if tun['export'] and tun['state'] != 'absent':
                export_tid_list.add(str(tid))

        # Activate tunnels that are marked as active
        if active_tid_list:
            cmd = [mktun_path, vopt, '-t', ','.join(active_tid_list)]
            module.run_command(cmd, check_rc=True)
            results['changed'] = True

        # Deactivate tunnels that are marked as defined
        if defined_tid_list:
            cmd = [rmtun_path, vopt, '-t', ','.join(defined_tid_list)]
            module.run_command(cmd, check_rc=True)
            results['changed'] = True

        # Remove tunnel definitions that are marked as absent
        if absent_tid_list:
            cmd = [rmtun_path, vopt, '-d', '-t', ','.join(absent_tid_list)]
            module.run_command(cmd, check_rc=True)
            results['changed'] = True

        # Process tunnel exports, if any
        if export_tid_list:
            tmpdir = tempfile.mkdtemp(dir=module.tmpdir)
            cmd = [exptun_path, vopt, '-f', tmpdir, '-t', ','.join(export_tid_list)]
            module.run_command(cmd, check_rc=True)
            source = os.path.join(tmpdir, 'ipsec_tun_manu.exp')
            with open(source, 'rb') as source_fh:
                source_content = source_fh.read()
                results['export_' + version] = base64.b64encode(source_content)

        # Process tunnel imports, if any
        if module.params['manual']['import_' + version]:
            source_content = base64.b64decode(module.params['manual']['import_' + version])
            tmpdir = tempfile.mkdtemp(dir=module.tmpdir)
            source = os.path.join(tmpdir, 'ipsec_tun_manu.exp')
            with open(source, 'wb') as source_fh:
                source_fh.write(source_content)
            cmd = [imptun_path, vopt, '-f', tmpdir]
            module.run_command(cmd, check_rc=True)
            results['changed'] = True

    # Re-run lstun if anything has changed
    if results['changed']:
        tunnels = lstun(module)

    results['ansible_facts']['tunnels']['manual'] = tunnels
    module.exit_json(**results)


if __name__ == '__main__':
    main()
