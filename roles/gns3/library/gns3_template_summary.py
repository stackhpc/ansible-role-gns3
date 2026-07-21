#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gns3_client import gns3_server
from gns3fy import Project


def run_module():
    module = AnsibleModule(
        argument_spec={
            "project_name": {"type": "str", "required": True},
            "gns3_switch_model": {"type": "str", "required": True},
        },
        supports_check_mode=True,
    )

    project_name = module.params["project_name"]
    gns3_switch_model = module.params["gns3_switch_model"]

    try:
        project = Project(name=project_name, connector=gns3_server)
        project.get()

        uploaded_templates = gns3_server.get_templates()

        # loop through the uploaded templates and check if any of them match the gns3_switch_model
        exists = any(
            template.get("name") == gns3_switch_model for template in uploaded_templates
        )

        module.exit_json(
            changed=False,
            exists=exists,
            templates=uploaded_templates,
        )

    except Exception as e:
        module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == "__main__":
    main()