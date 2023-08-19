# -*- coding: utf-8 -*-

import os
import configparser

config = {'ModelList': '',
          'Favourites': '',
          'MaxWindowWidth': 1024,
          'MaxWindowHeight': 920,
          'PixmapSize': 350,
          'RegionalPrompterPixmapSize': 500,
          'JsonExport': True,
          'JsonSingle': 'parameters.json',
          'JsonMultiple': 'all_parameters.json',
          'ModelHashExtractor': False,
          'LoraAddNet': True,
          'HiresCfg': True,
          'TiledDiffusion': True,
          'ControlNet': True,
          'RegionalPrompter': True,
          'ErrorList': 1,
          'IgnoreIfDataIsNotEmbedded': False,
          'TargetChunkIndex': 1,
          'MoveDelete': False,
          'UseCopyInsteadOfMove': True,
          'AskIfDelete': True,
          'AskIfClearTrashBin': True,
          'TabNavigation': False,
          'TabSearch': False
          }

ini_config = configparser.ConfigParser()
ini_config.read('config.ini', encoding='utf-8')
ini_section = [['Location', 'ModelList', 'Favourites'],
               ['Window', 'MaxWindowWidth', 'MaxWindowHeight'],
               ['Pixmap', 'PixmapSize', 'RegionalPrompterPixmapSize'],
               ['Features', 'ModelHashExtractor'],
               ['Features', 'JsonExport', 'JsonSingle', 'JsonMultiple'],
               ['Features', 'MoveDelete', 'UseCopyInsteadOfMove', 'AskIfDelete', 'AskIfClearTrashBin'],
               ['Features', 'TabNavigation', 'TabSearch'],
               ['Tab', 'LoraAddNet', 'HiresCfg', 'TiledDiffusion', 'ControlNet', 'RegionalPrompter'],
               ['Ignore', 'IgnoreIfDataIsNotEmbedded'],
               ['Debug', 'ErrorList'],
               ['PNG', 'TargetChunkIndex']
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
            elif section == 'Window' or section == 'Pixmap':
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
            elif option == "JsonSingle" or option == 'JsonMultiple':
                value = ini_config[section].get(option)
                if value:
                    config[option] = value
            else:
                try:
                    value = ini_config[section].getboolean(option)
                except ValueError:
                    continue
                config[option] = value

if not config.get('ModelList'):
    config['ModelList'] = os.path.join(os.path.abspath(''), 'model_list.csv')
