# -*- coding: utf-8 -*-

import qdarktheme
from PyQt6.QtCore import QObject

from gui.custom import *
from gui.dialog import *
from gui.listview import Listview
from gui.menu import MainMenu
from gui.search import SearchWindow
from gui.tab import Tabview
from gui.thumbnail import ThumbnailView
from gui.viewer import *
from lib import *

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


class ImageController(QObject):
    def __init__(self, app, filepaths):
        super().__init__()
        self.app = app
        self.filepaths = filepaths

        self.dark = DARK_THEME

        self.main_window = None
        self.main_menu = None
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
        self.__init_main_window()
        self.app.aboutToQuit.connect(self.__obliterate)

    def __init_class(self):
        self.models = io.import_model_list(MODEL_LIST)
        self.__load_images()

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

        if progress_bar:
            progress_bar.close()

        if len(self.loaded_images) == 0:
            MessageBox('There is no data to parse.\nExiting...', 'Oops!', parent=self.main_window)
            sys.exit()
        elif valid_total == 0:
            MessageBox('There is no data to parse.', 'Oops!', parent=self.main_window)

    def __init_main_window(self):
        if MAIN_WINDOW == 'thumbnail':
            self.__initialize_thumbnail_window()
        elif MAIN_WINDOW == 'listview':
            self.__initialize_listview_window()
        else:
            self.__initialize_tab_window()

    def __initialize_thumbnail_window(self, parent=None):
        indexes = [(index, image.params) for index, image in self.loaded_images]
        self.thumbnail = ThumbnailView(parent, self)
        self.thumbnail.init_thumbnail(indexes, self.moved_indexes, self.deleted_indexes)
        if not self.main_window:
            self.main_window = self.thumbnail
            self.main_menu = MainMenu(self.main_window, self)

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
            self.main_menu = MainMenu(self.main_window, self)

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
            self.main_menu = MainMenu(self.main_window, self)

    def __open_tab_window(self):
        if not self.tabview:
            self.__initialize_tab_window(self.main_window)
        elif not self.tabview.isVisible():
            self.tabview.show()
        elif not self.tabview.isActiveWindow():
            self.tabview.activateWindow()

    def __moved_image(self, index: int, remarks=None):
        self.moved_indexes.add(index)
        if self.thumbnail:
            self.thumbnail.manage_subordinates(index, 'moved', remarks)
        if self.listview:
            self.listview.manage_subordinates(index, 'moved', remarks)
        if self.tabview:
            self.tabview.manage_subordinates(index, 'moved', remarks)

    def __deleted_image(self, index: int, remarks=None):
        self.deleted_indexes.add(index)
        if self.thumbnail:
            self.thumbnail.manage_subordinates(index, 'deleted', remarks)
        if self.listview:
            self.listview.manage_subordinates(index, 'deleted', remarks)
        if self.tabview:
            self.tabview.manage_subordinates(index, 'deleted', remarks)

    def __matched_image(self, indexes: list):
        self.matched_indexes.update(indexes)

    def __update_tag_data_by_index(self, index: int, key: str, value: str):
        for image_index, image in self.loaded_images:
            if image_index == index:
                image.params[key] = value

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

    def get_data_by_index(self, index):
        for image_index, image_data in self.loaded_images:
            if image_index == index:
                return image_data
        return None

    def get_dictionary_by_index(self, index):
        for image_index, image_data in self.loaded_images:
            if image_index == index:
                return image_data.params

    def get_tag_data_by_index(self, index: int, key: str):
        for image_index, image_data in self.loaded_images:
            if image_index == index:
                return image_data.params.get(key)
        return None

    def get_all_dictionary(self):
        dictionaries = []
        for image_index, image_data in self.loaded_images:
            dictionaries.append(image_data.params)
        return dictionaries

    def request_reception(self, indexes: tuple, request: str, sender=None):
        result = None

        if request == 'view':
            if len(indexes) == 1:
                self.open_image_view(indexes[0])
        elif request == 'diff':
            if len(indexes) == 2:
                self.open_diff_view(tuple(indexes))
        elif request == 'json':
            if len(indexes) > 0:
                result = self.__export_json(tuple(indexes))
        elif request == 'add' or request == 'move' or request == 'delete':
            if len(indexes) > 0:
                result = self.__manage_image_files(indexes, request)
        elif request == 'search':
            self.open_search_dialog(sender)
        elif request == 'apply':
            self.__searched_check_and_emit(indexes, sender)
        elif request == 'append':
            result = self.__add_images(indexes[0], sender)
        elif request == 'replace':
            result = self.__add_images(indexes[0], sender, True)
        elif request == 'import':
            result = self.__import_json(indexes[0], sender, indexes[1])
        elif request == 'list':
            self.__open_listview_window()
        elif request == 'tab':
            self.__open_tab_window()
        elif request == 'thumbnail':
            self.__open_thumbnail_window()
        elif request == 'exit':
            QApplication.quit()
        return result

    def open_image_view(self, index: int):
        filepath = self.get_tag_data_by_index(index, 'Filepath')
        if not self.image_view:
            self.image_view = ImageWindow(self.main_window)
        self.image_view.filepath = filepath
        self.image_view.init_image_window()

    def open_search_dialog(self, sender):
        models = list(self.applied_model)
        models.sort()
        models.insert(0, '')
        if not self.search_dialog:
            self.search_dialog = SearchWindow(models, self)
        self.search_dialog.show_dialog(sender)

    def open_diff_view(self, indexes: tuple):
        image_a = self.get_dictionary_by_index(indexes[0])
        image_b = self.get_dictionary_by_index(indexes[1])
        DiffWindow((image_a, image_b), self.main_window)

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
                    self.thumbnail.add_images(param_list)
                if self.listview:
                    self.listview.add_image(param_list)
            else:
                if self.thumbnail:
                    self.thumbnail.init_thumbnail(param_list)
                if self.listview:
                    self.listview.add_images(param_list)
            return True

    def __export_json(self, indexes: tuple):
        category = 'selected'
        if len(indexes) == len(self.loaded_images):
            category = 'all'
        elif len(indexes) == 1:
            category = 'single'

        filepath = self.get_tag_data_by_index(indexes[0], 'Filepath')
        filename = custom_filename(filepath, category)

        dialog = FileDialog('save-file', 'Save JSON', self.main_window, 'JSON', filename)
        destination = dialog.result[0] if dialog.result else None

        if destination:
            dict_list = []
            for index in indexes:
                dict_list.append(self.get_dictionary_by_index(index))
            result, e = io.io_export_json(dict_list, destination)
            if not e:
                return True
            else:
                MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)
        return

    def __manage_image_files(self, indexes: tuple, request: str):
        use_copy = USE_MOVE
        destination = None
        succeed = []
        changed = []
        errored = []

        if ASK_DELETE and request == 'delete':
            result = MessageBox('Really?', 'Confirm', 'okcancel', 'question', self.main_window)
            if not result.success:
                return

        if request == 'add':
            if not destination:
                return
        elif request == 'delete':
            destination = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.trash')
            os.makedirs(destination, exist_ok=True)
            use_copy = False
        elif request == 'move':
            dialog = FileDialog('choose-directory', 'Select Directory', parent=self.main_window)
            destination = dialog.result[0] if dialog.result else None

        if destination and os.path.exists(destination):
            for index in indexes:
                source = self.get_tag_data_by_index(index, 'Filepath')
                result, e = io.image_copy_to(source, destination, use_copy)
                if not e and os.path.basename(source) == os.path.basename(result):
                    succeed.append((index, result))
                elif not e and os.path.basename(source) != os.path.basename(result):
                    changed.append((index, result))
                elif e:
                    errored.append(f'{source}\n{result}\n{e}')
            flag = self.__result_check_and_emit(request, succeed, changed, errored)
            return flag

        elif destination and not os.path.exists(destination):
            MessageBox(custom_text('404'), icon='critical', parent=self.main_window)
            return

        elif not destination:
            return

    def __result_check_and_emit(self, category, success: list = None, name_changed: list = None, errors: list = None):
        succeed_flag = False

        if success:
            for index, filepath in success:
                if category == 'add' or category == 'move':
                    self.__moved_image(index, filepath)
                elif category == 'delete':
                    self.__deleted_image(index, filepath)
                filename = os.path.basename(filepath)
                self.__update_tag_data_by_index(index, 'Filepath', filepath)
                self.__update_tag_data_by_index(index, 'Filename', filename)
            succeed_flag = True

        if name_changed:
            for index, filepath in name_changed:
                if category == 'add' or category == 'move':
                    self.__moved_image(index, filepath)
                elif category == 'delete':
                    self.__deleted_image(index, filepath)
                filename = os.path.basename(filepath)
                self.__update_tag_data_by_index(index, 'Filepath', filepath)
                self.__update_tag_data_by_index(index, 'Filename', filename)
            succeed_flag = True

        if errors:
            error_text = '\n'.join(errors)
            MessageBox(error_text, icon='critical', parent=self.main_window)

        return succeed_flag

    def __searched_check_and_emit(self, result: tuple, caller):
        if not result[0]:
            MessageBox(result[1], 'Result', parent=caller)
        else:
            if self.thumbnail:
                self.thumbnail.search_process(result[0])
            if self.listview:
                self.listview.search_process(result[0])
            MessageBox(result[1], 'Result', parent=caller)

    def __add_images(self, which: str, sender, is_replace: bool = False):
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
        else:
            dialog = FileDialog('choose-directory', 'Select Directory', sender)
            directory = dialog.result
            filepaths = None if not directory else find_target(directory, SUBDIRECTORY_DEPTH)

        if filepaths:
            if not is_replace:
                requested, duplicate = add_images_duplicate_checker(filepaths)
                requested = filepaths_check(requested)
            else:
                self.__clear_class()
                filepaths = sorted(filepaths)
                requested = filepaths_check(filepaths)
                duplicate = 0

            index_start = len(self.loaded_images)

            self.__load_images(requested)
            param_list = [(index, value.params) for index, value in self.loaded_images if index >= index_start]

            if is_replace:
                if self.thumbnail:
                    self.thumbnail.init_thumbnail(param_list)
                if self.listview:
                    self.listview.init_listview(param_list)
                if self.tabview:
                    self.tabview.init_tabview()
            else:
                if self.thumbnail:
                    self.thumbnail.thumbnail_add_images(param_list)
                if self.listview:
                    self.listview.listview_add_images(param_list)

            if duplicate > 0:
                MessageBox(f'{duplicate} file(s) are already shown.', parent=sender)
                if len(requested) == 0:
                    return
            return True
        return

    '''
    def __add_interrogate_wd14(self, select: int = 0, indexes: tuple = None):
        progress = None
        dialog = InterrogateSelectDialog(self.main_window)
        result = dialog.exec()

        if result == QDialog.DialogCode.Accepted:
            model = dialog.selected_model
            tag = dialog.tag_threshold
            chara = dialog.chara_threshold

            if select == 0:
                indexes = [self.root_tab.currentIndex()]
            elif select == 1:
                indexes = tuple(range(self.root_tab.count()))

            if len(indexes) > 1:
                progress = ProgressDialog(self)
                progress.setRange(0, len(indexes))
                progress.setLabelText('Interrogating......')

            for index in indexes:
                filepath = self.params[index].params.get('Filepath')
                current_tab_page = self.root_tab.widget(index)
                extension_tab = current_tab_page.findChild(QTabWidget, 'extension_tab')

                for tab_index in range(extension_tab.count()):
                    if extension_tab.tabText(tab_index) == 'Interrogate':
                        extension_tab.removeTab(tab_index)
                        break

                interrogate_result = interrogate(model, filepath, tag, chara)
                interrogate_tab = InterrogateTab(interrogate_result, extension_tab, self)
                extension_tab.addTab(interrogate_tab, 'Interrogate')
                new_index = extension_tab.indexOf(interrogate_tab)
                extension_tab.setCurrentIndex(new_index)

                if progress:
                    progress.update_value()

            if progress:
                progress.close()
                
    def __apply_search_result(self, indexes=None):
        hide = config.get('HideNotMatchedTabs', False)
        restore = self.centralWidget().findChild(QPushButton, 'Restore')
        if indexes:
            for tab_index in reversed(range(self.root_tab.count())):
                if tab_index not in indexes:
                    if hide:
                        title = self.root_tab.tabText(tab_index)
                        self.retracted.append([tab_index, self.root_tab.widget(tab_index), title])
                        self.root_tab.removeTab(tab_index)
                        restore.setDisabled(False)
                else:
                    self.root_tab.tabBar().setTabTextColor(tab_index, Qt.GlobalColor.green)
                    if self.tab_bar:
                        self.tab_bar.image_matched(indexes)
                        if hide:
                            self.tab_bar.pixmap_hide()

        else:
            palette = self.root_tab.palette()
            text_color = palette.color(QPalette.ColorRole.Text)
            for index in range(self.root_tab.count()):
                color = self.root_tab.tabBar().tabTextColor(index)
                if color == Qt.GlobalColor.green:
                    self.root_tab.tabBar().setTabTextColor(index, text_color)
            if self.retracted:
                for widget in reversed(self.retracted):
                    self.root_tab.insertTab(widget[0], widget[1], widget[2])
                self.retracted = []
                restore.setDisabled(True)
            if self.tab_bar:
                self.tab_bar.result_clear()

    def export_all_text(self):
        for i in range(self.root_tab.count()):
            extension_tab = self.root_tab.widget(i).findChild(QTabWidget, 'extension_tab')
            interrogate_tab = extension_tab.findChild(QStackedWidget, 'interrogate')
            if interrogate_tab is not None:
                interrogate_tab.export_text(True)
        self.toast.init_toast('Exported!', 1000)
'''

    def model_hash_extractor(self):
        which_mode = SelectDialog(self.main_window)
        result = which_mode.exec()
        mode = which_mode.selected

        if result == QDialog.DialogCode.Accepted:
            select_directory = FileDialog('choose-directory', 'Select directory', parent=self.main_window)
            directory = select_directory.result[0] if select_directory.result else None
            if directory:
                operation_progress = ProgressDialog(self)
                file_list = os.listdir(directory)
                file_list = [os.path.join(directory, v) for v in file_list if
                             os.path.isfile(os.path.join(directory, v))]
                file_list = [v for v in file_list if '.safetensors' in v or '.ckpt' in v or '.pt' in v]
                file_list.sort()
                operation_progress.setLabelText('Loading model file......')
                operation_progress.setRange(0, len(file_list) + 1)
                io.model_hash_maker(file_list, operation_progress, mode)
                MessageBox('Finished', "I'm knackered", 'ok', 'info', self.main_window)

    def change_themes(self):
        if self.dark:
            qdarktheme.setup_theme('light')
            self.dark = False
            self.main_menu.theme_check()
        else:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
            self.dark = True
            self.main_menu.theme_check()


def from_main(purpose, filepaths=None):
    if purpose == 'directory':
        app = QApplication(sys.argv)
        if DARK_THEME:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
        else:
            qdarktheme.setup_theme('light')
        open_directory = FileDialog('choose-directory', 'Select directory')
        result = open_directory.result
        return result

    elif purpose == 'files':
        app = QApplication(sys.argv)
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
        ImageController(app, filepaths)
        sys.exit(app.exec())


def find_target(root, depth):
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


def check_files(target_list):
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
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
