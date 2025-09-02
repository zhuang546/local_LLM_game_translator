# 构建命令：pyinstaller -F --clean UnityServerTranslator.py

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from time import perf_counter
from VLLMTranslatorManager import VLLMTranslatorManager
import uvicorn
from os import path, mkdir
import VLLMDefaultConfig
from sys import argv

'''
这个类为XUnity.AutoTranslator插件提供翻译服务，
它接受来自插件的GET请求，并返回翻译结果。
'''

class UnityServerTranslator:
    default_config = VLLMDefaultConfig.default_config_MToolServerTranslator
    def __init__(self, debug=False):
        self.debug = debug
        config_folder = path.join(path.dirname(path.abspath(argv[0])), 'Config')
        if not path.exists(config_folder):
            mkdir(config_folder)
        config_path = path.join(config_folder, 'UnityServerTranslator_config.ini') # 配置文件路径
        glossary_path = path.join(config_folder, 'UnityServerTranslator_glossary.json') # 术语表文件路径
        history_path = path.join(config_folder, 'UnityServerTranslator_history.json') # 历史记录文件路径

        self.manager = VLLMTranslatorManager(config_path, glossary_path, history_path, UnityServerTranslator.default_config, debug=self.debug)
        self.app = FastAPI() # FastAPI 应用

        # 中间件：记录最早收到请求时间与整体处理耗时，帮助区分网络/解析延迟与翻译耗时
        @self.app.middleware("http")
        async def timing_middleware(request: Request, call_next):
            t_in = perf_counter()
            if self.debug:
                print(f"[UnityServerTranslator] 接收到请求，{request.url}")

            response = await call_next(request)

            t_out = perf_counter()
            if self.debug:
                print(f"[UnityServerTranslator] 请求完成，总耗时: {(t_out - t_in)*1000:.2f} ms")
            return response

        # 接收来自XUnity.AutoTranslator的请求并返回翻译结果
        # Example Request: GET http://localhost:5000/translate?from=ja&to=zh-CN&text=こんにちは
        # Example Response (only body): 你好
        # 支持异步处理
        @self.app.get('/translate')
        async def translate_custom(request: Request):
            text = request.query_params.get('text') or ""
            # _from = request.query_params.get('from')
            # _to = request.query_params.get('to')
            print('[UnityServerTranslator] 解析到翻译文本：', text)
            start_time = perf_counter()
            # 直接调用底层异步翻译，不再做中间层并发限制；上游已做批处理 / 下游已做限流
            result = await self.manager.translator.translate_async(text)
            print('[UnityServerTranslator] 翻译结果：', result)
            print(f'[UnityServerTranslator] 翻译耗时：{(perf_counter() - start_time)*1000:.2f} 毫秒')
            return PlainTextResponse(result) # 返回纯文本

    def run(self, port=5000):
        """
        启动 FastAPI 服务。

        之前两秒延迟的原因：客户端用的是 http://localhost:5000，而服务端 uvicorn 只监听 host='0.0.0.0'（纯 IPv4）。
        在 Windows 下 requests 连接 localhost 时往往先尝试 ::1 (IPv6)，连接失败/超时后再回退到 127.0.0.1 (IPv4)，会引入 ~1–2 秒的额外握手/回退时间。

        做法：直接监听 IPv6 通配地址 '::'。在 Windows 下 uvicorn 会尝试创建一个
        dual-stack socket（若系统允许）从而同时接受 ::1 与 127.0.0.1 连接，客户端
        解析 localhost -> ::1 时即可立即成功，不再回退到 IPv4。

        若机器禁用了 IPv6 导致绑定失败，则自动回退到 127.0.0.1（纯 IPv4）。
        若需要局域网其它主机访问，可改为 '0.0.0.0'（仅 IPv4）或保留 '::'。
        """
        host_ipv6 = '::'
        try:
            print(f"[UnityServerTranslator] 监听: http://localhost:{port} (底层绑定 {host_ipv6})")
            uvicorn.run(self.app, host=host_ipv6, port=port)
        except OSError as e:
            print(f"[UnityServerTranslator] 绑定 IPv6 失败: {e}\n回退到 127.0.0.1 (IPv4)")
            uvicorn.run(self.app, host='127.0.0.1', port=port)

if __name__ == '__main__':
    app = UnityServerTranslator(debug=True)
    app.run()