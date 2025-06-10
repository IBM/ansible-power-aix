#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function

__metaclass__ = type

ANSIBLE_METADATA = {
    "metadata_version": "1.1",
    "status": ["preview"],
    "supported_by": "community",
}

DOCUMENTATION = r"""
---
author:
- AIX Development Team (@schamola)
module: nmon
short_description: Health Monitoring
description:
- This module allows to record local system statistics of a logical partition (LPAR).
version_added: '2.1.0'
requirements:
- AIX
- Python >= 3.6
- 'Privileged user with authorizations'
options:
  filename:
    description:
    - Specifies that the output is in spreadsheet format and the name of the output file
      is I(filename)
    type: str
  file_containing_disk_groups:
    description:
    - Specifies the file that contains the user-defined disk groups.
    - Each line in the file begins with a group name. The list of disks follows the group name and is separated with spaces.
    - A disk can belong to various disk groups, the file can contain a maximum of 64 disk groups
    type: str
  disklist:
    description:
    - Specifies a list of disks to be recorded.
    type: list
    elements: str
  save_to_dir:
    description:
    - Changes the directory before the command saves the data to a file.
    type: str
  disks_per_line:
    description:
    - Specifies the number of disks to list on each line.
    type: int
  timestamp_size:
    description:
    - Specifies the size of timestamp (Tnnnn) to be recorded.
    - The timestamp is recorded in the .csv file.
    - The value of the number parameter ranges from 4 through 16, for NMON analyzer, use the values 4 or 8.
    type: int
  percentage_of_process_threshold:
    description:
    - Specifies the percentage of process threshold at which the command ignores the TOP processes statistics.
    - The default percentage is 0.1.
    - The command does not save the TOP processes statistics if the process is using less processor than the specified percentage.
    type: int
  priority:
    description:
    - Specifies the priority of the nmon command that is running.
    - A value of -20 means important. A value of 20 means not important.
    - Only root user can specify a negative value.
    type: int
  runname:
    description:
    - Specifies the value for the runname field written to the spreadsheet file.
    - By default, the value is the hostname.
    type: str
  interval_seconds:
    description:
    - Specifies the interval in seconds between 2 consecutive recording snapshots.
    type: int
  output_path:
    description:
    - Specifies the file name or directory to which the recorded file is to be stored.
    type: str
  include_async:
    description:
    - Includes the Asynchronous I/O section in the view.
    type: bool
    default: false
  number_of_snapshots:
    description:
    - Specifies the number snapshots that must be taken by the command.
    - The default value is 10000000 for the NMON command.
    type: int
  include_disk_service_time:
    description:
    - Includes the Disk Service Time section in the view.
    type: bool
    default: false
  skip_disk_config:
    description:
    - Skips the Disk Configuration section.
    type: bool
    default: false
  skip_ess_config:
    description:
    - Skips the ESS Configuration section.
    type: bool
    default: false
  spreadsheet_output:
    description:
    - Specifies that the output is in spreadsheet format.
    - By default, the command takes 288 snapshots of system data with an interval of 300 seconds between each snapshot.
    - The name of the output file is in the format of hostname_YYMMDD_HHMM.nmon.
    type: bool
    default: false
  use_greenwhich_time:
    description:
    - Uses Greenwich mean time (GMT) instead of local time.
    - This method is helpful when you compare nmon files from many LPAR of 1
      system for processor view but the LPAR are in different time zones.
    type: bool
    default: false
  report_thread_level_stats:
    description:
    - Reports thread level statistics.
    type: bool
    default: false
  skip_JFS_section:
    description:
    - Skips the JFS section.
    type: bool
    default: false
  include_raw_kernal_section:
    description:
    - Includes the RAW Kernel section and the LPAR section in the recording file.
    - If set, it dumps the raw numbers of the corresponding data structure.
    - The memory dump is readable and can be used when the command is recording the data.
    type: bool
    default: false
  include_large_page_analysis:
    description:
    - Includes the large page analysis section.
    type: bool
    default: false
  include_mempages_section:
    description:
    - Includes the MEMPAGES section in the recording file.
    - The MEMPAGES section displays detailed memory statistics per page size.
    type: bool
    default: false
  include_nfs_section:
    description:
    - Includes the NFS section in the recording file
    type: bool
    default: false
  include_nfsv4_section:
    description:
    - Includes the NFSv4 section in the recording file
    type: bool
    default: false
  include_sea_vios_section:
    description:
    - Includes the Shared Ethernet adapter (SEA) VIOS sections in the recording file.
    type: bool
    default: false
  include_paging_space_section:
    description:
    - Includes the Paging Space section in the recording file.
    type: bool
    default: false
  include_wlm_section_with_subclasses:
    description:
    - Includes WLM sections with subclasses in the recording file.
    type: bool
    default: false
  include_top_processes:
    description:
    - Includes the top processes in the output.
    type: bool
    default: false
  include_top_processes_and_save_cli_agrs:
    description:
    - Includes the top processes in the output and saves the command-line arguments
      into the UARG section.
    type: bool
    default: false
  include_disk_vg_section:
    description:
    - Includes disk volume group section.
    type: bool
    default: false
  include_wlm_section:
    description:
    - Includes the WLM sections into the recording file.
    type: bool
    default: false
  sensible_recording_for_one_day:
    description:
    - Specifies the sensible spreadsheet recording for duration of 1 day for capacity planning.
    - By default, the recording is done every 900 seconds for 96 times.
    - This flag is equivalent to -ft -s 900 -c 96.
    type: bool
    default: false
  sensible_recording_for_one_hr:
    description:
    - Specifies the sensible spreadsheet recording for duration of 1 hour for capacity planning.
    - By default, the recording is done every 30 seconds for 120 times.
    - This flag is equivalent to -ft -s 30 -c 120.
    type: bool
    default: false
  scpu_details:
    description:
    - Enables or disables recording of Scaled CPU (SCPU) sections, which are nothing but metrics that start with SCPU.
    - These metrics are based on Scaled Processor Utilization of Resources Register (SPURR).
    type: str
    choices: ['on','off']
  pcpu_details:
    description:
    - Enables or disables recording of Physical CPU (PCPU) sections, which are nothing but metrics that start with PCPU.
    - These metrics are based on Processor Utilization of Resources Register (PURR).
    type: str
    choices: ['on','off']
  include_top_processes_with_commands:
    description:
    - Includes the top process in the recording with all of the commands of the same name that are added and recorded.
    type: bool
    default: false
  sensible_recording_one_day_without_top:
    description:
    - Specifies the sensible spreadsheet recording for duration of 1day for capacity planning.
    - By default, the recording is done every 900 seconds for 96 times. This flag is equivalent to -f -s 900 -c 96.
    type: bool
    default: false
  include_fibre_channel_section:
    description:
    - Includes the Fibre Channel (FC) sections.
    type: bool
    default: false
  restrict_commands_in_listing:
    description:
    - Restricts the process that are listed
    type: list
    elements: str
  delete_previous:
    description:
    - Deletes previous nmon files with the same name before creating the new one.
    type: bool
    default: false
notes:
  - You can refer to the IBM documentation for additional information on the commands used at
    U(https://www.ibm.com/docs/en/aix/7.3?topic=n-nmon-command),
"""

