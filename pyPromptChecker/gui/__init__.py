# -*- coding: utf-8 -*-

import os
import configparser

config = {}

module_filepath = os.path.abspath(os.path.dirname(__file__))
package_filepath = os.path.dirname(module_filepath)
installed_filepath = os.path.dirname(package_filepath)
config_file = os.path.join(installed_filepath, 'config.ini')

ini_config = configparser.ConfigParser()
ini_config.read(config_file, encoding='utf-8')
ini_section = [['Location', 'ModelList', 'Favourites'],
               ['Window', 'MaxWindowWidth', 'MaxWindowHeight', 'AlwaysStartWithDarkMode', 'AlwaysOpenBy'],
               ['Pixmap', 'PixmapSize', 'RegionalPrompterPixmapSize', 'ThumbnailPixmapSize', 'ListViewPixmapSize'],
               ['Features', 'SubDirectoryDepth', 'OpenWithShortenedWindow', 'UsesNumberAsTabName'],
               ['Features', 'ModelListSearchApplyLora', 'ModelListSearchApplyTi'],
               ['Features', 'JsonExport', 'JsonSingle', 'JsonMultiple', 'JsonSelected'],
               ['Features', 'MoveDelete', 'UseCopyInsteadOfMove', 'AskIfDelete', 'AskIfClearTrashBin'],
               ['Features', 'TabNavigation', 'TabNavigationWithThumbnails', 'TabNavigationWithListview'],
               ['Features', 'TabNavigationMinimumTabs', 'ThumbnailTabBar', 'ThumbnailTabBarVertical', 'HideNormalTabBar'],
               ['Features', 'TabSearch', 'HideNotMatchedTabs'],
               ['Tab', 'HiresExtras', 'CFG', 'LoraAddNet', 'TiledDiffusion', 'ControlNet', 'RegionalPrompter'],
               ['Ignore', 'IgnoreIfDataIsNotEmbedded'],
               ['Debug', 'ErrorList'],
               ]

for ini in ini_section:
    section = ini[0]
    for option in ini[1:]:
        if ini_config.has_option(section, option):
            if section == 'Location':
                value = ini_config[section].get(option)
                if '\\' in value:
                    value = value.replace('\\\\', '\\')
                if os.path.exists(value):
                    config[option] = value
            elif section == 'Window' and option == 'AlwaysOpenBy':
                value = ini_config[section].get(option)
                config[option] = value
            elif (section == 'Window' and not option == 'AlwaysStartWithDarkMode') or section == 'Pixmap':
                try:
                    value = ini_config[section].getint(option)
                except ValueError:
                    continue
                if section == 'Window' and value > 479:
                    config[option] = value
                elif section == 'Pixmap' and 99 < value < 801:
                    config[option] = value
            elif section == 'Debug':
                value = ini_config[section].get(option)
                if value == 'AlwaysOff':
                    int_value = 0
                elif value == 'AlwaysOn':
                    int_value = 2
                else:
                    int_value = 1
                config[option] = int_value
            elif section == 'PNG':
                if ini_config.has_option(section, 'Accept'):
                    try:
                        value = ini_config[section].getint(option)
                    except ValueError:
                        continue
                    config[option] = value
            elif option == "JsonSingle" or option == 'JsonMultiple' or option == 'JsonSelected':
                value = ini_config[section].get(option)
                if value:
                    config[option] = value
            elif option == 'TabNavigationMinimumTabs' or option == 'SubDirectoryDepth':
                try:
                    value = ini_config[section].getint(option)
                except ValueError:
                    continue
                config[option] = value
            else:
                try:
                    value = ini_config[section].getboolean(option)
                except ValueError:
                    continue
                config[option] = value

if not config.get('ModelList'):
    config['ModelList'] = os.path.join(installed_filepath, 'model_list.csv')

estimated_icon_path = os.path.abspath(os.path.join(package_filepath, 'icon/icon.png'))
config['IconPath'] = estimated_icon_path
config['Installed'] = installed_filepath
