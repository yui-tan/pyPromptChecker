# -*- coding: utf-8 -*-

import sys
from . import config
from pyPromptChecker.lib import *
from .dialog import *
from .subwindow import *
from .widget import *
from PyQt6.QtWidgets import QApplication, QLabel, QTabWidget, QHBoxLayout, QPushButton, QComboBox, QTextEdit
from PyQt6.QtCore import Qt


class ResultWindow(QMainWindow):
    def __init__(self, targets=None):
        super().__init__()
        self.root_tab = None
        self.dialog = None
        self.toast_window = None
        self.progress_bar = None
        self.progress_bar_enable = False
        self.setWindowTitle('PNG Prompt Data')
        self.models = io.import_model_list(config.get('ModelList'))
        self.params = []
        self.init_ui(targets)
        self.image_window = ImageWindow(self)
        self.tab_max_count = 0

        size_hint_width = self.sizeHint().width()
        size_hint_height = self.sizeHint().height()
        max_width = config.get('MaxWindowWidth')
        max_height = config.get('MaxWindowHeight')

        window_width = size_hint_width if max_width > size_hint_width else max_width
        window_height = size_hint_height if max_height > size_hint_height else max_height
        self.resize(window_width, window_height)
        move_center(self)

    def init_ui(self, targets):
        self.progress_bar_enable = True if len(targets) > 20 else False
        ignore = config.get('IgnoreIfDataIsNotEmbedded')
        pixmap_scale = config.get('PixmapSize')
        move_delete_enable = config.get('MoveDelete')
        json_export_enable = config.get('JsonExport')
        model_hash_extractor_enable = config.get('ModelHashExtractor')
        tab_jump_enable = config.get('TabNavigation')
        tab_search_enable = config.get('TabSearch')
        error_list_parameter = config.get('ErrorList')
        total = len(targets)
        valid_total = total
        image_count = 1

        if self.progress_bar_enable:
            self.progress_bar = ProgressDialog(self)
            self.progress_bar.setRange(0, total * 2)
            self.progress_bar.setLabelText('Extracting PNG Chunk...')

        for filepath in targets:
            chunk_data = chunk_text_extractor(filepath, 1)
            parameters = parse_parameter(chunk_data, filepath, self.models)
            if parameters.params['Positive'] == 'This file has no embedded data' and ignore:
                valid_total = valid_total - 1
                continue
            self.params.append(parameters)
            if self.progress_bar_enable:
                self.progress_bar.update_value()

        if valid_total == 0:
            MessageBox('There is no data to parse.', 'Oops!')
            if self.centralWidget():
                return
            sys.exit()

        if self.progress_bar_enable:
            self.progress_bar.setLabelText('Formatting prompt data...')

        root_layout = QVBoxLayout()
        self.root_tab = QTabWidget()

        for tmp in self.params:

            if self.progress_bar_enable:
                self.progress_bar.update_value()
            if valid_total > 1:
                tmp.params['File count'] = str(image_count) + ' / ' + str(valid_total)

            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            main_section = QGroupBox()
            main_section_layout = QHBoxLayout()

            main_label_layout = make_main_section(tmp, pixmap_scale, move_delete_enable)
            main_section_layout.addLayout(main_label_layout)
            main_section.setLayout(main_section_layout)
            tab_page_layout.addWidget(main_section)

            pixmap_label = main_section.findChild(PixmapLabel, 'Pixmap')
            pixmap_label.clicked.connect(self.pixmap_clicked)

            if move_delete_enable:
                for button in ['Favourite', 'Move to', 'Delete']:
                    managing_button = main_section.findChild(QPushButton, button)
                    managing_button.clicked.connect(self.managing_button_clicked)

            hires_tab = ['Hires upscaler', 'Face restoration', 'Dynamic thresholding enabled']
            lora_tab = ['Lora', 'AddNet Enabled']

            tabs = [['Prompts', True, True],
                    ['Hires.fix / CFG scale fix',
                     any(key in v for v in tmp.params for key in hires_tab),
                     config.get('HiresCfg')],
                    ['Lora / Add networks',
                     any(key in v for v in tmp.params for key in lora_tab),
                     config.get('LoraAddNet')],
                    ['Tiled diffusion',
                     'Tiled diffusion' in tmp.params,
                     config.get('TiledDiffusion')],
                    ['Control net',
                     'ControlNet' in tmp.params,
                     config.get('ControlNet')],
                    ['Regional prompter',
                     'RP Active' in tmp.params,
                     config.get('RegionalPrompter')]
                    ]

            for index, tab in enumerate(tabs):
                if tab[1] and tab[2]:
                    inner_page = QWidget()
                    if index == 0:
                        inner_page.setLayout(make_prompt_tab(tmp))
                    if index == 1:
                        inner_page.setLayout(make_hires_other_tab(tmp))
                    if index == 2:
                        inner_page.setLayout(make_lora_addnet_tab(tmp))
                    if index == 3:
                        inner_page.setLayout(make_tiled_diffusion_tab(tmp))
                    if index == 4:
                        inner_page = (make_control_net_tab(tmp, 0))
                    if index == 5:
                        rp_pixmap_scale = config.get('RegionalPrompterPixmapSize')
                        inner_page.setLayout(make_regional_prompter_tab(tmp, rp_pixmap_scale))
                    inner_tab.addTab(inner_page, tab[0])

            if not error_list_parameter == 0:
                error_page = make_error_tab(tmp, error_list_parameter)
                inner_tab.addTab(error_page, 'Errors')

            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            self.root_tab.addTab(tab_page, tmp.params.get('Filename'))

            image_count = image_count + 1

            if 'File count' in tmp.params:
                del tmp.params['File count']

        self.tab_max_count = self.root_tab.count()

        footer_layout = make_footer_area(json_export_enable, model_hash_extractor_enable)
        for i in range(footer_layout.count()):
            widget = footer_layout.itemAt(i).widget()
            if isinstance(widget, QPushButton):
                widget.clicked.connect(self.button_clicked)

        if tab_jump_enable and self.root_tab.count() > 5:
            filename_list = [item.params['Filename'] for item in self.params]
            header_layout = make_header_area(filename_list)
            for i in range(header_layout.count()):
                widget = header_layout.itemAt(i).widget()
                if isinstance(widget, QPushButton):
                    widget.clicked.connect(self.header_button_clicked)
            root_layout.addLayout(header_layout)

        root_layout.addWidget(self.root_tab)
        root_layout.addLayout(footer_layout)

        central_widget = QWidget()
        central_widget.setLayout(root_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

        if self.progress_bar_enable:
            self.progress_bar.close()

        self.toast_window = Toast(self)
        self.dialog = Dialog(self)

    def header_button_clicked(self):
        where_from = self.sender().objectName()
        if where_from == 'Jump to':
            combo_box = self.centralWidget().findChild(QComboBox, 'target_tab')
            target_tab = combo_box.currentText()
            for index in range(self.root_tab.count()):
                if self.root_tab.tabText(index) == target_tab:
                    self.root_tab.setCurrentIndex(index)
                    break
        elif where_from == 'Search':
            pass

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
                    self.toast_window.init_ui('Positive Copied!', self.sender().geometry(), 1000, True)
        elif where_from == 'Copy negative':
            text_edit = current_page.findChild(QTextEdit, 'Negative')
            if text_edit:
                text = text_edit.toPlainText()
                if text:
                    clipboard.setText(text)
                    self.toast_window.init_ui('Negative Copied!', self.sender().geometry(), 1000, True)
        elif where_from == 'Copy seed':
            label = current_page.findChild(QLabel, 'Seed_value')
            if label:
                text = label.text()
                clipboard.setText(text)
                self.toast_window.init_ui('Seed Copied!', self.sender().geometry(), 1000, True)
        elif where_from == 'Export JSON (This)':
            data = self.params[current_index].params
            filename = config.get('JsonSingle')
            if filename == 'filename':
                filename = self.params[current_index].params.get('Filepath')
                filename = os.path.splitext(os.path.basename(filename))[0] + '.json'
            self.dialog.init_dialog('save-file', 'Save JSON', filename, 'JSON')
            filepath = self.dialog.result[0] if self.dialog.result else None
            if filepath:
                result, e = io.export_json(data, filepath)
                if not e:
                    self.toast_window.init_ui('Saved!', self.sender().geometry(), 1000, True)
                else:
                    MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)
        elif where_from == 'Export JSON (All)':
            filename = config.get('JsonMultiple')
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
                    self.toast_window.init_ui('Saved!', self.sender().geometry(), 1000, True)
                else:
                    MessageBox(result + '\n' + str(e), 'Error', 'ok', 'critical', self)
        elif where_from == 'Reselect':
            self.dialog.init_dialog('choose-files', 'Select files', None, 'PNG')
            filepath = self.dialog.result
            if filepath:
                self.params = []
                self.init_ui(filepath)
        elif where_from == 'M':
            text = 'This operation requires a significant amount of time.'
            text = text + '\n...And more than 32GiB of memory.'
            text = text + '\nDo you still want to run it ?'
            result = MessageBox(text, 'Confirm', 'okcancel', 'question', self)
            if result.success:
                self.dialog.init_dialog('choose-directory', 'Select Directory', None, '')
                directory = self.dialog.result[0] if self.dialog.result else None
                if directory:
                    operation_progress = ProgressDialog(self)
                    io.model_hash_maker(directory, operation_progress)
                    MessageBox('Finished', "I'm knackered")

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
                    self.params[current_index].params['Filepath'] = os.path.join(destination, filename)
                    self.toast_window.init_ui('Added Favourite!', self.sender().geometry(), 1000)
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
                    self.params[current_index].params['Filepath'] = os.path.join(destination, filename)
                    self.toast_window.init_ui('Moved!', self.sender().geometry(), 1000)
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
                self.root_tab.tabBar().setTabTextColor(current_index, Qt.GlobalColor.red)
                self.params[current_index].params['Filepath'] = os.path.join(destination, filename)
                self.toast_window.init_ui('Deleted!', self.sender().geometry(), 1000)
            else:
                MessageBox(result.replace('moving/copying', 'deleting') + '\n' + str(e), 'Error', 'ok', 'critical',
                           self)

    def pixmap_clicked(self):
        if not self.image_window.isVisible():
            current_index = self.root_tab.currentIndex()
            self.image_window.filepath = self.params[current_index].params.get('Filepath')
            self.image_window.init_ui()

    def closeEvent(self, event):
        trash_bin = os.path.join(os.path.abspath(''), '.trash')
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


def move_center(myself, parent=None):
    if not parent or not parent.isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = parent.geometry().center()
    frame_geometry = myself.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    myself.move(frame_geometry.topLeft())


def from_main(purpose, target_data=None):
    if purpose == 'directory':
        app = QApplication(sys.argv)
        open_directory = Dialog()
        open_directory.init_dialog('choose-directory', 'Select directory')
        result = open_directory.result
        return result
    elif purpose == 'files':
        app = QApplication(sys.argv)
        open_files = Dialog()
        open_files.init_dialog('choose-files', 'Select files', None, 'PNG')
        result = open_files.result
        return result
    elif purpose == 'progress':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        progress = ProgressDialog()
        return app, progress
    elif purpose == 'result':
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        result_window = ResultWindow(target_data)
        result_window.show()
        sys.exit(app.exec())
