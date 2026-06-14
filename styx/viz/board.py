"""(S-board) Routine-board renderers — the ward deck as a clinical-instrument board (LYR-1).

Pure: data in → HTML/SVG string out. No Streamlit, no I/O, no RNG. The page injects ``BOARD_CSS``
once and renders these strings via ``st.markdown(..., unsafe_allow_html=True)``; swapping the front
end touches nothing here.

Colour discipline (matches ``styx.viz.palette``'s rule): the band ramp (green/amber/red) carries the
**NEWS2 band signal only**; the STYX teal accent is identity/trend, never a clinical band. Every
number is monospaced. No fabricated data — callers pass values the model already produces.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from html import escape

from styx.readouts import NEWS2_RED, NEWS2_TRIGGER, news2_subscores_at
from styx.synth.cohort import Patient

# --- light clinical tokens (reused from the news2-explainer / clinical-basis palette) ----------
_INK = "#13202B"
_INK_2 = "#44525F"
_INK_3 = "#71808D"
_LINE = "#E1E6EB"
_CARD = "#FFFFFF"
_TEAL = "#0B6E75"  # STYX accent — identity / trend only, never a band signal
#: NEWS2 band ramp — the one place band colour is allowed (keyed by ``band_of`` output).
BAND_COLOUR: dict[str, str] = {"low": "#2E7D5B", "med": "#D8661C", "high": "#C32232"}

#: Beds across a bay's fixed grid — the bay reads as physical bed positions, not a triage queue.
#: Rows grow to hold the largest ward; spare slots render as vacant tiles (``vacant_tile_html``).
BAY_COLS: int = 6


# --- NEWS2-at-clock --------------------------------------------------------------------------

@dataclass(frozen=True)
class News2Now:
    """A patient's NEWS2 standing at the replay clock — the card's primary signal."""

    aggregate: int
    subscores: dict[str, int]  # param label -> 0..3 (only the scored params)
    band: str  # "low" | "med" | "high" (band_of)
    single_red: bool  # any single parameter scores a red NEWS2_RED


def band_of(aggregate: int, single_red: bool) -> str:
    """RCP-2017 banding for the card colour: a single red lifts an otherwise-low score to medium."""
    if aggregate >= NEWS2_TRIGGER + 2:  # 7+ → high
        return "high"
    if aggregate >= NEWS2_TRIGGER or single_red:  # 5–6, or any single red → medium
        return "med"
    return "low"


def news2_now(patient: Patient, idx: int) -> News2Now:
    """Build the NEWS2 standing at sample ``idx`` from the existing comparator subscores."""
    subs = news2_subscores_at(patient, idx)
    aggregate = sum(subs.values())
    single_red = any(s >= NEWS2_RED for s in subs.values())
    return News2Now(aggregate, subs, band_of(aggregate, single_red), single_red)


# --- real-vital readings (P0-2) --------------------------------------------------------------
# A read-only slice of ``patient.vitals`` so the card shows the actual saturation as a percentage
# (``SpO₂ 91% ↓ (was 96)``), never a bare NEWS2 sub-score. No scoring, no synthetic data.

@dataclass(frozen=True)
class VitalReading:
    """One vital at the clock vs the patient's own early-stay baseline (for the card's vitals line)."""

    label: str  # display label, e.g. "SpO₂", "RR"
    value: int  # reading at the clock, rounded
    prior: int  # personal baseline (mean of the first samples), rounded
    unit: str  # "%" for SpO₂, "" for a count like RR
    trend: str  # "↑" | "↓" | "→" vs baseline (±deadband)


def vital_reading(
    patient: Patient, key: str, idx: int, *, label: str, unit: str,
    deadband: float = 2.0, baseline_n: int = 24,
) -> VitalReading:
    """Read ``patient.vitals[key]`` at ``idx`` and against its early-stay baseline (read-only)."""
    series = patient.vitals[key]
    value = int(round(float(series[idx])))
    prior = int(round(float(series[:baseline_n].mean())))
    delta = value - prior
    trend = "↑" if delta >= deadband else "↓" if delta <= -deadband else "→"
    return VitalReading(label, value, prior, unit, trend)


# --- card state vocabulary (P0-1) ------------------------------------------------------------
#: The approved ward-card state tokens — the only strings rendered with the ``styx-state`` marker.
#: Short and break-safe (no mid-word hyphen); the long ``silent-hypoxia-like`` forms are retired.
APPROVED_STATES: frozenset[str] = frozenset(
    {"silent hypoxia", "stable", "recovering", "early signal", "deteriorating — silent"}
)


def card_labels(flagged: bool, receding: bool) -> dict:
    """(badge, verdict, verdict_state) for a card. Flagged → the STYX verdict leads and is a state
    token; calm → a quiet ``stable``/``recovering`` badge with a descriptive (non-token) verdict."""
    if flagged:
        return {"badge": "early signal", "verdict": "deteriorating — silent", "verdict_state": True}
    badge = "recovering" if receding else "stable"
    return {"badge": badge, "verdict": "nominal — no drift", "verdict_state": False}


# --- ward rollup -----------------------------------------------------------------------------

@dataclass(frozen=True)
class Rollup:
    """A ward banner's live aggregate over its beds (occupancy = live count; no capacity modelled)."""

    occupancy: int
    high: int
    med: int
    max_news2: int


