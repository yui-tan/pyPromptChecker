# -*- coding: utf-8 -*-

import sys
import qdarktheme
from pyPromptChecker.lib import *

# sys.path.append('../')
# from lib import *

from . import config
from .dialog import *
from .subwindow import *
from .widget import *
from .menu import *
from PyQt6.QtWidgets import QApplication, QLabel, QTabWidget, QHBoxLayout, QPushButton, QComboBox, QTextEdit
from PyQt6.QtCore import Qt, QPoint


class ResultWindow(QMainWindow):
    def __init__(self, targets=None):
        super().__init__()
        self.root_tab = None
        self.dialog = None
        self.toast_window = None
        self.progress_bar = None
        self.params = []
        self.filepath_list = []
        self.extract_data(targets)
        self.image_window = ImageWindow(self)
        self.thumbnail = ThumbnailView(self)
        self.main_menu = MainMenu(self)
        self.tab_linker = TabMenu(self)
        self.tab_linker_enable = [False, 'Prompt']

        self.setWindowTitle('PNG Prompt Data')

        size_hint_width = self.sizeHint().width()
        size_hint_height = self.sizeHint().height()

        max_width = config.get('MaxWindowWidth', 650)
        max_height = config.get('MaxWindowHeight', 800)

        window_width = size_hint_width if max_width > size_hint_width else max_width
        window_height = size_hint_height if max_height > size_hint_height else max_height

        self.show()
        self.resize(window_width, window_height)
        self.move_centre_main()

    def init_ui(self):
        tab_navigation_enable = config.get('TabNavigation', True)
        tab_minimums = config.get('TabNavigationMinimumTabs', True)

        self.root_tab = QTabWidget()
        root_layout = QVBoxLayout()
        central_widget = QWidget()

        footer_layout = make_footer_area(self)
        self.make_root_tab()

        if tab_navigation_enable and self.root_tab.count() > tab_minimums:
            root_layout.addLayout(tab_navigation(self))
        root_layout.addWidget(self.root_tab)
        root_layout.addLayout(footer_layout)

        central_widget.setLayout(root_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

        self.root_tab.currentChanged.connect(self.tab_changed)
        self.root_tab.setTabBarAutoHide(True)

        self.toast_window = Toast(self)
        self.dialog = Dialog(self)

    def extract_data(self, targets):
        png_index = config.get('TargetChunkIndex', 1)
        ignore = config.get('IgnoreIfDataIsNotEmbedded', False)
        valid_total = len(targets)
        is_add = bool(self.params)

        if len(targets) > 5:
            self.progress_bar = ProgressDialog(self)
            self.progress_bar.setRange(0, len(targets) * 2)
            self.progress_bar.setLabelText('Extracting PNG Chunk...')

        models = io.import_model_list(config.get('ModelList', 'model_list.csv'))

        for array in targets:
            filepath, filetype = array

            chunk_data = chunk_text_extractor(filepath, filetype, png_index)
            if not chunk_data and ignore:
                valid_total -= 1
                continue

            parameters = parse_parameter(chunk_data, filepath, models)
            if parameters.params.get('Positive') == 'This file has no embedded data' and ignore:
                valid_total -= 1
                continue

            self.params.append(parameters)

            if self.progress_bar:
                self.progress_bar.update_value()

        if not self.centralWidget() and valid_total == 0:
            MessageBox('There is no data to parse.\nExiting...', 'Oops!')
            sys.exit()
        elif valid_total == 0:
            MessageBox('There is no data to parse.', 'Oops!')
            return

        if not is_add:
            self.init_ui()
        else:
            self.make_root_tab()

    def make_root_tab(self):
        shown_tab = self.root_tab.count()
        total = len(self.params)
        image_count = 0

        if self.progress_bar:
            self.progress_bar.setLabelText('Formatting prompt data...')

        for params_index, tmp in enumerate(self.params, 1):
            if shown_tab > 0 and params_index < shown_tab + 1:
                continue

            if self.progress_bar:
                self.progress_bar.update_value()

            if total > 1:
                tmp.params['File count'] = str(image_count + 1) + ' / ' + str(total)

            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            main_section = QGroupBox()
            main_section.setObjectName('main_section')
            main_section_layout = QHBoxLayout()

            main_label_layout = make_main_section(tmp)
            main_section_layout.addLayout(main_label_layout)
            main_section.setLayout(main_section_layout)
            tab_page_layout.addWidget(main_section)

            pixmap_label = main_section.findChild(PixmapLabel, 'Pixmap')
            if pixmap_label:
                pixmap_label.clicked.connect(self.pixmap_clicked)
            for button in ['Favourite', 'Move to', 'Delete']:
                managing_button = main_section.findChild(QPushButton, button)
                if managing_button:
                    managing_button.clicked.connect(self.managing_button_clicked)

            hires_tab = ['Hires upscaler', 'Face restoration', 'Extras']
            cfg_fix_auto_tab = ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler']
            lora_tab = ['Lora', 'AddNet Enabled']

            tabs = [['Prompts', True, True],
                    ['Hires.fix / Extras',
                     any(key in v for v in tmp.params for key in hires_tab),
                     config.get('HiresExtras', True)],
                    ['CFG',
                     any(key in v for v in tmp.params for key in cfg_fix_auto_tab),
                     config.get('CFG', True)],
                    ['Lora / Add networks',
                     any(key in v for v in tmp.params for key in lora_tab),
                     config.get('LoraAddNet', True)],
                    ['Tiled diffusion',
                     'Tiled diffusion' in tmp.params,
                     config.get('TiledDiffusion', True)],
                    ['Control net',
                     'ControlNet' in tmp.params,
                     config.get('ControlNet', True)],
                    ['Regional prompter',
                     'RP Active' in tmp.params,
                     config.get('RegionalPrompter', True)]
                    ]

            for index, tab in enumerate(tabs):
                if tab[1] and tab[2]:
                    inner_page = QWidget()
                    if index == 0:
                        inner_page.setLayout(make_prompt_tab(tmp))
                    if index == 1:
                        inner_page.setLayout(make_hires_other_tab(tmp))
                    if index == 2:
                        inner_page.setLayout(make_cfg_tab(tmp))
                    if index == 3:
                        inner_page.setLayout(make_lora_addnet_tab(tmp))
                    if index == 4:
                        inner_page.setLayout(make_tiled_diffusion_tab(tmp))
                    if index == 5:
                        inner_page = make_control_net_tab(tmp, 0)
                    if index == 6:
                        inner_page.setLayout(make_regional_prompter_tab(tmp))
                    inner_tab.addTab(inner_page, tab[0])

            error_list_parameter = config.get('ErrorList', 1)
            if not error_list_parameter == 0:
                error_page = make_error_tab(tmp, error_list_parameter)
                inner_tab.addTab(error_page, 'Errors')

            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            inner_tab.setObjectName('extension_tab')
            inner_tab.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            inner_tab.customContextMenuRequested.connect(self.show_tab_menu)
            inner_tab.currentChanged.connect(self.inner_tab_changed)

            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            if 'File count' in tmp.params:
                del tmp.params['File count']

            self.root_tab.addTab(tab_page, tmp.params.get('Filename', '---'))
            self.root_tab.setTabToolTip(shown_tab + image_count, tmp.params.get('Filename', '---'))
            image_count += 1

        if total != image_count and self.centralWidget():
            self.post_add_tab()

        if self.progress_bar:
            self.progress_bar.close()

    def post_add_tab(self):
        total = self.root_tab.count()
        tab_navigation_enable = config.get('TabNavigation', True)
        tab_minimums = config.get('TabNavigationMinimumTabs', True)
        tab_navigation_box = self.centralWidget().findChild(QComboBox, 'Combo')

        for index in range(total):
            text = str(index + 1) + ' / ' + str(total)
            widget = self.root_tab.widget(index)
            label = widget.findChild(QLabel, 'Number_value')
            if label:
                label.setText(text)

        if tab_navigation_enable and tab_minimums < total and not tab_navigation_box:
            root_layout = self.centralWidget().layout()
            root_layout.insertLayout(0, tab_navigation(self))
        elif tab_navigation_enable and tab_minimums < total and tab_navigation_box:
            filelist = [value.params.get('Filename') for value in self.params]
            tab_navigation_box.clear()
            tab_navigation_box.addItems(filelist)

    def tab_changed(self):
        current_index = self.root_tab.currentIndex()
        current_page = self.root_tab.widget(current_index)
        extension_tab = current_page.findChild(QTabWidget, 'extension_tab')
        combobox = self.centralWidget().findChild(QComboBox, 'Combo')
        if combobox:
            combobox.setCurrentIndex(current_index)
        if self.image_window.isVisible():
            self.image_window.filepath = self.params[current_index].params.get('Filepath')
            self.image_window.init_image_window()
        if self.tab_linker_enable[0]:
            tab_name = self.tab_linker_enable[1]
            for index in range(extension_tab.count()):
                if extension_tab.tabText(index) == tab_name:
                    extension_tab.setCurrentIndex(index)
                    break

    def inner_tab_changed(self):
        current_index = self.sender().currentIndex()
        tab_name = self.sender().tabText(current_index)
        self.tab_linker_enable[1] = tab_name

    def header_button_clicked(self):
        where_from = self.sender().objectName()
        if where_from == 'Combo':
            target_tab = self.sender().currentIndex()
            self.root_tab.setCurrentIndex(target_tab)
        elif where_from == 'Thumbnail':
            self.open_thumbnail()
        elif where_from == 'Search':
            self.not_yet_implemented()

    def button_clicked(self):
        where_from = self.sender().objectName()
        clipboard = QApplication.clipboard()
        current_page = self.root_tab.currentWidget()
        if where_from == 'Copy positive':
            text_edit = current_page.findChild(QTextEdit, 'Positive')
            if text_edit:
                text = text_edit.toPlainText()
                if text and not text == 'This file has no embedded data':
                    clipboard.setText(text)
                    self.toast_window.init_toast('Positive Copied!', 1000)
        elif where_from == 'Copy negative':
            text_edit = current_page.findChild(QTextEdit, 'Negative')
            if text_edit:
                text = text_edit.toPlainText()
                if text:
                    clipboard.setText(text)
                    self.toast_window.init_toast('Negative Copied!', 1000)
        elif where_from == 'Copy seed':
            label = current_page.findChild(QLabel, 'Seed_value')
            if label:
                text = label.text()
                clipboard.setText(text)
                self.toast_window.init_toast('Seed Copied!', 1000)
        elif where_from == 'Export JSON (This)':
            self.export_json_single()
        elif where_from == 'Export JSON (All)':
            self.export_json_all()
        elif where_from == '▲Menu':
            x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
            y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.main_menu.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            self.main_menu.exec(adjusted_pos)

    def managing_button_clicked(self):
        where_from = self.sender().objectName()
        current_page = self.root_tab.currentWidget()
        current_index = self.root_tab.currentIndex()
        is_move = not config.get('UseCopyInsteadOfMove')
        source = self.params[current_index].params.get('Filepath')
        filename = self.params[current_index].params.get('Filename')
        if not os.path.exists(source):
            text = "Couldn't find this image file."
            MessageBox(text, 'Error', 'ok', 'critical', self)
        elif where_from == 'Favourite':
            destination = config.get('Favourites')
            if not destination:
                text = "Couldn't find setting of destination directory.\nPlease Check setting in 'config.ini' file."
                MessageBox(text, 'Error', 'ok', 'critical', self)
            elif not os.path.isdir(destination):
                text = "Couldn't find destination directory.\nPlease Check setting in 'config.ini' file."
                MessageBox(text, 'Error', 'ok', 'critical', self)
            else:
                result, e = io.image_copy_to(source, destination, is_move)
                if not e:
                    self.root_tab.tabBar().setTabTextColor(current_index, Qt.GlobalColor.blue)
                    filepath_label = current_page.findChild(QLabel, 'Filepath_value')
                    filepath_label.setStyleSheet("color: blue;")
                    filepath_label.setText(destination)
                    filepath_label.setToolTip(destination)
                    self.params[current_index].params['Filepath'] = os.path.join(destination, filename)
                    self.toast_window.init_toast('Added!', 1000)
                else:
                    MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)
        elif where_from == 'Move to':
            self.dialog.init_dialog('choose-directory', 'Select Directory')
            destination = self.dialog.result[0] if self.dialog.result else None
            if destination:
                result, e = io.image_copy_to(source, destination, is_move)
                if not e:
                    self.root_tab.tabBar().setTabTextColor(current_index, Qt.GlobalColor.blue)
                    filepath_label = current_page.findChild(QLabel, 'Filepath_value')
                    filepath_label.setStyleSheet("color: blue;")
                    filepath_label.setText(destination)
                    filepath_label.setToolTip(destination)
                    self.params[current_index].params['Filepath'] = os.path.join(destination, filename)
                    self.toast_window.init_toast('Moved!', 1000)
                else:
                    MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)
        elif where_from == 'Delete':
            destination = os.path.join(os.path.abspath(''), '.trash')
            os.makedirs(destination, exist_ok=True)
            if config.get('AskIfDelete'):
                result = MessageBox('Really?', 'Confirm', 'okcancel', 'question', self)
                if not result.success:
                    return
            result, e = io.image_copy_to(source, destination, True)
            if not e:
                filepath_label = current_page.findChild(QLabel, 'Filepath_value')
                filepath_label.setStyleSheet("color: red;")
                filepath_label.setText(destination)
                filepath_label.setToolTip(destination)
                self.root_tab.tabBar().setTabTextColor(current_index, Qt.GlobalColor.red)
                self.params[current_index].params['Filepath'] = os.path.join(destination, filename)
                self.toast_window.init_toast('Deleted!', 1000)
            else:
                MessageBox(result.replace('moving/copying', 'deleting') + '\n' + str(e), 'Error', 'ok', 'critical',
                           self)

    def pixmap_clicked(self):
        if not self.image_window.isVisible():
            current_index = self.root_tab.currentIndex()
            self.image_window.filepath = self.params[current_index].params.get('Filepath')
            self.image_window.init_image_window()

    def show_tab_menu(self, pos):
        current_index = self.sender().currentIndex()
        tab_bar = self.sender().tabBar()
        tab_rect = tab_bar.tabRect(current_index)
        changed_pos = tab_bar.mapFrom(self.sender(), pos)
        if tab_rect.contains(changed_pos):
            x = tab_bar.mapToGlobal(tab_rect.topLeft()).x()
            y = tab_bar.mapToGlobal(tab_rect.topLeft()).y() - self.tab_linker.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            self.tab_linker.exec(adjusted_pos)

    def move_centre_main(self):
        screen_center = QApplication.primaryScreen().geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def open_thumbnail(self):
        filepath_list = []
        for index, tmp in enumerate(self.params):
            filepath_list.append([tmp.params.get('Filepath'), tmp.params.get('Filename'), index])
        self.thumbnail.init_thumbnail(filepath_list)

    def import_json_from_files(self):
        self.dialog.init_dialog('choose-files', 'Select JSONs', None, 'JSON')
        filepaths = self.dialog.result
        self.import_json(filepaths)

    def import_json_from_directory(self):
        self.dialog.init_dialog('choose-directory', 'Select directory')
        directory = self.dialog.result
        if directory:
            filepaths = [os.path.join(directory[0], value) for value in os.listdir(directory[0]) if '.json' in value]
            self.import_json(filepaths)

    def import_json(self, filepaths):
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
                    MessageBox('There is no valid JSON data.', 'pyPromptChecker', 'ok', 'warning', self)
                    return
                self.params = []
                for prepared_json in json_list:
                    json_class = parser.ChunkData('This data import from JSON')
                    json_class.import_json(prepared_json)
                    self.params.append(json_class)
            if len(self.params) > 5:
                self.progress_bar = ProgressDialog()
                self.progress_bar.setRange(0, len(self.params))
            self.init_ui()
            self.toast_window.init_toast('Imported!', 1000)

    def export_json_single(self):
        current_index = self.root_tab.currentIndex()
        data = self.params[current_index].params
        filename = config.get('JsonSingle', 'filename')
        if filename == 'filename':
            filename = self.params[current_index].params.get('Filepath')
            filename = os.path.splitext(os.path.basename(filename))[0] + '.json'
        self.dialog.init_dialog('save-file', 'Save JSON', filename, 'JSON')
        filepath = self.dialog.result[0] if self.dialog.result else None
        if filepath:
            result, e = io.export_json(data, filepath)
            if not e:
                self.toast_window.init_toast('Saved!', 1000)
            else:
                MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)

    def export_json_all(self):
        filename = config.get('JsonMultiple', 'directory')
        if filename == 'directory':
            filename = self.params[0].params.get('Filepath')
            filename = os.path.basename(os.path.dirname(filename)) + '.json'
        self.dialog.init_dialog('save-file', 'Save JSON', filename, 'JSON')
        filepath = self.dialog.result[0] if self.dialog.result else None
        if filepath:
            dict_list = []
            for tmp in self.params:
                dict_list.append(tmp.params)
            result, e = io.export_json(dict_list, filepath)
            if not e:
                self.toast_window.init_toast('Saved!', 1000)
            else:
                MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)

    def export_json_selected(self, selected_files):
        filename = config.get('JsonSelected', 'selected')
        if filename == 'selected':
            filename = self.params[selected_files[0]].params.get('Filepath')
            filename = os.path.splitext(os.path.basename(filename))[0] + '_and_so_on.json'
        self.dialog.init_dialog('save-file', 'Save JSON', filename, 'JSON')
        destination = self.dialog.result[0] if self.dialog.result else None
        if destination:
            dict_list = []
            for index in selected_files:
                dict_list.append(self.params[index].params)
            result, e = io.export_json(dict_list, destination)
            if not e:
                self.toast_window.init_toast('Saved!', 1000)
            else:
                MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)

    def reselect_files_duplicate_check(self, selected_filepaths):
        shown_files = [value.params.get('Filepath') for value in self.params]
        unique_filepaths = set(selected_filepaths)

        for filepath in shown_files:
            if filepath in unique_filepaths:
                unique_filepaths.remove(filepath)

        result = list(unique_filepaths)
        deleted = len(selected_filepaths) - len(result)
        result.sort()

        return result, deleted

    def reselect_files_from_directory(self):
        pass

    def reselect_files_append(self):
        self.reselect_files(True)

    def reselect_files(self, add=False):
        self.dialog.init_dialog('choose-files', 'Select files', None, 'PNG')
        filepath = self.dialog.result
        result_list = []
        duplicate = 0
        flag = False

        if filepath and add:
            filepath, duplicate = self.reselect_files_duplicate_check(filepath)
            if not filepath:
                MessageBox('Those files are already shown!', 'pyPromptChecker', 'ok', 'info', self)
                return
        if filepath:
            for tmp in filepath:
                result = image_format_identifier(tmp)
                if result:
                    result_list.append(result)
        if not result_list:
            MessageBox('There is no image files to parse!', 'pyPromptChecker', 'ok', 'info', self)
            return
        if self.image_window.isVisible():
            self.image_window.close()
        if self.thumbnail.isVisible():
            self.thumbnail.close()
        if len(result_list) > 10:
            self.progress_bar = ProgressDialog()
            self.progress_bar.setRange(0, len(result_list) * 2)
        if not add:
            self.params = []
            self.extract_data(result_list)
        else:
            self.extract_data(result_list)
            flag = True
        if duplicate > 0:
            text = "{} file(s) didn't processed due to already shown. ".format(duplicate)
            MessageBox(text, 'pyPromptChecker', 'ok', 'info', self)
        if flag:
            self.toast_window.init_toast('Added!', 1000)
        else:
            self.toast_window.init_toast('Replaced!', 1000)

    def model_hash_extractor(self):
        text = 'This operation requires a significant amount of time.' \
               '\n...And more than 32GiB of memory.' \
               '\nDo you still want to run it ?'
        result = MessageBox(text, 'Confirm', 'okcancel', 'question', self)

        if result.success:
            self.dialog.init_dialog('choose-directory', 'Select Directory', None, '')
            directory = self.dialog.result[0] if self.dialog.result else None
            if directory:
                operation_progress = ProgressDialog(self)
                file_list = os.listdir(directory)
                file_list = [os.path.join(directory, v) for v in file_list if
                             os.path.isfile(os.path.join(directory, v))]
                file_list = [v for v in file_list if 'safetensors' in v or 'ckpt' in v]
                operation_progress.setLabelText('Loading model file......')
                operation_progress.setRange(0, len(file_list) + 1)
                operation_progress.update_value()
                QApplication.processEvents()
                io.model_hash_maker(file_list, operation_progress)
                MessageBox('Finished', "I'm knackered", 'ok', 'info', self)

    def tab_link(self):
        if self.tab_linker_enable[0]:
            self.tab_linker_enable = [False, None]
        else:
            current_tab_index = self.root_tab.currentIndex()
            current_tab_page = self.root_tab.widget(current_tab_index)
            extension_tab = current_tab_page.findChild(QTabWidget, 'extension_tab')
            extension_tab_index = extension_tab.currentIndex()
            extension_tab_text = extension_tab.tabText(extension_tab_index) if extension_tab else None
            self.tab_linker_enable = [True, extension_tab_text]

    def not_yet_implemented(self):
        MessageBox('Sorry, not yet implemented...', 'pyPromptChecker', 'ok', 'info', self)

    def closeEvent(self, event):
        trash_bin = os.path.join(os.path.abspath(''), '.trash')
        if os.path.exists(trash_bin):
            ask = config.get('AskIfClearTrashBin')
            if not io.is_directory_empty(trash_bin):
                answer = None
                if ask:
                    text = 'Do you want to obliterate files in the trash bin ?'
                    answer = MessageBox(text, 'pyPromptChecker', 'okcancel', 'question', self)
                if answer.success or not ask:
                    io.clear_trash_bin(trash_bin)
        event.accept()
        QApplication.quit()


def from_main(purpose, target_data=None):
    if purpose == 'directory':
        app = QApplication(sys.argv)
        qdarktheme.setup_theme('auto')
        open_directory = Dialog()
        open_directory.init_dialog('choose-directory', 'Select directory')
        result = open_directory.result
        return result
    elif purpose == 'files':
        app = QApplication(sys.argv)
        qdarktheme.setup_theme('auto')
        open_files = Dialog()
        open_files.init_dialog('choose-files', 'Select files', None, 'PNG')
        result = open_files.result
        return result
    elif purpose == 'progress':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        qdarktheme.setup_theme('auto')
        progress = ProgressDialog()
        return app, progress
    elif purpose == 'result':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        result_window = ResultWindow(target_data)
        qdarktheme.setup_theme('auto')
        result_window.show()
        sys.exit(app.exec())
