# -*- coding: utf-8 -*-

from PIL import Image

import uuid
import csv
import json
import os
import shutil
import hashlib


def export_file(data, kind, filepath):
    try:
        if kind == 'csv':
            with open(filepath, 'a') as f:
                writer = csv.writer(f, lineterminator='\n')
                writer.writerows(data)
        elif kind == 'text':
            with open(filepath, 'w') as f:
                f.write(data)
        elif kind == 'json':
            with open(filepath, 'w') as f:
                json.dump(data, f, sort_keys=True, indent=4, ensure_ascii=False)
        return True, None
    except Exception as e:
        return 'Error occurred during writing file.', e


def io_export_json(json_data, filepath):
    try:
        with open(filepath, 'w') as f:
            json.dump(json_data, f, sort_keys=True, indent=4, ensure_ascii=False)
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


def image_copy_to(source, destination, use_copy=True):
    destination_path = os.path.join(destination, os.path.basename(source))

    if os.path.exists(destination_path):
        base, ext = os.path.splitext(destination_path)
        unique_suffix = str(uuid.uuid4())[:8]
        destination_path = os.path.join(destination, f"{base}-{unique_suffix}{ext}")

    if os.path.exists(source):
        try:
            shutil.copy(source, destination_path)
            if os.path.exists(destination_path) and not use_copy:
                os.remove(source)
                return destination_path, None
            return destination_path, None

        except Exception as e:
            return 'Error occurred moving/copying files.', e
    else:
        return "The source file doesn't exists.", 'FileNotFoundError'


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


def extract_lora_hash(filepath):
    lora_hash = hashlib.sha256()
    block = 1024 * 1024

    with open(filepath, 'rb') as f:
        f.seek(0)
        header = f.read(8)
        n = int.from_bytes(header, "little")
        offset = n + 8
        f.seek(offset)

        for chunk in iter(lambda: f.read(block), b''):
            lora_hash.update(chunk)

    return lora_hash.hexdigest()


def extract_model_hash(filepath):
    model_hash = hashlib.sha256()
    block = 1024 * 1024

    with open(filepath, 'rb') as f:
        for chunk in iter(lambda: f.read(block), b''):
            model_hash.update(chunk)

    return model_hash.hexdigest()


def extract_image_hash(filepath):
    img = Image.open(filepath)
    return hashlib.md5(img.tobytes()).hexdigest()
