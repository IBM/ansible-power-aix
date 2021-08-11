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
module: devices
short_description: Devices management.
description:
- Configures, modifies and unconfigures devices of a logical partition (LPAR).
- This module allows to configure a specified device or all devices in defined state. It can change
  attributes of a device in 'Defined/Available' state. At last it can unconfigure or stop a device
  in 'Available' state.
version_added: '2.9'
requirements:
- AIX
- Python >= 2.7
- 'Privileged user with authorizations:
  B(aix.device.manage.change,aix.device.manage.remove,aix.device.config)'
options:
  attributes:
    description:
    - When I(state=available), specifies the device attribute-value pairs used
      for changing specific attribute values.
    type: dict
  device:
    description:
    - Specifies the device logical name in the Customized Devices object class.
    - C(all) specifies to configure all devices when I(state=available).
    type: str
    default: all
  force:
    description:
    - Forces the change/unconfigure operation to take place on a locked device.
    type: bool
    default: false
  recursive:
    description:
    - Specifies to unconfigure the device and its children recursively.
    type: bool
    default: false
  state:
    description:
    - Specifies the desired state of the device.
    - C(available) (alias C(present)) configures device when its state is 'defined', otherwise it changes the device
      attributes.
    - C(defined) unconfigures/stops the device when its state is 'available', otherwise it changes
      the device attributes.
    - C(removed) (alias C(absent)) removes the device definition of unconfigured device in Customized Devices object class
    type: str
    choices: [ available, defined, removed ]
    default: available
  chtype:
    description:
    - Specifies the change type that is when the change should take place.
    - C(reboot) changes the device at system reboot.
    - C(current) changes the current state of the device temporarily. Not persistent after a reboot.
      The device will not be reset. (Not all devices supports this feature)
    - C(both) changes both the current state of the device and the device database. Persistent after
      a reboot. The device will not be reset. (Not all devices support this feature)
    - C(reset) changes both the current state of the device and the device database. Persistent after
      a reboot. The device will be reset.
    type: str
    choices: [ reboot, current, both, reset ]
    default: both
  parent_device:
    description:
    - While modifying device, specifies the parent device of the device to be updated.
      For unconfigure/stop operation, specifies the parent device whose children need to be
      unconfigured recursively.
    type: str
  rmtype:
    description:
    - Specifies whether to unconfigure/stop the device.
    - C(unconfigure) changes are applied to the device when the system is rebooted.
    - C(stop) changes the current state of the device temporarily.
    type: str
    choices: [ unconfigure, stop ]
    default: unconfigure
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/cfgmgr.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/c_commands/chdev.html),
    U(https://www.ibm.com/support/knowledgecenter/ssw_aix_72/r_commands/rmdev.html),
'''

EXAMPLES = r'''
- name: Configure a device
  devices:
    device: proc0
    state: available

- name: Unconfigure a device
  devices:
    device: proc0
    state: defined

- name: Remove (delete) fcs0 device and children
  devices:
    device: fcs0
    state: removed
    recursive: 'true'

- name: Put fcs0 device and children in defined state
  devices:
    device: fcs0
    state: defined
    recursive: 'true'

- name: Put the children of device fcs0 in defined state
  devices:
    parent_device: fcs0
    state: defined

- name: Remove (delete) ent0 device
  devices:
    device: ent0
    state: absent
    recursive: 'true'

- name: Change en0 MTU speed and disable arp
  devices:
    device: en0
    state: available
    attributes:
      mtu: 900
      arp: 'off'

- name: Configure the IP address, netmask and bring en0 up
  devices:
    device: en0
    state: available
    attributes:
      netaddr: 192.168.0.1
      netmask: 255.255.255.0
      state: 'up'

- name: Modify Crypt0 device max_requests (Crypt0 does not support changes while available)
  devices:
    device: Crypt0
    attributes:
      max_requests:32
    chtype: 'reset'

- name: Discover new devices (configure all devices)
  devices:
    device: "all"
    state: available
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
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

from ansible.module_utils.basic import AnsibleModule

results = None

def get_device_state(module, device):
    """
    Determines the current state of device.
    param module: Ansible module argument spec.
    param device: device name.
    return: True - device in available state / False - device in defined state /
             None - device does not exist
    """
    cmd = "lsdev -l %s" % device

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Command '%s' failed." % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    if stdout:
        device_state = stdout.split()[1]

        if device_state == 'Available':
            # Device is in Available state
            return True
        else:
            # Device is in Defined state
            return False

    return None


def get_device_attributes(module, device):
    """
    Fetches the current attributes from a device.
    param name: device name
    return: standard output of lsatter -El <device> command.
    """
    global results

    results = dict(
        changed=False,
        msg='',
        stdout='',
        stderr='',
    )

    cmd = "lsattr -El  %s" % device
    rc, stdout, stderr = module.run_command(cmd)
    results['cmd'] = cmd
    results['rc'] = rc
    results['stdout'] = stdout
    results['stderr'] = stderr
    if rc != 0:
        results['msg'] = "Failed to fetch attributes from device %s. \
                        Command '%s' failed." % (device, cmd)
        module.fail_json(**results)
    return stdout


def chdev(module, device):
    """
    Changes the attributes of the device.
    param module: Ansible module argument spec.
    param device: Volume Group name.
    return: changed - True/False(device state modified or not),
            msg - message
    """
    attributes = module.params["attributes"]
    force = module.params["force"]
    chtype = module.params["chtype"]
    parent_device = module.params["parent_device"]

    ''' get initial properties of the device before
    attempting to modfiy it. '''
    init_props = get_device_attributes(module, device)

    opts = ""

    if parent_device:
        opts += "-p %s " % parent_device

    if attributes:
        opts += "-a '"
        for attr, val in attributes.items():
            opts += "%s=%s " % (attr, val)
        opts += "' "

    if not opts:
        msg = "No changes specified for the device '%s'" % device
        return False, msg
    else:
        if force:
            opts += "-g "

        chtype_opt = {
            "both": '-U ',
            "current": '-T ',
            "reboot": '-P ',
            "reset": '',
        }

        opts += chtype_opt[chtype]

        cmd = "%s %s -l %s" % ("chdev", opts, device)
        rc, stdout, stderr = module.run_command(cmd)
        if rc != 0:
            msg = "Modification of Device attributes failed for device '%s'. cmd - '%s'" % (device, cmd)
            module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)


    if init_props != get_device_attributes(module, device):
        msg = "Modification of Device attributes completed for device '%s'" % device
        rc = True
    else:
        msg = "Nothing was modified for device '%s'" % device
        rc = False

    return rc, msg


