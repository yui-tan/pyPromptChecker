import os
import json
import sys
import csv
import pyPromptChecker.lib.decoder
import pyPromptChecker.lib.parser
from PyQt6.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout
from PyQt6.QtWidgets import QTabWidget, QTextEdit, QPushButton, QFileDialog
from PyQt6.QtWidgets import QSplitter, QMainWindow, QGroupBox, QScrollArea
from PyQt6.QtGui import QPixmap, QPainter, QColor
from PyQt6.QtCore import Qt


class ResultWindow(QMainWindow):
    def __init__(self, targets=None):
        super().__init__()
        self.setWindowTitle('PNG Prompt Data')
        self.models = model_hashes()
        self.params = []
        self.positive_for_copy = ''
        self.negative_for_copy = ''
        self.seed_for_copy = ''
        self.tab_index = 0
        self.init_ui(targets)

        size_hint_width = self.sizeHint().width()
        size_hint_height = self.sizeHint().height()

        window_width = size_hint_width if 1024 > size_hint_width else 640
        window_height = size_hint_height if 900 > size_hint_height else 900
        self.resize(window_width, window_height)
        self.center()
        print(size_hint_height)

    def init_ui(self, targets):
        for filepath in targets:
            chunk_data = pyPromptChecker.lib.decoder.decode_text_chunk(filepath, 1)
            parameters = pyPromptChecker.lib.parser.parse_parameter(chunk_data, filepath, self.models)
            self.params.append(parameters)
        self.positive_for_copy = self.params[0].params.get('Positive')
        self.negative_for_copy = self.params[0].params.get('Negative')
        self.seed_for_copy = self.params[0].params.get('Seed')

        root_layout = QVBoxLayout()
        root_tab = QTabWidget()

        for tmp in self.params:
            tab_page = QWidget()
            tab_page_layout = QVBoxLayout()
            inner_tab = QTabWidget()

            main_section = QGroupBox()
            main_section_layout = QHBoxLayout()

            main_section_layout.addLayout(make_main_section(tmp))
            main_section.setLayout(main_section_layout)
            tab_page_layout.addWidget(main_section)

            for i in range(6):
                inner_page = QWidget()
                if i == 0:
                    inner_page.setLayout(make_prompt_tab(tmp))
                    inner_tab.addTab(inner_page, 'Prompts')
                if i == 1 and (tmp.params.get('Hires upscaler') or tmp.params.get('Face restoration') or tmp.params.get('Dynamic thresholding enabled')):
                    inner_page.setLayout(make_hires_other_tab(tmp))
                    inner_tab.addTab(inner_page, 'Hires.fix / Other')
                if i == 2 and (tmp.params.get('Lora')):
                    inner_page.setLayout(make_lora_addnet_tab(tmp))
                    inner_tab.addTab(inner_page, 'Lora')
                if i == 3 and tmp.params.get('Tiled diffusion'):
                    inner_page.setLayout(make_tiled_diffusion_tab(tmp))
                    inner_tab.addTab(inner_page, 'Tiled diffusion')
                if i == 4 and tmp.params.get('ControlNet'):
                    inner_page = (make_control_net_tab(tmp, 0))
                    inner_tab.addTab(inner_page, 'ControlNet')
                if i == 5 and tmp.params.get('RP Active'):
                    inner_page.setLayout(make_regional_prompter_tab(tmp))
                    inner_tab.addTab(inner_page, 'Regional Prompter')
                if i == 6 and tmp.params.get('Dynamic thresholding enabled'):
                    inner_page.setLayout(make_other_tab(tmp))
                    inner_tab.addTab(inner_page, 'Other')

            inner_tab.setTabPosition(QTabWidget.TabPosition.South)
            tab_page_layout.addWidget(inner_tab)
            tab_page.setLayout(tab_page_layout)

            root_tab.addTab(tab_page, tmp.params.get('Filename'))
            root_tab.currentChanged.connect(self.tab_changed)

        root_layout.addWidget(root_tab)

        button_layout = QHBoxLayout()
        button_text = ['Copy positive',
                       'Copy negative',
                       'Copy seed',
                       'Export JSON (This image)',
                       'Export JSON (All images)',
                       'Reselect']
        for tmp in button_text:
            copy_button = QPushButton(tmp)
            button_layout.addWidget(copy_button)
            copy_button.clicked.connect(self.button_clicked)

        root_layout.addLayout(button_layout)

        central_widget = QWidget()
        central_widget.setLayout(root_layout)

        if self.centralWidget():
            self.centralWidget().deleteLater()
        self.setCentralWidget(central_widget)

    def center(self):
        frame_geometry = self.frameGeometry()
        screen_center = QApplication.primaryScreen().geometry().center()
        frame_geometry.moveCenter(screen_center)
        self.move(frame_geometry.topLeft())

    def tab_changed(self, index):
        self.positive_for_copy = self.params[index].params.get('Positive')
        self.negative_for_copy = self.params[index].params.get('Negative')
        self.seed_for_copy = self.params[0].params.get('Seed')
        self.tab_index = index

    def button_clicked(self):
        where_from = self.sender().text()
        clipboard = QApplication.clipboard()
        if where_from == 'Copy positive':
            if self.positive_for_copy:
                clipboard.setText(self.positive_for_copy)
        elif where_from == 'Copy negative':
            if self.negative_for_copy:
                clipboard.setText(self.negative_for_copy)
        elif where_from == 'Copy seed':
            if self.seed_for_copy:
                clipboard.setText(self.seed_for_copy)
        elif where_from == 'Export JSON (This image)':
            data = self.params[self.tab_index]
            filepath = savefile_choose_dialog()
            data.json_export(filepath)
        elif where_from == 'Export JSON (All images)':
            filepath = savefile_choose_dialog(True)
            if filepath:
                dict_list = []
                for tmp in self.params:
                    dict_list.append(tmp.params)
                with open(filepath, 'w') as f:
                    json.dump(dict_list, f, sort_keys=True, indent=4, ensure_ascii=False)
        elif where_from == 'Reselect':
            filepath = file_choose_dialog()[0]
            if filepath:
                self.params = []
                self.init_ui(filepath)


