# Synkademia

**Motor de Orquestación y Auditoría de Documentos Académicos**

Synkademia es una plataforma diseñada para automatizar la gestión, estructuración y cumplimiento de formatos en trabajos universitarios. A diferencia de un simple editor de texto, Synkademia actúa como un orquestador que extrae reglas de evaluación (heurísticas) directamente de rúbricas o sílabos utilizando Inteligencia Artificial local, asegurando que los equipos cumplan con los requisitos antes de la fase de redacción.

## Alcance del MVP (Fase Actual)

El desarrollo actual se centra en la arquitectura de datos, la extracción de contexto y la gestión de proyectos. 

**Módulos Funcionales:**
* **Dashboard de Proyectos:** Vista centralizada de los espacios de trabajo activos y gestión de acceso basada en autenticación local.
* **Asistente de Creación (Wizard) con IA:** Flujo de configuración de múltiples pasos que incluye:
    * Validación dinámica de integrantes del equipo en base de datos.
    * Procesamiento de documentos PDF (rúbricas/sílabos) mediante `pdfplumber`.
    * Auditoría de contexto offline mediante modelos locales (Ollama) para extraer heurísticas críticas (límites de palabras, secciones obligatorias, formato).
* **Workspace (Centro de Control):** Panel de administración del proyecto donde se consolidan las iteraciones de trabajo, los metadatos institucionales y el checklist de heurísticas exigidas.

**Módulos en Vista Previa (Visual/Mockup):**
* **Editor Híbrido:** Interfaz que proyecta la separación entre el lienzo de redacción (Markdown) y el panel de asistencia/auditoría.
* **Motor de Exportación:** Proyección del ensamblaje automatizado del documento final (inyección de reglas APA, portadas automáticas).

## Stack Tecnológico

* **Frontend / UI:** Streamlit (Configurado con perfil estricto minimalista/editorial).
* **Backend / ORM:** Python 3.10+, SQLAlchemy 2.0 (Tipado estricto moderno).
* **Base de Datos:** SQLite (Estructura relacional con campos JSON para metadatos polimórficos).
* **Procesamiento de Documentos:** `pdfplumber` para mapeo de texto estructurado.
* **Inteligencia Artificial:** * Motor local: Ollama (`qwen2.5:7b`).
    * Estructuración de datos: Pydantic (Structured Outputs forzando esquemas JSON).

## Flujo de uso de LLM
PDF
  ↓
LLM (exploración libre)
  ↓
Normalizador (estructura fija)
  ↓
Validador (reglas lógicas)
  ↓
Sistema final (proyecto)

## Arquitectura de Directorios

El proyecto mantiene una separación estricta entre el código lógico, los datos estructurales y los binarios subidos por los usuarios:

```text
synkademia/
├── .streamlit/             # Configuración de interfaz UI (Tema claro, minimalista)
├── data/                   # Almacenamiento local persistente (Ignorado en git)
│   ├── db/                 # Base de datos SQLite (synkademia.db)
│   └── uploads/            # Directorios dinámicos de contexto y rúbricas (project_id)
├── pages/                  # Vistas de la aplicación (Enrutamiento Streamlit)
├── src/                    # Lógica de negocio y abstracción de datos
│   ├── config.py.py        # Datos de conexión local estructurada con Ollama
│   ├── auth.py             # Gestión de sesiones y acceso
│   └── database.py         # Modelos SQLAlchemy 2.0 y conexión a SQLite
│   ├── llm/ai_client.py    # Config de LLM, definicion de chat
│   └── core/heuristicas.py # Definicion de funciones custom
├── app.py                  # Punto de entrada y Login
└── requirements.txt        # Dependencias del entorno