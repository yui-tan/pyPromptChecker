# -*- coding: utf-8 -*-


def search_images(condition_list, target_list):
    search_keyword = condition_list.get('Prompt')
    exact_match = condition_list.get('Exact match')
    case_sensitive = condition_list.get('Case sensitive')
    negative_target = condition_list.get('Negative prompt')
    region_target = condition_list.get('Region control')
    model_keyword = condition_list.get('Model')
    seed_keyword = condition_list.get('Seed')
    cfg_keyword = condition_list.get('CFG')
    result = []

    if search_keyword:
        prompt_result = []
        if not exact_match:
            search_keyword = search_keyword.split()
        else:
            search_keyword = [search_keyword]
        target_positive_prompt = [value.get('Positive') for value in target_list]
        for tmp in search_keyword:
            for index, target in enumerate(target_positive_prompt):
                if not case_sensitive:
                    tmp = tmp.lower()
                    target = target.lower()
                if tmp in target:
                    prompt_result.append(index)

        if negative_target:
            target_negative_prompt = [value.get('Negative') for value in target_list]
            for tmp in search_keyword:
                for index, target in enumerate(target_negative_prompt):
                    if not case_sensitive:
                        tmp = tmp.lower()
                        target = target.lower()
                    if tmp in target:
                        prompt_result.append(index)

        if prompt_result:
            result.extend(prompt_result)

    if model_keyword:
        model = []
        target_model = [value.get('Model') for value in target_list]
        for index, tmp in enumerate(target_model):
            if model_keyword == tmp:
                model.append(index)
        if model:
            result.extend(model)

    if seed_keyword:
        seed = []
        target_seed = [value.get('Seed') for value in target_list]
        for index, tmp in enumerate(target_seed):
            if seed_keyword == tmp:
                seed.append(index)
        if seed:
            result.extend(seed)

    if cfg_keyword:
        cfg = []
        target_cfg = [value.get('CFG scale') for value in target_list]
        cfg_value, detail = cfg_keyword
        for index, tmp in enumerate(target_cfg):
            cfg_value = float(cfg_value)
            tmp = float(tmp)
            if detail == 'Less than' and tmp < cfg_value:
                cfg.append(index)
            elif detail == 'Equal to' and tmp == cfg_value:
                cfg.append(index)
            elif detail == 'Greater than' and tmp > cfg_value:
                cfg.append(index)
        if cfg:
            result.extend(cfg)

    if result:
        result = set(result)

    return result
