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
- AIX Development Team (@pbfinley1911)
module: lpar_facts
short_description: Reports logical partition (LPAR) related information as facts.
description:
- Lists and reports information related to logical partition (LPAR) in Ansible facts.
version_added: '1.1.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
options: {}
notes:
  - You can refer to the IBM documentation for additional information on the lparstat command at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/l_commands/lparstat.html).
'''

EXAMPLES = r'''
- name: Retrieve the LPAR related information
  lpar_facts:
- name: Print the LPAR related information
  debug:
    var: ansible_facts.lpar
'''

RETURN = r'''
ansible_facts:
  description:
  - Facts to add to ansible_facts about LPAR related information.
  returned: always
  type: complex
  contains:
    lpar:
      description:
      - Reports logical partition (LPAR) related information.
      returned: always
      type: dict
      elements: dict
      contains:
        nodename:
          description: Node name.
          returned: always
          type: str
        lpar_name:
          description: Partition name.
          returned: when available
          type: str
        lpar_number:
          description: Partition number.
          returned: when available
          type: int
        lpar_type:
          description: Type.
          returned: always
          type: str
        lpar_mode:
          description: Mode.
          returned: always
          type: str
        entitled_capacity:
          description: Entitled capacity.
          returned: always
          type: float
        group_id:
          description: Partition Group-ID.
          returned: when available
          type: int
        pool_id:
          description: Shared Pool ID.
          returned: when available
          type: int
        online_vcpus:
          description: Online Virtual CPUs.
          returned: always
          type: int
        max_vcpus:
          description: Maximum Virtual CPUs.
          returned: always
          type: int
        min_vcpus:
          description: Minimum Virtual CPUs.
          returned: always
          type: int
        online_memory:
          description: Online Memory.
          returned: always
          type: float
        max_memory:
          description: Maximum Memory.
          returned: always
          type: float
        min_memory:
          description: Minimum Memory.
          returned: always
          type: float
        ps_16G:
          description: 16GB Page Memory.
          returned:  when available
          type: int
        variable_weight:
          description: Variable Capacity Weight.
          returned: when available
          type: int
        minimum_capacity:
          description: Minimum Capacity.
          returned: always
          type: float
        maximum_capacity:
          description: Maximum Capacity.
          returned: always
          type: float
        capacity_increment:
          description: Capacity Increment.
          returned: always
          type: float
        max_pcpus_in_sys:
          description: Maximum Physical CPUs in system.
          returned: always
          type: int
        pcpus_in_sys:
          description: Active Physical CPUs in system.
          returned: always
          type: int
        pcpus_in_pool:
          description: Active CPUs in Pool.
          returned: when available
          type: int
        shcpus_in_sys:
          description: Shared Physical CPUs in system.
          returned: when available
          type: int
        max_pool_capacity:
          description: Maximum Capacity of Pool.
          returned: when available
          type: int
        entitled_pool_capacity:
          description: Entitled Capacity of Pool.
          returned: when available
          type: int
        unalloc_capacity:
          description: Unallocated Capacity.
          returned: when available
          type: float
        pcpu_percent:
          description: Physical CPU Percentage.
          returned: always
          type: float
        unalloc_weight:
          description: Unallocated Weight.
          returned: when available
          type: int
        vrm_mode:
          description: Memory Mode.
          returned: when available
          type: str
        ent_mem_capacity:
          description: Total I/O Memory Entitlement.
          returned: when available
          type: float
        var_mem_weight:
          description: Variable Memory Capacity Weight.
          returned: when available
          type: int
        vrm_pool_id:
          description: Memory Pool ID.
          returned: when available
          type: int
        vrm_pool_physmem:
          description: Physical Memory in the Pool.
          returned: when available
          type: float
        hyp_pagesize:
          description: Hypervisor Page Size.
          returned: when available
          type: str
        unalloc_var_mem_weight:
          description: Unallocated Variable Memory Capacity Weight.
          returned: when available
          type: int
        unalloc_ent_mem_capacity:
          description: Unallocated I/O Memory entitlement.
          returned: when available
          type: float
        vrm_group_id:
          description: Memory Group ID of LPAR.
          returned: when available
          type: int
        desired_vcpus:
          description: Desired Virtual CPUs.
          returned: always
          type: int
        desired_memory:
          description: Desired Memory.
          returned: always
          type: float
        desired_variable_capwt:
          description: Desired Variable Capacity Weight.
          returned: when available
          type: int
        desired_capacity:
          description: Desired Capacity.
          returned: always
          type: float
        ame_factor_tgt:
          description: Target Memory Expansion Factor.
          returned: when available
          type: float
        ame_memsizepgs:
          description: Target Memory Expansion Size.
          returned: when available
          type: float
        psmode:
          description: Power Saving Mode.
          returned: when supported
          type: str
        spcm_status:
          description: Sub Processor Mode.
          returned: when supported
          type: str
        servpar_id:
          description: Service Partition ID.
          returned: when available
          type: int
        num_lpars:
          description: Number of Configured LPARs.
          returned: when available
          type: int
        inc_core_crypto_capable:
          description: Capability of In-Core Crypto Acceleration.
          returned: always
          type: bool
        inc_core_crypto_enabled:
          description: Enablement of In-Core Crypto Acceleration.
          returned: always
          type: bool
        nxcrypto_acc_capable:
          description: Capability of NX Crypto Acceleration.
          returned: always
          type: bool
        nxcrypto_acc_enabled:
          description: Enablement of NX Crypto Acceleration.
          returned: always
          type: bool
        full_coredump:
          description: Full core dump status.
          returned: always
          type: bool
        proc_imp_mode:
          description: Processor Implementation Mode.
          returned: always
          type: str
        proc_type:
          description: Processor Type.
          returned: always
          type: str
        oslevel:
          description: Operating system level.
          returned: always
          type: dict
          elements: dict
          contains:
            oslevel:
              description:
              - OperatingSystemBaseVersion TechnologyLevel ServicePack Build (vrmf).
              returned: always
              type: dict
              sample: '"oslevel": { "build": 2147, "sp": 3, "tl": 2, "base": "7.2.0.0" }'
        IBM.MCP_info:
          description: lsrsrc IBM.MCP command's output
          returned: always
          type: dict
          elements: dict
          contains:
            resource list:
              description: Resource Persistent Attributes for IBM.MCP
              returned: always
              type: dict
              sample:
                "resource 1": {
                    "ActiveCommMode": "1",
                    "ActivePeerDomain": "",
                    "ConnectivityNames": "{127.0.0.1}",
                    "HMCAddIPs": "",
                    "HMCAddIPv6s": "",
                    "HMCIPAddr": "127.0.0.1",
                    "HMCName": "Va87f6d*XXXXXXX",
                    "IPAddresses": "{127.0.0.1}",
                    "KeyToken": "somehmc",
                    "MNName": "127.0.0.1",
                    "NodeID": "12622478031XXXXXX",
                    "NodeNameList": "{somedomain.com}",
                    "RMCKey": "64b686a1XXXXXXXX"
                }