EXAMPLES = r"""
- name: Generate the nmon recording in the current directory for two hours, capturing data every 30 seconds
  ibm.power_aix.nmon:
    spreadsheet_output: true
    interval_seconds: 30
    number_of_snapshots: 240
    output_path: /nmonfiles/

- name: Generate nmon recording that includes raw kernal section
  ibm.power_aix.nmon:
    spreadsheet_output: true
    interval_seconds: 30
    number_of_snapshots: 2
    include_raw_kernal_section: true
    output_path: /nmonfiles/kernal_data

- name: Generate nmon recording that includes live page analysis
  ibm.power_aix.nmon:
    spreadsheet_output: true
    interval_seconds: 30
    number_of_snapshots: 4
    include_large_page_analysis: true
    output_path: /nmonfiles/livepage_data

- name: Generate nmon recording that includes nfsv4 section in the recording mode
  ibm.power_aix.nmon:
    spreadsheet_output: true
    interval_seconds: 30
    number_of_snapshots: 2
    include_nfsv4_section: true
    output_path: /nmonfiles/nfsv4_data
"""

RETURN = r"""
msg:
    description: The execution message.
    returned: always
    type: str
rc:
    description: The return code.
    returned: always
    type: int
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
changed:
    description: Tells whether any change occured on the system
    returned: always
    type: bool
"""
import os
import glob

from ansible.module_utils.basic import AnsibleModule

results = dict(
    changed=False,
    rc=0,
    msg="",
    stdout="",
    stderr="",
)


