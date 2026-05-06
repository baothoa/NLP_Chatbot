import requests


class OllamaClient:
    def __init__(self, api_key=None):
        self.url = "http://localhost:11434/api/chat"
        self.model = "qwen2.5:0.5b"

    def chat(self, messages):
        try:
            response = requests.post(
                self.url,
                json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False
                },
                timeout=120
            )

            data = response.json()

            return data["message"]["content"]

        except Exception as e:
            print("Ollama error:", e)
            return "Xin lỗi, AI local đang lỗi."