import streamlit as st
from src.database import get_session, Project

st.set_page_config(page_title="Dashboard - Synkademia", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

db = next(get_session())
user_id = st.session_state["user_id"]
username = st.session_state["username"]

st.title(f"Proyectos de {username}")
st.markdown("---")

# Filtramos los proyectos donde el usuario actual es miembro del equipo
todos_los_proyectos = db.query(Project).all()
mis_proyectos = []

for p in todos_los_proyectos:
    metadata = p.project_metadata or {}
    team_ids = metadata.get("team_ids", [])
    if user_id in team_ids:
        mis_proyectos.append(p)

if not mis_proyectos:
    st.info("No tienes proyectos activos. Dirígete a 'Nuevo Proyecto' en el menú lateral para comenzar.")
else:
    # Renderizado de la lista de proyectos (Estilo lista editorial)
    for proj in mis_proyectos:
        with st.container():
            col_info, col_tipo, col_accion = st.columns([5, 2, 2])
            
            with col_info:
                st.subheader(proj.title)
                # Obtenemos el nombre del formato si la relación existe
                nombre_formato = proj.format.name if proj.format else "Formato no definido"
                st.caption(f"Curso: {proj.course} | {nombre_formato}")
                
            with col_tipo:
                # Indicador de trabajo en equipo o individual
                es_individual = proj.project_metadata.get("is_solo", False)
                if es_individual:
                    st.markdown("**Modalidad:** Individual")
                else:
                    st.markdown("**Modalidad:** Equipo")
                    
            with col_accion:
                # Botón principal para ingresar al panel de control del proyecto
                if st.button("Abrir Workspace", key=f"btn_workspace_{proj.id}", type="primary", use_container_width=True):
                    st.session_state["current_project_id"] = proj.id
                    st.switch_page("pages/3_Workspace.py")
                    
        st.markdown("---")