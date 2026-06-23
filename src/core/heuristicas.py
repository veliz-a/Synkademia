import json
from typing import Optional, List

from pydantic import BaseModel, Field

from src.llm.ai_client import chat

# ==========================================
# SCHEMAS
# ==========================================

class Fase(BaseModel):
    titulo: str = Field(description="Nombre formal de la iteración.")
    descripcion: str = Field(description="Descripción breve de objetivos.")


class HeuristicasMinimas(BaseModel):
    fases_propuestas: List[Fase]
    limite_palabras: Optional[int]
    cantidad_fuentes_minima: Optional[int]
    formato_exigido: Optional[str]
    secciones_obligatorias: List[str]
    penalizaciones_clave: List[str]


# ==========================================
# UTILIDADES
# ==========================================

def safe_parse_json(content: str):
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        print("JSON inválido del modelo")
        print(content[:300])
        return None


# ==========================================
# FUNCIONES PRINCIPALES
# ==========================================

def extraer_contexto_integral(texto_contexto: str, requiere_fases: bool = True) -> dict:

    prompt = f"""
Eres un auditor académico estricto.

Analiza el siguiente documento de contexto y extrae reglas de evaluación.

{'Incluye una propuesta de fases de trabajo.' if requiere_fases else 'No incluyas fases.'}

Responde SOLO con JSON válido.

Contexto:
{texto_contexto[:15000]}
"""

    try:
        response = chat(
            messages=[{"role": "user", "content": prompt}],
            format="json",
            temperature=0.1
        )

        content = response.get("message", {}).get("content", "")
        if not content:
            return {}

        data = safe_parse_json(content)
        if not data:
            return {}

        # Validación estricta
        parsed = HeuristicasMinimas(**data)
        return parsed.model_dump()

    except Exception as e:
        print(f"Error en extracción: {e}")
        return {}


def revisar_coherencia_texto(texto: str, project_heuristics: dict | None = None) -> str:

    reglas = json.dumps(project_heuristics, indent=2) if project_heuristics else "Ninguna."

    prompt = f"""
Revisa este borrador universitario.

Reglas obligatorias:
{reglas}

Indica:
1. Incumplimientos
2. Errores estructurales críticos

Texto:
{texto}
"""

    try:
        response = chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response.get("message", {}).get("content", "Sin respuesta.")

    except Exception as e:
        print(f"Error en revisión: {e}")
        return "Servicio no disponible."