#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project
from ansible.module_utils.gns3_client import gns3_server


DOCUMENTATION = """
---
module: start_nodes

short_description: Start nodes in a GNS3 project

description:
    - Starts all nodes in a GNS3 project.

options:
    project_name:
        description:
            - Name of the GNS3 project.
        required: true
        type: str

"""


def run_module():

    module = AnsibleModule(
        argument_spec={
            "project_name": {
                "type": "str",
                "required": True,
            }
        },
        supports_check_mode=True,
    )

    project_name = module.params["project_name"]

    try:

        project = Project(name=project_name, connector=gns3_server)
        project.get()
        for node in project.nodes:
            node.start()

        module.exit_json(
            changed=True,
            msg=f"All nodes in project '{project_name}' have been started.",
        )
        
    except Exception as e:
        module.fail_json(msg=str(e))

def main():
    run_module()

if __name__ == "__main__":
    main()