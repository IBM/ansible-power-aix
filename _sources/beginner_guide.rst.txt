.. ...........................................................................
.. © Copyright IBM Corporation 2020                                          .
.. ...........................................................................

-----------

**Beginners Guide**


Items needed for this guide: 

* A Controller Node to install ansilbe on.

* A Managed Node(s) to apply the example ansible-power-aix playbook_.

   .. _playbook: https://github.com/IBM/ansible-power-aix/blob/dev-collection/playbooks/demo_nim_check.yml
  
   .. warning::
      There are several os architectures/flavors to choose from when installing ansible to your controller node. AIX is not supported. It also is not an ideal choice for starting out. For this guide we will use Red Hat Enterprise Linux 7.                                        This guide has also been tested with CentOS 7. Check this link for possible controller node options: 			https://docs.ansible.com/ansible/latest/installation_guide/intro_installation.html#installing-ansible-on-rhel-centos-or-fedora  
      
Install Ansible with:

   .. code-block:: sh
   
       $ sudo yum install ansible

To install a build from the ansible-power-aix Git repository:

   #. Obtain a local copy from the Git repository:

      .. code-block:: sh

         $ curl -L https://github.com/IBM/ansible-power-aix/blob/dev-collection/builds/ibm-power_aix-1.0.2.tar.gz\?raw\=true -o ibm-power_aix-1.0.2.tar.gz

   #. Install the local collection archive:

      .. code-block:: sh

          $ ansible-galaxy collection install ibm-power_aix-1.0.2.tar.gz

      In the output of collection installation, note the installation path to access the sample playbook:

      .. code-block:: sh

         Process install dependency map
         Starting collection install process
         Installing 'ibm.power_aix:1.0.0' to '/Users/user/.ansible/collections/ansible_collections/ibm/power_aix'


  .. note:: There is a role_ to auto install python and yum on your managed nodes, however for this guide we will perform this step manually for clarity.
    
  .. _role: https://ibm.github.io/ansible-power-aix/roles/power_aix_bootstrap.html#example-playbook

    **Installing yum on AIX:**
    
        #. Make sure rpm.rte is installed at a level of 4.13.0.10 or higher.
            To check this run:
            
                .. code-block:: sh

                     $lslpp -la rpm.rte
                 
        #. If it is not installed you can download rpm.rte from"https://ftp.software.ibm.com/aix/freeSoftware/aixtoolbox/INSTALLP/rpm.rte"
            Then install it:

                .. code-block:: sh

                    $install –d. –acgXY rpm.rte
            
        #. Download yum_bundle.tar from: https://public.dhe.ibm.com/aix/freeSoftware/aixtoolbox/ezinstall/ppc/ (it's recommended to Download the latest version)
            This bundle contains yum and all of it's dependency rpms.  Extract the yum packages from the yum_bundle.tar using tar: 
                .. code-block:: sh

                    $tar -xvf yum_bundle.tar
                
            Install each of the rpm packages using the rpm command: 
                .. code-block:: sh

                    $rpm -Uvh (packagename).rpm
            
        #. yum conf file:
            yum.conf file will be installed under the path /opt/freeware/etc/yum.conf
            By default with yum-3.4.3-1 only ppc repository is enabled.with yum-3.4.3-2 or higher version, ppc, noarch & any one of the ppc-6.1/ppc-7.1/ppc-7.2 repository is enabled.
            If you faced ssl error while installing with yum, <baseurl> use http instead of https.


    
    **Configure our Admin User for SSH Access:**
    
        We need to ensure our controller node can access the managed node over SSH without a password. We will set up an SSH key pair to allow this. Log onto the control node as the admin 		user and run the following command to generate an SSH key pair. Note: Just hit enter at the prompts to accept the defaults.
            .. code-block:: sh
            
                $sudo ssh-copy-id root@node_IP
            
    **Build your inventory:**
    
        The inventory file can be in one of many formats, depending on the inventory plugins you have. The most common formats are INI and YAML. A basic INI etc/ansible/hosts might look 		like this: (Make sure you are logged onto the Control node as the admin user).
            .. code-block:: sh	
            
                $sudo vi /etc/ansible/hosts
            
                    If all hosts in a group share a variable value, you can apply that variable to an entire group at once. In INI:

                    [nimserver]
                    host1
                    host2

                    [nimserver:vars]
                    ansible_ssh_port=22
                    ansible_ssh_user=root
                
        Test Connection:
            .. code-block:: sh

                $ansible all -u root -m ping
                
                    host1 | SUCCESS => {
                        "ansible_facts": {
                            "discovered_interpreter_python": "/usr/bin/python"
                            }, 
                                "changed": false, 
                            "ping": "pong"
                            }
                
                
                    host2 | SUCCESS => {
                        "ansible_facts": {
                            "discovered_interpreter_python": "/usr/bin/python"
                            }, 
                                "changed": false, 
                                "ping": "pong"
                            }

        
        Note:
        For more information you can check: https://docs.ansible.com/ansible/latest/user_guide/intro_inventory.html
    
    
    **Run your first Playbook:**
        
                
                
                
        Run your Playbook:
                Ensure you are in the collections playbook directory:

                .. code-block:: sh	

                cd ~/.ansible/collections/ansible_collections/ibm/power_aix/playbooks/
        
                .. code-block:: sh	
            
                    $ ansible-playbook demo_nim_check.yml 

                .. code-block:: sh	

                    [WARNING]: running playbook inside collection ibm.power_aix
                    PLAY [NIM check on AIX playbook] ***********************************************
                    TASK [AIX NIM] *****************************************************************
                    [WARNING]: Platform aix on host host1 is using the discovered Python
                    interpreter at /usr/bin/python, but future installation of another Python
                    interpreter could change this. See https://docs.ansible.com/ansible/2.9/referen
                    ce_appendices/interpreter_discovery.html for more information.
                    ok: [host1]
                    TASK [debug] *******************************************************************
                    ok: [host1] => {
                    "nim_output": {
                        "ansible_facts": {
                        "discovered_interpreter_python": "/usr/bin/python"
                        }, 
                        "changed": false, 
                        "failed": false, 
                        "msg": "NIM check completed successfully", 
                        "nim_node": {
                        "lpp_source": {}, 
                        "master": {
                            "cstate": "ready for a NIM operation", 
                            "oslevel": "7200-03-03-1914", 
                            "type": "master"
                        }, 
                        "standalone": {
                            "Client1": {
                            "cstate": "ready for a NIM operation", 
                            "ip": "client1", 
                            "oslevel": "7200-03-03-1914", 
                            "type": "standalone"
                            }, 
                            "client2": {
                            "cstate": "ready for a NIM operation", 
                            "ip": "client2", 
                            "oslevel": "7200-03-03-1914", 
                            "type": "standalone"
                            }
                        }, 
                        "vios": {}
                        }, 
                        "nim_output": [], 
                        "stderr": "", 
                        "stderr_lines": [], 
                        "stdout": "", 
                        "stdout_lines": [], 
                        "warnings": [
                        "Platform aix on host host1 is using the discovered Python interpreter at /usr/bin/python, but future installation of another Python interpreter could change this. See https://docs.ansible.com/ansible/2.9/reference_appendices/interpreter_discovery.html for more information."
                        ]
                    }
                    }
                    PLAY RECAP *********************************************************************
                    host1        : ok=2   changed=0  unreachable=0  failed=0  skipped=0  rescued=0  ignored=0    IBM Power Systems AIX Collection 