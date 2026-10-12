from ..config import get_settings 
import httpx 
from typing import List

class LLMClient: 
    def __init__(self): 
        self.settings = get_settings() 
        self.ngrok_url = self.settings.MODEL_URL 
        self.LLM_model_url = f"{self.ngrok_url}/ollama/api/generate" # this only for text generation model 
        self.embedding_model_url = f"{self.ngrok_url}/ollama/api/embed" 
        self.classification_url = f"{self.ngrok_url}/laya/v1/chat/completions" 
        self.reranker_model_url = f"{self.ngrok_url}/ollama/api/rerank"
        self.client =httpx.Client(
            timeout=120.0
        )

    def chat(self, messages: list[dict], temperature: float = 0.1,
        max_tokens: int = 512) -> str:
        payload = {
            "model": self.settings.LLM_MODEL,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": False,
        }
        r = self.client.post(self.classification_url, json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        # OpenAI-style response
        return data["choices"][0]["message"]["content"]

    
    def generate(self , messages:list[dict] , temperature:float=0.1,max_tokens:int=512): 
        llm_model = self.settings.LLM_MODEL 

        prompt = "\n\n".join(
            f"{message['role']}: {message['content']}"
            for message in messages
        )
        payload = {
            "model": llm_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature , 
                "max_tokens":max_tokens
            },
        }
        # print(f"LLM MODEL : {llm_model}")
        # print(f"LLM MODEL URL : {self.LLM_model_url}")
        response = self.client.post(
            self.LLM_model_url,
            json=payload,
        )

        # response.raise_for_status()

        data = response.json()

        return data.get("response", "") 
    

    def classify(self, messages: list[dict]) -> dict:

        payload = {
            "model": self.settings.CLASSIFICATION_MODEL,
            "messages": messages,
            "temperature": 0,
            "max_tokens": 200,
            "stream": False,
        }

        response = self.client.post(
            self.classification_url,
            json=payload,
            timeout=120,
        )

        print("STATUS:", response.status_code)
        print("RESPONSE:", response.text)

        response.raise_for_status()

        return response.json() 


    def embed(self ,text:str ):
        EMBEDDING_MODEL = self.settings.EMBEDDING_MODEL
        payload = {
        "model": EMBEDDING_MODEL,
        "input": text
        }

        response = self.client.post(self.embedding_model_url, json=payload)

        response.raise_for_status()

        data = response.json()
 
        return data
    


