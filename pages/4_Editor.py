import streamlit as st
from sqlalchemy.orm import joinedload
from src.database import get_session, Project, Iteration, Task, User
from src.core.heuristicas import revisar_coherencia_texto

st.set_page_config(page_title="Editor - Synkademia", layout="wide")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

if not st.session_state.get("current_project_id"):
    st.warning("Selecciona un proyecto desde el Dashboard para comenzar a trabajar.")
    st.stop()

db = next(get_session())
project_id = st.session_state["current_project_id"]
user_id = st.session_state["user_id"]

# Carga optimizada del proyecto, sus fases y tareas correspondientes
proyecto = db.query(Project).options(
    joinedload(Project.iterations).joinedload(Iteration.tasks).joinedload(Task.assignee)
).filter(Project.id == project_id).first()

if not proyecto:
    st.error("El proyecto especificado no existe.")
    st.stop()

# Inyección de estilos CSS para simular la hoja A4 y el look editorial limpio
st.markdown("""
    <style>
    /* El textarea ES la hoja A4 */
    .stTextArea textarea {
        background-color: #FFFFFF;
        font-family: 'Times New Roman', Times, serif;
        font-size: 12pt;
        line-height: 1.8;
        border: 1px solid #EAEAEA !important;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        padding: 40px 50px !important;
        min-height: 900px;
    }
    .task-highlight-owner {
        background-color: #F0F7F4;
        border-left: 4px solid #000000;
        padding: 12px;
        margin-bottom: 15px;
    }
    .task-highlight-other {
        background-color: #F9F9F9;
        border-left: 4px solid #CCCCCC;
        padding: 12px;
        margin-bottom: 15px;
        color: #757575;
    }
    </style>
""", unsafe_allow_html=True)

# Encabezado del documento
st.title(proyecto.title)
st.caption(f"Curso: {proyecto.course}")
st.markdown("---")

# Organización asimétrica de la pantalla
col_navegacion, col_lienzo = st.columns([1, 3], gap="large")

with col_navegacion:
    st.subheader("Secciones del Proyecto")
    
    # Recolectar todas las tareas organizadas por sus respectivas fases
    tareas_totales = []
    lista_opciones = []
    
    for iteracion in proyecto.iterations:
        for tarea in iteracion.tasks:
            tareas_totales.append(tarea)
            # Indicar visualmente si la tarea pertenece al usuario en sesión
            es_propia = " (Tuyo)" if tarea.assignee_id == user_id else f" ({tarea.assignee.username if tarea.assignee else 'Sin asignar'})"
            lista_opciones.append(f"{iteracion.title} - {tarea.title}{es_propia}")
            
    if not lista_opciones:
        st.info("No hay secciones configuradas para este proyecto.")
        st.stop()
        
    seleccion = st.radio("Selecciona el bloque a redactar", lista_opciones, label_visibility="collapsed")
    
    # Obtener el índice de la tarea seleccionada en el radio button
    indice_seleccionado = lista_opciones.index(seleccion)
    tarea_activa = tareas_totales[indice_seleccionado]
    
    st.markdown("---")
    
    # Validación visual de responsabilidades (Jerarquía y Cotejo de ID)
    if tarea_activa.assignee_id == user_id:
        st.markdown('<div class="task-highlight-owner"><strong>Espacio de Redacción Activo</strong><br>Esta sección te corresponde. Los cambios se guardarán directamente en el flujo común del equipo.</div>', unsafe_allow_html=True)
        modo_lectura = False
    else:
        responsable_name = tarea_activa.assignee.username if tarea_activa.assignee else "Nadie asignado"
        st.markdown(f'<div class="task-highlight-other"><strong>Sección de Solo Lectura</strong><br>Esta sección está asignada a: <strong>{responsable_name}</strong>. Puedes visualizar el avance pero no modificar el contenido primario.</div>', unsafe_allow_html=True)
        modo_lectura = True

    # El Botón de Auditoría Inteligente estilo Medium (Negro con letras blancas por el tema primario)
    st.subheader("Auditoría Documental")
    st.write("Ejecuta funciones de auditoría y soporte.")
    
    # Uso de st.toggle o botón para desplegar las opciones fijas sin necesidad de chat libre
    activar_auditor = st.button("Auditar Sección", type="primary", use_container_width=True)
    
    if activar_auditor or st.session_state.get("menu_ia_activo", False):
        st.session_state["menu_ia_activo"] = True
        
        # Opciones fijas controladas desde backend (heuristias.py)
        OPCIONES_AUDITORIA = {
            "Contrastar con Rúbrica": "rubrica",
            "Revisar Estructura y Coherencia": "estructura",
            "Verificar Citas y Formato": "citas",
        }

        opcion_auditoria = st.selectbox("Tipo de auditoría", list(OPCIONES_AUDITORIA.keys()))

        if st.button("Ejecutar Análisis", use_container_width=True):
            if tarea_activa.content:
                with st.spinner("Analizando..."):
                    st.session_state["resultado_auditoria"] = revisar_coherencia_texto(
                        texto=str(tarea_activa.content),
                        opcion=OPCIONES_AUDITORIA[opcion_auditoria],
                        tarea_titulo=tarea_activa.title,
                        project_heuristics=proyecto.project_heuristics
                    )
            else:
                st.warning("El lienzo actual está vacío. Añade contenido para auditar.")

with col_lienzo:
    st.markdown(f"### {tarea_activa.title}")
    st.caption("Escribe el contenido de la sección. Usa los botones inferiores para insertar tablas o imágenes.")

    contenido_input = st.text_area(
        label="Lienzo de texto",
        value=tarea_activa.content if tarea_activa.content else "",
        height=800,
        disabled=modo_lectura,
        label_visibility="collapsed",
        key=f"text_area_{tarea_activa.id}"
    )

    if not modo_lectura:
        col_btn1, col_btn2, col_save = st.columns([1, 1, 2])
        with col_btn1:
            if st.button("Insertar Tabla Base", use_container_width=True):
                contenido_input += "\n\n[ESTRUCTURA_TABLA: 3 Columnas, 2 Filas]\n\n"
                st.rerun()
        with col_btn2:
            if st.button("Insertar Imagen", use_container_width=True):
                contenido_input += "\n\n[ESTRUCTURA_IMAGEN: nombre_archivo.png]\n\n"
                st.rerun()
        with col_save:
            if st.button("Guardar Cambios en Servidor", type="primary", use_container_width=True):
                tarea_activa.content = contenido_input
                db.commit()
                st.success("Progreso consolidado de forma segura.")
                st.rerun()

if st.session_state.get("resultado_auditoria"):
    st.markdown("---")
    st.markdown("### Resultado del Auditor")
    st.info(st.session_state["resultado_auditoria"])