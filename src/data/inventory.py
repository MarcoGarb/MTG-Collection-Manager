# src/data/inventory.py
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Dict, Optional, Sequence, Tuple

from ai.inventory_constraints import normalize_name  # relative to src/


DEFAULT_NAME_COLS = ("name", "card_name", "card", "cardname", "card_name_normalized")
DEFAULT_QTY_COLS = ("quantity", "qty", "count", "owned", "owned_qty", "amount")


def _project_root() -> Path:
    # src/data/inventory.py -> parents[0]=src/data, [1]=src, [2]=repo root
    return Path(__file__).resolve().parents[2]


def _candidate_tables(conn: sqlite3.Connection) -> Sequence[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return [r[0] for r in rows]


def _table_columns(conn: sqlite3.Connection, table: str) -> Sequence[Tuple[int, str, str]]:
    # pragma: cid, name, type, notnull, dflt_value, pk
    return conn.execute(f"PRAGMA table_info({table})").fetchall()


def load_inventory_counts_by_name(
    db_path: Optional[Path] = None,
    table_hint: Optional[str] = None,
    name_col_hint: Optional[str] = None,
    qty_col_hint: Optional[str] = None,
) -> Dict[str, int]:
    """
    Returns {normalized_name: total_owned} by introspecting data/collection.db.
    If no suitable table/columns are found, returns {}.
    You can pass explicit hints to skip introspection.
    """
    db_path = db_path or (_project_root() / "data" / "collection.db")
    if not db_path.exists():
        return {}

    conn = sqlite3.connect(str(db_path))
    try:
        tables = [table_hint] if table_hint else list(_candidate_tables(conn))
        for table in tables:
            if not table:
                continue
            cols = _table_columns(conn, table)
            if not cols:
                continue

            col_names = {c[1].lower(): c[1] for c in cols}  # lower -> original
            # pick name col
            name_col = None
            if name_col_hint and name_col_hint.lower() in col_names:
                name_col = col_names[name_col_hint.lower()]
            else:
                for cand in DEFAULT_NAME_COLS:
                    if cand in col_names:
                        name_col = col_names[cand]
                        break
            # pick qty col
            qty_col = None
            if qty_col_hint and qty_col_hint.lower() in col_names:
                qty_col = col_names[qty_col_hint.lower()]
            else:
                for cand in DEFAULT_QTY_COLS:
                    if cand in col_names:
                        qty_col = col_names[cand]
                        break

            if not name_col or not qty_col:
                continue  # try next table

            # aggregate
            sql = f"SELECT {name_col} AS n, SUM({qty_col}) AS q FROM {table} GROUP BY {name_col}"
            counts: Dict[str, int] = {}
            for n, q in conn.execute(sql):
                key = normalize_name(n)
                counts[key] = counts.get(key, 0) + int(q or 0)
            if counts:
                return counts

        # nothing found
        return {}
    finally:
        conn.close()