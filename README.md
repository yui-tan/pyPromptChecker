# pyPromptChecker

A tiny script for AI images created by AUTOMATIC/stable-diffusion-webui  
Supported only PNG files
  
- ## Main Screenshot  
![Main](https://github.com/yui-tan/pyPromptChecker/assets/121333129/a0c86d10-563f-44a2-bf9f-cfc207fd262f)
- ## Hires.fix and CFG fix  
![Hires_cfg](https://github.com/yui-tan/pyPromptChecker/assets/121333129/e3ee643e-847f-4f76-a1a5-5b3c96c6598f)
- ## Lora and Additional networks  
![Lora_Addnet](https://github.com/yui-tan/pyPromptChecker/assets/121333129/41159dca-3577-441d-9fe2-bca32c6fd129)
- ## Controlnet  
![Controlnet](https://github.com/yui-tan/pyPromptChecker/assets/121333129/cb9bdcb8-49fa-46c5-9bac-547e80e992f7)
- ## Tiled diffusion  
![Tiled_diffusion](https://github.com/yui-tan/pyPromptChecker/assets/121333129/38a9387d-d663-40db-92d8-6ea39954c43a)
- ## Regional prompter  
![Regional_prompter](https://github.com/yui-tan/pyPromptChecker/assets/121333129/fe0c201c-09a2-4ae3-b59c-b2ff36ab7a28)
  
# Requirements  

- ### **Python 3.x**
- PyQt6
- pypng  

# Supported
- Stable Diffusion Webui
  - Hires.fix
  - Dynamic Thresholding (CFG fix) extension
  - Add Network extension
  - ControlNet extension
  - Tiled diffusion extension
  - Regional prompter extension
  

- Image format
  - PNG
# Howto
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

# ToDo

 - [x] Refactoring and clean up
 - [x] Add support for hires.fix status  
 - [x] Add support for ControlNet status  
 - [x] Add support for Additional Networks status  
 - [x] Add support for Regional Prompter status  
 - [x] Coding Export JSON (All Images) function  
 - [x] Coding Reselect files function
 - [x] Change initial behaviour by argument
 - [x] Various hard codings into a Configuration Class
 - [x] Make it installable using pip
 - [ ] Export JSON not only single and all but selected image
 - [ ] Add support for import JSON
 - [ ] Make it import data into Stable-Diffusion-Webui via API
 - [ ] Filtering main tabs various conditions
 - [ ] Be able to move and delete PNG images by button
 - [ ] Windows exe format (very low-priority)
 - [ ] Get marry to Miku
