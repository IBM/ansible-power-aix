# ansible-power-aix

## Scope

###Developer contributions for Ansible Automation on Power (AIX)

# AIX for Ansible

## Requirements

### Platforms

- AIX 6.1
- AIX 7.1
- AIX 7.2

### Ansible

- Requires Ansible 2.0 or newer

## Resources

### NIM_SUMA

Creates a task to automate the download of technology levels (TL) and service packs (SP) from a fix server.

Must be described in yaml format with the follwoing parameters:

```yaml
    nim_suma:
      oslevel:  required; specifies the OS level to update to;
                "latest" indicates the latest level of the higher TL among
                the target; based on the fix server, nim_suma will determine
                the actual oslevel necessary to update the targets
                and create the corresponding NIM resource on the NIM server;
                xxxx-xx(-00-0000): sepcifies a TL;
                xxxx-xx-xx-xxxx or xxxx-xx-xx: specifies a SP.
      location: required; if it is an absolute path, specifies the directory where the
                packages will be downloaded on the NIM server;
                if it is a filename, specifies the lpp_source_name
      targets:  required; specifies the NIM clients to update;
                "foo*": all the NIM clients with name starting by "foo";
                "foo[2:4]": designates the NIM clients among foo2, foo3 and foo4;
                "*" or "ALL": all the NIM clients.
      action:   required; specifies to action to be performed;
                possible values: "download" to download all the fixes and create
                                 the associated NIM resources;
                              or "preview" to execute all the checks without
                                 downloading the fixes.
```

### NIM

Creates a task to update targets.

Must be described in yaml format with the following parameters:

```yaml
    nim:
      lpp_source: indicates the lpp_source to apply to the targets;
                  "latest_tl", "latest_sp", "next_tl" and "next_sp" can be specified;
                  based on the NIM server resources, nim will determine
                  the actual oslevel necessary to update the targets.
      targets:    specifies the NIM clients to update;
                  "foo*" designates all the NIM clients with name starting by "foo";
                  "foo[2:4]" designates the NIM clients among foo2, foo3 and foo4;
                  "*" or "ALL" designates all the NIM clients.
      async:      boolean;
                  if set to "False" (default), a NIM client will be completely
                  installed before starting the installation of another NIM client;
                  if "lpp_source" is set to "latest_xx" or "next_xx", this parameter
                  is set to "false".
      action:     required; specifies the action to perform;
                  possible values: "update", "check" or "reboot";
                  "update" performs an updates of the targets;
                           requires "lpp_source" and "targets" to be specified;
                  "check" displays the oslevel of the targets and their NIM status;
                          requires "targets" to be specified;
                  "reboot" reboots the targets. "targets" must be specified.

```

### NIM_FLRTVC

Creates a task to check targets vulnerability against available fixes, and apply them necessary fixes

Must be described in yaml format with the following parameters:

```yaml
    nim_flrtvc:
      targets:      required; specifies the NIM clients to update;
                    "foo*" designates all the NIM clients with name starting by "foo";
                    "foo[2:4]" designates the NIM clients among foo2, foo3 and foo4;
                    "*" or "ALL" designates all tne NIM clients.
      path:         Working directory used for temporary files;
                    it will contain FLRTVC reports;
                    if not specified "/tmp/ansible" is used.
      apar:         type of apar to check or download;
                    "sec" security fixes;
                    "hiper" corrections to High Impact PERvasive threats;
                    "all" default value; both "sec" fixes and "hiper" fixes.
     filesets:      only fixes on the filesets specified will be checked and updated.
     csv:           path to a file containing the description of the "sec" and "hiper" fixes;
                    this file is usually transferred form the fix server;
                    this rather big transfer can be avoided by specifying
                    an already transferred file.
     check_only:    boolean;
                    if set to "True", only checks if fixes are already applied
                    on the targets.
     download_only: boolean;
                    if set to "True", performs "check_only" and downloads the fixes
                    (no update of the targets).
     clean:         boolean;
                    if set to "True", remove the working directory at the end of execution;
                    (default "False")
     force:         boolean;
                    if set to "True", remove currently installed ifix before running flrtvc;
                    (default "False")

```