def cfgdev(module, device):
    """
    Configure the device or discover all devices (device=all)
    param module: Ansible module argument spec.
    param device: device name.
    return: changed - True/False(device state modified or not),
            msg - message
    """
    current_state = 'None'
    cmd = "cfgmgr "
    if device != 'all':
        current_state = get_device_state(module, device)
        if current_state is True:
            msg = "Device %s is already in Available state." % device
            return False, msg

        if current_state is None:
              msg = "Device %s does not exist." % device
              module.fail_json(msg=msg)

        cmd += "-l %s " % device

    rc, out, err = module.run_command(cmd)

    if rc != 0:
        msg = "Device configuration failed for '%s'." % device
        module.fail_json(msg=msg, rc=rc, stdout=out, stderr=err)

    msg = "Device configuration completed for '%s'." % device
    return True, msg


def rmdev(module, device, state):
    """
    Unconfigure/stop the device when state is 'defined'
    Removes the device definition in Customized Devices object class when state is 'removed'
    param module: Ansible module argument spec.
    param device: device name.
    param state: state of the device
    return: changed - True/False(device state modified or not or device definition is removed or not),
            msg - message
    """
    parent_device = module.params["parent_device"]
    force = module.params["force"]
    recursive = module.params["recursive"]
    rmtype = module.params["rmtype"]
    current_state = None
    opts = ""

    if device != 'all':
        current_state = get_device_state(module, device)
        if current_state is None:
            msg = "Device %s does not exist." % device
            return False, msg

    if force:
        opts += "-g "
    if recursive:
        opts += "-R "

    if state == 'removed':
        if device == 'all' or device == 'none':
            msg = "Please provide the name of the device."
            module.fail_json(msg=msg)
        else:

            opts += "-d -l %s" % device
            cmd = "rmdev %s" % opts
            rc, stdout, stderr = module.run_command(cmd)
            if rc != 0:
                msg = "Operation to remove definition for device %s failed. cmd - '%s'" % (device, cmd)
                module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

            msg = "Successfully removed definition in Customized Devices object class for device %s" % device
            return True, msg

    if device == 'all':
        device = None

    # If the device is already defined, do nothing.
    if device is not None:
      if ( state == 'defined' ) and ( current_state == False):
          msg = "Device %s is already in defined state." % device
          return False, msg



    rmtype_opt = {
        "unconfigure": '',
        "stop": '-S ',
    }

    if rmtype:
        opts += rmtype_opt[rmtype]

    if parent_device:
        opts += "-p %s " % parent_device
    if device:
        opts += "-l %s " % device

    cmd = "rmdev %s" % opts
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        if device is not None:
            msg = "Operation '%s' for device %s failed. cmd - '%s'" % (rmtype, device, cmd)
        else:
            msg = "Operation '%s' for children of parent device '%s' failed. cmd - '%s'" % (rmtype, parent_device, cmd)
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    if device:
        msg = "Operation '%s' for device '%s' completed." % (rmtype, device)
    else:
        msg = "Operation '%s' for children of parent device '%s' completed." % (rmtype, parent_device)
    return True, msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            attributes=dict(type='dict'),
            device=dict(type='str', default='all'),
            force=dict(type='bool', default=False),
            recursive=dict(type='bool', default=False),
            state=dict(type='str', default='available', choices=['available', 'defined', 'removed', 'present', 'absent']),
            chtype=dict(type='str', default='both', choices=['reboot', 'current', 'both', 'reset']),
            parent_device=dict(type='str'),
            rmtype=dict(type='str', default='unconfigure', choices=['unconfigure', 'stop']),
        ),
    )

    changed = False
    device = module.params["device"]
    state = module.params["state"]
    if state == 'present':
       state = 'available'
    if state == 'absent':
      state = 'removed'

    attributes = module.params["attributes"]
    msg = ""


    if attributes:
        # Modify Device attributes.
        changed, msg = chdev(module, device)

    elif state == 'available':
        # Configure Device
        changed, msg = cfgdev(module, device)


    elif ( state == 'defined' ) or ( state == 'removed' ):
        # Move the device from 'available' to 'defined' state or delete the device
        changed, msg = rmdev(module, device, state)

    else:
        changed = False
        msg = "Invalid state '%s'" % current_state

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
