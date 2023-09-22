# -*- coding: utf-8 -*-

import json
import png
from PIL import Image


def is_json_check(filepath):
    try:
        with open(filepath, 'r') as f:
            json.load(f)
        return True
    except (json.JSONDecodeError, FileNotFoundError, UnicodeDecodeError):
        return False


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
        elif is_json_check(filepath):
            return [filepath, 9]
        else:
            return None


def chunk_text_extractor(target, method, index=1):
    if method == 0:
        index = max(index, 1)
        try:
            reader = png.Reader(filename=target)
            chunks = reader.chunks()
            chunk_list = list(chunks)

            for chunk_type, chunk_data in chunk_list:
                if chunk_type == b'IHDR':
                    width = int.from_bytes(chunk_data[0:4], byteorder='big')
                    height = int.from_bytes(chunk_data[4:8], byteorder='big')
                    break

            original_size = str(width) + 'x' + str(height)

            if index >= len(chunk_list):
                print('{} has no embedded data!'.format(target))
                return None, None

            text = ''
            ends = min(index + 4, len(chunk_list) - 1)
            for i in range(index, ends):
                chunk_data = chunk_list[i][1]
                str_data = chunk_data.decode('utf-8', errors='ignore').replace("\x00", "")
                if str_data.startswith('parameters'):
                    text = text + str_data
                elif str_data.startswith('extras'):
                    if text:
                        text = text + str_data.replace('extras', ',')
                    else:
                        text = text + str_data.replace('extras', 'parameters')

            if text.startswith('parameters'):
                return text, original_size
            else:
                print('{} has not valid parameters'.format(target))
                return None, original_size

        except Exception as e:
            print('An error occurred while decoding: {}\n{}'.format(target, str(e)))
            return None, None

    elif method == 1 or method == 2:
        try:
            img = Image.open(target)
            exif = img._getexif()
            if exif:
                binary = exif.get(37510, b'')
                text = binary.decode('utf-8', errors='ignore').replace("\x00", "")
            else:
                text = 'no embedded data'
            width, height = img.size

            if text.startswith('UNICODE'):
                text = text.replace('UNICODE', 'parameters', 1)
                original_size = str(width) + 'x' + str(height)
                return text, original_size
            else:
                original_size = str(width) + 'x' + str(height)
                print('{} has not valid parameters'.format(target))
                return None, original_size

        except Exception as e:
            print('An error occurred while decoding: {}\n{}'.format(target, str(e)))
            return None, None
