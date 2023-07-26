import png


def decode_text_chunk(target, index):
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