def ward_status(rollup: Rollup) -> str:
    """The banner's STEADY / BUSY / SURGE state (capacity + overdue dropped — no backing data)."""
    if rollup.high >= 2:
        return "SURGE"
    if rollup.high == 1 or rollup.med >= 2:
        return "BUSY"
    return "STEADY"


# --- inline SVG sparkline + trend arrow ------------------------------------------------------

def trend_arrow(history: Sequence[float]) -> str:
    """Up / flat / down arrow from the recent slope of the STYX risk history (≥0.01 risk = a move)."""
    if len(history) < 4:
        return "→"
    half = len(history) // 2
    delta = (sum(history[half:]) / len(history[half:])) - (sum(history[:half]) / half)
    return "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"


def sparkline_svg(history: Sequence[float], *, width: int = 72, height: int = 22) -> str:
    """A STYX-teal polyline of the risk history on a fixed [0, 1] scale (inline SVG, no Plotly)."""
    if not history:
        return ""
    n = len(history)
    pad = 2.0
    span_x, span_y = width - 2 * pad, height - 2 * pad
    step = span_x / max(n - 1, 1)
    pts = " ".join(
        f"{pad + i * step:.1f},{pad + (1.0 - min(max(v, 0.0), 1.0)) * span_y:.1f}"
        for i, v in enumerate(history)
    )
    return (
        f'<svg class="styx-spark" width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        f'preserveAspectRatio="none" aria-hidden="true">'
        f'<polyline points="{pts}" fill="none" stroke="{_TEAL}" stroke-width="1.5" '
        f'stroke-linejoin="round" stroke-linecap="round"/></svg>'
    )


# --- HTML fragments --------------------------------------------------------------------------

def _vitals_html(readings: Sequence[VitalReading]) -> str:
    """The vitals line: ``SpO₂ 91% ↓ (was 96)`` — real value + unit + trend glyph, prior on a move."""
    spans = []
    for r in readings:
        was = f' <span class="styx-was">(was {r.prior})</span>' if r.trend != "→" else ""
        spans.append(
            f'<span class="styx-vital">{escape(r.label)} '
            f'<b>{r.value}{escape(r.unit)}</b> {r.trend}{was}</span>'
        )
    return f'<div class="styx-vitals">{"".join(spans)}</div>'


def _stat(n: int, label: str) -> str:
    return f'<span class="styx-stat"><b>{n}</b> {label}</span>'


