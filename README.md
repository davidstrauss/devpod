# DevPod, A FOSS .devcontainer

A support framework for using `.devcontainer` on Linux desktops. Let's start
with Buildah + Podman + Builder, but the project is open to contributions for
other IDE integrations.

## On Fedora Silverblue

### Setup

1. Install GNOME Builder:

       flatpak install flathub org.gnome.Builder

### Usage

1. In the CLI, change to the parent directory of `.devcontainer`.
1. Run the utility (which will *delete* any container with the same name as your project directory):

       devpod build

