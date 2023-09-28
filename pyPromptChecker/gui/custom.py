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
    else:
        return


def custom_text(purpose):
    pass


def custom_keybindings(purpose):
    pass
