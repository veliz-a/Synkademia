# /src/llm/client.py
import ollama
from src.config import OLLAMA_MODEL, OLLAMA_TEMPERATURE

def chat(messages, temperature=None, format=None):
    return ollama.chat(
        model=OLLAMA_MODEL,
        messages=messages,
        format=format,
        options={
            "temperature": temperature if temperature is not None else OLLAMA_TEMPERATURE
        }
    )