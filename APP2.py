

import base64
import importlib.util
import io
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_extras.stylable_container import stylable_container

#pip install streamlit pandas numpy plotly streamlit-extras xlsxwriter

st.set_page_config(page_title="PRECIOS", page_icon=":herb:", layout="wide")

UNIT_MAP: Dict[str, Dict[str, Any]] = {
    "kg": {"category": "weight", "to_base": 1000},
    "kilogramo": {"category": "weight", "to_base": 1000},
    "kilo": {"category": "weight", "to_base": 1000},
    "g": {"category": "weight", "to_base": 1},
    "gramo": {"category": "weight", "to_base": 1},
    "l": {"category": "volume", "to_base": 1000},
    "lt": {"category": "volume", "to_base": 1000},
    "litro": {"category": "volume", "to_base": 1000},
    "ml": {"category": "volume", "to_base": 1},
    "mililitro": {"category": "volume", "to_base": 1},
    "pza": {"category": "piece", "to_base": 1},
    "pieza": {"category": "piece", "to_base": 1},
    "pz": {"category": "piece", "to_base": 1},
    "unidad": {"category": "piece", "to_base": 1},
}

MARGIN_OPTIONS = ["10%", "20%", "30%", "40%", "50%", "100%", "Personalizado"]
HOME_SECTIONS = [
    {
        "key": "calc-precio",
        "eyebrow": "Producto estrella",
        "label": "Calculadora de precio por producto",
        "description": "Calcula el costo real por rollo y obtén tu precio ideal.",
    },
    {
        "key": "calc-equilibrio",
        "eyebrow": "Negocio sano",
        "label": "Calculadora de punto de equilibrio",
        "description": "Descubre cuántos rollos necesitas vender para cubrir tus costos.",
    },
    {
        "key": "calc-gramaje",
        "eyebrow": "Consistencia",
        "label": "Calculadora de gramaje",
        "description": "Mantén cada rollo perfecto controlando el gramaje de tus ingredientes.",
    },
]
ROLL_IMAGE_PATH = Path(__file__).with_name("WhatsApp Image 2025-11-13 at 19.26.30.jpeg")
GRAM_PAGE_PATH = Path(__file__).resolve().parent / "pages" / "3_Calculadora_gramaje.py"
_GRAMAJE_MODULE = None
_GRAM_MODULE_MTIME = None


def load_roll_image() -> str | None:
    try:
        if ROLL_IMAGE_PATH.exists():
            return base64.b64encode(ROLL_IMAGE_PATH.read_bytes()).decode("utf-8")
    except Exception:
        st.warning("No pude cargar la imagen del rollo. Revisa el archivo en la carpeta.")
    return None


ROLL_IMAGE_B64 = load_roll_image()


def ensure_view_state() -> None:
    if "view" not in st.session_state:
        st.session_state["view"] = "home"
    if "nav_target" not in st.session_state:
        st.session_state["nav_target"] = "calc-equilibrio"


def set_view(view: str) -> None:
    st.session_state["view"] = view


