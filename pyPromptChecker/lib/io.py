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


def import_json():
    pass


def import_model_list(filepath):
    if os.path.exists(filepath):
        with open(filepath, encoding='utf8', newline='') as f:
            csvreader = csv.reader(f)
            model_list = [row for row in csvreader]
        return model_list
    else:
        return None


def image_copy_to(source, destination, is_move=False):
    try:
        shutil.copy(source, destination)
        if os.path.exists(destination) and is_move:
            os.remove(source)
            return True, None
        return True, None
    except Exception as e:
        return 'Error occurred moving/copying files.', e


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


def model_hash_maker(directory, progress):
    file_list = os.listdir(directory)
    file_list = [os.path.join(directory, v) for v in file_list if os.path.isfile(os.path.join(directory, v))]
    file_list = [v for v in file_list if 'safetensors' in v or 'ckpt' in v]
    progress.setLabelText('Loading model file......')
    progress.setRange(0, len(file_list))
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
    with open('model_list.csv', 'a') as w:
        writer = csv.writer(w, lineterminator='\n')
        writer.writerows(model_hash_data)
    progress.close()
