import json
import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader

# 1. Configuración de la página
st.set_page_config(
    page_title="CV Boost AI | Optimización de CVs",
    page_icon="🚀",
    layout="wide"
)

# 2. Título y descripción
st.title("🚀 CV Boost AI — Optimización de CVs con Inteligencia Artificial")
st.markdown("""
Esta herramienta analiza tu Currículum Vitae, mide la compatibilidad con el puesto de trabajo al que querés postular 
y genera una versión optimizada redactada para superar los filtros ATS.
""")

st.divider()

# 3. Sidebar: Configuración de API Key
st.sidebar.header("⚙️ Configuración")
api_key = st.sidebar.text_input("Ingresá tu Gemini API Key:", type="password")
st.sidebar.caption("Obtené tu API Key gratuita en Google AI Studio (aistudio.google.com).")

# 4. Formulario de Inputs del Usuario
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("1️⃣ Puesto Objetivo")
    puesto_objetivo = st.text_input(
        "¿A qué rol o puesto querés postular?",
        placeholder="Ej: Analista Financiero / Data Analyst"
    )

with col2:
    st.subheader("2️⃣ Tu CV Actual")
    opcion_input = st.radio("Seleccioná la forma de ingresar tu CV:", ["Pegar texto", "Subir PDF"])
    
    texto_cv = ""
    if opcion_input == "Pegar texto":
        texto_cv = st.text_area("Pega aquí el contenido de tu CV:", height=200)
    else:
        archivo_pdf = st.file_uploader("Cargá tu archivo CV en formato PDF", type=["pdf"])
        if archivo_pdf is not None:
            try:
                reader = PdfReader(archivo_pdf)
                for page in reader.pages:
                    texto_cv += page.extract_text() + "\n"
                st.success("✅ PDF leído correctamente.")
            except Exception as e:
                st.error(f"Error al procesar el archivo PDF: {e}")

st.divider()

# Botón principal para ejecutar el análisis
btn_procesar = st.button("✨ Procesar y Optimizar CV", type="primary", use_container_width=True)

# 5. Funciones de IA con la API de Google Gemini
def evaluar_cv(client, puesto, cv):
    prompt_evaluacion = f"""
    Sos un reclutador senior y especialista en sistemas ATS. Analiza el siguiente CV en relación con el puesto objetivo indicado y genera una evaluación en formato JSON estructurado.

    PUESTO OBJETIVO: {puesto}
    TEXTO DEL CV: {cv}

    INSTRUCCIONES DE SALIDA:
    Devuelve ÚNICAMENTE un objeto JSON con la siguiente estructura exacta:
    {{
      "score_compatibilidad": (número entero del 0 al 100),
      "puntos_fuertes": [(lista de 3 aspectos destacados)],
      "palabras_clave_faltantes": [(lista de palabras clave imprescindibles que faltan)],
      "critica_constructiva": [(lista de 3 recomendaciones concretas)]
    }}
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_evaluacion,
        config=types.GenerateContentConfig(
            response_mime_type="application/json"
        )
    )
    return json.loads(response.text)

def optimizar_cv(client, puesto, cv, palabras_clave):
    prompt_optimizacion = f"""
    Sos un redactor profesional de currículums enfocado en destacar logros e impacto. Genera una versión optimizada del currículum adaptada al puesto objetivo.

    PUESTO OBJETIVO: {puesto}
    CV ORIGINAL: {cv}
    PALABRAS CLAVE A INTEGRAR: {', '.join(palabras_clave)}

    REGLAS DE REESCRITURA:
    - Usá verbos de acción fuertes al inicio de las viñetas.
    - Aplicá la fórmula: [Verbo de Acción] + [Tarea/Herramienta] + [Resultado/Impacto].
    - Estructura la salida en formato Markdown claro con las secciones:
      # Perfil Profesional
      # Experiencia Laboral
      # Habilidades Clave
      # Educación
    """
    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt_optimizacion
    )
    return response.text

# 6. Lógica de Ejecución
if btn_procesar:
    if not api_key:
        st.error("⚠️ Por favor, ingresá tu Gemini API Key en el panel lateral para continuar.")
    elif not puesto_objetivo:
        st.warning("⚠️ Debes ingresar el Puesto Objetivo.")
    elif not texto_cv.strip():
        st.warning("⚠️ Debes ingresar o cargar el texto de tu CV.")
    else:
        try:
            client = genai.Client(api_key=api_key)
            
            with st.spinner("🤖 Analizando compatibilidad y procesando datos con Gemini IA..."):
                # Paso 1: Evaluación
                resultado_eval = evaluar_cv(client, puesto_objetivo, texto_cv)
                
                # Paso 2: Reescritura/Optimización
                cv_optimizado = optimizar_cv(
                    client, 
                    puesto_objetivo, 
                    texto_cv, 
                    resultado_eval.get("palabras_clave_faltantes", [])
                )
            
            st.success("🎉 ¡Análisis y optimización completados con éxito!")
            
            # 7. Despliegue de Resultados en la Interfaz
            tab1, tab2 = st.tabs(["📊 Reporte de Evaluación", "📄 CV Optimizado"])
            
            with tab1:
                st.metric(
                    label="Score de Compatibilidad ATS", 
                    value=f"{resultado_eval.get('score_compatibilidad', 0)} / 100"
                )
                
                col_a, col_b = st.columns(2)
                with col_a:
                    st.subheader("💪 Puntos Fuertes")
                    for pf in resultado_eval.get("puntos_fuertes", []):
                        st.write(f"- {pf}")
                        
                    st.subheader("🔑 Palabras Clave Faltantes")
                    for pk in resultado_eval.get("palabras_clave_faltantes", []):
                        st.write(f"- `{pk}`")
                        
                with col_b:
                    st.subheader("💡 Oportunidades de Mejora")
                    for rec in resultado_eval.get("critica_constructiva", []):
                        st.write(f"- {rec}")
                        
            with tab2:
                st.subheader("📝 Versión Optimizada para ATS")
                st.markdown(cv_optimizado)
                
                st.download_button(
                    label="📥 Descargar CV Optimizado (.md)",
                    data=cv_optimizado,
                    file_name="CV_Optimizado_AI.md",
                    mime="text/markdown"
                )

        except Exception as e:
            st.error(f"Ocurrió un error durante la ejecución: {e}")
