# 构建命令：pyinstaller -F --clean MToolTranslator.py
from os import path, mkdir
from json import load, dump
from tqdm import tqdm
from re import compile
from sys import argv
import VLLMDefaultConfig
from VLLMTranslatorManager import VLLMTranslatorManager

'''
MToolTranlator 类：
通过其父类 ConfigManager 类管理配置参数
用于批量翻译由MTool导出的json格式待翻译文本
机制说明：
将文本分组，分批处理，以便可以任何时候中断翻译过程，下次继续
'''
class MToolServerTranslator():
    default_config = VLLMDefaultConfig.default_config_MToolServerTranslator

    ascii_only_pattern = compile(r'^[\x20-\x7E\u3000\n\r]+$') # 包含全角空格和换行符
    def __init__(self,debug=False):
        # 初始化配置文件路径和消息头文件路径
        self.debug = debug
        config_folder = path.join(path.dirname(path.abspath(argv[0])),'Config')
        if not path.exists(config_folder):
            mkdir(config_folder)
        config_path = path.join(config_folder,'MToolServerTranslator_config.ini')
        glossary_path = path.join(config_folder,'MToolServerTranslator_glossary.json')
        history_path = path.join(config_folder, 'MToolServerTranslator_history.json')
        self.manager = VLLMTranslatorManager(config_path, glossary_path, history_path, MToolServerTranslator.default_config, debug=self.debug)
        self.group_length = self.manager.config.getint('Extra', 'group_length', fallback=int(MToolServerTranslator.default_config['Extra']['group_length'])) # 分组长度
        self.file_path = ''

    
    def get_temp_file_path(file_path, index):
        # 生成临时文件路径
        temp_folder = path.join(path.dirname(file_path), 'Temp Files')
        if not path.exists(temp_folder):
            mkdir(temp_folder)
        result = path.join(temp_folder, path.splitext(path.basename(file_path))[0]+f'_translated_{index}.json')
        return result

    def get_derived_file_path(file_path, index):
        # 生成派生行缓存文件路径
        temp_folder = path.join(path.dirname(file_path), 'Temp Files')
        if not path.exists(temp_folder):
            mkdir(temp_folder)
        result = path.join(temp_folder, path.splitext(path.basename(file_path))[0]+f'_derived_{index}.json')
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

    def error_possible(self, original_text, translated_text):
        # 检查翻译结果是否疑似存在错误
        if len(translated_text) // 2 > len(original_text): # 翻译结果长度过长
            return True
        if (not MToolServerTranslator.ascii_only_pattern.match(original_text)) and original_text == translated_text: # 翻译结果与原文相同
            return True
        return False

    def translate_json(self):
        # 读取 JSON 文件
        with open(self.file_path, 'r', encoding='utf-8') as f:
            game_texts = load(f)
        groups = self.group_text(game_texts)
        error_texts = {}
        translated_texts = {}
        derived_texts = {}

        for index, group in enumerate(groups):
            batch_idx = index + 1
            temp_filepath = MToolServerTranslator.get_temp_file_path(self.file_path, batch_idx)
            derived_filepath = MToolServerTranslator.get_derived_file_path(self.file_path, batch_idx)

            if path.isfile(temp_filepath):
                print(f'已存在第{batch_idx}批文本的翻译文件：', temp_filepath)
                with open(temp_filepath, 'r', encoding='utf-8') as f_batch:
                    batch_translated = load(f_batch)
                    translated_texts.update(batch_translated)
                # 派生文件
                if path.isfile(derived_filepath):
                    with open(derived_filepath, 'r', encoding='utf-8') as f_drv:
                        batch_derived = load(f_drv)
                        derived_texts.update(batch_derived)
                else:
                    # 重建派生
                    rebuild_derived = {}
                    for k in group.keys():
                        if '\n' in k and k in translated_texts:
                            orig_lines = k.split('\n')
                            trans_lines = translated_texts[k].split('\n')
                            if len(orig_lines) == len(trans_lines):
                                for o_line, t_line in zip(orig_lines, trans_lines):
                                    if o_line not in derived_texts:
                                        trimmed = t_line.strip()
                                        rebuild_derived[o_line] = trimmed
                                        derived_texts[o_line] = trimmed
                    if rebuild_derived:
                        with open(derived_filepath, 'w', encoding='utf-8') as f_drv:
                            dump(rebuild_derived, f_drv, indent=4, ensure_ascii=False)
                            print(f'已重建并缓存第{batch_idx}批派生行：', derived_filepath)
                continue

            batch_translated = {}
            batch_derived = {}
            for key, text in tqdm(group.items(), desc=f'翻译第{batch_idx}批文本'):
                is_multiline = '\n' in key and not MToolServerTranslator.ascii_only_pattern.match(key)
                if is_multiline:
                    # 翻译多行块
                    translated_block = self.manager.translator.translate(key)
                    batch_translated[key] = translated_block
                    orig_lines = key.split('\n')
                    trans_lines = translated_block.split('\n')
                    if len(orig_lines) == len(trans_lines):
                        for o_line, t_line in zip(orig_lines, trans_lines):
                            o_line = o_line.strip(' \u3000') # 去掉前后空格及全角空格
                            if o_line not in derived_texts:
                                trimmed = t_line.strip(' \u3000')
                                batch_derived[o_line] = trimmed
                                derived_texts[o_line] = trimmed
                    if self.error_possible(key, translated_block):
                        error_texts[key] = translated_block
                else:
                    # 单行：优先使用派生缓存
                    if key in derived_texts:
                        batch_translated[key] = derived_texts[key]
                    else:
                        if not MToolServerTranslator.ascii_only_pattern.match(key):
                            batch_translated[key] = self.manager.translator.translate(key)
                        else:
                            batch_translated[key] = key
                        if self.error_possible(key, batch_translated[key]):
                            error_texts[key] = batch_translated[key]

            # 写入批次缓存
            with open(temp_filepath, 'w', encoding='utf-8') as f_batch:
                dump(batch_translated, f_batch, indent=4, ensure_ascii=False)
                print(f'第{batch_idx}批文本翻译完成！已保存到缓存目录下：', temp_filepath)
            if batch_derived:
                with open(derived_filepath, 'w', encoding='utf-8') as f_drv:
                    dump(batch_derived, f_drv, indent=4, ensure_ascii=False)
                    print(f'第{batch_idx}批派生行已缓存：', derived_filepath)
            translated_texts.update(batch_translated)

        if error_texts:
            print('发现疑似错误文本!')
            for key, value in tqdm(error_texts.items(), desc='正在重新翻译...'):
                retranslated = self.manager.translator.translate(key)
                translated_texts[key] = retranslated
                error_texts[key] = f'{retranslated}\n【原文：{value}】'
            error_file_path = MToolServerTranslator.get_temp_file_path(self.file_path, 'error')
            with open(error_file_path, 'w', encoding='utf-8') as f:
                dump(error_texts, f, indent=4, ensure_ascii=False)
            print('已重新翻译疑似错误文本并输出到文件：', error_file_path)

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
                print('文件路径不存在或不合法！')
                return
        self.translate_json()

if __name__ == "__main__":
    # 带参数测试: python MToolServerTranslator.py "D:\zhuang\Documents\BaiduSyncdisk\Project\LocalLLMGameTranslator\test\ManualTransFile_test.json"
    mtool = MToolServerTranslator(debug=False)
    mtool.run(argv)