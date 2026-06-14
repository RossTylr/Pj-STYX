"""Okabe–Ito colourblind-safe palette — the one source of colour for every figure and badge (6l).

LYR-1: no Streamlit, no Plotly — just constants. Builders and pages import from here so a colour is
never hard-coded twice. **Colour never carries state alone**: every encoded state also has a shape,
dash, lane, or text label, so the figures and badges read for the ~8% with colour-vision deficiency.
"""

from __future__ import annotations

# ============================ BRAND CHROME (6h) — non-clinical ===================================
# Pj-STYX brand tokens, derived from the logo mark. These dress the *chrome only* (config theme,
# logo lockup, landing motif). They are the single source shared by app theming and the landing.
# They are NOT clinical encodings: the warm risk ramp and the Okabe–Ito ownership markers below
# carry state and must never be recoloured to match the brand.
BRAND_NAVY = "#15325E"  # headings + body ink
BRAND_TEAL = "#1FA89A"  # accent — links, selected states, the landing STYX line
BRAND_GREY = "#5E6E85"  # muted brand ink, neutral landing-motif dots
BRAND_ALERT = "#E23B2D"  # brand alert flag (labelled urgency only, never a clinical band)
BRAND_RAMP: tuple[str, ...] = ("#7B5FD1", "#2E80D6", "#1FA89A")  # cool brand sweep (chrome, not the warm clinical ramp)
BRAND_SURFACE = "#FFFFFF"  # canvas
BRAND_SURFACE_ALT = "#F5F8FB"  # sidebar + container surfaces
# ====================== CLINICAL-SEMANTIC (6l) — ratified, do not recolour =======================

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

# --- Table inks for warm-ramp-shaded cells (clinical-basis scoring table): near-black on the
# pale stops, warm off-white once the deep-terracotta stop drops below readable contrast. --------
TABLE_INK = "#1A1A1A"
TABLE_INK_ON_DEEP = "#FFF4ED"

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
