"""
The production rules.

Knowledge is represented as IF-THEN production rules on top of the frames in
frames.py. The engine works by forward chaining: the user's readings are added
as facts, the rules fire, and each firing either flags a limit that is broken
or combines several facts into a new conclusion. Every rule that fires writes a
short line into a trace, so the final result comes with its own explanation.

Fact types
----------
Reading(param, value)      a numeric measurement
Presence(param, present)   a yes/no measurement (coliform)
Limit(param, kind, value)  a guideline value pulled from the knowledge base
Exceedance(param)          a conclusion: this parameter is out of range
Inference(name, detail)    a conclusion built from more than one exceedance
"""
from . import compat  # noqa: F401  (must import before experta)
from experta import KnowledgeEngine, Fact, Rule, MATCH, TEST, DefFacts

from .frames import KB


class Reading(Fact):
    pass


class Presence(Fact):
    pass


class Limit(Fact):
    pass


class Exceedance(Fact):
    pass


class Inference(Fact):
    pass


class AquaRules(KnowledgeEngine):
    """Holds the rules and collects the trace while they fire."""

    def __init__(self):
        super().__init__()
        self.exceedances = []      # list of param keys that are out of range
        self.inferences = []       # list of (name, detail) combined conclusions
        self.trace = []            # human readable log of what fired

    # -- Load the guideline limits from the knowledge base as facts ----------
    @DefFacts()
    def load_limits(self):
        for f in KB.values():
            if f.direction == "band":
                yield Limit(param=f.key, kind="band_low", value=f.band_low)
                yield Limit(param=f.key, kind="band_high", value=f.band_high)
            elif f.direction == "min":
                yield Limit(param=f.key, kind="min", value=f.limit)
            else:
                yield Limit(param=f.key, kind="max", value=f.limit)

    def _flag(self, param, reason):
        if param not in self.exceedances:
            self.exceedances.append(param)
        self.trace.append(reason)
        self.declare(Exceedance(param=param))

    # -- Single-parameter rules ---------------------------------------------
    @Rule(Reading(param=MATCH.p, value=MATCH.v),
          Limit(param=MATCH.p, kind="max", value=MATCH.lim),
          TEST(lambda v, lim: v > lim))
    def over_maximum(self, p, v, lim):
        self._flag(p, "R1  %s reading %s is above the limit %s -> %s"
                   % (p, v, lim, KB[p].contaminant))

    @Rule(Reading(param=MATCH.p, value=MATCH.v),
          Limit(param=MATCH.p, kind="min", value=MATCH.lim),
          TEST(lambda v, lim: v < lim))
    def under_minimum(self, p, v, lim):
        self._flag(p, "R2  %s reading %s is below the minimum %s -> %s"
                   % (p, v, lim, KB[p].contaminant))

    @Rule(Reading(param=MATCH.p, value=MATCH.v),
          Limit(param=MATCH.p, kind="band_low", value=MATCH.lo),
          TEST(lambda v, lo: v < lo))
    def below_band(self, p, v, lo):
        self._flag(p, "R3  %s reading %s is below the healthy band (< %s) -> %s"
                   % (p, v, lo, KB[p].contaminant))

    @Rule(Reading(param=MATCH.p, value=MATCH.v),
          Limit(param=MATCH.p, kind="band_high", value=MATCH.hi),
          TEST(lambda v, hi: v > hi))
    def above_band(self, p, v, hi):
        self._flag(p, "R4  %s reading %s is above the healthy band (> %s) -> %s"
                   % (p, v, hi, KB[p].contaminant))

    @Rule(Presence(param=MATCH.p, present=True))
    def presence_positive(self, p):
        self._flag(p, "R5  %s detected as present -> %s"
                   % (p, KB[p].contaminant))

    # -- Combination rules (infer new facts from several conclusions) -------
    @Rule(Exceedance(param="chlorine"), Exceedance(param="coliform"))
    def low_chlorine_and_coliform(self):
        detail = ("Low chlorine residual together with coliform presence points "
                  "to recent microbial contamination or a biofilm problem in the "
                  "network, not just a single bad reading.")
        self.inferences.append(("Recent_microbial_or_biofilm_event", detail))
        self.trace.append("R6  chlorine low AND coliform present -> "
                          "recent microbial / biofilm event (re-disinfect and find the source)")

    @Rule(Exceedance(param="turbidity"), Exceedance(param="coliform"))
    def turbidity_and_coliform(self):
        detail = ("High turbidity next to coliform presence raises the microbial "
                  "risk further, because particles shield microbes from disinfection.")
        self.inferences.append(("Turbidity_raises_microbial_risk", detail))
        self.trace.append("R7  turbidity high AND coliform present -> "
                          "particles shield microbes, disinfection less effective")

    @Rule(Exceedance(param="ph"), Exceedance(param="lead"))
    def low_ph_and_lead(self):
        detail = ("pH out of range together with elevated lead suggests the lead "
                  "is being leached from plumbing by corrosive water, so the root "
                  "fix is corrosion control, not only point-of-use filtering.")
        self.inferences.append(("Corrosion_driven_lead", detail))
        self.trace.append("R8  pH out of range AND lead high -> "
                          "corrosion-driven lead leaching (fix corrosion control at the root)")
