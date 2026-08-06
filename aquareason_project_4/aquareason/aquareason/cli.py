

Usage:
    python -m aquareason.cli --sample rural_well
    python -m aquareason.cli --nitrate 62 --coliform yes --chlorine 0.05
    python -m aquareason.cli --treats arsenic
    python -m aquareason.cli --list
"""
import argparse
import json
import os

from .engine import diagnose, format_report
from .queries import treatments_for, sources_for
from .frames import KB

DATA = os.path.join(os.path.dirname(__file__), "..", "data", "samples.json")


def load_samples():
    with open(DATA, "r", encoding="utf-8") as fh:
        return json.load(fh)


def parse_bool(text):
    return str(text).lower() in ("1", "yes", "y", "true", "present")


def main():
    p = argparse.ArgumentParser(description="AquaReason drinking-water diagnosis")
    p.add_argument("--sample", help="run a named sample from data/samples.json")
    p.add_argument("--list", action="store_true", help="list the built-in samples")
    p.add_argument("--treats", help="ask which treatments remove a contaminant")
    p.add_argument("--sources", help="ask the likely sources of a contaminant")
    # individual readings
    for key in KB:
        p.add_argument("--" + key, help="reading for %s" % key)
    args = p.parse_args()

    if args.list:
        for name, s in load_samples().items():
            print("%-20s %s" % (name, s["description"]))
        return

    if args.treats:
        t = treatments_for(args.treats)
        print("Treatments for '%s': %s" % (args.treats, ", ".join(t) if t else "none found"))
        return

    if args.sources:
        s = sources_for(args.sources)
        print("Likely sources of '%s': %s" % (args.sources, ", ".join(s) if s else "none found"))
        return

    if args.sample:
        samples = load_samples()
        if args.sample not in samples:
            print("Unknown sample. Use --list to see the options.")
            return
        readings = samples[args.sample]["readings"]
        print("Sample: %s" % samples[args.sample]["description"])
        print("Readings: %s\n" % readings)
        print(format_report(diagnose(readings)))
        return

    # otherwise collect readings from the individual flags
    readings = {}
    for key in KB:
        val = getattr(args, key)
        if val is None:
            continue
        readings[key] = parse_bool(val) if key == "coliform" else float(val)

    if not readings:
        p.print_help()
        return

    print("Readings: %s\n" % readings)
    print(format_report(diagnose(readings)))


if __name__ == "__main__":
    main()
