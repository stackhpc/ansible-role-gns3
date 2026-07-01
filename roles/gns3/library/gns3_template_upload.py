#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: Contributors to the Ansible project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from ansible.module_utils.basic import AnsibleModule

DOCUMENTATION = """
---
module: gns3_template_upload
short_description: Parses a .gns3a file and uploads the template to the GNS3 server
description:
    - "This module uploads given templates to the GNS3 server."
options:
    templates:
        description:
            - List of .gns3a template files to upload.
        required: true
        type: list
"""

EXAMPLES = """
"""

from ansible.module_utils.gns3_parser import GNS3AParser
from ansible.module_utils.gns3_client import gns3_server

def run_module():
    module = AnsibleModule(
        argument_spec={
            "templates": {
                "type": "list",
                "elements": "str",
                "required": False,
                "default": [],
            },
        }
    )

    templates = module.params["templates"]

    try:
        existing_template_names = {template.name for template in gns3_server.get_templates()}
        uploaded_templates = []

        for template_file in templates:
            payload = GNS3AParser(template_file).build_template_payload()

            if payload["name"] in existing_template_names:
                continue

            gns3_server.create_template(payload)
            existing_template_names.add(payload["name"])
            uploaded_templates.append(payload["name"])

        module.exit_json(
            changed=bool(uploaded_templates),
            uploaded_templates=uploaded_templates,
        )

    except Exception as exc:
        module.fail_json(msg=str(exc))

def main():
    run_module()

if __name__ == "__main__":
    main()