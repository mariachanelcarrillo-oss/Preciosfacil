# pip install streamlit pandas numpy extra-streamlit-components streamlit-extras
# pip install google-genai  # si se usa el bloque de IA
# (SQLite viene en la stdlib)

from __future__ import annotations

import base64
import io
import os
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import streamlit as st

try:  # pragma: no cover - dependencia opcional
    from dotenv import load_dotenv  # type: ignore
except ImportError:  # pragma: no cover
    def load_dotenv(*_args, **_kwargs):
        return None

from recipes_db import (
    delete_recipe,
    get_recipe,
    get_recipe_ingredients,
    init_db,
    list_recipes,
    replace_recipe_ingredients,
    upsert_recipe,
)
from theme_utils import apply_portada_theme, render_section_header

try:  # pragma: no cover - depende de instalacion opcional
    from google import genai  # type: ignore
except Exception:  # pragma: no cover
    genai = None  # type: ignore

load_dotenv()
ENV_GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

ROLL_IMAGE_PATH = Path(__file__).resolve().parents[1] / "WhatsApp Image 2025-11-13 at 19.26.30.jpeg"


def load_roll_icon_b64() -> str | None:
    if not ROLL_IMAGE_PATH.exists():
        return None
    try:
        return base64.b64encode(ROLL_IMAGE_PATH.read_bytes()).decode("utf-8")
    except Exception:
        return None


ROLL_ICON_B64 = load_roll_icon_b64()

INGREDIENTE_COL = "Ingrediente"
CANTIDAD_COL = "Cantidad por batch"
UNIDAD_COL = "Unidad"
COSTO_COL = "Costo por unidad de medida (MXN por g/ml/pza)"
INGREDIENT_UNITS = ["g", "ml", "pza"]

NAME_KEY = "gramaje_recipe_name"
UNITS_KEY = "gramaje_units_per_batch"
NOTES_KEY = "gramaje_recipe_notes"
ING_TABLE_KEY = "gramaje_editor_table"
ACTIVE_ID_KEY = "gramaje_active_recipe_id"
SELECTOR_KEY = "gramaje_recipe_selector"
UNIDADES_PEDIDO_KEY = "gramaje_unidades_pedido"
MARGEN_KEY = "gramaje_margin_input"
MANUAL_PRICE_KEY = "gramaje_manual_price"
APPLY_MARGIN_KEY = "gramaje_apply_margin"
AI_RESULT_KEY = "gramaje_ai_result"
COST_REF_KEY = "gramaje_cost_reference"
IA_STYLE_APPLIED_KEY = "gramaje_ia_style_applied"


def get_gemini_api_key() -> str | None:
    return ENV_GEMINI_API_KEY


def formatea_moneda(x: float) -> str:
    """$ 12,345.67 para valores positivos y cero."""
    if x is None or np.isnan(x):
        return "$ 0.00"
    return f"$ {x:,.2f}"


def escala_receta(rows: list[dict], units_per_batch: float, unidades_pedido: int) -> pd.DataFrame:
    """Devuelve df con columnas: ingrediente, unidad, qty_total, costo_unit, costo_total."""
    if units_per_batch <= 0 or unidades_pedido <= 0 or not rows:
        df_empty = pd.DataFrame(columns=["ingrediente", "unidad", "qty_total", "costo_unit", "costo_total"])
        df_empty.attrs["unidades_pedido"] = unidades_pedido
        return df_empty

    factor = unidades_pedido / units_per_batch
    data: list[dict[str, Any]] = []
    for row in rows:
        qty_batch = float(row.get("qty_per_batch") or 0.0)
        cost_unit = float(row.get("cost_per_unit_qty") or 0.0)
        qty_total = qty_batch * factor
        costo_total = qty_total * cost_unit
        data.append(
            {
                "ingrediente": row.get("ingredient", ""),
                "unidad": row.get("unit_qty", ""),
                "qty_total": qty_total,
                "costo_unit": cost_unit,
                "costo_total": costo_total,
            }
        )

    df = pd.DataFrame(data)
    df.attrs["unidades_pedido"] = unidades_pedido
    df.attrs["factor"] = factor
    return df


def costo_totales(df_escalado: pd.DataFrame) -> tuple[float, float]:
    """(costo_total_pedido, costo_unitario)"""
    if df_escalado.empty:
        return 0.0, 0.0
    costo_total = float(df_escalado["costo_total"].sum())
    unidades = df_escalado.attrs.get("unidades_pedido") or 0
    costo_unitario = costo_total / unidades if unidades else 0.0
    return costo_total, costo_unitario