def load_gramaje_module():
    global _GRAMAJE_MODULE, _GRAM_MODULE_MTIME
    if not GRAM_PAGE_PATH.exists():
        return None

    current_mtime = GRAM_PAGE_PATH.stat().st_mtime
    needs_reload = _GRAMAJE_MODULE is None or _GRAM_MODULE_MTIME != current_mtime
    if not needs_reload:
        return _GRAMAJE_MODULE

    spec = importlib.util.spec_from_file_location("calculadora_gramaje_page", GRAM_PAGE_PATH)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    _GRAMAJE_MODULE = module
    _GRAM_MODULE_MTIME = current_mtime
    return module


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500;600&display=swap');

        body, .stApp {
            background: #EFF6E9;
            color: #1d2a21;
            font-family: "Inter", sans-serif;
        }

        .stApp header {background: transparent;}

        [data-testid="stAppViewContainer"] {
            background: linear-gradient(90deg, rgba(239,246,233,0.96), rgba(239,246,233,0.96)),
                         repeating-linear-gradient(90deg, rgba(127,164,109,0.08) 0px, rgba(127,164,109,0.08) 140px, transparent 140px, transparent 280px);
            min-height: 100vh;
            padding-top: 1.5rem;
        }

        .hero-shell {
            position: relative;
            margin-top: 0.5rem;
            margin-bottom: 2rem;
            padding: clamp(1.6rem, 5vw, 3rem);
            border-radius: 28px;
            border: 1px solid rgba(94,125,82,0.35);
            background: linear-gradient(140deg, rgba(255,255,255,0.92), rgba(239,246,233,0.88));
            box-shadow: 0 25px 50px rgba(77,96,62,0.22);
            display: flex;
            align-items: center;
            gap: clamp(1rem, 3vw, 2.6rem);
        }

        .hero-shell::before,
        .hero-shell::after {
            content: "";
            position: absolute;
            border-radius: 40%;
            background: rgba(127,164,109,0.22);
            filter: blur(30px);
            z-index: -1;
            width: 180px;
            height: 180px;
        }

        .hero-shell::before { top: -60px; left: -50px; }
        .hero-shell::after { bottom: -60px; right: -70px; }

        .hero-orb {
            width: clamp(85px, 11vw, 130px);
            height: clamp(85px, 11vw, 130px);
            border-radius: 38px;
            border: 2px solid rgba(94,125,82,0.5);
            background-size: cover;
            background-position: center;
            box-shadow: 0 16px 30px rgba(0,0,0,0.15), inset 0 2px 6px rgba(255,255,255,0.45);
        }

        .hero-main {
            flex: 1;
            text-align: center;
        }

        .hero-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.6rem;
            color: #5E7D52;
            font-size: 0.95rem;
        }

        .hero-title {
            font-family: "Playfair Display", serif;
            font-size: clamp(3rem, 5vw, 4.8rem);
            letter-spacing: 0.5rem;
            color: #141414;
            margin: 0.2rem 0 0.6rem;
        }

        .hero-subtitle {
            font-size: 1rem;
            color: rgba(20,20,20,0.76);
            letter-spacing: 0.2rem;
        }

        .pe-card {
            background: rgba(255,255,255,0.92);
            border-radius: 18px;
            border: 1px solid rgba(94,125,82,0.3);
            padding: 1.2rem 1.4rem;
            box-shadow: 0 12px 26px rgba(0,0,0,0.08);
        }

        .pe-card .pe-label {
            text-transform: uppercase;
            letter-spacing: 0.2rem;
            font-size: 0.8rem;
            color: #5E7D52;
        }

        .pe-card .pe-value {
            font-family: "Playfair Display", serif;
            font-size: 2rem;
            margin: 0.2rem 0;
        }

        .pe-section-title {
            font-family: "Playfair Display", serif;
            font-size: 1.3rem;
            margin-bottom: 0.4rem;
        }


        [data-testid="stStyledContainer"][data-user-key^="card-"] {
            background: #7FA46D;
            border: 1px solid #5E7D52;
            border-radius: 14px;
            padding: 26px 26px 30px;
            box-shadow: 0 6px 14px rgba(0, 0, 0, 0.12);
            color: #1d2a21;
            position: relative;
            overflow: hidden;
        }

        [data-testid="stStyledContainer"][data-user-key^="card-"]::before,
        [data-testid="stStyledContainer"][data-user-key^="card-"]::after {
            content: "";
            position: absolute;
            width: 18px;
            height: 18px;
            border-radius: 50%;
            background: #EFF6E9;
            border: 2px solid #5E7D52;
            top: 14px;
            box-shadow: inset 0 1px 3px rgba(0,0,0,0.25);
        }

        [data-testid="stStyledContainer"][data-user-key^="card-"]::before {left: 18px;}
        [data-testid="stStyledContainer"][data-user-key^="card-"]::after {right: 18px;}

        [data-testid="stStyledContainer"][data-user-key="card-result"] {
            background: #EFF6E9;
            border: 1px solid #7FA46D;
            box-shadow: 0 10px 24px rgba(0, 0, 0, 0.12);
        }

        [data-testid="stStyledContainer"][data-user-key="card-result"]::before,
        [data-testid="stStyledContainer"][data-user-key="card-result"]::after {
            background: #7FA46D;
            border-color: #5E7D52;
        }

        .card-eyebrow {
            text-transform: uppercase;
            font-size: 0.75rem;
            letter-spacing: 0.25rem;
            color: #223422;
        }

        .card-title {
            font-family: "Playfair Display", serif;
            font-size: 1.7rem;
            color: #141414;
            margin-bottom: 0.6rem;
        }

        div[data-testid="stMarkdown"] > p.card-subtitle {
            margin-top: 0;
            margin-bottom: 1.2rem;
            color: rgba(20,20,20,0.8);
        }

        label, [data-baseweb="input"] input {
            font-size: 0.95rem !important;
        }

        .subtotal-pill {
            font-weight: 600;
            color: #141414;
            font-size: 1.3rem;
            margin-top: 0.8rem;
        }

        .subtotal-pill span {
            font-family: "Playfair Display", serif;
            letter-spacing: 0.08rem;
        }

        .result-metric {
            position: relative;
            padding: 16px 18px 18px;
            border: 1px solid #5E7D52;
            border-radius: 12px;
            margin-bottom: 1rem;
            background: #fff;
            box-shadow: 0 6px 14px rgba(0,0,0,0.12);
        }

        .result-metric__label {
            font-size: 0.9rem;
            letter-spacing: 0.1rem;
            color: #5E7D52;
        }

        .result-metric__value {
            font-family: "Playfair Display", serif;
            font-size: 2.3rem;
            color: #1d2a21;
            margin: 0.2rem 0 0;
        }

        .result-badge {
            position: absolute;
            top: -12px;
            right: 16px;
            padding: 4px 12px;
            border-radius: 999px;
            font-size: 0.75rem;
            letter-spacing: 0.2rem;
            font-weight: 700;
            background: #7FA46D;
            color: #141414;
        }

        .result-badge.precio {
            background: #5E7D52;
            color: #EFF6E9;
        }

        .stDownloadButton button {
            width: 100%;
            border-radius: 999px;
            padding: 0.8rem 1.6rem;
            border: 1px solid #5E7D52;
            background: #7FA46D;
            color: #141414;
            font-weight: 600;
            letter-spacing: 0.1rem;
        }

        .stDownloadButton button:hover {
            background: #5E7D52;
            color: #EFF6E9;
        }

        div[data-testid="stDataEditorGrid"] {
            border-radius: 10px;
            overflow: hidden;
        }

        div[data-testid="stDataEditorToolbar"] {
            background: transparent;
        }

        .price-note {
            font-size: 0.85rem;
            color: rgba(29,42,33,0.8);
        }

        .home-intro {
            text-align: center;
            color: rgba(20,20,20,0.75);
            margin-bottom: 2rem;
        }

        .section-card {
            background: rgba(255,255,255,0.92);
            border: 1px solid rgba(94,125,82,0.3);
            border-radius: 16px;
            padding: 1.5rem;
            box-shadow: 0 12px 24px rgba(0,0,0,0.08);
            margin-bottom: 1.5rem;
        }

        [data-testid="stStyledContainer"][data-user-key^="home-card-"] {
            background: #7FA46D;
            border-radius: 18px;
            border: 1px solid #5E7D52;
            box-shadow: 0 10px 24px rgba(0,0,0,0.12);
            padding: 24px;
            color: #141414;
            min-height: 270px;
        }

        [data-testid="stStyledContainer"][data-user-key^="home-card-"]::before,
        [data-testid="stStyledContainer"][data-user-key^="home-card-"]::after {
            content: "";
            position: absolute;
            width: 14px;
            height: 14px;
            border-radius: 50%;
            border: 2px solid #5E7D52;
            background: #EFF6E9;
            top: 16px;
        }

        [data-testid="stStyledContainer"][data-user-key^="home-card-"]::before {left: 18px;}
        [data-testid="stStyledContainer"][data-user-key^="home-card-"]::after {right: 18px;}

        [data-testid="stStyledContainer"][data-user-key^="home-card-"] .card-eyebrow {
            font-size: 0.75rem;
            letter-spacing: 0.3rem;
            color: #223422;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def default_ingredients() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Ingrediente": "Harina de trigo",
                "Cantidad por batch": 1200,
                "Unidad": "g",
                "Precio de compra": 380,
                "Unidad de compra": "kg",
            },
            {
                "Ingrediente": "Azúcar mascabado",
                "Cantidad por batch": 350,
                "Unidad": "g",
                "Precio de compra": 48,
                "Unidad de compra": "kg",
            },
            {
                "Ingrediente": "Canela / mantequilla",
                "Cantidad por batch": 420,
                "Unidad": "g",
                "Precio de compra": 110,
                "Unidad de compra": "kg",
            },
        ]
    )


