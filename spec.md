# SEC 10-K Autonomous Risk Analyzer (MAS)

## 1. Visión Ejecutiva ("Outcomes over noise")
Este repositorio es una demostración de grado empresarial de un **Sistema Multi-Agente (MAS)** diseñado para el sector financiero. No es un simple "chat con un PDF". Es un pipeline autónomo que automatiza el proceso de "Due Diligence", extrayendo y validando factores de riesgo de reportes financieros públicos (SEC 10-K) con una tasa de alucinaciones controlada matemáticamente.

**Objetivo Comercial:** Reducir el ciclo de auditoría de riesgo de 3 semanas a minutos, manteniendo un control humano sobre las decisiones críticas (Human-in-the-loop) y garantizando la privacidad de los datos.

---

## 2. Arquitectura del Sistema (Tech Stack)

El proyecto está diseñado de forma modular (agnóstica) para permitir una ejecución 100% local o escalable en la nube.

* **Data Ingestion:** API pública EDGAR de la SEC (descarga automatizada de formularios 10-K).
* **Orquestación Core:** LangChain.
* **Orquestación Multi-Agente:** LangGraph (Patrón de Línea de Ensamblaje / Pipeline Secuencial).
* **Embeddings & Vector DB:** HuggingFace Embeddings + ChromaDB (Local) / Pinecone (Cloud).
* **LLM Engine:** Ollama corriendo Llama-3/Mistral (Local) / OpenAI API o Anthropic Claude (Cloud).
* **Observabilidad & Evals:** LangSmith (para trazar contextos, evaluar *Faithfulness* y prevenir alucinaciones).
* **Interfaz de Usuario (UI) & Tracking:** Streamlit. Se utiliza para visualizar el flujo de estado de LangGraph, rastrear qué agente está ejecutando su tarea y gestionar la aprobación humana (Human-in-the-loop).

---

## 3. Diseño del Grafo (Multi-Agent Flow)

El sistema opera bajo un grafo de estados (`StateGraph`) donde cada nodo es un agente especializado:

1.  **Data Fetcher Node:** Se conecta a la SEC, descarga el último 10-K de la empresa solicitada (ej. AAPL) y vectoriza la sección de "Risk Factors".
2.  **Risk Extractor Agent (Nodo 1):** Consulta la base de datos vectorial (RAG) y extrae exclusivamente los 5 riesgos financieros, operativos o legales más críticos.
3.  **Compliance Auditor Agent (Nodo 2):** Recibe los riesgos extraídos, los contrasta contra una política de inversión simulada y marca alertas rojas (ej. "Alta exposición a litigios").
4.  **Human-in-the-loop (Pausa del Grafo):** El grafo se detiene. A través de la UI en Streamlit, el usuario revisa el análisis parcial y aprueba la generación del reporte final o pide re-evaluación.
5.  **Executive Summarizer (Nodo 3):** Toma los datos auditados y aprobados, y redacta un veredicto final estructurado para la junta directiva.

---

## 4. Estructura del Repositorio

A continuación se detalla la estructura de carpetas recomendada para mantener el estándar de producción:

* `data/` -> Almacenamiento temporal de PDFs o TXTs descargados.
* `vector_store/` -> Persistencia local de ChromaDB.
* `src/` -> Código fuente principal.
    * `ingestion.py` -> Script para conectar con la API de la SEC y poblar la Vector DB.
    * `agents.py` -> Definición de los prompts y herramientas de cada agente.
    * `graph.py` -> Construcción del `StateGraph` de LangGraph (nodos, edges y puntos de interrupción).
    * `evals.py` -> Scripts de LangSmith para medir la fidelidad de las respuestas.
* `app.py` -> Aplicación principal de Streamlit (Frontend y tracking del estado del grafo).
* `.env.example` -> Variables de entorno (`OPENAI_API_KEY`, `LANGSMITH_API_KEY`, flags para modelo local/cloud).
* `requirements.txt` -> Dependencias de Python.

---

## 5. Guía de Implementación (Fases de Desarrollo)

**Fase 1: Configuración de Datos (Ingesta)**
* Implementar `ingestion.py` para descargar un reporte 10-K específico usando librerías como `sec-edgar-downloader`.
* Utilizar `RecursiveCharacterTextSplitter` de LangChain para fragmentar el texto.
* Almacenar los fragmentos en ChromaDB local.

**Fase 2: Construcción de Agentes y Grafo**
* Definir el `TypedDict` que servirá como el Estado global del grafo (ej. `empresa`, `riesgos_extraidos`, `auditoria`, `aprobado`).
* Codificar cada nodo en `graph.py` y conectar los flujos lógicos.
* Añadir el punto de interrupción (`interrupt_before=["Executive_Summarizer"]`).

**Fase 3: Observabilidad y Evals (El Diferenciador)**
* Conectar el proyecto a LangSmith configurando las variables de entorno.
* Crear un dataset de prueba en LangSmith con preguntas como "¿Cuáles son los riesgos de cadena de suministro de Apple?" y configurar evaluadores automáticos para medir que la IA no invente respuestas.

**Fase 4: Interfaz Web y Control de Estado (Streamlit)**
* En `app.py`, construir una barra lateral para ingresar el Ticker de la empresa (ej. TSLA).
* Implementar contenedores interactivos (`st.status` o `st.spinner`) para mostrar en pantalla: "Agente Extractor trabajando...", "Agente Auditor evaluando...".
* Utilizar el método `graph.get_state(config)` para detener la UI y mostrar botones de `Aprobar Reporte` o `Rechazar`, manejando la continuación del grafo mediante `graph.update_state`.

---

## 6. Ejecución Local

Para ejecutar este proyecto en tu máquina:

1. Clona el repositorio.
2. Instala las dependencias: `pip install -r requirements.txt`
3. Copia `.env.example` a `.env` y configura tus variables.
4. (Opcional) Levanta el motor de Ollama si decides usar la configuración 100% local.
5. Ejecuta la interfaz: `streamlit run app.py`