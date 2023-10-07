# -*- coding: utf-8 -*-

import os.path
import sys
import qdarktheme

from PyQt6.QtWidgets import QApplication, QLabel, QTabWidget, QHBoxLayout, QGridLayout, QPushButton, QComboBox, QTextEdit
from PyQt6.QtGui import QKeySequence, QPalette, QIcon
from PyQt6.QtCore import Qt, QPoint, QTimer

from .dialog import *
from .widget import *
from .menu import *
from .viewer import *
from .thumbnail import *
from .listview import *
from .tab import *
from .custom import *
from .search import SearchWindow
from . import config

from pyPromptChecker.lib import *
from pyPromptChecker.lora import *

# sys.path.append('../')
# from lib import *
# from lora import *


class ResultWindow(QMainWindow):
    def __init__(self, targets=None):
        super().__init__()
        self.dark = config.get('AlwaysStartWithDarkMode')
        self.hide_tab = config.get('OpenWithShortenedWindow', False)

        self.root_tab = None
        self.tab_bar = None
        self.dialog = None
        self.search = None
        self.toast_window = None
        self.progress_bar = None

        self.params = []
        self.retracted = []

        self.moved = set()
        self.deleted = set()

        self.extract_data(targets)

        self.image_window = ImageWindow(self)
        self.thumbnail = ThumbnailView(self)
        self.listview = Listview(self)
        self.main_menu = MainMenu(self)

        self.tab_linker = TabMenu(self)
        self.tab_linker_enable = [False, 'Prompt']

        self.setWindowTitle('PNG Prompt Data')

        custom_keybindings(self)

        self.show()
        self.adjustSize()
        self.move_centre_main()

    def init_ui(self):
        tab_navigation_enable = config.get('TabNavigation', True)
        tab_minimums = config.get('TabNavigationMinimumTabs', True)
        thumbnail_tab_bar = config.get('ThumbnailTabBar', False)
        tab_bar_orientation = config.get('ThumbnailTabBarVertical', True)
        filepaths = [value.params.get('Filepath') for value in self.params]

        self.moved.clear()
        self.deleted.clear()

        length = 2 if tab_bar_orientation else 1
        tab_bar_position = 1 if tab_bar_orientation else 0
        row_position = 1 if tab_bar_orientation else 2

        self.root_tab = QTabWidget()
        root_layout = QGridLayout()
        central_widget = QWidget()

        footer_layout = make_footer_area(self)
        self.make_root_tab()

        if tab_navigation_enable and self.root_tab.count() > tab_minimums:
            root_layout.addLayout(tab_navigation(self), 0, 0, 1, length)

        if thumbnail_tab_bar and self.root_tab.count() > 1:
            self.tab_bar = TabBar(filepaths, tab_bar_orientation, self)
            root_layout.addWidget(self.tab_bar, 1, tab_bar_position)
            toggle_button = QPushButton('<')
            toggle_button.setObjectName('bar_toggle')
            toggle_button.setFixedSize(25, 25)
            toggle_button.clicked.connect(self.button_clicked)
            footer_layout.addWidget(toggle_button)

        root_layout.addWidget(self.root_tab, row_position, 0)
        root_layout.addLayout(footer_layout, row_position + 1, 0, 1, length)

        central_widget.setLayout(root_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

        self.root_tab.currentChanged.connect(self.tab_changed)

        self.toast_window = Toast(self)

    def extract_data(self, targets):
        png_index = config.get('TargetChunkIndex', 1)
        ignore = config.get('IgnoreIfDataIsNotEmbedded', False)
        lora_name = config.get('ModelListSearchApplyLora', False)
        ti_name = config.get('ModelListSearchApplyTi', False)
        valid_total = len(targets)
        is_add = bool(self.params)

        if len(targets) > 5:
            self.progress_bar = ProgressDialog(self)
            self.progress_bar.setRange(0, len(targets) * 2)
            self.progress_bar.setLabelText('Extracting PNG Chunk...')

        models = io.import_model_list(config.get('ModelList', 'model_list.csv'))

        for array in targets:
            filepath, filetype = array
            chunk_data, original_size = chunk_text_extractor(filepath, filetype, png_index)

            if not chunk_data and ignore:
                valid_total -= 1
                continue
            elif not original_size:
                valid_total -= 1
                continue

            parameters = ChunkData(chunk_data, filepath, filetype, original_size)
            parameters.init_class()

            if parameters.params.get('Positive') == 'This file has no embedded data' and ignore:
                valid_total -= 1
                continue

            parameters.model_name(models)
            parameters.vae_name(models)

            if lora_name:
                parameters.override_lora(models)
                parameters.override_addnet_model(models)

            if ti_name:
                parameters.override_textual_inversion(models)

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
            main_section.setTitle(tmp.params.get('Filename', 'None'))
            tmp.used_params['Filename'] = True

            main_section_layout = QHBoxLayout()
            main_label_layout = make_main_section(tmp)
            main_section_layout.addLayout(main_label_layout)
            main_section_layout.setContentsMargins(5, 5, 0, 5)
            main_section.setLayout(main_section_layout)
            tab_page_layout.addWidget(main_section)

            main_section_height = config.get('PixmapSize', 350) + 60
            main_section.setFixedHeight(main_section_height)

            pixmap_label = main_section.findChild(PixmapLabel, 'Pixmap')
            if pixmap_label:
                pixmap_label.clicked.connect(self.pixmap_clicked)
            for button in ['Favourite', 'Move to', 'Delete']:
                managing_button = main_section.findChild(QPushButton, button)
                if managing_button:
                    managing_button.clicked.connect(self.managing_button_clicked)

            dummy_widget = QWidget()
            tab_page_layout.addWidget(dummy_widget)

            hires_tab = ['Hires upscaler', 'Face restoration', 'Extras']
            cfg_fix_auto_tab = ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler']
            lora_tab = ['Lora', 'AddNet Enabled', 'Textual inversion']

            tabs = [['Prompts', True, True],
                    ['Hires.fix / Extras',
                     any(key in v for v in tmp.params for key in hires_tab),
                     config.get('HiresExtras', True)],
                    ['CFG',
                     any(key in v for v in tmp.params for key in cfg_fix_auto_tab),
                     config.get('CFG', True)],
                    ['LoRa / Add networks',
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
                    inner_page.setMinimumHeight(config.get('PixmapSize', 350))
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
                        inner_page = make_regional_prompter_tab(tmp)
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

            if self.hide_tab:
                inner_tab.hide()

            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            if 'File count' in tmp.params:
                del tmp.params['File count']

            if config.get('UsesNumberAsTabName', False):
                self.root_tab.addTab(tab_page, str(image_count + 1))
            else:
                self.root_tab.addTab(tab_page, tmp.params.get('Filename', '---'))

            self.root_tab.setTabToolTip(shown_tab + image_count, tmp.params.get('Filename', '---'))
            image_count += 1

        if total != image_count and self.centralWidget():
            self.post_add_tab()

        if self.progress_bar:
            self.progress_bar.close()

        hide_normal_tab_bar = config.get('HideNormalTabBar', False)
        thumbnail_tab_bar = config.get('ThumbnailTabBar', False)
        if all([thumbnail_tab_bar, hide_normal_tab_bar]) or len(self.params) == 1:
            self.root_tab.tabBar().hide()

        model_list = [value.params.get('Model') for value in self.params if value.params.get('Model') is not None]
        model_list = list(set(model_list))
        model_list.sort()
        model_list.insert(0, '')
        model_list.append('None')
        self.search = SearchWindow(model_list, self)

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
            root_layout.addLayout(tab_navigation(self), 0, 0, 1, 2)
        elif tab_navigation_enable and tab_minimums < total and tab_navigation_box:
            filelist = [value.params.get('Filename') for value in self.params]
            tab_navigation_box.clear()
            tab_navigation_box.addItems(filelist)

        if self.tab_bar:
            filelist = [value.params.get('Filepath') for value in self.params]
            self.tab_bar.add_tab(filelist)

    def change_window(self, expand=False):
        for index in range(self.root_tab.count()):
            extension_tab = self.root_tab.widget(index).findChild(QTabWidget, 'extension_tab')
            if expand:
                extension_tab.show()
                self.hide_tab = False
            else:
                extension_tab.hide()
                self.hide_tab = True

        timer = QTimer(self)
        timer.timeout.connect(lambda: self.adjustSize())
        timer.start(10)

    def tab_changed(self):
        current_index = self.root_tab.currentIndex()
        current_page = self.root_tab.widget(current_index)
        extension_tab = current_page.findChild(QTabWidget, 'extension_tab')
        combobox = self.centralWidget().findChild(QComboBox, 'Combo')

        if combobox:
            combobox.setCurrentIndex(current_index)

        if self.tab_bar:
            self.tab_bar.image_current(current_index)

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
            self.tab_search_window()
        elif where_from == 'Restore':
            self.tab_tweak()
        elif where_from == 'Listview':
            self.open_listview()

    def button_clicked(self):
        where_from = self.sender().objectName()
        clipboard = QApplication.clipboard()
        current_page = self.root_tab.currentWidget()
        current_index = self.root_tab.currentIndex()

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
            self.export_json([current_index])

        elif where_from == 'Export JSON (All)':
            self.export_json(list(range(len(self.params))))

        elif where_from == 'Shrink':
            if self.sender().text() == 'Shrink':
                self.change_window()
                self.sender().setText('Expand')
                self.sender().setShortcut(QKeySequence('Ctrl+Tab'))
            else:
                self.change_window(True)
                self.sender().setText('Shrink')
                self.sender().setShortcut(QKeySequence('Ctrl+Tab'))

        elif where_from == '▲Menu':
            x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
            y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - self.main_menu.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            self.main_menu.exec(adjusted_pos)

        elif where_from == 'bar_toggle':
            self.tab_bar.toggle_tab_bar(self.sender())

    def managing_button_clicked(self):
        str_result = 'Added!'
        where_from = self.sender().objectName()
        current_index = self.root_tab.currentIndex()
        result = None
        error = None

        if where_from == 'Favourite':
            result, error = self.manage_image_files([current_index], self)
        elif where_from == 'Move to':
            result, error = self.manage_image_files([current_index], self, 'move')
            str_result = 'Moved!'
        elif where_from == 'Delete':
            result, error = self.manage_image_files([current_index], self, 'delete')
            str_result = 'Deleted!'

        if result and not error:
            self.toast_window.init_toast(str_result, 1000)
        elif not result and error:
            MessageBox(error[0], 'Error', 'ok', 'critical', self)

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

    def add_interrogate_tab(self, select: int = 0, indexes: tuple = None):
        progress = None
        dialog = InterrogateSelectDialog(self)
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

    def bar_toggle(self):
        if self.tab_bar:
            button = self.centralWidget().findChild(QPushButton, 'bar_toggle')
            self.tab_bar.toggle_tab_bar(button)

    def tab_search_window(self):
        if self.search.isVisible():
            self.search.activateWindow()
        else:
            self.search.show_dialog()

    def tab_tweak(self, indexes=None):
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

    def open_thumbnail(self, indexes=None):
        if self.thumbnail.isVisible():
            self.thumbnail.activateWindow()
        else:
            if indexes:
                dictionary_list = [(i, self.params[i].params) for i in indexes]
            else:
                dictionary_list = [(i, value.params) for i, value in enumerate(self.params)]
            self.thumbnail.init_thumbnail(dictionary_list, self.moved, self.deleted)

    def open_listview(self, indexes=None):
        if self.listview.isVisible():
            self.listview.activateWindow()
        else:
            if indexes:
                dictionary_list = [(i, self.params[i].params) for i in indexes]
            else:
                dictionary_list = [(i, value.params) for i, value in enumerate(self.params)]
            self.listview.init_listview(dictionary_list, self.moved, self.deleted)

    def manage_image_files(self, indexes: list, where_from, kind='favourite'):
        results = []
        ask_if = config.get('AskIfDelete', True)
        is_move = not config.get('UseCopyInsteadOfMove')

        if kind == 'favourite':
            destination = config.get('Favourites')
        elif kind == 'delete':
            destination = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.trash')
            os.makedirs(destination, exist_ok=True)
            is_move = True
        else:
            dialog = FileDialog('choose-directory', 'Select Directory', parent=where_from)
            destination = dialog.result[0] if dialog.result else None

        if kind == 'favourite' and not destination:
            text = "Couldn't find setting of destination directory.\nPlease check setting in 'config.ini' file."
            MessageBox(text, 'Error', 'ok', 'critical', where_from)
            return None, None

        elif kind == 'favourite' and not os.path.isdir(destination):
            text = "Couldn't find destination directory.\nPlease check setting in 'config.ini' file."
            MessageBox(text, 'Error', 'ok', 'critical', where_from)
            return None, None

        elif destination:
            if ask_if and kind == 'delete':
                result = MessageBox('Really?', 'Confirm', 'okcancel', 'question', where_from)
                if not result.success:
                    return None, None
            for index in indexes:
                source = self.params[index].params.get('Filepath')
                result, e = io.image_copy_to(source, destination, is_move)
                results.append([e, result, source, index])
            return self.post_manage(results, kind)
        return None, None

    def post_manage(self, results: list, kind):
        stylesheet = 'color: ' + custom_color('deleted') + ';' if kind == 'delete' else 'color: ' + custom_color('moved') + ';'
        text_color = custom_color('Q_deleted') if kind == 'delete' else custom_color('Q_moved')
        errors = []
        succeeds = []

        for result in results:
            error, filepath, source, index = result
            if not error:
                destination = os.path.dirname(filepath)
                filename = os.path.basename(filepath)
                target_page = self.root_tab.widget(index)
                self.root_tab.tabBar().setTabTextColor(index, text_color)
                self.root_tab.tabBar().setTabText(index,filename)
                filepath_label = target_page.findChild(QLabel, 'Filepath_value')
                filepath_label.setStyleSheet(stylesheet)
                filepath_label.setText(destination)
                filepath_label.setToolTip(destination)
                main_section = target_page.findChild(QGroupBox, 'main_section')
                main_section.setTitle(filename)
                move_delete_section = target_page.findChild(QWidget, 'move_delete')
                move_delete_section.refresh_filepath(filepath)
                if self.tab_bar and kind != 'delete':
                    self.tab_bar.image_moved([index])
                elif self.tab_bar and kind == 'delete':
                    self.tab_bar.image_deleted([index])
                if kind == 'delete':
                    self.deleted.add(index)
                else:
                    self.moved.add(index)
                self.params[index].params['Filepath'] = filepath
                self.params[index].params['Filename'] = filename
                succeeds.append([index, filepath])
            else:
                errors.append(f'{source}\n{filepath}\n{error}')
        return succeeds, errors

    def import_json_from_files(self):
        dialog = FileDialog('choose-files', 'Select JSONs', self, 'JSON')
        filepaths = dialog.result
        self.import_json(filepaths)

    def import_json_from_directory(self):
        dialog = FileDialog('choose-directory', 'Select directory', self)
        directory = dialog.result
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

    def export_all_text(self):
        for i in range(self.root_tab.count()):
            extension_tab = self.root_tab.widget(i).findChild(QTabWidget, 'extension_tab')
            interrogate_tab = extension_tab.findChild(QStackedWidget, 'interrogate')
            if interrogate_tab is not None:
                interrogate_tab.export_text(True)
        self.toast_window.init_toast('Exported!', 1000)

    def export_json_single(self):
        current_index = self.root_tab.currentIndex()
        self.export_json([current_index])

    def export_json_all(self):
        self.export_json(list(range(len(self.params))))

    def export_json(self, selected_files: list = None, request: str = None):
        if isinstance(selected_files, set):
            selected_files = list(selected_files)

        category = 'selected'
        if len(selected_files) == len(self.params):
            category = 'all'
        elif len(selected_files) == 1:
            category = 'single'

        filepath = self.params[selected_files[0]].params.get('Filepath')
        filename = custom_filename(filepath, category)

        dialog = FileDialog('save-file', 'Save JSON', self, 'JSON', filename)
        destination = dialog.result[0] if dialog.result else None

        if destination:
            dict_list = []
            for index in selected_files:
                dict_list.append(self.params[index].params)
            result, e = io.io_export_json(dict_list, destination)
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
        dialog = FileDialog('choose-files', 'Select files', self, 'PNG')
        filepath = dialog.result
        result_list = []
        duplicate = 0
        flag = False

        if filepath:
            if add:
                filepath, duplicate = self.reselect_files_duplicate_check(filepath)
                if not filepath:
                    MessageBox('Those files are already shown!', 'pyPromptChecker', 'ok', 'info', self)
                    return
            if add and len(self.params) == 1:
                shown_filepath = self.params[0].params.get('Filepath')
                filepath.insert(0, shown_filepath)
                flag = True
                add = False
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
            if self.listview.isVisible():
                self.listview.close()
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
        which_mode = SelectDialog(self)
        result = which_mode.exec()
        mode = which_mode.selected

        if result == QDialog.DialogCode.Accepted:
            select_directory = FileDialog('choose-directory', 'Select directory', parent=self)
            directory = select_directory.result[0] if select_directory.result else None
            if directory:
                operation_progress = ProgressDialog(self)
                file_list = os.listdir(directory)
                file_list = [os.path.join(directory, v) for v in file_list if os.path.isfile(os.path.join(directory, v))]
                file_list = [v for v in file_list if '.safetensors' in v or '.ckpt' in v or '.pt' in v]
                file_list.sort()
                operation_progress.setLabelText('Loading model file......')
                operation_progress.setRange(0, len(file_list) + 1)
                io.model_hash_maker(file_list, operation_progress, mode)
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

    def change_themes(self):
        if self.dark:
            qdarktheme.setup_theme('light')
            self.dark = False
            self.main_menu.theme_check()
        else:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
            self.dark = True
            self.main_menu.theme_check()

    def closeEvent(self, event):
        trash_bin = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.trash')
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
    theme = config.get('AlwaysStartWithDarkMode')
    icon_path = config.get('IconPath')
    if purpose == 'directory':
        app = QApplication(sys.argv)
        if theme:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
        else:
            qdarktheme.setup_theme('light')
        open_directory = FileDialog('choose-directory', 'Select directory')
        result = open_directory.result
        return result
    elif purpose == 'files':
        app = QApplication(sys.argv)
        if theme:
            qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
        else:
            qdarktheme.setup_theme('light')
        open_files = FileDialog('choose-files', 'Select files', file_filter='PNG')
        result = open_files.result
        return result
    elif purpose == 'progress':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            if icon_path:
                app.setWindowIcon(QIcon(icon_path))
            if theme:
                qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
            else:
                qdarktheme.setup_theme('light')
        progress = ProgressDialog()
        return app, progress
    elif purpose == 'result':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
            if icon_path:
                app.setWindowIcon(QIcon(icon_path))
            if theme:
                qdarktheme.setup_theme('dark', additional_qss=custom_stylesheet('theme', 'dark'))
            else:
                qdarktheme.setup_theme('light')
        result_window = ResultWindow(target_data)
        result_window.show()
        sys.exit(app.exec())
