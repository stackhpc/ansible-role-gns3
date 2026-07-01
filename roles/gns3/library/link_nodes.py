#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: link_nodes
short_description: Links nodes in a GNS3 project
description:
    - "This module links nodes in a GNS3 project on the GNS3 server."
options:
    project_name:
        description:
            - The name of the project containing the nodes to link.
        required: true
        type: str
    links:
        description:
            - Optional list of explicit link definitions.
        required: false
        type: list
"""

EXAMPLES = """
"""
from gns3fy import Project, Link
from ansible.module_utils.gns3_client import gns3_server


def _link_key(source_node_id, source_adapter, source_port, target_node_id, target_adapter, target_port):
    return tuple(
        sorted(
            [
                (source_node_id, source_adapter, source_port),
                (target_node_id, target_adapter, target_port),
            ]
        )
    )


def _project_link_keys(project):
    keys = set()

    for existing_link in getattr(project, "links", []) or []:
        nodes = existing_link.get("nodes", []) if isinstance(existing_link, dict) else getattr(existing_link, "nodes", [])

        if len(nodes) != 2:
            continue

        first = nodes[0]
        second = nodes[1]

        first_node_id = first.get("node_id") if isinstance(first, dict) else getattr(first, "node_id", None)
        first_adapter = first.get("adapter_number", 0) if isinstance(first, dict) else getattr(first, "adapter_number", 0)
        first_port = first.get("port_number", 0) if isinstance(first, dict) else getattr(first, "port_number", 0)

        second_node_id = second.get("node_id") if isinstance(second, dict) else getattr(second, "node_id", None)
        second_adapter = second.get("adapter_number", 0) if isinstance(second, dict) else getattr(second, "adapter_number", 0)
        second_port = second.get("port_number", 0) if isinstance(second, dict) else getattr(second, "port_number", 0)

        keys.add(
            _link_key(
                first_node_id,
                first_adapter,
                first_port,
                second_node_id,
                second_adapter,
                second_port,
            )
        )

    return keys

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
        }
    )

    project_name = module.params["project_name"]
    links = module.params["links"]

    try:
        project = Project(name=project_name, connector=gns3_server)
        project.get()
        existing_link_keys = _project_link_keys(project)

        created_links = []

        if links:
            node_by_name = {node.name: node for node in project.nodes}

            for link_definition in links:
                source_node = node_by_name.get(link_definition["source_node"])
                target_node = node_by_name.get(link_definition["target_node"])

                if source_node is None or target_node is None:
                    module.fail_json(
                        msg=(
                            "Unable to create link because one or more nodes were not found: "
                            f"{link_definition['source_node']} -> {link_definition['target_node']}"
                        )
                    )

                source_adapter = link_definition.get("source_adapter", 0)
                source_port = link_definition.get("source_port", 0)
                target_adapter = link_definition.get("target_adapter", 0)
                target_port = link_definition.get("target_port", 0)
                link_key = _link_key(
                    source_node.node_id,
                    source_adapter,
                    source_port,
                    target_node.node_id,
                    target_adapter,
                    target_port,
                )

                if link_key in existing_link_keys:
                    continue

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
                created_links.append({"source": source_node.name, "target": target_node.name})
        else:
            if len(project.nodes) < 2:
                module.fail_json(msg="Project must contain at least two nodes before linking them.")

            switch_node = project.nodes[0]
            cloud_node = project.nodes[1]
            link_key = _link_key(switch_node.node_id, 0, 0, cloud_node.node_id, 0, 0)

            if link_key not in existing_link_keys:
                link = Link(
                    project_id=project.project_id,
                    nodes=[
                        {"node_id": switch_node.node_id, "adapter_number": 0, "port_number": 0},
                        {"node_id": cloud_node.node_id, "adapter_number": 0, "port_number": 0},
                    ],
                    connector=gns3_server,
                )
                link.create()
                existing_link_keys.add(link_key)
                created_links.append({"source": switch_node.name, "target": cloud_node.name})

        module.exit_json(
            changed=bool(created_links),
            project_name=project_name,
            linked_nodes=created_links,
        )

    except Exception as exc:
        module.fail_json(msg=str(exc))

def main():
    run_module()

if __name__ == "__main__":
    main()