def result_window(target_data):
    app = QApplication(sys.argv)
    window = ResultWindow(target_data)
    window.show()
    sys.exit(app.exec())


def model_hashes():
    directory = os.path.dirname(__file__)
    filename = os.path.join(directory, '../../model_list.csv')
    if os.path.exists(filename):
        with open(filename, encoding='utf8', newline='') as f:
            csvreader = csv.reader(f)
            model_list = [row for row in csvreader]
        return model_list
    else:
        return None


def make_main_section(target):
    status = ['Filename',
              'Filepath',
              'Size',
              'Seed',
              'Sampler',
              'Eta',
              'Steps',
              'CFG scale',
              ['Dynamic thresholding enabled', 'CFG scale fix'],
              'Model',
              ['Variation seed', 'Var. seed'],
              ['Variation seed strength', 'Var. strength'],
              'Denoising strength',
              'Clip skip',
              ['Lora', 'Lora in prompt'],
              ['Hires upscaler', 'Hires.fix'],
              'ControlNet',
              'ENSD',
              'Version']
    filepath = target.params.get('Filepath')
    if target.params.get('Hires upscaler'):
        status.remove('Denoising strength')
    main_section_layout = QHBoxLayout()
    pixmap_label = make_pixmap_label(filepath)
    main_section_layout.addWidget(pixmap_label, 1)
    main_section_layout.addLayout(label_maker(status, target, 1, 1, True, True, 15), 1)

    return main_section_layout


def make_pixmap_label(filepath, scale=350):
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(scale, scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)
    pixmap_label = QLabel()
    pixmap_label.setPixmap(pixmap)
    pixmap_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
    return pixmap_label


