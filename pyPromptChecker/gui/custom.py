# -*- coding: utf-8 -*-

import os
import sys
from PyQt6.QtGui import QKeySequence, QShortcut, QColor

from . import config


def custom_stylesheet(category: str, purpose: str):
    if category == 'groupbox':
        style = 'QGroupBox {border: 2px solid @@@ ; padding : 1px 0 0 0; }'
        return style.replace('@@@', custom_color(purpose))
    elif category == 'colour':
        style = 'color: @@@;'
        return style.replace('@@@', custom_color(purpose))
    elif category == 'border':
        style = 'border: 2px solid @@@'
        return style.replace('@@@', custom_color(purpose))
    elif category == 'label':
        style = 'border-top: 2px solid transparent; border-bottom: 2px solid @@@ ; border-radius: 0px'
        return style.replace('@@@', custom_color(purpose))
    elif category == 'extension_label':
        style = 'border-radius: 5px ; border: 2px solid @@@ ; background-color: @@@ ; color: white ;'
        return style.replace('@@@', custom_color(purpose))
    elif category == 'extension_label_disable':
        return 'border-radius: 5px ; border: 1px solid palette(shadow);'
    elif category == 'title':
        style = 'QGroupBox::title {color: @@@; }'
        return style.replace('@@@', custom_color(purpose))
    elif category == 'slider':
        return custom_color(purpose)
    elif category == 'theme':
        if purpose == 'dark':
            return ("QPushButton { color: rgba(134, 206, 203, 1.0); } "
                    "QPushButton:hover { background:rgba(134, 206, 203, 0.110) } "
                    "QPushButton:default { background: rgba(134, 206, 203, 1.0); } "
                    "QPushButton:default:hover {background: rgba(134, 206, 203, 1.0); } "
                    "QPushButton:default:pressed,QPushButton:default:checked {background: rgba(134, 206, 203, 1.0); } "
                    "QLabel { selection-background-color: rgba(19, 122, 127, 1.0); } "
                    "QTextEdit:focus, QTextEdit:selected, QLineEdit:focus, QLineEdit:selected { selection-background-color: rgba(19, 122, 127, 1.0); } "
                    "QTextEdit:focus, QLineEdit:focus { border-color: rgba(134, 206, 203, 1.0); } "
                    "QSplitter:handle:hover { background-color: rgba(134, 206, 203, 1.0); } "
                    "QTabBar:tab:selected:enabled { color: rgba(134, 206, 203, 1.0); border-color: rgba(134, 206, 203, 1.0); } "
                    "QProgressBar::chunk {background: rgba(134, 206, 203, 1.0); } "
                    "QCheckBox:hover,QRadioButton:hover {border-bottom:2px solid rgba(134, 206, 203, 1.0); }"
                    "QSlider::sub-page:horizontal,QSlider::add-page:vertical,QSlider::handle {background: rgba(134, 206, 203, 1.0)}"
                    "QComboBox::item:selected {background: rgba(134, 206, 203, 0.400);}"
                    "QComboBox:focus, QComboBox:open {border-color: rgba(134, 206, 203, 1.0)}"
                    "QComboBox::item:selected {border:none; background:rgba(134, 206, 203, 0.400); border-radius:4px}")

        if purpose == 'light':
            return ("QPushButton { color: rgba(19, 122, 127, 1.0); } "
                    "QPushButton:hover { background:rgba(134, 206, 203, 0.110) } "
                    "QPushButton:default { background: rgba(19, 122, 127, 1.0); } "
                    "QPushButton:default:hover {background: rgba(19, 122, 127, 1.0); } "
                    "QPushButton:default:pressed,QPushButton:default:checked {background: rgba(19, 122, 127, 1.0); } "
                    "QLabel { selection-background-color: rgba(19, 122, 127, 0.65); } "
                    "QTextEdit:focus, QTextEdit:selected, QLineEdit:focus, QLineEdit:selected { selection-background-color: rgba(19, 122, 127, 0.65); } "
                    "QTextEdit:focus, QLineEdit:focus { border-color: rgba(19, 122, 127, 1.0); } "
                    "QSplitter:handle:hover { background-color: rgba(19, 122, 127, 0.5); } "
                    "QTabBar:tab:selected:enabled { color: rgba(19, 122, 127, 1.0); border-color: rgba(19, 122, 127, 1.0); } "
                    "QProgressBar::chunk {background: rgba(19, 122, 127, 0.8); } "
                    "QCheckBox:hover,QRadioButton:hover {border-bottom:2px solid rgba(19, 122, 127, 1.0); }"
                    "QSlider::sub-page:horizontal,QSlider::add-page:vertical,QSlider::handle {background: rgba(19, 122, 127, 1.0)}"
                    "QComboBox::item:selected {background: rgba(19, 122, 127, 0.400);}"
                    "QComboBox:focus, QComboBox:open {border-color: rgba(19, 122, 127, 1.0)}"
                    "QComboBox::item:selected {border:none; background:rgba(19, 122, 127, 0.400); border-radius:4px}")


