"""
🐞 Identificador de Insectos
Sube una foto y obtén: nombre, taxonomía, hábitat, peligrosidad,
estado de conservación y cómo devolverlo a su hábitat.
Ejecutar: streamlit run app.py
"""
import base64
import io
import json
import re

import streamlit as st
from anthropic import Anthropic
from PIL import Image, ImageOps

st.set_page_config(page_title="Identificador de Insectos", page_icon="🐞", layout="centered")

DEFAULT_MODEL = "claude-sonnet-5-5"
MAX_SIDE = 1568  # px; suficiente detalle y evita imágenes demasiado pesadas

SYSTEM_PROMPT = """Eres un entomólogo experto. Analiza la imagen enviada e identifica el animal.
Responde ÚNICAMENTE con un objeto JSON válido (sin texto extra ni ``` ) con esta estructura exacta:
{
  "es_artropodo_o_insecto": true/false,
  "imagen_clara": true/false,
  "confianza": "alta" | "media" | "baja",
  "nombre_comun": "...",
  "nombre_cientifico": "género y especie (o el nivel taxonómico más preciso posible)",
  "reino": "...", "filo": "...", "clase": "...", "orden": "...", "familia": "...",
  "especie": "...",
  "descripcion": "rasgos que permiten reconocerlo (2-3 frases)",
  "habitat": "hábitat natural, distribución y dieta",
  "peligrosidad": {
    "nivel": "inofensivo" | "precaucion" | "peligroso",
    "detalle": "por qué (picadura, veneno, vectores de enfermedades, plaga, etc.)",
    "precauciones": ["lista de recomendaciones al encontrarlo"],
    "primeros_auxilios": "qué hacer si pica/muerde (o 'No aplica')"
  },
  "estado_conservacion": "categoría UICN si se conoce (p. ej. Preocupación menor, No evaluada, Amenazada) y tendencia poblacional",
  "estado_ejemplar": "estado visible del ejemplar en la foto: vivo/activo, inmóvil, herido, muerto, en muda, etapa de vida (larva, pupa, adulto)",
  "como_devolverlo_al_habitat": ["pasos concretos y seguros para liberarlo donde corresponde"],
  "datos_curiosos": "un dato interesante",
  "notas": "advertencias sobre la identificación, especies parecidas con las que se puede confundir"
}
Reglas: sé honesto con la incertidumbre; si la foto no muestra un insecto o artrópodo, pon
"es_artropodo_o_insecto": false y explica en "notas". Si la especie exacta no puede
determinarse, indica el género o familia más probable y confianza baja. Responde en español.
Ante la duda sobre peligrosidad, recomienda precaución (no manipular con las manos desnudas)."""

NIVELES = {
    "inofensivo": ("🟢 Inofensivo", st.success),
    "precaucion": ("🟡 Tener precaución", st.warning),
    "peligroso": ("🔴 Peligroso", st.error),
}


@st.cache_resource
def get_client() -> Anthropic | None:
    key = None
    try:
        key = st.secrets["ANTHROPIC_API_KEY"]
    except Exception:
        import os
        key = os.environ.get("ANTHROPIC_API_KEY")
    return Anthropic(api_key=key) if key else None


def prepare_image(file) -> tuple[str, Image.Image]:
    """Corrige orientación, reduce tamaño y devuelve (base64 JPEG, imagen PIL)."""
    img = Image.open(file)
    img = ImageOps.exif_transpose(img).convert("RGB")
    img.thumbnail((MAX_SIDE, MAX_SIDE))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=90)
    return base64.standard_b64encode(buf.getvalue()).decode(), img


def parse_json(text: str) -> dict:
    text = text.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.MULTILINE).strip()
    start, end = text.find("{"), text.rfind("}")
    return json.loads(text[start : end + 1])


def identify(client: Anthropic, b64: str, contexto: str) -> dict:
    try:
        model = st.secrets["MODEL"]
    except Exception:
        model = DEFAULT_MODEL
    pregunta = "Identifica este animal y entrega el JSON solicitado."
    if contexto.strip():
        pregunta += f" Contexto del usuario (lugar/observaciones): {contexto.strip()}"
    msg = client.messages.create(
        model=model,
        max_tokens=2000,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": b64}},
                {"type": "text", "text": pregunta},
            ],
        }],
    )
    return parse_json("".join(b.text for b in msg.content if b.type == "text"))


