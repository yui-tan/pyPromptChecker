# -*- coding: utf-8 -*-

import importlib
from functools import lru_cache
from PyQt6.QtWidgets import QHBoxLayout, QVBoxLayout, QLabel, QPushButton, QTextEdit, QSizePolicy
from PyQt6.QtWidgets import QApplication, QGroupBox, QTabWidget, QScrollArea, QSplitter, QGridLayout, QWidget
from PyQt6.QtGui import QPixmap, QPainter, QImageReader
from PyQt6.QtCore import Qt, pyqtSignal, QPoint

from .menu import *
from .custom import *
from . import config

SHORTENED = config.get('OpenWithShortenedWindow', False)
FILE_MANAGEMENT = config.get('MoveDelete', True)


class PixmapLabel(QLabel):
    clicked = pyqtSignal()
    rightClicked = pyqtSignal()
    ctrl_clicked = pyqtSignal()
    shift_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("border: none;")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.ctrl_clicked.emit()
        elif event.button() == Qt.MouseButton.LeftButton and event.modifiers() == Qt.KeyboardModifier.ShiftModifier:
            self.shift_clicked.emit()
        elif event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()
        return QLabel.mousePressEvent(self, event)


class ClickableGroup(QGroupBox):
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        return QGroupBox.mousePressEvent(self, event)


class ButtonWithMenu(QPushButton):
    clicked = pyqtSignal()
    rightClicked = pyqtSignal()

    def __init__(self, text: str = None, parent=None):
        super().__init__(parent)
        self.setText(text)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()
        elif event.button() == Qt.MouseButton.RightButton:
            self.rightClicked.emit()


class FooterButtons(QWidget):
    def __init__(self, button_layout: tuple, parent=None, controller=None):
        super().__init__()
        self.controller = controller
        self.caller = parent
        self.shortened = SHORTENED
        self.buttons = {}
        self.menus = {}

        self.__init_buttons(button_layout)
        self.__init_submenu()
        self.__establish_connection()
        self.__check_management()

    def __init_buttons(self, buttons: tuple):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        for text, name in buttons:
            if '&' in text or 'Shrink' in text:
                button = QPushButton(text, self.caller)
            else:
                button = ButtonWithMenu(text, self.caller)
            if name == 'bar_toggle' or name == 'Shrink':
                self.buttons[name] = button
            else:
                self.buttons[text] = button
            button.setObjectName(name)
            layout.addWidget(button)
        self.setLayout(layout)

    def __establish_connection(self):
        for text, button in self.buttons.items():
            if hasattr(self.caller, 'signal_received'):
                if text == '▲M&enu':
                    button.clicked.connect(self.__show_submenu)
                else:
                    button.clicked.connect(self.caller.signal_received)

                if '&' not in text:
                    button.rightClicked.connect(self.__show_submenu)

            elif hasattr(self.caller, 'tab_signal_received'):
                if text == 'Shrink':
                    button.clicked.connect(self.caller.tab_signal_received)
                    button.setShortcut(QKeySequence('Ctrl+Tab'))
                    if self.shortened:
                        button.setText('Expand')
                elif text == '▲M&enu':
                    button.clicked.connect(self.__show_submenu)
                else:
                    button.clicked.connect(self.caller.tab_signal_received)

                if '&' not in text and 'Shrink' not in text:
                    button.rightClicked.connect(self.__show_submenu)

    def __init_submenu(self):
        if 'Add favourite' in self.buttons:
            manage_menu = FileManageMenu(self.caller, self.controller)
            self.menus['Add favourite'] = manage_menu
        if 'Search' in self.buttons:
            search_menu = SearchMenu(self.caller, self.controller)
            self.menus['Search'] = search_menu
        if '▲M&enu' in self.buttons:
            main_menu = MainMenu(self.caller, self.controller)
            self.menus['▲M&enu'] = main_menu

    def __check_management(self):
        if not FILE_MANAGEMENT:
            self.toggle_button('Add favourite', True)

    def __show_submenu(self):
        where_from = self.sender().objectName()
        menu = None

        if where_from == 'Add favourite':
            menu = self.menus.get(where_from)
        elif where_from == 'Search':
            menu = self.menus.get(where_from)
        elif where_from == '▲Menu':
            menu = self.menus.get('▲M&enu')

        if menu is not None and where_from == '▲Menu':
            menu.present_check(self.caller)

        if menu is not None:
            x = self.sender().mapToGlobal(self.sender().rect().topLeft()).x()
            y = self.sender().mapToGlobal(self.sender().rect().topLeft()).y() - menu.sizeHint().height()
            adjusted_pos = QPoint(x, y)
            menu.exec(adjusted_pos)

    def shrink_button_change(self, is_shrink: bool):
        button = self.buttons.get('Shrink')
        if button is not None:
            if is_shrink:
                self.shortened = True
                button.setText('Expand')
            else:
                self.shortened = False
                button.setText('Shrink')
            button.setShortcut(QKeySequence('Ctrl+Tab'))

    def button_change(self, name: str, text: str, is_visible: bool = True, is_disable: bool = False):
        button = self.buttons.get(name)
        if button is not None:
            button.setText(text)
            button.setDisabled(is_disable)
            if not is_visible:
                button.hide()

    def fixed_size_button(self, name: str, width: int, height: int):
        button = self.buttons.get(name)
        if button is not None:
            button.setFixedSize(width, height)

    def toggle_button(self, name: str, remove: bool = True):
        button = self.buttons.get(name)
        if button is not None:
            if remove:
                button.hide()
            else:
                button.show()

    def theme_menu_check(self):
        menu = self.menus.get('▲M&enu')
        if menu is not None:
            menu.theme_check()


