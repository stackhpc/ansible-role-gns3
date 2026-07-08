#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: gns3_delete_project
short_description: Deletes a GNS3 project
description:
    - "This module deletes a GNS3 project on the GNS3 server."
options:
    project_name:
        description:
            - The name of the project to delete.
        required: true
        type: str
"""

EXAMPLES = """
"""

from ansible.module_utils.gns3_client import gns3_server
from gns3fy import Project

def run_module():
    module = AnsibleModule(
        argument_spec={
            "project_name": {
                "type": "str",
                "required": True
            }
        }
    )

    project_name = module.params["project_name"]

    try:
        project = Project(name=project_name, connector=gns3_server)

        project.get()

        project.delete()

        module.exit_json(
            changed=True,
            project_name=project.name,
            status=project.status
        )

    except Exception as e:
        module.fail_json(msg=str(e))

def main():
    run_module()

if __name__ == "__main__":
    main()