def convert_price(price: Any, purchase_unit: str | None, use_unit: str | None) -> float:
    try:
        price_value = float(price)
    except (TypeError, ValueError):
        return 0.0

    purchase_data = UNIT_MAP.get((purchase_unit or "").strip().lower())
    use_data = UNIT_MAP.get((use_unit or "").strip().lower())
    if not purchase_data or not use_data:
        return price_value
    if purchase_data["category"] != use_data["category"]:
        return price_value

    price_per_base = price_value / purchase_data["to_base"]
    return price_per_base * use_data["to_base"]


def currency(value: float) -> str:
    return f"${value:,.2f}"


def formatea_moneda(value: float) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return "$0.00"
    return f"$ {value:,.2f}"


def calcular_be(P: float, CVu: float, CF: float) -> tuple[float, float, float]:
    mcu = P - CVu
    if mcu <= 0:
        return mcu, np.nan, np.nan
    q_be = CF / mcu if mcu else np.nan
    ventas = q_be * P if not np.isnan(q_be) else np.nan
    return mcu, q_be, ventas


def calcular_unidades_para_utilidad(P: float, CVu: float, CF: float, utilidad: float) -> float:
    mcu = P - CVu
    if mcu <= 0:
        return np.nan
    return (CF + utilidad) / mcu


def ensure_session_defaults() -> None:
    if "ingredients_table" not in st.session_state:
        st.session_state["ingredients_table"] = default_ingredients()


def get_equilibrio_inputs() -> tuple[float, float, float]:
    P = st.session_state.get("precio_sugerido")
    CVu = st.session_state.get("costo_unit_total")
    CF = st.session_state.get("fijos_mensuales")

    needs_inputs = any(value is None for value in (P, CVu, CF))
    with st.expander("Editar supuestos base", expanded=needs_inputs):
        P = st.number_input("Precio unitario (P)", min_value=0.0, value=float(P or 65.0), step=1.0)
        CVu = st.number_input("Costo variable unitario (CVu)", min_value=0.0, value=float(CVu or 22.0), step=1.0)
        CF = st.number_input("Costos fijos mensuales (CF)", min_value=0.0, value=float(CF or 9500.0), step=100.0)
        st.session_state["precio_sugerido"] = P
        st.session_state["costo_unit_total"] = CVu
        st.session_state["fijos_mensuales"] = CF

    return P, CVu, CF


