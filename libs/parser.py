import os
import re
import json


class ChunkData:
    def __init__(self, data):
        self.data = data
        self.original_data = data
        self.data_list = []
        self.error_list = []
        self.params = {}
        if not data:
            self.data = 'This file has no embedded data'

    def data_get(self):
        return self.data

    def data_list_get(self):
        return self.data_list

    def dictionary_get(self, key):
        if self.params:
            return self.params.get(key)
        else:
            return None

    def dictionary_length(self):
        return len(self.params)

    def original_data_get(self):
        return self.original_data

    def data_refresh(self, delete_target, add_list):
        if delete_target:
            self.data = self.data.replace(delete_target, '')
        if len(add_list) > 0:
            for index, value in enumerate(add_list):
                if len(value) == 2:
                    self.data_list = self.data_list + [value]
                else:
                    self.error_list = self.error_list + [value]

    def filepath_registration(self, filepath):
        filename = os.path.basename(filepath)
        self.data_list = self.data_list + [['Filename', filename], ['Filepath', filepath]]

    def make_dictionary(self):
        control_net = 0
        loras = 0
        if not self.data_list:
            return None
        self.data_list = [[value.strip() for value in d1] for d1 in self.data_list]
        for tmp in self.data_list:
            key, value = tmp
            self.params[key] = value
            if 'ControlNet' in key and 'True' in value:
                control_net = control_net + 1
            if 'Lora' in key:
                loras = loras + 1
        if control_net > 0:
            self.params['ControlNet'] = str(control_net)
        if loras > 0:
            self.params['Lora'] = str(loras)

    def model_name(self, model_list):
        model_hash = self.params.get('Model hash')
        if model_hash:
            model_name = '[' + model_hash + ']'
            for tmp in model_list:
                if tmp[1] == model_hash:
                    model_name = tmp[0] + ' [' + tmp[1] + ']'
            self.params['Model'] = model_name

    def json_export(self, filepath):
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.params, f, sort_keys=True, indent=4, ensure_ascii=False)


def parse_parameter(chunks, filepath, model_list):
    target_data = ChunkData(chunks)
    target_data.filepath_registration(filepath)
    target_data = main_prompt_parse(target_data)
    target_data = lora_parse(target_data)
    target_data = tiled_diffusion_parse(target_data)
    target_data = control_net_parse(target_data)
    target_data = main_status_parse(target_data)
    target_data.make_dictionary()
    target_data.model_name(model_list)
    return target_data


def main_status_parse(target_data):
    target_str = target_data.data_get()
    if target_str == 'This file has no embedded data':
        return target_data
    if target_str:
        result = [[value.split(':')[0], value.split(':')[1]] for value in target_str.split(',')]
        target_data.data_refresh(target_str, result)
    return target_data


def main_prompt_parse(target_data):
    prompt_regex = r'(?<=parameters)([\s\S]*)(?=Steps)'
    result = [['Positive', 'None'], ['Negative', 'None']]
    prompt = target_data.data_get()
    if prompt == 'This file has no embedded data':
        result = [['Positive', prompt]]
        target_data.data_refresh(prompt, result)
        return target_data
    match = re.search(prompt_regex, prompt)
    if match:
        prompt = match.group()
        tmp = prompt.split('Negative prompt: ')
        result[0][1] = tmp[0]
        if len(tmp) == 2:
            result[1][1] = tmp[1]
        target_data.data_refresh('parameters' + prompt, result)
    return target_data


def lora_parse(target_data):
    lora_regex = r'(?<=Lora hashes: )"[^"]*"'
    match = re.search(lora_regex, target_data.data_get())
    if match:
        target = match.group().replace('"', '')
        loras = [d1.split(':')[0].strip() + ' ' + '[' + d1.split(':')[1].strip() + ']' for d1 in target.split(',')]
        loras = [['Lora ' + str(index), value]for index, value in enumerate(loras)]
        target_data.data_refresh('Lora hashes: "' + target + '",', loras)
    return target_data


def additional_networks_parse(target_data):
    pass


def tiled_diffusion_parse(target_data):
    tiled_diffusion_regex = r'Tiled Diffusion: \{.*},'
    region_regex = r'"Region [0-9][^}]*}'
    region_control_regex = r'(?<="Region control": ).*$'
    comma_between_hyphen = r'\"[^"]*"'
    region_status_list = []
    match = re.search(tiled_diffusion_regex, target_data.data_get())
    if match:
        tiled_diffusion_status = match.group()
        if 'Region' in tiled_diffusion_status:
            region_status = re.findall(region_regex, tiled_diffusion_status)
            tiled_diffusion_status = re.sub(region_control_regex, 'True', tiled_diffusion_status)
            for tmp in region_status:
                tmp = re.sub(comma_between_hyphen, lambda match: match.group().replace(',', '<comma>'), tmp)
                number = tmp.split(':')[0]
                target_str = tmp.replace(number + ':', '').replace('{', '').replace('}', '').replace('"', '')
                target = target_str.split(',')
                number = number.replace('"', '')
                target = [[number + item.split(':')[0].replace('_', ' '), item.split(':')[1]] for item in target]
                region_status_list = region_status_list + target
        tiled_diffusion_status = tiled_diffusion_status.replace('Tiled Diffusion: {', 'Tiled diffusion: True, ')
        tiled_diffusion_status = tiled_diffusion_status.replace('Tile tile', 'Tile')
        tiled_diffusion_status = tiled_diffusion_status.replace('"', '').replace('}', '')
        result = [item.split(':') for item in tiled_diffusion_status.split(',')]
        if region_status_list:
            result = result + region_status_list
        result = [[d2.replace('<comma>', ',').strip() for d2 in d1] for d1 in result]
        result = [d1 for d1 in result if any(d1)]
        target_data.data_refresh(match.group(), result)
    return target_data


def control_net_parse(target_data):
    control_net_regex = r'(ControlNet.*"[^"]*",)'
    match = re.search(control_net_regex, target_data.data_get())
    if match:
        result = []
        target = match.group()
        controlnet_result = re.finditer(r'(ControlNet[^:]*: "[^"]*")', target)
        for tmp in controlnet_result:
            number = tmp.group().split(':')[0]
            hyphened = re.sub(r'(\([^)]*\))', lambda match: match.group(0).replace(', ', '-'), tmp.group(0))
            detail_param = re.sub(r'(["|,][^:]*: )', lambda match: match.group(0).replace(',', ', ' + number), hyphened)
            detail_param = detail_param.replace(number + ':', number + ': True,' + number)
            detail_param = detail_param.replace('"', '')
            result = [[value.split(':')[0], value.split(':')[1]] for value in detail_param.split(',')]
        target_data.data_refresh(target, result)
    return target_data


def regional_prompter_parse(target_data):
    pass
