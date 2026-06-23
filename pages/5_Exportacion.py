import streamlit as st
from sqlalchemy.orm import joinedload
from src.database import get_session, Project, Iteration, Task, User
from src.document_builder import generar_docx

st.set_page_config(page_title="Exportación - Synkademia", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

if not st.session_state.get("current_project_id"):
    st.warning("Selecciona un proyecto desde el Dashboard.")
    st.stop()

db = next(get_session())
project_id = st.session_state["current_project_id"]

proyecto = db.query(Project).options(
    joinedload(Project.iterations).joinedload(Iteration.tasks)
).filter(Project.id == project_id).first()

if not proyecto:
    st.error("El proyecto no existe.")
    st.stop()

# Recopilar tareas con contenido
tareas_con_contenido = []
for iteracion in proyecto.iterations:
    for tarea in iteracion.tasks:
        if tarea.content and tarea.content.strip():
            tareas_con_contenido.append(tarea)

# Recopilar equipo
metadata = proyecto.project_metadata or {}
team_ids = metadata.get("team_ids", [])
integrantes = db.query(User).filter(User.id.in_(team_ids)).all() if team_ids else []

st.markdown("""
    <style>
    .pdf-preview-container {
        background-color: #525659;
        padding: 40px;
        border-radius: 4px;
        height: 700px;
        overflow-y: scroll;
    }
    .pdf-page {
        background-color: #FFFFFF;
        max-width: 21cm;
        min-height: 29.7cm;
        margin: 0 auto 30px auto;
        padding: 2.54cm;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
        font-family: 'Times New Roman', Times, serif;
        color: #000000;
        line-height: 2;
    }
    .pdf-title {
        text-align: center;
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 20px;
    }
    .pdf-text {
        text-align: justify;
        text-indent: 1.27cm;
        margin-bottom: 10px;
    }
    .pdf-section-title {
        text-align: center;
        font-weight: bold;
        margin-top: 30px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

st.title("Compilación Final")
st.caption("Revisa el ensamblaje del documento antes de exportarlo.")
st.markdown("---")

col_prev, col_acciones = st.columns([7, 3], gap="large")

with col_prev:
    st.subheader("Vista Previa (Simulación de Impresión)")
    
    # Contenedor que emula el visor de PDF
    preview_html = '<div class="pdf-preview-container">'
    
    # Página 1: Portada
    preview_html += '<div class="pdf-page">'
    preview_html += f'<br><br><br><br><div class="pdf-title">{proyecto.title}</div>'
    preview_html += f'<div style="text-align: center;">Curso: {proyecto.course}</div><br>'
    
    if metadata.get("institution"):
        preview_html += f'<div style="text-align: center;">{metadata["institution"]}</div><br>'
        
    preview_html += '<div style="text-align: center;">Autores:</div>'
    for user in integrantes:
        preview_html += f'<div style="text-align: center;">{user.username}</div>'
    preview_html += '</div>'
    
    # Páginas de contenido (Concatenación simple para vista previa)
    preview_html += '<div class="pdf-page">'
    if not tareas_con_contenido:
        preview_html += '<div style="text-align:center; color:#999; margin-top:50px;">El documento no tiene contenido redactado aún.</div>'
    else:
        for tarea in tareas_con_contenido:
            preview_html += f'<div class="pdf-section-title">{tarea.title}</div>'
            parrafos = str(tarea.content).split('\n\n')
            for p in parrafos:
                if p.strip():
                    preview_html += f'<div class="pdf-text">{p.strip()}</div>'
    preview_html += '</div>'
    
    preview_html += '</div>'
    
    st.markdown(preview_html, unsafe_allow_html=True)

with col_acciones:
    st.subheader("Opciones de Exportación")
    
    st.info("El sistema aplicará estrictamente los márgenes, tipografía e interlineado configurados en las reglas del Workspace al generar el archivo.")
    
    if st.button("Generar Archivo de Word (.docx)", type="primary", use_container_width=True):
        if not tareas_con_contenido:
            st.warning("No hay contenido para exportar.")
        else:
            with st.spinner("Ensamblando documento y aplicando formatos..."):
                buffer = generar_docx(proyecto, integrantes, tareas_con_contenido)
                
                st.download_button(
                    label="Descargar Documento Final",
                    data=buffer,
                    file_name=f"{proyecto.title.replace(' ', '_')}_Final.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )