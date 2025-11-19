"""Utilidades para persistir recetas en SQLite."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Iterable

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = Path("recipes.db")
_ACTIVE_DB_PATH = DEFAULT_DB_PATH

RECIPES_SCHEMA = """
CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    units_per_batch REAL NOT NULL,
    notes TEXT
);
"""

INGREDIENTS_SCHEMA = """
CREATE TABLE IF NOT EXISTS recipe_ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    ingredient TEXT NOT NULL,
    qty_per_batch REAL NOT NULL,
    unit_qty TEXT NOT NULL,
    cost_per_unit_qty REAL,
    FOREIGN KEY(recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);
"""


def _get_connection() -> sqlite3.Connection:
    path = _ACTIVE_DB_PATH
    conn = sqlite3.connect(path if isinstance(path, str) else str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: str = "recipes.db") -> None:
    """Inicializa la base de datos garantizando las tablas necesarias."""
    global _ACTIVE_DB_PATH
    resolved_path = Path(db_path)
    if not resolved_path.parent.exists():
        resolved_path.parent.mkdir(parents=True, exist_ok=True)
    _ACTIVE_DB_PATH = resolved_path
    try:
        with _get_connection() as conn:
            conn.executescript(RECIPES_SCHEMA + INGREDIENTS_SCHEMA)
    except sqlite3.Error as exc:
        logger.exception("No pude inicializar la base de datos: %s", exc)
        raise RuntimeError("Error inicializando la base de datos de recetas.") from exc


def upsert_recipe(name: str, units_per_batch: float, notes: str | None = None) -> int:
    """Crea o actualiza una receta por nombre y devuelve su id."""
    if not name.strip():
        raise ValueError("El nombre de la receta no puede estar vacio.")
    if units_per_batch <= 0:
        raise ValueError("Las unidades por batch deben ser mayores a cero.")
    try:
        with _get_connection() as conn:
            conn.execute(
                """
                INSERT INTO recipes (name, units_per_batch, notes)
                VALUES (?, ?, ?)
                ON CONFLICT(name)
                DO UPDATE SET units_per_batch=excluded.units_per_batch,
                              notes=excluded.notes
                """,
                (name.strip(), float(units_per_batch), notes),
            )
            cursor = conn.execute("SELECT id FROM recipes WHERE name = ?", (name.strip(),))
            row = cursor.fetchone()
            if not row:
                raise RuntimeError("No se pudo recuperar la receta recien guardada.")
            return int(row["id"])
    except sqlite3.Error as exc:
        logger.exception("Fallo al guardar la receta '%s': %s", name, exc)
        raise RuntimeError("No pude guardar la receta en la base de datos.") from exc


def replace_recipe_ingredients(recipe_id: int, rows: list[dict]) -> None:
    """Reemplaza todos los ingredientes de una receta."""
    sanitized: list[tuple] = []
    for row in rows:
        ingredient = (row.get("ingredient") or "").strip()
        if not ingredient:
            continue
        qty = float(row.get("qty_per_batch") or 0.0)
        unit = (row.get("unit_qty") or "g").strip() or "g"
        cost_value = row.get("cost_per_unit_qty")
        cost = float(cost_value) if cost_value not in (None, "") else None
        sanitized.append((recipe_id, ingredient, qty, unit, cost))
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM recipe_ingredients WHERE recipe_id = ?", (recipe_id,))
            if sanitized:
                conn.executemany(
                    """
                    INSERT INTO recipe_ingredients
                    (recipe_id, ingredient, qty_per_batch, unit_qty, cost_per_unit_qty)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    sanitized,
                )
    except sqlite3.Error as exc:
        logger.exception("Fallo al actualizar ingredientes de la receta %s: %s", recipe_id, exc)
        raise RuntimeError("No pude actualizar los ingredientes de la receta.") from exc


def _rows_to_dicts(rows: Iterable[sqlite3.Row]) -> list[dict]:
    return [dict(row) for row in rows]


def list_recipes() -> list[dict]:
    """Devuelve todas las recetas disponibles."""
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, units_per_batch, notes FROM recipes ORDER BY name COLLATE NOCASE"
            )
            return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as exc:
        logger.exception("No pude listar las recetas: %s", exc)
        raise RuntimeError("Error al consultar las recetas guardadas.") from exc


def get_recipe(recipe_id: int) -> dict:
    """Recupera una receta especifica."""
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                "SELECT id, name, units_per_batch, notes FROM recipes WHERE id = ?",
                (recipe_id,),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}
    except sqlite3.Error as exc:
        logger.exception("No pude obtener la receta %s: %s", recipe_id, exc)
        raise RuntimeError("Error al consultar la receta solicitada.") from exc


def get_recipe_ingredients(recipe_id: int) -> list[dict]:
    """Obtiene los ingredientes de una receta."""
    try:
        with _get_connection() as conn:
            cursor = conn.execute(
                """
                SELECT id, ingredient, qty_per_batch, unit_qty, cost_per_unit_qty
                FROM recipe_ingredients
                WHERE recipe_id = ?
                ORDER BY id
                """,
                (recipe_id,),
            )
            return _rows_to_dicts(cursor.fetchall())
    except sqlite3.Error as exc:
        logger.exception("No pude obtener los ingredientes de la receta %s: %s", recipe_id, exc)
        raise RuntimeError("Error al consultar los ingredientes de la receta.") from exc


def delete_recipe(recipe_id: int) -> None:
    """Elimina una receta junto con sus ingredientes."""
    try:
        with _get_connection() as conn:
            conn.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
    except sqlite3.Error as exc:
        logger.exception("No pude eliminar la receta %s: %s", recipe_id, exc)
        raise RuntimeError("Error al eliminar la receta.") from exc