def make_pixmap_section(page, scale: int):
    pixmap_section = QWidget()
    pixmap_section_layout = QVBoxLayout()
    pixmap_section_layout.setContentsMargins(0, 5, 0, 0)

    filepath = page.filepath
    index = page.image_index

    if os.path.exists(filepath):
        pixmap = portrait_generator(filepath, scale)
        label = PixmapLabel()
        label.setPixmap(pixmap)
    else:
        label = QLabel("Couldn't load image")

    label.setObjectName(f'pixmap_{index}')
    label.setFixedSize(scale, scale)
    label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    label.clicked.connect(page.page_signal_received)
    label.rightClicked.connect(lambda: page.page_signal_received(right=True))

    pixmap_section_layout.addWidget(label, alignment=Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
    pixmap_section_layout.setContentsMargins(0, 0, 0, 0)
    pixmap_section.setLayout(pixmap_section_layout)

    return pixmap_section


def make_label_section(page, scale: int):
    status = [['File count', 'Number'],
              'Extensions',
              'Filepath',
              'Timestamp',
              ['Image size', 'Size'],
              ['Size', 'Initial Size'],
              'Init image hash',
              'Seed',
              'Sampler',
              'Eta',
              'Steps',
              'CFG scale',
              ['Dynamic thresholding enabled', 'CFG scale fix'],
              'Model',
              'VAE',
              ['Variation seed', 'Var. seed'],
              ['Variation seed strength', 'Var. strength'],
              ['Seed resize from', 'Resize from'],
              ['Denoising strength', 'Denoising'],
              'Mask blur',
              'Clip skip',
              ['Lora', 'Lora in prompt'],
              'Textual inversion',
              ['AddNet Number', 'Add network'],
              ['Hires upscaler', 'Hires.fix'],
              'Extras',
              'Tiled diffusion',
              ['Region control number', 'Region control'],
              'ControlNet',
              'ENSD',
              'Version'
              ]

    if page.params.get('Hires upscaler'):
        status = [value for value in status if not isinstance(value, list) or value[0] != 'Denoising strength']

    label_layout = label_maker(status, page, 1, 1, True, True, 20, 95)
    label_layout.setContentsMargins(0, 0, 0, 0)

    for i in range(label_layout.count()):
        label_layout.itemAt(i).widget().setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

    scroll_area = QScrollArea()
    scroll_area.setMinimumWidth(350)
    scroll_area.setMaximumHeight(scale)
    scroll_area.setStyleSheet('border: 0px; padding 0px;')

    scroll_contents = QWidget()
    scroll_contents.setLayout(label_layout)
    scroll_area.setWidget(scroll_contents)

    label_area = QWidget()
    label_area_layout = QVBoxLayout()
    label_area_layout.setContentsMargins(0, 0, 0, 0)
    label_area_layout.addWidget(scroll_area, alignment=Qt.AlignmentFlag.AlignTop)
    label_area.setLayout(label_area_layout)

    return label_area


# Todo: Make Tokenize functionality
def make_prompt_tab(target):
    textbox_tab_layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Vertical)

    positive_text = target.params.get('Positive', 'None')
    positive_prompt = QTextEdit()
    positive_prompt.setPlainText(positive_text)
    positive_prompt.setReadOnly(True)
    positive_prompt.setObjectName('Positive')

    negative_text = target.params.get('Negative', 'None')
    negative_prompt = QTextEdit(negative_text)
    negative_prompt.setPlainText(negative_text)
    negative_prompt.setReadOnly(True)
    negative_prompt.setObjectName('Negative')

    splitter.addWidget(positive_prompt)
    splitter.addWidget(negative_prompt)
    textbox_tab_layout.addWidget(splitter)

    target.used_params['Positive'] = True
    target.used_params['Negative'] = True

    return textbox_tab_layout


