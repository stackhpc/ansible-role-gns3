# ansible module to print node summary

#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from gns3fy import Project
from ansible.module_utils.gns3_client import gns3_server


DOCUMENTATION = """
---
module: debug_node

short_description: return node summary
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
        },
        supports_check_mode=True,
    )

    project_name = module.params["project_name"]

    try:
        project = Project(name=project_name, connector=gns3_server)
        project.get()

        nodes_summary = project.nodes_summary(is_print=False)

        module.exit_json(
            changed=False,
            nodes_summary=nodes_summary or [],
        )

    except Exception as e:
        module.fail_json(msg=str(e))    

def main():
    run_module()


if __name__ == "__main__":
    main()