# Argos · Doble Check

**Sistema de QA asistido por IA** — Aenima · Fluxer · Bound  
Procesador de video para análisis de marca. Cliente: Paladini Argentina.

Extrae frames y transcribe el audio de una pieza para preparar los archivos para revisión en el Project Argos de Claude.

---

## Stack

- **Streamlit** — interfaz web
- **FFmpeg** — extracción de frames y audio
- **Groq Whisper large-v3** — transcripción (API, sin costo de RAM)
- **Whisper small** — fallback local si no hay API key
- **fpdf2 + Pillow** — generación de PDF con frames

---

## Setup local

### 1. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 2. Variables de entorno (opcional)

```bash
export GROQ_API_KEY="gsk_..."
```

O ingresarlas directamente en la app al correrla.

### 3. Correr la app

```bash
streamlit run app.py
```

---

## Deploy en Streamlit Cloud

1. Subí el repo a GitHub
2. Conectalo en [share.streamlit.io](https://share.streamlit.io)
3. Configurá los secrets en la app:

```toml
GROQ_API_KEY = "gsk_..."
```

---

## Estructura

```
argos-doblecheck/
├── app.py                  # UI principal (Streamlit)
├── requirements.txt        # Dependencias Python
├── packages.txt            # Dependencias del sistema (FFmpeg)
└── .streamlit/
    └── config.toml         # Configuración tema y límites
```

---

## Qué genera

Por cada video procesado se producen dos archivos listos para subir al Project Argos en Claude:

| Archivo | Contenido |
|---|---|
| `[nombre]_doblecheck.pdf` | Un frame por página, orientación automática 9:16 o 16:9, timecode por página |
| `[nombre]_transcripcion.txt` | Texto completo + segmentos con timestamps `[00s - 05s]` |

---

## Límites (Streamlit Cloud free tier)

| Recurso | Límite |
|---|---|
| RAM | 1 GB (por eso Whisper local usa `small`) |
| Upload | 500 MB por archivo |
| Groq free tier | ~28.800s de audio/día (~960 videos de 30s) |

---

*Uso interno exclusivo — Aenima · Fluxer · Bound / AR*
