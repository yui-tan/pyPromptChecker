# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox, QLabel, QWidget, QVBoxLayout
from PyQt6.QtWidgets import QDialog, QRadioButton, QPushButton, QHBoxLayout, QComboBox, QSlider, QGridLayout
from PyQt6.QtCore import Qt, QTimer
from .widget import move_centre


class SelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Model hash extractor')
        self.selected = 0
        self.model = None
        self.lora = None
        self._init_select_dialog()
        self.resize(200, 80)

    def _init_select_dialog(self):
        layout = QVBoxLayout()
        button_layout = QHBoxLayout()

        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        self.model = QRadioButton('Model / VAE hash')
        self.model.setChecked(True)
        self.model.toggled.connect(self._toggle_radio_button)
        self.lora = QRadioButton('LoRa / Textual inversion hash')
        self.lora.toggled.connect(self._toggle_radio_button)
        layout.addWidget(self.model)
        layout.addWidget(self.lora)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def _toggle_radio_button(self):
        if self.model.isChecked():
            self.selected = 0
        elif self.lora.isChecked():
            self.selected = 1


class InterrogateSelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Interrogate Settings')
        self.selected_model = 'moat'
        self.tag_threshold = 0.35
        self.tag_label = QLabel()
        self.chara_threshold = 0.85
        self.chara_label = QLabel()

        self._init_interrogate_dialog()

    def _init_interrogate_dialog(self):
        root_layout = QGridLayout()

        for index, name in enumerate(('Model', 'Tag threshold', 'Character threshold')):
            label = QLabel(name + ' :')
            label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            root_layout.addWidget(label, index, 0)

            if index == 0:
                value = QComboBox()
                value.addItems(('MOAT', 'Swin', 'ConvNext', 'ConvNextV2', 'ViT'))
                value.currentIndexChanged.connect(self._model_change)
                root_layout.addWidget(value, index, 1, 1, 2)

            else:
                value = self.tag_threshold if index == 1 else self.chara_threshold
                int_value = self.tag_label if index == 1 else self.chara_label
                int_value.setText(str(value))
                int_value.setFixedSize(40, 25)
                root_layout.addWidget(int_value, index, 1)

                slider = QSlider()
                slider.setObjectName(name)
                slider.setRange(0, 100)
                slider.setMinimumWidth(200)
                slider.setValue(int(value * 100))
                slider.setOrientation(Qt.Orientation.Horizontal)
                slider.valueChanged.connect(self._threshold_change)
                root_layout.addWidget(slider, index, 2)

        button_layout = QHBoxLayout()
        ok_button = QPushButton('OK')
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)
        root_layout.addLayout(button_layout, 3, 0, 1, 3)

        self.setLayout(root_layout)

    def _model_change(self):
        self.selected_model = self.sender().currentText()

    def _threshold_change(self):
        value = float(self.sender().value() / 100)
        if self.sender().objectName() == 'Tag threshold':
            self.tag_threshold = value
            self.tag_label.setText(str(value))
        else:
            self.chara_threshold = value
            self.chara_label.setText(str(value))


class FileDialog(QFileDialog):

    def __init__(self, category: str, title: str, parent=None, file_filter: str = None, filename: str = None):
        super().__init__(parent)
        self.result = None
        self.file_filter = ''
        self.setWindowTitle(title)
        self._set_filter(file_filter)
        self.setDirectory(os.path.expanduser('~'))
        self.category = category
        self._set_category(self.category, filename)

        if self.exec():
            self.result = self.selectedFiles()

    def _set_category(self, category: str, filename: str):
        if category == 'save-file':
            self.setFileMode(QFileDialog.FileMode.AnyFile)
            self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            self.setNameFilter(self.file_filter)
            self.setOption(QFileDialog.Option.ShowDirsOnly, False)
            self.selectFile(filename)
        elif category == 'choose-files':
            self.setFileMode(QFileDialog.FileMode.ExistingFiles)
            self.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            self.setNameFilter(self.file_filter)
            self.setOption(QFileDialog.Option.ShowDirsOnly, False)
        elif category == 'choose-directory':
            self.setFileMode(QFileDialog.FileMode.Directory)
            self.setOption(QFileDialog.Option.ShowDirsOnly, True)

    def _set_filter(self, str_filter: str):
        if str_filter == 'JSON':
            self.file_filter = 'JSON Files(*.json)'
        elif str_filter == 'PNG':
            self.file_filter = 'Image files(*.png *.jpg *.jpeg *.webp)'


class ProgressDialog(QProgressDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Progress")
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self.setCancelButton(None)
        self.setMinimumDuration(0)
        self.setValue(0)
        self.now = 0
        move_centre(self)

    def update_value(self):
        now = self.now + 1
        self.setValue(now)
        self.now = now


class MessageBox(QMessageBox):
    def __init__(self, text: str, title: str = 'pyPromptChecker', style: str = 'ok', icon: str = 'info', parent=None):
        super().__init__(parent)
        self.success = False
        self.setText(text)
        self.setWindowTitle(title)
        self._set_style(style)
        self._add_icon(icon)

        self.result = self.exec()

        if self.result == QMessageBox.StandardButton.Ok:
            self.success = True

    def _set_style(self, style: str):
        if 'ok' in style:
            self.addButton(QMessageBox.StandardButton.Ok)
        if 'no' in style:
            self.addButton(QMessageBox.StandardButton.No)
        if 'cancel' in style:
            self.addButton(QMessageBox.StandardButton.Cancel)

    def _add_icon(self, icon: str):
        if icon == 'critical':
            self.setIcon(QMessageBox.Icon.Critical)
        elif icon == 'warning':
            self.setIcon(QMessageBox.Icon.Warning)
        elif icon == 'question':
            self.setIcon(QMessageBox.Icon.Question)
        elif icon == 'no':
            self.setIcon(QMessageBox.Icon.NoIcon)
        else:
            self.setIcon(QMessageBox.Icon.Information)


class Toast(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.timer = None
        self.message_label = QLabel()
        self.setWindowTitle("Toast")
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(50, 50, 50, 150); color: white; padding: 10px; border-radius: 5px;")
        self.hide()

        toast_layout = QVBoxLayout()
        toast_layout.addWidget(self.message_label)
        self.setLayout(toast_layout)

    def init_toast(self, message: str, duration: int = 2000):
        self.message_label.setText(message)
        self.show()
        self.adjustSize()
        adjust_x = int(self.sizeHint().width() / 2)
        adjust_y = int(self.sizeHint().height() / 2)
        width = self.parent().rect().width()
        height = self.parent().rect().height()
        x = int(width / 2)
        y = int(height / 2)
        self.move(x - adjust_x, y - adjust_y)

        self.timer = QTimer()
        self.timer.timeout.connect(self._close_toast)
        self.timer.start(duration)

    def _close_toast(self):
        self.timer.stop()
        self.close()
