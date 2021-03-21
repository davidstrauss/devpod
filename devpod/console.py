import pathlib
import string
import json
import os
import subprocess
import logging
import sys
import configparser
import click


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

    # Determine container configuration.
    click.echo("Loading configuration for project directory: {}".format(project_path))
    devc_dir = os.path.join(os.getcwd(), ".devcontainer")
    devc_config_path = os.path.join(devc_dir, "devcontainer.json")
    devc_config_json = ""
    with open(devc_config_path, "r") as devc_config_fp:
        for line in devc_config_fp.readlines():
            if not line.strip().startswith("//"):
                devc_config_json += line + "\n"
    devc_config = json.loads(devc_config_json)

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
            "--volume={}:/workspace:z".format(project_path),
            "--name={}".format(project_name),
            image_id,
        ],
        logger,
    )

    # Run post-creation commands.
    container_shell = "/bin/sh"
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
                "--workdir=/workspace",
                project_name,
                container_shell,
                "-c",
                devc_config["postCreateCommand"],
            ],
            logger,
        )
    else:
        click.echo("No postCreateCommand found.")

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
        run_command(["podman", "port", project_name], logger).decode("utf-8").strip()
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
