import yaml

# Returns
def get_config(container_compose_path, project_path, workspace_path, service_name):
    with open(container_compose_path, "r") as container_compose_fp:
        container_compose_config = yaml.load(container_compose_fp, Loader=yaml.FullLoader)

    for service_name, service in container_compose_config["services"].items():
        # @TODO: Either add support for the verbose syntax or switch to a library.
        # https://docs.docker.com/compose/compose-file/compose-file-v3/#volumes
        for volume in service["volumes"]:
            (from_path, to_path, *mount_opts) = volume.split(':')
            # A match on the workspace path means this is the "head" container.
            if to_path == workspace_path:
                container_compose_config["services"][service_name]["volumes"].append("{}:/devpodworkspace:z".format(project_path))

    return container_compose_config
