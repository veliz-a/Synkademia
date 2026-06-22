import os
from datetime import datetime
from typing import List, Optional
from sqlalchemy import create_engine, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "synkademia.db")
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False)

class Base(DeclarativeBase):
    pass

SessionLocal = sessionmaker(bind=engine)

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String, unique=True, index=True)
    orcid: Mapped[Optional[str]] = mapped_column(String) # Clave para formatos como APA 7
    
    tasks: Mapped[List["Task"]] = relationship(back_populates="assignee")

class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String)
    course: Mapped[str] = mapped_column(String)
    format_style: Mapped[str] = mapped_column(String, default="APA 7")
    institution: Mapped[Optional[str]] = mapped_column(String) # Requerido para portadas
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relaciones
    contexts: Mapped[List["ProjectContext"]] = relationship(back_populates="project", cascade="all, delete-orphan")
    iterations: Mapped[List["Iteration"]] = relationship(back_populates="project", cascade="all, delete-orphan")

class ProjectContext(Base):
    """Almacena la base de conocimiento empírica (sílabos, rúbricas, papers) para la IA."""
    __tablename__ = "project_contexts"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    filename: Mapped[str] = mapped_column(String)
    extracted_text: Mapped[str] = mapped_column(Text) # El texto crudo que consumirá Gemini
    uploaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship(back_populates="contexts")

class Iteration(Base):
    """Agrupa las tareas en fases lógicas (ej. 'Iteración 1: Estado del Arte')."""
    __tablename__ = "iterations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    title: Mapped[str] = mapped_column(String) # La IA generará este título
    status: Mapped[str] = mapped_column(String, default="pending") # pending, active, completed
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    project: Mapped["Project"] = relationship(back_populates="iterations")
    tasks: Mapped[List["Task"]] = relationship(back_populates="iteration", cascade="all, delete-orphan")
    snapshots: Mapped[List["Snapshot"]] = relationship(back_populates="iteration", cascade="all, delete-orphan")

class Task(Base):
    """La unidad de contenido. Ya no se liga al proyecto directo, sino a una iteración."""
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    iteration_id: Mapped[int] = mapped_column(ForeignKey("iterations.id"))
    assignee_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    
    title: Mapped[str] = mapped_column(String)
    status: Mapped[str] = mapped_column(String, default="pending") 
    content: Mapped[Optional[str]] = mapped_column(Text, default="") 
    ai_instructions: Mapped[Optional[str]] = mapped_column(Text) # Comentarios invisibles para guiar al redactor

    iteration: Mapped["Iteration"] = relationship(back_populates="tasks")
    assignee: Mapped[Optional["User"]] = relationship(back_populates="tasks")

class Snapshot(Base):
    """Guarda las versiones finales/entregables de cada iteración."""
    __tablename__ = "snapshots"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    iteration_id: Mapped[int] = mapped_column(ForeignKey("iterations.id"))
    file_path: Mapped[str] = mapped_column(String) # Ruta del archivo final exportado (DOCX/PDF)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    iteration: Mapped["Iteration"] = relationship(back_populates="snapshots")

def init_db():
    Base.metadata.create_all(bind=engine)

def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()