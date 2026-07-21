#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project
from ansible.module_utils.gns3_client import gns3_server
from ansible.module_utils.gns3_links import (
    link_key,
    project_link_keys,
    resolve_node,
)


DOCUMENTATION = """
---
module: gns3_link_status

short_description: Check if desired links already exist

description:
    - Checks if required links already exist in a GNS3 project.

options:
    project_name:
        description:
            - The name of the GNS3 project.
        required: true
        type: str

    links:
        description:
            - List of link definitions.
        required: true
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
                "required": True,
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


        node_by_name = {
            node.name: node
            for node in project.nodes
        }


        missing_links = []


        for link_definition in links:

            source_name = link_definition["source_node"]
            target_name = link_definition["target_node"]


            source_node = resolve_node(
                node_by_name,
                source_name,
            )

            target_node = resolve_node(
                node_by_name,
                target_name,
            )


            if source_node is None or target_node is None:

                module.fail_json(
                    msg=(
                        "Unable to check link because node was not found: "
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


            if desired_link_key not in existing_link_keys:

                missing_links.append(
                    {
                        "source": source_name,
                        "target": target_name,
                    }
                )


        module.exit_json(
            changed=False,
            exists=(len(missing_links) == 0),
            missing_links=missing_links,
        )


    except Exception as exc:

        module.fail_json(
            msg=str(exc),
            exists=False,
        )


def main():
    run_module()


if __name__ == "__main__":
    main()