### UPDATEIOS

Updates the Virtual I/O Server.

Must be described in yaml format with the following parameters:

```yaml
    nim_updateios:
      targets:          required; a list of VIOS to act upon depending on the "action" specified;
                        to perform an update on dual VIOS, specify the list as a tuple
                        with the following format : "(gdrh9v1, gdrh9v2) (gdrh10v1, gdrh10v2)”;
                        to specify a single VIOS, use the following format : "(gdrh11v0)".
      lpp_source:       the resource that will provide the installation images;
                        required in case of "install".
      filesets:         a list of filesets to act upon on each of the targets
                        depending on the "action" specified.
      installp_bundle:  the resource that lists the filesets to act upon on each of the targets
                        depending on the "action" specified;
                        "filesets" and "installp_bundle" are mutually exclusive.
      accept_licenses:  specify whether the software licenses should be automatically accepted
                        during the installation;
                        default value: "yes".
      action:           required; the operation to perform on the VIOS;
                        possible values are : "install", "commit", "reject", "cleanup" and "remove";
                        "reject" is not supported by the latest version of updateios.
      preview:          specify that only a preview operation will be performed
                        (the action itself will not be performed);
                        default value: "yes".
      time_limit:       when this parameter is specified, before starting the updateios action
                        specified on a new VIOS in the "targets" list, the actual date is compared
                        to this parameter value; if it is greater then the task is stopped;
                        the format is mm/dd/yyyy hh:mm
      vios_status:      specify the result of previous operation. This allows to combine severals
                        tasks that depend on the result of previous operation.
      vars:             specify playbook's variables to use (log_file for example);
                        if myvars is the playbook hash, use vars: "{{ myvars }}"
      nim_node:         allows to pass along NIM node info from a task to another so that it
                        discovers NIM info only one time for all tasks;
                        if you use: "register: backup_result", you can specify the following
                        nim_node: "{{ backup_result.nim_node }}"
```

### VIOS HEALTH CHECK

Performs a health check of VIOS before updating.

Requires vioshc.py as a prerequisite.
vioshc.py is available on https://github.com/aixoss/vios-health-checker.

Must be described in yaml format with the following parameters:

```yaml
    nim_vios_hc:
      targets:          required; a list of VIOS to act upon depending on the "action" specified;
                        to perform a health check on dual VIOS, specify the list as a tuple
                        with the following format : "(gdrh9v1, gdrh9v2) (gdrh10v1, gdrh10v2)”;
                        to specify a single VIOS, use the following format : "(gdrh11v0)".
      action:           required; the operation to perform on the VIOS;
                        must be set to "health_check".
      vars:             specify playbook's variables to use (log_file for example);
                        if myvars is the playbook hash, use vars: "{{ myvars }}"

```

### ALTERNATE DISK COPY on a VIOS

Performs alternate disk copy on a VIOS (before update).

Must be described in yaml format with the following parameters:

```yaml
    nim_vios_alt_disk:
      targets:          required; a list of VIOS to act upon depending on the "action" specified;
                        use a tuple format with the 1st element the VIOS and the 2nd element
                        the disk used for the alternate disk copy;
                        for a dual VIOS, the format will look like : "(vios1,disk1,vios2,disk2)";
                        for a single VIOS, the format will look like : "(vios1,disk1)".
      action:           required; the operation to perform on the VIOS;
                        2 possible values : "alt_disk_copy" and "alt_disk_clean".
      disk_size_policy: specify how the choose the alternate disk if not specified;
                        4 possible values : "nearest" (default), "lower", "upper", "minimize".
      time_limit:       when this parameter is specified, before starting the altternate disk action
                        specified on a new VIOS in the "targets" list, the actual date is compared
                        to this parameter value; if it is greater then the task is stopped
                        the format is mm/dd/yyyy hh:mm
      force:            when set to "yes", any existing altinst_rootvg is cleaned before looking for
                        an alternate disk for the copy operation.
      vios_status:      specify the result of previous operation. This allows to combine severals
                        tasks that depend on the result of previous operation.
      vars:             specify playbook's variables to use (log_file for example);
                        if myvars is the playbook hash, use vars: "{{ myvars }}"
      nim_node:         allows to pass along NIM node info from a task to another so that it
                        discovers NIM info only one time for all tasks;
                        if you use: "register: backup_result", you can specify the following
                        nim_node: "{{ backup_result.nim_node }}"

```

