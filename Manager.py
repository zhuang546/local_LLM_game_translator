# pyinstaller -F ConfigManager.py
from OllamaTranslator import OllamaTranslator
from os import path
import configparser
from json import load, dump
import DefaultConfig

from OllamaServer import OllamaServer # 测试用，本身并不依赖

'''
Manager类：
MToolTranlator 和 UnityTranslator 的父类
用于管理配置文件和消息头文件，提供翻译调用
'''
class Manager:
    # 默认配置，用于初始化配置文件
    default_config = DefaultConfig.default_config
    default_glossary = DefaultConfig.default_glossary

    def __init__(self, config_path, glossary_path, init_config=default_config):
        self.config_path = config_path # 配置文件路径
        self.glossary_path = glossary_path # 术语表文件路径
        self.init_config = init_config # 初始化的配置，如果外界传递了不同的配置，则按照传递的配置初始化

        self.config = configparser.ConfigParser()
        if not path.isfile(self.config_path):
            self.config_init()

        self.config.read(self.config_path, encoding='utf-8') # 读取配置文件
        self.num_ctx = self.config.getint('Model', 'num_ctx', fallback=int(Manager.default_config['Model']['num_ctx']))  # 上下文长度限制
        self.num_predict = self.config.getint('Model', 'num_predict', fallback=int(Manager.default_config['Model']['num_predict']))  # 生成的token数量限制
        self.temperature = self.config.getfloat('Model', 'temperature', fallback=float(Manager.default_config['Model']['temperature']))  # 文本的多样性
        #self.stop = self.config.get('Model', 'stop_words', fallback=Manager.default_config['Model']['stop_words']).split(',')  # 停止符
        self.top_k = self.config.getint('Model', 'top_k', fallback=int(Manager.default_config['Model']['top_k']))  # top_k采样
        self.top_p = self.config.getfloat('Model', 'top_p', fallback=float(Manager.default_config['Model']['top_p']))  # top_p采样
        self.repeat_penalty = self.config.getfloat('Model', 'repeat_penalty', fallback=float(Manager.default_config['Model']['repeat_penalty']))  # 重复惩罚
        self.repeat_last_n = self.config.getint('Model', 'repeat_last_n', fallback=int(Manager.default_config['Model']['repeat_last_n']))  # 重复惩罚的范围

        self.history_max_length = self.config.getint('History', 'history_max_length', fallback=int(Manager.default_config['History']['history_max_length']))  # 对话历史最大长度
        self.clear_history = self.config.getboolean('History', 'clear_history', fallback=bool(Manager.default_config['History']['clear_history']))  # 是否清空对话历史
        self.system_message = self.config.get('System', 'system_message', fallback=Manager.default_config['System']['system_message'])  # 系统消息

        self.translator = OllamaTranslator(
            num_ctx=self.num_ctx,
            num_predict=self.num_predict,
            temperature=self.temperature,
            #stop=self.stop,
            top_k=self.top_k,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            repeat_last_n=self.repeat_last_n,
            history_max_length=self.history_max_length,
            clear_history=self.clear_history,
            system_message=self.system_message
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
            self.translator.build_glossary(Manager.default_glossary) # 否则使用默认术语表初始化文件
            with open(self.glossary_path, 'w', encoding='utf-8') as f:
                dump(Manager.default_glossary, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    OllamaServer.start_ollama_server()
    manager = Manager('config.ini', 'glossary.json')
    manager.translator.run()
    OllamaServer.sys_exit()