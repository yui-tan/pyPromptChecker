# -*- coding: utf-8 -*-

import csv
import json
import os
import shutil
import hashlib

from PyQt6.QtWidgets import QApplication


def export_json(target_json, filepath):
    try:
        with open(filepath, 'w') as f:
            json.dump(target_json, f, sort_keys=True, indent=4, ensure_ascii=False)
            return True, None
    except Exception as e:
        return 'Error occurred during writing JSON.', e


def import_json(filepath):
    try:
        with open(filepath) as j:
            json_data = json.load(j)
            return json_data, None
    except json.JSONDecodeError as e:
        print('This is invalid JSON\n' + str(e) + '\n {}'.format(filepath))
        return None, e
    except Exception as e:
        return 'Error occurred during loading JSON.', e


def import_model_list(filepath):
    if os.path.exists(filepath):
        with open(filepath, encoding='utf8', newline='') as f:
            csvreader = csv.reader(f)
            model_list = [row for row in csvreader]
        return model_list
    else:
        return None


def image_copy_to(source, destination, is_move=False):
    destination_path = os.path.join(destination, os.path.basename(source))
    if not os.path.exists(destination_path):
        try:
            shutil.copy(source, destination)
            if os.path.exists(destination) and is_move:
                os.remove(source)
                return True, None
            return True, None
        except Exception as e:
            return 'Error occurred moving/copying files.', e
    else:
        return 'The same files already exists in destination.', 'AlreadyExistsError'


def clear_trash_bin(directory_path):
    file_list = os.listdir(directory_path)
    for filename in file_list:
        filepath = os.path.join(directory_path, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            return False, e
    return True


def is_directory_empty(directory_path):
    file_list = os.listdir(directory_path)
    return len(file_list) == 0


def model_hash_maker(file_list, progress):
    model_hash_data = []
    for tmp in file_list:
        model_name = os.path.basename(tmp)
        filename, extension = os.path.splitext(model_name)
        extension = extension.replace('.', '')
        with open(tmp, 'rb') as file:
            data = file.read()
            data_hash = hashlib.sha256(data).hexdigest()
            model_hash = data_hash[:10]
            model_hash_data.append([filename, model_hash, data_hash, filename, extension])
        progress.update_value()
        QApplication.processEvents()
    progress.setLabelText('Writing collected data......')
    QApplication.processEvents()
    with open('model_list.csv', 'a') as w:
        writer = csv.writer(w, lineterminator='\n')
        writer.writerows(model_hash_data)
    progress.update_value()
    progress.close()
