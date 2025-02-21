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
- AIX Development Team (@schamola)
module: bosboot
short_description: Creates boot image.
description:
- The bosboot command creates the boot image that interfaces with the machine boot ROS (Read-Only Storage) EPROM (Erasable Programmable Read-Only Memory).
- The bosboot command creates a boot file (boot image) from a RAM (Random Access Memory) disk file system and a kernel. This boot image is transferred to a
  particular media that the ROS boot code recognizes. When the machine is powered on or rebooted, the ROS boot code loads the boot image from the media into
  memory. ROS then transfers control to the loaded images kernel.
  version_added:'1.6.0'
requirements:
- AIX >= 7.1 TL3
- Python >= 3.6
- 'Privileged user with authorization:
  B(aix.system.install)'
options:
  disk_device:
    description:
    - Specifies the boot device.
    type: str
    default: 'hd5'
  prototype_file:
    description:
    - Uses the specified prototype file for the RAM disk file system.
    type: str
  only_verify:
    description:
    - Verify, but do not build boot image for I(directory) and I(image_name).
    type: bool
    default: False
  create_image:
    description:
    - Creates the complete boot image with I(image_name) in I(directory).
    type: bool
    default: False
  directory:
    description:
    - Specifies the directory in which the boot image will be stored.
    type: str
    default: '/tmp'
  image_name:
    description:
    - Specifies the name of the output image from the bosboot command.
    - The image will be stored in/as 'directory/image_name'.
    - If both directory and image_name are not given, the default value will be used i.e. The image will be saved as "/tmp/lv.bosboot"
    type: str
    default: 'lv.bosboot'
  table_entry:
    description:
    - Specifies which boot pointer table entry to update.
    - C(primary) Specifies the table entry that was most recently used.
    - C(standby) Specifies the table entry that was not most recently used.
    - C(both) Specifies both boot pointer table entries.
    type: str
    choices: [ primary, standby, both ]
  increase_space:
    description:
    - Takes user permession to increase the file space.
    type: bool
    default: False

