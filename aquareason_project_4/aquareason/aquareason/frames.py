"""
Frames and the knowledge base.

The knowledge is written down as a set of frames (Python dataclasses) with
slots, one frame per contaminant. Each frame holds the guideline limit, the
direction of the check, the likely sources, the health effect and the
recommended treatments. The values come from the WHO Guidelines for
Drinking-water Quality (4th edition) and the US EPA National Primary and
Secondary Drinking Water Regulations. A few expert facts (for example the pH
band and the low-chlorine reasoning) were added by hand.

This same data also serves as the ontology / triple view used by the query
module, so the rules and the queries always read from one single source.
"""
from dataclasses import dataclass, field
from typing import List


# ---- Frame definitions -----------------------------------------------------

@dataclass
class Treatment:
    name: str
    note: str = ""


@dataclass
class ContaminantFrame:
    """One frame per water-quality parameter."""
    key: str                 # short id used in the rules, e.g. "nitrate"
    label: str               # human readable name
    unit: str                # measurement unit
    limit: float             # guideline value
    direction: str           # "max", "min" or "band"
    band_low: float = None   # only used when direction == "band"
    band_high: float = None
    contaminant: str = ""    # the conclusion name when the limit is broken
    health_effect: str = ""
    sources: List[str] = field(default_factory=list)
    treatments: List[str] = field(default_factory=list)
    guideline: str = ""      # where the number comes from


# ---- The knowledge base ----------------------------------------------------
# Numbers are the guideline values. Nitrate is given as NO3 (WHO 50 mg/L).

KB = {
    "nitrate": ContaminantFrame(
        key="nitrate", label="Nitrate (as NO3)", unit="mg/L",
        limit=50.0, direction="max",
        contaminant="Nitrate_Exceedance",
        health_effect="Methemoglobinemia (blue-baby syndrome) in infants",
        sources=["Agricultural_runoff", "Septic_leakage", "Fertiliser_use"],
        treatments=["Ion_exchange", "Reverse_osmosis", "Alternative_supply"],
        guideline="WHO 50 mg/L",
    ),
    "arsenic": ContaminantFrame(
        key="arsenic", label="Arsenic", unit="mg/L",
        limit=0.01, direction="max",
        contaminant="Arsenic_Exceedance",
        health_effect="Skin lesions and long-term cancer risk (skin, bladder, lung)",
        sources=["Natural_geological", "Industrial_discharge", "Mining_activity"],
        treatments=["Reverse_osmosis", "Activated_alumina", "Ion_exchange", "Coagulation_filtration"],
        guideline="WHO / EPA 0.01 mg/L",
    ),
    "lead": ContaminantFrame(
        key="lead", label="Lead", unit="mg/L",
        limit=0.01, direction="max",
        contaminant="Lead_Exceedance",
        health_effect="Neurodevelopmental harm in children, kidney damage",
        sources=["Corroded_plumbing", "Lead_pipes_or_solder", "Brass_fixtures"],
        treatments=["Corrosion_control", "Reverse_osmosis", "Replace_plumbing"],
        guideline="WHO 0.01 mg/L (EPA action level 0.015 mg/L)",
    ),
    "fluoride": ContaminantFrame(
        key="fluoride", label="Fluoride", unit="mg/L",
        limit=1.5, direction="max",
        contaminant="Fluoride_Exceedance",
        health_effect="Dental and, at higher exposure, skeletal fluorosis",
        sources=["Natural_geological", "Industrial_discharge"],
        treatments=["Activated_alumina", "Reverse_osmosis", "Bone_char_filtration"],
        guideline="WHO 1.5 mg/L",
    ),
    "turbidity": ContaminantFrame(
        key="turbidity", label="Turbidity", unit="NTU",
        limit=5.0, direction="max",
        contaminant="High_Turbidity",
        health_effect="Particles can shield microbes and reduce disinfection",
        sources=["Surface_runoff", "Sediment", "Inadequate_filtration"],
        treatments=["Coagulation_filtration", "Sedimentation"],
        guideline="WHO acceptability 5 NTU (target < 1 NTU)",
    ),
    "ph": ContaminantFrame(
        key="ph", label="pH", unit="",
        limit=None, direction="band", band_low=6.5, band_high=8.5,
        contaminant="pH_Out_Of_Range",
        health_effect="No direct health effect, but affects corrosion and taste",
        sources=["Source_water_chemistry", "Treatment_imbalance"],
        treatments=["pH_adjustment"],
        guideline="WHO / EPA aesthetic range 6.5 - 8.5",
    ),
    "chlorine": ContaminantFrame(
        key="chlorine", label="Free chlorine residual", unit="mg/L",
        limit=0.2, direction="min",
        contaminant="Low_Chlorine_Residual",
        health_effect="Weak protection against microbial regrowth in the network",
        sources=["Long_distribution_time", "Chlorine_demand", "Dosing_fault"],
        treatments=["Re_chlorination", "Booster_disinfection"],
        guideline="WHO recommends >= 0.2 mg/L at the point of delivery",
    ),
    "coliform": ContaminantFrame(
        key="coliform", label="Total coliform / E. coli", unit="present/absent",
        limit=0, direction="max",
        contaminant="Microbial_Contamination",
        health_effect="Risk of gastrointestinal disease from faecal pathogens",
        sources=["Sewage_ingress", "Animal_waste", "Biofilm"],
        treatments=["Disinfection_chlorination", "UV_treatment", "Boil_water_advisory"],
        guideline="WHO / EPA must be absent in 100 mL",
    ),
}


def as_triples():
    """Return the knowledge base as (subject, predicate, object) triples.

    This is the ontology view mentioned in the proposal. It lets the query
    side answer questions like 'which treatments remove arsenic' by walking
    the links instead of running the rule engine.
    """
    triples = []
    for f in KB.values():
        c = f.contaminant
        if f.direction == "band":
            triples.append((c, "hasRange", "%s - %s" % (f.band_low, f.band_high)))
        else:
            triples.append((c, "hasLimit", "%s %s" % (f.limit, f.unit)))
        triples.append((c, "causesEffect", f.health_effect))
        for s in f.sources:
            triples.append((c, "typicalSource", s))
        for t in f.treatments:
            triples.append((c, "treatedBy", t))
    return triples
