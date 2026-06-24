import os
import pdfplumber
import streamlit as st
from src.database import get_session, Project, FormatTemplate, ProjectFile, Iteration, Task, User
from src.llm.ai_client import chat
from src.core.heuristicas import extraer_contexto_integral

st.set_page_config(page_title="Nuevo Proyecto - Synkademia", layout="centered")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

# Inicialización de la máquina de estados del Wizard
if "wizard_step" not in st.session_state:
    st.session_state["wizard_step"] = 1
if "draft_project" not in st.session_state:
    st.session_state["draft_project"] = {}
if "team_inputs" not in st.session_state:
    st.session_state["team_inputs"] = [""]

def next_step(): st.session_state["wizard_step"] += 1
def prev_step(): st.session_state["wizard_step"] -= 1

db = next(get_session())

st.title("Configuración de Proyecto")
st.progress(st.session_state["wizard_step"] / 3.0)
st.markdown("---")

# ==========================================
# PASO 1: METADATOS Y EQUIPO DINÁMICO
# ==========================================
if st.session_state["wizard_step"] == 1:
    st.subheader("Paso 1: Metadatos y Equipo")
    
    titulo = st.text_input("Título del trabajo", value=st.session_state["draft_project"].get("title", ""))
    curso = st.text_input("Curso", value=st.session_state["draft_project"].get("course", ""))
    
    formatos_db = db.query(FormatTemplate).all()
    nombres_formatos = [f.name for f in formatos_db] if formatos_db else ["APA 7"]
    formato = st.selectbox("Formato de Redacción Exigido", nombres_formatos)
    
    st.markdown("### Integrantes del Equipo")
    st.caption("Tu usuario ya está incluido. Añade el nombre de usuario exacto de tus compañeros.")
    
    for i in range(len(st.session_state["team_inputs"])):
        st.session_state["team_inputs"][i] = st.text_input(
            f"Compañero {i+1}", 
            value=st.session_state["team_inputs"][i], 
            key=f"team_input_{i}"
        )
        
    if st.button("Añadir casilla de integrante"):
        st.session_state["team_inputs"].append("")
        st.rerun()
        
    if st.button("Siguiente"):
        if titulo and curso:
            usernames_solicitados = [u.strip() for u in st.session_state["team_inputs"] if u.strip()]
            
            usuarios_encontrados = []
            if usernames_solicitados:
                usuarios_encontrados = db.query(User).filter(User.username.in_(usernames_solicitados)).all()
                nombres_encontrados = [u.username for u in usuarios_encontrados]
                
                faltantes = set(usernames_solicitados) - set(nombres_encontrados)
                if faltantes:
                    st.error(f"Los siguientes usuarios no existen: {', '.join(faltantes)}")
                    st.stop()
            
            is_solo = len(usuarios_encontrados) == 0
            team_ids = [st.session_state["user_id"]] + [u.id for u in usuarios_encontrados]
            
            st.session_state["draft_project"].update({
                "title": titulo, 
                "course": curso, 
                "format": formato,
                "team_ids": team_ids,
                "is_solo": is_solo
            })
            next_step()
            st.rerun()
        else:
            st.warning("El título y el curso son campos obligatorios.")

# ==========================================
# PASO 2: CARGA OBLIGATORIA DE CONTEXTO
# ==========================================
elif st.session_state["wizard_step"] == 2:
    st.subheader("Paso 2: Documento de Contexto")
    st.markdown("Para garantizar la auditoría inteligente, es obligatorio subir la rúbrica, sílabo o guía del proyecto.")
    
    archivo_contexto = st.file_uploader("Sube el documento guía (PDF)", type=["pdf"])
    
    requiere_fases = st.checkbox(
        "Deseo estructurar el desarrollo del proyecto en múltiples fases o iteraciones de entrega", 
        value=st.session_state["draft_project"].get("requiere_fases", True)
    )
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Atrás"):
            prev_step()
            st.rerun()
    with col2:
        if st.button("Procesar con Auditor IA", type="primary"):
            if not archivo_contexto:
                st.error("Debe proporcionar un archivo de contexto para continuar.")
            else:
                temp_dir = os.path.join("data", "uploads", "temp")
                os.makedirs(temp_dir, exist_ok=True)
                temp_path = os.path.join(temp_dir, archivo_contexto.name)
                
                with open(temp_path, "wb") as f:
                    f.write(archivo_contexto.getbuffer())
                
                texto_extraido = ""
                with st.spinner("Extrayendo texto del documento..."):
                    try:
                        with pdfplumber.open(temp_path) as pdf:
                            for page in pdf.pages:
                                text = page.extract_text()
                                if text:
                                    texto_extraido += text + "\n"
                    except Exception as e:
                        st.error(f"Error al leer el archivo PDF: {e}")
                        st.stop()
                
                if not texto_extraido.strip():
                    st.error("El PDF no contiene texto extraíble (podría ser una imagen).")
                    st.stop()
                
                st.session_state["draft_project"].update({
                    "requiere_fases": requiere_fases,
                    "context_file": {
                        "name": archivo_contexto.name,
                        "path": temp_path,
                        "extracted_text": texto_extraido.strip()
                    }
                })
                next_step()
                st.rerun()

