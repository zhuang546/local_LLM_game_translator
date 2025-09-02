# pyinstaller -F ConfigManager.py
from VLLMTranslator import VLLMTranslator
from os import path
import configparser
from json import load, dump
import VLLMDefaultConfig

'''
VLLMTranslatorManager 类：
负责配置管理和翻译请求的调度
翻译由 VLLMTranslator 处理
'''

class VLLMTranslatorManager:
    # 默认配置，用于初始化配置文件
    default_glossary = VLLMDefaultConfig.default_glossary
    default_virtual_history = VLLMDefaultConfig.default_virtual_history

    def __init__(self, config_path, glossary_path, history_path, default_config, debug=False):

        self.config_path = config_path
        self.glossary_path = glossary_path
        self.history_path = history_path
        self.default_config = default_config # 默认配置必须由外部类指定
        self.debug = debug

        self.config = configparser.ConfigParser()
        self.config_init()

        self.translator = VLLMTranslator( # 初始化翻译器
            base_url=self.config.get('Model', 'base_url',
                                     fallback=self.default_config['Model']['base_url']),
            model=self.config.get('Model', 'model',
                                  fallback=self.default_config['Model']['model']),
            max_tokens=self.config.getint('Model', 'max_tokens',
                                          fallback=int(self.default_config['Model']['max_tokens'])),
            temperature=self.config.getfloat('Model', 'temperature',
                                             fallback=float(self.default_config['Model']['temperature'])),
            top_p=self.config.getfloat('Model', 'top_p',
                                        fallback=float(self.default_config['Model']['top_p'])),
            history_max_length=self.config.getint('History', 'history_max_length',
                                                   fallback=int(self.default_config['History']['history_max_length'])),
            clear_history=self.config.getboolean('History', 'clear_history',
                                                  fallback=bool(self.default_config['History']['clear_history'])),
            system_message=self.config.get('System', 'system_message',
                                            fallback=self.default_config['System']['system_message']),
            debug=self.debug
        )
        
        self.glossary_init()

    def config_init(self):
        if path.isfile(self.config_path): # 如果配置文件存在，则读取
            self.config.read(self.config_path, encoding='utf-8') # 读取配置文件
        else:   
            self.config.read_dict(self.default_config)  # 如果配置文件不存在，则初始化并创建配置文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                self.config.write(f)

    def glossary_init(self):
        # 加载和管理术语表
        if path.isfile(self.glossary_path): # 如果术语表文件存在，则加载
            with open(self.glossary_path, 'r', encoding='utf-8') as f:
                glossary_texts=load(f)
        else:
            glossary_texts = VLLMTranslatorManager.default_glossary # 否则使用默认术语表初始化文件
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                dump(glossary_texts, f, ensure_ascii=False, indent=4)
        if path.isfile(self.history_path):
            with open(self.history_path, 'r', encoding='utf-8') as f:
                history_texts = load(f)
        else:
            history_texts = VLLMTranslatorManager.default_virtual_history
            with open(self.history_path, 'w', encoding='utf-8') as f:
                dump(history_texts, f, ensure_ascii=False, indent=4)
        self.translator.build_dialog_head(glossary=glossary_texts, virtual_history=history_texts)