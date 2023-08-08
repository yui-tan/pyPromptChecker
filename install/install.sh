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
mkdir "sh"

path_to_venv=$(pwd)"/venv/bin/activate"
path_to_sh=$(pwd)"/sh"
path_to_icon=$(pwd)"/icon/icon.png"

echo -e "#!/bin/bash\nsource ${path_to_venv}\nmikkumiku --filepath \$*" >> "${path_to_sh}/drop_files.sh"
echo -e "#!/bin/bash\nsource ${path_to_venv}\nmikkumiku --directory \$*" >> "${path_to_sh}/drop_directory.sh"

chmod +x sh/*

command[0]="/bin/bash -c \"source $path_to_venv && mikkumiku\""
command[1]="/bin/bash -c \"source $path_to_venv && mikkumiku --ask\""
command[2]="${path_to_sh}/drop_files.sh"
command[3]="${path_to_sh}/drop_directory.sh"

command_name[0]="mikkumiku"
command_name[1]="folder_picker"
command_name[2]="drop_files"
command_name[3]="drop_directory"

for i in 0 1 2 3
do
  {
    echo -e "[Desktop Entry]"
    echo -e "Name=pyPromptChecker"
    echo -e "Exec=${command[i]}"
    echo -e "Comment=A tiny script for AI images"
    echo -e "Terminal=false"
    echo -e "Icon=${path_to_icon}"
    echo -e "Type=Application"
  } >> sh/${command_name[i]}.desktop
done

# Explanation
echo "Now Installation is finished."
echo "In a new directory 'PyPromptChecker/sh', six files have been created."
echo "The following are the six files:"
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
echo "drop_files.desktop:"
echo "you can start the processing by dragging and dropping a file onto this file."
echo "This is same as running command 'mikkumiku --filepath ...'"
echo
echo "drop_directories.desktop:"
echo "you can start the processing by dragging and dropping a directory onto this file."
echo "This is same as running command 'mikkumiku --directory ...'"
echo
echo "drop_files.sh"
echo "drop_directory.sh"
echo
echo "You can relocate those .desktop files"
echo "But DO NOT move or edit .sh files"
echo

exit 0