def bullets(items):
    if isinstance(items, str):
        items = [items]
    for i in items or []:
        st.markdown(f"- {i}")


def show_result(r: dict):
    if not r.get("es_artropodo_o_insecto", True):
        st.warning("No parece haber un insecto o artrópodo en la imagen.")
        st.write(r.get("notas", ""))
        return
    if not r.get("imagen_clara", True):
        st.info("📷 La imagen no es muy clara; el resultado puede ser poco preciso.")

    st.header(r.get("nombre_comun", "Desconocido"))
    st.caption(f"*{r.get('nombre_cientifico', '—')}* · Confianza: **{r.get('confianza', '—')}**")
    st.write(r.get("descripcion", ""))

    p = r.get("peligrosidad", {})
    etiqueta, caja = NIVELES.get(p.get("nivel", "precaucion"), NIVELES["precaucion"])
    caja(f"**{etiqueta}** — {p.get('detalle', '')}")

    tab1, tab2, tab3, tab4 = st.tabs(["🧬 Taxonomía", "🌿 Hábitat y estado", "⚠️ Cuidados", "🏡 Devolverlo a su hábitat"])
    with tab1:
        c1, c2 = st.columns(2)
        c1.metric("Reino", r.get("reino", "—"))
        c2.metric("Especie", r.get("especie", "—"))
        st.table({
            "Nivel": ["Filo", "Clase", "Orden", "Familia"],
            "Valor": [r.get("filo", "—"), r.get("clase", "—"), r.get("orden", "—"), r.get("familia", "—")],
        })
    with tab2:
        st.subheader("Hábitat")
        st.write(r.get("habitat", "—"))
        st.subheader("Estado de conservación")
        st.write(r.get("estado_conservacion", "—"))
        st.subheader("Estado del ejemplar en la foto")
        st.write(r.get("estado_ejemplar", "—"))
    with tab3:
        st.subheader("Precauciones")
        bullets(p.get("precauciones"))
        st.subheader("Primeros auxilios")
        st.write(p.get("primeros_auxilios", "No aplica"))
    with tab4:
        bullets(r.get("como_devolverlo_al_habitat"))

    if r.get("datos_curiosos"):
        st.info(f"💡 {r['datos_curiosos']}")
    if r.get("notas"):
        st.caption(f"Notas: {r['notas']}")
    st.caption("⚠️ Identificación asistida por IA: puede equivocarse. Ante una picadura o mordedura "
               "con síntomas, o si dudas de la especie, consulta a un médico o a un especialista.")


# ------------------------------- Interfaz -------------------------------
st.title("🐞 Identificador de Insectos")
st.write("Sube o toma una foto de un insecto y descubre qué es, si es peligroso y cómo devolverlo a su hábitat.")

client = get_client()
if client is None:
    st.error("Falta la clave `ANTHROPIC_API_KEY`. Configúrala en *Secrets* (ver README).")
    st.stop()

modo = st.radio("Origen de la imagen", ["📁 Subir archivo", "📷 Usar cámara"], horizontal=True)
archivo = (st.file_uploader("Imagen del insecto", type=["jpg", "jpeg", "png", "webp"])
           if modo.startswith("📁") else st.camera_input("Toma la foto"))
contexto = st.text_input("Lugar u observaciones (opcional)", placeholder="Ej.: encontrado en el jardín, Tacna, Perú")

if archivo:
    b64, img = prepare_image(archivo)
    st.image(img, caption="Imagen a analizar", use_container_width=True)
    if st.button("🔍 Identificar", type="primary", use_container_width=True):
        with st.spinner("Analizando la imagen..."):
            try:
                st.session_state["resultado"] = identify(client, b64, contexto)
            except json.JSONDecodeError:
                st.error("No pude interpretar la respuesta. Intenta de nuevo con otra foto.")
            except Exception as e:
                st.error(f"Error al consultar el modelo: {e}")

if "resultado" in st.session_state and archivo:
    st.divider()
    show_result(st.session_state["resultado"])
