# -*- coding: utf-8 -*-

from PIL import Image
import sys
import PIL.Image
import functools
import os
import huggingface_hub

import numpy as np
from onnxruntime import InferenceSession
from pandas import read_csv
from cv2 import resize
from cv2 import copyMakeBorder
from cv2 import BORDER_CONSTANT
from cv2 import INTER_AREA
from cv2 import INTER_CUBIC

HF_TOKEN = os.environ.get("HF_TOKEN", "cpu")


def make_square(img, target_size):
    old_size = img.shape[:2]
    desired_size = max(old_size)
    desired_size = max(desired_size, target_size)

    delta_w = desired_size - old_size[1]
    delta_h = desired_size - old_size[0]
    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
    left, right = delta_w // 2, delta_w - (delta_w // 2)

    color = [255, 255, 255]
    new_im = copyMakeBorder(
        img, top, bottom, left, right, BORDER_CONSTANT, value=color
    )
    return new_im


def smart_resize(img, size):
    if img.shape[0] > size:
        img = resize(img, (size, size), interpolation=INTER_AREA)
    elif img.shape[0] < size:
        img = resize(img, (size, size), interpolation=INTER_CUBIC)
    return img


def model_downloads(repository, filename, label_file, model_name):
    model_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.models/' + model_name)
    os.makedirs(model_path, exist_ok=True)
    huggingface_hub.hf_hub_download(repository, filename, local_dir=model_path, local_dir_use_symlinks=False, use_auth_token=HF_TOKEN)
    huggingface_hub.hf_hub_download(repository, label_file, local_dir=model_path, local_dir_use_symlinks=False, use_auth_token=HF_TOKEN)


def model_loads(model_name, filename):
    path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.models/' + model_name)
    model_path = os.path.join(path, filename)

    if not os.path.exists(model_path):
        print('Error')
        return None

    loaded_model = InferenceSession(model_path, providers=['CPUExecutionProvider'])
    return loaded_model


def label_loads(model_name, filename):
    path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), '.models/' + model_name)
    label = os.path.join(path, filename)

    if not os.path.exists(label):
        print('Error')
        return None

    tags = read_csv(label)
    t_names = tags['name'].tolist()
    r_indexes = list(np.where(tags["category"] == 9)[0])
    g_indexes = list(np.where(tags["category"] == 0)[0])
    c_indexes = list(np.where(tags["category"] == 4)[0])
    return t_names, r_indexes, g_indexes, c_indexes


def predict(image,
            model_name,
            general_threshold,
            character_threshold,
            filename,
            tag_names,
            rating_indexes,
            general_indexes,
            character_indexes
            ):
    model = model_loads(model_name, filename)
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


def interrogate(model_param: str, filepath: str, tag_threshold: float, chara_threshold: float):
    model_param = model_param.lower()
    model_filename = 'model.onnx'
    label_filename = "selected_tags.csv"
    models = [['MOAT', 'SmilingWolf/wd-v1-4-moat-tagger-v2'],
              ['Swin', 'SmilingWolf/wd-v1-4-swinv2-tagger-v2'],
              ['ConvNext', 'SmilingWolf/wd-v1-4-convnext-tagger-v2'],
              ['ConvNextV2', 'SmilingWolf/wd-v1-4-convnextv2-tagger-v2'],
              ['ViT', 'SmilingWolf/wd-v1-4-vit-tagger-v2']]

    for model in models:
        model_base = '.models/' + model[0].lower() + '/' + model_filename
        label_base = '.models/' + model[0].lower() + '/' + label_filename
        model_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), model_base)
        label_path = os.path.join(os.path.abspath(os.path.dirname(sys.argv[0])), label_base)
        if not os.path.exists(model_path) or not os.path.exists(label_path):
            model_downloads(model[1], model_filename, label_filename, model[0].lower())

    tag_names, rating_indexes, general_indexes, character_indexes = label_loads(model_param, label_filename)

    func = functools.partial(
        predict,
        filename=model_filename,
        tag_names=tag_names,
        rating_indexes=rating_indexes,
        general_indexes=general_indexes,
        character_indexes=character_indexes,
    )

    image_file = Image.open(filepath)
    prompt, original, rating, character, confidence = func(image_file, model_param, tag_threshold, chara_threshold)
    result = [filepath, model_param, tag_threshold, chara_threshold, prompt, original, rating, character, confidence]

    return result
