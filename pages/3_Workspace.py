import os
import streamlit as st
from sqlalchemy.orm import joinedload
from src.database import get_session, Project, User, Iteration, Task, ProjectFile

st.set_page_config(page_title="Workspace - Synkademia", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Inicia sesión.")
    st.stop()

if not st.session_state.get("current_project_id"):
    st.warning("Selecciona un proyecto desde el Dashboard.")
    st.stop()

db = next(get_session())
project_id = st.session_state["current_project_id"]

# Uso de joinedload para optimizar las consultas a la base de datos en una sola transacción
proyecto = db.query(Project).options(
    joinedload(Project.format),
    joinedload(Project.iterations).joinedload(Iteration.tasks).joinedload(Task.assignee),
    joinedload(Project.files)
).filter(Project.id == project_id).first()

if not proyecto:
    st.error("El proyecto no existe o fue eliminado.")
    st.stop()

st.title(proyecto.title)
st.caption(f"{proyecto.course} | Formato base: {proyecto.format.name if proyecto.format else 'No definido'}")
st.markdown("---")

tab_metadatos, tab_heuristicas, tab_tablero = st.tabs([
    "Metadatos y Equipo", 
    "Reglas y Contexto", 
    "Tablero de Iteraciones"
])

# ==========================================
# PESTAÑA 1: METADATOS Y EQUIPO
# ==========================================
with tab_metadatos:
    st.subheader("Configuración Editorial")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Metadatos del Documento**")
        metadata = proyecto.project_metadata or {}
        st.text_input("Institución", value=metadata.get("institution", ""), disabled=True)
        st.text_input("Profesor / Catedrático", value=metadata.get("professor", ""), disabled=True)
        
    with col2:
        st.markdown("**Equipo de Trabajo**")
        team_ids = metadata.get("team_ids", [])
        usuarios_equipo = db.query(User).filter(User.id.in_(team_ids)).all() if team_ids else []
        
        for user in usuarios_equipo:
            st.markdown(f"- **{user.username}**")
            # Aquí en el futuro se pueden añadir inputs para que cada usuario ingrese su ORCID

# ==========================================
# PESTAÑA 2: REGLAS Y CONTEXTO
# ==========================================
with tab_heuristicas:
    st.subheader("Auditoría de Requisitos")
    st.write("Parámetros extraídos del documento base. Estas reglas guiarán las revisiones del modelo.")
    
    heuristicas = proyecto.project_heuristics or {}
    
    col_reglas, col_archivos = st.columns([2, 1])
    
    with col_reglas:
        st.markdown("**Restricciones Críticas**")
        st.write(f"Límite de palabras: {heuristicas.get('limite_palabras', 'No especificado')}")
        st.write(f"Fuentes mínimas: {heuristicas.get('cantidad_fuentes_minima', 'No especificado')}")
        
        penalizaciones = heuristicas.get("penalizaciones_clave", [])
        if penalizaciones:
            st.markdown("**Criterios de Penalización**")
            for p in penalizaciones:
                st.warning(p)
                
        reglas_extra = heuristicas.get("reglas_adicionales_detectadas", [])
        if reglas_extra:
            st.markdown("**Reglas Adicionales**")
            for r in reglas_extra:
                st.info(r)
                
    with col_archivos:
        st.markdown("**Archivos de Contexto Activos**")
        for archivo in proyecto.files:
            if archivo.file_type == "context_rubric":
                st.markdown(f"- {archivo.filename}")
                st.caption(f"Subido el {archivo.uploaded_at.strftime('%Y-%m-%d')}")

# ==========================================
# PESTAÑA 3: TABLERO DE ITERACIONES
# ==========================================
with tab_tablero:
    st.subheader("Gestión de Entregables")
    
    col_izq, col_der = st.columns([3, 1])
    
    with col_izq:
        for iteracion in proyecto.iterations:
            with st.container(border=True):
                st.markdown(f"#### {iteracion.title}")
                st.caption(f"Estado: {iteracion.status.upper()}")
                
                if not iteracion.tasks:
                    st.write("No hay secciones asignadas a esta fase.")
                else:
                    for tarea in iteracion.tasks:
                        t_col1, t_col2, t_col3 = st.columns([3, 2, 2])
                        with t_col1:
                            st.write(f"**{tarea.title}**")
                        with t_col2:
                            nombres_equipo = [u.username for u in usuarios_equipo]
                            indice_actual = nombres_equipo.index(tarea.assignee.username) if tarea.assignee and tarea.assignee.username in nombres_equipo else 0
                            
                            nuevo_asignado = st.selectbox(
                                "Responsable", 
                                ["Sin asignar"] + nombres_equipo,
                                index=indice_actual + 1 if tarea.assignee else 0,
                                key=f"assign_{tarea.id}",
                                label_visibility="collapsed"
                            )
                            
                            # Actualizar en BD si hay cambio
                            if nuevo_asignado != "Sin asignar" and (not tarea.assignee or tarea.assignee.username != nuevo_asignado):
                                user_obj = next((u for u in usuarios_equipo if u.username == nuevo_asignado), None)
                                if user_obj:
                                    tarea.assignee_id = user_obj.id
                                    db.commit()
                        with t_col3:
                            nuevo_estado = st.selectbox(
                                "Estado",
                                ["pending", "in_progress", "completed"],
                                index=["pending", "in_progress", "completed"].index(tarea.status),
                                key=f"status_{tarea.id}",
                                label_visibility="collapsed"
                            )
                            if nuevo_estado != tarea.status:
                                tarea.status = nuevo_estado
                                db.commit()
    with col_der:
        st.markdown("**Acciones**")
        if st.button("Ir al Editor del Documento", type="primary", use_container_width=True):
            st.switch_page("pages/4_Editor.py")