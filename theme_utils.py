import base64
from pathlib import Path
from string import Template

import streamlit as st

ROOT_DIR = Path(__file__).resolve().parent
BACKGROUND_IMAGE = ROOT_DIR / "WhatsApp Image 2025-11-13 at 19.26.30.jpeg"


def load_roll_image_b64() -> str | None:
    if BACKGROUND_IMAGE.exists():
        try:
            return base64.b64encode(BACKGROUND_IMAGE.read_bytes()).decode("utf-8")
        except Exception:
            st.warning("No pude cargar la imagen de referencia. Verifica el archivo JPG.")
    return None


def apply_portada_theme() -> None:
    image_b64 = load_roll_image_b64()
    bg_layer = ""
    if image_b64:
        bg_layer = Template(
            """
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image: url("data:image/jpeg;base64,$b64");
            background-size: cover;
            background-position: center;
            opacity: 0.55;
            z-index: -2;
        }
        """
        ).substitute(b64=image_b64)

    st.markdown(
        f"""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600&family=Inter:wght@400;500&display=swap');
        :root {{
            --page-bg: #eff6dd;
            --page-border: #6b7c36;
            --page-panel: #9ab66d;
            --page-text: #1b1d12;
        }}

        body, .stApp {{
            font-family: 'Inter', sans-serif;
            background: var(--page-bg);
            color: var(--page-text);
        }}

        {bg_layer}

        [data-testid="stAppViewContainer"] {{
            background: linear-gradient(90deg, rgba(239,246,221,0.92), rgba(214,236,189,0.65));
        }}

        .section-card {{
            background: rgba(255, 255, 255, 0.85);
            border: 1px solid rgba(107,124,54,0.35);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 10px 24px rgba(0,0,0,0.08);
        }}

        .hero-eyebrow {{
            letter-spacing: 0.45rem;
            font-size: 0.9rem;
            text-transform: uppercase;
            color: #5E7D52;
        }}

        .hero-title {{
            font-family: 'Playfair Display', serif;
            font-size: clamp(2.2rem, 4vw, 3.5rem);
            letter-spacing: 0.3rem;
            color: #141414;
            margin-bottom: 0.3rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(title: str, subtitle: str, show_roll: bool = False) -> None:
    if show_roll and BACKGROUND_IMAGE.exists():
        col_text, col_image = st.columns([2, 1], gap="large")
    else:
        col_text, col_image = st.container(), None

    with col_text:
        st.markdown(
            f"""
            <div>
                <div class="hero-eyebrow">Fácil y rápido</div>
                <div class="hero-title">{title.upper()}</div>
                <p style="color:rgba(20,20,20,0.75);font-size:1rem;max-width:520px;">{subtitle}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if col_image:
        with col_image:
            st.image(
                BACKGROUND_IMAGE.as_posix(),
                caption="",
                use_container_width=True,
                output_format="JPEG",
            )
