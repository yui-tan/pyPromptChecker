# pyPromptChecker  

A tiny script for AI images created by AUTOMATIC/stable-diffusion-webui  
For my personal use  
Supported only PNG files
  
Screenshot
![](https://user-images.githubusercontent.com/121333129/256966356-cf675550-ef93-4f28-a31b-a69db097d4be.png)

Tiled diffusion status screenshot
![](https://user-images.githubusercontent.com/121333129/256966357-6c778370-2153-45d7-b128-cdcd659f3ee7.png)

Additional and Hires status screenshot
![](https://user-images.githubusercontent.com/121333129/256966358-6fc1eac8-af03-4e2e-9ef4-0e5451f249c9.png)

ControlNet status screenshot
![](https://user-images.githubusercontent.com/121333129/256966359-3030c47e-13ea-49b7-b3fa-a2845b2818fc.png)

Regional prompter status screenshot
![](https://user-images.githubusercontent.com/121333129/257389785-b9b65076-ec8d-4fea-a9ed-fddebfde641f.png)
# Requirements  

- Python 3.x
- PyQt6
- pypng  

# Howto

````
cd /path/to/pyPromptChecker
pip3 install -e.
mikkumiku

usage: mikkumiku [-h] [-a | -f [FILEPATH ...] | -d DIRECTORY]

Script for extracting and formatting PNG chunks.
If no options are specified, the script will open a file choose dialog.
All options are mutually exclusive.

options:
  -h, --help            show this help message and exit
  -a, --ask              open directory choose dialog.
  -f [FILEPATH ...], --filepath [FILEPATH ...]
                              send path to files.
  -d DIRECTORY, --directory DIRECTORY
                              send path to directory.
````

# ToDo

 - [x] Refactoring and clean up
 - [x] Add support for hires.fix status  
 - [x] Add support for ControlNet status  
 - [x] Add support for Additional Networks status  
 - [x] Add support for Regional Prompter status  
 - [x] Coding Export JSON (All Images) function  
 - [x] Coding Reselect files function
 - [x] Change initial behaviour by argument
 - [x] Various hardcodings into a Configuration Class
 - [x] Make it installable using pip
 - [ ] Add support for import JSON
 - [ ] Get marry to Miku
