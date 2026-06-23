from src.llm.ai_client import chat

texto_prueba = """
El trabajo debe tener mínimo 2000 palabras.
Formato APA 7 obligatorio.
Debe incluir introducción, desarrollo y conclusiones.
Se requieren al menos 5 fuentes.
Penalización por plagio es grave.
"""

prompt = f"""
Eres un auditor académico.

Devuelve SOLO JSON válido.

Extrae reglas del siguiente texto:

{texto_prueba}
"""

response = chat(
    messages=[{"role": "user", "content": prompt}],
    format="json",
    temperature=0.1
)

print("\n===== RAW RESPONSE =====\n")
print(response)

print("\n===== CONTENT =====\n")
print(response.get("message", {}).get("content", ""))