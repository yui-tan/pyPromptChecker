import os
import configparser


class Configure:
    def __init__(self):
        path = os.path.abspath('')
        filepath = os.path.join(path, 'model_list.csv')
        self.config = {'ModelList': filepath,
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
                       'TargetChunkIndex': 1}

        self.ini_load('../../config.ini')

    def ini_load(self, filepath):
        ini_config = configparser.ConfigParser()
        ini_config.read('config.ini')
        ini_section = [['Location', 'ModelList'],
                       ['Window', 'MaxWindowWidth', 'MaxWindowHeight'],
                       ['Pixmap', 'PixmapSize', 'RegionalPrompterPixmapSize'],
                       ['JSON', 'JsonSingle', 'JsonMultiple'],
                       ['Tab', 'Lora', 'hiresOthers', 'TiledDiffusion', 'ControlNet', 'RegionalPrompter'],
                       ['Ignore', 'IgnoreIfDataIsNotEmbedded'],
                       ['Debug', 'ErrorList'],
                       ['PNG', 'TargetChunkIndex']
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
                    elif section == 'Tab':
                        try:
                            value = ini_config[section].getboolean(option)
                        except ValueError:
                            continue
                        self.config[option] = value
                    elif section == 'Location':
                        value = ini_config[section].get(option)
                        if os.path.exists(value):
                            self.config[option] = value
                    elif section == 'Ignore':
                        try:
                            value = ini_config[section].getboolean(option)
                        except ValueError:
                            continue
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
