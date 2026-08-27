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
    - Creates a switch node in a GNS3 project based on a specified template or
    creates a Cloud node.

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

    cloud_ports_mapping:
        description:
            - Cloud interface mappings.
        required: false
        type: list
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
            "cloud_ports_mapping": {
                "type": "list",
                "required": False,
                "default": None,
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
    cloud_ports_mapping = module.params["cloud_ports_mapping"]

    try:

        project = Project(
            name=project_name,
            connector=gns3_server
        )

        project.get()


        created_node = None


        # Create
        if node_type.lower() == "cloud":

            if module.check_mode:
                module.exit_json(
                    changed=True,
                    created_node="Cloud"
                )

            for i in range(module.params["cloud_node_quantity"]):
                response = gns3_server.http_call(
                    "post",
                    f"{gns3_server.base_url}/projects/{project.project_id}/nodes",
                    json_data={
                        "name": "Cloud " + str(i + 1),
                        "node_type": "",
                        "symbol": ":/symbols/cloud.svg",
                        "compute_id": "local",
                        "properties": {
                            "interfaces": []
                        },
                        "x": 100,
                        "y": 100,
                    },
                )

                created_node = response.json()["name"]

                cloud_node_id = response.json()["node_id"]


                if cloud_ports_mapping:

                    gns3_server.http_call(
                        "put",
                        f"{gns3_server.base_url}/projects/{project.project_id}/nodes/{cloud_node_id}",
                        json_data={
                            "properties": {
                                "ports_mapping": {
                                     "interface": cloud_interface[i]["interface"],
                                     "name": cloud_interface[i]["name"],
                                     "port_number": cloud_interface[i]["port_number"],
                                     "type": cloud_interface[i]["type"]
                                }
                            }
                        },
                    )

        #
        # Create template based node
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


            if not template:
                module.fail_json(
                    msg=f"No GNS3 template found matching '{node_type}'"
                )


            if not module.check_mode:

                node = Node(
                    project_id=project.project_id,
                    name=node_type,
                    template=template,
                    connector=gns3_server,
                )

                node.create()

            created_node = node_type


        module.exit_json(
            changed=True,
            project_name=project_name,
            created_node=created_node,
        )


    except Exception as exc:

        module.fail_json(
            msg=str(exc)
        )


def main():
    run_module()


if __name__ == "__main__":
    main()