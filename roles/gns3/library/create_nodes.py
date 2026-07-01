#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: create_nodes
short_description: Creates nodes in a GNS3 project
description:
    - "This module creates nodes in a GNS3 project on the GNS3 server."
options:
    project_name:
        description:
            - The name of the project to create.
        required: true
        type: str
    node_type:
        description:
            - The node type to create from an available GNS3 template.
        required: true
        type: str
    cloud_ports_mapping:
        description:
            - Optional list of cloud interface mappings to apply to the Cloud node.
        required: false
        type: list
"""

EXAMPLES = """
"""

from gns3fy import Project, Node
from ansible.module_utils.gns3_client import gns3_server

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
        }
    )

    project_name = module.params["project_name"]
    node_type = module.params["node_type"]
    cloud_ports_mapping = module.params["cloud_ports_mapping"]

    try:
        project = Project(name=project_name, connector=gns3_server)
        project.get()

        created_nodes = []
        existing_node_names = {node.name for node in project.nodes}
        matched_template_name = None

        for template in gns3_server.get_templates():
            if node_type in template["name"]:
                matched_template_name = template["name"]
                break

        if not matched_template_name:
            module.fail_json(msg=f"No GNS3 template matched node_type '{node_type}'.")

        if node_type not in existing_node_names:
            node = Node(
                project_id=project.project_id,
                name=node_type,
                template=matched_template_name,
                connector=gns3_server,
            )
            node.create()
            created_nodes.append(node.name)

        cloud_node = next((node for node in project.nodes if node.name == "Cloud"), None)
        if cloud_node is None:
            cloud_node = Node(
                project_id=project.project_id,
                name="Cloud",
                template="Cloud",
                connector=gns3_server,
            )
            cloud_node.create()
            created_nodes.append(cloud_node.name)

        cloud_updated = False

        if cloud_ports_mapping:
            cloud_node.update(ports_mapping=cloud_ports_mapping)
            cloud_updated = True

        project.get()

        # start nodes
        for node in project.nodes:
            if node.status() != "started":
                node.start()

        module.exit_json(
            changed=bool(created_nodes) or cloud_updated,
            project_name=project_name,
            created_nodes=created_nodes,
        )

    except Exception as exc:
        module.fail_json(msg=str(exc))

def main():
    run_module()

if __name__ == "__main__":
    main()