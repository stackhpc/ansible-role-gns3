#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule

from ansible.module_utils.gns3_parser import GNS3AParser
from ansible.module_utils.gns3_client import gns3_server


DOCUMENTATION = r"""
---
module: gns3_template_upload

short_description: Upload GNS3 templates from gns3a files

description:
  - Parses GNS3 appliance files and uploads missing templates.
  - Existing templates are skipped.

options:
  templates:
    description:
      - List of .gns3a template files.
    required: true
    type: list
    elements: str
"""


EXAMPLES = """
"""

def get_template_name(template):
    """
    Handle both gns3fy objects and API dictionaries.
    """

    if hasattr(template, "name"):
        return template.name

    if isinstance(template, dict):
        return template.get("name")

    return None


def run_module():

    module = AnsibleModule(
        argument_spec={
            "templates": {
                "type": "list",
                "elements": "str",
                "required": True,
            },
        },
        supports_check_mode=True,
    )

    template_files = module.params["templates"]

    try:

        existing_templates = gns3_server.get_templates()

        existing_template_names = {
            get_template_name(template)
            for template in existing_templates
        }

        uploaded_templates = []

        for template_file in template_files:

            parser = GNS3AParser(template_file)

            payload = parser.build_template_payload()

            template_name = payload["name"]

            if template_name in existing_template_names:
                continue


            if not module.check_mode:

                url = f"{gns3_server.base_url}/templates"

                gns3_server.http_call(
                    "post",
                    url,
                    json_data=payload
                )


            existing_template_names.add(template_name)
            uploaded_templates.append(template_name)


        module.exit_json(
            changed=bool(uploaded_templates),
            uploaded_templates=uploaded_templates,
        )


    except Exception as exc:

        module.fail_json(
            msg=str(exc)
        )


def main():
    run_module()


if __name__ == "__main__":
    main()