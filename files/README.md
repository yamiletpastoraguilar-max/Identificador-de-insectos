# 🐞 Identificador de Insectos

App en **Streamlit** que identifica un insecto a partir de una foto y muestra: nombre común y científico,
taxonomía (reino, filo, clase, orden, familia, especie), hábitat, nivel de peligrosidad con precauciones y
primeros auxilios, estado de conservación, estado del ejemplar y cómo devolverlo a su hábitat.

Usa visión por IA (API de Anthropic / Claude).

## Ejecutar localmente
```bash
git clone https://github.com/TU_USUARIO/identificador-insectos.git
cd identificador-insectos
pip install -r requirements.txt
mkdir -p .streamlit && cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# edita secrets.toml y coloca tu ANTHROPIC_API_KEY
streamlit run app.py
```

## Publicar en Streamlit Community Cloud
1. Sube este proyecto a un repositorio de GitHub (ver comandos abajo).
2. Entra a https://share.streamlit.io e inicia sesión con GitHub → **Create app**.
3. Elige el repositorio, rama `main` y archivo principal `app.py`.
4. En **Advanced settings → Secrets** pega:
   ```toml
   ANTHROPIC_API_KEY = "sk-ant-..."
   ```
5. **Deploy**.

## Subir a GitHub
```bash
git init
git add .
git commit -m "Identificador de insectos con Streamlit"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/identificador-insectos.git
git push -u origin main
```
> Nunca subas tu clave: `secrets.toml` ya está en `.gitignore`.

## Aviso
La identificación es orientativa. Ante picaduras con síntomas o dudas sobre la especie, consulta a un médico o especialista.
