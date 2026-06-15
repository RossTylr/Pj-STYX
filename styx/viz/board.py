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
    """A bay banner's live aggregate over its beds (occupancy = live count; no capacity modelled)."""

    occupancy: int
    high: int
    med: int
    max_news2: int
    early_signal: int = 0  # STYX-flagged (silent-but-rising) beds in the bay (P1 §A)


def bay_status(rollup: Rollup) -> str:
    """The bay badge — worst of {NEWS2 state, STYX state} (P1 §A), so a NEWS2-only summary can
    never tell the nurse to relax about a bay STYX is worried about. Worst-wins ladder:
    ATTENTION (any NEWS2 escalation — high or med, i.e. trigger reached) → WATCH (any STYX
    early-signal bed) → STEADY."""
    if rollup.high >= 1 or rollup.med >= 1:
        return "ATTENTION"
    if rollup.early_signal >= 1:
        return "WATCH"
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
    """One bay banner: name + live rollup (incl. the STYX early-signal count) + the worst-of
    ATTENTION/WATCH/STEADY status tag (P1 §A — propagates STYX, never NEWS2 alone)."""
    status = bay_status(rollup)
    return (
        f'<div class="styx-banner styx-status-{status.lower()}">'
        f'<div class="styx-banner-name">{escape(label)}</div>'
        f'<div class="styx-banner-stats">'
        f'{_stat(rollup.occupancy, "beds")}{_stat(rollup.high, "high")}'
        f'{_stat(rollup.med, "med")}{_stat(rollup.max_news2, "max NEWS2")}'
        f'{_stat(rollup.early_signal, "early signal")}'
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


# --- (P1 §E) ward overview strip + ranked review-now worklist ---------------------------------
# Replaces the flat 21-pill rail: orientation (counts, not pills) + a short ranked worklist, both
# DISPLAY cuts over the existing model output → hash-safe (no re-classification, no new score).

def review_rank(*, critical: bool, eta_soonest_min: float | None, risk_now: float, pid: int) -> tuple:
    """Worklist sort key (§E): reds first, then shortest lead-time, then highest score; pid tiebreak."""
    return (not critical, eta_soonest_min if eta_soonest_min is not None else float("inf"),
            -risk_now, pid)


def moving_vital(patient: Patient, idx: int) -> str:
    """The single most-departed vital (vs baseline) as a compact worklist token — the 'one moving
    number' (SpO₂ or RR), read-only over ``patient.vitals``."""
    sp = vital_reading(patient, "SpO2", idx, label="SpO₂", unit="%")
    rr = vital_reading(patient, "RR", idx, label="RR", unit="")
    pick = sp if abs(sp.value - sp.prior) >= abs(rr.value - rr.prior) else rr
    return f"{pick.label} {pick.value}{pick.unit} {pick.trend}"


def _ov_chip(tone: str, n: int, cap: str) -> str:
    return (f'<span class="styx-ov-chip"><span class="styx-ov-dot styx-ov-{tone}"></span>'
            f'<b>{n}</b> {cap}</span>')


def overview_strip_html(critical: int, early_signal: int, stable: int, clock: str) -> str:
    """The ward overview strip (§E): cohort line + status counts (critical / early signal / stable).
    Counts, not pills — the ward-level home for silent deterioration."""
    total = critical + early_signal + stable
    return (
        '<div class="styx-overview">'
        f'<div class="styx-ov-cohort">{total} patients · scored {escape(clock)}</div>'
        '<div class="styx-ov-chips">'
        f'{_ov_chip("crit", critical, "critical")}{_ov_chip("early", early_signal, "early signal")}'
        f'{_ov_chip("stable", stable, "stable")}'
        '</div></div>'
    )


def lead_headline(flagged_etas: Sequence[float | None]) -> str:
    """The cohort early-signal count (§D): how many patients sit in an early-signal window, flagged
    ahead of NEWS2. A count, never a cohort-level lead duration — the per-patient ETA band lives on
    the cards (UQ-1), and no aggregate lead-time figure is claimed here (it would conflate the
    per-patient time-to-escalation with a ward-wide lead-over-NEWS2). Never negates the alert.
    ``flagged_etas`` is the early-signal set (None where no crossing is yet projected)."""
    n = len(flagged_etas)
    if n == 0:
        return ""
    return f"{n} in an early-signal window — flagged ahead of NEWS2"


def worklist_html(rows: Sequence[tuple], more_count: int) -> str:
    """The ranked review-now worklist (§E): rank · bed · the one moving number · lead-time, reds/
    shortest-lead first; the tail collapses to '+k more in watch'. rows = (rank, pid, mover, lead,
    tone) already ordered by the caller via ``review_rank``."""
    if rows:
        body = "".join(
            f'<div class="styx-wl-row styx-wl-{tone}"><span class="styx-wl-rk">{rank}</span>'
            f'<span class="styx-wl-bed">Bed {pid}</span>'
            f'<span class="styx-wl-det">{escape(mover)}</span>'
            f'<span class="styx-wl-lead">{escape(lead)}</span>'
            f'<span class="styx-wl-chev">›</span></div>'
            for rank, pid, mover, lead, tone in rows
        )
    else:
        body = '<div class="styx-wl-empty">No beds to review now.</div>'
    more = f'<div class="styx-wl-more">+ {more_count} more in watch ›</div>' if more_count > 0 else ""
    return (
        '<div class="styx-worklist"><div class="styx-wl-head">'
        '<span class="styx-wl-t">Review first</span>'
        '<span class="styx-wl-s">ranked by lead-time</span></div>'
        f'{body}{more}</div>'
    )


# --- the single scoped style block the page injects once --------------------------------------
BOARD_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@500;600&family=IBM+Plex+Sans:wght@400;500;600&display=swap');
.styx-banner,.styx-card,.styx-overview,.styx-worklist{{
  font-family:'IBM Plex Sans',system-ui,sans-serif;color:{_INK};}}
.styx-pid,.styx-vital b,.styx-was,.styx-news2-foot,.styx-stat b,.styx-banner-status,
.styx-ov-chip b,.styx-wl-rk,.styx-wl-bed,.styx-wl-det{{
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
.styx-status-watch{{border-left-color:{BAND_COLOUR['med']};}}
.styx-status-watch .styx-banner-status{{color:{BAND_COLOUR['med']};border-color:{BAND_COLOUR['med']};}}
.styx-status-attention{{border-left-color:{BAND_COLOUR['high']};}}
.styx-status-attention .styx-banner-status{{color:{BAND_COLOUR['high']};border-color:{BAND_COLOUR['high']};}}
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
/* P1 §E — ward overview strip + ranked review-now worklist (replaces the flat rail) */
.styx-overview{{margin:.2rem 0 .5rem;}}
.styx-ov-cohort{{font-size:.78rem;color:{_INK_2};margin-bottom:.4rem;}}
.styx-ov-chips{{display:flex;gap:.5rem;flex-wrap:wrap;}}
.styx-ov-chip{{display:inline-flex;align-items:center;gap:7px;background:{_CARD};
  border:1px solid {_LINE};border-radius:8px;padding:.3rem .6rem;font-size:.78rem;color:{_INK_2};}}
.styx-ov-chip b{{font-size:1.05rem;color:{_INK};}}
.styx-ov-dot{{width:8px;height:8px;border-radius:50%;flex:none;}}
.styx-ov-crit{{background:{BAND_COLOUR['high']};}}
.styx-ov-early{{background:{BAND_COLOUR['med']};}}
.styx-ov-stable{{background:{BAND_COLOUR['low']};}}
.styx-worklist{{background:{_CARD};border:1px solid {_LINE};border-radius:10px;
  padding:.5rem .75rem;margin:.2rem 0 .7rem;}}
.styx-wl-head{{display:flex;justify-content:space-between;align-items:baseline;margin-bottom:.3rem;}}
.styx-wl-t{{font-size:.85rem;font-weight:600;}}
.styx-wl-s{{font-size:.72rem;color:{_INK_3};}}
.styx-wl-row{{display:flex;align-items:center;gap:.7rem;padding:.35rem 0;
  border-top:1px solid {_LINE};}}
.styx-wl-rk{{font-size:.72rem;color:{_INK_3};width:14px;}}
.styx-wl-bed{{font-size:.82rem;font-weight:600;width:58px;}}
.styx-wl-det{{font-size:.78rem;color:{_INK_2};flex:1;}}
.styx-wl-lead{{font-size:.74rem;color:{BAND_COLOUR['med']};white-space:nowrap;}}
.styx-wl-attention .styx-wl-lead{{color:{BAND_COLOUR['high']};}}
.styx-wl-chev{{font-size:.8rem;color:{_INK_3};}}
.styx-wl-more{{padding:.4rem 0 .1rem;border-top:1px solid {_LINE};margin-top:.1rem;
  font-size:.78rem;color:{_INK_2};}}
.styx-wl-empty{{font-size:.8rem;color:{_INK_3};}}
</style>
"""
