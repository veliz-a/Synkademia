import streamlit as st
import json
import os
from src.database import init_db, get_session, FormatTemplate
from src.auth import login, register, logout

st.set_page_config(page_title="Synkademia", layout="centered")

@st.cache_resource
def setup_db():
    init_db()

setup_db()

# Carga del logo global si el archivo existe
logo_path = os.path.join("assets", "logo.svg")
if os.path.exists(logo_path):
    st.logo(logo_path)

if "authenticated" not in st.session_state:
    st.session_state["authenticated"] = False
if "current_project_id" not in st.session_state:
    st.session_state["current_project_id"] = None

def main():
    if not st.session_state["authenticated"]:
        st.title("Synkademia")
        st.write("Gestión inteligente y edición colaborativa para equipos.")
        
        tab_login, tab_registro = st.tabs(["Iniciar Sesión", "Registrarse"])
        
        with tab_login:
            login_user = st.text_input("Usuario", key="login_input")
            if st.button("Ingresar"):
                if login_user and login(login_user):
                    # Redirección automática al Dashboard
                    st.switch_page("pages/1_Dashboard.py")
                else:
                    st.error("Usuario no encontrado.")
                    
        with tab_registro:
            reg_user = st.text_input("Nuevo Usuario", key="reg_input")
            if st.button("Crear Cuenta"):
                if reg_user and register(reg_user):
                    st.success("Cuenta creada exitosamente.")
                    # Redirección automática al Dashboard
                    st.switch_page("pages/1_Dashboard.py")
                else:
                    st.error("El usuario ya existe o el campo está vacío.")
    else:
        st.title(st.session_state["username"])
        st.write("Selecciona una opción en el menú lateral para comenzar a trabajar en tus proyectos.")
        
        if st.button("Cerrar Sesión"):
            logout()
            st.rerun()

def seed_formatos():
    db = next(get_session())
    formato_existente = db.query(FormatTemplate).filter_by(name="APA 7").first()
    
    if not formato_existente:
        ruta_seed = os.path.join(os.path.dirname(__file__), "src", "seeds", "format_apa7.json")
        try:
            with open(ruta_seed, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            nuevo_formato = FormatTemplate(
                name=data["name"],
                description=data["description"],
                style_rules=data["style_rules"]
            )
            db.add(nuevo_formato)
            db.commit()
            print("Semilla de APA 7 cargada exitosamente.")
        except FileNotFoundError:
            print(f"No se encontró el archivo seed en: {ruta_seed}")

if __name__ == "__main__":
    main()