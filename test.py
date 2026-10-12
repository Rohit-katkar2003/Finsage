import requests

# OLLAMA_URL = "https://6d73-34-31-56-191.ngrok-free.app/llama-serve/v1/rerank"
# RERANKER_MODEL = "hf.co/gpustack/bge-reranker-v2-m3-GGUF:Q4_K_M"

# res = requests.post(
#     OLLAMA_URL,
#     json={
#         "model": "gpustack/bge-reranker-v2-m3-GGUF:Q4_K_M",
#         "query": "What is P/E ratio?",
#         "documents": [
#             "P/E is a valuation ratio.",
#             "The weather is sunny today.",
#             "Price-to-earnings compares share price to earnings per share.",
#         ],
#         "top_n": 3,
#     },
#     timeout=120,
# )
# print(res.status_code)
# print(res.text) 


def generate(messages:list[dict] , temperature:float=0.1,max_tokens:int=512): 
        llm_model = "hf.co/Rohit-Katkar2003/mistral-7b-100steps-gguf:Q4_K_M" 

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
        response = requests.post(
            "https://3adb-34-31-56-191.ngrok-free.app/ollama/api/generate",
            json=payload,
        )

        # response.raise_for_status()

        data = response.json()
        print(data)
        return data.get("response", "") 

if __name__ == "__main__": 
    res = generate(messages=[{"role":"system" , "content":"you are expert ai assistant"} , {"role":"user" , "content":"what is ML?"}])
    print(res)