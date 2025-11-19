# pip install streamlit plotly
import numpy as np
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(
    page_title="Calculadora de punto de equilibrio",
    page_icon=":balance_scale:",
    layout="wide",
)


def apply_styles() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700&family=Inter:wght@400;500&display=swap');

        body, .stApp {
            background: #EFF6E9;
            color: #1d2a21;
            font-family: "Inter", sans-serif;
        }

        [data-testid="stAppViewContainer"] {
            background: radial-gradient(circle at top left, rgba(127,164,109,0.12), transparent 50%),
                        linear-gradient(90deg, rgba(239,246,233,0.92), rgba(239,246,233,0.9));
            padding-top: 1rem;
        }

        .pe-hero {
            margin: 0.5rem auto 2rem;
            padding: clamp(1.4rem, 4vw, 2.8rem);
            border-radius: 32px;
            border: 1px solid rgba(94,125,82,0.4);
            background: linear-gradient(140deg, rgba(255,255,255,0.96), rgba(239,246,233,0.88));
            box-shadow: 0 28px 48px rgba(77,96,62,0.2);
            text-align: center;
        }

        .pe-hero__eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.6rem;
            color: #5E7D52;
            font-size: 0.9rem;
        }

        .pe-hero__title {
            font-family: "Playfair Display", serif;
            font-size: clamp(2.5rem, 5vw, 3.8rem);
            letter-spacing: 0.35rem;
            margin: 0.4rem 0;
        }

        .pe-hero__subtitle {
            font-size: 1rem;
            color: rgba(20,20,20,0.78);
            letter-spacing: 0.15rem;
        }

        .pe-card {
            background: rgba(255,255,255,0.9);
            border-radius: 18px;
            border: 1px solid rgba(94,125,82,0.35);
            padding: 1.25rem 1.5rem;
            box-shadow: 0 12px 28px rgba(0,0,0,0.08);
        }

        .pe-section-title {
            font-family: "Playfair Display", serif;
            font-size: 1.4rem;
            margin-bottom: 0.6rem;
        }

        .pe-kpi-value {
            font-family: "Playfair Display", serif;
            font-size: 2.2rem;
            margin: 0.2rem 0;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def formatea_moneda(x: float) -> str:
    if x is None or np.isnan(x):
        return "$ 0.00"
    return f"$ {x:,.2f}"


def calcular_be(P: float, CVu: float, CF: float) -> tuple[float, float, float]:
    mcu = P - CVu
    if mcu <= 0:
        return mcu, np.nan, np.nan
    q_be = CF / mcu if mcu else np.nan
    ventas_be = q_be * P if not np.isnan(q_be) else np.nan
    return mcu, q_be, ventas_be


def calcular_unidades_para_utilidad(P: float, CVu: float, CF: float, utilidad: float) -> float:
    mcu = P - CVu
    if mcu <= 0:
        return np.nan
    return (CF + utilidad) / mcu


def obtener_valores() -> tuple[float, float, float]:
    P = st.session_state.get("precio_sugerido")
    CVu = st.session_state.get("costo_unit_total")
    CF = st.session_state.get("fijos_mensuales")

    with st.expander("Editar supuestos base", expanded=any(v is None for v in [P, CVu, CF])):
        P = st.number_input("Precio unitario (P)", min_value=0.0, value=float(P or 65.0), step=1.0)
        CVu = st.number_input("Costo variable unitario (CVu)", min_value=0.0, value=float(CVu or 22.0), step=1.0)
        CF = st.number_input("Costos fijos mensuales (CF)", min_value=0.0, value=float(CF or 9500.0), step=100.0)
        st.session_state["precio_sugerido"] = P
        st.session_state["costo_unit_total"] = CVu
        st.session_state["fijos_mensuales"] = CF

    return P, CVu, CF


def grafica_be(P: float, CVu: float, CF: float, q_be: float, q_req: float | None) -> go.Figure:
    q_max = max(q_be * 1.6 if not np.isnan(q_be) else 0, q_req or 0, 50)
    cantidades = np.arange(0, int(q_max) + 1)
    ingresos = P * cantidades
    costos = CF + CVu * cantidades

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=cantidades, y=ingresos, mode="lines", name="Ingresos", line=dict(color="#5E7D52", width=3)))
    fig.add_trace(go.Scatter(x=cantidades, y=costos, mode="lines", name="Costos totales", line=dict(color="#BF6F4B", width=3)))

    if not np.isnan(q_be):
        fig.add_vline(
            x=q_be,
            line=dict(color="#1B4332", width=2, dash="dot"),
            annotation_text="Punto de equilibrio",
            annotation_position="top",
        )
    if q_req and not np.isnan(q_req):
        fig.add_vline(
            x=q_req,
            line=dict(color="#B958A5", width=2, dash="dash"),
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


def main() -> None:
    apply_styles()

    st.markdown(
        """
        <div class="pe-hero">
            <div class="pe-hero__eyebrow">Negocio sano</div>
            <div class="pe-hero__title">Calculadora de punto de equilibrio</div>
            <div class="pe-hero__subtitle">Identifica cuántos rollos debes vender para cubrir tus costos.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    P, CVu, CF = obtener_valores()
    mcu, q_be, ventas_be = calcular_be(P, CVu, CF)

    if mcu <= 0:
        st.error("El precio debe ser mayor al costo variable unitario para que exista punto de equilibrio.")
        return

    if q_be < 0:
        st.error("Los datos proporcionados generan un punto de equilibrio negativo. Revisa tus costos.")
        return

    kpi_cols = st.columns(4)
    kpi_vals = [
        ("Precio unitario (P)", formatea_moneda(P)),
        ("Costo variable unitario (CVu)", formatea_moneda(CVu)),
        ("Margen de contribución (MCu)", formatea_moneda(mcu)),
        ("Costos fijos mensuales (CF)", formatea_moneda(CF)),
    ]
    for col, (label, value) in zip(kpi_cols, kpi_vals):
        with col:
            st.markdown('<div class="pe-card">', unsafe_allow_html=True)
            st.caption(label)
            st.markdown(f'<div class="pe-kpi-value">{value}</div>', unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    hero_cols = st.columns(2)
    with hero_cols[0]:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Punto de equilibrio (unidades/mes)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pe-kpi-value">{q_be:,.2f}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with hero_cols[1]:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Ventas al BE (MXN/mes)</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="pe-kpi-value">{formatea_moneda(ventas_be)}</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    util_col, vol_col = st.columns(2)
    with util_col:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Utilidad objetivo</div>', unsafe_allow_html=True)
        utilidad_obj = st.number_input("π objetivo (MXN)", min_value=0.0, value=0.0, step=500.0)
        q_req = calcular_unidades_para_utilidad(P, CVu, CF, utilidad_obj) if utilidad_obj > 0 else np.nan
        if utilidad_obj > 0 and not np.isnan(q_req):
            st.metric("Unidades requeridas", f"{q_req:,.2f}")
        st.markdown("</div>", unsafe_allow_html=True)

    with vol_col:
        st.markdown('<div class="pe-card">', unsafe_allow_html=True)
        st.markdown('<div class="pe-section-title">Volumen esperado</div>', unsafe_allow_html=True)
        volumen_esperado = st.number_input("Rollos esperados por mes", min_value=0, value=900, step=10)
        if volumen_esperado > 0:
            margen_seguridad = (volumen_esperado - q_be) / volumen_esperado
            st.metric("Margen de seguridad", f"{margen_seguridad:.2%}")
        st.markdown("</div>", unsafe_allow_html=True)

    fig = grafica_be(P, CVu, CF, q_be, q_req if utilidad_obj > 0 else None)
    st.plotly_chart(fig, use_container_width=True)

    st.success(
        f"Necesitas vender {q_be:,.2f} rolls/mes para cubrir todos tus costos. "
        f"A partir de ahí, cada unidad aporta {formatea_moneda(mcu)} de contribución."
    )


if __name__ == "__main__":
    main()
