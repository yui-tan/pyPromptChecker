# -*- coding: utf-8 -*-

from PIL import Image
from onnxruntime import InferenceSession
from huggingface_hub.file_download import hf_hub_download

import csv
import PIL.Image
import cv2
import functools
import os
import numpy as np


def make_square(img, target_size):
    old_size = img.shape[:2]
    desired_size = max(old_size)
    desired_size = max(desired_size, target_size)

    delta_w = desired_size - old_size[1]
    delta_h = desired_size - old_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [255, 255, 255]
    new_im = cv2.copyMakeBorder(
        img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
    )
    return new_im


def smart_resize(img, size):
    if img.shape[0] > size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_AREA)
    elif img.shape[0] < size:
        img = cv2.resize(img, (size, size), interpolation=cv2.INTER_CUBIC)
    return img


def model_downloads(repository, filename, label_file, model_path):
    os.makedirs(model_path, exist_ok=True)
    hf_hub_download(repository, label_file, local_dir=model_path, local_dir_use_symlinks=False, use_auth_token=False)
    hf_hub_download(repository, filename, local_dir=model_path, local_dir_use_symlinks=False, use_auth_token=False)


def model_loads(model_path):
    if not os.path.exists(model_path):
        print('Error')
        return None

    loaded_model = InferenceSession(model_path, providers=['CPUExecutionProvider'])
    return loaded_model


def label_loads(model_path, filename):
    label = os.path.join(model_path, filename)

    if not os.path.exists(label):
        print('Error')
        return None

    tags = []
    with open(label, "r") as f:
        reader = csv.reader(f)
        for row in reader:
            tags.append(row)

    tags_header = tags[0]
    category_index = tags_header.index('category')
    name_index = tags_header.index('name')

    names = [row[name_index] for row in tags[1:]]
    rating_indexes = [i for i, row in enumerate(tags[1:]) if row[category_index] == '9']
    general_indexes = [i for i, row in enumerate(tags[1:]) if row[category_index] == '0']
    chara_indexes = [i for i, row in enumerate(tags[1:]) if row[category_index] == '4']

    return names, rating_indexes, general_indexes, chara_indexes


def predict(image,
            general_threshold,
            character_threshold,
            filename,
            tag_names,
            rating_indexes,
            general_indexes,
            character_indexes
            ):
    model = model_loads(filename)
    _, height, width, _ = model.get_inputs()[0].shape

    # Alpha to white
    image = image.convert("RGBA")
    new_image = PIL.Image.new("RGBA", image.size, "WHITE")
    new_image.paste(image, mask=image)
    image = new_image.convert("RGB")
    image = np.asarray(image)

    # PIL RGB to OpenCV BGR
    image = image[:, :, ::-1]

    image = make_square(image, height)
    image = smart_resize(image, height)
    image = image.astype(np.float32)
    image = np.expand_dims(image, 0)

    input_name = model.get_inputs()[0].name
    label_name = model.get_outputs()[0].name
    probs = model.run([label_name], {input_name: image})[0]

    labels = list(zip(tag_names, probs[0].astype(float)))

    # First 4 labels are actually ratings: pick one with argmax
    ratings_names = [labels[i] for i in rating_indexes]
    rating = dict(ratings_names)

    # Then we have general tags: pick anywhere prediction confidence > threshold
    general_names = [labels[i] for i in general_indexes]
    general_res = [x for x in general_names if x[1] > general_threshold]
    general_res = dict(general_res)

    # Everything else is characters: pick anywhere prediction confidence > threshold
    character_names = [labels[i] for i in character_indexes]
    character_res = [x for x in character_names if x[1] > character_threshold]
    character_res = dict(character_res)

    b = dict(sorted(general_res.items(), key=lambda item: item[1], reverse=True))
    a = (", ".join(list(b.keys())).replace("_", " ").replace("(", "\(").replace(")", "\)"))
    c = ", ".join(list(b.keys()))

    return a, c, rating, character_res, general_res


def interrogate(model_param: str, filepath: str, tag_threshold: float, chara_threshold: float, installed: str):
    model_param = model_param.lower()
    model_filename = 'model.onnx'
    label_filename = "selected_tags.csv"
    model_path = os.path.join(os.path.abspath(installed), '.models/' + model_param)

    tag_names, rating_indexes, general_indexes, character_indexes = label_loads(model_path, label_filename)

    func = functools.partial(
        predict,
        filename=os.path.join(model_path, model_filename),
        tag_names=tag_names,
        rating_indexes=rating_indexes,
        general_indexes=general_indexes,
        character_indexes=character_indexes,
    )

    image_file = Image.open(filepath)
    prompt, original, rating, character, confidence = func(image_file, tag_threshold, chara_threshold)
    result = [filepath, model_param, tag_threshold, chara_threshold, prompt, original, rating, character, confidence]

    return result
