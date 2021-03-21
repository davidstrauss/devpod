# DevPod, A FOSS .devcontainer

A support framework for using `.devcontainer` on Linux desktops. Let's start
with Buildah + Podman + Builder, but the project is open to contributions for
other IDE integrations.

## Basic Setup and Usage

### Setup

1. Install GNOME Builder (example uses Flatpak, but a normal package works, too):

       flatpak install flathub org.gnome.Builder

1. This project isn't yet on PyPI, so follow the "local builds" instructions
   under "developing."

### Usage

1. In the CLI, change to the parent directory of `.devcontainer` for your project.
1. Run the utility (which will *delete* any container with the same name as your project directory):

       devpod launch

1. The `launch` command should list any open ports at the end of the process,
   but you can also list them using Podman directly:
   
       podman port --latest

1. Connect using a Web browser. For example, if the output of `port` is
   `80/tcp -> 0.0.0.0:12345`, then open a browser to `http://localhost:12345/`.

## Developing of DevPod Itself

### Installing the CLI Tool from Local Builds

1. Install Python package tooling (using a [Toolbox](https://docs.fedoraproject.org/en-US/fedora-silverblue/toolbox/) if desired):

       sudo dnf install poetry pipx

1. Clone this project's code and make it your working directory.
1. Build and install for global use:
       
       poetry build
       pipx install install dist/devpod-$VERSION.tar.gz

1. The `devpod` command should now be globally available to your user, even
   outside of any Toolbox.

## Resources

* [.devcontainer Reference Documentation](https://code.visualstudio.com/docs/remote/devcontainerjson-reference)
* [Podman Commands Documentation](http://docs.podman.io/en/latest/Commands.html)
* Rootless Podman
    * [Shortcomings of Rootless Podman](https://github.com/containers/podman/blob/master/rootless.md)
    * [Volumes and Rootless Podman](https://blog.christophersmart.com/2021/01/31/volumes-and-rootless-podman/)
    * [User Namespaces, SELinux, and Rootless Containers](https://www.redhat.com/sysadmin/user-namespaces-selinux-rootless-containers)
