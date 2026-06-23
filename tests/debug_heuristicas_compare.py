from src.llm.ai_client import chat

texto = """
El trabajo debe tener mínimo 2000 palabras.
Formato APA 7 obligatorio.
Debe incluir introducción, desarrollo y conclusiones.
Se requieren al menos 5 fuentes.
Penalización por plagio es grave.
"""

prompt = """
Devuelve JSON con EXACTAMENTE estas claves:

fases_propuestas
limite_palabras
cantidad_fuentes_minima
formato_exigido
secciones_obligatorias
penalizaciones_clave

Si no existe información, usa null o [].

TEXTO:
""" + texto

response = chat(
    messages=[{"role": "user", "content": prompt}],
    format="json",
    temperature=0.1
)

content = response.get("message", {}).get("content", "")

print("\n===== OUTPUT =====\n")
print(content)