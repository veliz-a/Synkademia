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
            model='gemini-1.5-flash',
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
            model='gemini-1.5-flash',
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"Error en la revisión de IA: {e}")
        return "No se pudo procesar la revisión en este momento."