def make_hires_other_tab(target):
    tab_layout = QHBoxLayout()
    hires_section = make_hires_section(target)
    tab_layout.addLayout(hires_section)
    extras_section = make_extras_section(target)
    tab_layout.addWidget(extras_section)
    return tab_layout


def make_hires_section(target):
    hires_section_layout = QVBoxLayout()

    status = [['Hires upscaler', 'Upscaler'],
              ['Hires upscale', 'Upscale'],
              ['Hires resize', 'Resize'],
              ['Hires steps', 'Steps'],
              ['Denoising strength', 'Denoising'],
              'Refiner',
              ['Refiner switch at', 'Switch at']
              ]
    hires_group = QGroupBox()
    hires_group.setTitle('Hires.fix')
    if not target.params.get('Hires upscaler'):
        hires_group.setDisabled(True)
    else:
        if not target.params.get(status[3][0]):
            status[3][0] = 'Steps'
    hires_group.setLayout(label_maker(status, target, 4, 6))

    status = ['Face restoration']
    face_section = QGroupBox()
    face_section.setTitle('Face restoration')
    item = target.params.get('Face restoration')
    if not item:
        face_section.setDisabled(True)
    face_section.setLayout(label_maker(status, target, 2, 1, False))

    hires_section_layout.addWidget(hires_group, 2)
    hires_section_layout.addWidget(face_section, 1)
    return hires_section_layout


def make_extras_section(target):
    status = [['Postprocess upscale by', 'Upscale by'],
              ['Postprocess upscale to', 'Upscale to'],
              ['Postprocess crop to', 'Crop to'],
              ['Postprocess upscaler', 'Upscaler 1'],
              ['Postprocess upscaler 2', 'Upscaler 2'],
              'GFPGAN visibility',
              'CodeFormer visibility',
              'CodeFormer weight',
              'Rembg']
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 2, 3))
    section.setTitle('Extras / Postprocess')
    if not target.params.get('Extras'):
        section.setDisabled(True)
    return section


def make_cfg_tab(target):
    tab_layout = QHBoxLayout()
    cfg_fix_section = dynamic_thresholding_section(target)
    tab_layout.addWidget(cfg_fix_section)
    cfg_auto_scheduler_layout = QVBoxLayout()
    cfg_auto_scheduler_layout.addWidget(cfg_auto(target))
    cfg_auto_scheduler_layout.addWidget(cfg_scheduler_section(target))
    tab_layout.addLayout(cfg_auto_scheduler_layout)
    return tab_layout


def cfg_auto(target):
    status = ['Scheduler',
              ['Main Strength', 'Main strength'],
              ['Sub- Strength', 'Sub strength'],
              ['Main Range', 'Main range'],
              ['Sub- Range', 'Sub range']
              ]
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 2, 3))
    section.setTitle('CFG auto')
    if not target.params.get('CFG auto'):
        section.setDisabled(True)
    else:
        target.used_params['CFG auto'] = True
    return section


