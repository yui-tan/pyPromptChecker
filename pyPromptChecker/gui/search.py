# -*- coding: utf-8 -*-

import re


def cfg_checks(cfg_keywords, relation, targets):
    result = []
    for target in targets:
        if relation == 'Less than' and float(cfg_keywords) > float(target):
            result.append(True)
        elif relation == 'Equal to' and float(cfg_keywords) == float(target):
            result.append(True)
        elif relation == 'Greater than' and float(cfg_keywords) < float(target):
            result.append(True)
        else:
            result.append(False)
    return result


def status_checks(keyword, targets):
    result = []
    for target in targets:
        if keyword == target:
            result.append(True)
        else:
            result.append(False)
    return result


def parse_search_query(input_string):
    phrases = re.findall(r'"([^"]*)"', input_string)
    tmp_string = re.sub(r'"[^"]*"', 'REPLACEMENT_STRING', input_string)
    and_parts = tmp_string.split()
    or_parts = [value.split('|') for value in and_parts]

    for i, part in enumerate(or_parts):
        d2 = len(or_parts[i])
        for j in range(d2):
            if 'REPLACEMENT_STRING' in or_parts[i][j]:
                or_parts[i][j] = or_parts[i][j].replace('REPLACEMENT_STRING', f'{phrases.pop(0)}').strip()
            else:
                or_parts[i][j] = or_parts[i][j].strip()

    result = or_parts

    return result


def target_string_adjust(positive, negative, region, target):
    positive_target = []
    negative_target = []
    region_target = []
    result = []

    if positive:
        positive_target = [value.get('Positive') for value in target]
    if negative:
        negative_target = [value.get('Negative') for value in target]
    if region:
        for tg in target:
            number = tg.get('Region control', None)
            if not number:
                region_target.append('---')
            else:
                str_target = ''
                for cnt in range(1, int(number) + 1):
                    prompt = tg.get('Region ' + str(cnt) + ' prompt')
                    negative = tg.get('Region ' + str(cnt) + ' neg prompt')
                    region_prompt = prompt + ', ' + negative
                    str_target += region_prompt
                region_target.append(str_target)

    with_values = [x for x in [positive_target, negative_target, region_target] if x]
    values_count = len(with_values)

    if values_count == 1:
        result = [value for d1 in with_values for value in d1]
    elif values_count == 2:
        result = [str(x) + '\n' + str(y) for x, y in zip(*with_values)]
    elif values_count == 3:
        result = [str(x) + '\n' + str(y) + '\n' + str(z) for x, y, z in zip(*with_values)]

    return result


def search_prompt_string(query, target_text, case):
    if len(query) > 1 and isinstance(query, list):
        return any(search_prompt_string(query_value, target_text, case) for query_value in query)
    else:
        if isinstance(query, list):
            query = query[0]
        if case:
            return query.lower in target_text.lower()
        else:
            return query in target_text


def search_images(condition_list, target_list):
    result = []
    prompt_result = []
    status_result = []
    extensions_result = []
    search_strings = condition_list.get('Search')

    if condition_list.get('Prompt') and search_strings:
        search_strings = parse_search_query(search_strings)
        case_insensitive = condition_list.get('Case insensitive')
        positive = condition_list.get('Positive')
        negative = condition_list.get('Negative')
        region = condition_list.get('Region control')

        target_data = target_string_adjust(positive, negative, region, target_list)
        for target in target_data:
            if all(search_prompt_string(query, target, case_insensitive) for query in search_strings):
                prompt_result.append(True)
            else:
                prompt_result.append(False)

    if condition_list.get('Status'):
        model_result = []
        seed_result = []
        cfg_result = []
        model_keyword = condition_list.get('Model')
        seed_keyword = condition_list.get('Seed')
        cfg_keyword = condition_list.get('CFG', '0')
        cfg_relation = condition_list.get('Relation')

        if model_keyword or seed_keyword or cfg_keyword:
            if model_keyword:
                model_target = [value.get('Model') for value in target_list]
                model_result = status_checks(model_keyword, model_target)
            if seed_keyword:
                seed_target = [value.get('Seed') for value in target_list]
                seed_result = status_checks(seed_keyword, seed_target)
            if float(cfg_keyword) > 0:
                cfg_target = [value.get('CFG scale') for value in target_list]
                cfg_result = cfg_checks(cfg_keyword, cfg_relation, cfg_target)

        result_with_values = [x for x in [model_result, seed_result, cfg_result] if x]
        result_counts = len(result_with_values)

        if result_counts > 1:
            tmp_status = list(zip(*result_with_values))
            for status in tmp_status:
                if all(status):
                    status_result.append(True)
                else:
                    status_result.append(False)
        else:
            tmp_status = [value for d1 in result_with_values for value in d1]
            for status in tmp_status:
                if status:
                    status_result.append(True)
                else:
                    status_result.append(False)

    if condition_list.get('Extension'):
        hires_keys = ['Hires upscaler', 'Face restoration', 'Extras']
        cfg_keys = ['Dynamic thresholding enabled', 'CFG auto', 'CFG scheduler']
        lora_keys = ['Lora', 'AddNet Enabled', 'TI in prompt']
        hires_enable = condition_list.get('Hires / Extras')
        lora_enable = condition_list.get('LoRa / AddNet')
        cfg_enable = condition_list.get('CFG')
        tiled_diffusion_enable = condition_list.get('Tiled diffusion')
        controlnet_enable = condition_list.get('ControlNet')
        regional_prompter_enable = condition_list.get('Regional prompter')

        lora = []
        hires = []
        cfg = []
        tiled = []
        control = []
        rp = []

        for target in target_list:
            if lora_enable:
                lora.append(any(key in v for v in target for key in lora_keys))
            if hires_enable:
                hires.append(any(key in v for v in target for key in hires_keys))
            if cfg_enable:
                cfg.append(any(key in v for v in target for key in cfg_keys))
            if tiled_diffusion_enable:
                tiled.append('Tiled diffusion' in target)
            if controlnet_enable:
                control.append('ControlNet' in target)
            if regional_prompter_enable:
                rp.append('RP Active' in target)

        result_with_values = [x for x in [lora, hires, cfg, tiled, control, rp] if x]
        result_counts = len(result_with_values)

        if result_counts > 1:
            tmp_status = list(zip(*result_with_values))
            for status in tmp_status:
                if all(status):
                    extensions_result.append(True)
                else:
                    extensions_result.append(False)
        else:
            tmp_status = [value for d1 in result_with_values for value in d1]
            for status in tmp_status:
                if status:
                    extensions_result.append(True)
                else:
                    extensions_result.append(False)

    no_empty_arrays = [x for x in [prompt_result, status_result, extensions_result] if x]
    array_counts = len(no_empty_arrays)

    if array_counts > 1:
        tmp_result = list(zip(*no_empty_arrays))
        for index, status in enumerate(tmp_result):
            if all(status):
                result.append(index)
    else:
        tmp_result = [value for d1 in no_empty_arrays for value in d1]
        for index, status in enumerate(tmp_result):
            if status:
                result.append(index)

    return result
