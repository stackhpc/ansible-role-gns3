#!/usr/bin/python
# -*- coding: utf-8 -*-

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.gns3_client import gns3_server
from gns3fy import Project


def run_module():
    module = AnsibleModule(
        argument_spec={
            "project_name": {
                "type": "str",
                "required": True,
            },
            "node_type": {
                "type": "str",
                "required": True,
            }
        },
        supports_check_mode=True,
    )

    project_name = module.params["project_name"]
    # remove spaces from the node_type parameter to avoid issues with matching
    node_type = module.params["node_type"].replace(" ", "")
    try:
        project = Project(name=project_name, connector=gns3_server)
        project.get()

        nodes_summary = project.nodes_summary(is_print=False)
        switch_node_present = False
        cloud_node_present = False
        # check if node type is in the nodes summary

        for node in nodes_summary:
            node_name = node[0].strip()

            if node_name == node_type:
                switch_node_present = True

            if node_name == "Cloud":
                cloud_node_present = True

        module.exit_json(
            changed=False,
            switch_node_present=bool(switch_node_present),
            cloud_node_present=bool(cloud_node_present),
            node_type=node_type,
        )

    except Exception as e:
        if "404" in str(e) or "not found" in str(e).lower():
            module.exit_json(
                changed=False,
                switch_node_present=False,
                cloud_node_present=False,
            )
        else:
            module.fail_json(msg=str(e))


def main():
    run_module()


if __name__ == "__main__":
    main()