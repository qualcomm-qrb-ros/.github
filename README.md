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

This workflow use `rosdep` with the `--ignore-src` option to install dependencies, but skips those that are specified in `dependencies` input parameter.

>Note:
> When you specify a repository through the dependencies input parameter, you also need to list all of its required dependencies in the same parameter..

### Inputs `colcon_args`
Colcon build arguments, e.g. `--cmake-args -DCMAKE_BUILD_TYPE=Release`.

### Inputs `ros-distro`
ROS2 distribution to use, e.g. `humble`, `jazzy`.

### Inputs `apt-packages`
List of apt packages to install, e.g. `python3-pip python3-rosdep


## FAQ
### Packages could not have their rosdep keys resolved to system dependencies
```
ERROR: the following packages/stacks could not have their rosdep keys resolved
to system dependencies:
qrb_ros_transport_point_cloud2_type: Cannot locate rosdep definition for [lib_mem_dmabuf]
qrb_ros_transport_image_type: Cannot locate rosdep definition for [lib_mem_dmabuf]
Error: Process completed with exit code 1.
```

This is because the package depends on `qrb_ros_transport` and it was added to `dependencies` input parameter. But `qrb_ros_transport` depends on `lib_mem_dmabuf` which is not added.

#### Solution
Add `lib_mem_dmabuf` to `dependencies` input parameter.
```
    with:
      dependencies: "qualcomm-qrb-ros/qrb_ros_transport qualcomm-qrb-ros/lib_mem_dmabuf"
```