# GNS3 Ansible Role

Ansible role to install and configure a GNS3 server on your device. It utilises
davidban77's gns3fy (https://github.com/davidban77/gns3fy) for project and node
creation, template upload and building node links. The role connects to the switch node via Telnet and uses Expect scripts to
establish an admin connection using configurable values.

### Configuration options

#### GNS3 Project Name
You can set the ```gns3_project_name``` variable in the playbook to the desired project name. It defaults to ```gns3_project``` in defaults/main.yml.

#### Switch types
The role aims to be compatible with several switch types, but is currently only compatible with Dell OS10 switches.

To ensure the correct images are installed, you must set the ```switch_type``` variable. Below is an example of how to set to be a Dell OS10 switch.

```yaml
switch_type: dellos10
```

This will determine which templates are uploaded to GNS3 and which commands are run to establish an admin connection point.

#### GNS3 Switch Node Model

On top of the switch manufacturer, it is important to choose the switch model. Right now, the Dell OS10 switches are set to v10.5.6.13, applicable models can be found online.

Here is an example of setting it to be a Dell OS10 N3248TE-10.5.6.13.327 switch:
```yaml
gns3_switch_model: "Dell OS10 N3248TE-10.5.6.13.327"
```

#### Management
In order to connect to the switch, it is necessary to set up a management interface. You will need to set an IP address to establish an SSH connection.

You need to assign values to the ```management_ip``` and ```management_interface``` variables.

For example:

```yaml
management_ip: 192.168.33.10/24
management_interface: mgmt1/1/1
```
####
#### Cloud Port Mappings
In order to set the port mappings for the cloud, which is required for connection to the switch, you should configure as so:

```yaml
gns3_cloud_ports_mapping:
        - interface: breth1
          name: breth1
          port_number: 0
          type: ethernet
        - interface: dummy1
          name: dummy1
          port_number: 1
          type: ethernet
        - interface: enp3s0
          name: enp3s0
          port_number: 2
          type: ethernet
        - interface: virbr0
          name: virbr0
          port_number: 3
          type: ethernet

```

### Next steps
- Increase switch compatability
- Make switch version configurable ?
- Change how port mappings are defined?
