import json
import re
from typing import Any, Optional, List, Dict
from pydantic import BaseModel, Field
from src.llm.ai_client import chat


# ==========================================
# SCHEMAS
# ==========================================

class Fase(BaseModel):
    titulo: str
    descripcion: Optional[str] = None
    semana: Optional[int] = None
    peso: Optional[int] = None
    tipo: Optional[str] = None          # Grupal | Individual | Mixto


class HeuristicasMinimas(BaseModel):
    # entregas
    fases_propuestas: List[Fase] = []

    # extensión del documento
    limite_palabras: Optional[int] = None
    limite_paginas: Optional[int] = None

    # fuentes
    cantidad_fuentes_minima: Optional[int] = None
    formato_citas: Optional[str] = None
    antiguedad_fuentes_max_anos: Optional[int] = None

    # entrega
    formato_exigido: Optional[str] = None
    plataforma_entrega: Optional[str] = None

    # estructura
    secciones_obligatorias: List[str] = []

    # grupo
    cantidad_integrantes_min: Optional[int] = None
    cantidad_integrantes_max: Optional[int] = None
    tipo_trabajo: Optional[str] = None

    # antiplagios
    herramienta_antiplagios: Optional[str] = None
    porcentaje_similitud_max: Optional[int] = None

    # nota y recuperación
    nota_minima_aprobatoria: Optional[int] = None
    permite_recuperacion: Optional[bool] = None

    # presentación oral
    requiere_defensa_oral: Optional[bool] = None
    duracion_presentacion_min: Optional[int] = None
    duracion_presentacion_max: Optional[int] = None

    # evaluación
    criterios_evaluacion: List[str] = []
    criterios_tipo: Dict[str, str] = {}     # nombre → Grupal/Individual
    pesos_evaluacion: Dict[str, int] = {}

    # reglas
    penalizaciones_clave: List[str] = []
    reglas_adicionales: List[str] = []


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


def _find_any(obj: Any, *keys) -> Any:
    """Busca recursivamente cualquiera de las claves en un objeto anidado."""
    if isinstance(obj, dict):
        for key in keys:
            if key in obj:
                return obj[key]
        for v in obj.values():
            result = _find_any(v, *keys)
            if result is not None:
                return result
    elif isinstance(obj, list):
        for item in obj:
            result = _find_any(item, *keys)
            if result is not None:
                return result
    return None


