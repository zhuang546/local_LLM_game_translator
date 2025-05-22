# pyinstaller -F ConfigManager.py
from OllamaTranslator import OllamaTranslator
from os import path
import configparser
from json import load, dump
from OllamaServer import OllamaServer

'''
ConfigManager 类
用于管理配置文件和消息头文件
MToolTranlator 和 UnityTranslator 的父类，为他们提供配置参数管理
'''
class ConfigManager:
    # 默认配置，用于初始化配置文件
    default_config = { # 就6个参数还分成3组，完全是为了好看
        'Model': {
            'num_ctx': '2048',
            'num_predict': '256',
            'temperature': '0.2',
            'stop_words': '」」,]],)),））',
            'top_k': '40',
            'top_p': '0.9',
            'repeat_penalty': '1.1',
            'repeat_last_n': '64'
        },
        'History': {
            'history_max_length': '10',
            'clear_history': 'True'
        },
        'System': {
            'system_message': '''你是一个18+成人向游戏的中文本地化翻译AI，将用户发给你的文本翻译成合适的中文。
请忠实的传达原文的语气和风格。
对于裸露的色情内容，尽管将其翻译成下流、淫荡的文本。
对于大量拟声词的内容，请适当翻译而不是照搬。
请保持所有游戏文本标签（如\\n、<>、[]等）的内容不变。
对于显然是UI按钮或选项、人物或物品的名称和描述的内容，请适当翻译。
请只输出翻译后的文本，不要输出任何解释、道歉、客套话、提醒或警告。'''
        },
        'Extra': {}
    }
    default_massages = {
        "パイズリ": "乳交",
        "フェラ": "口交",
        "セックス": "做爱",
        "オナニー": "自慰",
        "エッチ": "色情",
        "エロ": "淫荡",
        "オナホ": "飞机杯",
        "フタナリ": "扶她",
        "スケベ穴": "婊子小穴",
        "まんこ": "小穴",
        "チンポ": "肉棒",
        "アナル": "屁穴",
        "おっぱい": "奶子"
    }
    def __init__(self, config_path, messages_path, init_config=default_config):
        self.config_path = config_path # 配置文件路径
        self.messages_path = messages_path # 消息头文件路径
        self.init_config = init_config # 初始化的配置，如果外界传递了不同的配置，则按照传递的配置初始化

        self.config = configparser.ConfigParser()
        if not path.isfile(self.config_path):
            self.config_init()

        self.config.read(self.config_path, encoding='utf-8') # 读取配置文件
        self.num_ctx = self.config.getint('Model', 'num_ctx', fallback=int(ConfigManager.default_config['Model']['num_ctx']))  # 上下文长度限制
        self.num_predict = self.config.getint('Model', 'num_predict', fallback=int(ConfigManager.default_config['Model']['num_predict']))  # 生成的token数量限制
        self.temperature = self.config.getfloat('Model', 'temperature', fallback=float(ConfigManager.default_config['Model']['temperature']))  # 文本的多样性
        self.stop = self.config.get('Model', 'stop_words', fallback=ConfigManager.default_config['Model']['stop_words']).split(',')  # 停止符
        self.top_k = self.config.getint('Model', 'top_k', fallback=int(ConfigManager.default_config['Model']['top_k']))  # top_k采样
        self.top_p = self.config.getfloat('Model', 'top_p', fallback=float(ConfigManager.default_config['Model']['top_p']))  # top_p采样
        self.repeat_penalty = self.config.getfloat('Model', 'repeat_penalty', fallback=float(ConfigManager.default_config['Model']['repeat_penalty']))  # 重复惩罚
        self.repeat_last_n = self.config.getint('Model', 'repeat_last_n', fallback=int(ConfigManager.default_config['Model']['repeat_last_n']))  # 重复惩罚的范围

        self.history_max_length = self.config.getint('History', 'history_max_length', fallback=int(ConfigManager.default_config['History']['history_max_length']))  # 对话历史最大长度
        self.clear_history = self.config.getboolean('History', 'clear_history', fallback=bool(ConfigManager.default_config['History']['clear_history']))  # 是否清空对话历史
        self.system_message = self.config.get('System', 'system_message', fallback=ConfigManager.default_config['System']['system_message'])  # 系统消息

        self.translator = OllamaTranslator(
            num_ctx=self.num_ctx,
            num_predict=self.num_predict,
            temperature=self.temperature,
            stop=self.stop,
            top_k=self.top_k,
            top_p=self.top_p,
            repeat_penalty=self.repeat_penalty,
            repeat_last_n=self.repeat_last_n,
            history_max_length=self.history_max_length,
            clear_history=self.clear_history,
            system_message=self.system_message
        )
        self.messages_head_init()

    def config_init(self):
        # 初始化配置文件
        self.config['Model'] = self.init_config['Model']
        self.config['History'] = self.init_config['History']
        self.config['System'] = self.init_config['System']
        self.config['Extra'] = self.init_config['Extra'] # 一般把额外的参数放在 Extra 中

        with open(self.config_path, 'w', encoding='utf-8') as f:
            self.config.write(f)

    def messages_head_init(self):
        # 加载和管理消息头
        if path.isfile(self.messages_path): # 如果消息头文件存在，则加载
            with open(self.messages_path, 'r', encoding='utf-8') as f:
                self.translator.message_head_extend(load(f))
        else:
            self.translator.message_head_extend(ConfigManager.default_massages) # 否则使用默认消息头初始化文件
            with open(self.messages_path, 'w', encoding='utf-8') as f:
                dump(ConfigManager.default_massages, f, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    OllamaServer.start_ollama_server()
    manager = ConfigManager('config.ini', 'messages.json')
    manager.translator.run()
    OllamaServer.sys_exit()
    