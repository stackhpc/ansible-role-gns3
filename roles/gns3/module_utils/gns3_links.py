#!/usr/bin/python
# -*- coding: utf-8 -*-


def link_key(
    source_node_id,
    source_adapter,
    source_port,
    target_node_id,
    target_adapter,
    target_port,
):
    """
    Creates a unique key for a GNS3 link.
    Links are bidirectional, so node ordering does not matter.
    """

    return tuple(
        sorted(
            [
                (
                    source_node_id,
                    source_adapter,
                    source_port,
                ),
                (
                    target_node_id,
                    target_adapter,
                    target_port,
                ),
            ]
        )
    )


def project_link_keys(project):
    """
    Extract existing links from a GNS3 project and
    convert them into comparable link keys.
    """

    keys = set()

    for existing_link in getattr(project, "links", []) or []:

        nodes = (
            existing_link.get("nodes", [])
            if isinstance(existing_link, dict)
            else getattr(existing_link, "nodes", [])
        )

        if len(nodes) != 2:
            continue


        first, second = nodes


        first_node_id = (
            first.get("node_id")
            if isinstance(first, dict)
            else getattr(first, "node_id", None)
        )

        first_adapter = (
            first.get("adapter_number", 0)
            if isinstance(first, dict)
            else getattr(first, "adapter_number", 0)
        )

        first_port = (
            first.get("port_number", 0)
            if isinstance(first, dict)
            else getattr(first, "port_number", 0)
        )


        second_node_id = (
            second.get("node_id")
            if isinstance(second, dict)
            else getattr(second, "node_id", None)
        )

        second_adapter = (
            second.get("adapter_number", 0)
            if isinstance(second, dict)
            else getattr(second, "adapter_number", 0)
        )

        second_port = (
            second.get("port_number", 0)
            if isinstance(second, dict)
            else getattr(second, "port_number", 0)
        )


        keys.add(
            link_key(
                first_node_id,
                first_adapter,
                first_port,
                second_node_id,
                second_adapter,
                second_port,
            )
        )


    return keys



def resolve_node(node_by_name, node_name):
    """
    Resolve a node name.
    Handles differences like:

    DellOS10N3248TE
    Dell OS10 N3248TE
    """

    node = node_by_name.get(node_name)

    if node is not None:
        return node


    compact_name = node_name.replace(" ", "")


    if compact_name != node_name:

        for name, node in node_by_name.items():

            if name.replace(" ", "") == compact_name:
                return node


    return None