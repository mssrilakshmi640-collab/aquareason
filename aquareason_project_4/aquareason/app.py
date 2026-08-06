"""
Streamlit web interface for AquaReason.

Run locally:
    streamlit run app.py

The user types the readings in a form, presses Diagnose, and sees the verdict,
the findings, the combined inferences and the trace of rules that fired.
"""
import json
import os

import streamlit as st

from aquareason.engine import diagnose, _limit_text
from aquareason.queries import treatments_for, sources_for
from aquareason.frames import KB

st.set_page_config(page_title="AquaReason", page_icon="~", layout="centered")

st.title("AquaReason")
st.caption("A rule-based system for drinking-water contamination diagnosis and "
           "treatment advice. Limits come from the WHO and US EPA guidelines.")

# Load the built-in samples so the user can start from a preset
DATA = os.path.join(os.path.dirname(__file__), "data", "samples.json")
with open(DATA, "r", encoding="utf-8") as fh:
    samples = json.load(fh)

tab_diag, tab_query, tab_kb = st.tabs(["Diagnose a sample", "Ask a question", "Knowledge base"])

# --------------------------------------------------------------------------
with tab_diag:
    preset_name = st.selectbox(
        "Start from a preset (optional)",
        ["-- enter my own --"] + list(samples.keys()),
    )
    preset = samples[preset_name]["readings"] if preset_name in samples else {}
    if preset_name in samples:
        st.info(samples[preset_name]["description"])

    st.write("Enter the readings:")
    c1, c2 = st.columns(2)
    readings = {}
    numeric_keys = [k for k in KB if k != "coliform"]
    for i, key in enumerate(numeric_keys):
        col = c1 if i % 2 == 0 else c2
        default = float(preset.get(key, 0.0))
        readings[key] = col.number_input(
            "%s (%s), limit %s" % (KB[key].label, KB[key].unit, _limit_text(KB[key])),
            value=default, format="%.4f", step=0.01, key="in_" + key,
        )
    readings["coliform"] = st.checkbox(
        "Coliform / E. coli present", value=bool(preset.get("coliform", False)))

    if st.button("Diagnose", type="primary"):
        res = diagnose(readings)
        if res["safe"]:
            st.success("Sample is within all checked guideline limits.")
        else:
            st.error("Sample is NOT safe. See the findings below.")

        for f in res["findings"]:
            with st.expander("%s = %s  (limit %s)" %
                             (f["parameter"], f["reading"], f["limit"]), expanded=True):
                st.markdown("**Contaminant:** %s" % f["contaminant"])
                st.markdown("**Health risk:** %s" % f["health_risk"])
                st.markdown("**Likely source:** %s" % ", ".join(f["likely_source"]))
                st.markdown("**Recommended treatment:** %s" % ", ".join(f["recommend"]))

        if res["inferences"]:
            st.subheader("Combined inferences")
            for inf in res["inferences"]:
                st.markdown("**%s** — %s" % (inf["name"], inf["detail"]))

        st.subheader("Explanation trace")
        st.code("\n".join(res["trace"]) if res["trace"] else "no rule fired")

# --------------------------------------------------------------------------
with tab_query:
    st.write("Ask a direct question against the knowledge base.")
    q = st.text_input("Contaminant name (for example: arsenic, nitrate, lead)")
    if q:
        t = treatments_for(q)
        s = sources_for(q)
        if t or s:
            st.markdown("**Treatments:** %s" % (", ".join(t) if t else "none found"))
            st.markdown("**Likely sources:** %s" % (", ".join(s) if s else "none found"))
        else:
            st.warning("Nothing found for that term.")

# --------------------------------------------------------------------------
with tab_kb:
    st.write("The parameters and guideline limits the system knows about:")
    rows = []
    for f in KB.values():
        rows.append({
            "Parameter": f.label,
            "Limit": _limit_text(f),
            "Contaminant": f.contaminant,
            "Guideline": f.guideline,
        })
    st.dataframe(rows, use_container_width=True)