def build_excel_file(
    resumen_df: pd.DataFrame,
    ingredientes_df: pd.DataFrame,
    indirectos_df: pd.DataFrame,
    mano_df: pd.DataFrame,
) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        ingredientes_df.to_excel(writer, sheet_name="Ingredientes", index=False)
        indirectos_df.to_excel(writer, sheet_name="Indirectos", index=False)
        mano_df.to_excel(writer, sheet_name="Mano de obra", index=False)

        workbook = writer.book
        currency_format = workbook.add_format({"num_format": '"$"#,##0.00'})
        percent_format = workbook.add_format({"num_format": "0.00%"})
        bold_header = workbook.add_format({"bold": True})

        for sheet_name, df in {
            "Resumen": resumen_df,
            "Ingredientes": ingredientes_df,
            "Indirectos": indirectos_df,
            "Mano de obra": mano_df,
        }.items():
            worksheet = writer.sheets[sheet_name]
            worksheet.set_row(0, None, bold_header)
            for col_idx, column in enumerate(df.columns):
                series = df[column].astype(str)
                max_len = max([len(column)] + [len(x) for x in series])
                worksheet.set_column(col_idx, col_idx, min(max_len + 4, 40))

        resumen_sheet = writer.sheets["Resumen"]
        currency_columns = resumen_df.columns.get_indexer(["MXN"])
        percent_columns = resumen_df.columns.get_indexer(["Porcentaje"])
        for col_idx in currency_columns:
            resumen_sheet.set_column(col_idx, col_idx, None, currency_format)
        for col_idx in percent_columns:
            resumen_sheet.set_column(col_idx, col_idx, None, percent_format)

        ingredientes_sheet = writer.sheets["Ingredientes"]
        for col in ["Precio de compra", "Precio por unidad usada", "Costo por batch", "Costo por unidad"]:
            if col in ingredientes_df.columns:
                idx = ingredientes_df.columns.get_loc(col)
                ingredientes_sheet.set_column(idx, idx, None, currency_format)

        indirectos_sheet = writer.sheets["Indirectos"]
        if "MXN" in indirectos_df.columns:
            idx = indirectos_df.columns.get_loc("MXN")
            indirectos_sheet.set_column(idx, idx, None, currency_format)

        mano_sheet = writer.sheets["Mano de obra"]
        if "MXN" in mano_df.columns:
            idx = mano_df.columns.get_loc("MXN")
            mano_sheet.set_column(idx, idx, None, currency_format)

    return buffer.getvalue()


def plot_equilibrio(P: float, CVu: float, CF: float, q_be: float, q_req: float | None) -> go.Figure:
    max_base = max(q_be * 1.6 if not np.isnan(q_be) else 0, q_req or 0, 50)
    cantidades = np.arange(0, int(max_base) + 1)
    ingresos = P * cantidades
    costos = CF + CVu * cantidades

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cantidades, y=ingresos, mode="lines", name="Ingresos", line=dict(color="#2d6a4f", width=3)))
    fig.add_trace(go.Scatter(x=cantidades, y=costos, mode="lines", name="Costos totales", line=dict(color="#b56576", width=3)))

    if not np.isnan(q_be):
        fig.add_vline(
            x=q_be,
            line=dict(color="#1b4332", width=2, dash="dot"),
            annotation_text="Punto de equilibrio",
            annotation_position="top",
        )
    if q_req and not np.isnan(q_req):
        fig.add_vline(
            x=q_req,
            line=dict(color="#6a4c93", width=2, dash="dash"),
            annotation_text="Meta utilidad",
            annotation_position="top right",
        )

    fig.update_layout(
        template="simple_white",
        height=420,
        margin=dict(l=20, r=20, t=40, b=40),
        xaxis_title="Unidades (rollos)",
        yaxis_title="Monto MXN",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
    )
    return fig


def render_header(
    show_image: bool = False,
    title: str = "PRECIOS",
    subtitle: str = "Selecciona la calculadora que necesitas.",
) -> None:
    orb_style = (
        f'background-image: url("data:image/jpeg;base64,{ROLL_IMAGE_B64}");'
        if ROLL_IMAGE_B64
        else "background: radial-gradient(circle at 20% 20%, #fff, rgba(127,164,109,0.5));"
    )
    if show_image:
        st.markdown(
            f"""
            <div class="hero-shell">
                <div class="hero-orb" style="{orb_style}"></div>
                <div class="hero-main">
                    <div class="hero-eyebrow">FÁCIL Y RÁPIDO</div>
                    <div class="hero-title">{title.upper()}</div>
                    <p class="hero-subtitle">{subtitle}</p>
                </div>
                <div class="hero-orb" style="{orb_style}"></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            f"""
            <div class="hero-shell">
                <div class="hero-main">
                    <div class="hero-eyebrow">FÁCIL Y RÁPIDO</div>
                    <div class="hero-title">{title.upper()}</div>
                    <p class="hero-subtitle">{subtitle}</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_navigation() -> None:
    other_sections = [section for section in HOME_SECTIONS if section["key"] != "calc-precio"]
    label_to_key = {section["label"]: section["key"] for section in other_sections}
    labels = list(label_to_key.keys())
    default_label = next((label for label, key in label_to_key.items() if key == st.session_state.get("nav_target")), labels[0])

    nav_cols = st.columns([1, 1, 0.6], gap="small")
    with nav_cols[0]:
        st.button(
            "← Volver al inicio",
            use_container_width=True,
            on_click=set_view,
            args=("home",),
        )
    with nav_cols[1]:
        selected_label = st.selectbox(
            "Ir a otra sección",
            labels,
            index=labels.index(default_label),
            key="nav_section_select",
        )
        st.session_state["nav_target"] = label_to_key[selected_label]
    with nav_cols[2]:
        if st.button("Ir ahora", use_container_width=True):
            target = st.session_state.get("nav_target")
            if target:
                set_view(target)
            else:
                st.info("Selecciona una sección válida en el selector.")


def render_home_view() -> None:
    render_header(show_image=True)
    st.markdown(
        '<p class="home-intro">Selecciona una calculadora para continuar.</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(HOME_SECTIONS), gap="large")
    for column, card in zip(cols, HOME_SECTIONS):
        with column:
            with stylable_container(
                key=f"home-card-{card['key']}",
                css_styles="""
                    {
                        position: relative;
                    }
                """,
            ):
                st.markdown(f'<div class="card-eyebrow">{card["eyebrow"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="card-title">{card["label"]}</div>', unsafe_allow_html=True)
                st.markdown(f'<p class="card-subtitle">{card["description"]}</p>', unsafe_allow_html=True)
                st.button(
                    "Explorar",
                    key=f"open-{card['key']}",
                    use_container_width=True,
                    type="secondary",
                    on_click=set_view,
                    args=(card["key"],),
                    help="Abrir sección",
                )


def render_placeholder_view(section_key: str) -> None:
    section = next((item for item in HOME_SECTIONS if item["key"] == section_key), None)
    title_text = section["label"] if section else "Calculadora"
    render_header(
        show_image=True,
        title=title_text,
        subtitle="Esta sección estará disponible pronto.",
    )
    if section:
        st.subheader(section["label"])
        st.info("Estamos preparando esta sección. Muy pronto estará lista para ti.")
    else:
        st.info("Sección en construcción.")
    st.button("← Volver al inicio", on_click=set_view, args=("home",))


def render_precios_view() -> None:
    render_header(
        show_image=True,
        title="Precio por producto",
        subtitle="Desglosa cada costo y obtén el precio sugerido por rollo.",
    )
    render_navigation()

    layout_cols = st.columns([1.8, 1])
    with layout_cols[0]:
        top_cols = st.columns(2, gap="large")
        with top_cols[0]:
            batch_size, ingr_df, ingr_processed_df, ingredientes_unit = ingrediente_card()
        with top_cols[1]:
            (
                indirecto_fijo_unit,
                indirecto_variable_unit,
                fixed_inputs,
                variable_inputs,
                produccion_mensual,
            ) = indirectos_card()

        spacer_cols = st.columns([0.1, 0.8, 0.1])
        with spacer_cols[1]:
            (
                horas_batch,
                sueldo_hora,
                mano_batch,
                mano_unit,
            ) = mano_obra_card(batch_size)

    with layout_cols[1]:
        (
            margen_decimal,
            impuesto,
            costo_total_unit,
            precio_sugerido,
            precio_impuesto,
        ) = resultados_card(
            ingredientes_unit=ingredientes_unit,
            indirecto_fijo=indirecto_fijo_unit,
            indirecto_variable=indirecto_variable_unit,
            mano_unit=mano_unit,
        )

    resumen_df = pd.DataFrame(
        [
            {"Concepto": "Ingredientes por unidad", "MXN": ingredientes_unit, "Porcentaje": np.nan},
            {
                "Concepto": "Indirectos fijos por unidad",
                "MXN": indirecto_fijo_unit,
                "Porcentaje": np.nan,
            },
            {
                "Concepto": "Indirectos variables por unidad",
                "MXN": indirecto_variable_unit,
                "Porcentaje": np.nan,
            },
            {"Concepto": "Mano de obra por unidad", "MXN": mano_unit, "Porcentaje": np.nan},
            {"Concepto": "Costo total por unidad", "MXN": costo_total_unit, "Porcentaje": np.nan},
            {"Concepto": "Margen aplicado", "MXN": np.nan, "Porcentaje": margen_decimal},
            {"Concepto": "Precio sugerido", "MXN": precio_sugerido, "Porcentaje": np.nan},
            {
                "Concepto": "Impuesto",
                "MXN": np.nan,
                "Porcentaje": (impuesto / 100) if impuesto else np.nan,
            },
            {
                "Concepto": "Precio con impuesto",
                "MXN": precio_impuesto if precio_impuesto is not None else np.nan,
                "Porcentaje": np.nan,
            },
        ]
    )

    ingredientes_export = ingr_processed_df.copy()
    ingredientes_export["Precio por unidad usada"] = ingredientes_export["Precio por unidad usada"].fillna(0.0)
    ingredientes_export["Costo por batch"] = ingredientes_export["Costo por batch"].fillna(0.0)
    ingredientes_export["Costo por unidad"] = ingredientes_export["Costo por unidad"].fillna(0.0)

    indirect_rows = [{**{"Concepto": name, "MXN": value}} for name, value in fixed_inputs.items()]
    indirect_rows.append({"Concepto": "Total fijos mensuales", "MXN": sum(fixed_inputs.values())})
    indirect_rows.append({"Concepto": "Producción mensual estimada", "MXN": produccion_mensual})
    indirect_rows.append({"Concepto": "Indirecto fijo por unidad", "MXN": indirecto_fijo_unit})
    indirect_rows.extend({**{"Concepto": name, "MXN": value}} for name, value in variable_inputs.items())
    indirect_rows.append({"Concepto": "Indirecto variable por unidad", "MXN": indirecto_variable_unit})
    indirectos_df = pd.DataFrame(indirect_rows)

    mano_df = pd.DataFrame(
        [
            {"Concepto": "Horas por batch", "Valor": horas_batch, "MXN": np.nan},
            {"Concepto": "Sueldo por hora", "Valor": sueldo_hora, "MXN": np.nan},
            {"Concepto": "Mano de obra por batch", "Valor": np.nan, "MXN": mano_batch},
            {"Concepto": "Mano de obra por unidad", "Valor": np.nan, "MXN": mano_unit},
        ]
    )

    st.session_state["precio_sugerido"] = precio_sugerido
    st.session_state["costo_unit_total"] = costo_total_unit
    st.session_state["fijos_mensuales"] = sum(fixed_inputs.values())

    excel_bytes = build_excel_file(resumen_df, ingredientes_export, indirectos_df, mano_df)
    st.download_button(
        "Descargar Excel",
        data=excel_bytes,
        file_name="precios_rollo_canela.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def render_equilibrio_view() -> None:
    render_header(
        show_image=True,
        title="Punto de equilibrio",
        subtitle="Identifica cuántos rollos necesitas vender para cubrir tus costos.",
    )
    render_navigation()

    P, CVu, CF = get_equilibrio_inputs()
    mcu, q_be, ventas_be = calcular_be(P, CVu, CF)

    if mcu <= 0:
        st.error("El precio debe ser mayor al costo variable unitario para que exista punto de equilibrio.")
        return
    if q_be < 0:
        st.error("Los datos proporcionados generan un punto de equilibrio negativo. Revisa tus costos.")
        return

    kpi_cols = st.columns(4, gap="large")
    kpi_data = [
        ("Precio unitario (P)", formatea_moneda(P)),
        ("Costo variable unitario (CVu)", formatea_moneda(CVu)),
        ("Margen de contribución", formatea_moneda(mcu)),
        ("Costos fijos mensuales (CF)", formatea_moneda(CF)),
    ]
    for col, (label, value) in zip(kpi_cols, kpi_data):
        with col:
            st.markdown('<div class="pe-card">', unsafe_allow_html=True)
            st.caption(label)
            st.markdown(f'<div class="pe-value">{value}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    summary_cols = st.columns(2, gap="large")
    with summary_cols[0]:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Punto de equilibrio (unidades/mes)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pe-value">{q_be:,.2f}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with summary_cols[1]:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Ventas al BE (MXN/mes)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pe-value">{formatea_moneda(ventas_be)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    util_col, vol_col = st.columns(2, gap="large")
    with util_col:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Utilidad objetivo</div>', unsafe_allow_html=True)
        utilidad_obj = st.number_input("π objetivo (MXN)", min_value=0.0, value=0.0, step=500.0, key="utilidad_objetivo")
        q_req = calcular_unidades_para_utilidad(P, CVu, CF, utilidad_obj) if utilidad_obj > 0 else np.nan
        if utilidad_obj > 0 and not np.isnan(q_req):
            st.metric("Unidades requeridas", f"{q_req:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with vol_col:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Volumen esperado</div>', unsafe_allow_html=True)
        volumen_esperado = st.number_input(
            "Rollos esperados por mes",
            min_value=0,
            value=900,
            step=10,
            key="volumen_esperado",
        )
        if volumen_esperado > 0:
            margen_seguridad = (volumen_esperado - q_be) / volumen_esperado
            st.metric("Margen de seguridad", f"{margen_seguridad:.2%}")
        st.markdown("</div>", unsafe_allow_html=True)

    fig = plot_equilibrio(P, CVu, CF, q_be, q_req if utilidad_obj > 0 else None)
    st.plotly_chart(fig, use_container_width=True)


def render_gramaje_view() -> None:
    render_header(
        show_image=True,
        title="Calculadora de gramaje",
        subtitle="Crea, guarda y escala tus recetas para cualquier pedido.",
    )
    render_navigation()
    module = load_gramaje_module()
    if not module or not hasattr(module, "render_calculadora_gramaje"):
        st.warning("No pude cargar la calculadora de gramaje. Verifica el archivo pages/3_Calculadora_gramaje.py.")
        return
    try:
        module.render_calculadora_gramaje(embed=True, show_header=False)
    except Exception as exc:
        st.error(f"Ocurrio un problema al renderizar la calculadora de gramaje: {exc}")


def ingrediente_card() -> tuple[float, pd.DataFrame, pd.DataFrame, float]:
    ensure_session_defaults()
    with stylable_container(
        key="card-ingredients",
        css_styles="""
            {
                padding: 0;
            }
        """,
    ):
        st.markdown('<div class="card-eyebrow">Materia prima</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Ingredientes</div>', unsafe_allow_html=True)
        st.markdown('<p class="card-subtitle">Define tu batch y captura cada ingrediente con su costo real.</p>', unsafe_allow_html=True)

        batch_size = st.number_input("Tamaño del batch (rollos)", min_value=0.0, step=1.0, value=24.0, key="batch_size_input")

        ingrediente_df = st.data_editor(
            st.session_state["ingredients_table"],
            num_rows="dynamic",
            hide_index=True,
            use_container_width=True,
            key="ingredients_editor",
            column_config={
                "Ingrediente": st.column_config.TextColumn("Ingrediente", required=True),
                "Cantidad por batch": st.column_config.NumberColumn("Cantidad por batch", min_value=0.0, format="%.2f"),
                "Unidad": st.column_config.SelectboxColumn("Unidad (g/ml/pza)", options=["g", "kg", "ml", "L", "pza"]),
                "Precio de compra": st.column_config.NumberColumn("Precio de compra", min_value=0.0, format="%.2f"),
                "Unidad de compra": st.column_config.SelectboxColumn(
                    "Unidad de compra",
                    options=["kg", "g", "L", "ml", "pza"],
                ),
            },
        )
        st.session_state["ingredients_table"] = ingrediente_df

        working_df = ingrediente_df.copy()
        for column in ["Cantidad por batch", "Precio de compra"]:
            working_df[column] = pd.to_numeric(working_df[column], errors="coerce").fillna(0.0)
        working_df["Unidad"] = working_df["Unidad"].fillna("").astype(str)
        working_df["Unidad de compra"] = working_df["Unidad de compra"].fillna("").astype(str)

        working_df["Precio por unidad usada"] = working_df.apply(
            lambda row: convert_price(row["Precio de compra"], row["Unidad de compra"], row["Unidad"]),
            axis=1,
        )
        working_df["Costo por batch"] = working_df["Cantidad por batch"] * working_df["Precio por unidad usada"]
        working_df["Costo por unidad"] = np.where(
            batch_size > 0,
            working_df["Costo por batch"] / batch_size,
            0.0,
        )

        ingredientes_total_batch = float(working_df["Costo por batch"].sum())
        ingredientes_por_unidad = ingredientes_total_batch / batch_size if batch_size > 0 else 0.0

        if batch_size <= 0:
            st.warning("El tamaño del batch debe ser mayor a 0 para obtener el costo unitario.")

        st.markdown(
            f'<div class="subtotal-pill">Subtotal ingredientes / unidad: <span>{currency(ingredientes_por_unidad)}</span></div>',
            unsafe_allow_html=True,
        )

    return batch_size, ingrediente_df, working_df, ingredientes_por_unidad


def indirectos_card() -> tuple[float, float, dict[str, float], dict[str, float], float]:
    with stylable_container(
        key="card-indirect",
        css_styles="""
            {
                padding: 0;
            }
        """,
    ):
        st.markdown('<div class="card-eyebrow">Operación</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Indirectos</div>', unsafe_allow_html=True)
        st.markdown('<p class="card-subtitle">Separa fijos mensuales y variables por unidad.</p>', unsafe_allow_html=True)

        fixed_cols = st.columns(2, gap="medium")
        with fixed_cols[0]:
            renta = st.number_input("Renta mensual", min_value=0.0, value=4500.0, step=100.0)
            servicios = st.number_input("Servicios (luz/agua)", min_value=0.0, value=1800.0, step=50.0)
        with fixed_cols[1]:
            sueldos = st.number_input("Sueldos administrativos", min_value=0.0, value=3200.0, step=100.0)
            licencias = st.number_input("Licencias/software", min_value=0.0, value=450.0, step=50.0)



        produccion_mensual = st.number_input("Producción mensual estimada (unidades)", min_value=0.0, value=480.0, step=10.0)

        fixed_total = renta + servicios + sueldos + licencias
        if produccion_mensual <= 0:
            st.warning("Captura la producción mensual estimada para prorratear los costos fijos.")

        indirecto_fijo_unit = fixed_total / produccion_mensual if produccion_mensual > 0 else 0.0

        st.markdown("---")
        st.caption("Variables por unidad")
        var_cols = st.columns(3, gap="medium")
        with var_cols[0]:
            empaque = st.number_input("Empaque", min_value=0.0, value=6.5, step=0.5)
        with var_cols[1]:
            etiquetas = st.number_input("Etiquetas", min_value=0.0, value=2.5, step=0.5)
        with var_cols[2]:
            bolsas = st.number_input("Bolsas / cajas", min_value=0.0, value=4.0, step=0.5)

        indirecto_variable_unit = empaque + etiquetas + bolsas

        st.markdown(
            f'<div class="subtotal-pill">Indirectos / unidad: <span>{currency(indirecto_fijo_unit + indirecto_variable_unit)}</span></div>',
            unsafe_allow_html=True,
        )

    fixed_inputs = {
        "Renta": renta,
        "Servicios": servicios,
        "Sueldos": sueldos,
        "Licencias": licencias,
    }
    variable_inputs = {
        "Empaque": empaque,
        "Etiquetas": etiquetas,
        "Bolsas / cajas": bolsas,
    }
    return indirecto_fijo_unit, indirecto_variable_unit, fixed_inputs, variable_inputs, produccion_mensual


def mano_obra_card(batch_size: float) -> tuple[float, float, float, float]:
    with stylable_container(
        key="card-mano",
        css_styles="""
            {
                padding: 0;
            }
        """,
    ):
        st.markdown('<div class="card-eyebrow">Equipo</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Mano de obra</div>', unsafe_allow_html=True)
        st.markdown('<p class="card-subtitle">Calcula horas por batch y prorratea al rollo.</p>', unsafe_allow_html=True)

        horas_batch = st.number_input("Horas por batch", min_value=0.0, value=5.0, step=0.5)
        sueldo_hora = st.number_input("Sueldo por hora", min_value=0.0, value=90.0, step=5.0)

        mano_batch = horas_batch * sueldo_hora
        mano_unit = mano_batch / batch_size if batch_size > 0 else 0.0

        if batch_size <= 0:
            st.warning("Define el tamaño del batch para calcular la mano de obra por unidad.")

        st.markdown(
            f'<div class="subtotal-pill">Mano de obra / unidad: <span>{currency(mano_unit)}</span></div>',
            unsafe_allow_html=True,
        )

    return horas_batch, sueldo_hora, mano_batch, mano_unit


def resultados_card(
    ingredientes_unit: float,
    indirecto_fijo: float,
    indirecto_variable: float,
    mano_unit: float,
):
    with stylable_container(
        key="card-result",
        css_styles="""
            {
                padding: 0;
            }
        """,
    ):
        st.markdown('<div class="card-eyebrow">Resumen</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Costo & Precio</div>', unsafe_allow_html=True)

        col_margin = st.container()
        with col_margin:
            selected_margin = st.radio(
                "Margen de ganancia",
                options=MARGIN_OPTIONS,
                horizontal=True,
                index=MARGIN_OPTIONS.index("30%"),
                key="margin_selector",
            )
            if selected_margin == "Personalizado":
                margen_personalizado = st.number_input("Margen personalizado (%)", min_value=0.0, value=35.0, step=1.0)
                margen_decimal = margen_personalizado / 100
            else:
                margen_decimal = float(selected_margin.strip("%")) / 100

        impuesto = st.number_input("Impuesto (%)", min_value=0.0, value=0.0, step=1.0)

        costo_total_unit = ingredientes_unit + indirecto_fijo + indirecto_variable + mano_unit
        precio_sugerido = costo_total_unit * (1 + margen_decimal)
        precio_con_impuesto = precio_sugerido * (1 + impuesto / 100) if impuesto > 0 else None

        st.markdown(
            f"""
            <div class="result-metric">
                <div class="result-badge costo">COSTO</div>
                <div class="result-metric__label">Costo total por unidad</div>
                <div class="result-metric__value">{currency(costo_total_unit)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            f"""
            <div class="result-metric">
                <div class="result-badge precio">PRECIO</div>
                <div class="result-metric__label">Precio sugerido</div>
                <div class="result-metric__value">{currency(precio_sugerido)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        if precio_con_impuesto is not None:
            st.markdown(
                f'<p class="price-note">Precio con impuesto ({impuesto:.0f}%): <strong>{currency(precio_con_impuesto)}</strong></p>',
                unsafe_allow_html=True,
            )

    return margen_decimal, impuesto, costo_total_unit, precio_sugerido, precio_con_impuesto


def main() -> None:
    inject_styles()
    ensure_view_state()
    current_view = st.session_state.get("view", "home")

    if current_view == "calc-precio":
        render_precios_view()
    elif current_view == "calc-equilibrio":
        render_equilibrio_view()
    elif current_view == "calc-gramaje":
        render_gramaje_view()
    else:
        render_home_view()


if __name__ == "__main__":
    main()