def banner_html(label: str, rollup: Rollup) -> str:
    """One ward banner: name + live rollup + the derived STEADY/BUSY/SURGE status tag."""
    status = ward_status(rollup)
    return (
        f'<div class="styx-banner styx-status-{status.lower()}">'
        f'<div class="styx-banner-name">{escape(label)}</div>'
        f'<div class="styx-banner-stats">'
        f'{_stat(rollup.occupancy, "beds")}{_stat(rollup.high, "high")}'
        f'{_stat(rollup.med, "med")}{_stat(rollup.max_news2, "max NEWS2")}'
        f'</div><div class="styx-banner-status">{status}</div></div>'
    )


def card_html(
    pid: int, ward_label: str, n2: News2Now, *,
    flagged: bool, receding: bool, vitals: Sequence[VitalReading],
    sub_line: str, arrow: str, sparkline: str,
) -> str:
    """One patient card (P0-3 hierarchy): for a STYX-flagged bed the verdict (state + trend +
    lead-time) is primary and NEWS2 is a muted foot line *after* it; calm beds recede. The accent
    colour owns dot + border + verdict together so the encodings cannot disagree."""
    lab = card_labels(flagged, receding)
    accent = (BAND_COLOUR["high"] if n2.band == "high" else BAND_COLOUR["med"]) if flagged \
        else BAND_COLOUR["low"]
    verdict_cls = "styx-verdict-txt styx-state" if lab["verdict_state"] else "styx-verdict-txt"
    foot = (f"NEWS2 {n2.aggregate} · below trigger"
            if flagged and n2.aggregate < NEWS2_TRIGGER else f"NEWS2 {n2.aggregate}")
    bar = '<div class="styx-card-bar"></div>' if flagged else ""
    flag_cls = " styx-flag" if flagged else ""
    return (
        f'<div class="styx-card styx-card-v{flag_cls}" style="--accent:{accent}">'
        f'{bar}'
        f'<div class="styx-card-head">'
        f'<span class="styx-pid">Bed {pid} · {escape(ward_label)}</span>'
        f'<span class="styx-badge"><span class="styx-dot"></span>'
        f'<span class="styx-state">{escape(lab["badge"])}</span></span></div>'
        f'<div class="styx-verdict"><span class="styx-arrow">{arrow}</span>'
        f'<span class="{verdict_cls}">{escape(lab["verdict"])}</span></div>'
        f'<div class="styx-sub">{escape(sub_line)}</div>'
        f'{_vitals_html(vitals)}'
        f'{sparkline}'
        f'<div class="styx-news2-foot">{foot}</div>'
        f'</div>'
    )


def vacant_tile_html() -> str:
    """An empty bed slot — pads a bay's grid to its fixed capacity. Carries no patient data."""
    return '<div class="styx-card styx-vacant"><span>vacant bed</span></div>'


def attention_rail_html(items: Sequence[tuple[int, str, str]]) -> str:
    """The across-the-top rail of flagged beds only: (pid, band, short reason) chips."""
    if not items:
        return ('<div class="styx-rail styx-rail-empty">No beds flagged — '
                'all wards within routine monitoring.</div>')
    chips = "".join(
        f'<span class="styx-rail-chip styx-band-{band}" style="--band:{BAND_COLOUR[band]}">'
        f'<b>patient {pid}</b> {escape(reason)}</span>'
        for pid, band, reason in items
    )
    return f'<div class="styx-rail">{chips}</div>'


# --- the single scoped style block the page injects once --------------------------------------
BOARD_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
.styx-banner,.styx-card,.styx-rail{{font-family:'IBM Plex Sans',system-ui,sans-serif;color:{_INK};}}
.styx-pid,.styx-vital b,.styx-was,.styx-news2-foot,.styx-stat b,.styx-banner-status,.styx-rail-chip b{{
  font-family:'IBM Plex Mono',ui-monospace,Menlo,monospace;}}
.styx-banner{{display:flex;align-items:center;gap:.8rem;padding:.5rem .8rem;margin:.2rem 0 .6rem;
  background:{_CARD};border:1px solid {_LINE};border-left:4px solid {_INK_3};border-radius:8px;}}
