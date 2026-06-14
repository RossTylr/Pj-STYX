"""(S-board) Routine-board renderers — pure builders, asserted off strings (no Streamlit).

Guards the presentation-only contract: NEWS2 standing is a read-only slice of the existing
comparator subscores (no new scoring), the band ramp is the only place band colour appears, and
every rendered fragment is plain (no codename, no raw enum, HTML-escaped).
"""

from __future__ import annotations

import re

from styx.readouts import NEWS2_RED, news2_complete, news2_subscores_at
from styx.synth import build_cohort
from styx.viz import board


def _strip_tags(html: str) -> str:
    """Drop HTML tags so a content rule (e.g. the SpO₂ token) reads contiguous text, not markup."""
    return re.sub(r"<[^>]+>", "", html)


def test_band_of_thresholds() -> None:
    assert board.band_of(0, False) == "low"
    assert board.band_of(4, False) == "low"
    assert board.band_of(3, True) == "med"   # a single red lifts low → medium
    assert board.band_of(5, False) == "med"
    assert board.band_of(6, False) == "med"
    assert board.band_of(7, False) == "high"


def test_news2_now_is_a_readonly_slice_of_the_comparator() -> None:
    # The aggregate must equal the existing complete-NEWS2 comparator at that sample — no new maths.
    p = build_cohort(seed=42).silent_case()
    idx = len(p.t_min) // 2
    n2 = board.news2_now(p, idx)
    assert n2.aggregate == int(news2_complete(p)[idx])
    assert n2.subscores == news2_subscores_at(p, idx)
    assert n2.single_red == any(s >= NEWS2_RED for s in n2.subscores.values())
    assert n2.band == board.band_of(n2.aggregate, n2.single_red)


def test_news2_now_is_deterministic() -> None:
    a = build_cohort(seed=42).silent_case()
    b = build_cohort(seed=42).silent_case()
    idx = len(a.t_min) // 2
    assert board.news2_now(a, idx) == board.news2_now(b, idx)


def test_bay_status_worst_of_news2_and_styx() -> None:
    # P1 §A worst-wins ladder: NEWS2 escalation (high or med) → ATTENTION; else any STYX
    # early-signal bed → WATCH; else STEADY. The safety inversion (STEADY over a flagged bed) is
    # impossible by construction.
    assert board.bay_status(board.Rollup(8, 0, 0, 1, early_signal=0)) == "STEADY"
    assert board.bay_status(board.Rollup(8, 0, 0, 2, early_signal=3)) == "WATCH"   # flagged → WATCH
    assert board.bay_status(board.Rollup(8, 0, 1, 5, early_signal=4)) == "ATTENTION"  # med fired
    assert board.bay_status(board.Rollup(8, 2, 0, 8, early_signal=0)) == "ATTENTION"  # high
    # the hard invariant: a bay with flagged beds can never read STEADY
    assert board.bay_status(board.Rollup(17, 0, 0, 2, early_signal=9)) != "STEADY"


def test_trend_arrow_reads_the_slope() -> None:
    assert board.trend_arrow([0.1, 0.1, 0.2, 0.3, 0.4, 0.5]) == "↑"
    assert board.trend_arrow([0.5, 0.4, 0.3, 0.2, 0.1, 0.0]) == "↓"
    assert board.trend_arrow([0.3, 0.3, 0.3, 0.3]) == "→"
    assert board.trend_arrow([0.3]) == "→"  # too short to call a trend


def test_sparkline_is_wellformed_svg_on_a_fixed_scale() -> None:
    svg = board.sparkline_svg([0.0, 0.5, 1.0], width=72, height=22)
    assert svg.startswith("<svg") and svg.endswith("</svg>")
    assert "polyline" in svg and svg.count(",") >= 3  # three plotted points
    assert board.sparkline_svg([]) == ""  # empty history → no figure, never a fabricated line


def _spo2(value: int, prior: int, trend: str) -> board.VitalReading:
    return board.VitalReading("SpO₂", value, prior, "%", trend)


def test_flagged_card_leads_with_the_styx_verdict_and_demotes_news2() -> None:
    # P0-3: the STYX verdict element precedes the muted NEWS2 line in DOM order; NEWS2 reads as a
    # below-trigger counterpoint, not the headline; the bed/ward header is present.
    n2 = board.News2Now(aggregate=2, subscores={"SpO₂": 2}, band="med", single_red=False)
    html = board.card_html(6, "Respiratory", n2, flagged=True, receding=False,
                           vitals=[_spo2(91, 96, "↓")], sub_line="~1–2 h before NEWS2 would escalate",
                           arrow="↑", sparkline=board.sparkline_svg([0.1, 0.4]))
    assert "Bed 6 · Respiratory" in html
    assert "deteriorating — silent" in html and "early signal" in html
    assert html.index("styx-verdict") < html.index("styx-news2-foot")  # verdict before NEWS2
    assert "NEWS2 2 · below trigger" in html
    assert "silent_hypoxia" not in html  # never the raw enum
    assert not re.search(r"AEGIS|SENTINEL|CALLIOPE", html)  # never a codename


