import requests
import time

def test_translation_delay(text="こんにちは", from_lang="ja", to_lang="zh-CN", port=5000):
    url = f"http://127.0.0.1:{port}/translate"
    params = {
        "from": from_lang,
        "to": to_lang,
        "text": text
    }

    print(f"发送翻译请求: {text}")
    start_time = time.time()
    response = requests.get(url, params=params)
    end_time = time.time()

    print(f"返回结果: {response.text}")
    print(f"耗时: {end_time - start_time:.4f} 秒")

if __name__ == "__main__":
    test_translation_delay()