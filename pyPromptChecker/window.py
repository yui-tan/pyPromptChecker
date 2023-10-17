# -*- coding: utf-8 -*-
import sys
import random
import qdarktheme
from PyQt6.QtCore import QObject
from PyQt6.QtGui import QIcon

from gui.custom import *
from gui.dialog import *
from gui.listview import Listview
from gui.search import SearchWindow
from gui.tab import Tabview
from gui.thumbnail import ThumbnailView
from gui.viewer import *
from lib import *
from lora import *

DARK_THEME = config.get('AlwaysStartWithDarkMode', False)
MAIN_WINDOW = config.get('AlwaysOpenBy', 'tab').lower()
MODEL_LIST = config.get('ModelList', 'model_list.csv')
FAVOURITE = config.get('Favourites')
IGNORE_IMAGE = config.get('IgnoreIfDataIsNotEmbedded', False)
LORA_NAME = config.get('ModelListSearchApplyLora', False)
TI_NAME = config.get('ModelListSearchApplyTi', False)
ASK_CLEAR = config.get('AskIfClearTrashBin')
ASK_DELETE = config.get('AskIfDelete', True)
USE_MOVE = config.get('UseCopyInsteadOfMove', True)
SUBDIRECTORY_DEPTH = config.get('SubDirectoryDepth', 0)
ASK_WHEN_QUIT = config.get('AskWhenQuit', True)
ICON_PATH = config.get('IconPath')