def cfg_scheduler_section(target):
    status = [['loops', 'Loops'],
              ['target denoising', 'Target'],
              'CFG',
              'ETA',
              ]
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 1, 3, True))
    section.setTitle('CFG scheduler')
    if not target.params.get('CFG scheduler'):
        section.setDisabled(True)
    else:
        target.used_params['CFG scheduler'] = True
    return section


def dynamic_thresholding_section(target):
    status = ['CFG mode',
              'CFG scale minimum',
              'Mimic mode',
              'Mimic scale',
              'Mimic scale minimum',
              'Scheduler value',
              'Threshold percentile',
              ['Separate Feature Channels', 'Separate feature channels'],
              ['Scaling Startpoint', 'Scaling startpoint'],
              ['Variability Measure', 'Variability measure'],
              ['Interpolate Phi', 'Interpolate phi']
              ]
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 6, 4))
    section.setTitle('Dynamic thresholding (CFG scale fix)')
    if not target.params.get('Dynamic thresholding enabled'):
        section.setDisabled(True)
    return section


# Todo: unite Textual invention & Lora & Add net extension
def make_lora_addnet_tab(target):
    tab_layout = QHBoxLayout()
    lora_group = make_lora_section(target)
    tab_layout.addWidget(lora_group)
    addnet_group = make_addnet_section(target)
    tab_layout.addWidget(addnet_group)
    return tab_layout


def make_lora_section(target):
    lora_section = QGroupBox()
    scroll_area = QScrollArea()
    content_widget = QWidget()
    content_layout = QVBoxLayout()
    section_layout = QVBoxLayout()
    scroll_area.setStyleSheet('border: 0px;')
    scroll_area.setContentsMargins(0, 0, 0, 0)
    content_widget.setContentsMargins(0, 0, 0, 0)
    lora_num = target.params.get('Lora')
    ti_num = target.params.get('Textual inversion')
    if not lora_num:
        caption = 'LoRa : 0'
    else:
        caption = 'LoRa : ' + lora_num
        loop_num = max(int(lora_num), 14) + 1
        keyring = []
        for i in range(loop_num):
            key = 'Lora ' + str(i)
            title = 'Lora ' + str(i + 1)
            if target.params.get(key):
                keyring.append([key, title])
        section_layout.addLayout(label_maker(keyring, target, 1, 3))
    if not ti_num:
        caption += ', Textual Inversion : 0'
    else:
        caption += ', Textual Inversion : ' + ti_num
        loop_num = max(int(ti_num), 14) + 1
        keyring = []
        for i in range(loop_num):
            key = 'Ti ' + str(i)
            title = 'Ti ' + str(i + 1)
            if target.params.get(key):
                keyring.append([key, title])
        section_layout.addLayout(label_maker(keyring, target, 1, 3))
    content_widget.setLayout(section_layout)
    scroll_area.setWidget(content_widget)
    content_layout.addWidget(scroll_area)
    lora_section.setLayout(content_layout)
    lora_section.setTitle(caption)
    return lora_section


def make_addnet_section(target):
    status = [['Module', 'Module'],
              ['Weight A', 'UNet / TEnc'],
              ['Model', 'Model']
              ]
    addnet = target.params.get('AddNet Enabled')
    addnet_section = QGroupBox()
    scroll_area = QScrollArea()
    content_widget = QWidget()
    content_layout = QVBoxLayout()
    section_layout = QVBoxLayout()
    scroll_area.setStyleSheet('border: 0px;')
    scroll_area.setContentsMargins(0, 0, 0, 0)
    content_widget.setContentsMargins(0, 0, 0, 0)
    if not addnet:
        addnet_section.setDisabled(True)
        cnt = 0
    else:
        cnt = 5
        for i in range(1, 6):
            key = [['AddNet ' + value[0] + ' ' + str(i), value[1]] for value in status]
            if not target.params.get(key[0][0]):
                cnt = cnt - 1
                continue
            section_layout.addLayout(label_maker(key, target, 1, 2, True, False, 99, 80))
    caption = 'Additional Networks : ' + str(cnt)
    content_widget.setLayout(section_layout)
    scroll_area.setWidget(content_widget)
    content_layout.addWidget(scroll_area)
    addnet_section.setLayout(content_layout)
    addnet_section.setTitle(caption)
    target.used_params['AddNet Enabled'] = True
    return addnet_section


