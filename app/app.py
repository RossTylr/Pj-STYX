"""STYX Streamlit entry — the navigation router (LYR-1: thin client, holds zero logic).

Owns the sidebar nav (explicit titles, icons, sections) and the app-wide chrome: brand theme
(.streamlit/config.toml), the logo, and the favicon. Every view lives in app/pages/ as a thin
styx client. Nav titles are audience-named — the clinician 'Patient detail' vs the patient-facing
'Bedside display' — and ordered to the ward→patient workflow.
"""

import streamlit as st

st.set_page_config(page_title="STYX", page_icon="docs/Pj-STYX.jpeg", layout="wide")
st.logo("docs/Pj-STYX.jpeg", size="large")  # (6h) app-wide brand mark in the sidebar banner
st.markdown(  # (6h+) full-width brand mark in the sidebar banner; gone when the sidebar is closed
    "<style>"
    "[data-testid='stSidebarHeader']{height:auto!important;display:block!important;"
    "position:relative!important;padding:.5rem!important;}"
    "[data-testid='stSidebarCollapseButton']{position:absolute!important;"
    "top:.35rem!important;right:.35rem!important;z-index:2!important;}"
    "[data-testid='stSidebarHeader'] [data-testid='stLogoLink']{width:100%!important;"
    "height:auto!important;max-height:none!important;display:block!important;}"
    "[data-testid='stSidebarLogo']{width:100%!important;height:auto!important;"
    "max-height:none!important;}"
    "section[data-testid='stSidebar'][aria-expanded='false'] [data-testid='stSidebarLogo']"
    "{display:none!important;}"
    "</style>",
    unsafe_allow_html=True,
)

# (6h+) Sidebar nav — explicit titles/icons/sections (st.navigation suppresses the filename-derived
# pages/ nav). Files keep their names so the test suite's page paths stay valid.
home = st.Page("pages/00_home.py", title="Home", icon=":material/home:", default=True)
ward = st.Page("pages/02_ward.py", title="Ward board", icon=":material/grid_view:")
patient = st.Page("pages/01_patient.py", title="Patient detail", icon=":material/person:")
bedside = st.Page("pages/03_patient_display.py", title="Bedside display", icon=":material/groups:")
clinical = st.Page("pages/04_clinical_basis.py", title="Clinical basis", icon=":material/menu_book:")

st.navigation(
    {
        "": [home],
        "Monitoring": [ward, patient],
        "Patient-facing": [bedside],
        "Reference": [clinical],
    }
).run()
