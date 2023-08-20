# -*- coding: utf-8 -*-

import png
from PIL import Image


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


def chunk_text_extractor(target, method, index=1):
    if method == 0:
        index = max(index, 1)
        try:
            reader = png.Reader(filename=target)
            chunks = reader.chunks()
            chunk_list = list(chunks)

            if index >= len(chunk_list):
                print('The index value {} is greater than the number of chunks in the file!'.format(index))
                return None

            chunk_data = chunk_list[index][1]
            text = chunk_data.decode('utf-8', errors='ignore').replace("\x00", "")

            if text.startswith('parameters'):
                return text
            else:
                print('{} has not valid parameters'.format(target))
                return None

        except Exception as e:
            print('An error occurred while decoding: {}\n{}'.format(target, str(e)))
            return None

    elif method == 1:
        try:
            img = Image.open(target)
            exif = img._getexif()
            binary = exif.get(37510, b'')
            text = binary.decode('utf-8', errors='ignore').replace("\x00", "")

            if text.startswith('UNICODE'):
                return text
            else:
                print('{} has not valid parameters'.format(target))
                return None

        except Exception as e:
            print('An error occurred while decoding: {}\n{}'.format(target, str(e)))
            return None

    else:
        print("couldn't extract parameter from {}\nBecause this feature is not yet implemented.".format(target))
        return None
