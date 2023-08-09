import csv
import json
import os
import shutil


def export_json(target_json, filepath):
    with open(filepath, 'w') as f:
        json.dump(target_json, f, sort_keys=True, indent=4, ensure_ascii=False)


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
            return True
        return False
    except Exception as e:
        return False, e


def clear_trash_bin(dirpath):
    file_list = os.listdir(dirpath)
    for filename in file_list:
        filepath = os.path.join(dirpath, filename)
        try:
            os.remove(filepath)
        except Exception as e:
            return False, e
    return True


def is_directory_empty(dirpath):
    file_list = os.listdir(dirpath)
    return len(file_list) == 0
