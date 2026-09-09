# GNS3 Ansible Role

Ansible role to install and configure a GNS3 server on your device, including setup for NGS. It utilises
davidban77's gns3fy (https://github.com/davidban77/gns3fy) for project and node
creation, template upload and building node links. The role connects to the switch node via Telnet and uses Expect scripts to
establish an admin connection using configurable values.


### How to run

In order to run this, you will need a playbook and an inventory. A minimal inventory could simply be

```yaml
[gns3]
localhost ansible_connection=local
```
Paired with the above inventory, a playbook to configure GNS3 with a Dell OS10 S4000 switch could look like so:

```yaml
- hosts: gns3
  become: true
  roles:
    - role: gns3
      vars:
        gns3_project_name: Trial_project
        switch_type: dellos10
        gns3_switch_model: "Dell OS10 S4000-10.5.6.13.327"
        gns3_cloud_interfaces:
        - cloud: Cloud1
          interface: breth1
          name: breth1
          port_number: 0
          type: ethernet
        - cloud: Cloud2
          interface: breth1
          name: breth1
          port_number: 0
          type: ethernet
        - cloud: Cloud3
          interface: brgns3
          name: brgns3
          port_number: 0
          type: ethernet
        gns3_switch_boot_delay: 181
```

### Configuration options

#### GNS3 Project Name
You can set the ```gns3_project_name``` variable in the playbook to the desired
project name. It defaults to ```gns3_project``` in defaults/main.yml.

#### Switch types
The role aims to be compatible with several switch types, but is currently only
compatible with Dell OS10 switches.

To ensure the correct images are installed, you must set the ```switch_type```
variable. Below is an example of how to set to be a Dell OS10 switch.

```yaml
switch_type: dellos10
```

This will determine which templates are uploaded to GNS3 and which commands are
run to establish an admin connection point, and apply intial configuration for
NGS.

#### GNS3 Switch Node Model

On top of the switch manufacturer, it is important to choose the switch model.
Right now, the Dell OS10 switches are set to v10.5.6.13, applicable models can
be found online.

Here is an example of setting it to be a Dell OS10 N3248TE-10.5.6.13.327 switch:
```yaml
gns3_switch_model: "Dell OS10 N3248TE-10.5.6.13.327"
```

#### Management
In order to connect to the switch, it is necessary to set up a management
nterface. You will need to set an IP address to establish an SSH connection.

You need to assign values to the ```management_ip``` and
```management_interface``` variables.

For example, the defaults are:

```yaml
management_ip: 192.168.33.10/24
management_interface: mgmt1/1/1
```
####
#### Cloud interfaces
Cloud nodes must be used in GNS3 so the switch can communicate with specific
interfaces. ``port_number`` refers to the cloud port.
```yaml
gns3_cloud_interfaces:
  - cloud: Cloud1
    interface: breth1
    name: breth1
    port_number: 0
    type: ethernet
  - cloud: Cloud2
    interface: breth1
    name: breth1
    port_number: 0
    type: ethernet
  - cloud: Cloud3
    interface: brgns3
    name: brgns3
    port_number: 0
    type: ethernet
```

You should ensure ``gns3_cloud_node_quantity`` is set to match the number of
interfaces defined so GNS3 creates the correct number of cloud nodes. NOTE:
Could maybe remove this variable and calculate how many interfaces there are.

#### Links

It is important to define the required links in GNS3. This will be based on
which port connects to which interface in your setup.
This differs based on the switch model but below is an example for a Dell OS10.
```yaml
gns3_links:
  - source_node: "{{ gns3_switch_model }}"
    source_adapter: 0
    source_port: 0 #mgmt 1/1/1
    target_node: Cloud1
    target_adapter: 0
    target_port: 0
  - source_node: "{{ gns3_switch_model }}"
    source_adapter: 1
    source_port: 0 #eth 1/1/1
    target_node: Cloud2
    target_adapter: 0
    target_port: 0
  - source_node: "{{ gns3_switch_model }}"
    source_adapter: 2
    source_port: 0 #eth 1/1/2
    target_node: Cloud3
    target_adapter: 0
    target_port: 0
```
#### Additional variables
``gns3_work_dir`` is currently defaults to ``"{{ ansible_facts['env']['HOME'] }}/gns3-work"``
but may be changed to change where your code downloads. This is a temporary
directory.