# 构建命令：pyinstaller -F --clean MToolTranslator.py
from OllamaTranslatorManager import Manager
from os import path, mkdir
from json import load, dump
from tqdm import tqdm
from re import compile
from sys import argv
import OllamaDefaultConfig

from OllamaServer import OllamaServer # 测试用，本身并不依赖

'''
MToolTranlator 类：
通过其父类 ConfigManager 类管理配置参数
用于批量翻译由MTool导出的json格式待翻译文本
机制说明：
将文本分组，分批处理，以便可以任何时候中断翻译过程，下次继续
'''
class MToolTranslator(Manager):
    default_config = OllamaDefaultConfig.default_config_MToolTranslator

    ascii_only_pattern = compile(r'^[\x20-\x7E]+$')
    def __init__(self):
        # 初始化配置文件路径和消息头文件路径
        config_folder = path.join(path.dirname(path.abspath(argv[0])),'Config')
        if not path.exists(config_folder):
            mkdir(config_folder)
        self.config_path = path.join(config_folder,'MToolTranslator_config.ini')
        self.messages_path = path.join(config_folder,'MToolTranslator_messages.json')

        super().__init__(self.config_path, self.messages_path, MToolTranslator.default_config) # 调用父类初始化配置，这里传入了一个不同的默认配置
        self.group_length = self.config.getint('Extra', 'group_length', fallback=int(MToolTranslator.default_config['Extra']['group_length'])) # 分组长度
        self.file_path = ''
        
    
    def get_temp_file_path(file_path, index):
        # 生成临时文件路径
        temp_folder = path.join(path.dirname(file_path), 'Temp Files')
        if not path.exists(temp_folder):
            mkdir(temp_folder)
        result = path.join(temp_folder, path.splitext(path.basename(file_path))[0]+f'_translated_{index}.json')
        return result
    
    def group_text(self, game_texts):
        # 将文本分组，分批处理
        items = list(game_texts.items())
        groups = []
        groups_num = len(items) // self.group_length  # 使用 self.group_length
        
        for i in range(groups_num):
            groups.append(dict(items[i*self.group_length:(i+1)*self.group_length]))
        if len(game_texts) % self.group_length != 0:
            groups.append(dict(items[groups_num*self.group_length:]))
        return groups
    
    def translate_json(self):
        # 读取 JSON 文件
        with open(self.file_path, 'r', encoding='utf-8') as f:
            game_texts = load(f)
        groups = self.group_text(game_texts) # 分组
        error_texts = {} # 记录错误生成的文本

        for index, group in enumerate(groups):
            # 检查是否已存在翻译文件
            temp_filepath = MToolTranslator.get_temp_file_path(self.file_path, index+1)
            if path.isfile(temp_filepath):
                print(f'已存在第{index+1}批文本的翻译文件：', temp_filepath)
                continue
            # 如果没有，则翻译当前批的文本
            translated_texts = {}
            for key, text in tqdm(group.items(), desc=f'翻译第{index+1}批文本'):
                if not MToolTranslator.ascii_only_pattern.match(key):
                    translated_texts[key] = self.translator.translate(key) 
                else:
                    translated_texts[key] = key

                if len(translated_texts[key]) // 2 > len(key): # 翻译结果长度过长，怀疑为错误文本
                    error_texts.update({key: translated_texts[key]})

            # 保存翻译结果到缓存文件
            with open(temp_filepath, 'w', encoding='utf-8') as f:
                dump(translated_texts, f, indent=4, ensure_ascii=False)
                print(f'第{index+1}批文本翻译完成！已保存到缓存目录下：', temp_filepath)

        # 从缓存文件中读取并合并所有翻译结果
        translated_texts = {}
        for index, group in enumerate(groups):
            temp_filepath = MToolTranslator.get_temp_file_path(self.file_path, index+1)
            with open(temp_filepath, 'r', encoding='utf-8') as f:
                translated_texts.update(load(f))

        # 重新翻译疑似错误文本
        if error_texts:
            for key, value in error_texts.items():
                retranslated = self.translator.translate(key)
                translated_texts[key] = retranslated
                error_texts[key] = f'{retranslated}\n【原文：{value}】'
            error_file_path = MToolTranslator.get_temp_file_path(self.file_path, 'error')
            with open(error_file_path, 'w', encoding='utf-8') as f:
                dump(error_texts, f, indent=4, ensure_ascii=False)
            print('有疑似错误文本，已重新翻译并输出到文件：', error_file_path)

        # 保存翻译结果到 JS 文件
        translated_file_path = path.splitext(self.file_path)[0]+'_translated.json'
        with open(translated_file_path, 'w', encoding='utf-8') as f:
            dump(translated_texts, f, indent=4, ensure_ascii=False)
        print('所有文本翻译完成！已保存到：', translated_file_path)        

    def run(self, argv=[]):
        # 通过run函数启动翻译流程
        if  len(argv) > 1:
            self.file_path = path.join(argv[1]) # 从命令行参数获取文件名
            print('已获取文件路径：', self.file_path)
        else:
            self.file_path = path.join(input('请输入待翻译文件的路径（可带引号）：').strip('\'" ')) # 手动输入文件路径
            if not path.isfile(self.file_path):
                OllamaServer.sys_exit('文件路径不存在或不合法！')
        self.translate_json()

if __name__ == "__main__":
    # 测试
    OllamaServer.start_ollama_server()
    mtool = MToolTranslator()
    mtool.run(argv)
    OllamaServer.sys_exit()