# ==========================================
# PASO 3: COTEJO DE HEURÍSTICAS Y CONFIRMACIÓN
# ==========================================
elif st.session_state["wizard_step"] == 3:
    st.subheader("Paso 3: Validación de Heurísticas y Estructura")
    
    texto_contexto = st.session_state["draft_project"].get("context_file", {}).get("extracted_text", "")
    requiere_fases = st.session_state["draft_project"]["requiere_fases"]
    
    # Ejecución única del análisis del modelo por sesión en este paso
    if "ai_analysis" not in st.session_state["draft_project"]:
        with st.spinner("El modelo local está auditando el documento..."):
            analisis = extraer_contexto_integral(texto_contexto, requiere_fases=requiere_fases)
            st.session_state["draft_project"]["ai_analysis"] = analisis

    analisis = st.session_state["draft_project"]["ai_analysis"]
    
    # 1. Visualización de Estilos de Reducción según la Base de Datos
    formato_nombre = st.session_state["draft_project"]["format"]
    formato_template = db.query(FormatTemplate).filter_by(name=formato_nombre).first()
    
    st.markdown(f"### Estilos Determinados del Documento ({formato_nombre})")
    if formato_template and isinstance(formato_template.style_rules, dict):
        rules = formato_template.style_rules
        st.markdown(f"- **Fuentes y Tamaño:** {rules.get('font', 'No definido')}")
        st.markdown(f"- **Estructura H1:** {rules.get('h1', 'No definido')}")
        st.markdown(f"- **Márgenes:** {rules.get('margins', 'No definido')}")
    else:
        st.caption("Falta inicializar las semillas de formato estáticas. Se aplicarán valores APA 7 por defecto.")
    
    # 2. Heurísticas detectadas (solo las que tienen valor)
    st.markdown("### Heurísticas Detectadas")

    detectado = []
    if analisis.get("tipo_trabajo"):
        detectado.append(f"**Modalidad:** {analisis['tipo_trabajo'].capitalize()}")
    if analisis.get("cantidad_integrantes_max"):
        detectado.append(f"**Integrantes por grupo:** {analisis['cantidad_integrantes_max']}")
    if analisis.get("limite_palabras"):
        detectado.append(f"**Límite de palabras:** {analisis['limite_palabras']}")
    if analisis.get("limite_paginas"):
        detectado.append(f"**Límite de páginas:** {analisis['limite_paginas']}")
    if analisis.get("cantidad_fuentes_minima"):
        detectado.append(f"**Mínimo de fuentes:** {analisis['cantidad_fuentes_minima']}")
    if analisis.get("formato_citas"):
        detectado.append(f"**Formato de citas:** {analisis['formato_citas']}")
    if analisis.get("criterios_evaluacion"):
        detectado.append(f"**Criterios:** {', '.join(analisis['criterios_evaluacion'])}")
    if analisis.get("nota_minima_aprobatoria"):
        detectado.append(f"**Nota mínima:** {analisis['nota_minima_aprobatoria']}")

    for item in detectado:
        st.markdown(f"- {item}")

    if not detectado:
        st.caption("No se detectaron heurísticas cuantificables en el documento.")

    if analisis.get("penalizaciones_clave"):
        st.markdown("**Penalizaciones:**")
        for pen in analisis["penalizaciones_clave"]:
            st.warning(pen)

    if analisis.get("reglas_adicionales"):
        st.markdown("**Reglas del trabajo:**")
        for regla in analisis["reglas_adicionales"]:
            st.info(regla)

    # 3. Propuesta de División del Trabajo / Fases
    st.markdown("### Planificación Temporal Propuesta")
    fases_propuestas = analisis.get("fases_propuestas", [])
    
    if requiere_fases and fases_propuestas:
        for idx, fase in enumerate(fases_propuestas):
            st.markdown(f"**Fase {idx+1}: {fase.get('titulo')}**")
            st.caption(fase.get("descripcion", ""))
    else:
        st.markdown("- **Iteración 1: Entrega Única** (Estructura de entrega única activada o no se detectaron fases).")

    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Atrás"):
            st.session_state["draft_project"].pop("ai_analysis", None)
            prev_step()
            st.rerun()
    with col2:
        if st.button("Confirmar y Finalizar Creación", type="primary"):
            with st.spinner("Registrando proyecto y asignando tareas..."):
                
                formato_db = db.query(FormatTemplate).filter_by(name=formato_nombre).first()
                
                metadata = {
                    "team_ids": st.session_state["draft_project"]["team_ids"],
                    "is_solo": st.session_state["draft_project"]["is_solo"]
                }
                
                nuevo_proyecto = Project(
                    title=st.session_state["draft_project"]["title"],
                    course=st.session_state["draft_project"]["course"],
                    format_id=formato_db.id if formato_db else None,
                    project_metadata=metadata,
                    project_heuristics=analisis
                )
                db.add(nuevo_proyecto)
                db.commit()
                db.refresh(nuevo_proyecto)
                
                # Mover el archivo de la carpeta temporal a la definitiva
                if "context_file" in st.session_state["draft_project"]:
                    old_path = st.session_state["draft_project"]["context_file"]["path"]
                    filename = st.session_state["draft_project"]["context_file"]["name"]
                    
                    final_dir = os.path.join("data", "uploads", f"project_{nuevo_proyecto.id}")
                    os.makedirs(final_dir, exist_ok=True)
                    final_path = os.path.join(final_dir, filename)
                    os.rename(old_path, final_path)
                    
                    nuevo_archivo = ProjectFile(
                        project_id=nuevo_proyecto.id,
                        filename=filename,
                        file_path=final_path,
                        file_type="context_rubric",
                        extracted_text=st.session_state["draft_project"]["context_file"]["extracted_text"],
                        processed_data=analisis
                    )
                    db.add(nuevo_archivo)
                
                # Distribución de tareas con round-robin sobre integrantes
                from itertools import cycle

                team_ids = metadata["team_ids"]
                assignee_cycle = cycle(team_ids)

                criterios     = analisis.get("criterios_evaluacion") or []
                criterios_tipo = analisis.get("criterios_tipo") or {}
                pesos         = analisis.get("pesos_evaluacion") or {}
                secciones     = analisis.get("secciones_obligatorias") or ["Introducción", "Desarrollo", "Conclusiones"]

                def items_fase(es_ultima: bool) -> list:
                    # Última fase → criterios de evaluación; intermedias → secciones del documento
                    if es_ultima and criterios:
                        return [
                            {
                                "titulo": c,
                                "instruccion": f"Tipo: {criterios_tipo.get(c, 'No especificado')} — Peso: {pesos.get(c, '?')}%"
                            }
                            for c in criterios
                        ]
                    return [{"titulo": s, "instruccion": None} for s in secciones]

                if requiere_fases and fases_propuestas:
                    for i, fase in enumerate(fases_propuestas):
                        es_ultima = (i == len(fases_propuestas) - 1)
                        nueva_iteracion = Iteration(
                            project_id=nuevo_proyecto.id,
                            title=fase.get("titulo", "Fase")
                        )
                        db.add(nueva_iteracion)
                        db.commit()
                        db.refresh(nueva_iteracion)

                        for item in items_fase(es_ultima):
                            db.add(Task(
                                iteration_id=nueva_iteracion.id,
                                title=item["titulo"],
                                ai_instructions=item["instruccion"],
                                assignee_id=next(assignee_cycle)
                            ))
                else:
                    nueva_iteracion = Iteration(
                        project_id=nuevo_proyecto.id,
                        title="Iteración 1: Entrega Final"
                    )
                    db.add(nueva_iteracion)
                    db.commit()
                    db.refresh(nueva_iteracion)

                    # Sin fases: si hay criterios los usamos directamente, si no, secciones
                    items = items_fase(es_ultima=True)
                    for item in items:
                        db.add(Task(
                            iteration_id=nueva_iteracion.id,
                            title=item["titulo"],
                            ai_instructions=item["instruccion"],
                            assignee_id=next(assignee_cycle)
                        ))
                
                db.commit()
                
                # Limpieza de estados del Wizard
                st.session_state.pop("wizard_step", None)
                st.session_state.pop("draft_project", None)
                st.session_state["team_inputs"] = [""]
                st.session_state["current_project_id"] = nuevo_proyecto.id
                
                st.switch_page("pages/3_Workspace.py")