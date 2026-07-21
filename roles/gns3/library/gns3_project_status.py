#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: gns3_project_status
short_description: Checks if a GNS3 project exists on the GNS3 server
description:
    - "This module checks if a GNS3 project exists on the GNS3 server."
options:
    project_name:
        description:
            - The name of the project to check.
        required: true
        type: str
"""

EXAMPLES = """
"""
from ansible.module_utils.gns3_client import gns3_server
from gns3fy import Project


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            project_name=dict(type="str", required=True)
        )
    )

    project_name = module.params["project_name"]

    try:
        project = Project(name=project_name, connector=gns3_server)
        project.get()

        module.exit_json(
            changed=False,
            exists=True
        )

    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            module.exit_json(
                changed=False,
                exists=False
            )
        else:
            module.fail_json(msg=str(e))

def main():
    run_module()


if __name__ == "__main__":
    main()