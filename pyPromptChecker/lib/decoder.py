# -*- coding: utf-8 -*-

import png
import pyexiv2


def image_format_identifier(filepath):
    with open(filepath, 'rb') as f:
        png_signature = b'\x89PNG\r\n\x1a\n'
        jpeg_signature = b'\xff\xd8\xff'
        webp_head_signature = b'\x52\x49\x46\x46'
        webp_foot_signature = b'\x57\x45\x42\x50'
        file_header = f.read(12)
        if file_header.startswith(png_signature):
            return [filepath, 0]
        elif file_header.startswith(jpeg_signature):
            return [filepath, 1]
        elif file_header.startswith(webp_head_signature) and file_header.endswith(webp_foot_signature):
            return [filepath, 2]
        else:
            return None


def chunk_text_extractor(target, index):
    if index < 0:
        raise Exception('The index value {} less than 0!'.format(index))

    try:
        reader = png.Reader(filename=target)
        chunks = reader.chunks()
        chunk_list = list(chunks)

        if index >= len(chunk_list):
            raise Exception('The index value {} is greater than the number of chunks in the file!'.format(index))

        chunk_data = chunk_list[index][1]
        text = chunk_data.decode('utf-8', errors='ignore').replace("\x00", "")

        if 'parameters' in text:
            return text
        else:
            return None

    except FileNotFoundError as e:
        raise Exception('The file "{}" was not found', format(target))

    except Exception as e:
        raise Exception('An error occurred while decoding: {}', format(target))


def jpeg_text_extractor(filepath):
    img = pyexiv2.Image(filepath)
    metadata = img.read_exif()
    text = metadata.get('Exif.Photo.UserComment')
    mark = 'charset=Unicode '
    if mark in text:
        return text.replace(mark, '')
    else:
        return None