def make_prompt_tab(target):
    textbox_tab_layout = QVBoxLayout()
    splitter = QSplitter(Qt.Orientation.Vertical)
    positive_text = target.params.get('Positive')
    positive_prompt = QTextEdit()
    positive_prompt.setPlainText(positive_text)
    positive_prompt.setReadOnly(True)
    negative_text = target.params.get('Negative')
    negative_prompt = QTextEdit(negative_text)
    negative_prompt.setPlainText(negative_text)
    negative_prompt.setReadOnly(True)

    splitter.addWidget(positive_prompt)
    splitter.addWidget(negative_prompt)
    textbox_tab_layout.addWidget(splitter)

    return textbox_tab_layout


def make_hires_other_tab(target):
    tab_layout = QHBoxLayout()
    hires_section = make_hires_section(target)
    tab_layout.addLayout(hires_section)
    cfg_fix_section = dynamic_thresholding_section(target)
    tab_layout.addWidget(cfg_fix_section)
    return tab_layout


def make_hires_section(target):
    hires_section_layout = QVBoxLayout()

    status = [['Hires upscaler', 'Upscaler'],
              ['Hires upscale', 'Upscale'],
              ['Hires resize', 'Resize'],
              ['Hires steps', 'Steps'],
              ['Denoising strength', 'Denoising']
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


def dynamic_thresholding_section(target):
    status = ['CFG mode',
              'CFG scale minimum',
              'Mimic mode',
              'Mimic scale',
              'Mimic scale minimum',
              'Scheduler value',
              'Threshold percentile'
              ]
    section = QGroupBox()
    section.setLayout(label_maker(status, target, 6, 4))
    section.setTitle('Dynamic thresholding (CFG scale fix)')
    if not target.params.get('Dynamic thresholding enabled'):
        section.setDisabled(True)
    return section


def make_lora_addnet_tab(target):
    tab_layout = QHBoxLayout()
    lora_group = make_lora_section(target)
    tab_layout.addWidget(lora_group, 3)
    addnet_group = make_addnet_section(target)
    tab_layout.addWidget(addnet_group, 4)
    return tab_layout


def make_lora_section(target):
    lora_section = QGroupBox()
    section_layout = QVBoxLayout()
    lora_num = target.params.get('Lora')
    if not lora_num:
        caption = 'Lora in prompt : 0'
    else:
        caption = 'Lora in prompt : ' + lora_num
        loop_num = max(int(lora_num), 14) + 1
        keyring = []
        for i in range(loop_num):
            key = 'Lora ' + str(i)
            title = 'Lora ' + str(i + 1)
            if target.params.get(key):
                keyring.append([key, title])
            else:
                keyring.append([None, None])
        section_layout.addLayout(label_maker(keyring, target, 1, 3))
    lora_section.setLayout(section_layout)
    lora_section.setTitle(caption)
    return lora_section


def make_addnet_section(target):
    status = [['Module', 'Module'],
              ['Weight A', 'UNet / TEnc'],
              ['Model', 'Model']
              ]
    addnet_section = QGroupBox()
    addnet = target.params.get('AddNet Enabled')
    section_layout = QVBoxLayout()
    if not addnet:
        addnet_section.setDisabled(True)
        cnt = 0
    else:
        cnt = 5
        for i in range(1, 6):
            key = [['AddNet ' + value[0] + ' ' + str(i), value[1]] for value in status]
            if not target.params.get(key[0][0]):
                key = [None, None, None]
                cnt = cnt - 1
            section_layout.addLayout(label_maker(key, target, 1, 3))
    addnet_section.setLayout(section_layout)
    addnet_section.setTitle('Additional Networks : ' + str(cnt))
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
    if not target.params.get('Noise inversion'):
        section.setDisabled(True)
    status = [[value, value.replace('Noise inversion ', '')] for value in status]
    section.setLayout(label_maker(status, target, 2, 3))
    return section


def region_control_section(target):
    status = [['blend mode', 'Blend mode'],
              ['feather ratio', 'Feather ratio'],
              ['w', 'Width'],
              ['h', 'Height'],
              ['x', 'X'],
              ['y', 'Y'],
              ['seed', 'Seed'],
              ]
    region_control_tab = QTabWidget()
    for i in range(1, 9):
        region_number = 'Region ' + str(i)
        check = target.params.get(region_number + ' enable')
        if check or i == 1:
            page = QWidget()
            region_control_section_layout = QVBoxLayout()
            keys = [[region_number + ' ' + value[0], value[1]] for value in status]
            region_control_section_layout.addLayout(label_maker(keys, target, 1, 1, True))
            str_prompt = target.params.get(region_number + ' prompt')
            prompt = QTextEdit(str_prompt)
            prompt.setReadOnly(True)
            region_control_section_layout.addWidget(prompt)
            str_negative_prompt = target.params.get(region_number + ' neg prompt')
            negative_prompt = QTextEdit(str_negative_prompt)
            negative_prompt.setReadOnly(True)
            region_control_section_layout.addWidget(negative_prompt)
            page.setLayout(region_control_section_layout)
            region_control_tab.addTab(page, region_number)
            if not check:
                region_control_tab.setDisabled(True)
    return region_control_tab


def make_control_net_tab(target, starts):
    control_tab = QScrollArea()
    controlnet_widget = QWidget()
    page_layout = QHBoxLayout()
    status = [['model', 'Model'],
              ['control mode', 'Control mode'],
              ['pixel perfect', 'Pixel perfect'],
              ['preprocessor', 'Preprocessor'],
              ['resize mode', 'Resize mode'],
              ['starting/ending', 'Starting/ending'],
              ['weight', 'Weight'],
              ['preprocessor params', 'Preproc. params'],
              ]
    control_tab.setWidgetResizable(True)
    control_tab.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    control_tab.setStyleSheet('QScrollArea {background-color:transparent;}')

    unit_num = int(target.params.get('ControlNet'))
    loop_num = 2 if 2 > unit_num else unit_num
    for i in range(starts, loop_num):
        control_net_enable = target.params.get('ControlNet ' + str(i))
        status = [['ControlNet ' + str(i) + ' ' + value[0], value[1]] for value in status]
        section = QGroupBox()
        section.setTitle('ControlNet Unit ' + str(i))
        if not control_net_enable:
            section.setDisabled(True)
        section.setLayout(label_maker(status, target, 4, 6))
        page_layout.addWidget(section)
    controlnet_widget.setLayout(page_layout)
    controlnet_widget.setStyleSheet('background-color:transparent')
    control_tab.setWidget(controlnet_widget)
    return control_tab


def make_regional_prompter_tab(target, scale=500):
    filepath = target.params.get('Filepath')
    pixmap = QPixmap(filepath)
    pixmap = pixmap.scaled(scale, scale, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.FastTransformation)

    regional_prompter_group = QHBoxLayout()
    regional_prompter_group.addWidget(make_regional_prompter_status_section(target), 1)

    ratio_pixmap_label = QLabel()
    str_ratios = target.params.get('RP Ratios')
    ratio_mode = target.params.get('RP Matrix submode')
    main, sub = regional_prompter_ratio_check(str_ratios, ratio_mode)
    if main and sub:
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

    return regional_prompter_group


def make_regional_prompter_status_section(target):
    status = [['RP Calc Mode', 'Generation Mode'],
              ['RP Base Ratios', 'Base prompt ratio'],
              ['RP Use Base', 'Use base prompt'],
              ['RP Use Common', 'Use common prompt'],
              ['RP Use Ncommon', 'Use negative prompt'],
              ['RP Divide mode', 'Divide mode'],
              ['RP Mask submode', 'Mask submode'],
              ['RP Prompt submode', 'Prompt submode'],
              ['RP Change AND', 'Change "AND" to "BREAK"'],
              ['RP LoRA Neg U Ratios', 'Lora negative UNet Ratio'],
              ['RP LoRA Neg Te Ratios', 'Lora negative TEnc Ratio'],
              ['RP threshold', 'Threshold']]
    status_section = QGroupBox()
    status_section.setLayout(label_maker(status, target, 2, 1))
    status_section.setTitle('Status')
    return status_section


def make_regional_prompter_pixmap(pixmap, divide_mode, main_ratio, sub_ratio):
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


def regional_prompter_ratio_check(str_ratio, divide_mode):
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
            main_ratio.append(int(ratio[0]))
            sub_ratio.append([int(number) for number in ratio[1:]])
        except ValueError:
            result = False
            break

    if not result:
        return None, None
    else:
        return main_ratio, sub_ratio


def make_other_tab(target):
    page_layout = QHBoxLayout()
    page_layout.addWidget(dynamic_thresholding_section(target))
    for i in range(2):
        page_layout.addWidget(make_dummy_section(7))
    return page_layout


def label_maker(status, target, stretch_title, stretch_value, selectable=False, remove_if_none=False, minimums=99):
    label_count = 0
    section_layout = QGridLayout()
    for tmp in status:
        maximum_size = 15
        if isinstance(tmp, list):
            item = target.params.get(tmp[0])
            if item:
                if 'ControlNet' in tmp[0] and 'model' in tmp[0]:
                    item = item.replace(' ', '\n')
                elif 'AddNet' in tmp[0] and 'Model' in tmp[0]:
                    item = item.replace('(', ' [').replace(')', ']')
                elif 'AddNet' in tmp[0] and 'Weight A' in tmp[0]:
                    weight_b = target.params.get(tmp[0].replace(' A ', ' B '))
                    item = item + ' / ' + weight_b
                elif 'Lora ' in tmp[0]:
                    item = item.replace(' [', ' [')
                elif tmp[1] == 'Hires.fix':
                    item = 'True'
            tmp = tmp[1]
        else:
            item = target.params.get(tmp)
        if tmp == 'Filepath':
            item = os.path.dirname(item)
        if not item and remove_if_none:
            continue
        elif tmp and not item:
            item = 'None'
            if tmp == 'Keep input size':
                item = 'False'
        title = QLabel(tmp)
        value = QLabel(item)
        title.setMaximumSize(1000, maximum_size)
        if value.sizeHint().height() > 30:
            maximum_size = maximum_size * 2
        value.setMaximumSize(1000, maximum_size)
        if selectable:
            value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(stretch_title)
        size_policy_value.setHorizontalStretch(stretch_value)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        section_layout.addWidget(title, label_count, 0)
        section_layout.addWidget(value, label_count, 1)
        label_count = label_count + 1
    if 20 > minimums > label_count:
        for i in range(minimums - label_count):
            margin = QLabel()
            section_layout.addWidget(margin, label_count, 0)
            label_count = label_count + 1
    return section_layout


def make_dummy_section(num):
    section = QGroupBox()
    section_layout = QVBoxLayout()
    for i in range(num):
        title = QLabel()
        section_layout.addWidget(title)
    section.setLayout(section_layout)
    section.setTitle('Dummy')
    section.setDisabled(True)
    return section


def savefile_choose_dialog(all_images=False):
    caption = 'Save File'
    path = os.path.expanduser('~')
    default_filename = os.path.join(path, 'parameters.json')
    if all_images:
        default_filename = os.path.join(path, 'all_parameters.json')
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


def file_choose_dialog(where=False):
    if where:
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


def directory_choose_dialog(where=False):
    if where:
        app = QApplication(sys.argv)
    caption = 'Select Directory'
    default_dir = os.path.expanduser('~')
    directory = QFileDialog.getExistingDirectory(
        None,
        caption,
        default_dir,
    )
    return directory