def make_tiled_diffusion_tab(target):
    tab_layout = QHBoxLayout()
    tiled_diffusion_section = QVBoxLayout()
    tiled_diffusion_basic_info = make_tiled_diffusion_section(target)
    noise_inversion_info = make_noise_inversion_section(target)
    region_control_info = region_control_section(target)

    tiled_diffusion_section.addWidget(tiled_diffusion_basic_info)
    tiled_diffusion_section.addWidget(noise_inversion_info)

    tab_layout.addLayout(tiled_diffusion_section, 1)
    tab_layout.addWidget(region_control_info, 1)
    return tab_layout


def make_tiled_diffusion_section(target):
    status = ['Method',
              'Keep input size',
              'Tile batch size',
              'Tile width',
              'Tile height',
              'Tile Overlap',
              'Upscaler',
              'Upscale factor'
              ]
    section = QGroupBox()
    section.setTitle('Tiled diffusion')
    section.setLayout(label_maker(status, target, 2, 3))
    return section


def make_noise_inversion_section(target):
    status = ['Noise inversion Kernel size',
              'Noise inversion Renoise strength',
              'Noise inversion Retouch',
              'Noise inversion Steps'
              ]
    section = QGroupBox()
    section.setTitle('Noise inversion')
    target.used_params['Noise inversion'] = True
    if not target.params.get('Noise inversion'):
        section.setDisabled(True)
    status = [[value, value.replace('Noise inversion ', '')] for value in status]
    section.setLayout(label_maker(status, target, 2, 3))
    return section


def region_control_section(target):
    status = [['blend mode', 'Blend mode'],
              ['feather ratio', 'Feather ratio'],
              ['w', 'Width'],
              ['x', 'X'],
              ['seed', 'Seed'],
              ]
    region_control_tab = QTabWidget()
    target.used_params['Region control'] = True
    for i in range(1, 9):
        region_number = 'Region ' + str(i)
        check = target.params.get(region_number + ' enable')
        target.used_params[region_number + ' enable'] = True
        if check or i == 1:
            page = QWidget()
            region_control_section_layout = QVBoxLayout()
            keys = [[region_number + ' ' + value[0], value[1]] for value in status]
            region_control_section_layout.addLayout(label_maker(keys, target, 1, 1, True))
            str_prompt = target.params.get(region_number + ' prompt')
            prompt = QTextEdit(str_prompt)
            prompt.setReadOnly(True)
            region_control_section_layout.addWidget(prompt)
            target.used_params[region_number + ' prompt'] = True
            str_negative_prompt = target.params.get(region_number + ' neg prompt')
            negative_prompt = QTextEdit(str_negative_prompt)
            negative_prompt.setReadOnly(True)
            region_control_section_layout.addWidget(negative_prompt)
            target.used_params[region_number + ' neg prompt'] = True
            page.setLayout(region_control_section_layout)
            region_control_tab.addTab(page, region_number)
            if not check:
                region_control_tab.setDisabled(True)
    return region_control_tab