def run_nmon(module):
    """
    Generates and runs the nmon command with specified attributes.
    arguments:
        module (dict) - Ansible generic module.
    returns:
        success_msg (str) - Success message if the command runs successfully, otherwise ends up failing.
    """

    f_name = module.params["filename"]
    sp_op = module.params["spreadsheet_output"]
    sensible_rec_one_day = module.params["sensible_recording_for_one_day"]
    sensible_rec_one_hr = module.params["sensible_recording_for_one_hr"]
    sensible_rec_one_day_no_top = module.params[
        "sensible_recording_one_day_without_top"
    ]

    # In recording mode, one of the following should be included -f, -F, -x , -X, -z
    if (
        not f_name
        and not sp_op
        and not sensible_rec_one_day
        and not sensible_rec_one_hr
        and not sensible_rec_one_day_no_top
    ):
        fail_msg = """Need to provide one of the following: ['filename', 'spreadsheet_output', 'sensible_recording_for_one_day',
            'sensible_recording_for_one_hr', 'sensible_recording_one_day_without_top'] in case of recording mode."""
        module.fail_json(msg=fail_msg)

    # Fail, if the provided directory doesn't exist
    if module.params["save_to_dir"]:
        op_path = module.params["save_to_dir"]

        if not os.path.exists(op_path):
            results["msg"] = (
                "The provided directory does not exist, please check and re-run."
            )
            module.fail_json(**results)

    # Check if the file already exists on the system.
    # If it exists, either delete it or fail as per the provided attributes.
    if module.params["output_path"]:
        op_path = module.params["output_path"]

        # If it's a directory, check for it's existence
        if os.path.isdir(op_path):
            if not os.path.exists(op_path):
                results["msg"] = (
                    "The provided directory does not exist, please check and re-run."
                )
                module.fail_json(**results)
        else:
            # Get the folder path from the provided output path
            folder_path = "/"
            if "/" in op_path:
                folder_path += "/" + "/".join(op_path.split("/")[:-1])

            # Check if there are any previous files with same prefix
            pattern = os.path.join(folder_path, f"{op_path}*")
            matching_files = glob.glob(pattern)

            if matching_files:
                if not module.params["delete_previous"]:
                    results["msg"] = (
                        f"The file(s) ({op_path}) are already present in the provided location,"
                    )
                    results[
                        "msg"
                    ] += " please remove them or set 'delete_previous' to True, and re-run."
                    module.fail_json(**results)
                else:
                    for file_path in matching_files:
                        os.remove(file_path)

    # Basic nmon command
    cmd = ["/usr/bin/nmon"]

    # Adding flags as per the requirements
    if sp_op:
        cmd.append(" -f")

    if f_name:
        cmd.append(f" -F {f_name}")

    if sensible_rec_one_day:
        cmd.append(" -x")

    if sensible_rec_one_hr:
        cmd.append(" -X")

    if sensible_rec_one_day_no_top:
        cmd.append(" -z")

    if module.params["file_containing_disk_groups"]:
        cmd.append(f" -g {module.params['file_containing_disk_groups']}")

    if module.params["disklist"]:
        d_list = ",".join(module.params["disklist"])
        cmd.append(f" -k {d_list}")

    if module.params["save_to_dir"]:
        cmd.append(f" -m {module.params['save_to_dir']}")

    if module.params["disks_per_line"]:
        cmd.append(f" -l {module.params['disks_per_line']}")

    if module.params["timestamp_size"]:
        t_size = module.params["timestamp_size"]
        if t_size < 4 or t_size > 16:
            results["msg"] = (
                f"Value of timestamp_size should be between 4-16. Provided value - {t_size}"
            )
            module.fail_json(**results)

        cmd.append(f" -w {module.params['timestamp_size']}")

    if module.params["percentage_of_process_threshold"]:
        cmd.append(f" -I {module.params['percentage_of_process_threshold']}")

    if module.params["priority"]:
        cmd.append(f" -Z {module.params['priority']}")

    if module.params["runname"]:
        cmd.append(f" -r {module.params['runname']}")

    if module.params["interval_seconds"]:
        cmd.append(f" -s {module.params['interval_seconds']}")

    if module.params["output_path"]:
        cmd.append(f" -o {module.params['output_path']}")

    if module.params["restrict_commands_in_listing"]:
        cmd_list = ":".join(module.params["restrict_commands_in_listing"])
        cmd.append(f" -C {cmd_list}")

    if module.params["include_async"]:
        cmd.append(" -A")

    if module.params["number_of_snapshots"]:
        cmd.append(f" -c {module.params['number_of_snapshots']}")

    if module.params["include_disk_service_time"]:
        cmd.append(" -d")

    if module.params["skip_disk_config"]:
        cmd.append(" -D")

    if module.params["skip_ess_config"]:
        cmd.append(" -E")

    if module.params["use_greenwhich_time"]:
        cmd.append(" -G")

    if module.params["report_thread_level_stats"]:
        cmd.append(" -i")

    if module.params["skip_JFS_section"]:
        cmd.append(" -J")

    if module.params["include_raw_kernal_section"]:
        cmd.append(" -K")

    if module.params["include_large_page_analysis"]:
        cmd.append(" -L")

    if module.params["include_mempages_section"]:
        cmd.append(" -M")

    if module.params["include_nfs_section"]:
        cmd.append(" -N")

    if module.params["include_nfsv4_section"]:
        cmd.append(" -NN")

    if module.params["include_sea_vios_section"]:
        cmd.append(" -O")

    if module.params["include_paging_space_section"]:
        cmd.append(" -P")

    if module.params["include_wlm_section_with_subclasses"]:
        cmd.append(" -S")

    if module.params["include_top_processes"]:
        cmd.append(" -t")

    if module.params["include_top_processes_and_save_cli_agrs"]:
        cmd.append(" -T")

    if module.params["include_disk_vg_section"]:
        cmd.append(" -V")

    if module.params["include_wlm_section"]:
        cmd.append(" -W")

    if module.params["scpu_details"]:
        cmd.append(f" -y SCPU={module.params['scpu_details']}")

    if module.params["pcpu_details"]:
        cmd.append(f" -y PCPU={module.params['pcpu_details']}")

    if module.params["include_top_processes_with_commands"]:
        cmd.append(" -Y")

    if module.params["include_fibre_channel_section"]:
        cmd.append(" -^")

    # Run the generated command
    rc, stdout, stderr = module.run_command(cmd)

    joined_cmd = "".join(cmd)

    fail_msg = f"Following command failed: {joined_cmd} ; Please see stderr for more information."
    success_msg = f"Successfully ran the following command: {joined_cmd}"

    if rc:
        results["rc"] = rc
        results["msg"] = fail_msg
        results["stdout"] = stdout
        results["stderr"] = stderr
        module.fail_json(**results)

    return success_msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            filename=dict(type="str"),
            file_containing_disk_groups=dict(type="str"),
            disklist=dict(type="list", elements="str"),
            save_to_dir=dict(type="str"),
            disks_per_line=dict(type="int"),
            timestamp_size=dict(type="int"),
            percentage_of_process_threshold=dict(type="int"),
            priority=dict(type="int"),
            runname=dict(type="str"),
            interval_seconds=dict(type="int"),
            output_path=dict(type="str"),
            include_async=dict(type="bool", default=False),
            number_of_snapshots=dict(type="int"),
            include_disk_service_time=dict(type="bool", default=False),
            skip_disk_config=dict(type="bool", default=False),
            skip_ess_config=dict(type="bool", default=False),
            spreadsheet_output=dict(type="bool", default=False),
            use_greenwhich_time=dict(type="bool", default=False),
            report_thread_level_stats=dict(type="bool", default=False),
            skip_JFS_section=dict(type="bool", default=False),
            include_raw_kernal_section=dict(type="bool", default=False),
            include_large_page_analysis=dict(type="bool", default=False),
            include_mempages_section=dict(type="bool", default=False),
            include_nfs_section=dict(type="bool", default=False),
            include_nfsv4_section=dict(type="bool", default=False),
            include_sea_vios_section=dict(type="bool", default=False),
            include_paging_space_section=dict(type="bool", default=False),
            include_wlm_section_with_subclasses=dict(type="bool", default=False),
            include_top_processes=dict(type="bool", default=False),
            include_top_processes_and_save_cli_agrs=dict(type="bool", default=False),
            include_disk_vg_section=dict(type="bool", default=False),
            include_wlm_section=dict(type="bool", default=False),
            sensible_recording_for_one_day=dict(type="bool", default=False),
            sensible_recording_for_one_hr=dict(type="bool", default=False),
            scpu_details=dict(type="str", choices=["on", "off"]),
            pcpu_details=dict(type="str", choices=["on", "off"]),
            include_top_processes_with_commands=dict(type="bool", default=False),
            sensible_recording_one_day_without_top=dict(type="bool", default=False),
            include_fibre_channel_section=dict(type="bool", default=False),
            restrict_commands_in_listing=dict(type="list", elements="str"),
            delete_previous=dict(type="bool", default=False),
        ),
        mutually_exclusive=[
            [
                "filename",
                "spreadsheet_output",
                "sensible_recording_for_one_day",
                "sensible_recording_for_one_hr",
                "sensible_recording_one_day_without_top",
            ],
            [
                "include_top_processes_and_save_cli_agrs",
                "include_top_processes",
                "include_top_processes_with_commands",
            ],
        ],
    )

    results["msg"] = run_nmon(module)

    # Changed should be set to true as the command generates and saves the file on the system
    results["changed"] = True

    module.exit_json(**results)


if __name__ == "__main__":
    main()
