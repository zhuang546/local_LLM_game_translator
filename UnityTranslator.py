# 异步推理版本
# qwen3更新了无推理版本后，无需再专门对qwen3做适配了
# 构建命令：pyinstaller -F --clean UnityTranslator.py

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from time import time
from Manager import Manager
from OllamaServer import OllamaServer
from os import path, mkdir
from sys import argv
import asyncio
from time import time
import uvicorn
from threading import Lock
import DefaultConfig

class UnityTranslator(Manager):
    default_config = DefaultConfig.default_config_UnityTranslator

    def __init__(self):

        config_folder = path.join(path.dirname(path.abspath(argv[0])),'Config')
        if not path.exists(config_folder):
            mkdir(config_folder)
        config_path = path.join(config_folder, 'UnityTranslator_config.ini')
        glossary_path = path.join(config_folder, 'UnityTranslator_glossary.json')
        super().__init__(config_path, glossary_path, UnityTranslator.default_config)

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
            #_from = request.query_params.get('from')
            #_to = request.query_params.get('to')

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