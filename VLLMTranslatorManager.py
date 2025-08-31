# pyinstaller -F ConfigManager.py
from VLLMTranslator import VLLMTranslator
from os import path
import configparser
from json import load, dump
import VLLMDefaultConfig

#from OllamaServer import OllamaServer # 测试用，本身并不依赖

class VLLMTranslatorManager:
    # 默认配置，用于初始化配置文件
    default_config = VLLMDefaultConfig.default_config
    default_glossary = VLLMDefaultConfig.default_glossary

    def __init__(self, config_path, glossary_path, init_config=default_config):
        self.config_path = config_path # 配置文件路径
        self.glossary_path = glossary_path # 术语表文件路径
        self.init_config = init_config # 初始化的配置，如果外界传递了不同的配置，则按照传递的配置初始化

        self.config = configparser.ConfigParser()
        if not path.isfile(self.config_path):
            self.config_init()

        self.config.read(self.config_path, encoding='utf-8') # 读取配置文件

        base_url = self.config.get('Model', 'base_url', fallback=VLLMTranslatorManager.default_config['Model']['base_url'])
        model = self.config.get('Model', 'model', fallback=VLLMTranslatorManager.default_config['Model']['model'])

        max_tokens = self.config.getint('Model', 'max_tokens', fallback=int(VLLMTranslatorManager.default_config['Model']['max_tokens']))  # 生成的token数量限制
        temperature = self.config.getfloat('Model', 'temperature', fallback=float(VLLMTranslatorManager.default_config['Model']['temperature']))  # 文本的多样性
        top_p = self.config.getfloat('Model', 'top_p', fallback=float(VLLMTranslatorManager.default_config['Model']['top_p']))  # top_p采样

        history_max_length = self.config.getint('History', 'history_max_length', fallback=int(VLLMTranslatorManager.default_config['History']['history_max_length']))  # 对话历史最大长度
        clear_history = self.config.getboolean('History', 'clear_history', fallback=bool(VLLMTranslatorManager.default_config['History']['clear_history']))  # 是否清空对话历史
        system_message = self.config.get('System', 'system_message', fallback=VLLMTranslatorManager.default_config['System']['system_message'])  # 系统消息

        self.translator = VLLMTranslator(
            base_url=base_url, model=model,
            max_tokens=max_tokens, temperature=temperature, top_p=top_p,
            history_max_length=history_max_length, clear_history=clear_history,
            system_message=system_message
        )
        
        self.glossary_init()

    def config_init(self):
        # 初始化配置文件
        self.config['Model'] = self.init_config['Model']
        self.config['History'] = self.init_config['History']
        self.config['System'] = self.init_config['System']
        self.config['Extra'] = self.init_config['Extra'] # 一般把额外的参数放在 Extra 中

        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def glossary_init(self):
        # 加载和管理术语表
        if path.isfile(self.glossary_path): # 如果术语表文件存在，则加载
            with open(self.glossary_path, 'r', encoding='utf-8') as f:
                self.translator.build_glossary(load(f))
        else:
            self.translator.build_glossary(VLLMTranslatorManager.default_glossary) # 否则使用默认术语表初始化文件
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                dump(VLLMTranslatorManager.default_glossary, f, ensure_ascii=False, indent=4)

'''if __name__ == "__main__":
    OllamaServer.start_ollama_server()
    manager = Manager('config.ini', 'glossary.json')
    manager.translator.run()
    OllamaServer.sys_exit()'''