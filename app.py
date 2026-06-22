"""
Argos · Doble Check — Procesador de Video
Aenima · Fluxer · Bound  /  Cliente: Paladini Argentina

Uso: streamlit run app.py
"""

import os, json, subprocess, glob, time, shutil, tempfile
import streamlit as st
import whisper
try:
    from groq import Groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
from fpdf import FPDF
from PIL import Image

# ─── Config ──────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Argos · Doble Check",
    page_icon="🎬",
    layout="centered",
    initial_sidebar_state="collapsed",
)

MARGEN = 12.0          # mm
WHISPER_MODEL = "small"   # local fallback si no hay Groq API key
GROQ_MODEL    = "whisper-large-v3"  # API de Groq — mejor calidad, corre en sus servidores

# ─── Session state init ───────────────────────────────────────────────────────
for key in ("pdf_bytes", "txt_bytes", "result_meta", "processed_name"):
    if key not in st.session_state:
        st.session_state[key] = None


# ─── CSS — Estética bound.film ────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=IBM+Plex+Mono:wght@300;400;500&display=swap');

/* Reset base */
html, body, [data-testid="stAppViewContainer"] {
    background-color: #000 !important;
    color: #fff !important;
}
[data-testid="stAppViewContainer"] {
    background-color: #000 !important;
}
[data-testid="stHeader"] {
    background-color: #000 !important;
    border-bottom: 1px solid #1a1a1a;
}
[data-testid="stMain"] {
    background-color: #000 !important;
}
.main .block-container {
    background-color: #000 !important;
    padding-top: 0 !important;
    max-width: 780px;
}

/* Tipografía global */
* { font-family: 'Space Grotesk', sans-serif !important; }
code, pre, .mono { font-family: 'IBM Plex Mono', monospace !important; }

/* ── Header ── */
.argos-header {
    border-bottom: 1px solid #222;
    padding: 36px 0 28px;
    margin-bottom: 48px;
}
.argos-eyebrow {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: #555;
    text-transform: uppercase;
    margin-bottom: 12px;
}
.argos-logo {
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: #fff;
}
.argos-logo span {
    color: #E8FF00;
}
.argos-title {
    font-size: 42px;
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.0;
    color: #fff;
    margin: 16px 0 8px;
}
.argos-subtitle {
    font-size: 14px;
    color: #555;
    letter-spacing: 0.04em;
    font-weight: 400;
}

/* ── Sección ── */
.section-label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: #444;
    text-transform: uppercase;
    margin-bottom: 20px;
    padding-top: 32px;
    border-top: 1px solid #1a1a1a;
}

/* ── Upload zone ── */

/* Ocultar SOLO el botón browse dentro del dropzone — no tocar botones externos */
[data-testid="stFileUploaderDropzone"] button,
[data-testid="stFileUploaderDropzone"] [data-testid="stBaseButton-secondary"],
[data-testid="stFileUploader"] > label,
[data-testid="stWidgetLabel"] {
    display: none !important;
}

[data-testid="stFileUploader"] {
    background: #0a0a0a !important;
    border: 1px solid #222 !important;
    border-radius: 0 !important;
    padding: 4px !important;
}
[data-testid="stFileUploader"]:hover {
    border-color: #E8FF00 !important;
}
[data-testid="stFileUploaderDropzone"] {
    background: transparent !important;
    border: 1px dashed #2a2a2a !important;
    border-radius: 0 !important;
    padding: 28px 20px !important;
    cursor: pointer !important;
    transition: border-color 0.2s !important;
}
[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #E8FF00 !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] {
    display: flex !important;
    flex-direction: column !important;
    align-items: center !important;
    gap: 6px !important;
}
[data-testid="stFileUploaderDropzoneInstructions"] p,
[data-testid="stFileUploaderDropzoneInstructions"] span,
[data-testid="stFileUploaderDropzoneInstructions"] small {
    color: #444 !important;
    font-size: 11px !important;
    font-family: 'IBM Plex Mono', monospace !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}

