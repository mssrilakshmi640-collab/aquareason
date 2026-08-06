"""
Direct questions against the knowledge base.

Besides diagnosing a sample, the system can answer questions by walking the
links in the frames / triples, without running the rule engine. Two examples:
'which treatments remove arsenic' and 'is this sample safe'.
"""
from .frames import KB, as_triples


def treatments_for(contaminant_or_key):
    """Return the treatments that address a given contaminant.

    Accepts either a frame key ('arsenic') or a contaminant name
    ('Arsenic_Exceedance'), case-insensitive and partial.
    """
    q = contaminant_or_key.lower()
    for f in KB.values():
        if q in f.key.lower() or q in f.contaminant.lower() or q in f.label.lower():
            return f.treatments
    return []


def sources_for(contaminant_or_key):
    q = contaminant_or_key.lower()
    for f in KB.values():
        if q in f.key.lower() or q in f.contaminant.lower() or q in f.label.lower():
            return f.sources
    return []


def contaminants_treated_by(treatment):
    """Reverse lookup: which contaminants does a treatment help with."""
    q = treatment.lower()
    hits = []
    for f in KB.values():
        for t in f.treatments:
            if q in t.lower():
                hits.append(f.contaminant)
                break
    return hits


def all_triples():
    return as_triples()
