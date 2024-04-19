#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2022- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pvtorres1703)
module: nim_resource
short_description: show/define/delete NIM resource object(s).
description:
- This module facilitates the display, creation or deletion of NIM resource objects.
version_added: '1.5.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 2.7
- User with root authority to run the nim command.
- NIM master software bos.sysmgt.nim.master.
- 'Privileged user with authorization:
  B(aix.system.install,aix.system.nim.config.server,aix.system.nim.stat)'
options:
  action:
    description:
    - Specifies the action to be performed.
    - C(show) shows all NIM resource objects. Can be used with options I(name) or I(object_type) to filter objects.
    - C(create) creates a NIM resource object. It requires options I(name), I(object_type) and I(attributes).
    - C(delete) deletes a NIM resource object. It requires option I(name).
    type: str
    choices: [ show, create, delete ]
    required: true
  name:
    description:
    - Specifies the NIM object name.
    type: str
    required: false
  object_type:
    description:
    - NIM resource object's type.
    - Required for action I(action=create).
    - Optional for I(action=show).
    - Some of the choices are provided as examples. For details of all possible
      NIM resources objects, refer to the IBM documentation at
      U(https://www.ibm.com/docs/en/aix/7.2?topic=management-using-nim-resources)
    - The following are examples of the most common choices "pp_source, spot, bosinst_data, mksysb, fb_script and  res_group"
    type: str
    required: false
  attributes:
    description:
    - Specifies the attribute-value pairs required for I(action=create) or I(action=show)
    type: dict
    required: false
  showres:
    description:
    - show the contents of a resource.
    - supports spot and lpp_source.
    type: dict
    required: false
    suboptions:
      fetch_contents:
        description:
        - determines if the contents of a valid resource type will be fetched.
        type: bool
        default: false
      max_retries:
        description:
        - max number of attempts to fetch the contents a resource.
        type: int
        default: 10
      retry_wait_time:
        description:
        - wait time in seconds in between retrying attempts to fetch the contents of a resorce.
        type: int
        default: 1
notes:
  - You can refer to the IBM documentation for additional information on the NIM concept and command
    at U(https://www.ibm.com/support/knowledgecenter/ssw_aix_73/install/nim_concepts.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_73/n_commands/nim.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_73/n_commands/nim_master_setup.html).
'''

EXAMPLES = r'''
- name: Show all NIM resource objects.
  ibm.power_aix.nim_resource:
    action: show

- name: Create a copy of the images from source to location and
        define a NIM lpp_source resource from that location.
  ibm.power_aix.nim_resource:
    action: create
    name: lpp_730
    object_type: lpp_resource
    attributes:
      source: /software/AIX7300
      location: /nim1/copy_AIX7300_resource

- name: Define a NIM lpp_source resource object from a directory that
        contains the images.
  ibm.power_aix.nim_resource:
    action: create
    name: lpp_730
    object_type: lpp_resource
    attributes:
      location: /nim1/copy_AIX7300_resource

- name: Define a NIM spot (Shared Product Object Tree) resource
        using a defined lpp_source.
  ibm.power_aix.nim_resource:
    action: create
    name: spot_730
    object_type: spot
    attributes:
      source: lpp_730
      location: /nim1/spot_730_resource

- name: Create a NIM resource group object.
  ibm.power_aix.nim_resource:
    action: create
    name: ResGrp730
    object_type: res_group
    attributes:
      lpp_source: lpp_730
      spot: spot_730
      bosinst_data: bosinst_data730
      comments: "730 Resources"

- name: Show all the defined NIM resource objects.
  ibm.power_aix.nim_resource:
    action: show

- name: Show all the defined NIM resource objects of type spot.
  ibm.power_aix.nim_resource:
    action: show
    object_type: spot

- name: Show a specific NIM resource object.
  ibm.power_aix.nim_resource:
    action: show
    name: lpp_730

- name: Delete a NIM resource object.
  ibm.power_aix.nim_resource:
    action: delete
    name: spot_730
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
    sample: 'Resource spot_730 was removed.'
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
cmd:
    description: Command executed.
    returned: always
    type: str
nim_resource_found:
    description: Return if a queried object resource exist.
    returned: If I(action=show).
    type: bool
nim_resources:
    description: Dictionary output with the NIM resource object information.
    returned: If I(action=show).
    type: dict
    sample:
        "nim_resources": {
            "lpp_source_test": {
                "Rstate": "ready for use",
                "alloc_count": "0",
                "arch": "power",
                "class": "resources",
                "location": "/nim1/lpp_source_test4",
                "prev_state": "unavailable for use",
                "server": "master",
                "simages": "yes",
                "type": "lpp_source",
            }
        }

'''

import re
import time
from ansible.module_utils.basic import AnsibleModule

results = None

NIM_SHOWRES = [
    'spot',
    'lpp_source',
    # below are not yet supported
    'script',
    'bosinst_data',
    'image_data',
    'installp_bundle',
    'fix_bundle',
    'resolv_conf',
    'exclude_files',
    'adapter_def',
]
# NIM resource objects that contains filesets
# that can be fetched through nim -o showres .
NIM_SHOWRES_FILESETS = [
    'spot',
    'lpp_source',
]
# headers for spot and lpp_source showres output
NIM_SHOWRES_FILESET_HEADERS = [
    'package_name',
    'fileset',
    'level',
]


def res_show(module):
    '''
    Show nim resources.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        updated results dictionary.
    '''

    cmd = '/usr/sbin/lsnim -l'
    name = module.params['name']
    object_type = module.params['object_type']

    # This module will only show general information about the resource
    # object class.
    if not object_type and not name:
        cmd += ' -c resources'

    if object_type:
        cmd += f' -t {object_type}'

    if name:
        cmd += ' ' + name

    if module.check_mode:
        results['msg'] = f'Command \'{cmd}\' preview mode, execution skipped.'
        return

    return_code, stdout, stderr = module.run_command(cmd)

    results['stderr'] = stderr
    results['stdout'] = stdout
    results['cmd'] = cmd
    results['nim_resources'] = {}
    results['nim_resource_found'] = False

    if return_code != 0:

        # 0042-053 The NIM objefct is not there.
        pattern = r"0042-053"
        found = re.search(pattern, stderr)

        if found:
            results['msg'] = f'There is no NIM object resource named {name} '
        else:
            results['msg'] = f'Error trying to display object {name}'
            results['rc'] = return_code
            module.fail_json(**results)
    else:
        if stdout.strip():
            results['nim_resources'] = build_dic(stdout)
            results['nim_resource_found'] = True

    if module.params['showres']:
        # check if we need to fetch the filesets installed in a lpp_source or
        # spot NIM object.
        for resource, info in results['nim_resources'].items():
            results['nim_resources'][resource]['contents'] = res_showres(module, resource, info)

    return


def res_create(nim_cmd, module):
    '''
    Define a NIM resource object.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        updated results dictionary.
    '''

    opts = ""
    name = module.params['name']
    object_type = module.params['object_type']
    attributes = module.params['attributes']

    if object_type:
        if object_type == "res_group":
            cmd = nim_cmd + ' -o define '
        else:
            cmd = nim_cmd + ' -a server=master -o define '
        cmd += ' -t ' + object_type

    if attributes is not None:
        for attr, val in attributes.items():
            opts += f" -a {attr}=\"{val}\" "
        cmd += opts

    if name:
        cmd += ' ' + name

    if module.check_mode:
        results['msg'] = f'Command \'{cmd}\' preview mode, execution skipped.'
        return

    return_code, stdout, stderr = module.run_command(cmd)

    results['stderr'] = stderr
    results['stdout'] = stdout
    results['cmd'] = cmd

    if return_code != 0:

        # 0042-081 The resource already exists on "master"
        # 0042-032 object name must be unique
        pattern = r"0042-081|0042-032"
        found = re.search(pattern, stderr)
        if not found:
            results['rc'] = return_code
            results['msg'] = f'Error trying to define resource {name} '
            module.fail_json(**results)
        else:
            results['msg'] = 'Resource already exist'

    else:
        results['msg'] = f'Creation of resource {name} was a success'
        results['changed'] = True

    return


def res_delete(nim_cmd, module):
    '''
    Remove a NIM resource object.

    arguments:
        module  (dict): The Ansible module
    note:
        Exits with fail_json in case of error
    return:
        updated results dictionary.
    '''

    name = module.params['name']
    cmd = nim_cmd + f' -o remove {name}'

    if module.check_mode:
        results['msg'] = f'Command \'{cmd}\' in preview mode, execution skipped.'
        return

    return_code, stdout, stderr = module.run_command(cmd)

    results['stderr'] = stderr
    results['stdout'] = stdout
    results['cmd'] = cmd

    if return_code != 0:

        # 0042-053 The NIM objefct is not there.
        pattern = r"0042-053"
        found = re.search(pattern, stderr)

        if found:
            results['msg'] = f'There is no NIM object resource named {name} '
        else:
            results['msg'] = f'Error trying to remove NIM object {name}'
            results['rc'] = return_code
            module.fail_json(**results)

    else:
        results['msg'] = f'Resource {name} was removed.'
        results['changed'] = True

    return


def build_dic(stdout):
    """
    Build dictionary with the stdout info

    arguments:
        stdout   (str): stdout of the command to parse
    returns:
        info    (dict): NIM object dictionary
    """

    info1 = {}
    info = {}
    key = ""
    lines = stdout.splitlines()

    for line in lines:
        if "=" not in line:
            if key:
                info[key] = info1
                info1 = {}
            key = line.strip()[:-1]
        else:
            attr = (line.split("=")[0]).strip()
            val = (line.split("=")[1]).strip()
            info1[attr] = val

    if key:
        info[key] = info1

    return info


def res_showres(module, resource, info):
    """
    Fetch contents of valid NIM object resource

    arguments:
        module  (dict): The Ansible module
        resource (str): NIM resource name
        info    (info): NIM resource attributes information
    return:
        contents: (dict): NIM resource contents
    """
    fail_msg = f'Unable to fetch contents of {resource}.'
    max_retries = module.params['showres']['max_retries']
    retry_wait_time = module.params['showres']['max_retries']
    contents = {}
    results['testing'] = ""
    # 0042-001 nim: processing error encountered on "master":,
    #     0042-207 m_showres: Unable to allocate the spot_72V_2114 resource to master.
    pattern = r"0042-207"

    if info['type'] in NIM_SHOWRES:
        cmd = 'nim -o showres '
        if info['type'] == 'spot':
            cmd += '-a lslpp_flags=Lc '
        elif info['type'] == 'lpp_source':
            cmd += '-a installp_flags=L '
        cmd += resource

        while True:
            return_code, stdout, stderr = module.run_command(cmd)
            results['testing'] += f"max_retries: {max_retries}, rc: {return_code}"

            if return_code != 0:
                max_retries -= 1
                results['cmd'] = cmd
                results['stderr'] = stderr
                results['stdout'] = stdout
                results['rc'] = return_code

                if max_retries == 0:
                    results['msg'] += fail_msg
                    results['msg'] += "Number of attempts to fetch contents of "
                    results['msg'] += f"{resource} has been reached."
                    module.fail_json(**results)
                    break

                found = re.search(pattern, stderr)
                if found:
                    # error code 0042-207 means that the resource is
                    # currently being used by another showres command
                    # wait and retry
                    time.sleep(retry_wait_time)
                    continue
                # for any other error proceed to the next resource
                results['msg'] += fail_msg
                module.fail_json(**results)
                break
            else:
                # successfully fetched contents, stored in stdout
                # break out of retry loop and parse contents
                break

        # parse contents of nim resource
        if info['type'] in NIM_SHOWRES_FILESETS:
            lines = stdout.splitlines()
            for line in lines[1:]:
                fileset_info = line.split(':')[0:3]
                # fileset_info[0] - package name
                # fileset_info[1] - fileset name
                # fileset_info[2] - fileset level
                if fileset_info[1] in contents:
                    contents[fileset_info[1]][NIM_SHOWRES_FILESET_HEADERS[2]].append(
                        fileset_info[2]
                    )
                else:
                    contents[fileset_info[1]] = dict(
                        zip(
                            NIM_SHOWRES_FILESET_HEADERS[0:2],
                            fileset_info[0:2]
                        )
                    )
                    contents[fileset_info[1]][NIM_SHOWRES_FILESET_HEADERS[2]] = [
                        fileset_info[2]
                    ]

    return contents


def main():
    global results

    showres_spec = dict(
        fetch_contents=dict(type='bool', default=False),
        max_retries=dict(type='int', default=10),
        retry_wait_time=dict(type='int', default=1)
    )

    module = AnsibleModule(

        argument_spec=dict(
            action=dict(type='str', required=True, choices=['show', 'create', 'delete']),
            name=dict(type='str'),
            object_type=dict(type='str'),
            attributes=dict(type='dict'),
            showres=dict(type='dict', options=showres_spec),
        ),
        required_if=[
            ('action', 'create', ('name', 'object_type', 'attributes')),
            ('action', 'delete', ('name',), True),
        ],
        supports_check_mode=True
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    nim_cmd = module.get_bin_path('nim', required=False)

    if nim_cmd is None:
        results['msg'] = "Target nim server does not have the required software for "\
            "nim server operations. Verify if the filesystem bos.sysmgt.nim.master is installed."
        module.fail_json(**results)

    action = module.params['action']

    if action == 'show':
        res_show(module)
    elif action == 'create':
        res_create(nim_cmd, module)
    elif action == 'delete':
        res_delete(nim_cmd, module)
    else:
        results['msg'] = 'The action selected is NOT recognized. Please check again.'
        module.fail_json(**results)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