def _all_text(obj: Any) -> List[str]:
    """Extrae todos los strings del objeto anidado."""
    result = []
    if isinstance(obj, str):
        result.append(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            result.extend(_all_text(v))
    elif isinstance(obj, list):
        for item in obj:
            result.extend(_all_text(item))
    return result


def _mine_text(texts: List[str]) -> dict:
    """Minería de patrones sobre el corpus de strings del RAW."""
    corpus = " ".join(texts).lower()
    found = {}

    # integrantes
    m = (re.search(r"grupo[s]? de (\d+)\s+(?:estudiante|alumno|integrante|persona|miembro)", corpus)
         or re.search(r"(\d+)\s+(?:estudiante|alumno|integrante|persona|miembro)[s]? por grupo", corpus)
         or re.search(r"equipo[s]? de (\d+)", corpus))
    if m:
        found["cantidad_integrantes_max"] = int(m.group(1))

    m = re.search(r"m[ií]nimo\s+(\d+)\s+(?:integrante|miembro|estudiante)", corpus)
    if m:
        found["cantidad_integrantes_min"] = int(m.group(1))

    # tipo de trabajo
    if re.search(r"\bindividual\b", corpus) and re.search(r"\bgrupal\b", corpus):
        found["tipo_trabajo"] = "mixto"
    elif re.search(r"\bgrupal\b", corpus):
        found["tipo_trabajo"] = "grupal"
    elif re.search(r"\bindividual\b", corpus):
        found["tipo_trabajo"] = "individual"

    # páginas
    m = re.search(r"(\d+)\s*p[aá]gina[s]?", corpus)
    if m:
        found["limite_paginas"] = int(m.group(1))

    # palabras (fallback desde texto)
    m = re.search(r"(\d+)\s*palabra[s]?", corpus)
    if m:
        found["limite_palabras_texto"] = int(m.group(1))

    # antigüedad de fuentes
    m = re.search(r"(\d+)\s*a[ñn]o[s]?\s*(?:de antiguedad|de antig|m[aá]ximo|como m[aá]ximo)", corpus)
    if not m:
        m = re.search(r"(?:publicad|fuente)[^\d]*(\d{4})\s*en adelante", corpus)
    if m:
        found["antiguedad_fuentes_max_anos"] = int(m.group(1))

    # fuentes mínimas
    m = re.search(r"(\d+)\s*(?:fuente[s]?|referencia[s]?|bibliograf)", corpus)
    if m:
        found["cantidad_fuentes_minima"] = int(m.group(1))

    # formato citas
    m = re.search(r"\b(apa\s*\d*|ieee|vancouver|chicago|mla|icontec)\b", corpus)
    if m:
        found["formato_citas"] = m.group(1).strip().upper().replace(" ", "")

    # formato archivo
    m = re.search(r"\b(pdf|word|docx?|pptx?|excel)\b", corpus)
    if m:
        found["formato_exigido"] = m.group(1).upper()

    # plataforma entrega
    for plat in ["canvas", "blackboard", "moodle", "classroom", "teams", "drive"]:
        if plat in corpus:
            found["plataforma_entrega"] = plat.capitalize()
            break

    # antiplagios
    for tool in ["turnitin", "ithenticate", "urkund", "copyleaks"]:
        if tool in corpus:
            found["herramienta_antiplagios"] = tool.capitalize()
            break

    m = re.search(r"similitud[^\d]*(\d+)\s*%|(\d+)\s*%[^\d]*similitud", corpus)
    if m:
        found["porcentaje_similitud_max"] = int(m.group(1) or m.group(2))

    # nota mínima
    m = re.search(r"nota\s*m[ií]nima[^\d]*(\d+)|m[ií]nimo[^\d]*(\d+)\s*para\s*aprobar", corpus)
    if m:
        found["nota_minima_aprobatoria"] = int(m.group(1) or m.group(2))

    # recuperación
    if re.search(r"recuperaci[oó]n|segunda\s+oportunidad", corpus):
        found["permite_recuperacion"] = True

    # defensa oral
    if re.search(r"defensa\s+oral|sustentaci[oó]n|exposici[oó]n\s+oral", corpus):
        found["requiere_defensa_oral"] = True

    # duración presentación
    m = re.search(r"(\d+)\s*(?:a|-)\s*(\d+)\s*minuto[s]?", corpus)
    if m:
        found["duracion_presentacion_min"] = int(m.group(1))
        found["duracion_presentacion_max"] = int(m.group(2))
    else:
        m = re.search(r"(\d+)\s*minuto[s]?", corpus)
        if m:
            found["duracion_presentacion_max"] = int(m.group(1))

    return found


def _extraer_reglas_adicionales(obj: Any, skip_keys: set) -> List[str]:
    """Extrae textos de listas de reglas/requisitos que no son fases ni criterios."""
    reglas = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in skip_keys:
                continue
            if isinstance(v, list):
                for item in v:
                    if isinstance(item, dict):
                        texto = item.get("requisito") or item.get("descripcion") or item.get("regla") or item.get("nombre")
                        if texto and isinstance(texto, str) and len(texto) > 10:
                            reglas.append(texto)
                    elif isinstance(item, str) and len(item) > 10:
                        reglas.append(item)
            if isinstance(v, (dict, list)):
                reglas.extend(_extraer_reglas_adicionales(v, skip_keys))
    elif isinstance(obj, list):
        for item in obj:
            reglas.extend(_extraer_reglas_adicionales(item, skip_keys))
    return reglas


def normalize_heuristicas(data: dict) -> dict:
    """
    Convierte outputs variables del modelo a estructura estable.
    Combina búsqueda estructural + minería de texto.
    """
    if not isinstance(data, dict):
        return {}

    FASE_KEYS = {"fases_propuestas", "fases_entregas", "fases", "entregas"}
    CRITERIO_KEYS = {"criterios_evaluacion", "criterios"}

    # ---- criterios, pesos y tipo ----
    criterios_raw = _find_any(data, *CRITERIO_KEYS)
    criterios, pesos, criterios_tipo = [], {}, {}
    if isinstance(criterios_raw, list):
        for item in criterios_raw:
            if isinstance(item, dict) and "nombre" in item:
                nombre = item["nombre"]
                criterios.append(nombre)
                if "peso" in item:
                    pesos[nombre] = item["peso"]
                if "tipo" in item:
                    criterios_tipo[nombre] = item["tipo"]
            elif isinstance(item, str):
                criterios.append(item)

    if not pesos:
        pesos_raw = _find_any(data, "pesos_evaluacion")
        if isinstance(pesos_raw, dict):
            pesos = pesos_raw

    # ---- fases ----
    fases_raw = _find_any(data, *FASE_KEYS)
    fases = []
    if isinstance(fases_raw, list):
        for item in fases_raw:
            if isinstance(item, dict):
                fases.append({
                    "titulo": item.get("nombre") or item.get("titulo"),
                    "descripcion": item.get("descripcion"),
                    "semana": item.get("semana"),
                    "peso": item.get("peso"),
                    "tipo": item.get("tipo"),
                })

    # ---- minería de texto sobre todo el RAW ----
    mined = _mine_text(_all_text(data))

    # ---- limite_palabras (estructural primero, texto como fallback) ----
    limite = _find_any(data, "limite_palabras")
    if isinstance(limite, dict):
        limite = limite.get("minimo")
    if not limite:
        limite = mined.get("limite_palabras_texto")

    # ---- penalizaciones ----
    penalizaciones = _find_any(data, "penalizaciones_clave", "penalizaciones") or []
    if isinstance(penalizaciones, str):
        penalizaciones = [penalizaciones]

    # ---- secciones ----
    secciones = _find_any(data, "secciones_obligatorias", "secciones") or []
    if isinstance(secciones, str):
        secciones = [secciones]

    # ---- reglas adicionales (todo lo que no son fases/criterios) ----
    reglas_raw = _extraer_reglas_adicionales(data, FASE_KEYS | CRITERIO_KEYS)
    # deduplicar y filtrar las que ya están en penalizaciones
    pen_set = set(penalizaciones)
    reglas_adicionales = [r for r in dict.fromkeys(reglas_raw) if r not in pen_set]

    return {
        "fases_propuestas": fases,

        "limite_palabras": limite,
        "limite_paginas": mined.get("limite_paginas") or _find_any(data, "limite_paginas"),

        "cantidad_fuentes_minima": _find_any(data, "cantidad_fuentes_minima") or mined.get("cantidad_fuentes_minima"),
        "formato_citas": _find_any(data, "formato_citas") or mined.get("formato_citas"),
        "antiguedad_fuentes_max_anos": _find_any(data, "antiguedad_fuentes_max_anos") or mined.get("antiguedad_fuentes_max_anos"),

        "formato_exigido": _find_any(data, "formato_exigido", "formato") or mined.get("formato_exigido"),
        "plataforma_entrega": _find_any(data, "plataforma_entrega") or mined.get("plataforma_entrega"),

        "secciones_obligatorias": secciones,

        "cantidad_integrantes_min": _find_any(data, "cantidad_integrantes_min") or mined.get("cantidad_integrantes_min"),
        "cantidad_integrantes_max": _find_any(data, "cantidad_integrantes_max") or mined.get("cantidad_integrantes_max"),
        "tipo_trabajo": _find_any(data, "tipo_trabajo") or mined.get("tipo_trabajo"),

        "herramienta_antiplagios": _find_any(data, "herramienta_antiplagios") or mined.get("herramienta_antiplagios"),
        "porcentaje_similitud_max": _find_any(data, "porcentaje_similitud_max") or mined.get("porcentaje_similitud_max"),

        "nota_minima_aprobatoria": _find_any(data, "nota_minima_aprobatoria") or mined.get("nota_minima_aprobatoria"),
        "permite_recuperacion": _find_any(data, "permite_recuperacion") or mined.get("permite_recuperacion"),

        "requiere_defensa_oral": _find_any(data, "requiere_defensa_oral") or mined.get("requiere_defensa_oral"),
        "duracion_presentacion_min": _find_any(data, "duracion_presentacion_min") or mined.get("duracion_presentacion_min"),
        "duracion_presentacion_max": _find_any(data, "duracion_presentacion_max") or mined.get("duracion_presentacion_max"),

        "criterios_evaluacion": criterios,
        "criterios_tipo": criterios_tipo,
        "pesos_evaluacion": pesos,

        "penalizaciones_clave": penalizaciones,
        "reglas_adicionales": reglas_adicionales,
    }


def validate_heuristics(h: dict) -> List[str]:
    warnings = []

    if not h:
        return ["No se pudo extraer información"]

    # evaluación
    if not h.get("criterios_evaluacion"):
        warnings.append("No se detectaron criterios de evaluación")

    if h.get("pesos_evaluacion"):
        total = sum(h["pesos_evaluacion"].values())
        if total and total != 100:
            warnings.append(f"Pesos de criterios no suman 100% (actual: {total}%)")

    if h.get("fases_propuestas"):
        total_fases = sum(f.get("peso") or 0 for f in h["fases_propuestas"])
        if total_fases and total_fases != 100:
            warnings.append(f"Pesos de fases no suman 100% (actual: {total_fases}%)")

    # extensión
    if not h.get("limite_palabras") and not h.get("limite_paginas"):
        warnings.append("Sin límite de extensión detectado")

    # fuentes
    if not h.get("cantidad_fuentes_minima"):
        warnings.append("Sin mínimo de fuentes detectado")

    if not h.get("formato_citas"):
        warnings.append("Sin formato de citas detectado (APA, IEEE, etc.)")

    # grupo
    if not h.get("tipo_trabajo"):
        warnings.append("No se pudo determinar si el trabajo es individual o grupal")

    if h.get("tipo_trabajo") in ("grupal", "mixto") and not h.get("cantidad_integrantes_max"):
        warnings.append("Trabajo grupal sin número de integrantes detectado")

    # presentación oral detectada pero sin duración
    if h.get("requiere_defensa_oral") and not h.get("duracion_presentacion_max"):
        warnings.append("Defensa oral requerida pero sin duración especificada")

    return warnings


# ==========================================
# FUNCIONES PRINCIPALES
# ==========================================

def extraer_contexto_integral(texto_contexto: str, requiere_fases: bool = True) -> dict:

    prompt = f"""
Eres un auditor académico.

Analiza el documento y extrae TODA la estructura evaluativa posible.

Incluye si existe:
- fases o entregas con semana y peso
- criterios de evaluación
- pesos por criterio
- reglas de formato o estructura

Puedes estructurar libremente el JSON.

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

        # 1. normalizar
        normalized = normalize_heuristicas(data)

        # 2. validar estructura
        parsed = HeuristicasMinimas(**normalized)
        result = parsed.model_dump()

        # 3. validar lógica
        result["warnings"] = validate_heuristics(result)

        # opcional debug
        result["raw"] = data

        return result

    except Exception as e:
        print(f"Error en extracción: {e}")
        return {}


def _resumir_heuristicas(h: dict) -> str:
    """Construye un resumen legible de las reglas del proyecto, omitiendo campos vacíos."""
    lineas = []
    if h.get("tipo_trabajo"):
        lineas.append(f"- Modalidad: {h['tipo_trabajo']}")
    if h.get("cantidad_integrantes_max"):
        lineas.append(f"- Integrantes por grupo: {h['cantidad_integrantes_max']}")
    if h.get("criterios_evaluacion"):
        pesos = h.get("pesos_evaluacion") or {}
        tipos = h.get("criterios_tipo") or {}
        for c in h["criterios_evaluacion"]:
            detalle = []
            if c in pesos:
                detalle.append(f"{pesos[c]}%")
            if c in tipos:
                detalle.append(tipos[c])
            sufijo = f" ({', '.join(detalle)})" if detalle else ""
            lineas.append(f"- Criterio de evaluación: {c}{sufijo}")
    if h.get("fases_propuestas"):
        for f in h["fases_propuestas"]:
            titulo = f.get("titulo", "Fase")
            semana = f.get("semana")
            peso = f.get("peso")
            info = []
            if semana: info.append(f"semana {semana}")
            if peso: info.append(f"{peso}%")
            sufijo = f" ({', '.join(info)})" if info else ""
            lineas.append(f"- Entrega: {titulo}{sufijo}")
    if h.get("limite_palabras"):
        lineas.append(f"- Límite de palabras: {h['limite_palabras']}")
    if h.get("limite_paginas"):
        lineas.append(f"- Límite de páginas: {h['limite_paginas']}")
    if h.get("formato_citas"):
        lineas.append(f"- Formato de citas: {h['formato_citas']}")
    if h.get("cantidad_fuentes_minima"):
        lineas.append(f"- Mínimo de fuentes: {h['cantidad_fuentes_minima']}")
    if h.get("reglas_adicionales"):
        for r in h["reglas_adicionales"]:
            lineas.append(f"- Regla: {r}")
    if h.get("penalizaciones_clave"):
        for p in h["penalizaciones_clave"]:
            lineas.append(f"- Penalización: {p}")
    return "\n".join(lineas) if lineas else "No se extrajeron reglas del documento de contexto."


def revisar_coherencia_texto(
    texto: str,
    opcion: str = "estructura",
    tarea_titulo: str = "",
    project_heuristics: dict | None = None
) -> str:

    try:
        contexto = _resumir_heuristicas(project_heuristics) if project_heuristics else "Sin reglas de contexto."
        seccion = f'"{tarea_titulo}"' if tarea_titulo else "esta sección"

        if opcion == "rubrica":
            prompt = f"""Eres un auditor académico. Revisa el borrador de {seccion} y evalúa si cumple con las reglas del trabajo.

Reglas del proyecto:
{contexto}

Texto a revisar:
{texto}

Responde de forma concisa y específica al texto:
✅ Qué cumple con las reglas
⚠️ Qué incumple o necesita corrección
No inventes reglas que no estén listadas arriba."""

        elif opcion == "citas":
            formato = (project_heuristics or {}).get("formato_citas") or "APA 7"
            prompt = f"""Eres un revisor editorial académico. Analiza las citas y referencias en {seccion}.

Formato exigido: {formato}

Texto a revisar:
{texto}

Indica:
- Citas presentes y si tienen el formato correcto de {formato}
- Lugares donde se necesita citar pero no se hizo
- Errores de formato específicos
Si el texto no tiene citas, señala dónde deberían ir según el contenido."""

        else:  # estructura
            prompt = f"""Eres un revisor de escritura académica. Analiza la estructura y coherencia del texto de {seccion}.

Texto a revisar:
{texto}

Evalúa de forma puntual:
- Claridad de la idea principal en cada párrafo
- Transiciones y hilo conductor entre ideas
- Nivel de formalidad académica
- Extensión y proporción de cada parte
Da sugerencias concretas de mejora, no descripciones genéricas."""

        response = chat(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        return response.message.content or "Sin respuesta."

    except Exception as e:
        print(f"Error en revisión: {e}")
        return f"Error al ejecutar la auditoría: {type(e).__name__}: {e}"