def default_ingredient_table() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {INGREDIENTE_COL: "Harina de trigo", CANTIDAD_COL: 1200.0, UNIDAD_COL: "g", COSTO_COL: np.nan},
            {INGREDIENTE_COL: "Azucar mascabado", CANTIDAD_COL: 350.0, UNIDAD_COL: "g", COSTO_COL: np.nan},
            {INGREDIENTE_COL: "Mantequilla / canela", CANTIDAD_COL: 420.0, UNIDAD_COL: "g", COSTO_COL: np.nan},
        ]
    )


def ensure_page_state() -> None:
    defaults = {
        NAME_KEY: "",
        UNITS_KEY: 24.0,
        NOTES_KEY: "",
        ING_TABLE_KEY: default_ingredient_table(),
        ACTIVE_ID_KEY: None,
        SELECTOR_KEY: None,
        UNIDADES_PEDIDO_KEY: 24,
        MARGEN_KEY: 30.0,
        APPLY_MARGIN_KEY: True,
        COST_REF_KEY: 0.0,
        IA_STYLE_APPLIED_KEY: False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def load_recipe_into_form(recipe_id: int | None) -> None:
    if recipe_id is None:
        st.session_state[NAME_KEY] = ""
        st.session_state[UNITS_KEY] = 24.0
        st.session_state[NOTES_KEY] = ""
        st.session_state[ING_TABLE_KEY] = default_ingredient_table()
        return

    recipe = get_recipe(recipe_id)
    ingredients = get_recipe_ingredients(recipe_id)
    st.session_state[NAME_KEY] = recipe.get("name", "")
    st.session_state[UNITS_KEY] = float(recipe.get("units_per_batch") or 0.0)
    st.session_state[NOTES_KEY] = recipe.get("notes") or ""
    if ingredients:
        table_rows = []
        for row in ingredients:
            table_rows.append(
                {
                    INGREDIENTE_COL: row.get("ingredient"),
                    CANTIDAD_COL: float(row.get("qty_per_batch") or 0.0),
                    UNIDAD_COL: row.get("unit_qty") or "g",
                    COSTO_COL: row.get("cost_per_unit_qty"),
                }
            )
        st.session_state[ING_TABLE_KEY] = pd.DataFrame(table_rows)
    else:
        st.session_state[ING_TABLE_KEY] = default_ingredient_table()


def editor_rows_to_db(df: pd.DataFrame) -> list[dict]:
    records: list[dict[str, Any]] = []
    for row in df.to_dict("records"):
        ingredient = (row.get(INGREDIENTE_COL) or "").strip()
        if not ingredient:
            continue
        qty = float(row.get(CANTIDAD_COL) or 0.0)
        if qty < 0:
            raise ValueError("Cada ingrediente debe tener una cantidad mayor o igual a cero.")
        unit = row.get(UNIDAD_COL) or "g"
        cost_value = row.get(COSTO_COL)
        cost = float(cost_value) if cost_value not in (None, "") else None
        records.append(
            {
                "ingredient": ingredient,
                "qty_per_batch": qty,
                "unit_qty": unit,
                "cost_per_unit_qty": cost,
            }
        )
    return records


def inject_ai_button_style() -> None:
    if st.session_state.get(IA_STYLE_APPLIED_KEY):
        return
    image_css = (
        f"background-image:url('data:image/jpeg;base64,{ROLL_ICON_B64}');"
        if ROLL_ICON_B64
        else "background-image:linear-gradient(135deg,#f7eadb,#f3d7b2);"
    )
    st.markdown(
        f"""
        <style>
        div[data-testid="stSidebar"] .stButton button {{
            width: 100%;
            border-radius: 999px;
            background: linear-gradient(135deg, #d9f0c6, #bee3a0);
            border: none;
            color: transparent;
            font-size: 0;
            padding: 1.05rem 1rem;
            box-shadow: 0 12px 24px rgba(0,0,0,0.12);
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 1rem;
            position: relative;
        }}
        div[data-testid="stSidebar"] .stButton button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 16px 30px rgba(0,0,0,0.18);
        }}
        div[data-testid="stSidebar"] .stButton button::before {{
            content: "";
            width: 44px;
            height: 44px;
            border-radius: 14px;
            {image_css}
            background-size: cover;
            background-position: center;
            box-shadow: inset 0 2px 6px rgba(255,255,255,0.6);
        }}
        div[data-testid="stSidebar"] .stButton button::after {{
            content: "Analizar con IA";
            color: #1f2617;
            font-weight: 600;
            letter-spacing: 0.1rem;
            font-size: 0.95rem;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.session_state[IA_STYLE_APPLIED_KEY] = True


def render_recipe_admin(recipes: list[dict]) -> dict:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Administrador de recetas")
    st.caption("Crea, guarda y versiona tus batches maestros.")

    select_col, button_col = st.columns([4, 1], gap="large")
    options = [None] + [recipe["id"] for recipe in recipes]
    labels = {None: "Selecciona una receta"} | {
        recipe["id"]: f"{recipe['name']} - rinde {recipe['units_per_batch']:,.0f} uds" for recipe in recipes
    }
    with select_col:
        selected_id = st.selectbox(
            "Recetas guardadas",
            options=options,
            format_func=lambda opt: labels.get(opt, ""),
            key=SELECTOR_KEY,
        )
    current_recipe_snapshot = next((recipe for recipe in recipes if recipe["id"] == selected_id), {})
    with button_col:
        if st.button("Nueva receta", use_container_width=True):
            load_recipe_into_form(None)
            st.session_state[SELECTOR_KEY] = None
            st.session_state[ACTIVE_ID_KEY] = None
            st.info("Formulario limpio. Captura la nueva receta.")
            current_recipe_snapshot = {}

    if st.session_state.get(ACTIVE_ID_KEY) != selected_id:
        load_recipe_into_form(selected_id)
        st.session_state[ACTIVE_ID_KEY] = selected_id

    with st.form("recipe_form", enter_to_submit=False):
        name = st.text_input("Nombre de la receta", key=NAME_KEY, placeholder="Rollos clasicos con glaseado")
        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            units_per_batch = st.number_input(
                "Unidades por batch",
                min_value=1.0,
                step=1.0,
                key=UNITS_KEY,
                help="Indica cuantos rollos obtienes por preparacion completa.",
            )
        with col_b:
            notes = st.text_area("Notas / recordatorios", key=NOTES_KEY, height=90)

        ingredientes_df = st.data_editor(
            st.session_state[ING_TABLE_KEY],
            key=ING_TABLE_KEY,
            num_rows="dynamic",
            use_container_width=True,
            column_config={
                INGREDIENTE_COL: st.column_config.TextColumn(required=True),
                CANTIDAD_COL: st.column_config.NumberColumn(min_value=0.0, step=10.0),
                UNIDAD_COL: st.column_config.SelectboxColumn(options=INGREDIENT_UNITS),
                COSTO_COL: st.column_config.NumberColumn(
                    min_value=0.0,
                    step=0.5,
                    format="$ %.2f",
                    help="MXN por g/ml/pza (igual que en la pagina 1).",
                ),
            },
            hide_index=True,
        )

        buttons_col, delete_col = st.columns([3, 1])
        with buttons_col:
            save_clicked = st.form_submit_button("Guardar receta", use_container_width=True, type="primary")
        with delete_col:
            delete_clicked = st.form_submit_button(
                "Eliminar", disabled=selected_id is None, type="secondary", use_container_width=True
            )

    if save_clicked:
        try:
            rows = editor_rows_to_db(ingredientes_df)
        except ValueError as exc:
            st.error(str(exc))
            return current_recipe_snapshot

        if not name.strip():
            st.error("Ponle un nombre a la receta antes de guardarla.")
            return current_recipe_snapshot
        if units_per_batch <= 0:
            st.error("Las unidades por batch deben ser mayores a cero.")
            return current_recipe_snapshot
        if not rows:
            st.error("Agrega al menos un ingrediente.")
            return current_recipe_snapshot

        recipe_id = upsert_recipe(name.strip(), units_per_batch, notes.strip() or None)
        replace_recipe_ingredients(recipe_id, rows)
        st.session_state[SELECTOR_KEY] = recipe_id
        st.session_state[ACTIVE_ID_KEY] = recipe_id
        st.success("Receta guardada.")
        load_recipe_into_form(recipe_id)
        st.experimental_rerun()

    if delete_clicked and selected_id is not None:
        delete_recipe(selected_id)
        st.success("Receta eliminada.")
        load_recipe_into_form(None)
        st.session_state[SELECTOR_KEY] = None
        st.session_state[ACTIVE_ID_KEY] = None
        st.experimental_rerun()

    st.markdown("</div>", unsafe_allow_html=True)
    return current_recipe_snapshot


def render_shared_costs_block() -> tuple[float, float | None, float | None, bool]:
    shared_margin = st.session_state.get("margen_pct")
    shared_price = st.session_state.get("precio_sugerido")
    shared_cost = st.session_state.get("costo_unit_total")
    imported = []
    if shared_margin is not None:
        imported.append("margen")
        if MARGEN_KEY not in st.session_state or st.session_state[MARGEN_KEY] == 30.0:
            st.session_state[MARGEN_KEY] = round(shared_margin * 100, 2)
    if shared_price is not None:
        imported.append("precio sugerido")
    if shared_cost is not None:
        imported.append("costo unitario base")

    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Datos compartidos con la pagina de precios")
    st.caption("Usa los inputs de la pagina 1 cuando ya calculaste tu CVu y precio meta.")
    if imported:
        st.markdown(
            f'<div style="padding:0.4rem 1rem;border-radius:999px;background:#EEF7E0;display:inline-block;">'
            f"Datos importados: {', '.join(imported)}</div>",
            unsafe_allow_html=True,
        )

    if shared_cost is not None and (
        st.session_state.get(COST_REF_KEY) == 0.0 or st.session_state.get(COST_REF_KEY) is None
    ):
        st.session_state[COST_REF_KEY] = float(shared_cost)

    col1, col2, col3 = st.columns(3)
    with col1:
        margen_pct = st.number_input(
            "Margen deseado (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=MARGEN_KEY,
        ) / 100
    with col2:
        costo_manual = st.number_input(
            "Costo unitario desde pagina 1 (opcional)",
            min_value=0.0,
            step=1.0,
            format="%0.2f",
            key=COST_REF_KEY,
            help="Solo para referencia visual; no modifica la receta.",
        )
    with col3:
        apply_margin = st.checkbox(
            "Aplicar margen sobre el costo calculado del gramaje?",
            key=APPLY_MARGIN_KEY,
            help="Si desactivas este checkbox podras fijar un precio manual.",
        )

    price_reference = shared_price
    st.markdown("</div>", unsafe_allow_html=True)
    return margen_pct, price_reference, costo_manual or None, apply_margin


def build_excel_file(resumen_df: pd.DataFrame, ingredientes_df: pd.DataFrame) -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        resumen_df.to_excel(writer, sheet_name="Resumen", index=False)
        ingredientes_df.to_excel(writer, sheet_name="Ingredientes", index=False)
        workbook = writer.book
        currency_fmt = workbook.add_format({"num_format": '"$"#,##0.00'})
        worksheet_resumen = writer.sheets["Resumen"]
        worksheet_ing = writer.sheets["Ingredientes"]
        worksheet_resumen.set_column("A:A", 30)
        worksheet_resumen.set_column("B:B", 24, currency_fmt)
        worksheet_ing.set_column("A:B", 28)
        worksheet_ing.set_column("C:D", 18)
        worksheet_ing.set_column("E:E", 20, currency_fmt)
    buffer.seek(0)
    return buffer.getvalue()


def render_scaler_section(
    recipe: dict,
    recipes_lookup: dict[int, list[dict]],
    margen_pct: float,
    price_reference: float | None,
    apply_margin: bool,
) -> tuple[pd.DataFrame, dict]:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Escalador de pedido")
    st.caption("Calcula cantidades y costos totales para pedidos puntuales.")

    if not recipe:
        st.info("Selecciona y guarda una receta para poder escalarla.")
        st.markdown("</div>", unsafe_allow_html=True)
        return pd.DataFrame(), {}

    unidades_pedido = st.number_input(
        "Unidades a producir (pedido)",
        min_value=1,
        step=1,
        key=UNIDADES_PEDIDO_KEY,
    )

    recipe_rows = recipes_lookup.get(recipe["id"], [])
    if recipe["units_per_batch"] <= 0:
        st.warning("La receta seleccionada no tiene unidades por batch validas.")
        st.markdown("</div>", unsafe_allow_html=True)
        return pd.DataFrame(), {}
    if not recipe_rows:
        st.warning("Esta receta no tiene ingredientes registrados aun.")
        st.markdown("</div>", unsafe_allow_html=True)
        return pd.DataFrame(), {}

    df_escalado = escala_receta(recipe_rows, recipe["units_per_batch"], int(unidades_pedido))
    costo_total_pedido, costo_unitario = costo_totales(df_escalado)

    precio_unitario = None
    precio_fuente = ""
    if price_reference and price_reference > 0:
        precio_unitario = float(price_reference)
        precio_fuente = "Precio importado de la pagina 1"
    elif apply_margin:
        precio_unitario = costo_unitario * (1 + margen_pct)
        precio_fuente = "Margen aplicado"
    else:
        if MANUAL_PRICE_KEY not in st.session_state:
            st.session_state[MANUAL_PRICE_KEY] = max(costo_unitario * 1.2, 1.0)
        precio_unitario = st.number_input(
            "Precio unitario manual",
            min_value=0.0,
            step=1.0,
            format="%0.2f",
            key=MANUAL_PRICE_KEY,
        )
        precio_fuente = "Precio manual"

    if not precio_unitario or precio_unitario <= 0:
        precio_unitario = st.number_input(
            "Define un precio valido para continuar",
            min_value=0.0,
            value=float(max(costo_unitario, 1.0)),
            step=1.0,
        )
        precio_fuente = "Precio manual requerido"

    ingreso_total = precio_unitario * unidades_pedido
    ganancia = ingreso_total - costo_total_pedido

    df_display = df_escalado.copy()
    df_display["Cantidad total"] = df_display["qty_total"]
    df_display["Costo unitario usado"] = df_display["costo_unit"]
    df_display["Costo total"] = df_display["costo_total"]
    df_display = df_display[["ingrediente", "unidad", "Cantidad total", "Costo unitario usado", "Costo total"]]
    df_display.rename(
        columns={
            "ingrediente": "Ingrediente",
            "unidad": "Unidad",
        },
        inplace=True,
    )
    st.dataframe(
        df_display.style.format(
            {
                "Cantidad total": "{:,.2f}",
                "Costo unitario usado": "$ {:,.4f}",
                "Costo total": "$ {:,.2f}",
            }
        ),
        use_container_width=True,
        hide_index=True,
    )

    if (df_escalado["costo_unit"] == 0).any():
        faltantes = df_escalado.loc[df_escalado["costo_unit"] == 0, "ingrediente"].tolist()
        st.warning(
            "Faltan costos unitarios para: " + ", ".join(faltantes) + ". Completa la columna en el administrador."
        )

    kpi_cols = st.columns(4, gap="large")
    kpi_values = [
        ("Costo por unidad", formatea_moneda(costo_unitario)),
        ("Precio por unidad", formatea_moneda(precio_unitario)),
        ("Costo total del pedido", formatea_moneda(costo_total_pedido)),
        ("Ganancia estimada", formatea_moneda(ganancia)),
    ]
    for col, (label, value) in zip(kpi_cols, kpi_values):
        with col:
            st.markdown(f'<div class="pe-card"><div class="pe-section-title">{label}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="pe-value">{value}</div></div>', unsafe_allow_html=True)

    resumen_df = pd.DataFrame(
        [
            {"Variable": "Receta", "Valor": recipe["name"]},
            {"Variable": "Unidades por batch", "Valor": recipe["units_per_batch"]},
            {"Variable": "Unidades del pedido", "Valor": unidades_pedido},
            {"Variable": "Factor de escala", "Valor": df_escalado.attrs.get("factor", 0)},
            {"Variable": "Costo total del pedido", "Valor": costo_total_pedido},
            {"Variable": "Costo por unidad", "Valor": costo_unitario},
            {"Variable": "Precio unitario aplicado", "Valor": precio_unitario},
            {"Variable": "Margen considerado", "Valor": margen_pct},
            {"Variable": "Fuente del precio", "Valor": precio_fuente},
            {"Variable": "Ingreso total", "Valor": ingreso_total},
            {"Variable": "Ganancia estimada", "Valor": ganancia},
        ]
    )

    ingredientes_excel = df_display.rename(
        columns={
            "Cantidad total": "Cantidad total",
            "Costo unitario usado": "Costo unitario usado (MXN)",
            "Costo total": "Costo total (MXN)",
        }
    )

    excel_bytes = build_excel_file(resumen_df, ingredientes_excel)
    nombre_archivo = f"pedido_{recipe['name'].lower().replace(' ', '_')}.xlsx"
    st.download_button(
        "Descargar Excel con resumen e ingredientes",
        data=excel_bytes,
        file_name=nombre_archivo,
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
    st.caption(precio_fuente)
    st.markdown("</div>", unsafe_allow_html=True)

    kpi_data = {
        "costo_unitario": costo_unitario,
        "precio_unitario": precio_unitario,
        "costo_total_pedido": costo_total_pedido,
        "ganancia": ganancia,
        "unidades_pedido": unidades_pedido,
    }
    return df_escalado, kpi_data


def build_recipes_lookup(recipes: list[dict]) -> dict[int, list[dict]]:
    lookup: dict[int, list[dict]] = {}
    for recipe in recipes:
        lookup[recipe["id"]] = get_recipe_ingredients(recipe["id"])
    return lookup


def estimate_cost_per_unit(recipe: dict, ingredients: list[dict]) -> float | None:
    if not recipe or recipe.get("units_per_batch", 0) <= 0 or not ingredients:
        return None
    total = 0.0
    for row in ingredients:
        qty = float(row.get("qty_per_batch") or 0.0)
        cost = float(row.get("cost_per_unit_qty") or 0.0)
        total += qty * cost
    if total == 0:
        return None
    return total / float(recipe["units_per_batch"])


def render_ai_block(
    recipe: dict,
    recipes_lookup: dict[int, list[dict]],
    df_escalado: pd.DataFrame,
    pedido_kpis: dict,
    shared_cost_manual: float | None,
    all_recipes: list[dict],
) -> None:
    api_key = get_gemini_api_key()
    with st.sidebar:
        st.markdown("### IA  Gemini")
        if not api_key:
            st.warning("Configura GEMINI_API_KEY en tu entorno para habilitar el analisis.")
        inject_ai_button_style()
        analizar = st.button(
            "Analizar con IA",
            key="gramaje_ia_button",
            use_container_width=True,
            disabled=api_key is None,
            help="Ejecuta el analisis de recetas usando Gemini.",
        )

    if not api_key or not analizar:
        return
    if genai is None:
        st.sidebar.error("Instala google-genai para activar este bloque (pip install google-genai).")
        return
    if not recipe or df_escalado.empty:
        st.sidebar.warning("Necesitas una receta con ingredientes y un pedido calculado.")
        return

    shared_state = {
        "costo_unit_total": st.session_state.get("costo_unit_total"),
        "precio_sugerido": st.session_state.get("precio_sugerido"),
        "margen_pct": st.session_state.get("margen_pct"),
        "fijos_mensuales": st.session_state.get("fijos_mensuales"),
        "q_be": st.session_state.get("q_be") or st.session_state.get("Q_BE"),
    }

    recipes_summary = []
    for recipe_row in all_recipes:
        costo_estimado = estimate_cost_per_unit(recipe_row, recipes_lookup.get(recipe_row["id"], []))
        recipes_summary.append(
            {
                "name": recipe_row["name"],
                "units_per_batch": recipe_row["units_per_batch"],
                "costo_unitario_estimado": costo_estimado,
            }
        )

    context_lines = [
        "Analiza la operacion de rollos de canela considerando estas tres vistas:",
        "1) Pagina 1 - calculo de costos y precio objetivo.",
        "2) Pagina 2 - punto de equilibrio y costos fijos.",
        "3) Pagina 3 - gramaje y escalado del pedido actual.",
        "",
        f"Receta seleccionada: {recipe['name']} (rinde {recipe['units_per_batch']:,.0f} unidades por batch).",
        "Ingredientes normalizados (costo MXN por unidad base):",
    ]
    for row in recipes_lookup.get(recipe["id"], []):
        costo = row.get("cost_per_unit_qty")
        costo_txt = f"$ {costo:,.4f}" if costo not in (None, 0) else "sin costo definido"
        context_lines.append(
            f"- {row['ingredient']}: {row['qty_per_batch']} {row['unit_qty']} por batch, costo unitario {costo_txt}"
        )

    context_lines.append("")
    context_lines.append(
        f"Pedido analizado: {pedido_kpis.get('unidades_pedido', 0):,.0f} unidades "
        f"-> costo por unidad {formatea_moneda(pedido_kpis.get('costo_unitario', 0))}, "
        f"precio aplicado {formatea_moneda(pedido_kpis.get('precio_unitario', 0))}, "
        f"ganancia estimada {formatea_moneda(pedido_kpis.get('ganancia', 0))}."
    )

    if shared_state["costo_unit_total"]:
        context_lines.append(
            f"Costo variable unitario desde pagina 1: {formatea_moneda(shared_state['costo_unit_total'])}."
        )
    if shared_state["precio_sugerido"]:
        context_lines.append(f"Precio sugerido global: {formatea_moneda(shared_state['precio_sugerido'])}.")
    if shared_state["fijos_mensuales"]:
        context_lines.append(f"Costos fijos mensuales (pagina 2): {formatea_moneda(shared_state['fijos_mensuales'])}.")
    if shared_state["q_be"]:
        context_lines.append(f"Volumen de equilibrio estimado: {shared_state['q_be']:,.0f} unidades / mes.")
    if shared_cost_manual:
        context_lines.append(f"Costos manuales capturados en esta pagina: {formatea_moneda(shared_cost_manual)}.")

    context_lines.append("")
    context_lines.append("Resumen de recetas guardadas en la DB local:")
    for resumen in recipes_summary:
        costo_txt = (
            formatea_moneda(resumen["costo_unitario_estimado"])
            if resumen["costo_unitario_estimado"] is not None
            else "sin datos"
        )
        context_lines.append(
            f"- {resumen['name']}  {resumen['units_per_batch']:,.0f} uds/batch  costo estimado {costo_txt}"
        )

    context_lines.append("")
    context_lines.append(
        "Responde en espanol: "
        "1) Que receta ofrece mejor costo/beneficio segun los datos? "
        "2) Que ajustes de gramaje sugieres para maximizar margen sin comprometer calidad? "
        "3) Conviene subir precio o reducir costo variable? Da 3 acciones accionables."
    )

    prompt = "\n".join(context_lines)
    client = genai.Client(api_key=api_key)  # type: ignore[call-arg]
    with st.spinner("Analizando recetas con Gemini..."):
        try:
            response = client.responses.generate(
                model="gemini-2.5-flash",
                contents=[{"role": "user", "parts": [{"text": prompt}]}],
            )
        except Exception as exc:  # pragma: no cover - depende de API
            st.sidebar.error(f"No pude ejecutar Gemini: {exc}")
            return

    ai_text = getattr(response, "output_text", None)
    if not ai_text:
        candidates = getattr(response, "candidates", [])
        fragments = []
        for candidate in candidates:
            content = getattr(candidate, "content", None)
            if not content:
                continue
            for part in getattr(content, "parts", []):
                text = getattr(part, "text", "")
                if text:
                    fragments.append(text)
        ai_text = "\n".join(fragments) if fragments else "Sin respuesta legible."

    st.session_state[AI_RESULT_KEY] = ai_text


def render_ai_result() -> None:
    st.markdown('<div class="section-card">', unsafe_allow_html=True)
    st.markdown("### Insight de Gemini")
    ai_text = st.session_state.get(AI_RESULT_KEY)
    if ai_text:
        st.markdown(ai_text)
    else:
        if get_gemini_api_key():
            st.info("Ejecuta el analisis desde el panel lateral para obtener una recomendacion.")
        else:
            st.info("El analisis IA se activara cuando vincules tu clave de Gemini en el entorno.")
    st.markdown("</div>", unsafe_allow_html=True)


def render_calculadora_gramaje(embed: bool = False, show_header: bool = True) -> None:
    if not embed:
        st.set_page_config(page_title="Calculadora de gramaje", page_icon=":scales:", layout="wide")
        apply_portada_theme()
        if show_header:
            render_section_header("Calculadora de gramaje", "Crea, guarda y escala tus recetas.", show_roll=False)
    else:
        if show_header:
            st.markdown("### Calculadora de gramaje")
            st.caption("Crea, guarda y escala tus recetas.")

    init_db()
    ensure_page_state()

    recipes = list_recipes()
    recipes_lookup = build_recipes_lookup(recipes)
    recipe = render_recipe_admin(recipes)
    margen_pct, price_reference, shared_cost_manual, apply_margin = render_shared_costs_block()
    df_escalado, pedido_kpis = render_scaler_section(
        recipe=recipe or {},
        recipes_lookup=recipes_lookup,
        margen_pct=margen_pct,
        price_reference=price_reference,
        apply_margin=apply_margin,
    )
    render_ai_block(recipe or {}, recipes_lookup, df_escalado, pedido_kpis, shared_cost_manual, recipes)
    render_ai_result()


def main() -> None:
    render_calculadora_gramaje()


if __name__ == "__main__":
    main()
