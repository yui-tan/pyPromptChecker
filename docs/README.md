# pyPromptChecker
A small script designed for analyzing AI-generated images created by AUTOMATIC/stable-diffusion-webui.  
It extracts incomprehensible strings embedded within image files, formatting them into human-readable.  
The formatted data can be exported as JSON and subsequently imported from the JSON output.  
Additionally, the script offers in-data search and basic file management functionalities.  
All of these features are accessible even without AUTOMATIC/stable-diffusion-webui.


# Screenshots
![Main](https://user-images.githubusercontent.com/121333129/270104343-eebf6863-d429-4233-ac82-24ff9d041aab.png)

More screenshots [here.](description.md#screenshots)

# Features

- Extract creation data, formatting and display it.
- Any number of files can be processed simultaneously (Tested up to 1500 files).
- Image file move and delete with single click.
- JSON export and import.
- Make List of model hash from .safetensors and .ckpt files.
- Tab navigation with filename or thumbnails.
- Search with various conditions.

See more details [here.](description.md)


# Requirements  
### ~~pyPromptChecker binary edition no longer has any requirements.~~ 
I decided to give up distribute binary editions.  
Because of quite difficult to avoid false positives of Windows Defender.  
If you want to continue using you need to install at least python 3.x 
- Python 3.x
- pillow (PIL)
- pypng
- PyQt6
- pyqtdarktheme

As follows for interrogate features.
- onnxruntime
- numpy
- opencv-python
- huggingface_hub

# Installation
### ~~pyPromptChecker binary edition (for Linux and Windows users)~~   
~~1. Download the binary packages from the 'Releases'.~~  
~~2. Extract pyPromptChecker directory to any location of your choice.~~  
~~3. Optionally, desktop files for enable drag-and-drop functionality.~~  
~~4. Execute pyPromptChecker by double-click.~~ 

### pyPromptChecker source code edition

For Linux
````bash
git clone https://github.com/yui-tan/pyPromptChecker
cd pyPromptChecker/install
./install.sh
````
For Windows
1. Make sure you've got Python 3.x hanging around. 
2. Download the packages from the 'Releases' or code > download ZIP.
3. Extract the packages to a location of your choice as 'pyPromptChecker'.
4. Run pyPromptChecker/install/install.bat file.
5. Don't miss a single word of the words that pop up on the screen, before going wild in the comments
# Usage
### Source code edition
```bash
mikkumiku -a, --ask  
# Open directory choose dialog.
mikkumiku -f [FILEPATH ...], --filepath [FILEPATH ...]  
# Send file or directory paths to the script.
```
# Roadmap
 - [x] Tab navigation with thumbnails
 - [x] Listview
 - [x] Diff mode
 - [x] Filtering and searching tabs various conditions
 - [x] Add support for other image file formats
    - [x] jpeg
    - [x] webp
 - [x] Add support for import JSON
 - [ ] Automated LoRa creation
    - [x] Positive prompt export to txt files.
    - [x] Implement interrogate feature.
    - [ ] Import configure from files.
    - [ ] Linking sd-scripts.
 - [ ] ~~Export Data to Stable-Diffusion-Webui via API~~
 - [ ] Get marry to Miku

 # Author
 ### Yui-tan / Yuiyui
 Nutjob who loves Hatsune Miku.  
 napier2.718281828@gmail.com  
 https://civitai.com/user/Yui_tan  
 https://chichi-pui.com/users/yuiyui20170927

 # Licence
This script created under [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).
