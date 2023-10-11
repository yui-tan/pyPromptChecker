# -*- coding: utf-8 -*-

import re
from PyQt6.QtWidgets import QDialog, QGridLayout, QGroupBox, QCheckBox, QSlider
from PyQt6.QtWidgets import QWidget, QPushButton, QLabel, QLineEdit, QComboBox
from PyQt6.QtWidgets import QRadioButton
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtCore import Qt, QRegularExpression

from .dialog import MessageBox


class SearchWindow(QDialog):
    def __init__(self, model_list: list, controller, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Search")
        self.controller = controller
        self.conditions = {}
        self.result = 'Tabs'
        self.caller = None
        self.prompt = None
        self.status = None
        self.extension = None
        self.search_box = None
        self.search_model = None
        self.search_seed_box = None
        self.search_cfg_label = None
        self.search_button = None
        self.central_widget = None
        self.__init_search_window(model_list)

    def __init_search_window(self, model_list: list):
        layout = QGridLayout()

        result_label = QLabel('Result shows: ')
        result_box = QComboBox()
        result_box.addItems(['Tabs', 'Listview', 'Thumbnails'])
        result_box.currentIndexChanged.connect(self.__result_change)

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
        search_cfg.valueChanged.connect(self.__value_change)

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
        search_button.clicked.connect(self.__do_search)
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

    def __result_change(self):
        self.result = self.sender().currentText()

    def __value_change(self):
        self.search_cfg_label.setText('CFG : ' + str(self.sender().value() * 0.5))

    def __do_search(self):
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

        if self.__validation():
            params = self.controller.request_reception('dictionary', self.caller)
            matched = search_images(self.conditions, params)
            if len(matched) > 0:
                match_text = str(len(matched)) + ' image(s) found !'
            else:
                match_text = 'There is no match to show.'
            self.controller.request_reception('apply', self.caller, indexes=(matched, match_text))

    def __validation(self):
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

    def show_dialog(self, caller):
        self.caller = caller
        self.search_box.setFocus()
        self.show()

    def update_model_list(self, model_list: list):
        self.search_model.clear()
        self.search_model.addItems(model_list)

    def window_close(self):
        self.caller = None
        self.close()


def cfg_checks(cfg_keywords: str, relation: str, targets: list):
    result = []
    for target in targets:
        if relation == 'Less than' and float(cfg_keywords) > float(target):
            result.append(True)
        elif relation == 'Equal to' and float(cfg_keywords) == float(target):
            result.append(True)
        elif relation == 'Greater than' and float(cfg_keywords) < float(target):
            result.append(True)
        else:
            result.append(False)
    return result


def status_checks(keyword: str, targets: list):
    result = []
    for target in targets:
        if keyword == target:
            result.append(True)
        else:
            result.append(False)
    return result


def parse_search_query(input_string: str):
    phrases = re.findall(r'"([^"]*)"', input_string)
    tmp_string = re.sub(r'"[^"]*"', 'REPLACEMENT_STRING', input_string)
    and_parts = tmp_string.split()
    or_parts = [value.split('|') for value in and_parts]

    for i, part in enumerate(or_parts):
        d2 = len(or_parts[i])
        for j in range(d2):
            if 'REPLACEMENT_STRING' in or_parts[i][j]:
                or_parts[i][j] = or_parts[i][j].replace('REPLACEMENT_STRING', f'{phrases.pop(0)}').strip()
            else:
                or_parts[i][j] = or_parts[i][j].strip()

    result = or_parts

    return result


def target_string_adjust(positive: bool, negative: bool, region: bool, target: list):
    positive_target = []
    negative_target = []
    region_target = []
    result = []

    if positive:
        positive_target = [value.get('Positive') for value in target]
    if negative:
        negative_target = [value.get('Negative') for value in target]
    if region:
        for tg in target:
            number = tg.get('Region control', None)
            if not number:
                region_target.append('---')
            else:
                str_target = ''
                for cnt in range(1, int(number) + 1):
                    prompt = tg.get('Region ' + str(cnt) + ' prompt')
                    negative = tg.get('Region ' + str(cnt) + ' neg prompt')
                    region_prompt = prompt + ', ' + negative
                    str_target += region_prompt
                region_target.append(str_target)

    with_values = [x for x in [positive_target, negative_target, region_target] if x]
    values_count = len(with_values)

    if values_count == 1:
        result = [value for d1 in with_values for value in d1]
    elif values_count == 2:
        result = [str(x) + '\n' + str(y) for x, y in zip(*with_values)]
    elif values_count == 3:
        result = [str(x) + '\n' + str(y) + '\n' + str(z) for x, y, z in zip(*with_values)]

    return result


def search_prompt_string(query: list, target_text: str, case: bool):
    if len(query) > 1 and isinstance(query, list):
        return any(search_prompt_string(query_value, target_text, case) for query_value in query)
    else:
        if isinstance(query, list):
            query = query[0]
        if case:
            return query.lower() in target_text.lower()
        else:
            return query in target_text


def search_images(condition_list: dict, target_list: list):
    result = []
    prompt_result = []
    status_result = []
    extensions_result = []
    search_strings = condition_list.get('Search')

    if condition_list.get('Prompt') and search_strings:
        search_strings = parse_search_query(search_strings)
        case_insensitive = condition_list.get('Case insensitive')
        positive = condition_list.get('Positive')
        negative = condition_list.get('Negative')
        region = condition_list.get('Region control')

        target_data = target_string_adjust(positive, negative, region, target_list)
        for target in target_data:
            if not target or target == 'This file has no embedded data':
                target = '----'
            if all(search_prompt_string(query, target, case_insensitive) for query in search_strings):
                prompt_result.append(True)
            else:
                prompt_result.append(False)

    if condition_list.get('Status'):
        model_result = []
        seed_result = []
        cfg_result = []
        model_keyword = condition_list.get('Model')
        seed_keyword = condition_list.get('Seed')
        cfg_keyword = condition_list.get('CFG', '0')
        cfg_relation = condition_list.get('Relation')

        if model_keyword or seed_keyword or cfg_keyword:
            if model_keyword:
                model_target = [value.get('Model') for value in target_list]
                model_result = status_checks(model_keyword, model_target)
            if seed_keyword:
                seed_target = [value.get('Seed') for value in target_list]
                seed_result = status_checks(seed_keyword, seed_target)
            if float(cfg_keyword) > 0:
                cfg_target = [value.get('CFG scale') for value in target_list]
                cfg_result = cfg_checks(cfg_keyword, cfg_relation, cfg_target)

        result_with_values = [x for x in [model_result, seed_result, cfg_result] if x]
        result_counts = len(result_with_values)

        if result_counts > 1:
            tmp_status = list(zip(*result_with_values))
            for status in tmp_status:
                if all(status):
                    status_result.append(True)
                else:
                    status_result.append(False)
        else:
            tmp_status = [value for d1 in result_with_values for value in d1]
            for status in tmp_status:
                if status:
                    status_result.append(True)
                else:
                    status_result.append(False)

    if condition_list.get('Extension'):
        hires_keys = ['Hires upscaler', 'Face restoration', 'Extras']
        cfg_keys = ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler']
        lora_keys = ['Lora', 'AddNet Enabled', 'Textual inversion']
        hires_enable = condition_list.get('Hires / Extras')
        lora_enable = condition_list.get('LoRa / AddNet')
        cfg_enable = condition_list.get('CFG')
        tiled_diffusion_enable = condition_list.get('Tiled diffusion')
        controlnet_enable = condition_list.get('ControlNet')
        regional_prompter_enable = condition_list.get('Regional prompter')

        lora = []
        hires = []
        cfg = []
        tiled = []
        control = []
        rp = []

        for target in target_list:
            if lora_enable:
                lora.append(any(key in v for v in target for key in lora_keys))
            if hires_enable:
                hires.append(any(key in v for v in target for key in hires_keys))
            if cfg_enable:
                cfg.append(any(key in v for v in target for key in cfg_keys))
            if tiled_diffusion_enable:
                tiled.append('Tiled diffusion' in target)
            if controlnet_enable:
                control.append('ControlNet' in target)
            if regional_prompter_enable:
                rp.append('RP Active' in target)

        result_with_values = [x for x in [lora, hires, cfg, tiled, control, rp] if x]
        result_counts = len(result_with_values)

        if result_counts > 1:
            tmp_status = list(zip(*result_with_values))
            for status in tmp_status:
                if all(status):
                    extensions_result.append(True)
                else:
                    extensions_result.append(False)
        else:
            tmp_status = [value for d1 in result_with_values for value in d1]
            for status in tmp_status:
                if status:
                    extensions_result.append(True)
                else:
                    extensions_result.append(False)

    no_empty_arrays = [x for x in [prompt_result, status_result, extensions_result] if x]
    array_counts = len(no_empty_arrays)

    if array_counts > 1:
        tmp_result = list(zip(*no_empty_arrays))
        for index, status in enumerate(tmp_result):
            if all(status):
                result.append(index)
    else:
        tmp_result = [value for d1 in no_empty_arrays for value in d1]
        for index, status in enumerate(tmp_result):
            if status:
                result.append(index)

    return result
