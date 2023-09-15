# -*- coding: utf-8 -*-

from .dialog import MessageBox
from functools import lru_cache
from PyQt6.QtWidgets import QDialog, QGridLayout, QGroupBox, QCheckBox, QSlider
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QComboBox
from PyQt6.QtWidgets import QRadioButton
from PyQt6.QtGui import QPixmap, QImageReader, QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression


class SearchWindow(QDialog):
    def __init__(self, model_list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.conditions = {}
        self.result = 'Tabs'
        self.prompt = None
        self.status = None
        self.extension = None
        self.search_box = None
        self.search_model = None
        self.search_seed_box = None
        self.search_cfg_label = None
        self.search_button = None
        self.central_widget = None
        self.init_search_window(model_list)

    def init_search_window(self, model_list):
        layout = QGridLayout()

        result_label = QLabel('Result shows: ')
        result_box = QComboBox()
        result_box.addItems(['Tabs', 'Listview', 'Thumbnails'])
        result_box.currentIndexChanged.connect(self.result_change)

        prompt_group = QGroupBox()
        prompt_group.setTitle('Search Keywords')
        prompt_group.setCheckable(True)
        prompt_group.setChecked(True)
        prompt_group_layout = QGridLayout()

        search_label = QLabel('Search words : ')
        self.search_box = QLineEdit(self)

        for i, tmp in enumerate(['Positive', 'Negative', 'Region control']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            prompt_group_layout.addWidget(checkbox, 2, i + 1)
            if tmp == 'Positive':
                checkbox.setChecked(True)

        checkbox = QCheckBox('Case insensitive')
        checkbox.setObjectName('Case insensitive')
        prompt_group_layout.addWidget(checkbox, 3, 2, 1, 2)

        checkbox = QCheckBox('Use regex')
        checkbox.setObjectName('Use regex')
        checkbox.setDisabled(True)
        prompt_group_layout.addWidget(checkbox, 3, 1)

        prompt_group_layout.addWidget(search_label, 1, 0)
        prompt_group_layout.addWidget(self.search_box, 1, 1, 1, 3)
        prompt_group.setLayout(prompt_group_layout)
        self.prompt = prompt_group

        status_group = QGroupBox()
        status_group.setTitle('Status')
        status_group.setCheckable(True)
        status_group.setChecked(False)
        status_group_layout = QGridLayout()

        search_model_label = QLabel('Model : ')
        self.search_model = QComboBox()
        self.search_model.addItems(model_list)

        status_group_layout.addWidget(search_model_label, 0, 0)
        status_group_layout.addWidget(self.search_model, 0, 1, 1, 3)

        search_seed_label = QLabel('Search seed : ')
        self.search_seed_box = QLineEdit(self)
        reg_ex = QRegularExpression('^[0-9]*')
        validator = QRegularExpressionValidator(reg_ex)
        self.search_seed_box.setValidator(validator)

        self.search_cfg_label = QLabel('CFG : 0')
        search_cfg = QSlider()
        search_cfg.setOrientation(Qt.Orientation.Horizontal)
        search_cfg.setTickInterval(1)
        search_cfg.setRange(0, 40)
        search_cfg.valueChanged.connect(self.value_change)

        for i, tmp in enumerate(['Less than', 'Equal to', 'Greater than']):
            radio_button = QRadioButton(tmp)
            radio_button.setObjectName(tmp)
            status_group_layout.addWidget(radio_button, 3, i + 1)
            if tmp == 'Equal to':
                radio_button.setChecked(True)

        status_group_layout.addWidget(search_seed_label, 1, 0)
        status_group_layout.addWidget(self.search_seed_box, 1, 1, 1, 3)
        status_group_layout.addWidget(self.search_cfg_label, 2, 0)
        status_group_layout.addWidget(search_cfg, 2, 1, 1, 3)

        status_group.setLayout(status_group_layout)
        self.status = status_group

        extension_group = QGroupBox()
        extension_group.setTitle('Extensions')
        extension_group.setCheckable(True)
        extension_group.setChecked(False)
        extension_group_layout = QGridLayout()

        for i, tmp in enumerate(['LoRa / AddNet', 'Hires / Extras', 'CFG']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            extension_group_layout.addWidget(checkbox, 0, i)

        for i, tmp in enumerate(['Tiled diffusion', 'ControlNet', 'Regional prompter']):
            checkbox = QCheckBox(tmp)
            checkbox.setObjectName(tmp)
            extension_group_layout.addWidget(checkbox, 1, i)

        extension_group.setLayout(extension_group_layout)
        self.extension = extension_group

        search_button = QPushButton("Search", self)
        search_button.clicked.connect(self.search)
        close_button = QPushButton('Close', self)
        close_button.clicked.connect(self.window_close)

        layout.addWidget(result_label, 0, 0)
        layout.addWidget(result_box, 0, 1, 1, 3)
        layout.addWidget(prompt_group, 1, 0, 2, 4)
        layout.addWidget(status_group, 4, 0, 2, 4)
        layout.addWidget(extension_group, 6, 0, 2, 4)
        layout.addWidget(search_button, 8, 0, 1, 2)
        layout.addWidget(close_button, 8, 2, 1, 2)

        central_widget = QWidget()
        central_widget.setLayout(layout)
        self.setLayout(layout)

    def show_dialog(self):
        self.show()

    def result_change(self):
        self.result = self.sender().currentText()

    def value_change(self):
        self.search_cfg_label.setText('CFG : ' + str(self.sender().value() * 0.5))

    def window_close(self):
        self.close()

    def search(self):
        self.conditions['Result'] = self.result
        if self.prompt.isChecked():
            self.conditions['Search'] = self.search_box.text()
            for tmp in self.prompt.findChildren(QCheckBox):
                key = tmp.objectName()
                self.conditions[key] = tmp.isChecked()
        self.conditions['Prompt'] = self.prompt.isChecked()

        if self.status.isChecked():
            relation = 'Greater than'
            for tmp in self.status.findChildren(QRadioButton):
                if tmp.isChecked():
                    relation = tmp.objectName()
                    break

            keys = ['Model', 'Seed', 'CFG', 'Relation']
            seek = [self.search_model.currentText(),
                    self.search_seed_box.text(),
                    self.search_cfg_label.text().replace('CFG : ', ''),
                    relation]

            for index, key in enumerate(keys):
                self.conditions[key] = seek[index]
        self.conditions['Status'] = self.status.isChecked()

        if self.extension.isChecked():
            for tmp in self.extension.findChildren(QCheckBox):
                self.conditions[tmp.objectName()] = tmp.isChecked()
        self.conditions['Extension'] = self.extension.isChecked()

        if self.validation():
            self.parent().tab_search(self.conditions)

    def validation(self):
        words = self.conditions.get('Search', 'None')
        count = words.count('"')

        if count % 2 != 0:
            text = 'There are not an even number of double quotes.'
            MessageBox(text, 'Please check it out', 'ok', 'info', self)
            return False

        if ' | ' in words:
            text = 'There is space on either side of |.'
            MessageBox(text, 'Please check it out', 'ok', 'info', self)
            return False

        return True


@lru_cache(maxsize=1000)
def portrait_generator(filepath, size):
    image_reader = QImageReader(filepath)
    pixmap = QPixmap.fromImageReader(image_reader)
    pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    return pixmap
