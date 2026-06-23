from src.core.heuristicas import extraer_contexto_integral

texto_prueba = """
El trabajo debe tener mínimo 2000 palabras.
Formato obligatorio APA 7.
Debe incluir: introducción, desarrollo, conclusiones.
Se requieren al menos 5 fuentes bibliográficas.
Penalización por plagio: -100% del trabajo.
"""

resultado = extraer_contexto_integral(texto_prueba, requiere_fases=True)

print("\n===== RESULTADO =====\n")
print(resultado)