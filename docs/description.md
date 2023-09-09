# Supported formats and Webui extensions
  - Supported image formats
    - png
    - jpeg
    - webp
  - Supported web-ui extension
    - Basic information
    - Hires.fix
    - Extras
    - Dynamic thresholding (CFG fix)
    - Auto CFG
    - CFG scheduling
    - Add networks
    - Tiled diffusion
    - ControlNet
    - Regional Prompter
    
# Descriptions about features
The authors themselves had no idea it would be so feature-rich.  
## Key bindings
Here are some common key bindings.  
The key bindings for each feature, see the feature description.
- ### Basic
  - **Ctrl + Tab :** Toggle expand / shorten window
  - **Ctrl + D :** Toggle dark/light theme
  - **Ctrl + Q :** Quit
- ### Tab control
  - **Ctrl + O :** Add tabs
  - **Ctrl + N :** Replace tabs
- ### Button control
  - **Alt + P :** Copy positive
  - **Alt + N :** Copy negative
  - **Alt + S :** Copy seed
  - **Alt + E :** Open menu
## Config.ini
- ### Overview
  The behaviour of the script is configured in 'config.ini'.  
  It will work with the default values even without it, but you may want to create your own favourite settings.  
  The description of each configuration value is given here, but see below for a description of the individual features.
- ### [Window] section
  - **"MaxWindowWidth" option** (Integer)
  - **"MaxWindowHeight" option** (Integer)   
Sets the maximum size of the window.  
Not very useful in practice.  
I'll address this soon, but for now, please treat it as a placeholder.
  - **"AlwaysStartWithDarkMode" option** (Boolean)  
If this setting set to True, always turn on dark mode at startup.  
Default value is **False**.
- ### [Pixmap] section
  - **"PixmapSize" option** (Integer)  
Sets the size of the pixmap.  
Unlike window size, this one is always adhered to.  
The long sides of the image are scaled up/down to this size.  
This value has a significant effect on the size of the window itself.  
The default value is **350**.
  - **"RegionalPrompterPixmapSize" option** (Integer)  
Set the size of pixmap of regional prompter tab.  
This value also has the same overview as the previous 'PixmapSize' option.  
The default value is **500**.
  - **"ThumbnailPixmapSize" option** (Integer)  
Set the pixmap size of thumbnail mode.  
The default value is **150**.
  - **"ListViewPixmapSize" option** (Integer)  
Set the pixmap size of Listview mode.  
The default value is **200**.
- ### [Features] section
  - **"SubDirectoryDepth" option** (Integer)  
Sets how many levels of subdirectories are searched when a directory path is passed to the script.  
The default value is **0**, meaning it will only search for files inside the specified directory.  
If large number is specified, the script may not function properly due to the large number of files.  
The author has confirmed that it can manage up to 10,000 files somehow.
  - **"UsesNumberAsTabName" option** (Boolean)  
If set to True, the number is used instead of the filename as tab title.  
Default value is **False**
  - **"OpenWithShortenedWindow" option** (Boolean)  
If set to True, the extension tabs at the bottom of the window will start in a hidden state.  
Default value is **False**.
  - **"ModelListSearchApplyLora" option** (Boolean)
  - **"ModelListSearchApplyTi" option** (Boolean)  
If this is set to True,  
the same process performed on 'Model Hash' will also be applied to LoRa and textual inversion.  
In other words, you can freely set the display names for LoRa and textual inversion using 'Model_list.csv'.  
Default value is **False**.

- ### [Tab] section
  - **"HiresExtras" option** (Boolean)
  - **"CFG" option** (Boolean)
  - **"LoraAddnet" option** (Boolean)
  - **"TiledDiffusion" option** (Boolean)
  - **"ControlNet" option** (Boolean)
  - **"RegionalPrompter" option** (Boolean)  
Setting show/hide tab at the bottom of the window.  
If set to false, the script don't create tab even if the image uses applicable extension.  
Default value is **True** all.
- ### [Ignore] section
  - **"IgnoreIfDataIsNotEmbedded" option** (Boolean)  
Setting behaviour if image has no embedded data.  
If set to True, the script does not create image's tab.  
If set to False, it creates image's tab with minimum information.  
(e.g. filepath, filename, etc.)  
Default value is **False**.
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
  - Each of value must be comma-separated and the values must not be enclosed in quotation marks.  
  - The script uses the first and second columns for searching.  
  - Therefore, you can delete columns from the third onward or add something in columns from the sixth onward without any issues.  

- ### Model hash extractor  
  The feature that extract model hash from your own model files and create 'model_list.csv' file or append data to it.  
Now it can be find in menu > model hash extractor.  
Depends on number of files, it requires huge mount of time and memories[^2].


- ### Related values in 'config.ini'
  - ### [Location] section ###
    - **"ModelList" option** (Directory path)  
       If this parameter is unset, the program will search in the same directory as 'config.ini' file by default.  
       If you relocate 'model_list.csv', **you must** declare the new path by setting this parameter.

## JSON import and export
- ### Overview
  Export creation data as JSON formatted data.  
  It can now be found in the menu > Export JSON
  'Import JSON' feature is not intended to import any JSON other than what it has exported[^1].
  If you use 'import JSON' feature, all tabs will be replaced.

- ### Key bindings
  - **Alt + T :** Export JSON of present image file 
  - **Alt + A :** Export JSON of all image file 
  - **Alt + L :** Export JSON of selected image file
    