.styx-banner-name{{font-weight:600;font-size:.95rem;}}
.styx-banner-stats{{display:flex;gap:.7rem;flex-wrap:wrap;margin-left:auto;
  color:{_INK_2};font-size:.78rem;}}
.styx-stat b{{color:{_INK};}}
.styx-banner-status{{font-size:.72rem;font-weight:600;letter-spacing:.06em;padding:.12rem .5rem;
  border-radius:999px;border:1px solid {_LINE};}}
.styx-status-steady{{border-left-color:{BAND_COLOUR['low']};}}
.styx-status-steady .styx-banner-status{{color:{BAND_COLOUR['low']};border-color:{BAND_COLOUR['low']};}}
.styx-status-busy{{border-left-color:{BAND_COLOUR['med']};}}
.styx-status-busy .styx-banner-status{{color:{BAND_COLOUR['med']};border-color:{BAND_COLOUR['med']};}}
.styx-status-surge{{border-left-color:{BAND_COLOUR['high']};}}
.styx-status-surge .styx-banner-status{{color:{BAND_COLOUR['high']};border-color:{BAND_COLOUR['high']};}}
/* P0-1: never break a label mid-word — wrap only at spaces, no auto-hyphenation. */
.styx-card{{position:relative;display:block;padding:.55rem .7rem;margin:.35rem 0;
  background:{_CARD};border:1px solid {_LINE};border-radius:8px;overflow:hidden;
  overflow-wrap:normal;word-break:keep-all;hyphens:none;}}
.styx-flag{{border-color:var(--accent);}}
.styx-card-bar{{position:absolute;left:0;top:0;bottom:0;width:4px;background:var(--accent);}}
.styx-vacant{{display:flex;align-items:center;justify-content:center;min-height:74px;
  border:1px dashed {_LINE};background:{_CARD};color:{_INK_3};font-size:.72rem;
  letter-spacing:.04em;font-family:'IBM Plex Mono',ui-monospace,Menlo,monospace;}}
.styx-card-head{{display:flex;justify-content:space-between;align-items:baseline;gap:.4rem;
  margin-bottom:.3rem;}}
.styx-pid{{font-weight:600;font-size:.82rem;}}
.styx-badge{{display:inline-flex;align-items:center;gap:5px;font-size:.7rem;font-weight:600;
  white-space:nowrap;}}
.styx-badge .styx-state{{color:var(--accent);}}
.styx-dot{{width:8px;height:8px;border-radius:50%;background:var(--accent);flex:none;}}
.styx-verdict{{display:flex;align-items:center;gap:6px;margin-bottom:1px;}}
.styx-arrow{{color:var(--accent);font-size:1rem;line-height:1;}}
.styx-verdict-txt{{font-size:.95rem;color:{_INK_2};font-weight:400;}}
.styx-flag .styx-verdict-txt{{color:var(--accent);font-weight:600;}}
.styx-sub{{font-size:.72rem;color:{_INK_2};margin:.1rem 0 .4rem;}}
.styx-vitals{{display:flex;gap:16px;flex-wrap:wrap;font-size:.74rem;color:{_INK_2};
  margin-bottom:.4rem;}}
.styx-vital b{{color:{_INK};font-weight:600;}}
.styx-was{{color:{_INK_3};}}
.styx-spark{{display:block;}}
.styx-news2-foot{{font-size:.68rem;color:{_INK_3};margin-top:.4rem;padding-top:.35rem;
  border-top:1px solid {_LINE};}}
.styx-rail{{display:flex;gap:.4rem;flex-wrap:wrap;padding:.45rem .6rem;margin:.2rem 0 .6rem;
  background:{_CARD};border:1px solid {_LINE};border-radius:8px;}}
.styx-rail-empty{{color:{_INK_3};font-size:.8rem;}}
.styx-rail-chip{{font-size:.74rem;padding:.1rem .45rem;border-radius:6px;
  border:1px solid var(--band);color:{_INK_2};border-left:3px solid var(--band);}}
.styx-rail-chip b{{color:{_INK};}}
</style>
"""
