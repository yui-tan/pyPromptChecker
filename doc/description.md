<!-- TOC -->
* [Descriptions about features](#descriptions-about-features)
  * [config.ini](#configini)
  * [Model_list.csv](#model_listcsv)
  * [JSON export](#json-export)
  * [Model hash extractor](#model-hash-extractor)
  * [Move/Delete feature](#movedelete-feature)
  * [Tab navigation](#tab-navigation)
* [Screenshots](#screenshots)
<!-- TOC -->
# Descriptions about features
The authors themselves had no idea it would be so feature-rich.  
## config.ini
## Model_list.csv
- ### Overview  
  'model_list.csv' is a file what script locate model name from hash values.  
  This file can be place anywhere of your choice.  
  But if you move from initial place, declare new path in 'config.ini'  
  And you **can not** rename this file from 'model_list.csv'

- ### Format  
  The structure of 'model_list.csv' is as following:  

  | Display name | Model hash | Entire SHA256 hash | Filename | Model type |
  |:------------:|:----------:|:------------------:|:--------:|:----------:|

  - The display name in the first column is the same as the filename if freshly output from the script.
  - But there is no issue to  edit it according to your preference.
  - The each of value must be comma-separated and the values must not be enclosed in quotation marks.  
  - The script uses the first and second columns for searching.  
  - Therefore, you can delete columns from the third onward or add something in columns from the sixth onward without any issues.  

- ### Related values in 'config.ini'
  - [Location] section, "ModelList" option
  - If this parameter is unset, the program will search in the same directory as 'config.ini' file by default.
  - If you relocate 'model_list.csv', **you must** declare the new path by setting this parameter.

## JSON export
- ### Overview
- ### related values in 'config.ini'
## Model hash extractor
- ### Overview
- ### Related values in 'config.ini'
  - ***Deprecated***
  - [Features] section, "ModelHashExtractor" option
## Move/Delete feature
- ### Overview
  - Favourite button: Move/copy image to favourite directory.
  - Move to button: Move/copy image to any directory.
  - Delete button: Delete[^1] image file.

- ### Related values in 'config.ini'
  - ### [Location] section ###
    - **"Favourites" option*** (Filepath)  
      Set an absolute directory path here to gather your favourite images.  
      However, if you leave this value blank or enter a non-existent directory path,  
      the favourite button will still appear, but this features won't be available.
  - ### [Features] section ###
    - **"MoveDelete" option** (Boolean)  
      If set to True, 3 buttons will be shown beneath the image.
    - **"UseCopyInsteadOfMove" option** (Boolean)   
      If set to True, this scripts will copy file instead of moving it.  
      *But this setting is not affected to 'Delete' feature.*
    - **"AskIfDelete" option** (Boolean)  
      If set to True, confirmation dialog will be shown when the delete button is pressed.
    - **"AskIfClearTrashBin" option[^2]** (Boolean)   
      If set to True, confirmation dialog will be shown the script exits,   
      asking if delete all files within the TrashBin directory.  
      
## Tab navigation
- ### Overview
- ### Tab navigation
- ### Related values in 'config.ini'

# Screenshots
- ### Main screen
- ### Highres fix and Dynamic thresholding
- ### Lora and Add network
- ### Tiled diffusion
- ### Controlnet
- ### Regional prompter
- ### Region control in Tiled diffusion
- ### Image view
- ### Thumbnail tab navigation


 [^1]:Pressing the delete button will not actually perform the deletion:instead, the file will be moved to TrashBin directory (/pyPromptChecker/.trash).  
 The actual deletion of files occurs when the script exits.
 [^2]:For fail-safe, it is highly recommended to set 'Ture' for 'AskIfClearTrashBin'.  
  It might be a bit bothersome but even if the script crashes, image files will remain in '/pyPromptChecker/.trash'.  
  Additionally, even if you accidentally delete image files, the script should protect your files if you press 'cancel'
