import streamlit as st
from src.database import get_session, Project, Task, User
from src.ai_client import generar_estructura_proyecto

st.set_page_config(page_title="Nuevo Proyecto - Synkademia", layout="centered")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

st.title("Configuración de Proyecto")

with st.form("project_form"):
    titulo = st.text_input("Título del trabajo")
    tipo_trabajo = st.selectbox("Tipo de documento", ["Informe de Investigación", "Ensayo", "Estudio de Caso", "Monografía"])
    curso = st.text_input("Curso")
    
    st.markdown("Integrantes del equipo")
    integrantes_raw = st.text_input("Nombres separados por comas (ej. Ana, Carlos, Luis)")
    
    submit_button = st.form_submit_button("Generar Estructura")

if submit_button:
    if not titulo or not curso or not integrantes_raw:
        st.warning("Completa todos los campos obligatorios.")
    else:
        integrantes_list = [i.strip() for i in integrantes_raw.split(",") if i.strip()]
        
        with st.spinner("Analizando contexto académico y estructurando responsabilidades..."):
            estructura_json = generar_estructura_proyecto(tipo_trabajo, curso, integrantes_list)
            
        if estructura_json:
            st.success("Estructura generada exitosamente.")
            
            # Guardar el proyecto en la base de datos
            db = next(get_session())
            nuevo_proyecto = Project(
                title=titulo,
                work_type=tipo_trabajo,
                course=curso
            )
            db.add(nuevo_proyecto)
            db.commit()
            db.refresh(nuevo_proyecto)
            
            # Mostrar la estructura generada y crear las tareas
            st.markdown("### Asignación Propuesta")
            for item in estructura_json:
                st.write(f"**{item.get('titulo', 'Sección')}** — Asignado a: {item.get('asignado_a', 'Sin asignar')}")
                
                # Crear tarea pendiente en la base de datos
                nueva_tarea = Task(
                    title=item.get('titulo', 'Sección'),
                    project_id=nuevo_proyecto.id
                )
                db.add(nueva_tarea)
            
            db.commit()
            
            st.session_state["current_project_id"] = nuevo_proyecto.id
            if st.button("Ir al Editor"):
                st.switch_page("pages/3_Editor.py")
        else:
            st.error("Hubo un problema al contactar con la IA. Inténtalo nuevamente.")