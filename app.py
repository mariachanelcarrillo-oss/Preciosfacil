import base64
from pathlib import Path
from string import Template

import streamlit as st
from streamlit_extras.stylable_container import stylable_container
from streamlit_extras.switch_page_button import switch_page

# pip install streamlit streamlit-extras

st.set_page_config(page_title="Precios - Facil y Rapido", page_icon=":herb:", layout="wide")

BACKGROUND_IMAGE_PATH = Path(__file__).with_name("WhatsApp Image 2025-11-13 at 19.26.30.jpeg")


def load_background_image_b64() -> str | None:
    """Return the base64 string for the background image if it exists."""
    try:
        if BACKGROUND_IMAGE_PATH.exists():
            return base64.b64encode(BACKGROUND_IMAGE_PATH.read_bytes()).decode("utf-8")
    except Exception:
        st.warning("No fue posible cargar la imagen de fondo. Verifica el archivo.")
        return None
    else:
        st.warning("La imagen de fondo no se encontró en la carpeta actual.")
    return None


BACKGROUND_IMAGE_B64 = load_background_image_b64()


def inject_global_styles(background_b64: str | None) -> None:
    """Load Google Fonts, CSS tokens, and component styles, including the background image."""
    background_layer = ""
    if background_b64:
        bg_template = Template(
            """
        .stApp::before {
            content: "";
            position: fixed;
            inset: 0;
            background-image: url("data:image/jpeg;base64,$b64");
            background-size: cover;
            background-position: center;
            opacity: 0.65;
            filter: saturate(0.95) contrast(1.05);
            z-index: -2;
        }

        .stApp::after {
            content: "";
            position: fixed;
            inset: 0;
            background: linear-gradient(90deg, rgba(239,246,221,0.65), rgba(214,236,189,0.4));
            z-index: -1;
        }
            """
        )
        background_layer = bg_template.substitute(b64=background_b64)

    style_template = Template(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=EB+Garamond:wght@500&family=Inter:wght@400;500&display=swap');

        :root {
            --color-bg: #eff6dd;
            --color-panel: #9ab66d;
            --color-panel-border: #6b7c36;
            --color-shadow: rgba(73, 87, 32, 0.35);
            --color-pin: #d3dd52;
            --color-title: #1b1d12;
            --color-accent: #b67b4a;
            --font-heading: 'Playfair Display', serif;
            --font-script: 'EB Garamond', serif;
            --font-body: 'Inter', sans-serif;
        }

        body {
            background: var(--color-bg);
            font-family: var(--font-body);
        }

        .stApp {
            position: relative;
            min-height: 100vh;
            overflow: hidden;
            background: var(--color-bg);
        }

        $background_layer

        [data-testid="stAppViewContainer"] {
            background: transparent;
            font-family: var(--font-body);
        }

        [data-testid="stAppViewContainer"] .main,
        .block-container {
            background: transparent;
        }

        .block-container {
            max-width: 960px;
            margin: 0 auto;
            padding-left: 1rem;
            padding-right: 1rem;
        }

        .hero-shell {
            position: relative;
            margin-top: 1.5rem;
            margin-bottom: 2.5rem;
            padding: clamp(1.5rem, 6vw, 2.8rem);
            border-radius: 28px;
            border: 1px solid rgba(107,124,54,0.45);
            background: linear-gradient(135deg, rgba(255,255,255,0.9), rgba(239,246,221,0.85));
            box-shadow: 0 22px 45px rgba(67,82,45,0.18);
            display: flex;
            align-items: center;
            gap: clamp(1rem, 4vw, 2.5rem);
            overflow: hidden;
        }

        .hero-shell::before,
        .hero-shell::after {
            content: "";
            position: absolute;
            width: 180px;
            height: 180px;
            border-radius: 40%;
            background: rgba(127,164,109,0.18);
            filter: blur(30px);
            z-index: -1;
        }

        .hero-shell::before { top: -70px; left: -60px; }
        .hero-shell::after { bottom: -60px; right: -80px; }

        .hero-side {
            flex: 0 0 auto;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .hero-orb {
            width: clamp(90px, 12vw, 140px);
            height: clamp(90px, 12vw, 140px);
            border-radius: 36px;
            border: 2px solid rgba(94,125,82,0.55);
            box-shadow: 0 16px 26px rgba(0,0,0,0.12), inset 0 2px 6px rgba(255,255,255,0.45);
            background-size: cover;
            background-position: center;
        }

        .hero-main {
            text-align: center;
            flex: 1;
        }

        .hero-eyebrow {
            font-family: var(--font-script);
            letter-spacing: 0.7rem;
            text-transform: uppercase;
            color: #5E7D52;
            font-size: 0.95rem;
        }

        .hero-title {
            font-family: var(--font-heading);
            font-size: clamp(2.8rem, 5vw, 4.5rem);
            letter-spacing: 0.6rem;
            margin: 0.4rem 0 0.8rem;
            color: var(--color-title);
        }

        .hero-subtitle {
            font-size: 1.05rem;
            color: rgba(20,20,20,0.75);
            letter-spacing: 0.12rem;
        }

        .hero-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            padding: 0.35rem 1.2rem;
            border-radius: 999px;
            border: 1px solid rgba(94,125,82,0.45);
            background: rgba(127,164,109,0.16);
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.3rem;
            margin-top: 0.4rem;
        }

        @media (max-width: 768px) {
            .hero-shell {
                flex-direction: column;
            }

            .hero-orb {
                width: 120px;
                height: 120px;
            }

            .hero-eyebrow {
                letter-spacing: 0.4rem;
            }

            .hero-title {
                letter-spacing: 0.3rem;
            }
        }

        .price-card-shell {
            width: 100%;
            display: flex;
            justify-content: center;
            margin-bottom: 2rem;
        }

        .hanging-lines {
            display: flex;
            justify-content: center;
            gap: 1.8rem;
            margin-bottom: -0.3rem;
        }

        .hanging-lines span {
            width: 2px;
            height: 26px;
            background: rgba(70, 80, 50, 0.45);
        }

        .price-card {
            position: relative;
            width: min(280px, 90%);
            min-height: 138px;
            background: var(--color-panel);
            border: 2px solid var(--color-panel-border);
            border-radius: 12px;
            box-shadow: 0 12px 0 #7e8d41, 0 20px 30px var(--color-shadow);
            padding: 1.25rem;
        }

        .price-card::before,
        .price-card::after {
            content: '';
            position: absolute;
            top: 10px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            border: 2px solid var(--color-panel-border);
            background: radial-gradient(circle at 40% 40%, #fefefe, var(--color-pin));
            box-shadow: inset 0 1px 1px rgba(0,0,0,0.15);
        }

        .price-card::before {
            left: 14px;
        }

        .price-card::after {
            right: 14px;
        }

        .card-label {
            font-family: var(--font-heading);
            color: var(--color-title);
            font-size: 1.4rem;
            letter-spacing: 2px;
            text-align: center;
            text-transform: uppercase;
            line-height: 1.3;
        }

        @media (max-width: 900px) {
            .price-card {
                width: 92%;
                margin: 0 auto;
            }
        }
        </style>
        """
    )

    st.markdown(style_template.substitute(background_layer=background_layer), unsafe_allow_html=True)


def inject_button_styles() -> None:
    st.markdown(
        """
        <style>
        [data-testid="stStyledContainer"][data-user-key^="button-shell-"] {
            display: flex;
            justify-content: center;
            margin-top: -0.5rem;
            margin-bottom: 2.5rem;
        }

        [data-testid="stStyledContainer"][data-user-key^="button-shell-"] button {
            border-radius: 999px;
            padding: 0.4rem 2.4rem;
            border: 2px solid #6b7c36;
            background: #eff6dd;
            color: #1b1d12;
            font-weight: 600;
            letter-spacing: 0.18rem;
            text-transform: uppercase;
            box-shadow: 0 6px 14px rgba(0,0,0,0.12);
        }

        [data-testid="stStyledContainer"][data-user-key^="button-shell-"] button:hover {
            background: #9ab66d;
            color: #fefefe;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


inject_global_styles(BACKGROUND_IMAGE_B64)
inject_button_styles()

hero_orb_style = (
    f'background-image: url("data:image/jpeg;base64,{BACKGROUND_IMAGE_B64}");'
    if BACKGROUND_IMAGE_B64
    else "background: radial-gradient(circle at 20% 20%, #fff, rgba(127,164,109,0.6));"
)

st.markdown(
    f"""
    <div class="hero-shell">
        <div class="hero-side hero-side--left">
            <div class="hero-orb" style="{hero_orb_style}"></div>
        </div>
        <div class="hero-main">
            <div class="hero-eyebrow">FÁCIL Y RÁPIDO</div>
            <div class="hero-title">PRECIOS</div>
            <p class="hero-subtitle">Calculadoras verdes para tomar decisiones claras.</p>
            <div class="hero-pill">TODO EN UNA SOLA APP</div>
        </div>
        <div class="hero-side hero-side--right">
            <div class="hero-orb" style="{hero_orb_style}"></div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

card_contents = [
    "Calculadora de precio por producto",
    "Calculadora de punto de equilibrio",
    "Calculadora de gramaje",
]


def render_card(card_key: str, label: str, target: str) -> None:
    """Draw a hanging price card with the provided label."""
    with stylable_container(
        key=card_key,
        css_styles="""
            {
                display: flex;
                flex-direction: column;
                align-items: center;
            }
        """,
    ):
        st.markdown(
            f"""
            <div class="price-card-shell">
                <div>
                    <div class="hanging-lines">
                        <span></span>
                        <span></span>
                    </div>
                    <div class="price-card" data-card="{card_key}">
                        <div class="card-label">{label}</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        with stylable_container(
            key=f"button-shell-{card_key}",
            css_styles="""
                {
                    width: 100%;
                }
            """,
        ):
            if st.button("Abrir", key=f"open-{card_key}"):
                switch_page(target)


top_columns = st.columns([1, 1, 1], gap="large")

for column, (idx, label) in zip(top_columns, enumerate(card_contents)):
    with column:
        render_card(card_key=f"card-{idx}", label=label, target=label)
