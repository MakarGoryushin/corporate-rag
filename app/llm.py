import requests
from app.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL, LLM_TIMEOUT

class OpenAICompatibleLLM:
    def __init__(self, base_url=LLM_BASE_URL, api_key=LLM_API_KEY, model=LLM_MODEL):
        self.base_url, self.api_key, self.model = base_url.rstrip("/"), api_key, model

    @property
    def configured(self): return bool(self.base_url and self.model)

    def generate(self, prompt: str) -> str:
        if not self.configured:
            raise RuntimeError("LLM не настроена. Заполните LLM_BASE_URL и LLM_MODEL в .env")
        response = requests.post(f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {self.api_key}"} if self.api_key else {},
             json={
                 "model": self.model,
                 "messages": [
                     {
                         "role": "user",
                         "content": prompt,
                     }
                 ],
                 "temperature": 0.1,
                 "max_tokens": 1024,
                 "stream": False,
             }, timeout=LLM_TIMEOUT)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
