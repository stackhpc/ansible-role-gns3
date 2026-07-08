#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project, Node
from ansible.module_utils.gns3_client import gns3_server


DOCUMENTATION = """
---
module: create_nodes

short_description: Creates nodes in a GNS3 project

description:
    - Creates nodes in a GNS3 project from existing templates.
    - Creates a Cloud node if required.
    - Applies Cloud port mappings during Cloud node creation.

options:
    project_name:
        description:
            - Name of the GNS3 project.
        required: true
        type: str

    node_type:
        description:
            - GNS3 template name to use for the node.
        required: true
        type: str

    cloud_ports_mapping:
        description:
            - Cloud interface mappings.
        required: false
        type: list
"""


EXAMPLES = """
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


        changed = False
        created_nodes = []


        # Find existing nodes in project
        existing_node_names = {
            node.name
            for node in project.nodes
        }


       # Find matching template for requested node type
        matched_template_name = None

        for template in gns3_server.get_templates():

            template_name = (
                template["name"]
                if isinstance(template, dict)
                else template.name
            )

            if template_name == node_type:
                matched_template_name = template_name
                break


        if not matched_template_name:
            module.fail_json(
                msg=f"No GNS3 template found matching '{node_type}'"
            )


       # Create relevant node if it doesn't already exist in the project
        if node_type not in existing_node_names:

            changed = True

            if not module.check_mode:

                node = Node(
                    project_id=project.project_id,
                    name=node_type,
                    template=matched_template_name,
                    connector=gns3_server,
                )

                node.create()

            created_nodes.append(node_type)


       # Create Cloud node if it doesn't already exist in the project
        project.get()

        cloud_node = next(
            (
                node
                for node in project.nodes
                if node.name == "Cloud"
            ),
            None
        )

        if cloud_node is None:

            changed = True

            if not module.check_mode:

                response = gns3_server.http_call(
                    "post",
                    f"{gns3_server.base_url}/projects/{project.project_id}/nodes",
                    json_data={
                        "name": "Cloud",
                        "node_type": "cloud",
                        "compute_id": "local",
                        "properties": {
                            "interfaces": []
                        },
                        "x": 100,
                        "y": 100,
                    },
                )

                cloud_node_id = response.json()["node_id"]

                created_nodes.append("Cloud")


        # Update Cloud node with port mappings if provided
        if cloud_ports_mapping:

            gns3_server.http_call(
                "put",
                f"{gns3_server.base_url}/projects/{project.project_id}/nodes/{cloud_node_id}",
                json_data={
                    "properties": {
                        "ports_mapping": cloud_ports_mapping
                    }
                },
            )

        # Start nodes
        if not module.check_mode:
            project.get()
            for node in project.nodes:

                if node.status != "started":
                    node.start()
                    changed = True


        module.exit_json(
            changed=changed,
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