# installed packages: psutil
import subprocess
import time
import psutil
from sys import exit

def pause_exit(error_message=''):
    print(error_message)
    input("按回车继续...")
    exit()

'''
OllamaServer 类：
用于启动和关闭 Ollama 服务器
'''
class OllamaServer:
    def __init__(self):
        self.ollama_process = None
        self.start_ollama_server()

    def __del__(self):
        # 在类被销毁时关闭 Ollama 服务器，这种方法不稳定，但胜在简单
        self.stop_ollama_server()

    def start_ollama_server(self):
        try:
            self.ollama_process = subprocess.Popen(
                ["ollama", "serve"],
                stdout=subprocess.DEVNULL, # 关闭控制台输出
                stderr=subprocess.DEVNULL
            )
            time.sleep(2)
            print("Ollama 服务器已启动")
        except Exception as e:
            print(f"启动 Ollama 失败: {e}")

    def stop_ollama_server(self):
        # 使用 psutil 来终止进程，这种方法具有很好的跨平台特性
        if self.ollama_process is None:
            return
        try:
            parent = psutil.Process(self.ollama_process.pid)
            children = parent.children()  # 模型运行时ollama.exe服务会启动其他ollama.exe进程

            # 先终止父进程（主 ollama.exe）
            parent.terminate()
            parent.wait(timeout=5)

            # 如果子进程还在，则终止它
            if children: # 如果有二级及以下进程，需要更复杂的遍历，但这里省去
                for child in children:
                    if child.is_running():
                        child.terminate()
                        child.wait(timeout=5)
        except Exception as e:
            print(f"终止 Ollama 服务器失败: {e}")
        else:
            print("Ollama 服务器已停止")

if __name__ == "__main__":
    # 测试代码
    managment = OllamaServer()
    pause_exit()
