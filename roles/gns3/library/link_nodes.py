#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project, Link
from ansible.module_utils.gns3_client import gns3_server
from ansible.module_utils.gns3_links import (
    link_key,
    project_link_keys,
    resolve_node,
)


DOCUMENTATION = """
---
module: link_nodes

short_description: Links nodes in a GNS3 project

description:
    - Creates links between nodes in a GNS3 project.

options:
    project_name:
        description:
            - The name of the GNS3 project.
        required: true
        type: str

    links:
        description:
            - List of link definitions.
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
            "links": {
                "type": "list",
                "required": False,
                "default": None,
            },
        },
        supports_check_mode=True,
    )


    project_name = module.params["project_name"]
    links = module.params["links"]


    try:

        project = Project(
            name=project_name,
            connector=gns3_server,
        )

        project.get()


        existing_link_keys = project_link_keys(project)

        created_links = []


       # Find existing nodes in project
        node_by_name = {
            node.name: node
            for node in project.nodes
        }


        # Create links between nodes
        if links:

            for link_definition in links:


                source_name = link_definition["source_node"]
                target_name = link_definition["target_node"]


                source_node = resolve_node(node_by_name, source_name)
                target_node = resolve_node(node_by_name, target_name)


                if source_node is None or target_node is None:

                    module.fail_json(
                        msg=(
                            "Unable to create link because one or more "
                            "nodes were not found: "
                            f"{source_name} -> {target_name}"
                        ),
                        available_nodes=list(node_by_name.keys()),
                    )


                source_adapter = link_definition.get(
                    "source_adapter",
                    0,
                )

                source_port = link_definition.get(
                    "source_port",
                    0,
                )

                target_adapter = link_definition.get(
                    "target_adapter",
                    0,
                )

                target_port = link_definition.get(
                    "target_port",
                    0,
                )


                desired_link_key = link_key(
                    source_node.node_id,
                    source_adapter,
                    source_port,
                    target_node.node_id,
                    target_adapter,
                    target_port,
                )


                if desired_link_key in existing_link_keys:
                    continue


                if not module.check_mode:

                    link = Link(
                        project_id=project.project_id,
                        nodes=[
                            {
                                "node_id": source_node.node_id,
                                "adapter_number": source_adapter,
                                "port_number": source_port,
                            },
                            {
                                "node_id": target_node.node_id,
                                "adapter_number": target_adapter,
                                "port_number": target_port,
                            },
                        ],
                        connector=gns3_server,
                    )

                    link.create()


                existing_link_keys.add(link_key)

                created_links.append(
                    {
                        "source": source_name,
                        "target": target_name,
                    }
                )
        else:

            print("Please provide a list of links to create. No links were specified.")


        module.exit_json(
            changed=bool(created_links),
            project_name=project_name,
            linked_nodes=created_links,
        )


    except Exception as exc:

        module.fail_json(
            msg=str(exc)
        )



def main():
    run_module()


if __name__ == "__main__":
    main()