- ### Related values in 'config.ini'
  - ### [Features] section ###
    - **"JsonExport" option** (Boolean)  
      This option now only mean toggle shown/not shown "Export Json" buttons.  
      Default value is **False**.
    - **"JsonSingle" option** (Strings)  
      This option is setting for exported JSONs (single file) default Name. Setting whatever you want.  
      If 'JsonSingle=filename' is set, the image file name will be set as default.
    - **"JsonMultiple" option** (Strings)  
      This option is setting for exported JSONs (all file) default Name. Setting whatever you want.  
      If 'JsonMultiple=directory' is set, the first image's directory name will be set as default.
    - **"JsonSelected" option** (Strings)  
      This option is setting for exported JSONs (selected) default Name. Setting whatever you want.  
      If 'JsonSelected=selected' is set, the first image's name + "-and-so-on" will be set as default. maybe...

## Move/Delete feature
- ### Overview  
  Provides simple file management functions.  
Images can be moved to a pre-registered favourite directory,  
moved to an arbitrary directory and can be deleted.  
If enable this feature, three buttons appear beneath pixmap.
  - Favourite button: Move/copy image to favourite directory.
  - Move to button: Move/copy image to any directory.
  - Delete button: Delete[^3] image file.

- ### Key bindings
  - **Alt + F :** Add favourite
  - **Alt + M :** Move to
  - **Delete :** Delete image

- ### Related values in 'config.ini'
  - ### [Location] section ###
    - **"Favourites" option** (Directory path)  
      Set an absolute directory path here to gather your favourite images.  
      However, if you leave this value blank or enter a non-existent directory path,  
      the favourite button will still appear, but this features won't be available.
  - ### [Features] section ###
    - **"MoveDelete" option** (Boolean)  
If set to True, 3 buttons will be shown beneath the image.  
Default value is **True**.
    - **"UseCopyInsteadOfMove" option** (Boolean)   
If set to True, this scripts will copy file instead of moving it.  
Default value is **True**.  
*But this setting is not affect to 'Delete' feature.*
    - **"AskIfDelete" option** (Boolean)  
If set to True, confirmation dialog will be shown when the delete button is pressed.  
Default value is **True**.
    - **"AskIfClearTrashBin" option[^4]** (Boolean)   
If set to True, confirmation dialog will be shown the script exits,   
Asking if delete all files within the TrashBin directory.  
Default value is **True**.
## Tab navigation ##
![tab_navigation](https://user-images.githubusercontent.com/121333129/263465639-d02bc716-bfe9-4940-a655-6f8cade02348.png)
- ### Overview ###
  This is provided to allow navigation between tabs when many tabs are generated.  
A combo box at the top of the window and a thumbnail window are provided.    
- ### Key bindings
    - **Ctrl + F :** Search
    - **Ctrl + T :** Open thumbnail window
    - **Ctrl + L :** Open listview window
- ### Related values in 'config.ini' ###  
  - ### [Features] section ###
    - **"TabNavigation" option** (Boolean)  
Toggle to enable or to disable tab navigation.  
Default value is **True**.
    - **"TabNavigationWithThumbnails" option** (Boolean)  
Toggle to enable or to disable thumbnail view.  
If set to True, thumbnail button appears next to 'Jump to' button, right top of the window.  
This setting has no meanings unless "TabNavigation" option is enable.  
Default value is **True**.
    - **"TabNavigationMinimumTabs" option** (Integer)  
Setting appear tab navigation when how many files are opens.   
This setting is meaningless unless both of the above settings are enabled.  
Default value is **2**
## Compare extension
![compare](https://user-images.githubusercontent.com/121333129/263465633-7bda6efe-f70a-445a-b1ae-2436b41a7e15.png)
- ### Overview ###
  If left click on bottom tab (e.g. Prompt, Tiled Diffusion, etc) appears menu with checkbox.  
  Check the checkbox to maintain the selected tab in the bottom, even when you switch tabs in the top.
# Screenshots
- ### Main screen
![main_screen](https://user-images.githubusercontent.com/121333129/261905025-69283ba2-ac9d-4b92-944e-bd187ce2abc2.png)
![main_screen_2](https://user-images.githubusercontent.com/121333129/261905120-ad750fda-e8b3-458d-b03a-a3d97eff7bfb.png)
- ### Highres fix and Extras
![hires_extras](https://user-images.githubusercontent.com/121333129/263465147-63e51453-50c6-4c5c-949a-0069dc0dd5b4.png)
- ### Lora and Add network
![Lora_addnet](https://user-images.githubusercontent.com/121333129/261911864-42731ce9-b9de-48b2-8f70-b538be7a56e8.png)   
- ### CFG  
![CFG](https://user-images.githubusercontent.com/121333129/263465167-0875b003-f0c2-4ed2-a876-f7bd7e9df138.png)
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

[^1]:But it would be interesting to try it out.
 [^2]:It may require more than 32 GiB of memory (not VRAM).  
For example, in my case, it took 20 minutes to process 62 files, and the memory usage went up to 29 GiB.
 [^3]:Pressing the delete button will not actually perform the deletion:instead, the file will be moved to TrashBin directory (/pyPromptChecker/.trash).  
 The actual deletion of files occurs when the script exits.
 [^4]:For fail-safe, it is highly recommended to set 'Ture' for 'AskIfClearTrashBin'.  
  It might be a bit bothersome but even if the script crashes, image files will remain in '/pyPromptChecker/.trash'.  
  Additionally, even if you accidentally delete image files, the script should protect your files if you press 'cancel'
