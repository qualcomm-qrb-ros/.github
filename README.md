# QRB ROS Build Workflow
This repository contains the ROS build workflow for the [QRB ROS](https://github.com/qualcomm-qrb-ros) project. It is used to build the QRB ROS packages and their dependencies.

## Usage
To use this workflow, you need to call this workflow by using the `use` keyword in your workflow file. For example:
```yaml
jobs:
  ros-build:
    uses: qualcomm-qrb-ros/.github/.github/workflows/ubuntu-build.yml@ubuntu-build
    with:
        # List of repositories to checkout, e.g. "owner/repo1 owner/repo2"
        dependencies:

        # Colcon build arguments, e.g. --cmake-args -DCMAKE_BUILD_TYPE=Release
        colcon_args:

        # ROS2 distribution to use, e.g. humble, jazzy
        ros-distro: jazzy

        # List of apt packages to install, e.g. "python3-pip python3-rosdep"
        apt-packages:
```

### Inputs `dependencies`
List of repositories to checkout, e.g. "owner/repo1 owner/repo2".
This parameter is primarily used for packages cannot be installed by `rosdep` or `apt`.

### Inputs `colcon_args`
Colcon build arguments, e.g. `--cmake-args -DCMAKE_BUILD_TYPE=Release`.

### Inputs `ros-distro`
ROS2 distribution to use, e.g. `humble`, `jazzy`.

### Inputs `apt-packages`
List of apt packages to install, e.g. `python3-pip python3-rosdep