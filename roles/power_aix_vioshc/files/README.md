# vios-health-checker

## Purpose

Health assessment tool for VIOS pre-install routines.
It check if a VIO Server or a pair of VIO Servers could be updated.

It checks the
- active client LPARs
- vSCSI mapping
- NPIV Path for Fibre Channel configuration
- SEA configuration
- VNIC configuration

## Note

This tool:
- should be executed on the NIM master (it uses lsnim commands).
- uses Curl (pycurl) to interract with the HMC REST API.
- will try to retrieve the HMC login/password from the HMC password file (using dkeyexch) if not specified. 
- uses a HMC session key for Curl requests.

## Syntax

- To display the usage message:
    vioshc -h
- To display the managed system information
    vioshc [-u id] [-p pwd] -i hmc_ip_addr -l m [-v] 
- To display the managed system informatio and VIOS(es) UUID
    vioshc [-u id] [-p pwd] -i hmc_ip_addr -l a [-v] 
- To perform the heath checking on a VIO Server
    vioshc [-u id] [-p pwd] -i hmc_ip_addr -m managed_system_uuid -U vios_uuid [-v]
- To perform the heath check on a pair of VIO Servers
    vioshc [-u id] [-p pwd] -i hmc_ip_addr -m managed_system_uuid -U vios_uuid -U vios_uuid [-v]
- To choose the path directory to save the log files and .xml files, use -L /path option
    by default all traces are stored in /tmp/vios_maint directory
- To keep xml directory and .xml files use the -D option

You can use the following option to provide additionnal inforamtion:
 -u : hmc user ID
 -p : hmc user password

## Exit Status

This command returns the following exit values:
- 0        in case of success, list operation succeeds or the pre-check is pass 
- not 0    an error occurred.

## Files

- /usr/sbin/vios-hc.py
- /tmp/vios_maint/*.log             traces of the execution
- /tmp/vios_maint/<xml_dir_xxxx>/sessionkey.xml    HMC credentials used for HMC requests 
- /tmp/vios_maint/<xml_dir_xxxx>/*.xml  results of REST API calls can remain in case of error

## Example

- /usr/sbin/vioshc.py -l a -i e08hmc2.aus.stglabs.ibm.com                                                                              

<pre><code>

Managed Systems UUIDs                   Serial
-------------------------------------   ----------------------
931a9335-bb33-388b-b708-a01b5cd24534    8246-L2C*100194A

        VIOS                                    Partition ID
        -------------------------------------   --------------
        21C6104E-2D61-4180-B525-8522ECFF2938    2
        5D01525E-8A34-4B1E-997B-36932C562755    1

582ae663-feb3-3946-9602-ee0999416c59    8246-L2C*10018FA

        VIOS                                    Partition ID
        -------------------------------------   --------------
        277A536E-7436-4AB7-B5C5-7398AB470AEB    2
        7DDD1C13-95C6-4801-9BCF-9EA829670217    1

</code></pre>

- /usr/sbin/vioshc.py -i e08hmc2.aus.stglabs.ibm.com -m 582ae663-feb3-3946-9602-ee0999416c59 -U 277A536E-7436-4AB7-B5C5-7398AB470AEB -U 7DDD1C13-95C6-4801-9BCF-9EA829670217

<pre><code>

Primary VIOS Name         IP Address      ID         UUID                
-------------------------------------------------------------------------------------------------
gdrh9v2                   9.3.18.143      2          277A536E-7436-4AB7-B5C5-7398AB470AEB     

Backup VIOS Name          IP Address      ID         UUID                
-------------------------------------------------------------------------------------------------
gdrh9v1                   9.3.18.142      1          7DDD1C13-95C6-4801-9BCF-9EA829670217     

PASS: Active client lists are the same for both VIOSes
FAIL: vSCSI configurations are not identical on both vioses.
PASS: same FC mapping configuration on both vioses.
FAIL: SEA deserving VLAN(s) 12 are not in the correct state for HA operation.
PASS: SEA deserving VLAN(s) 10,11 are configured for failover.
No VNIC Configuration Detected.


3 of 5 Health Checks Passed
2 of 5 Health Checks Failed
Pass rate of 60%

</code></pre>



