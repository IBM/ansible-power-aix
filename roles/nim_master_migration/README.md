# Ansible Role: nim_alt_disk_migration
The [IBM Power Systems AIX](../../README.md) collection provides an 
[Ansible role](https://docs.ansible.com/ansible/latest/user_guide/playbooks_reuse_roles.html), 
referred to as `nim_master_migration`, which assists in automating in migration in 
migration of NIM master machine.

For guides and reference, see the [Docs Site](https://ibm.github.io/ansible-power-aix/roles.html).

## Requirements

None.

## Role Variables


Available variables are listed below, along with default values:

<table>
    <thead>
        <tr>
            <th colspan="6"> Role Variables </th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <td><b> Variable </b></td>
            <td><b> Suboptions </b></td>
            <td><b> Required </b></td>
            <td><b> Default </b></td>
            <td><b> Choices </b></td>
            <td><b> Comments </b></td>
        </tr>
        <tr>
            <td><b> master_a </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                NIM Master that will be used in migrating the required Master machine. Controller node would be connected to this node.
            </td>
        </tr>
        <tr>
            <td><b> master_b </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td>
                Specifies the NIM Master machine that is supposed to be migrated using
                another NIM Master (master_a) as its master.
            </td>
        </tr>
        <tr>
            <td><b> alt_disk </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies the alternate disk on which NIM Alt Disk Migration will take place.
            </td>
        </tr>
        <tr>
            <td><b> db_filename </b></td>
            <td>  </td>
            <td> false </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies the filename, where the database backup will be created on master_b machine.
            </td>
        </tr>
        <tr>
            <td><b> lpp_source_v </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies a NIM object name associated to a LPP resource for the desired level of migration.
            </td>
        </tr>
        <tr>
            <td><b> spot_v </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies a NIM object name associated to a spot resource for the desired level of migration.
            </td>
        </tr>
        <tr>
            <td><b> nim_master_fileset_src </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies the location and filename, where the NIM master fileset (nos.sysmgt) is located.
            </td>
        </tr>
        <tr>
            <td><b> nim_master_fileset_dest </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies the location wher NIM master fileset will be copied to/located on the NIM master mahine (master_b)
            </td>
        </tr>
        <tr>
            <td><b> db_file_controller </b></td>
            <td>  </td>
            <td> false </td>
            <td>  </td>
            <td>  </td>
            <td> 
                Specifies the location where the database backup file will be copied to from the NIM master machine (master_b)
            </td>
        </tr>
        <tr>
            <td><b> phase </b></td>
            <td>  </td>
            <td> true </td>
            <td>  </td>
            <td> backup_and_migration, db_restore </td>
            <td> 
                Specifies the phase of operations that need to be performed so as to accomplish the broader task of Migrating NIM Master machine.
            </td>
        </tr>
    </tbody>
</table>

**NOTES**: 
- This role requires another machine having NIM master setup (***master_a***), master_a should be able to establish SSH connection with the master machine that needs to be migrated.
- This machine (master_a) should be on the level to which you want your master machine (***master_b***) to be migrated.
- Controller node's primary target is master_a, but It should be able to establish SSH connection with master_b (The machine that needs to be migrated) as well.
- To completely migrate the required machine and bring it back to the original state, you need to run the role twice. Once, with phase = "backup_and_migration" and second time with phase = "db_restore"
- ***backup_and_migration*** will initialise the setup required and perform the migration of master_b using master_a as master.
- ***db_restore*** will restore the database and bring the machine (master_b) to previous state.

## Dependencies

- nim_alt_disk_migration role

## Example Playbook

```
# Use C(phase) = backup_and_migration to perform the following tasks:
# Creating database backup file
# Unconfiguring master_b (NIM master machine that needs to be migrated)
# Setting up master_b as client of master_a
# Perform Nim Alt disk migration operation
# Rebooting the machine (master_b)

- name: "nim_master_migration demo"
  hosts: all
  gather_facts: false
  remote_user: root
  collections:
    - ibm.power_aix
  tasks:
    - import_role:
        name: ibm.power_aix.nim_master_migration
      vars:
        master_a: p9zpa-ansible-nim1.aus.stglabs.ibm.com
        master_b: "fvtfleet1-lp1.aus.stglabs.ibm.com"
        alt_disk: "hdisk1"
        db_filename: "db_backupfile"
        lpp_source_v: "2317A_73D"
        spot_v: "2317A_73D_spot"
        nim_master_fileset_src: "~/bos.sysmgt"
        nim_master_fileset_dest: "~/bos.sysmgt"
        phase: backup_and_migration
```

```
# Use C(phase) = db_restore to perform the following tasks:
# Copy and install nim master fileset (bos.sysmgt.nim.master) on NIM master (master_b)
# Transfer and restore database backup on NIM master (master_b)
- name: "nim_master_migration demo"
  hosts: all
  gather_facts: false
  remote_user: root
  collections:
    - ibm.power_aix
  tasks:
    - import_role:
        name: ibm.power_aix.nim_master_migration
      vars:
        master_a: p9zpa-ansible-nim1.aus.stglabs.ibm.com
        master_b: "fvtfleet1-lp1.aus.stglabs.ibm.com"
        alt_disk: "hdisk1"
        db_filename: "db_backupfile"
        lpp_source_v: "2317A_73D"
        spot_v: "2317A_73D_spot"
        nim_master_fileset_src: "~/bos.sysmgt"
        nim_master_fileset_dest: "~/bos.sysmgt"
        phase: db_restore
        db_file_controller: "~/db_backupfile"
```
## Copyright
© Copyright IBM Corporation 2022
