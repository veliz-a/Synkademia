import os
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Configuración de la base de datos (archivo local en la raíz para el MVP)

# 1. Obtiene la ruta absoluta del archivo actual (src/database.py)
# 2. Sube un nivel al directorio padre (la carpeta raíz del proyecto)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 3. Une la ruta base con el nombre del archivo de la base de datos
DB_PATH = os.path.join(BASE_DIR, "synkademia.db")

engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

Base = declarative_base()
SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    
    # Relación bidireccional con las tareas
    tasks = relationship("Task", back_populates="assignee")

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    work_type = Column(String, nullable=False) # ej. Ensayo, Informe, Caso de estudio
    course = Column(String, nullable=False)
    deadline = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")

class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False) # ej. "Introducción", "Marco Teórico"
    status = Column(String, default="pending") # pending, in_progress, completed
    content = Column(Text, default="") # Almacena el texto co-editado de esta sección

    project_id = Column(Integer, ForeignKey("projects.id"))
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    project = relationship("Project", back_populates="tasks")
    assignee = relationship("User", back_populates="tasks")

def init_db():
    """Crea las tablas en la base de datos si no existen."""
    Base.metadata.create_all(bind=engine)

def get_session():
    """Generador para proveer una sesión transaccional."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()