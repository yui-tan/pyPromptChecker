#!/bin/bash

# Check if the current directory is "install"
if [[ $(basename $(pwd)) != "install" ]]; then
    echo "This script should be executed in the 'pyPromptChecker/install' directory."
    exit 1
fi

cd ..

# Check if the current directory is "pyPromptChecker"
if [[ $(basename $(pwd)) != "pyPromptChecker" ]]; then
    echo "This script should be executed in the 'pyPromptChecker/install' directory."
    exit 1
fi

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
  echo "Python 3 is not installed."
  exit 1
fi

# Create and activate the virtual environment
if [[ ! -d "venv" ]]; then
    echo "Installing venv..."
    python3 -m venv venv
fi

echo "activating venv..."
source venv/bin/activate

pip install --upgrade pip

# Install pyPromptChecker into venv
echo "Installing pyPromptChecker..."
pip3 install -e.

# Making .sh file and .desktop file
echo "Making files..."
mkdir sh

path_to_venv=$(pwd)"/venv/bin/activate"
path_to_icon=$(pwd)"/pyPromptChecker/icon/icon.png"
command[0]="/bin/bash -c 'source $path_to_venv && mikkumiku \"\$@\"' bash"
command[1]="/bin/bash -c \"source $path_to_venv && mikkumiku --ask\""
command_name[0]="mikkumiku"
command_name[1]="folder_picker"

for i in 0 1
do
  {
    echo -e "[Desktop Entry]"
    echo -e "Name=pyPromptChecker"
    echo -e "Exec=${command[i]}"
    echo -e "Path=$(pwd)"
    echo -e "Comment=A tiny script for AI images"
    echo -e "Terminal=false"
    echo -e "Icon=${path_to_icon}"
    echo -e "Type=Application"
  } >> sh/${command_name[i]}.desktop
done

# Explanation
echo "Now Installation is finished."
echo "In a new directory 'PyPromptChecker/sh', two files have been created."
echo "The following are the two files:"
echo
echo "mikkumiku.desktop:"
echo "When you run this file, a file selection dialog will appear,"
echo "and once a file is selected, processing will begin."
echo "This is same as running command 'mikkumiku'"
echo
echo "folder_picker.desktop:"
echo "When you run this file, a directory selection dialog will appear,"
echo "and once a directory is selected, processing will begin."
echo "This is same as running command 'mikkumiku --ask'"
echo

exit 0