import os
import configparser


class Configure:
    def __init__(self):
        path = os.path.abspath('../')
        filepath = os.path.join(path, 'model_list.csv')
        if not os.path.exists(filepath):
            path = os.path.abspath('')
            filepath = os.path.join(path, 'model_list.csv')
        ini_path = os.path.join(path,'config.ini')
        self.config = {'ModelList': filepath,
                       'Favourites': '',
                       'MaxWindowWidth': 1024,
                       'MaxWindowHeight': 920,
                       'PixmapSize': 350,
                       'RegionalPrompterPixmapSize': 500,
                       'JsonSingle': 'parameters.json',
                       'JsonMultiple': 'all_parameters.json',
                       'Lora': True,
                       'HiresOthers': True,
                       'TiledDiffusion': True,
                       'ControlNet': True,
                       'RegionalPrompter': True,
                       'ErrorList': 1,
                       'IgnoreIfDataIsNotEmbedded': False,
                       'TargetChunkIndex': 1,
                       'UseCopyInsteadOfMove': True,
                       'AskIfClearTrashBin': True}

        self.ini_load(ini_path)

    def ini_load(self, ini_path):
        ini_config = configparser.ConfigParser()
        ini_config.read(ini_path)
        ini_section = [['Location', 'ModelList', 'Favourites'],
                       ['Window', 'MaxWindowWidth', 'MaxWindowHeight'],
                       ['Pixmap', 'PixmapSize', 'RegionalPrompterPixmapSize'],
                       ['JSON', 'JsonSingle', 'JsonMultiple'],
                       ['Tab', 'Lora', 'HiresOthers', 'TiledDiffusion', 'ControlNet', 'RegionalPrompter'],
                       ['Ignore', 'IgnoreIfDataIsNotEmbedded'],
                       ['Debug', 'ErrorList'],
                       ['PNG', 'TargetChunkIndex'],
                       ['Warning', 'UseCopyInsteadOfMove', 'AskIfClearTrashBin']
                       ]
        for d1 in ini_section:
            section = d1[0]
            for option in d1[1:]:
                if ini_config.has_option(section, option):
                    if section == 'Window' or section == 'Pixmap':
                        try:
                            value = ini_config[section].getint(option)
                        except ValueError:
                            continue
                        if section == 'Window' and value > 479:
                            self.config[option] = value
                        elif section == 'Pixmap' and 99 < value < 801:
                            self.config[option] = value
                    elif section == 'Tab' or section == 'ignore' or section == 'Warning':
                        try:
                            value = ini_config[section].getboolean(option)
                        except ValueError:
                            continue
                        self.config[option] = value
                    elif section == 'Location':
                        value = ini_config[section].get(option)
                        if os.path.exists(value):
                            self.config[option] = value
                    elif section == 'Debug':
                        value = ini_config[section].get(option)
                        if value == 'AlwaysOff':
                            int_value = 0
                        elif value == 'AlwaysOn':
                            int_value = 2
                        else:
                            int_value = 1
                        self.config[option] = int_value
                    elif section == 'PNG':
                        if ini_config.has_option(section, 'Accept'):
                            try:
                                value = ini_config[section].getint(option)
                            except ValueError:
                                continue
                            self.config[option] = value
                    else:
                        value = ini_config[section].get(option)
                        self.config[option] = value

    def get_option(self, name):
        return self.config.get(name, None)
