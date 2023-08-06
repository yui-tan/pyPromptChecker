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
        self.used_params = {}
        if not data:
            self.data = 'This file has no embedded data'

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
        add_net = 0
        region_control = 0
        if not self.data_list:
            return None
        self.data_list = [[value.strip() for value in d1] for d1 in self.data_list]
        for tmp in self.data_list:
            key, value = tmp
            if key == 'Tiled Diffusion scale factor':
                continue
            if key == 'Tiled Diffusion upscaler':
                continue
            if 'NoiseInv' in key:
                key = key.replace('NoiseInv', 'Noise inversion')
            if value == 'true':
                value = 'True'
            if 'ControlNet' in key and 'True' in value:
                control_net += 1
            if 'Lora' in key:
                loras += 1
            if 'AddNet Module' in key:
                add_net += 1
            if 'Region' in key and 'enable' in key:
                region_control += 1
            self.params[key] = value
        if control_net > 0:
            self.params['ControlNet'] = str(control_net)
        if loras > 0:
            self.params['Lora'] = str(loras)
        if add_net > 0:
            self.params['AddNet Number'] = str(add_net)
        if region_control > 0:
            self.params['Region control'] = str(region_control)

    def model_name(self, model_list):
        model_hash = self.params.get('Model hash')
        if model_hash:
            model_name = '[' + model_hash + ']'
            if model_list:
                for tmp in model_list:
                    if tmp[1] == model_hash:
                        model_name = tmp[0] + ' [' + tmp[1] + ']'
            self.params['Model'] = model_name
            self.used_params['Model hash'] = True

    def json_export(self, filepath):
        if filepath:
            with open(filepath, 'w') as f:
                json.dump(self.params, f, sort_keys=True, indent=4, ensure_ascii=False)


def parse_parameter(chunks, filepath, model_list=None):
    target_data = ChunkData(chunks)
    target_data.filepath_registration(filepath)
    target_data = prompt_parse(target_data)
    target_data = lora_parse(target_data)
    target_data = tiled_diffusion_parse(target_data)
    target_data = control_net_parse(target_data)
    target_data = main_status_parse(target_data)
    target_data.make_dictionary()
    target_data.model_name(model_list)
    return target_data


def main_status_parse(target_data):
    target_str = target_data.data
    comma_in_hyphen_regex = r'\"[^"]*"'
    if target_str == 'This file has no embedded data':
        return target_data
    if target_str:
        target_str = re.sub(comma_in_hyphen_regex, lambda match: match.group().replace(',', '<comma>'), target_str)
        noise_match = re.search(r'\nTemplate:[\s\S]*$', target_str)
        if noise_match:
            target_str = target_str.replace(noise_match.group(), '')
        result = [[value.split(':')[0], value.split(':')[1]] for value in target_str.split(',')]
        result = [[d2.replace('<comma>', ',').replace('"', '').strip() for d2 in d1] for d1 in result]
        target_data.data_refresh(target_str, result)
    return target_data


def prompt_parse(target_data):
    prompt_regex = r'([\S\s]*)(?=Steps: )'
    result = [['Positive', 'None'], ['Negative', 'None']]
    prompt = target_data.data
    if prompt == 'This file has no embedded data':
        result = [['Positive', prompt]]
        target_data.data_refresh(prompt, result)
        return target_data
    match = re.search(prompt_regex, prompt)
    if match:
        prompt = match.group()
        if re.search(r'^parameters', prompt):
            prompt = prompt.replace('parameters', '', 1)
            send_prompt = 'parameters' + prompt
        else:
            send_prompt = prompt
        tmp = prompt.split('Negative prompt: ')
        result[0][1] = tmp[0]
        if len(tmp) == 2:
            result[1][1] = tmp[1]
        target_data.data_refresh(send_prompt, result)
    return target_data


def lora_parse(target_data):
    lora_regex = r'(?<=Lora hashes: )"[^"]*"'
    match = re.search(lora_regex, target_data.data)
    if match:
        target = match.group().replace('"', '')
        loras = [d1.split(':')[0].strip() + ' ' + '[' + d1.split(':')[1].strip() + ']' for d1 in target.split(',')]
        loras = [['Lora ' + str(index), value] for index, value in enumerate(loras)]
        target_data.data_refresh('Lora hashes: "' + target + '",', loras)
    return target_data


def tiled_diffusion_parse(target_data):
    tiled_diffusion_regex = r'Tiled Diffusion: \{.*},'
    region_regex = r'"Region [0-9][^}]*}'
    region_control_regex = r'(?<="Region control": ).*$'
    comma_between_hyphen = r'\"[^"]*"'
    region_status_list = []
    match = re.search(tiled_diffusion_regex, target_data.data)
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
    match = re.search(control_net_regex, target_data.data)
    if match:
        result = []
        target = match.group()
        controlnet_result = re.finditer(r'(ControlNet[^:]*: "[^"]*")', target)
        for tmp in controlnet_result:
            number = tmp.group().split(':')[0]
            hyphened = re.sub(r'(\([^)]*\))', lambda match: match.group(0).replace(', ', '<comma>'), tmp.group(0))
            detail_param = re.sub(r'(["|,][^:]*: )', lambda match: match.group(0).replace(',', ', ' + number), hyphened)
            detail_param = detail_param.replace(number + ':', number + ': True,' + number)
            detail_param = detail_param.replace('"', '')
            result = [[value.split(':')[0], value.split(':')[1]] for value in detail_param.split(',')]
            result = [[value.replace('<comma>', ',') for value in d1] for d1 in result]
        target_data.data_refresh(target, result)
    return target_data
