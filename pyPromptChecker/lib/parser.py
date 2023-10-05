# -*- coding: utf-8 -*-

import os
import re
import datetime

PROMPT_REGEX = r'([\S\s]*)(?=Steps: )'
LORA_HASH_REGEX = r'(?<=Lora hashes: )"[^"]*"'
TI_HASH_REGEX = r'(?<=TI hashes: )"[^"]*"'
TILED_DIFFUSION_REGEX = r'Tiled Diffusion: \{.*},'
REGION_REGEX = r'"Region [0-9][^}]*}'
REGION_CONTROL_REGEX = r'(?<="Region control": ).*$'
CONTROL_NET_REGEX = r'(ControlNet.*"[^"]*",)'
CFG_REGEX = r' CFG Scheduler Info: ".*",'
HYPHENED_STR_REGEX = r'\"[^"]*"'


class ChunkData:
    def __init__(self, data, filepath=None, filetype=None, size=None):
        self.filepath = filepath
        self.type = filetype
        self.size = size

        self.data = data
        self.original_data = data

        self.data_list = []
        self.error_list = []

        self.params = {}
        self.used_params = {}

    def init_class(self):
        if not self.data:
            self.data = 'This file has no embedded data'

        if self.type == 0:
            ext = 'PNG'
        elif self.type == 1:
            ext = 'JPEG'
        elif self.type == 2:
            ext = 'WEBP'
        elif self.type == 9:
            ext = 'JSON'
        else:
            ext = '---'

        filename = os.path.basename(self.filepath)

        self.data_list.extend([['Filename', filename],
                               ['Filepath', self.filepath],
                               ['Extensions', ext],
                               ['Image size', self.size]])

        if os.path.exists(self.filepath):
            timestamp = datetime.datetime.fromtimestamp(os.path.getctime(self.filepath))
            self.data_list.append(['Timestamp', timestamp.strftime('%Y/%m/%d %H:%M')])

        self.prompt_parse()

        if 'Tiled Diffusion' in self.data:
            self.tiled_diffusion_parse()

        if 'Lora' in self.data:
            self.lora_parse()

        if 'TI' in self.data:
            self.ti_parse()

        if 'ControlNet' in self.data:
            self.control_net_parse()

        if 'CFG Scheduler Info' in self.data:
            self.cfg_scheduler_parse()

        self.main_status_parse()
        self.make_dictionary()

    def data_refresh(self, delete_target, add_list):
        if delete_target:
            self.data = self.data.replace(delete_target, '')

        if add_list is not None and len(add_list) > 0:
            for index, value in enumerate(add_list):
                if len(value) == 2:
                    self.data_list.append(value)
                else:
                    self.error_list.append(value)

    def make_dictionary(self):
        add_net = 0
        extras = False
        cfg_auto = False

        if not self.data_list:
            return None

        self.data_list = [[value.strip() for value in d1] for d1 in self.data_list]
        for tmp in self.data_list:
            key, value = tmp

            if key == 'Tiled Diffusion scale factor' or key == 'Tiled Diffusion upscaler':
                continue
            elif 'AddNet Module' in key:
                add_net += 1
            elif 'Postprocess' in key:
                extras += 1
            elif key == 'Scheduler':
                cfg_auto += 1

            if value == 'true':
                value = 'True'

            self.params[key] = value

        if add_net > 0:
            self.params['AddNet Number'] = str(add_net)

        if extras:
            self.params['Extras'] = 'True'

        if cfg_auto:
            self.params['CFG auto'] = 'True'

    def model_name(self, model_list):
        model_hash = self.params.get('Model hash')
        if model_hash:
            model_name = '[' + model_hash + ']'
            if model_list:
                for tmp in model_list:
                    if model_hash in tmp[1]:
                        model_name = tmp[0] + ' [' + tmp[1] + ']'

            self.params['Model'] = model_name
            self.used_params['Model hash'] = True

    def vae_name(self, model_list):
        vae_hash = self.params.get('VAE hash')
        if vae_hash:
            vae_name = '[' + vae_hash + ']'
            if model_list:
                for tmp in model_list:
                    if vae_hash in tmp[1]:
                        vae_name = tmp[0] + ' [' + tmp[1] + ']'

            self.params['VAE'] = vae_name
            self.used_params['VAE hash'] = True

    def override_lora(self, model_list):
        for key, value in self.params.items():
            if 'Lora ' in key and '[' in value:
                match = re.search(r'\[.*]', value)
                if match:
                    lora_hash = match.group().replace('[', '').replace(']', '')
                    for tmp in model_list:
                        if lora_hash in tmp[1]:
                            self.params[key] = tmp[0] + ' [' + lora_hash + ']'

    def override_addnet_model(self, model_list):
        for key, value in self.params.items():
            if 'AddNet Model' in key:
                match = re.search(r'\(.*\)', value)
                if match:
                    lora_hash = match.group().replace('(', '').replace(')', '')
                    for tmp in model_list:
                        if lora_hash in tmp[1]:
                            self.params[key] = tmp[0] + ' (' + lora_hash + ')'

    def override_textual_inversion(self, model_list):
        for key, value in self.params.items():
            if 'Ti ' in key and '[' in value:
                match = re.search(r'\[.*]', value)
                if match:
                    ti_hash = match.group().replace('[', '').replace(']', '')
                    for tmp in model_list:
                        if tmp[1] in ti_hash:
                            self.params[key] = tmp[0] + ' [' + ti_hash + ']'

    def set_used_to_param_key(self, key):
        if key in self.params:
            self.used_params[key] = True

    def import_json(self, json_data):
        self.params = json_data
        self.used_params['Model hash'] = True

    def prompt_parse(self):
        result = [['Positive', 'None'], ['Negative', 'None']]
        if self.data == 'This file has no embedded data':
            result = [['Positive', self.data]]
            self.data_refresh(self.data, result)
            return

        match = re.search(PROMPT_REGEX, self.data)
        if match:
            prompt = match.group()
            matched_prompt = prompt

            if re.search(r'^parameters', prompt):
                matched_prompt = prompt.replace('parameters', '', 1)
            elif re.search(r'^UNICODE', prompt):
                matched_prompt = prompt.replace('UNICODE', '', 1)

            tmp = matched_prompt.split('Negative prompt: ')
            result[0][1] = tmp[0]

            if len(tmp) == 2:
                result[1][1] = tmp[1]

            self.data_refresh(prompt, result)
        else:
            match = re.search(r'^parameters', self.data)
            if match:
                matched_prompt = match.group()
                matched_prompt = matched_prompt.replace('parameters', '', 1)
                self.data_refresh('parameters', matched_prompt)
            else:
                unicode_match = re.search(r'^UNICODE', self.data)
                if unicode_match:
                    matched_prompt = unicode_match.group()
                    matched_prompt = matched_prompt.replace('UNICODE', '', 1)
                    self.data_refresh('UNICODE', matched_prompt)

    def lora_parse(self):
        match = re.search(LORA_HASH_REGEX, self.data)
        if match:
            target = match.group().replace('"', '')
            loras = [d1.split(':')[0].strip() + ' ' + '[' + d1.split(':')[1].strip() + ']' for d1 in target.split(',')]
            loras = [['Lora ' + str(index), value] for index, value in enumerate(loras)]
            loras.append(['Lora', str(len(loras))])
            self.data_refresh('Lora hashes: "' + target + '",', loras)

    def ti_parse(self):
        match = re.search(TI_HASH_REGEX, self.data)
        if match:
            target = match.group().replace('"', '')
            tis = [d1.split(':')[0].strip() + ' ' + '[' + d1.split(':')[1].strip() + ']' for d1 in target.split(',')]
            tis = [['Ti ' + str(index), value] for index, value in enumerate(tis)]
            tis.append(['Textual inversion', str(len(tis))])
            self.data_refresh('TI hashes: "' + target + '",', tis)

    def tiled_diffusion_parse(self):
        region_status_list = []
        match = re.search(TILED_DIFFUSION_REGEX, self.data)
        if match:
            tiled_diffusion_status = match.group()

            if 'Region' in tiled_diffusion_status:
                region_status = re.findall(REGION_REGEX, tiled_diffusion_status)
                tiled_diffusion_status = re.sub(REGION_CONTROL_REGEX, 'True', tiled_diffusion_status)

                for tmp in region_status:
                    tmp = re.sub(HYPHENED_STR_REGEX, lambda match_part: match_part.group().replace(',', '<comma>'), tmp)
                    tmp = re.sub(HYPHENED_STR_REGEX, lambda match_part: match_part.group().replace(':', '<colon>'), tmp)
                    number = tmp.split(':')[0]
                    target_str = tmp.replace(number + ':', '').replace('{', '').replace('}', '').replace('"', '')
                    target = target_str.split(',')
                    number = number.replace('"', '')
                    target = [[number + item.split(':')[0].replace('_', ' '), item.split(':')[1]] for item in target]
                    region_status_list += target

                region_status_list.append(['Region control number', str(len(region_status))])

            tiled_diffusion_status = tiled_diffusion_status.replace('Tiled Diffusion: {', 'Tiled diffusion: True, ')
            tiled_diffusion_status = tiled_diffusion_status.replace('Tile tile', 'Tile')
            tiled_diffusion_status = tiled_diffusion_status.replace('"', '').replace('}', '')
            result = [item.split(':') for item in tiled_diffusion_status.split(',')]

            if region_status_list:
                result += region_status_list

            result = [[d2.replace('<comma>', ',').strip() for d2 in d1] for d1 in result]
            result = [[d2.replace('<colon>', ':').strip() for d2 in d1] for d1 in result]
            result = [[d2.replace('NoiseInv', 'Noise inversion') for d2 in d1] for d1 in result]
            result = [d1 for d1 in result if any(d1)]
            self.data_refresh(match.group(), result)

    def control_net_parse(self):
        match = re.search(CONTROL_NET_REGEX, self.data)
        if match:
            cnt = 0
            result = []
            target = match.group()
            controlnet_result = re.finditer(r'(ControlNet[^:]*: "[^"]*")', target)

            for tmp in controlnet_result:
                number = tmp.group().split(':')[0]
                hyphened = re.sub(r'(\([^)]*\))', lambda match_part: match_part.group(0).replace(', ', '<comma>'), tmp.group(0))
                detail_param = re.sub(r'(["|,][^:]*: )', lambda match_part: match_part.group(0).replace(',', ', ' + number), hyphened)
                detail_param = detail_param.replace(number + ':', number + ': True,' + number)
                detail_param = detail_param.replace('"', '')
                result = [[value.split(':')[0], value.split(':')[1]] for value in detail_param.split(',')]
                result = [[value.replace('<comma>', ',') for value in d1] for d1 in result]
                cnt += 1

            result.append(['ControlNet', str(cnt)])
            self.data_refresh(target, result)

    def cfg_scheduler_parse(self):
        match = re.search(CFG_REGEX, self.data)
        if match:
            target = match.group()
            cfg_match = re.search(HYPHENED_STR_REGEX, target)
            if cfg_match:
                cfg_result = cfg_match.group()
                cfg_result = cfg_result.replace('terget denoising', '\\n target denoising')
                cfg_result = cfg_result.replace('\\n"', '').replace('"', '')
                result = [[value.split(':')[0], str(value.split(':', 1)[1])] for value in cfg_result.split('\\n')]
                result.append(['CFG scheduler', 'True'])
                self.data_refresh(target, result)

    def main_status_parse(self):
        if self.data == 'This file has no embedded data':
            return

        if self.data:
            target_str = re.sub(HYPHENED_STR_REGEX, lambda match: match.group().replace(',', '<comma>'), self.data)
            noise_match = re.search(r'\nTemplate:[\s\S]*$', self.data)

            if noise_match:
                target_str = target_str.replace(noise_match.group(), '')

            result = [[value.split(':')[0], value.split(':')[1]] for value in target_str.split(',')]
            result = [[d2.replace('<comma>', ',').replace('"', '').strip() for d2 in d1] for d1 in result]
            self.data_refresh(target_str, result)