### UPGRADEIOS

Upgrades the Virtual I/O Server using NIM and viosbr.

Must be described in yaml format with the following parameters:

```yaml
    nim_upgradeios:
      targets:             required; a list of VIOS to act upon depending on the "action" specified;
                           to perform an action on dual VIOS, specify the list as a tuple
                           with the following format : "(gdrh9v1, gdrh9v2) (gdrh10v1, gdrh10v2)”;
                           to specify a single VIOS, use the following format : "(gdrh11v0)".
      action:              required; the operation to perform on the VIOS;
                           possible values are : "backup", "view_backup", "upgrade_restore", "all".
      email:               email address to set in the NIM master's /etc/niminfo file if not already
                           set with: export NIM_MASTER_UID=<email@ddress>
      location:            existing directory to store the ios_backup on the NIM master;
                           required for if "action" is "backup".
      backup_prefix:       prefix of the ios_backup NIM resource; the name of the target VIOS is
                           added to this prefix;
                           default value: "ios_backup_<vios_name>".
      force:               when set to "yes", any existing ios_backup NIM resource for each target
                           is removed before performing the backup creation; supported for "backup"
                           action;
                           default value: "no".
      boot_client:         specify whether the clients of the target VIOS should be booted after the
                           upgrade and restore operation; can be used for "upgrade_restore" and
                           "all" actions;
                           default value: "no".
      resolv_conf:         specify the NIM resource to use for the VIOS installation;
                           required for "upgrade_restore" and "all" actions;
      spot_prefix:         prefix of the Shared product Object Tree (SPOT) NIM resource to use for
                           the VIOS installation; the NIM name of the target VIOS is added to find
                           the actual NIM resource, like: "<spot_prefix>_<vios_name>"; this resource
                           must exists prior the playbook execution;
                           required for "upgrade_restore" action;
      mksysb_prefix:       prefix of the mksysb NIM resource to use for the VIOS installation; the
                           NIM name of the target VIOS is added to this prefix to find the actual
                           NIM resource, like: "<mksysb_prefix>_<vios_name>";
                           this resource must exists prior the playbook execution;
                           required for "upgrade_restore" and "all" actions;
      bosinst_data_prefix: prefix of the bosinst_data NIM resource that contains the BOS
                           installation program to use; the NIM name of the target VIOS is added to
                           this prefix to find the actual NIM resource, like:
                           "<bosinst_data_prefix>_<vios_name>"; this resource must exists prior the
                           playbook execution;
                           required for "upgrade_restore" and "all" actions;
      time_limit:          when this parameter is specified, before starting the upgradeios action
                           specified on a new VIOS in the "targets" list, the actual date is
                           compared to this parameter value; if it is greater then the task stops;
                           the format is mm/dd/yyyy hh:mm
      vios_status:         specify the result of previous operation. This allows to combine
                           severals tasks that depend on the result of previous operation.
      vars:                specify playbook's variables to use (log_file for example);
                           if myvars is the playbook hash, use vars: "{{ myvars }}"
      nim_node:            allows to pass along NIM node info from a task to another so that it
                           discovers NIM info only one time for all tasks;
                           if you use: "register: backup_result", you can specify the following
                           nim_node: "{{ backup_result.nim_node }}"
```