class WindowController(QObject):
    def __init__(self, app: QApplication, filepaths: list):
        super().__init__()
        self.app = app
        self.filepaths = filepaths

        self.dark = DARK_THEME

        self.main_window = None
        self.thumbnail = None
        self.listview = None
        self.tabview = None
        self.interrogate = None
        self.image_view = None
        self.search_dialog = None

        self.models = []
        self.loaded_images = []

        self.applied_model = set()
        self.hidden_indexes = set()
        self.moved_indexes = set()
        self.deleted_indexes = set()
        self.matched_indexes = set()

        self.__init_class()
        self.app.aboutToQuit.connect(self.__obliterate)

    def __init_class(self):
        self.models = io.import_model_list(MODEL_LIST)
        self.__load_images()
        self.__init_main_window()

    def __clear_class(self):
        self.filepaths = []
        self.loaded_images = []
        self.applied_model.clear()
        self.hidden_indexes.clear()
        self.moved_indexes.clear()
        self.deleted_indexes.clear()
        self.matched_indexes.clear()

    def __load_images(self, filepath_list: list = None):
        filepaths = filepath_list if filepath_list is not None else self.filepaths
        image_indexes = 0 if not self.loaded_images else len(self.loaded_images)
        valid_total = len(filepaths)
        progress_bar = None

        if len(filepaths) > 5:
            progress_bar = ProgressDialog(self.main_window)
            progress_bar.setRange(0, len(filepaths))
            progress_bar.setLabelText('Extracting PNG Chunk...')

        for tuples in filepaths:
            filepath, filetype = tuples

            if filetype == 9:
                valid_total -= 1
                continue

            chunk_data, original_size = chunk_text_extractor(filepath, filetype)

            if not chunk_data and IGNORE_IMAGE:
                valid_total -= 1
                continue

            elif not original_size:
                valid_total -= 1
                continue

            parameters = ChunkData(chunk_data, filepath, filetype, original_size)
            parameters.init_class()

            if parameters.params.get('Positive') == 'This file has no embedded data' and IGNORE_IMAGE:
                valid_total -= 1
                continue

            if filepath_list:
                self.filepaths.append([filepath, filetype])

            parameters.model_name(self.models)
            parameters.vae_name(self.models)

            if LORA_NAME:
                parameters.override_lora(self.models)
                parameters.override_addnet_model(self.models)

            if TI_NAME:
                parameters.override_textual_inversion(self.models)

            self.applied_model.add(parameters.params.get('Model'))
            self.loaded_images.append((image_indexes, parameters))
            image_indexes += 1

            if progress_bar:
                progress_bar.update_value()

        if len(self.loaded_images) == 0:
            MessageBox('There is no data to parse.\nExiting...', 'Oops!', parent=self.main_window)
            sys.exit()
        elif valid_total == 0:
            MessageBox('There is no data to parse.', 'Oops!', parent=self.main_window)

        if progress_bar:
            progress_bar.close()

    def __init_main_window(self):
        if MAIN_WINDOW == 'thumbnail':
            self.__initialize_thumbnail_window()
        elif MAIN_WINDOW == 'listview':
            self.__initialize_listview_window()
        elif MAIN_WINDOW == 'depends':
            number = len(self.loaded_images)
            if 0 < number < 11:
                self.__initialize_tab_window()
            elif 10 < number < 21:
                self.__initialize_listview_window()
            elif 20 < number:
                self.__initialize_thumbnail_window()
        elif MAIN_WINDOW == 'random':
            number = random.randint(1, 3)
            if number == 1:
                self.__initialize_tab_window()
            elif number == 2:
                self.__initialize_listview_window()
            elif number == 3:
                self.__initialize_thumbnail_window()
        else:
            self.__initialize_tab_window()

    def __initialize_thumbnail_window(self, parent=None):
        indexes = [(index, image.params) for index, image in self.loaded_images]
        self.thumbnail = ThumbnailView(parent, self)
        self.thumbnail.init_thumbnail(indexes, self.moved_indexes, self.deleted_indexes)
        if not self.main_window:
            self.main_window = self.thumbnail

    def __open_thumbnail_window(self):
        if not self.thumbnail:
            self.__initialize_thumbnail_window(self.main_window)
        elif not self.thumbnail.isVisible():
            self.thumbnail.show()
        elif not self.thumbnail.isActiveWindow():
            self.thumbnail.activateWindow()

    def __initialize_listview_window(self, parent=None):
        indexes = [(index, image.params) for index, image in self.loaded_images]
        self.listview = Listview(parent, self)
        self.listview.init_listview(indexes, self.moved_indexes, self.deleted_indexes)
        if not self.main_window:
            self.main_window = self.listview

    def __open_listview_window(self):
        if not self.listview:
            self.__initialize_listview_window(self.main_window)
        elif not self.listview.isVisible():
            self.listview.show()
        elif not self.listview.isActiveWindow():
            self.listview.activateWindow()

    def __initialize_tab_window(self, parent=None):
        self.tabview = Tabview(parent, self)
        self.tabview.init_tabview(self.loaded_images, self.moved_indexes, self.deleted_indexes)
        if not self.main_window:
            self.main_window = self.tabview

    def __open_tab_window(self):
        if not self.tabview:
            self.__initialize_tab_window(self.main_window)
        elif not self.tabview.isVisible():
            self.tabview.show()
        elif not self.tabview.isActiveWindow():
            self.tabview.activateWindow()

    def __open_image_view(self, index: int):
        filepath = self.__get_tag_data_by_index(index, 'Filepath')
        if not self.image_view:
            self.image_view = ImageWindow(self.main_window)
        self.image_view.filepath = filepath
        self.image_view.init_image_window()

    def __open_search_dialog(self, sender):
        models = list(self.applied_model)
        models.sort()
        models.insert(0, '')
        if not self.search_dialog:
            self.search_dialog = SearchWindow(models, self)
        self.search_dialog.show_dialog(sender)

    def __open_diff_view(self, indexes: tuple):
        image_a = self.__get_dictionary_by_index(indexes[0])
        image_b = self.__get_dictionary_by_index(indexes[1])
        DiffWindow((image_a, image_b), self.main_window)

    def __image_state_changed(self, index: int, state: str, remarks: str = None):
        if state == 'moved':
            self.moved_indexes.add(index)
        elif state == 'deleted':
            self.deleted_indexes.add(index)
        elif state == 'matched':
            self.matched_indexes.add(index)

        if self.thumbnail:
            self.thumbnail.manage_subordinates(index, state, remarks)
        if self.listview:
            self.listview.manage_subordinates(index, state, remarks)
        if self.tabview:
            self.tabview.manage_subordinates(index, state, remarks)

    def __update_tag_data_by_index(self, index: int, key: str, value: str):
        for image_index, image in self.loaded_images:
            if image_index == index:
                image.params[key] = value

    def __get_data_by_index(self, index: int):
        for image_index, image_data in self.loaded_images:
            if image_index == index:
                return image_data

    def __get_dictionary_by_index(self, index: int):
        for image_index, image_data in self.loaded_images:
            if image_index == index:
                return image_data.params

    def __get_tag_data_by_index(self, index: int, key: str):
        for image_index, image_data in self.loaded_images:
            if image_index == index:
                return image_data.params.get(key)

    def __get_all_dictionary(self):
        dictionaries = []
        for image_index, image_data in self.loaded_images:
            dictionaries.append(image_data.params)
        return dictionaries

    def __check_main_window(self, sender):
        return self.main_window == sender

    def __search_init_image(self, sender, index: int):
        image_hash = self.__get_tag_data_by_index(index, 'Init image hash')
        if not image_hash:
            MessageBox('This image has not init image hash data.', parent=sender)
            return

        dialog = FileDialog('choose-directory', 'Select directory', sender)
        directory = dialog.result
        if not directory:
            return

        filepaths = find_target(directory, SUBDIRECTORY_DEPTH)
        valid_filepath, _, _, _ = check_files(filepaths)

        for file, filetype in valid_filepath:
            if filetype != 9:
                target_hash = io.extract_image_hash(file)
                if image_hash == target_hash:
                    self.__add_images('', sender, False, file)
                    return

        MessageBox("Couldn't find init image.", parent=sender)

    def __import_json(self, which, sender, is_append=False):
        index_start = len(self.loaded_images) if is_append else 0

        def import_json_from_files():
            dialog = FileDialog('choose-files', 'Select JSONs', sender, 'JSON')
            files = dialog.result
            return files

        def import_json_from_directory():
            dialog = FileDialog('choose-directory', 'Select directory', sender)
            directory = dialog.result
            if directory:
                files = [os.path.join(directory[0], value) for value in os.listdir(directory[0]) if '.json' in value]
                return files

        if which == 'files':
            filepaths = import_json_from_files()
        else:
            filepaths = import_json_from_directory()

        if filepaths:
            json_list = []
            for filepath in filepaths:
                json_data, e = io.import_json(filepath)

                if isinstance(json_data, list):
                    for data in json_data:
                        if data.get('Filepath', None):
                            json_list.append(data)
                else:
                    if json_data.get('Filepath', None):
                        json_list.append(json_data)

                if len(json_list) < 1:
                    MessageBox('There is no valid JSON data.', parent=sender)
                    return

                i = index_start

                for prepared_json in json_list:
                    json_class = parser.ChunkData('This data import from JSON')
                    json_class.import_json(prepared_json)
                    self.loaded_images.append((i, json_class))
                    i += 1

            param_list = [(index, value.params) for index, value in self.loaded_images if index >= index_start]

            if is_append:
                if self.thumbnail:
                    self.thumbnail.thumbnail_add_images(param_list)
                if self.listview:
                    self.listview.listview_add_images(param_list)
                if self.tabview:
                    loaded = [(index, value) for index, value in self.loaded_images if index >= index_start]
                    self.tabview.tabview_add_images(loaded)
            else:
                if self.thumbnail:
                    self.thumbnail.init_thumbnail(param_list)
                if self.listview:
                    self.listview.init_listview(param_list)
                if self.tabview:
                    loaded = [(index, value) for index, value in self.loaded_images if index >= index_start]
                    self.tabview.init_tabview(loaded)
            return True

    def __export_json(self, indexes: tuple):
        category = 'selected'
        if len(indexes) == len(self.loaded_images):
            category = 'all'
        elif len(indexes) == 1:
            category = 'single'

        filepath = self.__get_tag_data_by_index(indexes[0], 'Filepath')
        filename = custom_filename(filepath, category)

        dialog = FileDialog('save-file', 'Save JSON', self.main_window, 'JSON', filename)
        destination = dialog.result[0] if dialog.result else None

        if destination:
            dict_list = []
            for index in indexes:
                dict_list.append(self.__get_dictionary_by_index(index))
            result, e = io.io_export_json(dict_list, destination)
            if not e:
                return True
            else:
                MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)
        return

    def __manage_image_files(self, sender, indexes: tuple, request: str):
        use_copy = USE_MOVE
        destination = None
        succeed = []
        errored = []

        def result_check_and_emit(category, success: list = None, errors: list = None):
            succeed_flag = False

            if success:
                for image_index, filepath in success:
                    if category == 'add' or category == 'move':
                        self.__image_state_changed(image_index, 'moved', filepath)
                    elif category == 'delete':
                        self.__image_state_changed(image_index, 'deleted', filepath)
                    filename = os.path.basename(filepath)
                    self.__update_tag_data_by_index(image_index, 'Filepath', filepath)
                    self.__update_tag_data_by_index(image_index, 'Filename', filename)
                succeed_flag = True

            if errors:
                error_text = '\n'.join(errors)
                MessageBox(error_text, icon='critical', parent=sender)

            return succeed_flag

        if ASK_DELETE and request == 'delete':
            result = MessageBox('Really?', 'Confirm', 'okcancel', 'question', sender)
            if not result.success:
                return

        if request == 'add':
            destination = FAVOURITE
            if not destination:
                return

        elif request == 'delete':
            destination = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.trash')
            os.makedirs(destination, exist_ok=True)
            use_copy = False

        elif request == 'move':
            dialog = FileDialog('choose-directory', 'Select Directory', parent=sender)
            destination = dialog.result[0] if dialog.result else None

        if destination and os.path.exists(destination):
            for index in indexes:
                source = self.__get_tag_data_by_index(index, 'Filepath')
                result, e = io.image_copy_to(source, destination, use_copy)
                if not e:
                    succeed.append((index, result))
                elif e:
                    errored.append(f'{source}\n{result}\n{e}')
            flag = result_check_and_emit(request, succeed, errored)
            return flag

        elif destination and not os.path.exists(destination):
            MessageBox(custom_text('404'), icon='critical', parent=sender)
            return

        elif not destination:
            return

    def __searched_check_and_emit(self, result: tuple, caller):
        if not result[0]:
            MessageBox(result[1], 'Result', parent=caller)
        else:
            if self.thumbnail:
                self.thumbnail.search_process(None)
                self.thumbnail.search_process(result[0])
            if self.listview:
                self.listview.search_process(None)
                self.listview.search_process(result[0])
            if self.tabview:
                self.tabview.search_process(None)
                self.tabview.search_process(result[0])
            MessageBox(result[1], 'Result', parent=caller)
            self.search_dialog.activateWindow()

    def __add_images(self, which: str, sender, is_replace: bool = False, filepath: str = None):
        def filepaths_check(target):
            valid, not_found, directories, not_image = check_files(target)

            if not_found:
                print('\n'.join(not_found))
                print('These files are not found')
            if directories:
                print('\n'.join(directories))
                print('This is directory')
            if not_image:
                print('\n'.join(not_image))
                print('These files are not supported image files.')
            if not valid:
                MessageBox('There is no valid image files', icon='info', parent=sender)
                return

            return valid

        def add_images_duplicate_checker(requested_filepath: list):
            loaded_files = [value[0] for value in self.filepaths]
            unique_filepaths = set(requested_filepath)

            for path in loaded_files:
                if path in unique_filepaths:
                    unique_filepaths.remove(path)

            result = list(unique_filepaths)
            deleted = len(requested_filepath) - len(result)
            result.sort()

            return result, deleted

        if which == 'files':
            dialog = FileDialog('choose-files', 'Select files', sender, 'PNG')
            filepaths = dialog.result
        elif which == 'directory':
            dialog = FileDialog('choose-directory', 'Select Directory', sender)
            directory = dialog.result
            filepaths = None if not directory else find_target(directory, SUBDIRECTORY_DEPTH)
        else:
            filepaths = [filepath]

        if filepaths:
            if not is_replace:
                requested, duplicate = add_images_duplicate_checker(filepaths)
                requested = filepaths_check(requested)
            else:
                self.__clear_class()
                filepaths = sorted(filepaths)
                requested = filepaths_check(filepaths)
                duplicate = 0

            if requested:
                index_start = len(self.loaded_images)
                self.__load_images(requested)
                param_list = [(index, value.params) for index, value in self.loaded_images if index >= index_start]
                params = [(index, value) for index, value in self.loaded_images if index >= index_start]

                if is_replace:
                    if self.thumbnail:
                        self.thumbnail.init_thumbnail(param_list)
                    if self.listview:
                        self.listview.init_listview(param_list)
                    if self.tabview:
                        self.tabview.init_tabview(params)
                else:
                    if self.thumbnail:
                        self.thumbnail.thumbnail_add_images(param_list)
                    if self.listview:
                        self.listview.listview_add_images(param_list)
                    if self.tabview:
                        self.tabview.tabview_add_images(params)

            if duplicate > 0:
                MessageBox(f'{duplicate} file(s) are already shown.', parent=sender)
                if not requested:
                    return
            return True
        return

    def __add_interrogate_wd14(self, indexes: tuple, sender):
        progress = None
        model_filename = 'model.onnx'
        label_filename = "selected_tags.csv"
        models = (('MOAT', 'SmilingWolf/wd-v1-4-moat-tagger-v2'),
                  ('Swin', 'SmilingWolf/wd-v1-4-swinv2-tagger-v2'),
                  ('ConvNext', 'SmilingWolf/wd-v1-4-convnext-tagger-v2'),
                  ('ConvNextV2', 'SmilingWolf/wd-v1-4-convnextv2-tagger-v2'),
                  ('ViT', 'SmilingWolf/wd-v1-4-vit-tagger-v2'))

        def model_checks():
            flag = False
            text = "The script couldn't locate the required files."
            text += "\nWould you like to download them?"
            text += "\nIf so, you'll need approximately 2 GiB of free space."

            for model_setting in models:
                model_base = '.models/' + model_setting[0].lower() + '/' + model_filename
                label_base = '.models/' + model_setting[0].lower() + '/' + label_filename
                model_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), model_base)
                label_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), label_base)
                if not os.path.exists(model_path) or not os.path.exists(label_path):
                    flag = True
                    break

            if flag:
                selected = MessageBox(text, 'Interrogate', 'ok_cancel', 'info', sender)
                if selected.result:
                    for model_setting in models:
                        model_downloads(model_setting[1], model_filename, label_filename, model_setting[0].lower())
                    return True
            return True

        model_enable = model_checks()
        if not model_enable:
            return

        dialog = InterrogateSelectDialog(sender)
        result = dialog.exec()

        if indexes and result == QDialog.DialogCode.Accepted:
            model = dialog.selected_model
            tag = dialog.tag_threshold
            chara = dialog.chara_threshold

            if not self.tabview:
                self.__initialize_tab_window()
            elif not self.tabview.isActiveWindow():
                self.tabview.activateWindow()

            if len(indexes) > 1:
                progress = ProgressDialog()
                progress.setRange(0, len(indexes))
                progress.setLabelText('Interrogating......')

            for index in indexes:
                for image_index, image_data in self.loaded_images:
                    if image_index == index:
                        filepath = image_data.params.get('Filepath')
                        interrogate_result = interrogate(model, filepath, tag, chara)
                        self.tabview.manage_subordinates(image_index, 'interrogated', result=interrogate_result)
                if progress:
                    progress.update_value()

            if sender != self.tabview:
                self.tabview.post_process_of_interrogate(indexes[0])
            if progress:
                progress.close()
            return True

    def __directory_interrogate_wd14(self, setting_tuple: tuple):
        return interrogate(setting_tuple[0], setting_tuple[1], setting_tuple[2], setting_tuple[3])

    def __change_themes(self):
        if self.dark:
            qdarktheme.setup_theme('light')
            self.dark = False
            if self.thumbnail:
                self.thumbnail.footer.theme_menu_check()
            if self.listview:
                self.listview.footer.theme_menu_check()
            if self.tabview:
                self.tabview.footer.theme_menu_check()
        else:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
            self.dark = True
            if self.thumbnail:
                self.thumbnail.footer.theme_menu_check()
            if self.listview:
                self.listview.footer.theme_menu_check()
            if self.tabview:
                self.tabview.footer.theme_menu_check()

    def __exit_scripts(self, sender):
        if sender == self.main_window:
            if not ASK_WHEN_QUIT:
                QApplication.quit()
            else:
                text = 'This is main window.\nQuit script?'
                result = MessageBox(text, style='ok_cancel', icon='question', parent=sender)
                if result.success:
                    QApplication.quit()
        else:
            sender.close()

    def __obliterate(self):
        trash_bin = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.trash')
        if os.path.exists(trash_bin):
            if not io.is_directory_empty(trash_bin):
                answer = None
                if ASK_CLEAR:
                    text = 'Do you want to obliterate files in the trash bin ?'
                    answer = MessageBox(text, 'pyPromptChecker', 'okcancel', 'question', self.main_window)
                if answer.success or not ASK_CLEAR:
                    io.clear_trash_bin(trash_bin)

    def request_reception(self, request: str, sender: QMainWindow, indexes: tuple = None, conditions: str = None, index: int = None):
        result = None

        if request == 'view' and len(indexes) == 1:
            self.__open_image_view(indexes[0])
        elif request == 'diff' and len(indexes) == 2:
            self.__open_diff_view(indexes)
        elif request == 'search':
            self.__open_search_dialog(sender)
        elif request == 'apply':
            self.__searched_check_and_emit(indexes, sender)
        elif request == 'list':
            self.__open_listview_window()
        elif request == 'tab':
            self.__open_tab_window()
        elif request == 'thumbnail':
            self.__open_thumbnail_window()
        elif request == 'theme':
            self.__change_themes()
        elif request == 'init' and len(indexes) == 1:
            self.__search_init_image(sender, indexes[0])
        elif request == 'json' and len(indexes) > 0:
            result = self.__export_json(indexes)
        elif request == 'interrogate' and len(indexes) > 0:
            result = self.__add_interrogate_wd14(indexes, sender)
        elif request == 're-interrogate':
            result = self.__directory_interrogate_wd14(indexes)
        elif (request == 'add' or request == 'move' or request == 'delete') and len(indexes) > 0:
            result = self.__manage_image_files(sender, indexes, request)
        elif request == 'append':
            result = self.__add_images(conditions, sender)
        elif request == 'replace':
            result = self.__add_images(conditions, sender, True)
        elif request == 'import':
            result = self.__import_json(indexes[0], sender, indexes[1])
        elif request == 'dictionary':
            result = self.__get_all_dictionary()
        elif request == 'check':
            result = self.__check_main_window(sender)
        elif request == 'data':
            result = self.__get_data_by_index(index)
        elif request == 'exit':
            self.__exit_scripts(sender)
        elif request == 'hash':
            model_hash_extractor(sender)

        return result


