import pathlib
import string
import json
import os
import subprocess
import logging
import sys
import configparser
import click
import yaml
import tempfile

from devpod import devcontainer, containercompose

def init_logger():
    # From https://stackoverflow.com/a/46065766
    logger = logging.getLogger()
    h = logging.StreamHandler(sys.stdout)
    h.flush = sys.stdout.flush
    logger.addHandler(h)
    return logger


def run_command(cmd, logger):
    logger.info("Command: {}".format(cmd))
    try:
        cproc = subprocess.run(cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        print("Attempted command: {}".format(e.cmd))
        print(
            "Non-zero return code {}: {}".format(e.returncode, e.stderr.decode("utf-8"))
        )
        exit(1)
    output = cproc.stdout.strip()
    logger.debug("Output: {}".format(output))
    return output

@click.group()
@click.option("--debug/--no-debug", default=False)
def cli(debug):
    logger = logging.getLogger()
    if debug:
        click.echo("Debug output on.")
        logger.setLevel(logging.DEBUG)


@cli.command()
@click.option("--launch/--no-launch", default=False)
def run(launch=False):
    logger = init_logger()
    # Establish script paths (relative to this script).
    base_path = os.path.dirname(os.path.realpath(__file__))
    buildconfig_tpl_path = os.path.join(base_path, "buildconfig.template")
    buildconfig_tpl_str = pathlib.Path(buildconfig_tpl_path).read_text()
    buildconfig_tpl = string.Template(buildconfig_tpl_str)

    # Establish project paths (relative to working directory).
    project_path = os.getcwd()  # Make configurable?
    project_name = pathlib.Path(project_path).name.strip()
    devc_dir = os.path.join(project_path, ".devcontainer")

    # .devcontainer paths are all relative to the .devcontainer directory.
    os.chdir(devc_dir)

    # Determine .devcontainer configuration.
    click.echo("Loading configuration for project directory: {}".format(project_path))
    devc_config = devcontainer.get_config(devc_dir)

    workspace_path = "/workspace"
    if "workspaceFolder" in devc_config:
        workspace_path = devc_config["workspaceFolder"]

    composed = False
    if "dockerComposeFile" in devc_config:
        composed = True

        # Start running the new pod.
        click.echo(
            "Removing existing pod if present: {}".format(project_name)
        )
        run_command(
            [
                "podman",
                "pod",
                "rm",
                "--ignore",
                "--force",
                project_name
            ],
            logger,
        )

        click.echo(
            "Processing Container/Docker Compose file: {}".format(devc_config["dockerComposeFile"])
        )
        compose_config = containercompose.get_config(devc_config["dockerComposeFile"], project_path, workspace_path, devc_config["service"])
        logger.debug("Modified YAML: {}".format(compose_config))
        with tempfile.NamedTemporaryFile(mode="w+", prefix="container-compose-",suffix=".yml") as compose_config_fp:
            logger.debug("Modified YAML path: {}".format(compose_config_fp.name))
            yaml.dump(compose_config, compose_config_fp)
            compose_config_fp.flush()
            click.echo(
                "Building and running new pod: {}".format(project_name)
            )
            compose_file = os.path.join(devc_dir, devc_config["dockerComposeFile"])
            run_command(
                [
                    "podman-compose",
                    "-p",
                    project_name,
                    "--transform_policy=1podfw",
                    "--file={}".format(compose_config_fp.name),
                    "up",
                    "--detach",
                ],
                logger,
            )
    else:
        # @TODO: Skip this if the project specifies an image directly.
        # Build the new container.
        container_build_filename = devc_config["build"]["dockerfile"]
        container_build_path = os.path.join(devc_dir, container_build_filename)
        click.echo("Building container: {}".format(project_name))
        pb_output = run_command(
            ["podman", "build", "-t", project_name, "-f", container_build_path, "."], logger
        )  # --build-arg
        image_id = pb_output.splitlines()[-1].decode("utf-8").strip()

        # Start running the new container.
        click.echo(
            "Running new container (replacing existing if present)...".format(project_name)
        )
        run_command(["podman", "stop", "--ignore", project_name], logger)
        run_command(["podman", "rm", "--ignore", project_name], logger)
        # @TODO: Consider adding the :U option to --volume once supported in releases of Podman.
        run_command(
            [
                "podman",
                "run",
                "-P",
                "-d",
                "--volume={}:{}:z".format(project_path, workspace_path),
                "--name={}".format(project_name),
                image_id,
            ],
            logger,
        )

    # Run post-creation commands.
    container_shell = "/bin/sh"
    cmd_container_name = project_name

    # If this is composed, match the workspaceFolder to mounts to determine the primary container.
    if composed:
        click.echo("Searching containers in pod for workspace directory: {}".format(workspace_path))
        pod_data_json = run_command(
            [
                "podman",
                "pod",
                "inspect",
                project_name
            ],
            logger,
        )
        pod_data = json.loads(pod_data_json)
        for container_attr in pod_data["Containers"]:
            container_name = container_attr["Name"]
            container_data_json = run_command(
                [
                    "podman",
                    "container",
                    "inspect",
                    container_name
                ],
                logger,
            )
            container_data = json.loads(container_data_json)
            for mount_attr in container_data[0]["Mounts"]:
                # @TODO: Compare these more robustly.
                if mount_attr["Destination"] == workspace_path:
                    cmd_container_name = container_name
        click.echo("Found matching mount for primary workspace in container: {}".format(cmd_container_name))

    # Prefer the specified shell, or fall back to /bin/sh?
    # if "settings" in devc_config and "terminal.integrated.shell.linux" in devc_config["settings"]:
    #    container_shell = devc_config["settings"]["terminal.integrated.shell.linux"]
    if "postCreateCommand" in devc_config:
        click.echo(
            "Running postCreateCommand: {}".format(devc_config["postCreateCommand"])
        )
        run_command(
            [
                "podman",
                "exec",
                "--workdir=/devpodworkspace",
                cmd_container_name,
                container_shell,
                "-c",
                devc_config["postCreateCommand"],
            ],
            logger,
        )
    else:
        click.echo("No postCreateCommand found. Project files are only in the bindmount location: {}".format(workspace_path))

    # Export Builder configuration.
    click.echo("Exporting GNOME Builder configuration: .buildconfig")
    bldcfg = buildconfig_tpl.substitute(
        containerid=project_name, homedir=pathlib.Path.home(), project=project_name
    )
    config = configparser.ConfigParser()
    config.read_string(bldcfg)
    with open(".buildconfig", "w") as configfile:
        config.write(configfile, space_around_delimiters=False)

    # List forwarded ports.
    ports = (
        run_command(["podman", "port", cmd_container_name], logger).decode("utf-8").strip()
    )
    if len(ports) > 0:
        click.echo(
            "Container {} has the following ports forwarded:".format(project_name)
        )
        ports_linked = ports.replace("0.0.0.0:", "http://localhost:")
        click.echo(ports_linked)
        if launch:
            click.echo("Launching forwarded ports as URLs.")
            for line in ports_linked.splitlines():
                parts = line.split("->")
                url = parts[1].strip()
                click.launch(url)
        else:
            click.echo(
                "Click links above to launch them your default browser (or use --launch)."
            )
    else:
        click.echo(
            "Container {} successfully created, but no ports are forwarded.".format(
                project_name
            )
        )
        if launch:
            click.echo("Need at least one port forwarded to launch in browser.")