'''


from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


descr2key = {
    "Node Name": ('nodename', 'str'),
    "Partition Name": ('lpar_name', 'str'),
    "Partition Number": ('lpar_number', 'int'),
    "Type": ('lpar_type', 'str'),
    "Mode": ('lpar_mode', 'str'),
    "Entitled Capacity": ('entitled_capacity', 'float'),
    "Partition Group-ID": ('group_id', 'int'),
    "Shared Pool ID": ('pool_id', 'int'),
    "Online Virtual CPUs": ('online_vcpus', 'int'),
    "Maximum Virtual CPUs": ('max_vcpus', 'int'),
    "Minimum Virtual CPUs": ('min_vcpus', 'int'),
    "Online Memory": ('online_memory', 'sizemb'),
    "Maximum Memory": ('max_memory', 'sizemb'),
    "Minimum Memory": ('min_memory', 'sizemb'),
    "16GB Page Memory": ('ps_16G', 'int'),
    "Variable Capacity Weight": ('variable_weight', 'int'),
    "Minimum Capacity": ('minimum_capacity', 'float'),
    "Maximum Capacity": ('maximum_capacity', 'float'),
    "Capacity Increment": ('capacity_increment', 'float'),
    "Maximum Physical CPUs in system": ('max_pcpus_in_sys', 'int'),
    "Active Physical CPUs in system": ('pcpus_in_sys', 'int'),
    "Active CPUs in Pool": ('pcpus_in_pool', 'int'),
    "Shared Physical CPUs in system": ('shcpus_in_sys', 'int'),
    "Maximum Capacity of Pool": ('max_pool_capacity', 'int'),
    "Entitled Capacity of Pool": ('entitled_pool_capacity', 'int'),
    "Unallocated Capacity": ('unalloc_capacity', 'float'),
    "Physical CPU Percentage": ('pcpu_percent', 'percent'),
    "Unallocated Weight": ('unalloc_weight', 'int'),
    "Memory Mode": ('vrm_mode', 'str'),
    "Total I/O Memory Entitlement": ('ent_mem_capacity', 'sizemb'),
    "Variable Memory Capacity Weight": ('var_mem_weight', 'int'),
    "Memory Pool ID": ('vrm_pool_id', 'int'),
    "Physical Memory in the Pool": ('vrm_pool_physmem', 'sizegb'),
    "Hypervisor Page Size": ('hyp_pagesize', 'str'),
    "Unallocated Variable Memory Capacity Weight": ('unalloc_var_mem_weight', 'int'),
    "Unallocated I/O Memory entitlement": ('unalloc_ent_mem_capacity', 'sizemb'),
    "Memory Group ID of LPAR": ('vrm_group_id', 'int'),
    "Desired Virtual CPUs": ('desired_vcpus', 'int'),
    "Desired Memory": ('desired_memory', 'sizemb'),
    "Desired Variable Capacity Weight": ('desired_variable_capwt', 'int'),
    "Desired Capacity": ('desired_capacity', 'float'),
    "Target Memory Expansion Factor": ('ame_factor_tgt', 'float'),
    "Target Memory Expansion Size": ('ame_memsizepgs', 'sizemb'),
    "Power Saving Mode": ('psmode', 'str'),
    "Sub Processor Mode": ('spcm_status', 'str'),
    "Service Partition ID": ('servpar_id', 'int'),
    "Number of Configured LPARs": ('num_lpars', 'int'),
    "Processor Implementation Mode": ('proc_imp_mode', 'str'),
    "Processor Type": ('proc_type', 'str'),
    "NX Crypto Acceleration": ('nxcrypto_acc', 'bool'),
    "In-Core Crypto Acceleration": ('inc_core_crypto', 'bool'),
    "Full Core": ('full_coredump', 'bool'),
    "oslevel": ('oslevel', 'str'),
    "IBM.MCP_info": ('IBM.MCP_info', 'str')
}


def parse_MCP_info(stdout):
    """
    Utility function to parse the information retrieved from "lsrsrc IBM.MCP" command
    arguments:
      stdout - Standard output of the command
    returns:
      parsed_info (dict) - Parsed stdout in the form of a dictionary
    """
    parsed_info = {}
    lines = stdout.splitlines()
    current_resource = ""
    resource_info = {}

    for line in lines:
        if ":" not in line and "=" not in line:
            continue
        if ":" in line:
            if current_resource:
                parsed_info[current_resource] = resource_info
                resource_info = {}
                current_resource = line.strip()[:-1]
            else:
                current_resource = line.strip()[:-1]
        elif "=" in line:
            id, val = line.split("=")
            if id[:2] == "\t":
                id = id[2:]
            id = id.strip()
            val = val.strip()
            if id in ["NodeID", "ActiveCommMode"]:
                val = int(val)
            else:
                val = ''.join(val.split('\"'))
            resource_info[id] = val

    if current_resource not in parsed_info.keys():
        parsed_info[current_resource] = resource_info

    return parsed_info


def main():
    module = AnsibleModule(
        argument_spec={},
        supports_check_mode=True
    )

    lparstat_path = module.get_bin_path('lparstat', required=True)
    prtconf_path = module.get_bin_path('prtconf', required=True)
    oslevel_path = module.get_bin_path('oslevel', required=True)
    lsrsrc_path = module.get_bin_path('lsrsrc', required=True)

    cmd = [lparstat_path, '-is']
    ret, stdout, stderr = module.run_command(cmd, check_rc=True)
    ''' prtconf to get the following:
     NX Crypto Acceleration
     In-Core Crypto Acceleration
     Processor Implementation Mode
     Processor Type
     Full Core
    '''
    cmd = [prtconf_path]
    ret1, stdout1, stderr1 = module.run_command(cmd, check_rc=True)

    if not ret and not ret1:
        stdout = stdout + "\n" + stdout1

    '''Get oslevel and print in the format of
        base level,
        technology level,
        service pack,
        build
    '''
    cmd = [oslevel_path, '-s']
    ret1, stdout1, stderr1 = module.run_command(cmd, check_rc=True)
    stdout1 = "oslevel: " + stdout1

    cmd = [lsrsrc_path, 'IBM.MCP']
    ret2, stdout2, stderr2 = module.run_command(cmd, check_rc=True)

    if not ret2:
        stdout = stdout + "\n" + stdout1

    lparstat = {}
    lparstat["IBM.MCP_info"] = parse_MCP_info(stdout2)

    for line in stdout.splitlines():
        if ':' not in line:
            continue
        attr, val = line.split(':', 2)
        key = descr2key.get(attr.strip(), None)
        if key:
            val = val.strip()
            if not val or val == '-':
                continue
            id, vtype = key
            if vtype == 'str':
                if id == "oslevel":
                    vrmf = val.split('-')
                    if len(vrmf) == 4:
                        # formatting the base level in the format 7.2.0.0
                        level_1 = int(int(vrmf[0]) / 1000) % 10
                        level_2 = int(int(vrmf[0]) / 100) % 10
                        level_3 = int(int(vrmf[0]) / 10) % 10
                        level_4 = int(vrmf[0]) % 10
                        baselevel = f"{level_1}.{level_2}.{level_3}.{level_4}"
                        lparstat[id] = {
                            'base': baselevel,
                            'tl': int(vrmf[1]),
                            'sp': int(vrmf[2]),
                            'build': int(vrmf[3])
                        }
                else:
                    lparstat[id] = val
            elif vtype == 'int':
                lparstat[id] = int(val)
            elif vtype == 'float':
                lparstat[id] = float(val)
            elif vtype == 'sizemb':
                lparstat[id] = float(val.split()[0].strip())
            elif vtype == 'sizegb':
                lparstat[id] = float(val.split()[0].strip())
            elif vtype == 'percent':
                lparstat[id] = float(val.strip().rstrip('%'))
            elif vtype == 'bool':
                if id == "full_coredump":
                    if val.strip() == "false":
                        lparstat[id] = False
                    else:
                        lparstat[id] = True
                elif id == "nxcrypto_acc":
                    nxcrypto_val = val.strip()
                    if "not Capable" in nxcrypto_val:
                        lparstat['nxcrypto_acc_capable'] = False
                    else:
                        lparstat['nxcrypto_acc_capable'] = True
                    if "not Enabled" in nxcrypto_val:
                        lparstat['nxcrypto_acc_enabled'] = False
                    else:
                        lparstat['nxcrypto_acc_enabled'] = True
                elif id == "inc_core_crypto":
                    inc_crypto_val = val.strip()
                    if "not Capable" in inc_crypto_val:
                        lparstat['inc_core_crypto_capable'] = False
                    else:
                        lparstat['inc_core_crypto_capable'] = True
                    if "not Enabled" in inc_crypto_val:
                        lparstat['inc_core_crypto_enabled'] = False
                    else:
                        lparstat['inc_core_crypto_enabled'] = True

    module.exit_json(ansible_facts=dict(lpar=lparstat))


if __name__ == '__main__':
    main()
