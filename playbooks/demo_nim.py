---
- name: "NIM operation on AIX/VIOS"
  hosts: nimserver
  gather_facts: no
  vars:
    check_targets_v:        standalone
    install_targets_v:      quimby06
    update_lpp_v:           latest_sp
    bos_inst_resgroup_v:    basic_res_grp
    bos_inst_script_v:      setup_root
    master_setup_device_v:  "/dev/cd0"
    define_resource_v:      setup_root
    define_location_v:      /export/nim/script_res/yum_install.sh
    apply_script_v:         setup_yum
    alloc_resource_v:       7200-03-04-1938-lpp_source
    rm_resource_v:          quimby06_svg

  collections:
  - ibm.power_aix
  tasks:

    - name: Update a LPAR to the latest level available
      nim:
        action: update
        targets: "{{ install_targets_v }}"
        lpp_source: "{{ update_lpp_v }}"
        asynchronous: True
        force: False
      register: result
    # - debug: var=result

    - name: BOS installation using a group resource a customization script
      nim:
        action: bos_inst
        targets: "{{ install_targets_v }}"
        group: "{{ bos_inst_resgroup_v }}"
        script: "{{ bos_inst_script_v }}"
      register: result
    # - debug: var=result

    - name: Configure the NIM master
      nim:
        action: master_setup
        device: "{{ master_setup_device_v }}"
      register: result
    # - debug: var=result

    - name: Get oslevels
      nim:
        action: check
        targets: "{{ check_targets_v }}"
      register: result
    # - debug: var=result

    - name: Compare installation inventories
      nim:
        action: compare
        targets: "{{ check_targets_v }}"
      register: result
    # - debug: var=result

    - name: Define a customization script
      nim:
        action: define_script
        targets: "{{ install_targets_v }}"
        resource: "{{ define_resource_v }}"
        location: "{{ define_location_v }}"
      register: result
    # - debug: var=result

    - name: Apply a customization script
      nim:
        action: script
        targets: "{{ install_targets_v }}"
        script: "{{ apply_script_v }}"
        asynchronous: True
      register: result
    # - debug: var=result

    - name: Allocate a NIM resource
      nim:
        action: allocate
        targets: "{{ install_targets_v }}"
        lpp_source: "{{ alloc_resource_v }}"
      register: result
    # - debug: var=result

    - name: Deallocate a NIM resource
      nim:
        action: deallocate
        targets: "{{ install_targets_v }}"
        lpp_source: "{{ alloc_resource_v }}"
      register: result
    # - debug: var=result

    - name: Remove the resource from the NIM master
      nim:
        action: remove
        resource: "{{ rm_resource_v }}"
      register: result
    # - debug: var=result

    - name: Reset the current state of standalone partitions
      nim:
        action: reset
        targets: "{{ check_targets_v }}"
        force: False
      register: result
    # - debug: var=result

    - name: Reboot a partition
      nim:
        action: reboot
        targets: "{{ install_targets_v }}"
      register: result
    # - debug: var=result

    - name: Perform a maintenance operation on standalone partition
      nim:
        action: maintenance
        targets: "{{ install_targets_v }}"
      register: result
    # - debug: var=result
