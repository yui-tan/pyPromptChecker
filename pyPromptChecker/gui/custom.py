# -*- coding: utf-8 -*-

from PyQt6.QtGui import QKeySequence, QColor
from PyQt6.QtCore import Qt


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
    elif category == 'theme':
        if purpose == 'dark':
            return ("QPushButton { color: #86cecb; } "
                    "QPushButton:hover { background:rgba(134, 206, 203, 0.110) } "
                    "QPushButton:default { background: #86cecb; } "
                    "QPushButton:default:hover {background: #86cecb; } "
                    "QPushButton:default:pressed,QPushButton:default:checked {background: #86cecb; } "
                    "QLabel { selection-background-color: #137a7f; } "
                    "QTextEdit:focus, QTextEdit:selected { selection-background-color: #137a7f; } "
                    "QTextEdit:focus { border-color: #86cecb; } "
                    "QSplitter:handle:hover { background-color: #86cecb; } "
                    "QTabBar:tab:selected:enabled { color: #86cecb; border-color: #86cecb; } "
                    "QProgressBar::chunk {background: #86cecb; } "
                    "QCheckBox:hover,QRadioButton:hover {border-bottom:2px solid #86cecb; }")

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
                    "QCheckBox:hover,QRadioButton:hover {border-bottom:2px solid rgba(19, 122, 127, 1.0); }")


def custom_color(purpose):
    if purpose == 'Q_moved':
        return QColor(0, 112, 255, 255)
    elif purpose == 'Q_deleted':
        return QColor(204, 0, 34, 255)
    elif purpose == 'Q_matched':
        return QColor(255, 255, 255, 255)
    elif purpose == 'current':
        return 'rgba(134, 206, 203, 1.0)'
    elif purpose == 'moved':
        return 'rgba(0, 112, 255, 1.0)'
    elif purpose == 'deleted':
        return 'rgba(204, 0, 34, 1.0)'
    elif purpose == 'matched':
        return ''
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
    else:
        return


def custom_text(purpose):
    pass


def custom_keybindings(purpose):
    pass
