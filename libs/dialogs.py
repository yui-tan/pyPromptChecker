import os
import sys
import csv
import re
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QHBoxLayout
from PyQt5.QtWidgets import QTabWidget, QTextEdit, QPushButton, QFileDialog, QDesktopWidget
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt


def make_label_layout(layout, data):
    filename = 'libs/model_list.csv'
    with open(filename, encoding='utf8', newline='') as f:
        csvreader = csv.reader(f)
        model_list = [row for row in csvreader]
    status_data = ['Filename',
                   'Filepath',
                   'Size',
                   'Seed',
                   'Sampler',
                   'Steps',
                   'Cfg scale',
                   'Model hash',
                   'Clip skip',
                   'Version',
                   'Tiled diffusion',
                   'Controlnet']

    for tmp in status_data:
        status_layout = QHBoxLayout()
        if tmp == 'Controlnet':
            title = QLabel('ControlNet')
            value = QLabel(data.get('Controlnet 0', 'False'))
        elif tmp == 'Tiled diffusion':
            title = QLabel(tmp)
            value = QLabel(data.get('Tiled diffusion', 'False'))
        elif tmp == 'Model hash' and model_list:
            title = QLabel('Model')
            value = QLabel(model_hash_to_name(data.get(tmp, 'None'), model_list))
        else:
            title = QLabel(tmp.replace('Cfg', 'CFG'))
            value = QLabel(data.get(tmp, 'None'))
        size_policy_title = title.sizePolicy()
        size_policy_value = value.sizePolicy()
        size_policy_title.setHorizontalStretch(1)
        size_policy_value.setHorizontalStretch(2)
        title.setSizePolicy(size_policy_title)
        value.setSizePolicy(size_policy_value)
        status_layout.addWidget(title)
        status_layout.addWidget(value)
        layout.addLayout(status_layout)
    return layout


def make_tab_widget(data):
    flag = False
    tabs = QTabWidget()
    tabs.setMaximumWidth(350)
    for tmp in data:
        if tmp == 'Tiled diffusion':
            page = QTabWidget(tabs)
            page.setLayout(make_tiled_diffusion_page(data))
            tabs.addTab(page, 'Tiled diffusion')
            flag = True
        if tmp == 'Controlnet 0':
            target = '-'.join(data.keys())
            match = re.findall(r'Controlnet [0-9]*', target)
            count = set(match)
            for number_of_controlnet in count:
                page = QTabWidget(tabs)
                page.setLayout(make_control_net_page(number_of_controlnet, data))
                tabs.addTab(page, number_of_controlnet)
                flag = True
#        if tmp == 'Lora hashes':
#            page = QTabWidget(tabs)
    if flag:
        return tabs
    else:
        return None


def make_tiled_diffusion_page(data):
    status_data = ['method',
                   'keep input size',
                   'tile batch size',
                   'tile width',
                   'tile height',
                   'tile Overlap',
                   'upscaler',
                   'scale factor'
                   ]
    page_layout = QVBoxLayout()
    for tmp in status_data:
        key_str = 'Tiled diffusion ' + tmp
        for key, value in data.items():
            if key_str == key:
                data_layout = QHBoxLayout()
                title = QLabel(tmp.capitalize())
                value = QLabel(value)
                data_layout.addWidget(title)
                data_layout.addWidget(value)
                page_layout.addLayout(data_layout)
    return page_layout


def make_control_net_page(target, data):
    page_layout = QVBoxLayout()
    for key, value in data.items():
        if target in key and target != key:
            data_layout = QHBoxLayout()
            title = key.replace(target, '').strip()
            if title.lower() == 'model':
                value = value.replace(' [', '\n[')
            title = QLabel(title.capitalize())
            value = QLabel(value.capitalize())
            data_layout.addWidget(title)
            data_layout.addWidget(value)
            page_layout.addLayout(data_layout)
    return page_layout


def model_hash_to_name(model_hash, model_list):
    result = None
    for tmp in model_list:
        if model_hash in tmp:
            result = tmp
            break
    if result:
        model_name = result[1] + ' [' + result[0] + ']'
    else:
        model_name = '[' + model_hash + ']'

    model_name = model_name.replace('"', '')

    return model_name
