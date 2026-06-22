import streamlit as st
from src.database import get_session, Project, Task, User

st.set_page_config(page_title="Dashboard - Synkademia", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

st.title("Proyectos Activos")
st.markdown("---")

def cargar_proyectos():
    db = next(get_session())
    user_id = st.session_state["user_id"]
    
    # Obtener proyectos donde el usuario tiene al menos una tarea asignada
    proyectos = db.query(Project).join(Task).filter(Task.assignee_id == user_id).all()
    return proyectos

proyectos = cargar_proyectos()

if not proyectos:
    st.info("No tienes proyectos activos. Ve a 'Nuevo Proyecto' para comenzar.")
else:
    for proj in proyectos:
        with st.container():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(proj.title)
                st.caption(f"{proj.work_type} | {proj.course}")
            with col2:
                if st.button("Abrir Proyecto", key=f"open_{proj.id}"):
                    st.session_state["current_project_id"] = proj.id
                    st.switch_page("pages/3_Editor.py")
            st.markdown("---")