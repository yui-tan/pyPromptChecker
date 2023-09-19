# -*- coding: utf-8 -*-

import os
from PyQt6.QtWidgets import QFileDialog, QProgressDialog, QMessageBox, QLabel, QWidget, QVBoxLayout, QApplication
from PyQt6.QtWidgets import QDialog, QRadioButton, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer, pyqtSignal


class PixmapLabel(QLabel):
    clicked = pyqtSignal()
    rightClicked = pyqtSignal()

    def __init__(self, parent=None):
        super(PixmapLabel, self).__init__(parent)
        self.setStyleSheet("border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        return QLabel.mousePressEvent(self, event)


class SelectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Model hash extractor')
        self.selected = 0
        self.model = None
        self.lora = None
        self.init_select_dialog()
        self.resize(200, 80)

    def init_select_dialog(self):
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
        self.model.toggled.connect(self.toggle_radio_button)
        self.lora = QRadioButton('LoRa / Textual inversion hash')
        self.lora.toggled.connect(self.toggle_radio_button)
        layout.addWidget(self.model)
        layout.addWidget(self.lora)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def toggle_radio_button(self):
        if self.model.isChecked():
            self.selected = 0
        elif self.lora.isChecked():
            self.selected = 1


class FileDialog(QFileDialog):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.result = None
        self.setDirectory(os.path.expanduser('~'))
        self.file_filter = 'All files(*.*)'

    def init_dialog(self, category, title, filename=None, file_filter=None):
        self.result = None
        self.setWindowTitle(title)
        self.set_filter(file_filter)
        self.set_category(category, filename)

        if self.exec():
            self.result = self.selectedFiles()

    def set_category(self, category, filename):
        if category == 'save-file':
            self.setFileMode(QFileDialog.FileMode.AnyFile)
            self.setAcceptMode(QFileDialog.AcceptMode.AcceptSave)
            self.setNameFilter(self.file_filter)
            self.setOption(QFileDialog.Option.ShowDirsOnly, False)
            self.selectFile(filename)
        elif category == 'choose-files':
            self.selectFile('*')
            self.setFileMode(QFileDialog.FileMode.ExistingFiles)
            self.setAcceptMode(QFileDialog.AcceptMode.AcceptOpen)
            self.setNameFilter(self.file_filter)
            self.setOption(QFileDialog.Option.ShowDirsOnly, False)
        elif category == 'choose-directory':
            self.selectFile('*')
            self.setFileMode(QFileDialog.FileMode.Directory)
            self.setOption(QFileDialog.Option.ShowDirsOnly, True)

    def set_filter(self, str_filter):
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
        self.move_centre(parent)

    def update_value(self):
        now = self.now + 1
        self.setValue(now)
        self.now = now

    def move_centre(self, parent=None):
        if not parent or not parent.isVisible():
            screen_center = QApplication.primaryScreen().geometry().center()
        else:
            screen_center = parent.geometry().center()
        frame_geometry = self.frameGeometry()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())


class MessageBox(QMessageBox):
    def __init__(self, text, title='pyPromptChecker', style='ok', icon='info', parent=None):
        super().__init__(parent)
        self.success = False
        self.setText(text)
        self.setWindowTitle(title)
        self.set_style(style)
        self.add_icon(icon)

        self.result = self.exec()

        if self.result == QMessageBox.StandardButton.Ok:
            self.success = True

    def set_style(self, style):
        if 'ok' in style:
            self.addButton(QMessageBox.StandardButton.Ok)
        if 'no' in style:
            self.addButton(QMessageBox.StandardButton.No)
        if 'cancel' in style:
            self.addButton(QMessageBox.StandardButton.Cancel)

    def add_icon(self, icon):
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
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.WindowDoesNotAcceptFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background-color: rgba(50, 50, 50, 150); color: white; padding: 10px; border-radius: 5px;")
        self.hide()

        toast_layout = QVBoxLayout()
        toast_layout.addWidget(self.message_label)
        self.setLayout(toast_layout)

    def init_toast(self, message, duration=2000):
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
        self.timer.timeout.connect(self.close_toast)
        self.timer.start(duration)

    def close_toast(self):
        self.timer.stop()
        self.close()