def model_hash_extractor(window):
    which_mode = SelectDialog(window)
    result = which_mode.exec()
    filelist = []
    model_hash_data = []

    def extract_hashes(filepath):
        filename, extension = os.path.splitext(os.path.basename(filepath))
        extension = extension.replace('.', '')

        if which_mode.selected == 0:
            data_hash = io.extract_model_hash(filepath)
        else:
            data_hash = io.extract_lora_hash(filepath)

        model_hash = data_hash[:12]
        model_hash_data.append([filename, model_hash, data_hash, filename, extension])

    if result == QDialog.DialogCode.Accepted:
        select_directory = FileDialog('choose-directory', 'Select directory', parent=window)
        directory = select_directory.result[0] if select_directory.result else None

        if directory:
            files = os.listdir(directory)
            for file in files:
                path = os.path.join(directory, file)
                if os.path.isfile(path):
                    if '.pt' in file or 'ckpt' in file or 'safetensors' in file:
                        filelist.append(path)
            filelist.sort()

            progress = ProgressDialog(window)
            progress.setLabelText('Loading model file......')
            progress.setRange(0, len(filelist))

            for file in filelist:
                extract_hashes(file)
                progress.update_value()

            if model_hash_data:
                result, error = io.export_file(model_hash_data, 'csv', 'model_list.csv')
                if error:
                    MessageBox(f'{result}\n{error}', 'Error', 'ok', 'critical', window)
                    return

            progress.close()

            MessageBox('Finished', "I'm knackered", 'ok', 'info', window)


