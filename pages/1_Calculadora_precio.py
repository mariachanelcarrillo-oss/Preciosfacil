import streamlit as st

from theme_utils import apply_portada_theme, render_section_header


st.set_page_config(
    page_title="Calculadora de precio por producto",
    page_icon=":herb:",
    layout="wide",
)

apply_portada_theme()
render_section_header(
    "Calculadora de precio por producto",
    "Estructura tus costos antes de calcular para mantener márgenes saludables.",
    show_roll=True,
)


st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### Ingredientes")
st.caption("Define las materias primas de tu batch.")
st.data_editor(
    [
        {"Ingrediente": "Harina", "Cantidad": 1200, "Unidad": "g", "Precio compra": 380},
        {"Ingrediente": "Azúcar mascabado", "Cantidad": 300, "Unidad": "g", "Precio compra": 85},
        {"Ingrediente": "Canela", "Cantidad": 120, "Unidad": "g", "Precio compra": 60},
    ],
    num_rows="dynamic",
    hide_index=True,
    key="ingredients_editor",
    use_container_width=True,
)
st.number_input("Tamaño del batch (rollos)", min_value=1, step=1, value=24)
st.markdown("</div>", unsafe_allow_html=True)


st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### Indirectos")
st.caption("Registra gastos fijos mensuales y estimados por unidad.")
col1, col2, col3 = st.columns(3)
with col1:
    st.number_input("Renta mensual", min_value=0.0, value=4000.0, step=100.0)
    st.number_input("Servicios", min_value=0.0, value=1500.0, step=50.0)
with col2:
    st.number_input("Sueldos administrativos", min_value=0.0, value=2800.0, step=100.0)
    st.number_input("Licencias", min_value=0.0, value=450.0, step=50.0)
with col3:
    st.number_input("Producción mensual estimada", min_value=1.0, value=500.0, step=10.0)
st.divider()
col4, col5, col6 = st.columns(3)
with col4:
    st.number_input("Empaque unitario", min_value=0.0, value=6.5, step=0.5)
with col5:
    st.number_input("Etiquetas", min_value=0.0, value=2.5, step=0.5)
with col6:
    st.number_input("Otros insumos", min_value=0.0, value=4.0, step=0.5)
st.markdown("</div>", unsafe_allow_html=True)


st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### Mano de obra")
st.caption("Cuantifica el tiempo dedicado al batch para prorratearlo por unidad.")
col7, col8 = st.columns(2)
with col7:
    st.number_input("Horas por batch", min_value=0.0, value=5.0, step=0.5)
with col8:
    st.number_input("Sueldo por hora", min_value=0.0, value=90.0, step=5.0)
st.markdown("</div>", unsafe_allow_html=True)


st.markdown('<div class="section-card">', unsafe_allow_html=True)
st.markdown("### Margen deseado")
st.caption("Selecciona un preset o define un porcentaje personalizado.")
col9, col10 = st.columns([2, 1])
with col9:
    st.selectbox(
        "Presets de margen",
        options=["10%", "20%", "30%", "40%", "50%", "100%", "Personalizado"],
        index=2,
    )
with col10:
    st.number_input("Margen personalizado (%)", min_value=0.0, value=35.0, step=1.0)
st.toggle("Incluir impuesto", value=False)
st.markdown("</div>", unsafe_allow_html=True)


st.button("Guardar estructura (placeholder)", use_container_width=True, type="primary")
