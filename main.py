# 构建命令：pyinstaller -F --clean main.py
from MToolTranslator import MToolTranslator
from UnityTranslator import UnityTranslator
from sys import argv
from OllamaServer import OllamaServer

if __name__ == "__main__":
    OllamaServer.start_ollama_server() # 启动Ollama服务器
    if len(argv) > 1:
        print('检测到离线翻译文件：', argv[1],'，使用离线翻译模式。')
        mtool_translator = MToolTranslator()
        mtool_translator.run(argv)
        OllamaServer.sys_exit()

    print("请选择模式:")
    print("1. 离线模式（用于MTool导出的待翻译文件的批量翻译）")
    print("2. 在线模式（用于XUnity.AutoTranslator插件的实时翻译）")
    
    choice = input("请输入选项 (1 或 2): ").strip()
    if choice == '1':
        print("已选择离线模式。")
        mtool_translator = MToolTranslator()
        mtool_translator.run()
    elif choice == '2':
        print("已选择在线模式。")
        unity_translator_app = UnityTranslator()
        unity_translator_app.run()
    else:
        OllamaServer.sys_exit("无效输入，请输入 1 或 2")
    OllamaServer.sys_exit()
