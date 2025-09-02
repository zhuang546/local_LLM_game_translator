# VLLMTranslator.py
import requests
from threading import Lock
import asyncio
from time import perf_counter

class VLLMTranslator:
    def __init__(self, base_url, model, max_tokens, temperature, top_p, history_max_length, clear_history, system_message, debug=False):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.max_tokens = max_tokens  # 生成的token数量限制
        self.temperature = temperature  # 文本的多样性
        self.top_p = top_p  # top_p采样
        self.history_max_length = history_max_length  # 对话历史最大长度
        self.clear_history = clear_history  # 是否清空对话历史
        self.system_message = "\n".join(line.strip() for line in system_message.splitlines())  # 系统消息
        self.dialog_head = [{"role":"system","content": self.system_message}]
        self.dialog_history = []
        self.lock = Lock()
        self.debug = debug

    def build_dialog_head(self, glossary: dict[str, str], virtual_history: list[dict[str, str]]):
        # 构建对话头，包含系统消息、术语表和虚拟历史记录
        glossary_texts = ""
        for src, tgt in glossary.items():
            glossary_texts += f"{src}={tgt}\n"
        
        self.dialog_head += [{"role":"system","content":"以下是一些术语表，用于指导翻译，请在翻译时参考：\n"+glossary_texts}] + virtual_history

    def _post_chat(self, text: str) -> str:
        with self.lock:
            local_history = list(self.dialog_history)

        payload = {
            "model": self.model,
            "messages": self.dialog_head + local_history + [{"role":"user","content": text}],
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "stream": False
        }
        t0 = perf_counter()
        r = requests.post(f"{self.base_url}/v1/chat/completions", json=payload, timeout=60)
        r.raise_for_status()
        data = r.json()
        t1 = perf_counter()
        if self.debug:
            print(f"[VLLMTranslator] 翻译服务耗时: {(t1 - t0)*1000:.2f} 毫秒")
        return data["choices"][0]["message"]["content"].strip()

    def translate(self, text: str) -> str:
        if not text:
            return ""
        
        result = self._post_chat(text)

        # 维护历史
        if self.history_max_length:
            with self.lock:
                self.dialog_history += [{"role":"user","content": text},
                                        {"role":"assistant","content": result}]
                if len(self.dialog_history) > self.history_max_length*2:
                    if self.clear_history:
                        self.dialog_history = []
                    else:
                        self.dialog_history = self.dialog_history[-self.history_max_length // 2 * 2:]
        return result

    async def translate_async(self, text: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.translate, text)
