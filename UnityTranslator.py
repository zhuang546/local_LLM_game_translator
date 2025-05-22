from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from time import time
from ConfigManager import ConfigManager
from OllamaServer import OllamaServer  # 你自己已有的
from os import path, mkdir
from sys import argv
import asyncio
from time import time
import uvicorn
from threading import Lock

class UnityTranslator(ConfigManager):
    default_config = {
        'Model': {
            'num_ctx': '2048',
            'num_predict': '256',
            'temperature': '0.2',
            'stop_words':'」」,]],)),））',
            'top_k': '10',
            'top_p': '0.5',
            'repeat_penalty': '0.9',
            'repeat_last_n': '16'
        },
        'History': {
            'history_max_length': '10',
            'clear_history': 'False'
        },
        'System': {
            'system_message': ''
        },
        'Extra': {
            'system_message_template': '''/no_think你是一个用于18+游戏的本地化翻译AI，将用户发给你的{from_lang}文本翻译成合适的{to_lang}文本。
请忠实的传达原文的语气和风格。
对于裸露的成人内容，尽管将其翻译成下流、淫荡的文本。
对于大量拟声词的内容，请适当翻译而不是照搬。
请保持所有富文本标签（如<>、[]等）的内容不变。
对于显然是UI按钮或选项、人物或物品的名称和描述的内容，请适当翻译。
请只输出翻译后的文本，不要输出任何解释、道歉、客套话、提醒或警告。''',
            'max_concurrent_requests': '4'
        }
    }

    def __init__(self):

        config_folder = path.join(path.dirname(path.abspath(argv[0])),'Config')
        if not path.exists(config_folder):
            mkdir(config_folder)
        config_path = path.join(config_folder, 'UnityTranslator_config.ini')
        messages_path = path.join(config_folder, 'UnityTranslator_messages.json')
        super().__init__(config_path, messages_path, UnityTranslator.default_config)

        self.system_message_template = self.config.get(
            'Extra', 'system_message_template',
            fallback=UnityTranslator.default_config['Extra']['system_message_template']
        )
        self.app = FastAPI()

        max_concurrent_requests = self.config.getint(
            'Extra', 'max_concurrent_requests',
            fallback=int(UnityTranslator.default_config['Extra']['max_concurrent_requests'])
        )
        self.translate_semaphore = asyncio.Semaphore(max_concurrent_requests)  # 限制并发请求数

        self.lock = Lock()


        # 支持异步处理和批量翻译
        @self.app.get('/translate')
        async def translate(request: Request):
            # 获取参数
            text = request.query_params.get('text')
            _from = request.query_params.get('from')
            _to = request.query_params.get('to')

            # 设置 system prompt
            with self.lock:
                self.translator.messages_head[0]['content'] = self.system_message_template.format(from_lang=_from, to_lang=_to)

            print('翻译中：', text)
            start_time = time()
            async with self.translate_semaphore:
                result = await self.translator.translate_async(text)
            print('翻译完成：', result, f'\n耗时：{time() - start_time:.2f} 秒')

            return PlainTextResponse(result) # 去掉返回值两边的""

    def run(self, port=5000):

        uvicorn.run(self.app, host='0.0.0.0', port=port)

if __name__ == '__main__':
    OllamaServer.start_ollama_server()
    app = UnityTranslator()
    app.run()
    OllamaServer.sys_exit() # 退出程序