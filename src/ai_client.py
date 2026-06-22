import os
import json
from urllib import response
from google import genai
from google.genai import types
from dotenv import load_dotenv # Carga la API KEY

# Cargar variables de entorno
load_dotenv()

# Inicializar el cliente moderno (asume que GEMINI_API_KEY está en el entorno)
client = genai.Client()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")


def _es_error_de_cuota(exception: Exception) -> bool:
    mensaje = str(exception)
    return "RESOURCE_EXHAUSTED" in mensaje or "429" in mensaje or "quota" in mensaje.lower()


def _fallback_estructura(tipo_trabajo, curso, integrantes):
    integrantes_validos = [nombre for nombre in integrantes if nombre]
    if not integrantes_validos:
        integrantes_validos = ["Sin asignar"]

    secciones = [
        "Introducción",
        "Marco Teórico",
        "Metodología",
        "Desarrollo",
        "Resultados",
        "Conclusiones",
    ]

    if tipo_trabajo:
        secciones[0] = f"Introducción al {tipo_trabajo.lower()}"
    if curso:
        secciones[1] = f"Contexto de {curso}"

    estructura = []
    for index, titulo in enumerate(secciones[: max(4, min(len(secciones), len(integrantes_validos) + 2))]):
        estructura.append(
            {
                "titulo": titulo,
                "asignado_a": integrantes_validos[index % len(integrantes_validos)],
            }
        )

    return estructura


def _fallback_revisar_texto(texto):
    return (
        "No se pudo usar Gemini por cuota agotada. "
        "Sugerencias rápidas:\n"
        "1. Verifica que cada idea tenga una oración principal clara.\n"
        "2. Reemplaza repeticiones y verbos vagos por lenguaje más preciso.\n"
        "3. Revisa citas, referencias y consistencia con normas APA en todo el texto."
    )

def generar_estructura_proyecto(tipo_trabajo, curso, integrantes):
    """
    Llama al LLM para generar una estructura de trabajo desglosada y asignar responsables.
    """
    prompt = f"""
    Actúa como un coordinador académico experto universitario. 
    Genera una estructura de secciones lógica para un trabajo de tipo '{tipo_trabajo}' del curso '{curso}'.
    El equipo tiene los siguientes integrantes disponibles para asignar: {', '.join(integrantes)}.
    
    Reglas estrictas:
    1. Divide el trabajo en al menos 4 secciones fundamentales.
    2. Asigna equitativamente a los integrantes en la clave "asignado_a".
    3. Devuelve ÚNICAMENTE un arreglo JSON válido, sin texto adicional.
    [
        {{"titulo": "Introducción", "asignado_a": "Nombre1"}},
        {{"titulo": "Marco Teórico", "asignado_a": "Nombre2"}}
    ]
    """
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            )
        )
        if not response.text:
            return []
    
        return json.loads(response.text)
    
    except Exception as e:
        print(f"Error en la llamada a la API de IA: {e}")
        if _es_error_de_cuota(e):
            return _fallback_estructura(tipo_trabajo, curso, integrantes)
        return []

def revisar_coherencia_texto(texto):
    """
    Simula la funcionalidad del asistente IA de coherencia para la edición colaborativa.
    """
    prompt = f"""
    Revisa el siguiente texto académico y detecta inconsistencias de estilo, tono o normas APA.
    Proporciona 3 sugerencias breves y directas de mejora.
    
    Texto:
    {texto}
    """
    
    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error en la revisión de IA: {e}")
        if _es_error_de_cuota(e):
            return _fallback_revisar_texto(texto)
        return "No se pudo procesar la revisión en este momento."