def from_main(purpose: str, filepaths: list = None):
    if purpose == 'directory':
        app = QApplication(sys.argv)
        if ICON_PATH:
            app.setWindowIcon(QIcon(ICON_PATH))
        if DARK_THEME:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
        else:
            qdarktheme.setup_theme('light')
        open_directory = FileDialog('choose-directory', 'Select directory')
        result = open_directory.result
        return result

    elif purpose == 'files':
        app = QApplication(sys.argv)
        if ICON_PATH:
            app.setWindowIcon(QIcon(ICON_PATH))
        if DARK_THEME:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
        else:
            qdarktheme.setup_theme('light')
        open_files = FileDialog('choose-files', 'Select files', file_filter='PNG')
        result = open_files.result
        return result

    elif purpose == 'window':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            if ICON_PATH:
                app.setWindowIcon(QIcon(ICON_PATH))
            if DARK_THEME:
                qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
            else:
                qdarktheme.setup_theme('light')
        WindowController(app, filepaths)
        sys.exit(app.exec())


def find_target(root: str, depth: int):
    filepaths = []

    def _directory_search(current_dir, current_depth):
        if current_depth <= depth and os.path.exists(current_dir):
            for filename in os.listdir(current_dir):
                fullpath = os.path.join(current_dir, filename)
                if os.path.isfile(fullpath):
                    filepaths.append(fullpath)
                elif os.path.isdir(fullpath):
                    _directory_search(fullpath, current_depth + 1)
        else:
            return

    for path in root:
        if os.path.isfile(path):
            filepaths.append(path)
        else:
            _directory_search(path, 0)
    return filepaths


def check_files(target_list: list):
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
    if ICON_PATH:
        app.setWindowIcon(QIcon(ICON_PATH))
    if DARK_THEME:
        qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
    else:
        qdarktheme.setup_theme('light')
    file_counts = len(target_list) if target_list else 0
    progress_bar = None
    file_is_not_found_list = []
    this_is_directory_list = []
    this_file_is_not_image_file_list = []
    valid_file_list = []

    if file_counts > 5:
        progress_bar = ProgressDialog()
        progress_bar.setLabelText("Checking files...")
        progress_bar.setRange(0, file_counts)

    for filepath in target_list:
        if not os.path.exists(filepath):
            file_is_not_found_list.append(filepath)
            if progress_bar:
                progress_bar.update_value()
            continue

        elif not os.path.isfile(filepath):
            this_is_directory_list.append(filepath)
            if progress_bar:
                progress_bar.update_value()
            continue

        result = decoder.image_format_identifier(filepath)
        if not result:
            this_file_is_not_image_file_list.append(filepath)
        else:
            valid_file_list.append(result)

        if progress_bar:
            progress_bar.update_value()

    if progress_bar:
        progress_bar.close()

    return valid_file_list, file_is_not_found_list, this_is_directory_list, this_file_is_not_image_file_list
