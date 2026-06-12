"""Warm-ramp NEWS2 scoring table (Table A) — a pandas Styler, streamlit-free (LYR-1).

Cells are coloured by the NEWS2 point of their column using the *same* ramp as the clinical
trajectory schematic: the schematic shades by the summed two-vital sub-score (0–6), and a single
parameter scoring p sits at sum 2p, so each table cell is literally a stop of the schematic's own
``palette.WARM_RAMP`` — the assets-pack §E hexes by construction, single-sourced, never decoration.
"""

from __future__ import annotations

import pandas as pd
from pandas.io.formats.style import Styler

from styx.clinical_basis import TABLE_A_COLUMNS, TABLE_A_ROWS, TABLE_A_SCORES
from styx.viz.palette import TABLE_INK, TABLE_INK_ON_DEEP, WARM_RAMP

#: NEWS2 point (0–3) → ramp stop. WARM_RAMP[2p] ≡ the assets §E literals.
RAMP_FOR_POINT: dict[int, str] = {p: WARM_RAMP[2 * p] for p in range(4)}
#: NEWS2 point → ink with readable contrast on that stop.
INK_FOR_POINT: dict[int, str] = {0: TABLE_INK, 1: TABLE_INK, 2: TABLE_INK, 3: TABLE_INK_ON_DEEP}


def scoring_table_styler() -> Styler:
    """Table A (NEWS2 Scale 1, the four SIG-1 vitals) with cells shaded by column point value."""
    df = pd.DataFrame(
        {param: list(cells) for param, cells in TABLE_A_ROWS.items()}, index=TABLE_A_COLUMNS
    ).T
    df.columns = list(TABLE_A_COLUMNS)

    def colour_col(col: pd.Series) -> list[str]:
        point = TABLE_A_SCORES[TABLE_A_COLUMNS.index(col.name)]
        style = f"background-color: {RAMP_FOR_POINT[point]}; color: {INK_FOR_POINT[point]}"
        return [style for _ in col]

    return df.style.apply(colour_col, axis=0)
