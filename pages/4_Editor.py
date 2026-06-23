import streamlit as st
from src.database import get_session, Project, Task
from src.llm.ai_client import revisar_coherencia_texto

st.set_page_config(page_title="Editor - Synkademia", layout="wide")

# 1. Autenticación estricta y segregada
if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

if not st.session_state.get("current_project_id"):
    st.warning("Selecciona un proyecto desde el Dashboard para comenzar a editar.")
    st.stop()

db = next(get_session())
proyecto_id = st.session_state["current_project_id"]

# .first() devuelve Project | None
proyecto = db.query(Project).filter(Project.id == proyecto_id).first()

# 2. Corrección Pylance: Validación explícita de existencia (evita errores None)
if not proyecto:
    st.error("El proyecto no existe o fue eliminado.")
    st.stop()

# Al pasar el st.stop(), Pylance sabe con certeza que 'proyecto' es válido
st.title(str(proyecto.title))
st.caption(f"{proyecto.work_type} | Curso: {proyecto.course}")
st.markdown("---")

col_editor, col_ia = st.columns([7, 3], gap="large")

with col_editor:
    st.subheader("Lienzo de Redacción")
    
    tareas = db.query(Task).filter(Task.project_id == proyecto.id).all()
    
    # 3. Corrección Pylance: Se ignora la advertencia de columna dinámica del ORM
    nombres_secciones = [t.title for t in tareas] 
    seccion_actual = st.selectbox("Sección a editar", nombres_secciones)
    
    tarea_activa = next((t for t in tareas if t.title == seccion_actual), None) 
    
    if tarea_activa:
        # Se asegura que si el contenido es None en la BD, se maneje como string vacío
        contenido_actual = tarea_activa.content or "" 
        
        nuevo_contenido = st.text_area(
            label="Contenido",
            value=str(contenido_actual),
            height=450,
            label_visibility="collapsed"
        )
        
        if st.button("Guardar progreso"):
            tarea_activa.content = nuevo_contenido 
            db.commit()
            st.success("Cambios guardados.")

with col_ia:
    st.subheader("Asesor IA")
    st.info("Solicita una revisión de coherencia, tono académico y formato APA para la sección actual.")
    
    if st.button("Analizar Texto", type="primary"):
        # Se valida que el bloque no esté vacío antes de llamar a la API
        if tarea_activa and tarea_activa.content: 
            with st.spinner("Analizando estructura..."):
                sugerencias = revisar_coherencia_texto(str(tarea_activa.content)) 
                
            st.markdown("### Sugerencias de mejora")
            st.write(sugerencias)
        else:
            st.warning("El bloque de texto está vacío. Escribe algo para analizar.")