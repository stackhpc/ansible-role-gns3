#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project
from ansible.module_utils.gns3_client import gns3_server


DOCUMENTATION = """
---
module: gns3_node_info

short_description: Retrieve information about a node in a GNS3 project.

options:
  project_name:
    type: str
    required: true

  node_name:
    type: str
    required: true
"""


def run_module():

    module = AnsibleModule(
        argument_spec={
            "project_name": {
                "type": "str",
                "required": True,
            },
            "node_name": {
                "type": "str",
                "required": True,
            },
        },
        supports_check_mode=True,
    )

    project_name = module.params["project_name"]
    node_name = module.params["node_name"]

    try:

        project = Project(
            name=project_name,
            connector=gns3_server,
        )

        project.get()

        # Find right node
        node = project.get_node(name=node_name)

        if node is None:
            node = next(
                (
                    candidate
                    for candidate in project.nodes
                    if node_name in candidate.name
                ),
                None,
            )

        if node is None:
            node = next(
                (
                    candidate
                    for candidate in project.nodes
                    if candidate.name != "Cloud" and getattr(candidate, "console", None) is not None
                ),
                None,
            )

        if node is None:
            module.fail_json(
                msg=f"Node '{node_name}' not found."
            )

        node.get()

        module.exit_json(
            changed=False,
            node_name=node.name,
            node_id=node.node_id,
            console_port=node.console,
            console_host=node.console_host,
            status=node.status,
        )

    except Exception as exc:
        module.fail_json(msg=str(exc))


def main():
    run_module()


if __name__ == "__main__":
    main()