/* ── Info card ── */
.info-card {
    background: #0d0d0d;
    border: 1px solid #1e1e1e;
    padding: 20px 24px;
    margin: 20px 0;
    display: flex;
    gap: 32px;
}
.info-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
}
.info-label {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px;
    letter-spacing: 0.2em;
    color: #444;
    text-transform: uppercase;
}
.info-value {
    font-size: 15px;
    font-weight: 500;
    color: #fff;
}
.info-value.accent {
    color: #E8FF00;
}

/* ── Timecode barra ── */
.timecode-bar {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px;
    color: #E8FF00;
    letter-spacing: 0.15em;
    background: #0a0a0a;
    border: 1px solid #1e1e1e;
    padding: 10px 16px;
    margin: 8px 0;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.timecode-rec {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: #ff3b3b;
}
.timecode-dot {
    width: 6px;
    height: 6px;
    background: #ff3b3b;
    border-radius: 50%;
    display: inline-block;
    animation: blink 1s step-end infinite;
}
@keyframes blink { 50% { opacity: 0; } }

/* ── Progress ── */
[data-testid="stProgress"] > div > div {
    background: #1a1a1a !important;
    border-radius: 0 !important;
    height: 3px !important;
}
[data-testid="stProgress"] > div > div > div {
    background: #E8FF00 !important;
    border-radius: 0 !important;
}

/* ── Log / status ── */
.log-box {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 11px;
    color: #666;
    background: #050505;
    border: 1px solid #1a1a1a;
    padding: 16px 20px;
    line-height: 2;
    margin: 16px 0;
    max-height: 260px;
    overflow-y: auto;
}
.log-line { color: #555; }
.log-line.done { color: #888; }
.log-line.active {
    color: #E8FF00;
}
.log-line.active::before {
    content: '▶ ';
    color: #E8FF00;
}
.log-line.done::before {
    content: '✓ ';
    color: #2ecc71;
}
.log-line.pending::before {
    content: '· ';
    color: #333;
}

/* ── Botón primario ── */
[data-testid="stButton"] > button {
    background: #E8FF00 !important;
    color: #000 !important;
    border: none !important;
    border-radius: 0 !important;
    font-weight: 700 !important;
    font-size: 12px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 14px 32px !important;
    transition: opacity 0.2s !important;
    width: 100% !important;
}
[data-testid="stButton"] > button:hover {
    opacity: 0.85 !important;
}
[data-testid="stButton"] > button:disabled {
    background: #1a1a1a !important;
    color: #444 !important;
}

/* ── Download button ── */
[data-testid="stDownloadButton"] > button {
    background: transparent !important;
    color: #E8FF00 !important;
    border: 1px solid #E8FF00 !important;
    border-radius: 0 !important;
    font-weight: 600 !important;
    font-size: 11px !important;
    letter-spacing: 0.15em !important;
    text-transform: uppercase !important;
    padding: 12px 24px !important;
    width: 100% !important;
}
[data-testid="stDownloadButton"] > button:hover {
    background: #E8FF00 !important;
    color: #000 !important;
}

/* ── Result card ── */
.result-block {
    border: 1px solid #222;
    padding: 24px;
    margin: 12px 0;
    background: #080808;
}
.result-title {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 10px;
    letter-spacing: 0.2em;
    color: #555;
    text-transform: uppercase;
    margin-bottom: 8px;
}
.result-meta {
    font-size: 22px;
    font-weight: 700;
    color: #fff;
    letter-spacing: -0.01em;
}
.result-sub {
    font-size: 12px;
    color: #444;
    margin-top: 4px;
}

/* ── Footer ── */
.argos-footer {
    margin-top: 80px;
    padding-top: 24px;
    border-top: 1px solid #111;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.footer-left {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px;
    letter-spacing: 0.2em;
    color: #2a2a2a;
    text-transform: uppercase;
}
.footer-right {
    font-family: 'IBM Plex Mono', monospace !important;
    font-size: 9px;
    letter-spacing: 0.15em;
    color: #2a2a2a;
}

/* Ocultar elementos Streamlit que no queremos */
[data-testid="stDecoration"] { display: none !important; }
#MainMenu { display: none !important; }
footer { display: none !important; }
</style>
""", unsafe_allow_html=True)


# ─── Funciones de procesamiento ───────────────────────────────────────────────

def get_video_info(path: str) -> dict:
    cmd = [
        "ffprobe", "-v", "error",
        "-show_entries", "format=duration",
        "-show_entries", "stream=width,height",
        "-select_streams", "v:0",
        "-of", "json", path
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(r.stdout)
    w = int(data["streams"][0]["width"])
    h = int(data["streams"][0]["height"])
    dur = float(data.get("format", {}).get("duration", 0) or 0)
    return {"width": w, "height": h, "duration": dur}


def extract_frames(video_path: str, frames_dir: str):
    os.makedirs(frames_dir, exist_ok=True)
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-vf", "fps=1",
        "-q:v", "2",
        os.path.join(frames_dir, "frame_%04d.jpg"),
        "-hide_banner", "-loglevel", "error", "-y"
    ], check=True)


def extract_audio(video_path: str, audio_path: str):
    subprocess.run([
        "ffmpeg", "-i", video_path,
        "-ac", "1", "-ar", "16000",
        audio_path,
        "-hide_banner", "-loglevel", "error", "-y"
    ], check=True)


def transcribe(audio_path: str) -> tuple[list[dict], str]:
    """
    Transcribe con Groq Whisper large-v3 si hay API key configurada,
    sino cae a Whisper small local.
    Devuelve (segmentos, modelo_usado).
    """
    groq_key = st.secrets.get("GROQ_API_KEY", "") if hasattr(st, "secrets") else ""

    if groq_key and GROQ_AVAILABLE:
        try:
            client = Groq(api_key=groq_key)
            with open(audio_path, "rb") as f:
                response = client.audio.transcriptions.create(
                    file=(os.path.basename(audio_path), f.read()),
                    model=GROQ_MODEL,
                    language="es",
                    response_format="verbose_json",
                    timestamp_granularities=["segment"],
                )
            # Los segmentos pueden venir como objetos o como dicts según la versión del SDK
            segments = []
            for s in response.segments:
                if isinstance(s, dict):
                    segments.append({"start": s["start"], "end": s["end"], "text": s["text"]})
                else:
                    segments.append({"start": s.start, "end": s.end, "text": s.text})
            return segments, f"Groq / {GROQ_MODEL}"
        except Exception as e:
            st.warning(f"⚠️  Groq API error: {e} — usando Whisper small local.")

    # Fallback local
    model = whisper.load_model(WHISPER_MODEL)
    result = model.transcribe(audio_path, language="es", verbose=False)
    return result["segments"], f"Whisper local / {WHISPER_MODEL}"


def build_txt(segments: list[dict], name: str) -> bytes:
    lines = [f"TRANSCRIPCIÓN · {name}\n{'=' * 60}\n\n"]
    lines.append("=== TEXTO COMPLETO ===\n\n")
    lines.append(" ".join(s["text"].strip() for s in segments))
    lines.append("\n\n=== CON TIMESTAMPS ===\n\n")
    for s in segments:
        ini = int(s["start"])
        fin = int(s["end"])
        lines.append(f"[{ini:02d}s - {fin:02d}s] {s['text'].strip()}\n")
    return "".join(lines).encode("utf-8")


def fit_image(iw, ih, aw, ah):
    if iw / ih > aw / ah:
        return aw, aw * ih / iw
    return ah * iw / ih, ah


def build_pdf(frames_dir: str, name: str, vw: int, vh: int, dur: float) -> bytes:
    is_vert = vh > vw
    if is_vert:
        ori, pw, ph = "P", 210.0, 297.0
        ori_str = f"Vertical 9:16 > A4 Portrait"
    else:
        ori, pw, ph = "L", 297.0, 210.0
        ori_str = f"Horizontal 16:9 > A4 Landscape"

    aw, ah = pw - 2 * MARGEN, ph - 2 * MARGEN

    pdf = FPDF(orientation=ori, unit="mm", format="A4")
    pdf.set_auto_page_break(auto=False)
    pdf.set_margins(0, 0, 0)

    # Portada
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 22)
    pdf.set_y(40)
    pdf.set_text_color(0, 0, 0)
    # Franja superior
    pdf.set_fill_color(20, 20, 20)
    pdf.rect(0, 0, pw, 28, "F")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(200, 200, 200)
    pdf.set_xy(MARGEN, 10)
    pdf.cell(pw - 2 * MARGEN, 8, "ARGOS . DOBLE CHECK / AENIMA . FLUXER . BOUND")
    # Cuerpo portada
    pdf.set_text_color(30, 30, 30)
    pdf.set_font("Helvetica", "B", 28)
    pdf.set_xy(MARGEN, 50)
    pdf.multi_cell(pw - 2 * MARGEN, 12, name, align="L")
    pdf.set_font("Helvetica", "", 11)
    pdf.set_text_color(100, 100, 100)
    y = pdf.get_y() + 10
    for label, val in [
        ("Resolucion", f"{vw} x {vh} px"),
        ("Duracion", f"{int(dur)}s"),
        ("Orientacion", ori_str),
        ("Frames", f"{len(sorted(glob.glob(os.path.join(frames_dir, '*.jpg'))))}"),
        ("Modelo Whisper", WHISPER_MODEL.upper()),
        ("Cliente", "Paladini Argentina"),
    ]:
        pdf.set_xy(MARGEN, y)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(160, 160, 160)
        pdf.cell(50, 6, label.upper())
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(60, 60, 60)
        pdf.cell(0, 6, val)
        y += 9

    # Franja inferior portada
    pdf.set_fill_color(20, 20, 20)
    pdf.rect(0, ph - 12, pw, 12, "F")
    pdf.set_font("Helvetica", "", 7)
    pdf.set_text_color(100, 100, 100)
    pdf.set_xy(MARGEN, ph - 9)
    pdf.cell(0, 6, "Archivo generado para uso interno. No distribuir.")

    # Frames
    frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
    for i, fp in enumerate(frames):
        with Image.open(fp) as img:
            fw, fh = img.size
        iw, ih = fit_image(fw, fh, aw, ah)
        x = (pw - iw) / 2
        y = (ph - ih) / 2
        pdf.add_page()
        pdf.image(fp, x=x, y=y, w=iw, h=ih)
        # Franja inferior con timecode
        pdf.set_fill_color(12, 12, 12)
        pdf.rect(0, ph - 10, pw, 10, "F")
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(180, 180, 180)
        pdf.set_xy(MARGEN, ph - 7)
        seg = i + 1
        m, s = seg // 60, seg % 60
        pdf.cell(pw - 2 * MARGEN, 5,
                 f"00:{m:02d}:{s:02d}:00   FRAME {i+1:03d} / {len(frames):03d}   {name}",
                 align="L")

    tmp = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
    pdf.output(tmp.name)
    with open(tmp.name, "rb") as f:
        data = f.read()
    os.unlink(tmp.name)
    return data


# ─── UI ───────────────────────────────────────────────────────────────────────

# Header
st.markdown("""
<div class="argos-header">
  <div class="argos-eyebrow">Aenima · Fluxer · Bound — Sistema QA</div>
  <div class="argos-logo">ARGOS <span>·</span> DOBLE CHECK</div>
  <div class="argos-title">Procesador<br>de Video</div>
  <div class="argos-subtitle">Preparación de assets para análisis de marca — Cliente Paladini Argentina</div>
</div>
""", unsafe_allow_html=True)

# Upload
st.markdown('<div class="section-label">01 · Subir archivo</div>', unsafe_allow_html=True)

mode_col1, mode_col2 = st.columns(2)
with mode_col1:
    st.markdown("""
    <div style="font-family:'IBM Plex Mono',monospace; font-size:9px; letter-spacing:0.2em;
                color:#444; text-transform:uppercase; margin-bottom:8px;">Modo</div>
    """, unsafe_allow_html=True)
    modo = st.radio(
        "modo",
        ["🎬  Video", "🎙  Audio"],
        horizontal=True,
        label_visibility="collapsed"
    )

es_audio = "Audio" in modo

if es_audio:
    uploaded = st.file_uploader(
        "Arrastrá o seleccioná el audio",
        type=["mp3", "wav", "m4a", "aac", "ogg", "flac", "weba", "webm"],
        label_visibility="collapsed"
    )
else:
    uploaded = st.file_uploader(
        "Arrastrá o seleccioná el video de la pieza",
        type=["mp4", "mov", "avi", "mkv", "webm"],
        label_visibility="collapsed"
    )

if uploaded:
    # Guardar en temp
    tmp_dir = tempfile.mkdtemp()
    file_path = os.path.join(tmp_dir, uploaded.name)
    with open(file_path, "wb") as f:
        f.write(uploaded.getbuffer())

    name = os.path.splitext(uploaded.name)[0]
    ext  = os.path.splitext(uploaded.name)[1].lower()

    if es_audio:
        # Para audio: obtener duración con ffprobe
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", file_path],
            capture_output=True, text=True
        )
        try:
            dur = float(r.stdout.strip())
        except:
            dur = 0
        vw, vh = 0, 0
        ori_label = "Audio"
        size_mb = uploaded.size / (1024 * 1024)
        st.markdown(f"""
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">Archivo</span>
            <span class="info-value">{uploaded.name[:32]}{"…" if len(uploaded.name) > 32 else ""}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Duracion</span>
            <span class="info-value">{int(dur)}s</span>
          </div>
          <div class="info-item">
            <span class="info-label">Tamaño</span>
            <span class="info-value">{size_mb:.1f} MB</span>
          </div>
          <div class="info-item">
            <span class="info-label">Formato</span>
            <span class="info-value accent">{ext.upper().replace(".", "")}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Para video: info completa
        video_path = file_path
        info = get_video_info(video_path)
        vw, vh, dur = info["width"], info["height"], info["duration"]
        is_vert = vh > vw
        ori_label = "Vertical 9:16" if is_vert else "Horizontal 16:9"
        st.markdown(f"""
        <div class="info-card">
          <div class="info-item">
            <span class="info-label">Archivo</span>
            <span class="info-value">{uploaded.name[:32]}{"…" if len(uploaded.name) > 32 else ""}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Resolucion</span>
            <span class="info-value">{vw}×{vh}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Duracion</span>
            <span class="info-value">{int(dur)}s</span>
          </div>
          <div class="info-item">
            <span class="info-label">Formato</span>
            <span class="info-value accent">{ori_label}</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-label">02 · Procesar</div>', unsafe_allow_html=True)

    # Si ya procesamos este mismo archivo, saltear y mostrar resultados directamente
    already_done = (
        st.session_state.processed_name == name
        and st.session_state.pdf_bytes is not None
        and st.session_state.txt_bytes is not None
    )

    if not already_done:
        if st.button("▶  INICIAR PROCESAMIENTO"):
            frames_dir = os.path.join(tmp_dir, "frames")
            audio_path = os.path.join(tmp_dir, "audio.wav")

            tc_placeholder = st.empty()
            progress = st.progress(0)
            log_placeholder = st.empty()

            steps = [
                ("Extrayendo frames", "01"),
                ("Extrayendo audio", "02"),
                ("Transcribiendo con Whisper", "03"),
                ("Generando PDF", "04"),
            ]

            def render_log(current: int):
                lines = []
                for i, (label, num) in enumerate(steps):
                    if i < current:
                        cls = "done"
                    elif i == current:
                        cls = "active"
                    else:
                        cls = "pending"
                    lines.append(f'<div class="log-line {cls}">{num} · {label}</div>')
                log_placeholder.markdown(
                    f'<div class="log-box">{"".join(lines)}</div>',
                    unsafe_allow_html=True
                )

            def tick_timecode(frame_n: int, total: int):
                m = frame_n // 60
                s = frame_n % 60
                pct = int((frame_n / max(total, 1)) * 100)
                tc_placeholder.markdown(f"""
                <div class="timecode-bar">
                  <span><span class="timecode-rec"><span class="timecode-dot"></span>REC</span></span>
                  <span>00:{m:02d}:{s:02d}:00</span>
                  <span>{pct}% · {frame_n}/{total} frames</span>
                  <span>4K · 1fps</span>
                </div>
                """, unsafe_allow_html=True)

            if es_audio:
                # ── MODO AUDIO: solo transcribir ──────────────────────────
                steps_audio = [
                    ("Analizando archivo", "01"),
                    ("Transcribiendo con Whisper", "02"),
                    ("Generando TXT", "03"),
                ]

                def render_log_audio(current):
                    lines = []
                    for i, (label, num) in enumerate(steps_audio):
                        cls = "done" if i < current else ("active" if i == current else "pending")
                        lines.append(f'<div class="log-line {cls}">{num} · {label}</div>')
                    log_placeholder.markdown(f'<div class="log-box">{"".join(lines)}</div>', unsafe_allow_html=True)

                render_log_audio(0)
                progress.progress(10)

                # Convertir a WAV si no lo es
                if not file_path.endswith(".wav"):
                    wav_path = os.path.join(tmp_dir, "audio.wav")
                    subprocess.run([
                        "ffmpeg", "-i", file_path,
                        "-ac", "1", "-ar", "16000", wav_path,
                        "-hide_banner", "-loglevel", "error", "-y"
                    ], check=True)
                else:
                    wav_path = file_path

                progress.progress(30)
                render_log_audio(1)
                segments, model_used = transcribe(wav_path)
                progress.progress(75)

                render_log_audio(2)
                txt_bytes = build_txt(segments, name)
                pdf_bytes = None   # no hay PDF en modo audio
                frames = []
                progress.progress(100)

            else:
                # ── MODO VIDEO: pipeline completo ─────────────────────────
                video_path = file_path

                # Paso 1 — Frames
                render_log(0)
                tick_timecode(0, int(dur))
                progress.progress(5)
                extract_frames(video_path, frames_dir)
                frames = sorted(glob.glob(os.path.join(frames_dir, "*.jpg")))
                tick_timecode(len(frames), len(frames))
                progress.progress(25)

                # Paso 2 — Audio
                render_log(1)
                extract_audio(video_path, audio_path)
                progress.progress(40)

                # Paso 3 — Transcripción
                render_log(2)
                segments, model_used = transcribe(audio_path)
                txt_bytes = build_txt(segments, name)
                progress.progress(70)

                # Paso 4 — PDF
                render_log(3)
                pdf_bytes = build_pdf(frames_dir, name, vw, vh, dur)
                progress.progress(100)

            # Guardar en session_state para que persistan entre descargas
            st.session_state.pdf_bytes = pdf_bytes
            st.session_state.txt_bytes = txt_bytes
            st.session_state.processed_name = name
            st.session_state.result_meta = {
                "frames": len(frames),
                "segments": len(segments),
                "ori_label": ori_label,
                "size_pdf": len(pdf_bytes) / (1024 * 1024) if pdf_bytes else 0,
                "size_txt": len(txt_bytes) / 1024,
                "model_used": model_used,
                "es_audio": es_audio,
            }

            # Log y timecode final
            if es_audio:
                log_placeholder.markdown("""
                <div class="log-box">
                  <div class="log-line done">01 · Archivo analizado</div>
                  <div class="log-line done">02 · Transcripción completada</div>
                  <div class="log-line done">03 · TXT generado</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                log_placeholder.markdown("""
                <div class="log-box">
                  <div class="log-line done">01 · Frames extraídos</div>
                  <div class="log-line done">02 · Audio extraído</div>
                  <div class="log-line done">03 · Transcripción completada</div>
                  <div class="log-line done">04 · PDF generado</div>
                </div>
                """, unsafe_allow_html=True)

            tc_placeholder.markdown(f"""
            <div class="timecode-bar" style="border-color:#E8FF00">
              <span style="color:#E8FF00;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0.15em">
                PROCESO COMPLETADO
              </span>
              <span>{len(frames)} frames · {len(segments)} segmentos · {model_used}</span>
              <span>{ori_label}</span>
            </div>
            """, unsafe_allow_html=True)

            shutil.rmtree(tmp_dir, ignore_errors=True)
            st.rerun()

    # ── Bloque de descarga — se muestra tanto post-proceso como al volver ──────
    if st.session_state.pdf_bytes is not None and st.session_state.processed_name == name:
        meta = st.session_state.result_meta

        st.markdown('<div class="section-label">03 · Descargar archivos</div>', unsafe_allow_html=True)

        st.markdown(f"""
        <div class="timecode-bar" style="border-color:#E8FF00; margin-bottom:16px;">
          <span style="color:#E8FF00;font-family:'IBM Plex Mono',monospace;font-size:11px;letter-spacing:0.15em">
            PROCESO COMPLETADO
          </span>
          <span style="font-family:'IBM Plex Mono',monospace;font-size:10px;color:#666;">
            {meta['frames']} frames · {meta['segments']} segmentos · {meta['ori_label']}
          </span>
        </div>
        """, unsafe_allow_html=True)

        if not meta.get("es_audio") and st.session_state.pdf_bytes:
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"""
                <div class="result-block">
                  <div class="result-title">PDF · Frames visuales</div>
                  <div class="result-meta">{meta['frames']} páginas</div>
                  <div class="result-sub">{meta['size_pdf']:.1f} MB · {meta['ori_label']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.download_button(
                    label="↓  DESCARGAR PDF",
                    data=st.session_state.pdf_bytes,
                    file_name=f"{name}_doblecheck.pdf",
                    mime="application/pdf",
                    key="dl_pdf"
                )
            with col2:
                st.markdown(f"""
                <div class="result-block">
                  <div class="result-title">TXT · Transcripción</div>
                  <div class="result-meta">{meta['segments']} segmentos</div>
                  <div class="result-sub">{meta['size_txt']:.1f} KB · {meta['model_used']}</div>
                </div>
                """, unsafe_allow_html=True)
                st.download_button(
                    label="↓  DESCARGAR TXT",
                    data=st.session_state.txt_bytes,
                    file_name=f"{name}_transcripcion.txt",
                    mime="text/plain",
                    key="dl_txt"
                )
        else:
            st.markdown(f"""
            <div class="result-block">
              <div class="result-title">TXT · Transcripción de audio</div>
              <div class="result-meta">{meta['segments']} segmentos</div>
              <div class="result-sub">{meta['size_txt']:.1f} KB · {meta['model_used']}</div>
            </div>
            """, unsafe_allow_html=True)
            st.download_button(
                label="↓  DESCARGAR TRANSCRIPCIÓN",
                data=st.session_state.txt_bytes,
                file_name=f"{name}_transcripcion.txt",
                mime="text/plain",
                key="dl_txt"
            )
        # ── Previsualizadores ─────────────────────────────────────────────────
        st.markdown('<div class="section-label" style="margin-top:32px;">04 · Previsualizar</div>', unsafe_allow_html=True)

        if meta.get("es_audio"):
            # Modo audio — solo transcripción
            st.markdown("""
            <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; color:#444;
                        letter-spacing:0.15em; text-transform:uppercase; margin-bottom:16px;">
              Vista previa · Transcripción con timestamps
            </div>
            """, unsafe_allow_html=True)
            txt_content = st.session_state.txt_bytes.decode("utf-8")
            st.markdown(
                f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:11px; '
                f'color:#888; background:#050505; border:1px solid #1a1a1a; '
                f'padding:20px 24px; line-height:1.9; white-space:pre-wrap; '
                f'max-height:500px; overflow-y:auto;">{txt_content}</div>',
                unsafe_allow_html=True
            )
        else:
            # Modo video — frames + transcripción en tabs
            tab_pdf, tab_txt_container = st.tabs(["🖼  Frames", "📝  Transcripción"])

            if tab_pdf is not None:
                with tab_pdf:
                    st.markdown("""
                    <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; color:#444;
                                letter-spacing:0.15em; text-transform:uppercase; margin-bottom:16px;">
                      Vista previa · Frames extraídos — 1 frame por segundo
                    </div>
                    """, unsafe_allow_html=True)
                    preview_frames = sorted(glob.glob(os.path.join(tmp_dir, "frames", "*.jpg")))
                    if preview_frames:
                        cols_per_row = 3
                        for row_start in range(0, min(len(preview_frames), 30), cols_per_row):
                            row_frames = preview_frames[row_start:row_start + cols_per_row]
                            cols = st.columns(cols_per_row)
                            for col, fp in zip(cols, row_frames):
                                seg_num = int(os.path.splitext(os.path.basename(fp))[0].split("_")[1])
                                m, s = seg_num // 60, seg_num % 60
                                with col:
                                    st.image(fp, use_container_width=True)
                                    st.markdown(
                                        f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:9px; '
                                        f'color:#444; text-align:center; letter-spacing:0.1em; margin-top:4px;">' 
                                        f'00:{m:02d}:{s:02d}:00</div>',
                                        unsafe_allow_html=True
                                    )
                        if len(preview_frames) > 30:
                            st.markdown(
                                f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:10px; '
                                f'color:#444; text-align:center; letter-spacing:0.1em; margin-top:12px;">'
                                f'· · · mostrando 30 de {len(preview_frames)} frames · descargá el PDF para ver todos · · ·</div>',
                                unsafe_allow_html=True
                            )
                    else:
                        st.markdown(
                            '<div style="font-family:\'IBM Plex Mono\',monospace; font-size:11px; color:#444; '
                            'padding:24px; text-align:center;">Los frames temporales ya fueron limpiados. '
                            'Descargá el PDF para ver todos los frames.</div>',
                            unsafe_allow_html=True
                        )

            with tab_txt_container:
                st.markdown("""
                <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; color:#444;
                            letter-spacing:0.15em; text-transform:uppercase; margin-bottom:16px;">
                  Vista previa · Transcripción con timestamps
                </div>
                """, unsafe_allow_html=True)
                txt_content = st.session_state.txt_bytes.decode("utf-8")
                st.markdown(
                    f'<div style="font-family:\'IBM Plex Mono\',monospace; font-size:11px; '
                    f'color:#888; background:#050505; border:1px solid #1a1a1a; '
                    f'padding:20px 24px; line-height:1.9; white-space:pre-wrap; '
                    f'max-height:500px; overflow-y:auto;">{txt_content}</div>',
                    unsafe_allow_html=True
                )

        st.markdown("""
        <div style="margin-top:16px; padding:16px; border:1px solid #1a1a1a; background:#050505; display:flex; justify-content:space-between; align-items:center;">
          <div>
            <span style="font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:0.15em; color:#555; text-transform:uppercase;">
              PRÓXIMO PASO
            </span>
            <p style="font-size:13px; color:#888; margin:6px 0 0; line-height:1.6;">
              Subí el PDF y el TXT al Project <strong style="color:#fff">Argos</strong> en Claude para iniciar el análisis de marca.
            </p>
          </div>
        </div>
        """, unsafe_allow_html=True)

        # Botón para limpiar y procesar otro video
        st.markdown("<div style='margin-top:24px;'>", unsafe_allow_html=True)
        if st.button("✕  LIMPIAR Y PROCESAR OTRO VIDEO"):
            for key in ("pdf_bytes", "txt_bytes", "result_meta", "processed_name"):
                st.session_state[key] = None
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

else:
    # Estado vacío
    st.markdown("""
    <div style="border:1px dashed #1a1a1a; padding:48px; text-align:center; margin:24px 0;">
      <div style="font-family:'IBM Plex Mono',monospace; font-size:10px; letter-spacing:0.2em; color:#333; text-transform:uppercase; margin-bottom:12px;">
        EN ESPERA
      </div>
      <div style="font-size:13px; color:#3a3a3a; line-height:1.7;">
        Subí un video (MP4, MOV, MKV) o un audio (MP3, WAV, M4A) para comenzar.<br>
        El sistema extraerá los frames, transcribirá el audio<br>
        y preparará los archivos para revisión en Claude.
      </div>
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<div class="argos-footer">
  <div class="footer-left">Argos · Doble Check v2026 — Uso interno exclusivo</div>
  <div class="footer-right">Aenima · Fluxer · Bound / AR</div>
</div>
""", unsafe_allow_html=True)