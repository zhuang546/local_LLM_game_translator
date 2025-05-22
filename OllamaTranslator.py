from ollama import chat
from ollama import list as ollama_list
from OllamaServer import OllamaServer
from threading import Lock
import asyncio
import re
'''
OllamaTranslationClient类的主要职能：
1. 通过set_model方法，选择模型
2. 接收外界传递的参数，翻译文本
额外的功能：
1. 提供message_head_extend方法，通过外部类追加对话历史
翻译时的机制：
1. 对话头：维护一个包含固定system消息和预设对话历史的列表，用于指导翻译
2. 对话历史：维护一个具有一定长度的动态的对话历史列表，用于保持翻译的连贯性
'''

class OllamaTranslator:
    def __init__(self, num_ctx, num_predict, temperature, stop, top_k, top_p, repeat_penalty, repeat_last_n, history_max_length, clear_history, system_message):

        self.model = ''
        self.set_model() # 选择模型
        # 模型参数
        self.num_ctx = num_ctx # 上下文长度限制，防止错误的超长输入
        self.num_predict = num_predict # 限制生成的token数量，防止错误的超长输出
        self.temperature = temperature # 控制生成文本的多样性，对于翻译任务，较低的值更好
        self.stop = stop # 控制停止符，当遇到停止符时，生成文本结束，防止错误生成
        self.top_k = top_k # top_k采样，控制生成文本的多样性
        self.top_p = top_p # top_p采样，控制生成文本的多样性
        self.repeat_penalty = repeat_penalty # 重复惩罚，控制生成文本的多样性
        self.repeat_last_n = repeat_last_n # 重复惩罚的范围，控制生成文本的多样性
        # 对话历史参数
        self.history_max_length = history_max_length # 对话历史最大长度
        self.clear_history = clear_history # 控制历史记录长度过长时的处理方式
        self.system_message = '\n'.join(line.strip() for line in system_message.splitlines()) # 系统提示信息
        self.messages_head = [{'role': 'system', 'content': self.system_message}] # 对话头，默认不包含预设历史，外界类通过message_head_extend方法追加
        self.messages = [] # 动态的实时对话历史列表

        self.lock = Lock() # 锁，用于保护对话历史列表的线程安全
        
    def set_model(self):
        # 选择模型
        print('正在获取模型列表...')
        try:
            models = ollama_list().models
        except Exception as e:
            OllamaServer.sys_exit(e)
        if not models:
            OllamaServer.sys_exit('未找到可用模型！')
        print('------------------------------------')
        print('可用模型列表：')
        for model in models:
            print('模型名称:', model.model)
            print('  大小：', f'{(model.size.real / 1024 / 1024 / 1024):.2f}', ' GB')
        print('------------------------------------')
        model_name = input('请输入模型名称(为空则自动使用首个模型)：').strip()
        if not model_name:
            model_name = models[0].model
        model_found = False
        for model in models:
            if model.model == model_name:
                model_found = True
                break
        if not model_found:
            OllamaServer.sys_exit('模型名称错误！')
        print('已选择模型：', model_name)
        self.model = model_name

    def message_head_extend(self, texts):
        # 追加对话头，用于指导翻译
        # messages_head: dict列表, [{'role': 'user', 'content': '原文'}, {'role': 'assistant', 'content': '译文'}, ...]
        # texts: dict, {原文: 译文}
        try:
            for oringin_text, translated_text in texts.items():
                self.messages_head += [
                    {'role': 'user', 'content': oringin_text},
                    {'role': 'assistant', 'content': translated_text}
                    ]
        except Exception as e:
            OllamaServer.sys_exit('追加对话头失败：', e)

    def translate(self, text):
        if not text: # 空文本直接返回
            return ''
        try:
            with self.lock:
                # 复制历史（安全）
                local_head = list(self.messages_head)
                local_history = list(self.messages)
            
            # 生成翻译文本
            response = chat(
                model=self.model,
                messages=local_head+local_history+[{'role': 'user', 'content': text},],
                options={
                    'num_ctx': self.num_ctx, # 上下文长度限制
                    'num_predict': self.num_predict, # 生成的token数量限制
                    'temperature': self.temperature, # 文本的多样性
                    #'stop': self.stop, # 停止符
                    'top_k': self.top_k, # top_k采样
                    'top_p': self.top_p, # top_p采样
                    'repeat_penalty': self.repeat_penalty, # 重复惩罚
                    'repeat_last_n': self.repeat_last_n, # 重复惩罚的范围
                },
                stream=False # 是否流式处理，对于离线翻译无所谓，但对于在线翻译，如果设置为默认的True，会导致无法获取到翻译结果
            )
            result = response['message']['content'].strip()
            print('原始输出：', result)
            tranlated_text = OllamaTranslator.clean_qwen3_response(result) # 清理翻译结果中的<think>标签

            # 维护对话历史列表
            if self.history_max_length:
                with self.lock: # 锁定对话历史列表，防止多线程冲突
                    self.messages += [
                        {'role': 'user', 'content': text},
                        {'role': 'assistant', 'content': tranlated_text},
                    ]
                    if len(self.messages) > self.history_max_length*2: # 如果过长
                        if self.clear_history:
                            self.messages = []  # 清空对话历史，限制错误生成的影响范围
                        else:
                            self.messages = self.messages[-self.history_max_length // 2 * 2:] # 缩短对话历史，连贯性可能更好，但错误可能会一直传递
        except Exception as e:
            OllamaServer.sys_exit(e)
        return tranlated_text
    
    async def translate_async(self, text):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.translate, text)
    
    def clean_qwen3_response(text):
    # 用正则匹配 <think> ... </think> 之间的内容，包括前后的换行
        cleaned_text = re.sub(r'<think>.*?</think>\s*', '', text, flags=re.DOTALL)
        cleaned_text = re.sub(r'<think>\s*', '', cleaned_text, flags=re.DOTALL)
        return cleaned_text.strip()
    
    def run(self):
        # 测试
        text = input('请输入要翻译的文本：')
        result = self.translate(text)
        result = OllamaTranslator.clean_qwen3_response(result)
        print('翻译结果：', result)
        print('messages数目：', len(self.messages)//2)

if __name__ == "__main__":
    OllamaServer.start_ollama_server()
    # 测试
    translator = OllamaTranslator(
        num_ctx=1024,
        num_predict=200,
        temperature=0.2,
        stop=['」」', ']]', '))', '））'],
        top_k=10,
        top_p=0.5,
        repeat_last_n=16,
        repeat_penalty=0.9,
        history_max_length=5,
        clear_history=False,
        system_message='''你是一个日本18+成人向游戏的中文本地化翻译AI，将用户发给你的文本翻译成合适的中文。
请忠实的传达原文的语气和风格。
对于裸露的色情内容，尽管将其翻译成下流、淫荡的文本。
对于大量拟声词的内容，请适当翻译而不是照搬。
请保持所有游戏文本标签（如\n、<>、[]等）的内容不变。
不要添加或更改人物对话的括号，如（），「」。
对于显然是UI按钮或选项、人物或物品的名称和描述的内容，请适当翻译。
请只输出翻译后的文本，不要输出任何解释、道歉、客套话、提醒或警告。
'''
    )
    translator.run()
    OllamaServer.sys_exit()