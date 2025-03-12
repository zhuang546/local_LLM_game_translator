# 构建命令：pyinstaller -F --clean OllamaServer.py
import subprocess
import time
import psutil
from sys import exit
from os import getpid

'''
OllamaServer 类：
用于启动和关闭 Ollama 服务器
'''
class OllamaServer:
    @staticmethod
    def start_ollama_server():
        try:
            server_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL, # 关闭控制台输出
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            print("Ollama 服务器已启动，pid：",server_process.pid)
        except Exception as e:
            print(f"启动 Ollama 失败: {e}")

    @staticmethod
    def stop_ollama_server():
        # 使用 psutil 来终止进程，这种方法具有很好的跨平台特性
        try:
            parent = psutil.Process(getpid())
            # 递归终止子进程
            for child in parent.children(recursive=True):
                child.terminate()
                child.wait(timeout=5)
                print("Ollama 服务器已停止，pid：", child.pid)
        except Exception as e:
            print(f"终止 Ollama 服务器失败: {e}")

    @staticmethod
    def sys_exit(error_message=''):
        print(error_message)
        OllamaServer.stop_ollama_server()
        input("按回车退出...")
        exit()

if __name__ == "__main__":
    # 测试
    OllamaServer.start_ollama_server()
    OllamaServer.sys_exit()
