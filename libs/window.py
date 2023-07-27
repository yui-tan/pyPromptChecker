import sys
import os
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QTabWidget, QTextEdit, QPushButton, QFileDialog
from PyQt6.QtWidgets import QSplitter, QMainWindow, QGroupBox
from PyQt6.QtGui import QPixmap
from PyQt6.QtCore import Qt


class ResultWindow(QMainWindow):
    def __init__(self, target_data):
        super().__init__()

        self. Properties = ['Filename',
                            'Filepath',
                            'Size',
                            'Seed',
                            'Sampler',
                            'Steps',
                            'CFG scale',
                            'Model',
                            'Clip skip',
                            'ENSD',
                            'Version',
                            'Lora',
                            'Additional Networks',
                            'Tiled diffusion',
                            'Region control',
                            'ControlNet',
                            'Regional Prompter']
        self.setWindowTitle('PNG Prompt Data')
        self.params = target_data
        self.positive_for_copy = self.params[0].dictionary_get('Positive')
        self.negative_for_copy = self.params[0].dictionary_get('Negative')
        self.seed_for_copy = self.params[0].dictionary_get('Seed')
        self.tab_index = 0
        window_width = 1050
        window_height = 864
        self.setGeometry(0, 0, window_width, window_height)

        root_layout = QVBoxLayout()
        # self.setLayout(root_layout)
        self.root_tab = QTabWidget()

        for tmp in self.params:
            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            label_group = QGroupBox()
            label_group_layout = QHBoxLayout()

            label_layout = make_label_layout(self, tmp)
            label_group_layout.addLayout(label_layout)
            label_group.setLayout(label_group_layout)
            tab_page_layout.addWidget(label_group)

            for i in range(1):
                inner_page = QWidget()
                inner_page.setLayout(make_page_layout(tmp))
                inner_tab.addTab(inner_page, 'Prompts')
            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            self.root_tab.addTab(tab_page, tmp.dictionary_get('Filename'))
            self.root_tab.currentChanged.connect(self.tab_changed)

        root_layout.addWidget(self.root_tab)

        button_layout = QHBoxLayout()
        button_text = ['Positive to Clipboard',
                       'Negative to Clipboard',
                       'Seed to Clipboard',
                       'Export JSON (This Image)',
                       'Export JSON (All Images)']
        for tmp in button_text:
            copy_button = QPushButton(tmp)
            button_layout.addWidget(copy_button)
            copy_button.clicked.connect(self.button_clicked)

        root_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(root_layout)
        self.setCentralWidget(central_widget)

        self.center()

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().geometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def tab_changed(self, index):
        self.positive_for_copy = self.params[index].dictionary_get('Positive')
        self.negative_for_copy = self.params[index].dictionary_get('Negative')
        self.seed_for_copy = self.params[0].dictionary_get('Seed')
        self.tab_index = index

    def button_clicked(self):
        where_from = self.sender().text()
        clipboard = QApplication.clipboard()
        if where_from == 'Positive to Clipboard':
            if self.positive_for_copy:
                clipboard.setText(self.positive_for_copy)
        elif where_from == 'Negative to Clipboard':
            if self.negative_for_copy:
                clipboard.setText(self.negative_for_copy)
        elif where_from == 'Seed to Clipboard':
            if self.seed_for_copy:
                clipboard.setText(self.seed_for_copy)
        elif where_from == 'Export JSON (This Image)':
            data = self.params[self.tab_index]
            filepath = savefile_choose_dialog()
            data.json_export(filepath)
        elif where_from == 'Export JSON (All Images)':
            pass


def show_result_window(target_data):
    app = QApplication(sys.argv)
    window = ResultWindow(target_data)
    window.show()
    sys.exit(app.exec())


def make_page_layout(target_data):
    textbox_layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Vertical)
    positive_text = target_data.dictionary_get('Positive')
    positive_prompt = QTextEdit()
    positive_prompt.setPlainText(positive_text)
    positive_prompt.setReadOnly(True)
    negative_text = target_data.dictionary_get('Negative')
    negative_prompt = QTextEdit()
    negative_prompt.setPlainText(negative_text)
    negative_prompt.setReadOnly(True)

    splitter.addWidget(positive_prompt)
    splitter.addWidget(negative_prompt)
    textbox_layout.addWidget(splitter)

    return textbox_layout


def make_label_layout(layout, data):
    label_number = 0
    upper_label_layout = QHBoxLayout()
    label_layout = QVBoxLayout()
    for tmp in layout.Properties:
        item = data.dictionary_get(tmp)
        if item:
            status_layout = QHBoxLayout()
            title = QLabel(tmp)
            value = QLabel(item)
            size_policy_title = title.sizePolicy()
            size_policy_value = value.sizePolicy()
            size_policy_title.setHorizontalStretch(1)
            size_policy_value.setHorizontalStretch(2)
            title.setSizePolicy(size_policy_title)
            value.setSizePolicy(size_policy_value)
            status_layout.addWidget(title)
            status_layout.addWidget(value)
            label_layout.addLayout(status_layout)
            label_number = label_number + 1
            if tmp == 'Lora':
                title.setText('Loras in prompt')
                cnt = data.dictionary_length()
                for i in range(cnt):
                    key = 'Lora ' + str(i)
                    item = data.dictionary_get(key)
                    if item:
                        status_layout = QHBoxLayout()
                        title = QLabel(key)
                        value = QLabel(item)
                        size_policy_title = title.sizePolicy()
                        size_policy_value = value.sizePolicy()
                        size_policy_title.setHorizontalStretch(1)
                        size_policy_value.setHorizontalStretch(2)
                        title.setSizePolicy(size_policy_title)
                        value.setSizePolicy(size_policy_value)
                        status_layout.addWidget(title)
                        status_layout.addWidget(value)
                        label_layout.addLayout(status_layout)
                        label_number = label_number + 1
    if label_number < 11:
        for i in range(11 - label_number):
            margin = QLabel()
            label_layout.addWidget(margin)
    filepath = data.dictionary_get('Filepath')
    pixmap = make_pixmap_label(filepath)
    upper_label_layout.addWidget(pixmap)
    upper_label_layout.addLayout(label_layout)

    return upper_label_layout


def make_add_networks_tab():
    pass


def make_tiled_diffusion_tab():
    pass


def region_control_tab():
    pass


def make_control_net_tab():
    pass


def make_regional_prompter_tab():
    pass


def make_pixmap_label(filepath):
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaledToHeight(300)
    image_label = QLabel()
    image_label.setPixmap(pixmap)
    image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return image_label


def savefile_choose_dialog():
    caption = 'Save File'
    path = os.path.expanduser('~')
    default_filename = os.path.join(path, 'parameters.json')
    file_filter = 'JSON Files(*.json)'
    select_filter = ''
    filename, _ = QFileDialog.getSaveFileName(
        None,
        caption,
        default_filename,
        file_filter,
        select_filter
    )
    return filename


def file_choose_dialog():
    app = QApplication(sys.argv)
    caption = 'Select Files'
    default_dir = os.path.expanduser('~')
    file_filter = 'PNG Images(*.png)'
    select_filter = ''
    filenames = QFileDialog.getOpenFileNames(
        None,
        caption,
        default_dir,
        file_filter,
        select_filter
    )
    return filenames