def make_control_net_tab(target, starts: int):
    control_tab = QScrollArea()
    controlnet_widget = QWidget()
    page_layout = QHBoxLayout()
    status = [['Model', 'Model'],
              ['Control Mode', 'Control mode'],
              ['Module', 'Module'],
              ['Pixel Perfect', 'Pixel perfect'],
              ['Resize Mode', 'Resize mode'],
              ['Guidance Start', 'Guidance start'],
              ['Guidance End', 'Guidance end'],
              ['Weight', 'Weight'],
              ['Threshold A', 'Threshold A'],
              ['Low Vram', 'Low vram'],
              ['Preprocessor params', 'Preproc. params']
              ]
    control_tab.setWidgetResizable(True)
    control_tab.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    control_tab.setStyleSheet('QScrollArea {background-color: transparent; border: 0px}')

    unit_num = int(target.params.get('ControlNet'))
    loop_num = 2 if 2 > unit_num else unit_num
    for i in range(starts, loop_num):
        control_net_enable = target.params.get('ControlNet ' + str(i))
        if target.params.get('ControlNet ' + str(i) + ' starting/ending'):
            status = [value for value in status if 'Guidance' not in value[0]]
            status.insert(5, ['starting/ending', 'Starting / Ending'])
            status_key = [['ControlNet ' + str(i) + ' ' + value[0].lower(), value[1]] for value in status]
        else:
            status_key = [['ControlNet ' + str(i) + ' ' + value[0], value[1]] for value in status]
        section = QGroupBox()
        section.setTitle('ControlNet Unit ' + str(i))
        if not control_net_enable:
            section.setDisabled(True)
        else:
            target.used_params['ControlNet ' + str(i)] = True
        section.setLayout(label_maker(status_key, target, 4, 6))
        page_layout.addWidget(section)
    controlnet_widget.setLayout(page_layout)
    controlnet_widget.setStyleSheet('background-color:transparent')
    control_tab.setWidget(controlnet_widget)
    return control_tab