notes:
  - You can refer to the IBM documentation for additional information on the bosboot command at
    U(https://www.ibm.com/docs/en/aix/7.2?topic=b-bosboot-command),
    U(https://www.ibm.com/docs/en/aix/7.2?topic=c-chfs-command)
'''

EXAMPLES = r'''
- name: Only Verify
  bosboot:
    only_verify: true
    disk_device: "hd5"
    prototype_file: "usr/lib/boot/chrp.cd.proto"
- name: Table Entry
  bosboot:
    only_verify: true
    table_entry: primary
    prototype_file: "usr/lib/boot/chrp.cd.proto"
- name: Create Image
  bosboot:
    increase_space: true
    disk_device: "hd5"
    prototype_file: "usr/lib/boot/chrp.cd.proto"
    table_entry: "both"
    directory: "/tmp"
    image_name: "New_Boot_Image"
    create_image: true
'''

RETURN = r'''
msg:
  description: The execution message.
  returned: always
  type: str
stdout:
  description: The standard output.
  returned: If the command failed.
  type: str
stderr:
  description: The standard error.
  returned: If the command failed.
  type: str
'''


from ansible.module_utils.basic import AnsibleModule
__metaclass__ = type


module = None
results = None


def validate_disk_device(disk_device):
    """
    Checks if the provided disk device is in the map or not.
    param disk_device: Disk device name
    returns:
        1 - If the provided disk device is valid.
        0 - If the provided disk device is not valid.
    """
    cmd = "/usr/sbin/lsvg -m rootvg"
    rc, stdout, stderr = module.run_command(cmd)

    # To check if the disk device was validated.

    if rc:
        results['msg'] += "Could not validate the disk device."
        results['cmd'] = cmd
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)

    if disk_device in stdout:
        return 1
    return 0


def validate_space(module):
    """
    Checks if the space is enough for the bosboot image to be created in the required directories.
    param module: Ansible module argument spec.
    returns: Nothing
    """
    req_space = determine_required_space(module)

    # key represents directory and value represents space

    for key, val in req_space.items():
        cmd = "/usr/bin/df -m "
        cmd += key
        rc, stdout, stderr = module.run_command(cmd)
        stdout_lines = stdout.split("\n")[1:]

        # To Check if the space was validated.

        if rc:
            results['msg'] += "Could not validate space."
            results['cmd'] = cmd
            results['stdout'] = stdout
            results['stderr'] = stderr
            module.fail_json(**results)
        present_space = 0
        current_line = stdout_lines[1].split("\t")
        count = 0
        for space in current_line[1:]:
            if space != "" and count == 1:
                present_space = int(space)
                break
            if space != "":
                count += 1

        # If required space is less than the present space and user
        # has set the value of increase_space
        # attribute to true, increase_disk_space function is called
        # to increase the disk.

        if present_space < val:
            if module.params['increase_space']:
                increase_disk_space(val - present_space + 1, key)
            else:
                results['msg'] += "Not enought space in the " + key + " directory"
                results['cmd'] = cmd
                results['stdout'] = stdout
                results['stderr'] = stderr
                module.exit_json(**results)


def determine_required_space(module):
    """
    Determines the required space in various directories.
    param module: Ansible module argument spec.
    returns:
        file_systems - Dictionary containing information about space needed in various directories.
                     - It contains directory as keys and space required as values.
    """
    cmd = "/usr/sbin/bosboot -vq -b " + module.params['directory'] + "/"
    cmd += module.params['image_name']
    rc, stdout, stderr = module.run_command(cmd)
    stdout_lines = stdout.split("\n")

    # Check if the required space could be determined.

    if rc:
        results['msg'] += "Could not determine the required space."
        results['cmd'] = cmd
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)
    file_systems = {}
    for line in stdout_lines[1:]:
        line = line.split("\t")
        disk = line[0]
        space = None
        for space in line[2:]:
            if space != "":
                file_systems[disk] = int(space) // 1000
                break
    return file_systems


def increase_disk_space(req_space, dir):
    """
    Increases the disk space
    param req_space: Extra space that is required to perform some task.
    param dir: The directory for which space needs to be increased.
    returns: Nothing (Doesn't return anything)
    """
    cmd = "/usr/sbin/chfs -a size=+" + str(req_space + 100) + "M " + dir
    rc, stdout, stderr = module.run_command(cmd)

    # Check if the space was increased.

    if rc:
        results['msg'] += "Failed to increase the size of " + dir
        results['cmd'] = cmd
        results['stdout'] = stdout
        results['stderr'] = stderr
        module.fail_json(**results)
    results['changed'] = True
    results['msg'] += "Space for " + dir + " increased successfully "


def check_existing_image(location):
    """
    Checks if the image already exists in the user given location.
    param location: The location which needs to be checked for the pre-existence of the boot image.
    returns: Nothing (Doesn't return anything)
    """
    cmd = "ls " + location
    rc, stdout, stderr = module.run_command(cmd)

    if not rc:
        results['msg'] += "The Bosboot Image already exists, "
        results['msg'] += "Change the image name or the directory and try again."
        results['cmd'] = cmd
        results['stdout'] = stdout
        results['stderr'] = stderr
        results['changed'] = False
        module.exit_json(**results)


def verify(module):
    """
    Only verifies if the boot image can be created with the user given inputs(attributes).
    param module: Ansible module argument spec.
    returns: Nothing (Doesn't return anything)
    """
    cmd = "/usr/sbin/bosboot -v"

    # Adding the user provided attributes to the command.

    if module.params['disk_device']:
        cmd += " -d " + module.params['disk_device']
    if module.params['prototype_file']:
        cmd += " -p " + module.params['prototype_file']
    if module.params['table_entry']:
        cmd += " -M " + module.params['table_entry']

    location = module.params['directory'] + "/" + module.params['image_name']
    cmd += " -b " + location

    rc, stdout, stderr = module.run_command(cmd)

    results['cmd'] = cmd
    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc:
        results['msg'] += "Failed to verify, check stderr for details."
        module.fail_json(**results)
    results['msg'] += "Verified successfully !!"


def create_image(module):
    """
    Creates the boot image using the user given inputs(attributes).
    param module: Ansible module argument spec.
    returns: Nothing (Doesn't return anything)
    """

    validate_space(module)

    location = module.params['directory'] + "/" + module.params['image_name']

    check_existing_image(location)

    cmd = "/usr/sbin/bosboot -a"

    # Adding the user provided attributes to the command.

    if module.params['disk_device']:
        cmd += " -d " + module.params['disk_device']

    if module.params['prototype_file']:
        cmd += " -p " + module.params['prototype_file']

    cmd += " -b " + location

    if module.params['table_entry']:
        cmd += " -M " + module.params['table_entry']

    rc, stdout, stderr = module.run_command(cmd)

    # Check if the command ran successfully.

    results['cmd'] = cmd
    results['stdout'] = stdout
    results['stderr'] = stderr

    if rc:
        results['msg'] += "Could not run the command: " + cmd
        results['msg'] += "   Location  :   " + location
        module.fail_json(**results)
    results['msg'] += "The Image has been created successfully !!"
    results['changed'] = True


def main():
    global module
    global results

    module = AnsibleModule(
        supports_check_mode=True,

        argument_spec=dict(
            disk_device=dict(type='str', default='hd5'),
            prototype_file=dict(type='str'),
            only_verify=dict(type='bool', default=False),
            create_image=dict(type='bool', default=False),
            directory=dict(type='str', default='/tmp'),
            image_name=dict(type='str', default='lv.bosboot'),
            table_entry=dict(type='str', choices=['primary', 'standby', 'both']),
            increase_space=dict(type='bool', default=False),
        ),
    )

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    # Check for verifying if the prototype file is given along with disk device value or not.

    if module.params['prototype_file'] and not module.params['disk_device']:
        results['msg'] = "disk_device attribute is not given, while prototype_file is given"
        module.fail_json(**results)

    # Check for verifying that both the create_image and only_verify are not set at the same time.

    if (module.params['create_image'] and module.params['only_verify']) or\
            (not module.params['create_image'] and not module.params['only_verify']):
        results['msg'] = "create_image and only_verify attribute can not have same boolean value"
        module.fail_json(**results)

    # Check if the provided disk device is valid or not.

    if not validate_disk_device(module.params['disk_device']):
        results['msg'] = "The provided disk device " + module.params['disk_device']
        results['msg'] += " doesn't exist in the machine."
        module.fail_json(**results)

    if module.params['create_image']:
        create_image(module)
    else:
        verify(module)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
