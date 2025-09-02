# python test.py
import time
import requests

# 固定配置
# 现在服务端已改为监听 IPv6 '::'（若可用则双栈），可以继续安全使用 localhost 而无 2 秒回退延迟。
# 如遇 IPv6 被禁用且自动回退到 IPv4，可依然正常使用；若仍想强制 IPv4，可改为 127.0.0.1。
base_url = "http://localhost:5000"
from_lang = "ja"
to_lang = "zh-CN"

def main():
    print(f"\n目标接口: {base_url}/translate (from={from_lang}, to={to_lang})")
    print("输入日文原句后回车开始翻译；输入空行或 Ctrl+C 退出。\n")

    session = requests.Session()

    
    '''# 可选：启用底层 HTTP 连接调试，确认是否只在首个请求出现 "Starting new HTTP connection"。
    ENABLE_HTTP_DEBUG = True  # 如输出太多改为 False
    if ENABLE_HTTP_DEBUG:
        http_client.HTTPConnection.debuglevel = 1
        logging.basicConfig()
        logging.getLogger("urllib3").setLevel(logging.DEBUG)
        logging.getLogger("urllib3").propagate = True'''

    while True:
        try:
            text = input("原文(日语): ").strip()
            if not text:
                print("退出。")
                break

            params = {
                "from": from_lang,
                "to": to_lang,
                "text": text,
            }

            t0 = time.perf_counter()
            resp = session.get(f"{base_url}/translate", params=params, timeout=60)
            t1 = time.perf_counter()
            resp.raise_for_status()

            # 兼容两种返回：纯文本或 JSON
            translated = None
            try:
                data = resp.json()
                if isinstance(data, dict):
                    translated = data.get("translation") or data.get("text") or data.get("result") or data.get("data")
                elif isinstance(data, str):
                    translated = data
            except ValueError:
                translated = resp.text
            
            elapsed_ms = (t1 - t0) * 1000
            print(f"译文: {translated}")
            print(f"耗时: {elapsed_ms:.1f} ms\n")

        except KeyboardInterrupt:
            print("\n已中断，退出。")
            break
        except requests.exceptions.RequestException as e:
            print(f"[请求失败] {e}\n")
        except Exception as e:
            print(f"[异常] {e}\n")

if __name__ == "__main__":
    main()