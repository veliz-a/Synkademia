import re
from typing import Any, Dict, List


def _walk(obj: Any) -> List[dict]:
    """
    Aplana cualquier JSON anidado buscando dicts relevantes.
    """
    found = []

    if isinstance(obj, dict):
        found.append(obj)
        for v in obj.values():
            found.extend(_walk(v))

    elif isinstance(obj, list):
        for item in obj:
            found.extend(_walk(item))

    return found


def normalize_heuristicas(data: dict) -> dict:

    if not isinstance(data, dict):
        return {}

    nodes = _walk(data)

    fases = []
    criterios = []
    pesos = {}

    limite = None
    penalizaciones = []

    for node in nodes:

        if not isinstance(node, dict):
            continue

        # ---- detectar fases (heurística por contenido) ----
        if {"nombre", "semana"} & node.keys():
            fases.append({
                "titulo": node.get("nombre"),
                "semana": node.get("semana"),
                "peso": node.get("peso"),
                "descripcion": node.get("descripcion")
            })

        # ---- detectar criterios ----
        if "nombre" in node and "peso" in node:
            criterios.append(node["nombre"])
            pesos[node["nombre"]] = node["peso"]

        # ---- detectar límite de palabras ----
        for k, v in node.items():
            if isinstance(v, str):
                match = re.search(r"(\d+)\s*palabra", v.lower())
                if match:
                    limite = int(match.group(1))

        # ---- penalizaciones ----
        if "penalizacion" in str(node).lower():
            if isinstance(node, dict):
                penalizaciones.append(node.get("requisito") or node.get("descripcion"))

    return {
        "fases_propuestas": fases,
        "limite_palabras": limite,
        "cantidad_fuentes_minima": None,
        "formato_exigido": None,
        "secciones_obligatorias": [],
        "penalizaciones_clave": penalizaciones,
        "criterios_evaluacion": criterios,
        "pesos_evaluacion": pesos
    }