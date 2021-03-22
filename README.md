# DevPod: Rootless, FOSS .DevContainer Tooling

A support framework for using `.devcontainer` on Linux desktops. Let's start
with Buildah + Podman + Builder, but the project is open to contributions for
other IDE integrations.

## Example Project

**This example assumes a working Podman installation, which exists out of the box on [Fedora Silverblue](https://silverblue.fedoraproject.org/) but is also available on [many distributions and platforms](https://podman.io/getting-started/installation).**

1. Install this utility:

       pip install devpod

1. Clone [Microsoft's PHP sample repository](https://github.com/microsoft/vscode-remote-try-php) and make it the working directory:

       git clone https://github.com/microsoft/vscode-remote-try-php.git
       cd vscode-remote-try-php/

1. In `.devcontainer/devcontainer.json`, uncomment the `postCreateCommand` directive and ensure there's a comma at the end of the line [if not yet fixed](https://github.com/microsoft/vscode-remote-try-php/pull/9).

    ![Uncomment postCreateCommand](https://github.com/davidstrauss/devpod/blob/main/screenshots/devcontainer_json.png?raw=true)

1. Build the container and launch:

       devpod run --launch

    ![Building and launching the container](https://github.com/davidstrauss/devpod/blob/main/screenshots/devpod_run_launch.png?raw=true)

1. Edit `index.php` in your IDE and reload the page in your Browser to see changes.

    ![Showing index.php in the IDE](https://github.com/davidstrauss/devpod/blob/main/screenshots/index_php.png?raw=true)
    ![Showing index.php in the browser](https://github.com/davidstrauss/devpod/blob/main/screenshots/browser.png?raw=true)

## Basic Setup and Usage

### Setup

**These instructions should work out of the box on Fedora Silverblue 33+.** 

1. Install this utility (choosing an alternative to `pip` like `pipx` if you like):

       pip install devpod

### Usage

1. In the CLI, change to the parent directory of `.devcontainer` for your project.
1. Run the utility (which will *delete* any container with the same name as your project directory):

       devpod run --launch  # Will open a browser to forwarded ports.

### Troubleshooting

* The `launch` command should list any open ports at the end of the process,
   but you can also list them using Podman directly:
   
       podman port --latest

## Developing DevPod Itself

### Installing the CLI Tool from Local Builds

**These instructions have been tested on Fedora Silverblue 33 but are probably adaptable to other setups.**

1. Install Python package tooling (using a [Toolbox](https://docs.fedoraproject.org/en-US/fedora-silverblue/toolbox/) if desired):

       sudo dnf install poetry pipx

1. Clone the DevPod code and make it your working directory.
1. Build and (re)install the utility for global use:

       rm -rf dist/ && poetry build && pipx install --force dist/devpod-*.tar.gz

1. The `devpod` command should now be globally available to your user, even
   outside of any Toolbox.

## Project Philosophy

* Supplement -- don't interfere with -- people's existing development setups.
    * Tread lightly. Things that work for users today shouldn't break.
    * Exit gracefully. We shouldn't leave junk scattered on a user's system.
* Build working glue before refined architecture.
    * It's unclear how some things will best fit together until more features are integrated (and this entire space matures).
* Only take on only a handful of mature runtime dependencies.
    * Yes, there are many Python wrappers for container tools, but we will avoid additional layers that might be hard to debug.
    * This space is moving so quickly that many wrappers aren't keeping up.
    * It's convenient to have `devpod` installed at the user/system level, so let's drag along fewer dependencies (`pipx` notwithstanding).
* Invest in compatibility over spec conformance and custom tests.
    * Testing by automating standing up official example -- and some community -- repositories.
    * Custom tests still make sense below the integration level.

## Resources

* [.devcontainer Reference Documentation](https://code.visualstudio.com/docs/remote/devcontainerjson-reference)
* [Podman Commands Documentation](http://docs.podman.io/en/latest/Commands.html)
* Rootless Podman
    * [Shortcomings of Rootless Podman](https://github.com/containers/podman/blob/master/rootless.md)
    * [Volumes and Rootless Podman](https://blog.christophersmart.com/2021/01/31/volumes-and-rootless-podman/)
    * [User Namespaces, SELinux, and Rootless Containers](https://www.redhat.com/sysadmin/user-namespaces-selinux-rootless-containers)
* [From Docker Compose to Kubernetes with Podman](https://www.redhat.com/sysadmin/compose-kubernetes-podman)
* [Podman Compose](https://github.com/containers/podman-compose)

## Reference Repositories

These are repositories currently used for interoperability testing.

* [Basic project](https://github.com/microsoft/vscode-remote-try-php)
* [Compose-based project](https://github.com/valenvb/vscode-devcontainer-wordpress)
