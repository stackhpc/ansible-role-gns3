#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project, Node
from ansible.module_utils.gns3_client import gns3_server


DOCUMENTATION = """
---
module: create_nodes

short_description: Creates a node in a GNS3 project

description:
    - Creates a node in a GNS3 project based on a specified template.
    - Creates one or more Cloud nodes when node_type is Cloud.
    - Cloud interface mappings can be supplied using cloud_interfaces.

options:
    project_name:
        description:
            - Name of the GNS3 project.
        required: true
        type: str

    node_type:
        description:
            - GNS3 template name or Cloud.
        required: true
        type: str

    cloud_interfaces:
        description:
            - Cloud interface mappings.
        required: false
        type: list
        default: null

    cloud_node_quantity:
        description:
            - Number of Cloud nodes to create.
        required: false
        type: int
        default: 1
"""


def run_module():

    module = AnsibleModule(
        argument_spec={
            "project_name": {
                "type": "str",
                "required": True,
            },
            "node_type": {
                "type": "str",
                "required": True,
            },
            "cloud_interfaces": {
                "type": "list",
                "required": False,
                "default": None,
            },
            "cloud_node_quantity": {
                "type": "int",
                "required": False,
                "default": 1,
            },
        },
        supports_check_mode=True,
    )

    project_name = module.params["project_name"]
    node_type = module.params["node_type"]
    cloud_interfaces = module.params["cloud_interfaces"]
    cloud_node_quantity = module.params["cloud_node_quantity"]

    try:

        #
        # Get project
        #
        project = Project(
            name=project_name,
            connector=gns3_server,
        )

        project.get()

        created_nodes = []

        #
        # Create Cloud nodes
        #
        if node_type.lower() == "cloud":

            #
            # Check mode
            #
            if module.check_mode:

                module.exit_json(
                    changed=True,
                    project_name=project_name,
                    created_nodes=[
                        f"Cloud{i + 1}"
                        for i in range(cloud_node_quantity)
                    ],
                )

            #
            # Create each Cloud
            #
            for i in range(cloud_node_quantity):

                cloud_name = f"Cloud{i + 1}"

                #
                # Create Cloud node
                #
                response = gns3_server.http_call(
                    "post",
                    f"{gns3_server.base_url}/projects/"
                    f"{project.project_id}/nodes",
                    json_data={
                        "name": cloud_name,
                        "node_type": "cloud",
                        "symbol": ":/symbols/cloud.svg",
                        "compute_id": "local",
                        "properties": {
                            "interfaces": []
                        },
                        "x": 100,
                        "y": 100,
                    },
                )

                response_data = response.json()

                created_node = response_data["name"]
                cloud_node_id = response_data["node_id"]

                created_nodes.append(created_node)

                #
                # Build ports_mapping for this Cloud
                #
                cloud_ports_mapping = []

                if cloud_interfaces:

                    for interface in cloud_interfaces:

                        if interface.get("cloud") != cloud_name:
                            continue

                        cloud_ports_mapping.append(
                            {
                                "interface": interface["interface"],
                                "name": interface["name"],
                                "port_number": interface["port_number"],
                                "type": interface["type"],
                            }
                        )

                #
                # Update ports_mapping
                #
                if cloud_ports_mapping:

                    gns3_server.http_call(
                        "put",
                        f"{gns3_server.base_url}/projects/"
                        f"{project.project_id}/nodes/{cloud_node_id}",
                        json_data={
                            "properties": {
                                "ports_mapping": cloud_ports_mapping
                            }
                        },
                    )

        #
        # Create template-based node
        #
        else:

            template = None

            for item in gns3_server.get_templates():

                template_name = (
                    item["name"]
                    if isinstance(item, dict)
                    else item.name
                )

                if template_name == node_type:
                    template = template_name
                    break

            #
            # Template not found
            #
            if not template:

                module.fail_json(
                    msg=f"No GNS3 template found matching '{node_type}'"
                )

            #
            # Create node
            #
            if not module.check_mode:

                node = Node(
                    project_id=project.project_id,
                    name=node_type,
                    template=template,
                    connector=gns3_server,
                )

                node.create()

            created_nodes.append(node_type)

        #
        # Return
        #
        module.exit_json(
            changed=True,
            project_name=project_name,
            created_nodes=created_nodes,
        )

    except Exception as exc:

        module.fail_json(
            msg=str(exc)
        )


def main():
    run_module()


if __name__ == "__main__":
    main()
