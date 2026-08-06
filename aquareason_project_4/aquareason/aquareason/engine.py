"""
The reasoning engine.

diagnose() takes a plain dictionary of readings, feeds them into the rule
engine as facts, runs the forward chaining, and then builds a full structured
result from the frames: which readings are over the limit, the likely
contaminant and source, the health risk, the recommended treatment, any
combined inferences, whether the sample is safe overall, and the trace of
rules that fired.
"""
from . import compat  # noqa: F401
from .frames import KB
from .rules import AquaRules, Reading, Presence


# Which keys are yes/no (presence) rather than numeric
PRESENCE_KEYS = {"coliform"}


def diagnose(readings):
    """Run the engine on a dict of readings and return a result dict.

    readings example:
        {"nitrate": 62, "arsenic": 0.004, "coliform": True, "chlorine": 0.05}
    Keys must match the ones in the knowledge base (frames.KB).
    """
    engine = AquaRules()
    engine.reset()  # this loads the guideline limits via DefFacts

    used = {}
    for param, value in readings.items():
        if param not in KB:
            continue  # ignore unknown parameters quietly
        used[param] = value
        if param in PRESENCE_KEYS:
            engine.declare(Presence(param=param, present=bool(value)))
        else:
            engine.declare(Reading(param=param, value=float(value)))

    engine.run()

    # Build the structured diagnosis from the frames
    findings = []
    for key in engine.exceedances:
        f = KB[key]
        findings.append({
            "parameter": f.label,
            "reading": used.get(key),
            "limit": _limit_text(f),
            "contaminant": f.contaminant,
            "health_risk": f.health_effect,
            "likely_source": f.sources,
            "recommend": f.treatments,
        })

    result = {
        "readings": used,
        "findings": findings,
        "inferences": [{"name": n, "detail": d} for n, d in engine.inferences],
        "trace": list(engine.trace),
        "safe": len(engine.exceedances) == 0,
    }
    return result


def _limit_text(frame):
    if frame.direction == "band":
        return "%s - %s" % (frame.band_low, frame.band_high)
    if frame.direction == "min":
        return ">= %s %s" % (frame.limit, frame.unit)
    return "<= %s %s" % (frame.limit, frame.unit)


def format_report(result):
    """Turn a result dict into a readable text block (used by the CLI)."""
    lines = []
    if result["safe"]:
        lines.append("VERDICT: sample is within all checked guideline limits.")
    else:
        lines.append("VERDICT: sample is NOT safe. Problems found below.")
    lines.append("")

    if result["findings"]:
        lines.append("Findings:")
        for f in result["findings"]:
            lines.append("  - %s = %s   (limit %s)" %
                         (f["parameter"], f["reading"], f["limit"]))
            lines.append("      contaminant : %s" % f["contaminant"])
            lines.append("      health risk : %s" % f["health_risk"])
            lines.append("      likely source: %s" % ", ".join(f["likely_source"]))
            lines.append("      treatment    : %s" % ", ".join(f["recommend"]))
            lines.append("")

    if result["inferences"]:
        lines.append("Combined inferences:")
        for inf in result["inferences"]:
            lines.append("  - %s" % inf["name"])
            lines.append("      %s" % inf["detail"])
        lines.append("")

    lines.append("Explanation trace (rules that fired):")
    if result["trace"]:
        for t in result["trace"]:
            lines.append("  %s" % t)
    else:
        lines.append("  (no rule fired: every reading was within limits)")
    return "\n".join(lines)
