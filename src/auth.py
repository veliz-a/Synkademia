import streamlit as st
from src.database import User, get_session

def login(username: str) -> bool:
    """Verifica si el usuario existe y guarda sus datos en sesión."""
    db = next(get_session())
    user = db.query(User).filter(User.username == username).first()
    
    if user:
        st.session_state["user_id"] = user.id
        st.session_state["username"] = user.username
        st.session_state["authenticated"] = True
        return True
    return False

def register(username: str) -> bool:
    """Crea un nuevo usuario y lo loguea automáticamente."""
    if not username.strip():
        return False
        
    db = next(get_session())
    if db.query(User).filter(User.username == username).first():
        return False 
        
    new_user = User(username=username)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    st.session_state["user_id"] = new_user.id
    st.session_state["username"] = new_user.username
    st.session_state["authenticated"] = True
    return True

def logout():
    """Limpia el estado de la sesión."""
    st.session_state.clear()
    st.session_state["authenticated"] = False