def make_regional_prompter_tab(target):
    filepath = target.params.get('Filepath')
    scale = config.get('RegionalPrompterPixmapSize', 350)
    pixmap = None

    if os.path.exists(filepath):
        pixmap = QPixmap(filepath)
        pixmap = pixmap.scaled(scale, int(scale * 0.7), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

    regional_prompter_group = QHBoxLayout()
    regional_prompter_group.addWidget(make_regional_prompter_status_section(target), 1)

    ratio_pixmap_label = QLabel()
    str_ratios = target.params.get('RP Ratios')
    ratio_mode = target.params.get('RP Matrix submode')
    if not ratio_mode:
        ratio_mode = '---'
    main, sub = regional_prompter_ratio_check(str_ratios, ratio_mode)
    if main and sub and os.path.exists(filepath):
        pixmap = make_regional_prompter_pixmap(pixmap, ratio_mode, main, sub)
        ratio_pixmap_label.setPixmap(pixmap)
    else:
        ratio_pixmap_label.setText("Couldn't analyze ratio strings")
    ratio_pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

    ratio_strings = '(' + str_ratios.replace(' ', '') + ')'

    ratio_strings_section = QGroupBox()
    ratio_strings_section_layout = QVBoxLayout()
    ratio_strings_section.setTitle('Regional Prompter Ratios: ' + ratio_mode + ' ' + ratio_strings)

    ratio_strings_section_layout.addWidget(ratio_pixmap_label)
    ratio_strings_section.setLayout(ratio_strings_section_layout)
    regional_prompter_group.addWidget(ratio_strings_section, 2)

    scroll_area = QScrollArea()
    content_widget = QWidget()
    content_widget.setLayout(regional_prompter_group)
    scroll_area.setWidget(content_widget)

    scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
    scroll_area.setStyleSheet("QScrollArea { border: 0px; }")
    scroll_area.setContentsMargins(0, 0, 0, 0)
    content_widget.setContentsMargins(0, 0, 0, 0)

    return scroll_area


def make_regional_prompter_status_section(target):
    status = [['RP Calc Mode', 'Generation Mode'],
              ['RP Base Ratios', 'Base prompt ratio'],
              ['RP Use Base', 'Use base prompt'],
              ['RP Use Common', 'Use common prompt'],
              ['RP Use Ncommon', 'Use negative prompt'],
              ['RP Divide mode', 'Divide mode'],
              ['RP Mask submode', 'Mask submode'],
              ['RP Prompt submode', 'Prompt submode'],
              ['RP Change AND', '"AND" to "BREAK"'],
              ['RP LoRA Neg U Ratios', 'Lora negative UNet ratio'],
              ['RP LoRA Neg Te Ratios', 'Lora negative TEnc ratio'],
              ['RP LoRA Stop Step', 'Lora Stop Step'],
              ['RP LoRA Hires Stop Step', 'Hires Stop Step'],
              ['RP threshold', 'Threshold']]
    status_section = QGroupBox()
    status_section.setLayout(label_maker(status, target, 2, 1))
    status_section.setTitle('Status')
    target.used_params['RP Active'] = True
    target.used_params['RP Matrix submode'] = True
    target.used_params['RP Ratios'] = True
    return status_section


def make_regional_prompter_pixmap(pixmap: QPixmap, divide_mode: str, main_ratio: str, sub_ratio: str):
    divide_sum = sum(main_ratio)

    paint_area = QPainter()
    paint_area.begin(pixmap)
    paint_area.drawPixmap(0, 0, pixmap)
    paint_area.setPen(QColor(255, 255, 255))
    paint_area.setBrush(QColor(255, 255, 255))
    painted_pos_y = 0
    painted_pos_x = 0

    if divide_mode == 'Horizontal':
        for index, ratio in enumerate(main_ratio):
            height_by_ratio = int((pixmap.height() / divide_sum) * ratio)
            start_draw_pos_y = painted_pos_y + height_by_ratio
            paint_area.drawRect(0, start_draw_pos_y, pixmap.width(), 2)
            if sub_ratio[index] and len(sub_ratio[index]) > 1:
                sub_divide_sum = sum(sub_ratio[index])
                painted_pos_x = 0
                for tmp in sub_ratio[index]:
                    width_by_sub_ratio = int((pixmap.width() / sub_divide_sum) * tmp)
                    start_draw_pos_x = painted_pos_x + width_by_sub_ratio
                    paint_area.drawRect(start_draw_pos_x, painted_pos_y, 2, height_by_ratio)
                    painted_pos_x = start_draw_pos_x
            painted_pos_y = start_draw_pos_y
    elif divide_mode == 'Vertical':
        for index, ratio in enumerate(main_ratio):
            width_by_ratio = int((pixmap.width() / divide_sum) * ratio)
            start_draw_pos_x = painted_pos_x + width_by_ratio
            paint_area.drawRect(start_draw_pos_x, 0, 2, pixmap.height())
            if sub_ratio[index] and len(sub_ratio[index]) > 1:
                sub_divide_sum = sum(sub_ratio[index])
                painted_pos_y = 0
                for tmp in sub_ratio[index]:
                    height_by_sub_ratio = int((pixmap.height() / sub_divide_sum) * tmp)
                    start_draw_pos_y = painted_pos_y + height_by_sub_ratio
                    paint_area.drawRect(painted_pos_x, start_draw_pos_y, width_by_ratio, 2)
                    painted_pos_y = start_draw_pos_y
            painted_pos_x = start_draw_pos_x

    paint_area.end()

    return pixmap


def regional_prompter_ratio_check(str_ratio: str, divide_mode: str):
    result = True
    main_ratio = []
    sub_ratio = []
    major_splitter = ';'
    minor_splitter = ','
    if divide_mode == 'Vertical':
        major_splitter = minor_splitter
        minor_splitter = ';'

    for tmp in str_ratio.split(major_splitter):
        ratio = tmp.split(minor_splitter)
        try:
            if ';' in str_ratio:
                main_ratio.append(int(ratio[0]))
                sub_ratio.append([int(number) for number in ratio[1:]])
            elif divide_mode == 'Horizontal':
                main_ratio.append(1)
                sub_ratio.append([int(number) for number in ratio])
            else:
                pass
        except ValueError:
            result = False
            break

    if not result:
        return None, None
    else:
        return main_ratio, sub_ratio


def make_error_tab(target, image, parameter: int):
    error_list = image.error_list
    difference = set(target.params.keys() - target.used_params.keys())
    if error_list or difference or parameter == 2:
        diff_text = 'Diff: ' + ','.join(difference)
        error_text = 'Error: ' + ','.join(error_list)
        inner_page = QWidget()
        inner_page_layout = QVBoxLayout()
        original_data = image.original_data
        error = QTextEdit()
        error.setPlainText(diff_text + '\n\n' + error_text)
        original = QTextEdit()
        original.setPlainText(original_data)
        description_text = 'If an error occurs, please share the developer data displayed here.'
        description = QLabel(description_text)
        inner_page_layout.addWidget(original)
        inner_page_layout.addWidget(error)
        inner_page_layout.addWidget(description)
        inner_page.setLayout(inner_page_layout)
        return inner_page
    return None


def label_maker(status: list,
                target,
                stretch_title: int,
                stretch_value: int,
                selectable: bool = False,
                remove_if_none: bool = False,
                minimums: int = 99,
                restriction: int = 0):
    label_count = 0
    section_layout = QGridLayout()
    for tmp in status:
        if isinstance(tmp, list):
            item = target.params.get(tmp[0])
            key, name = tmp
        else:
            item = target.params.get(tmp)
            key = name = tmp
        if item:
            if 'Filepath' in key:
                item = os.path.dirname(item)
            elif 'ControlNet' in key and 'model' in key:
                item = item.replace(' ', '\n')
            elif 'Hires.fix' in name:
                item = 'True'
            elif 'AddNet' in key and 'Model' in key:
                item = item.replace('(', ' [').replace(')', ']')
            elif 'AddNet' in key and 'Weight A' in key:
                weight_b_key = key.replace(' A ', ' B ')
                weight_b = target.params.get(weight_b_key)
                item = item + ' / ' + weight_b
                target.used_params[weight_b_key] = True
        else:
            if name == 'Keep input size':
                item = 'False'
            elif 'ControlNet' in key and 'module' in key and not item:
                tmp_key = key.replace('module', 'preprocessor')
                item = target.params.get(tmp_key)
                if item:
                    target.used_params[tmp_key] = True
                else:
                    item = 'None'
            elif name and not remove_if_none:
                item = 'None'

        if 'w' in key and 'Region' in key:
            name = 'Width x Height'
            height_key = key.replace('w', 'h')
            height_item = target.params.get(height_key)
            if height_item:
                item = item + ' x ' + height_item
                target.used_params[height_key] = True
            else:
                item = 'None'
        elif 'x' in key and 'Region' in key:
            name = '(X, Y)'
            y_key = key.replace('x', 'y')
            y_item = target.params.get(y_key)
            if y_item:
                item = '(' + item + ', ' + y_item + ')'
                target.used_params[y_key] = True
            else:
                item = 'None'

        if not item and remove_if_none:
            continue

        title = QLabel(name)
        value = QLabel(item)
        if restriction > 0:
            title.setMinimumWidth(restriction)
            title.setMaximumWidth(restriction)
        if selectable:
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        if name:
            title.setObjectName(name + '_title')
            value.setObjectName(name + '_value')
        if name == 'Filepath' or name == 'Filename':
            value.setToolTip(item)
            value.setMaximumWidth(300)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(stretch_title)
        size_policy_value.setHorizontalStretch(stretch_value)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        section_layout.addWidget(title, label_count, 0)
        section_layout.addWidget(value, label_count, 1)
        label_count = label_count + 1
        if not item == 'None':
            target.used_params[key] = True
        elif key == 'CFG' or key == 'ETA':
            target.used_params[key] = True
    if 20 > minimums > label_count:
        for i in range(minimums - label_count):
            margin = QLabel()
            section_layout.addWidget(margin, label_count, 0)
            label_count = label_count + 1
    return section_layout


@lru_cache(maxsize=1000)
def portrait_generator(filepath, size):
    if not os.path.exists(filepath):
        return QPixmap(size, size)
    image_reader = QImageReader(filepath)
    pixmap = QPixmap.fromImageReader(image_reader)
    pixmap = pixmap.scaled(size, size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    return pixmap


def move_centre(target=None):
    if not target.parent() or not target.parent().isVisible():
        screen_center = QApplication.primaryScreen().geometry().center()
    else:
        screen_center = target.parent().geometry().center()

    frame_geometry = target.frameGeometry()
    frame_geometry.moveCenter(screen_center)
    target.move(frame_geometry.topLeft())


def module_checker(module_name: str):
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False
