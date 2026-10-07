import httpx

url = "https://ae25-136-69-240-149.ngrok-free.app/laya/v1/systemone"

payload = {
    "model": "ggml-org/Laya-GGUF",
    "prompt": "Classify this query as conceptual, live_data, document_based, or multi_step.\n\nQuery: What is P/E ratio?\n\nAnswer:",
    "temperature": 0,
    "n_predict": 50,
    "stream": False
}

response = httpx.post(
    url,
    json=payload,
    timeout=120
)

print(response.status_code)
print(response.text)