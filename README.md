# pyPromptChecker
"pyPromptChecker" is a script designed for analyzing AI-generated images created by AUTOMATIC/stable-diffusion-webui.  
It extracts incomprehensible strings embedded within image files, formatting them into human-readable.  
The formatted data can be exported as JSON and subsequently imported from the JSON output.  
Additionally, the script offers in-data search and basic file management functionalities.  
All of these features are accessible even without AUTOMATIC/stable-diffusion-webui.


# Screenshots
![Main](https://github.com/yui-tan/pyPromptChecker/assets/121333129/a0c86d10-563f-44a2-bf9f-cfc207fd262f)

More screenshots here.

# Features

- Extract creation data, formatting and display it.
- Any number of files can be processed simultaneously (Tested up to 1500 files).
- Image file move and delete with single click.
- JSON export and import.
- Make List of model hash from .safetensors and .ckpt files.
- Tab navigation with filename or thumbnails.
- Search with various conditions.

See more details here. 


# Requirements  
### pyPromptChecker binary edition no longer has any requirements.  
But old-fashioned versions still has requirements as follows.
- Python 3.x
- pypng
- PyQt6

# Installation
### pyPromptChecker binary edition (both Linux and Windows)  
1. Download the binary packages from the 'Releases'.
2. Extract pyPromptChecker-bin directory anywhere you want.
3. Double click pyPromptChecker.exe / pyPromptChecker.
4. Provide shortcuts / .desktop file for drag-and-drop if you want.
5. Done

### Old-fashioned pyPromptChecker

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

# Roadmap

 - [ ] Filtering and searching tabs various conditions
 - [ ] Add support for other image file formats
    - [ ] jpeg
    - [ ] webp
    - [ ] heif
 - [ ] Add support for import JSON
 - [ ] Export Data to Stable-Diffusion-Webui via API
 - [ ] Get marry to Miku

 # Author
 ### Yui-tan
 Nutjob who loves Hatsune Miku.  
 napier2.718281828@gmail.com  
 https://civitai.com/user/Yui_tan  
 https://chichi-pui.com/users/yuiyui20170927

 # Licence
This script created under [GPLv3](https://www.gnu.org/licenses/gpl-3.0.html).

 # How to use Model hash extractor

1. Open the 'config.ini' and change the value of 'ModelHashExtractor' from False to True.
2. Run pyPromptChecker and click the 'M' button located at the bottom right.
3. Select a directory containing the files you want to process.
4. Highly recommended value of 'Model Hash Extractor' from True back to False for fool proof.

Depending on the number of files, this feature may take a significant amount of time to process.  
Additionally, it may require more than 32 GiB of memory (not VRAM).  
For example, in my case, it took 20 minutes to process 62 files, and the memory usage went up to 29 GiB.  

If you edited 'model_list.csv', I recommend relocate 'model_list.csv' before runnning this feature.  
This feature works in append mode, but The outputs is slightly different format than before.

# About 'model_list.csv'

- This script is required to locate model names.  
- The structure is following:
  
| Display name | Model hash | Entire SHA256 hash | Filename | Model type |
|:---:|:---:|:---:|:---:|:---:|

- The display name in the first column is the same as the filename if freshly output from the script.
- But there is no issue to  edit it according to your preference.  
- The each of value must be comma-separated and the values must not be enclosed in quotation marks.  
- The script uses the first and second columns for searching.  
- Therefore, you can delete columns from the third onward or add something in columns from the sixth onward without any issues.  
