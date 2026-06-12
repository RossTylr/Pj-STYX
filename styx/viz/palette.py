"""Okabe–Ito colourblind-safe palette — the one source of colour for every figure and badge (6l).

LYR-1: no Streamlit, no Plotly — just constants. Builders and pages import from here so a colour is
never hard-coded twice. **Colour never carries state alone**: every encoded state also has a shape,
dash, lane, or text label, so the figures and badges read for the ~8% with colour-vision deficiency.
"""

from __future__ import annotations

# --- Okabe–Ito base swatches (plus a neutral grey, which the 8-colour set omits) ---------------
BLACK = "#000000"
ORANGE = "#E69F00"
SKY_BLUE = "#56B4E9"
BLUISH_GREEN = "#009E73"
YELLOW = "#F0E442"
BLUE = "#0072B2"
VERMILLION = "#D55E00"
REDDISH_PURPLE = "#CC79A7"
GREY = "#999999"

# --- Semantic roles (what a colour *means* in STYX) — builders use these, never raw swatches ----
RISK = BLUE  # observed risk, the forecast path
NOW = BLUE  # the "now" marker
THRESHOLD = VERMILLION  # the escalation line, the absolute breach, the crisis attractor
EARLY_WARNING = ORANGE  # AEGIS, the hindsight forecast, the ETA band
STABLE = BLUISH_GREEN  # the stability basin, the recovered outcome
NEUTRAL = GREY  # the trajectory line, fallbacks
COMPARATOR = BLACK  # the named-standard NEWS2 marker
ANNOTATION = "#222222"  # near-black guide lines (the "now" rule)

# --- Faint fills (same hues, low opacity) for bands and zones ----------------------------------
RISK_FILL = "rgba(0,114,178,0.12)"
CONE_FILL = "rgba(0,114,178,0.18)"
ZONE_OPACITY = 0.18

# --- Warm risk ramp (clinical trajectory background) — white (0 pts) → deep terracotta (6 pts).
# Indexed by the NEWS2 Scale-1 sub-score for the two plotted vitals (SpO₂ + RR), so the shading
# *is* the comparator's own points field, not decoration. Single warm hue (no red–green pair). ---
WARM_RAMP: tuple[str, ...] = (
    "#FFFFFF", "#FBEFE7", "#F7D9C6", "#F1BE9F", "#E79C74", "#D9764A", "#C4532D",
)

# --- Theograph care-event channels (fixed order; one distinguishable swatch each) --------------
CHANNELS: dict[str, str] = {
    "primary_care": BLUISH_GREEN,
    "ae": VERMILLION,
    "non_elective_admission": ORANGE,
    "outpatient": BLUE,
    "mental_health": REDDISH_PURPLE,
    "social_care": GREY,
}

# --- ECHO neighbour outcomes (colour + a dash in the builder, so never hue alone) --------------
OUTCOMES: dict[str, str] = {"escalated": VERMILLION, "recovered": BLUISH_GREEN}

# --- Ward watch-flag badges — Streamlit badge colour names (the flag *text* carries the meaning;
# the colour is a redundant cue only). Kept here so every colour decision lives in one module. ---
WARD_FLAG_BADGE: dict[str, str] = {
    "silent_but_rising": "orange",
    "quietest": "green",
    "new_low_history": "violet",
}

# --- (6k) Ward-card urgency-tier badges — keyed by ``styx.cohort.watch_tier`` output. Same
# principle: the tier *word* carries the meaning, the colour is a redundant cue only. ------------
WATCH_TIER_BADGE: dict[str, str] = {
    "review_now": "red",
    "this_hour": "orange",
    "watch": "gray",
}
