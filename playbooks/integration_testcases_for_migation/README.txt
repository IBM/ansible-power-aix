Test integration for role ibm.power_aix.nim_alt_disk_migration
This role will migrate an end-node to a next AIX relase using nimadm (NIM alternate disk Migration).

Some of the test can not be run within the same playbook. The variables from one
execution will affect the other. For that reason, they have been isolated to a differnt playbooks:

integration_migration_test13_no_disk_name_variable.yml
integration_migration_test12_no_target_disks_variable.yml
integration_migration_test11_no_nim_client_variable.yml
integration_migration_test10_no_lpp_source.yml
integration_migration_test09_minimum_vars_for_migration_validation.yml
integration_migration_test01-08.yml   <== Define paramters but test them empty. Test validation and perform a  migration.
