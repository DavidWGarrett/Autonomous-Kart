#!/bin/bash

# Update and upgrade the system
echo "YOU NEED UBUNTU 24.04 - Updating and upgrading system..."
echo "THIS WILL TAKE A LONG TIME"
sudo apt update && sudo apt upgrade -y

# Install OpenSSH server
echo "Installing OpenSSH server..."
sudo apt install openssh-server -y
sudo systemctl start ssh
sudo systemctl enable ssh

# Configure locale settings
echo "Configuring locale settings..."
locale
sudo apt update && sudo apt install locales -y
sudo locale-gen en_US en_US.UTF-8
sudo update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8
export LANG=en_US.UTF-8
locale

# Install required dependencies
echo "Installing required dependencies..."
sudo apt install software-properties-common -y
sudo add-apt-repository universe -y

# Update and install curl
echo "Installing curl..."
sudo apt update && sudo apt install curl -y

# Add ROS repository key
echo "Adding ROS repository key..."
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# Add ROS repository
echo "Adding ROS repository..."
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Update and install ROS packages
echo "Updating package list and installing ROS..."
sudo apt update && sudo apt install ros-dev-tools -y
sudo apt update && sudo apt upgrade -y
sudo apt install ros-jazzy-desktop -y
sudo apt install ros-jazzy-rtabmap-ros -y

# Install ROS2 package for Oak-D Camera
echo "Installing ROS2 package for Oak-D Camera"
sudo apt install ros-jazzy-depthai-ros -y

# Install ROS2 package for navigation stack
echo "Installing ROS2 navigation stack"
sudo apt install ros-jazzy-navigation2 ros-jazzy-nav2-bringup -y

# Rosdep
echo "Installing Rosdep"
sudo rosdep init
rosdep update

# Install Colcon
echo "Install Colcon"
sudo apt install python3-colcon-common-extensions -y

# To avoid re-sourcing every time, add this to ~/.bashrc
echo "After installing ROS 2, source it every time you open a new terminal"
echo "source /opt/ros/jazzy/setup.bash" >> ~/.bashrc
source ~/.bashrc

# Install Python
echo "Installing Python"
sudo apt install -y python3 python3-pip python3-venv

# Install Git
echo "Installing Git"
sudo apt install git -y

# Install Vim
echo "Installing Vim"
sudo apt install vim vim-gtk3 -y
sudo apt install xclip xsel -y

# Enable GPIO setup
echo "Setting up GPIO access on Ubuntu 24.04"

echo "Setting up raspi-config"
sudo apt install raspi-config -y

# Update package lists
sudo apt update

# Install necessary GPIO dependencies
echo "Installing GPIO dependencies..."
sudo apt install -y python3-pip python3-gpiozero python3-rpi.gpio
sudo apt install -y gpiod libgpiod-dev python3-libgpiod

# Create gpio group if it doesn't exist
if ! getent group gpio > /dev/null; then
    echo "Creating gpio group..."
    sudo groupadd gpio
else
    echo "gpio group already exists"
fi

# Add the current user to the gpio group
echo "Adding $USER to gpio group..."
sudo usermod -aG gpio $USER

# Set correct permissions for GPIO access
echo "Setting permissions for GPIO devices..."
sudo chown root:gpio /dev/gpiomem /dev/gpiochip*
sudo chmod 660 /dev/gpiomem /dev/gpiochip*

# Create a udev rule for persistent permissions
echo "Creating udev rule for GPIO..."
sudo bash -c 'cat <<EOF > /etc/udev/rules.d/99-gpio.rules
SUBSYSTEM=="gpio*", GROUP="gpio", MODE="0660"
KERNEL=="gpiomem", GROUP="gpio", MODE="0660"
EOF'

# Reload udev rules
sudo udevadm control --reload-rules
sudo udevadm trigger

# Display GPIO chip information to verify setup
echo "Verifying GPIO setup..."
ls -l /dev/gpiochip*
gpiodetect
gpioinfo

# Check if permissions are applied correctly
echo "Checking GPIO permissions..."
ls -l /dev/gpiomem
ls -l /dev/gpiochip*

# Clone the ROS 2 workspace from GitHub
echo "Cloning the ROS 2 workspace from GitHub..."
cd ~
if [ -d "ros2_ws" ]; then
    echo "ros2_ws already exists, pulling latest changes..."
    cd ros2_ws
    git pull origin main
else
    git clone https://github.com/DavidWGarrett/Autonomous-Kart.git ros2_ws
    cd ros2_ws
fi

# Install dependencies
echo "Installing ROS 2 package dependencies..."
rosdep install --from-paths src --ignore-src -r -y

# Build the ROS 2 workspace
echo "Building the ROS 2 workspace..."
colcon build

# Source the workspace
echo "Sourcing the workspace..."
echo "source ~/ros2_ws/install/setup.bash" >> ~/.bashrc
source ~/.bashrc

echo "Setup complete! Please reboot your system for changes to apply."
