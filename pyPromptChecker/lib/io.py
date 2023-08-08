import csv
import json
import os


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
    pass


def clear_trash_can():
    pass
