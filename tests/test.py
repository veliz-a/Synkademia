# test_ollama.py

import ollama

response = ollama.chat(
    model="qwen2.5:7b",
    messages=[{"role": "user", "content": "di hola"}]
)

print(response)