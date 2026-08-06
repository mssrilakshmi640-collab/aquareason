# AquaReason

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/YOUR-USERNAME/aquareason/blob/main/AquaReason_Colab.ipynb)

AquaReason is a small expert system that looks at drinking-water test results and
tells you whether the water is safe to drink. You give it the readings from a
water sample, such as nitrate, arsenic, lead, fluoride, turbidity, pH, the
chlorine level and whether coliform bacteria are present, and it works out four
things for you. It flags which readings are over the safe limit, it names the
most likely contaminant and where it probably came from, it explains the health
risk, and it suggests how to treat the water. On top of that it shows you the
exact rules it used to reach the answer, so nothing is hidden.

The safe limits come from two official guidelines, the WHO Guidelines for
Drinking-water Quality and the US EPA drinking-water regulations. The reasoning
is done with forward-chaining production rules using the experta engine. This
was built as a project for the Knowledge Representation course at Bielefeld
University.

## The easy way to run it: Google Colab

The simplest way to try AquaReason is in Google Colab, where you do not have to
install anything on your computer. Click the "Open in Colab" button at the top
of this page. When the notebook opens, run the cells one after another by
pressing Shift and Enter on each one.

The first cell installs the rule engine. The second cell loads the system. The
third cell is a small form where you type in your own readings and see the
diagnosis straight away. The cells after that show a few worked examples, let you
ask a direct question such as which treatments remove arsenic, and run the
evaluation.

## Running it on your own computer

If you would rather run it locally, you need Python 3.8 or newer. A small fix for
a known experta problem on newer Python versions is already built into the code,
so you do not have to do anything about it.

Open a terminal inside the project folder and set up a clean environment:

```bash
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS or Linux:
source .venv/bin/activate

pip install -r requirements.txt
```

To start the web app, run:

```bash
streamlit run app.py
```

This opens a page in your browser where you can pick a ready-made sample or type
your own readings, press Diagnose, and read the result together with the list of
rules that fired.

There is also a command-line version if you like working in the terminal. You can
list the built-in samples, run one of them, enter your own readings, or ask a
direct question:

```bash
python -m aquareason.cli --list
python -m aquareason.cli --sample network_end_epanet
python -m aquareason.cli --nitrate 62 --coliform yes --chlorine 0.05
python -m aquareason.cli --treats arsenic
```

To check that everything works, run the evaluation. It runs the labelled test
set and prints the accuracy and how much of the knowledge base is covered:

```bash
python -m aquareason.evaluation
```

## What is inside the project

The notebook `AquaReason_Colab.ipynb` is the one-click version that runs in the
browser. The `aquareason` folder is the actual system: `frames.py` holds the
knowledge base built from the WHO and EPA values, `rules.py` holds the
forward-chaining production rules, `engine.py` runs a diagnosis and builds the
explanation trace, `queries.py` answers direct questions, `cli.py` is the command
line, and `evaluation.py` checks the accuracy and coverage. The `app.py` file is
the Streamlit web form, and the `data` folder has the example samples and the
labelled test set.

```
aquareason/
├── AquaReason_Colab.ipynb
├── aquareason/
│   ├── compat.py
│   ├── frames.py
│   ├── rules.py
│   ├── engine.py
│   ├── queries.py
│   ├── cli.py
│   └── evaluation.py
├── app.py
├── data/
│   ├── samples.json
│   └── test_cases.json
└── requirements.txt
```

## A note

AquaReason is a course project. It is not a replacement for a proper laboratory
test or professional advice.