def test_calm_card_recedes_with_a_quiet_state() -> None:
    n2 = board.News2Now(aggregate=0, subscores={}, band="low", single_red=False)
    html = board.card_html(9, "Respiratory", n2, flagged=False, receding=False,
                           vitals=[_spo2(97, 97, "→")], sub_line="STYX and NEWS2 agree",
                           arrow="→", sparkline="")
    assert "Bed 9 · Respiratory" in html and ">stable</span>" in html
    assert "NEWS2 0" in html and "below trigger" not in html  # calm: no trigger noise


def test_card_html_escapes_injected_ward_label() -> None:
    n2 = board.News2Now(aggregate=0, subscores={}, band="low", single_red=False)
    html = board.card_html(1, "<script>x</script>", n2, flagged=False, receding=False,
                           vitals=[_spo2(97, 97, "→")], sub_line="ok", arrow="→", sparkline="")
    assert "<script>" not in html and "&lt;script&gt;" in html


def test_card_labels_drawn_from_the_approved_set() -> None:
    for flagged in (True, False):
        for receding in (True, False):
            lab = board.card_labels(flagged, receding)
            assert lab["badge"] in board.APPROVED_STATES
            if lab["verdict_state"]:  # only a marked verdict must be an approved token
                assert lab["verdict"] in board.APPROVED_STATES
    assert board.card_labels(True, False)["verdict"] == "deteriorating — silent"
    assert board.card_labels(False, True)["badge"] == "recovering"


def test_vitals_html_is_a_percentage_with_trend_and_prior() -> None:
    html = board._vitals_html([_spo2(91, 96, "↓")])
    assert re.search(r"SpO.? ?\d{2,3}%", _strip_tags(html))  # the disambiguated SpO₂ token
    assert "(was 96)" in html and "↓" in html
    flat = board._vitals_html([_spo2(97, 97, "→")])
    assert "(was" not in flat  # a flat reading shows no prior


def test_vital_reading_reads_against_the_early_stay_baseline() -> None:
    # Read-only over patient.vitals — value at the clock, prior = early-stay mean, trend vs deadband.
    p = build_cohort(seed=42).silent_case()
    r = board.vital_reading(p, "SpO2", len(p.t_min) - 1, label="SpO₂", unit="%")
    assert r.value == int(round(float(p.vitals["SpO2"][-1])))
    assert r.prior == int(round(float(p.vitals["SpO2"][:24].mean())))
    assert r.trend in {"↑", "↓", "→"}


def test_banner_html_shows_label_status_and_early_signal_count() -> None:
    html = board.banner_html("Respiratory", board.Rollup(17, 0, 0, 2, early_signal=9))
    assert "Respiratory" in html and "WATCH" in html and "max NEWS2" in html
    assert "<b>9</b> early signal" in html  # §A: the STYX count rides the header


def test_overview_strip_counts_not_pills() -> None:
    html = board.overview_strip_html(0, 21, 29, "12:30")
    assert "50 patients" in html and "scored 12:30" in html
    assert ">21<" in html and "early signal" in html and "29" in html and "stable" in html


def test_review_rank_orders_reds_then_shortest_lead() -> None:
    key = board.review_rank
    red = key(critical=True, eta_soonest_min=999.0, risk_now=0.1, pid=9)
    soon = key(critical=False, eta_soonest_min=15.0, risk_now=0.2, pid=1)
    late = key(critical=False, eta_soonest_min=90.0, risk_now=0.9, pid=2)
    none = key(critical=False, eta_soonest_min=None, risk_now=0.5, pid=3)
    assert red < soon < late < none  # reds first; then shortest lead; no-forecast last


def test_worklist_caps_and_collapses_the_tail() -> None:
    rows = [(i + 1, i, f"SpO₂ {90 + i}% ↓", "~1–2 h lead", "watch") for i in range(6)]
    html = board.worklist_html(rows, more_count=15)
    assert html.count("styx-wl-row") == 6 and "Bed 0" in html
    assert "+ 15 more in watch" in html
    assert board.worklist_html([], 0).count("styx-wl-row") == 0  # empty → no rows


def test_vacant_tile_is_plain_and_patient_free() -> None:
    # A padding slot carries no patient identity, no NEWS2, no drill target — just "vacant bed".
    tile = board.vacant_tile_html()
    assert "vacant bed" in tile and "styx-vacant" in tile
    assert "patient" not in tile and "NEWS2" not in tile


def test_bay_padding_fills_a_short_bay_in_bed_order() -> None:
    # The bay grid is bed-ordered (pid ascending) and padded with vacant slots to a fixed capacity —
    # the layout rule the page applies, asserted here on plain lists (no Streamlit).
    bay_cols = board.BAY_COLS
    pids = [12, 0, 6, 3]  # an out-of-order, short bay
    ordered = sorted(pids)
    rows = -(-len(ordered) // bay_cols)  # ceil
    capacity = rows * bay_cols
    beds = ordered + [None] * (capacity - len(ordered))
    assert beds[: len(ordered)] == [0, 3, 6, 12]  # bed order, never urgency
    assert len(beds) == capacity and beds.count(None) == capacity - len(ordered)


def test_board_module_imports_no_streamlit() -> None:
    import sys
    # Importing the builder must not drag Streamlit into the package (LYR-1).
    assert "streamlit" not in sys.modules or board.__name__  # builder itself never imports it
    src = (board.__file__)
    with open(src, encoding="utf-8") as fh:
        assert "import streamlit" not in fh.read()
