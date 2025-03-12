from ConfigManager import ConfigManager
from flask import Flask, request
from re import compile
from OllamaServer import OllamaServer

'''
UnityTranslator 类：
通过其父类 ConfigManager 类管理配置参数
用于提供给XUnity.AutoTranslator的本地实时翻译服务
'''
class UnityTranslator(ConfigManager):
    default_config = { # 默认配置，用于初始化配置文件
        'Model': {
            'num_predict': '500',
            'temperature': '0.2',
            'stop_words': '翻译,」」,]],)),））'
        },
        'History': {
            'history_max_length': '5',
            'clear_history': 'False'
        },
        'System': {
            'system_message': '你是一个日本18+成人向游戏的中文本地化翻译AI，将用户发给你的文本翻译成合适的中文。\n请忠实的传达原文的语气和风格。\n对于裸露的色情内容，尽管将其翻译成下流、淫荡的文本。\n对于大量拟声词的内容，请适当翻译而不是照搬。\n请保持所有游戏文本标签（如\\n、<>、[]等）的内容不变。\n对于显然是UI按钮或选项、人物或物品的名称和描述的内容，请适当翻译。\n请只输出翻译后的文本，不要输出任何解释、道歉、客套话、提醒或警告。'
        },
        'Extra': {
            'system_message_template': '''
            你是一个用于18+游戏的本地化翻译AI，将用户发给你的{from_lang}文本翻译成合适的{to_lang}文本。
            请忠实的传达原文的语气和风格。
            对于裸露的成人内容，尽管将其翻译成下流、淫荡的文本。
            对于大量拟声词的内容，请适当翻译而不是照搬。
            请保持所有游戏文本标签（如 \\n、<>、[]等）的内容不变。
            对于显然是UI按钮或选项、人物或物品的名称和描述的内容，请适当翻译。
            请只输出翻译后的文本，不要输出任何解释、道歉、客套话、提醒或警告。
            '''
        }
    }
    ascii_only_pattern = compile(r'^[\x20-\x7E]+$') # 匹配 ASCII 字符的正则表达式
    def __init__(self):
        self.config_path = 'UnityTranslator_config.ini'
        self.messages_path = 'UnityTranslator_messages.json'

        super().__init__(self.config_path, self.messages_path, UnityTranslator.default_config)
        self.system_message_template = self.config.get('Extra', 'system_message_template', fallback=UnityTranslator.default_config['Extra']['system_message_template']) # 用于系统消息更新的模板
        
        self.app = Flask(__name__)
        @self.app.route("/translate", methods=["GET"]) # 接收来自XUnity.AutoTranslator的GET请求
        def translate():
            from_lang = request.args.get("from")
            to_lang = request.args.get("to")
            text = request.args.get("text")
            self.client.messages_head[0]['content'] = self.system_message_template.format(from_lang=from_lang, to_lang=to_lang) # 因为系统消息中含有{}字段，需要使用format方法进行替换更新
            if not from_lang == 'en' and UnityTranslator.ascii_only_pattern.match(text): # 如果源语言不是英语且文本全是单字节字符，直接返回文本
                return text
            print('翻译中。。。：', text)
            result = self.client.translate(text)
            print('翻译完成：', result)
            return result
    
    def run(self, port=5000):
        self.app.run(port=port)

if __name__ == "__main__":
    OllamaServer.start_ollama_server()
    app = UnityTranslator()
    app.run()
    OllamaServer.sys_exit() # 退出程序