def custom_color(purpose: str):
    if purpose == 'Q_moved':
        return QColor(0, 112, 255, 255)
    elif purpose == 'Q_deleted':
        return QColor(204, 0, 34, 255)
    elif purpose == 'Q_matched':
        return QColor(19, 122, 127, 128)
    elif purpose == 'current':
        return 'rgba(134, 206, 203, 1.0)'
    elif purpose == 'moved':
        return 'rgba(0, 112, 255, 1.0)'
    elif purpose == 'deleted':
        return 'rgba(204, 0, 34, 1.0)'
    elif purpose == 'matched':
        return 'rgba(19, 122, 127, 1.0)'
    elif purpose == 'leave':
        return 'transparent'
    elif purpose == 'hover':
        return 'rgba(134, 206, 203, 1.0)'
    elif purpose == 'available' or purpose == 'txt2img':
        return 'palette(highlight)'
    elif purpose == 'PNG':
        return 'green'
    elif purpose == 'JPEG':
        return 'blue'
    elif purpose == 'WEBP' or purpose == 'img2img' or purpose == 'inpaint':
        return 'red'
    elif purpose == 'confidence':
        return 'QSlider::handle:horizontal {height: 0px; width: 0px; border-radius: 0px; }' \
               'QSlider::sub-page {background: rgba(134, 206, 203, 0.8)}'
    else:
        return


# noinspection PyUnresolvedReferences
def custom_keybindings(parent):
    if parent.parent() is not None:
        parent = parent.parent()

    toggle_theme_shortcut = QShortcut(QKeySequence('Ctrl+D'), parent)
    toggle_tab_bar_shortcut = QShortcut(QKeySequence('Ctrl+B'), parent)
    add_tab_shortcut = QShortcut(QKeySequence('Ctrl+O'), parent)
    replace_tab_shortcut = QShortcut(QKeySequence('Ctrl+N'), parent)
    quit_shortcut = QShortcut(QKeySequence('Ctrl+Q'), parent)

    toggle_tab_bar_shortcut.activated.connect(parent.bar_toggle)
    toggle_theme_shortcut.activated.connect(parent.change_themes)
    add_tab_shortcut.activated.connect(parent.reselect_files_append)
    replace_tab_shortcut.activated.connect(parent.reselect_files)
    quit_shortcut.activated.connect(lambda: sys.exit())


def custom_filename(filepath: str, category: str):
    if category == 'single':
        filename = config.get('JsonSingle', 'filename')
        if filename == 'filename':
            filename = os.path.splitext(os.path.basename(filepath))[0] + '.json'

    elif category == 'all':
        filename = config.get('JsonMultiple', 'directory')
        if filename == 'directory':
            filename = os.path.basename(os.path.dirname(filepath)) + '.json'

    else:
        filename = config.get('JsonSelected', 'selected')
        if filename == 'selected':
            filename = os.path.splitext(os.path.basename(filepath))[0] + '_and_so_on.json'

    return filename


def custom_text(purpose):
    if purpose == '404':
        return "Couldn't find destination directory.\nPlease check your selected directory exists."
