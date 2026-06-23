import os
import PyPDF2
import streamlit as st
from src.database import get_session, Project, FormatTemplate, ProjectFile, Iteration, User
# Importaremos estas funciones de tu cliente de IA (las construiremos en el siguiente paso)
from src.llm.ai_client import generar_mockup_iteraciones, extraer_heuristicas

st.set_page_config(page_title="Nuevo Proyecto - Synkademia", layout="centered")

if not st.session_state.get("authenticated"):
    st.error("Acceso denegado. Por favor, inicia sesión.")
    st.stop()

if "wizard_step" not in st.session_state:
    st.session_state["wizard_step"] = 1
if "draft_project" not in st.session_state:
    st.session_state["draft_project"] = {}
if "team_inputs" not in st.session_state:
    # Se inicia con un campo vacío para invitar compañeros
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
    formato = st.selectbox("Formato de Redacción", nombres_formatos)
    
    st.markdown("### Integrantes del Equipo")
    st.caption("Tu usuario ya está incluido. Añade el username exacto de tus compañeros.")
    
    # Renderizado dinámico de casillas
    for i in range(len(st.session_state["team_inputs"])):
        st.session_state["team_inputs"][i] = st.text_input(f"Compañero {i+1}", value=st.session_state["team_inputs"][i], key=f"team_{i}")
        
    if st.button("Añadir otro compañero"):
        st.session_state["team_inputs"].append("")
        st.rerun()
        
    if st.button("Siguiente"):
        if titulo and curso:
            # Limpiar lista de vacíos
            usernames_solicitados = [u.strip() for u in st.session_state["team_inputs"] if u.strip()]
            
            # Validación en Base de Datos
            usuarios_encontrados = []
            if usernames_solicitados:
                usuarios_encontrados = db.query(User).filter(User.username.in_(usernames_solicitados)).all()
                nombres_encontrados = [u.username for u in usuarios_encontrados]
                
                faltantes = set(usernames_solicitados) - set(nombres_encontrados)
                if faltantes:
                    st.error(f"Los siguientes usuarios no existen en el sistema: {', '.join(faltantes)}")
                    st.stop()
            
            # Failsafe: Trabajo individual
            is_solo = len(usuarios_encontrados) == 0
            
            # Recolectar IDs (Incluyendo al creador)
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
            st.warning("Completa el título y el curso.")

# ==========================================
# PASO 2: FASES Y EXTRACCIÓN DE CONTEXTO
# ==========================================
elif st.session_state["wizard_step"] == 2:
    st.subheader("Paso 2: Iteraciones y Reglas")
    
    num_fases = st.number_input("Cantidad de fases o entregables", min_value=1, max_value=10, value=st.session_state["draft_project"].get("num_fases", 1))
    
    st.markdown("Si el proyecto tiene múltiples fases, **es obligatorio** subir la rúbrica o sílabo para que el motor IA procese el contexto.")
    archivo_contexto = st.file_uploader("Sube el documento de contexto (PDF)", type=["pdf"])
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Atrás"):
            prev_step()
            st.rerun()
    with col2:
        if st.button("Procesar Contexto", type="primary"):
            if num_fases > 1 and not archivo_contexto:
                st.error("Requisito faltante: Sube el archivo de contexto para procesar múltiples iteraciones.")
            else:
                st.session_state["draft_project"]["num_fases"] = num_fases
                
                if archivo_contexto:
                    temp_dir = os.path.join("data", "uploads", "temp")
                    os.makedirs(temp_dir, exist_ok=True)
                    temp_path = os.path.join(temp_dir, archivo_contexto.name)
                    
                    with open(temp_path, "wb") as f:
                        f.write(archivo_contexto.getbuffer())
                    
                    # Extracción real de texto con PyPDF2
                    texto_extraido = ""
                    try:
                        reader = PyPDF2.PdfReader(temp_path)
                        for page in reader.pages:
                            texto_extraido += page.extract_text() + "\n"
                    except Exception as e:
                        st.error("No se pudo leer el PDF. Asegúrate de que no esté encriptado.")
                        st.stop()
                    
                    st.session_state["draft_project"]["context_file"] = {
                        "name": archivo_contexto.name,
                        "path": temp_path,
                        "extracted_text": texto_extraido.strip()
                    }
                
                next_step()
                st.rerun()

# ==========================================
# PASO 3: PROPUESTA IA Y CONSOLIDACIÓN
# ==========================================
elif st.session_state["wizard_step"] == 3:
    st.subheader("Paso 3: Auditoría y Estructura Propuesta")
    
    texto_contexto = st.session_state["draft_project"].get("context_file", {}).get("extracted_text", "")
    num_fases = st.session_state["draft_project"]["num_fases"]
    
    # Invocación simulada a la IA (Solo corre una vez por sesión en este paso)
    if "ai_proposal" not in st.session_state["draft_project"]:
        with st.spinner("La IA está leyendo el contexto y estructurando las fases..."):
            # Aquí se conecta con ai_client.py. Devuelve un dict con nombres propuestos.
            propuesta_fases = generar_mockup_iteraciones(texto_contexto, num_fases)
            heuristicas = extraer_heuristicas(texto_contexto)
            
            st.session_state["draft_project"]["ai_proposal"] = propuesta_fases
            st.session_state["draft_project"]["ai_heuristics"] = heuristicas

    propuesta = st.session_state["draft_project"]["ai_proposal"]
    
    st.success("Contexto procesado exitosamente.")
    
    if st.session_state["draft_project"]["is_solo"]:
        st.info("Modo individual detectado: Las tareas se asignarán automáticamente a ti.")
    
    st.markdown("### Fases Detectadas")
    for fase in propuesta:
        st.markdown(f"- **{fase['titulo']}**: {fase['descripcion']}")
        
    st.markdown("---")
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("Atrás"):
            # Limpiar propuesta para que recalcule si cambia algo
            st.session_state["draft_project"].pop("ai_proposal", None) 
            prev_step()
            st.rerun()
    with col2:
        if st.button("Confirmar y Crear Proyecto", type="primary"):
            with st.spinner("Ensamblando base de datos..."):
                formato_seleccionado = db.query(FormatTemplate).filter_by(name=st.session_state["draft_project"]["format"]).first()
                
                # Inyección del equipo en la metadata del proyecto
                metadata = {
                    "team_ids": st.session_state["draft_project"]["team_ids"],
                    "is_solo": st.session_state["draft_project"]["is_solo"]
                }
                
                nuevo_proyecto = Project(
                    title=st.session_state["draft_project"]["title"],
                    course=st.session_state["draft_project"]["course"],
                    format_id=formato_seleccionado.id if formato_seleccionado else None,
                    project_metadata=metadata,
                    project_heuristics=st.session_state["draft_project"].get("ai_heuristics", {})
                )
                db.add(nuevo_proyecto)
                db.commit()
                db.refresh(nuevo_proyecto)
                
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
                        processed_data=st.session_state["draft_project"].get("ai_heuristics", {})
                    )
                    db.add(nuevo_archivo)
                
                for fase in propuesta:
                    nueva_iteracion = Iteration(
                        project_id=nuevo_proyecto.id,
                        title=fase["titulo"]
                    )
                    db.add(nueva_iteracion)
                
                db.commit()
                
                st.session_state["wizard_step"] = 1
                st.session_state["draft_project"] = {}
                st.session_state["team_inputs"] = [""]
                st.session_state["current_project_id"] = nuevo_proyecto.id
                
                st.switch_page("pages/3_Workspace.py")