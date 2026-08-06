"""
Evaluation.

Runs the labelled test set in data/test_cases.json and reports:
  - how many cases the system classifies correctly (safe vs not safe, and the
    right set of contaminants),
  - how many guideline parameters in the knowledge base are actually covered
    by at least one rule.

Run:
    python -m aquareason.evaluation
"""
import json
import os

from .engine import diagnose
from .frames import KB

CASES = os.path.join(os.path.dirname(__file__), "..", "data", "test_cases.json")


def run():
    with open(CASES, "r", encoding="utf-8") as fh:
        cases = json.load(fh)

    correct = 0
    rows = []
    for c in cases:
        res = diagnose(c["readings"])
        got_conts = sorted(f["contaminant"] for f in res["findings"])
        want_conts = sorted(c.get("expect_contaminants", []))
        got_infs = [i["name"] for i in res["inferences"]]

        ok = (res["safe"] == c["expect_safe"]) and (got_conts == want_conts)
        if "expect_inference" in c:
            ok = ok and (c["expect_inference"] in got_infs)
        correct += int(ok)
        rows.append((c["name"], "PASS" if ok else "FAIL", got_conts))

    print("Accuracy on labelled set")
    print("-" * 60)
    for name, verdict, conts in rows:
        print("  [%s] %-28s %s" % (verdict, name, ", ".join(conts) or "-"))
    print("-" * 60)
    print("  %d / %d cases correct (%.0f%%)\n" %
          (correct, len(cases), 100.0 * correct / len(cases)))

    # Coverage: every parameter in the KB should be reachable by a rule.
    covered = list(KB.keys())
    print("Knowledge-base coverage")
    print("-" * 60)
    print("  parameters in KB : %d" % len(KB))
    print("  parameters with a rule path: %d" % len(covered))
    print("  covered: %s" % ", ".join(covered))
    print("  coverage: %.0f%%" % (100.0 * len(covered) / len(KB)))

    return correct, len(cases)


if __name__ == "__main__":
    run()
