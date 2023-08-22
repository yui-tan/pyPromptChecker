# About
  - Supported image formats
    - png
    - jpeg
  - Supported web-ui extension
    - Basic information
    - Hires.fix
    - Dynamic threshoulding (CFG fix)
    - Add networks
    - Tiled diffusion
    - ControlNet
    - Regional Prompter
    
# Descriptions about features
The authors themselves had no idea it would be so feature-rich.  
## Config.ini
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
  - ### [Location] section ###
    - **"ModelList" option** (Directory path)  
      If this parameter is unset, the script will search in the same directory as 'config.ini' file by default.  
      If relocate 'model_list.csv', **you must** declare the new path by setting this parameter.

## JSON export
- ### Overview
  - Export creation data as JSON formatted data.
  - It can now be found in the menu > Export JSON
    
- ### Related values in 'config.ini'
  - ### [Features] section ###
    - **"JsonExport" option** (Boolean)  
      This option now only mean toggle shown/not shown "Export Json" buttons.
    - **"JsonSingle" option** (Strings)  
      This option is setting for exported JSONs (single file) default Name. Setting whatever you want.  
      If 'JsonSingle=filename' is set, the image file name will be set as default.
    - **"JsonMultiple" option** (Strings)  
      This option is setting for exported JSONs (all file) default Name. Setting whatever you want.  
      If 'JsonMultiple=directory' is set, the first image's directory name will be set as default.
    - **"JsonSelected" option** (Strings)  
      This option is setting for exported JSONs (selected) default Name. Setting whatever you want.  
      If 'JsonSelected=selected' is set, the first image's name + "-and-so-on" will be set as default. maybe...
      
## Model hash extractor
- ### Overview
  - The feature that extract model hash from your own model files and create 'model_list.csv' file or append data to it.
  - Now it can be find in menu > model hash extractor.
  - Depends on number of files, it requires huge mount of time and memories[^1].
  
- ### Related values in 'config.ini'
  - ### [Features] section ###
    - **"ModelHashExtractor" option** (Boolean)  
    *Deprecated*

## Move/Delete feature
- ### Overview
  - Favourite button: Move/copy image to favourite directory.
  - Move to button: Move/copy image to any directory.
  - Delete button: Delete[^2] image file.

- ### Related values in 'config.ini'
  - ### [Location] section ###
    - **"Favourites" option** (Filepath)  
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
    - **"AskIfClearTrashBin" option[^3]** (Boolean)   
      If set to True, confirmation dialog will be shown the script exits,   
      asking if delete all files within the TrashBin directory.  
      
## Tab navigation
- ### Overview
- ### Tab navigation
- ### Related values in 'config.ini'

# Screenshots
- ### Main screen
![main_screen](https://user-images.githubusercontent.com/121333129/261905025-69283ba2-ac9d-4b92-944e-bd187ce2abc2.png)
![main_screen_2](https://user-images.githubusercontent.com/121333129/261905120-ad750fda-e8b3-458d-b03a-a3d97eff7bfb.png)
- ### Highres fix and Dynamic thresholding
![hires_cfg](https://user-images.githubusercontent.com/121333129/261911834-178e9918-3f3a-4434-90e9-6f8ce7c33bde.png)
- ### Lora and Add network
![Lora_addnet](https://user-images.githubusercontent.com/121333129/261911864-42731ce9-b9de-48b2-8f70-b538be7a56e8.png)
- ### Tiled diffusion
![tiled_diffusion](https://user-images.githubusercontent.com/121333129/261911802-a571772a-3e53-404b-b09b-4b9dc576add9.png)
- ### Controlnet
![controlnet](https://user-images.githubusercontent.com/121333129/261911911-cb4219a6-0270-4381-ba59-b333a91d7456.png)
- ### Regional prompter
![regional_prompter](https://user-images.githubusercontent.com/121333129/261966851-dff68376-70e2-4fe9-a24b-399c120e0f60.png)
![regional_prompter_2](https://user-images.githubusercontent.com/121333129/261966907-8cb29c70-1c9a-4601-98cc-8c771e5cf608.png)
- ### Region control in Tiled diffusion
- ### Image view
![image_view](https://user-images.githubusercontent.com/121333129/261905238-2aee6631-de09-4a1a-9052-a61bba7f348a.png)
- ### Thumbnail tab navigation
![Thumbnail](https://user-images.githubusercontent.com/121333129/261905360-cae29606-c641-4400-9c5d-64bb5251d8af.png)

 [^1]:It may require more than 32 GiB of memory (not VRAM).  
For example, in my case, it took 20 minutes to process 62 files, and the memory usage went up to 29 GiB.
 [^2]:Pressing the delete button will not actually perform the deletion:instead, the file will be moved to TrashBin directory (/pyPromptChecker/.trash).  
 The actual deletion of files occurs when the script exits.
 [^3]:For fail-safe, it is highly recommended to set 'Ture' for 'AskIfClearTrashBin'.  
  It might be a bit bothersome but even if the script crashes, image files will remain in '/pyPromptChecker/.trash'.  
  Additionally, even if you accidentally delete image files, the script should protect your files if you press 'cancel'
