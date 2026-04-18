# aegis

A layered Python pipeline for automatic GDPR text classification.


### Miljösetup

```bash
git clone https://github.com/Abdriano95/aegis.git
cd aegis
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest --co -q
```

På Windows / PowerShell aktiveras venv istället med:

```powershell
.venv\Scripts\Activate.ps1
```

På Windows / CMD aktiveras venv istället med:

```cmd
.venv\Scripts\activate.bat
```

Alla kommandon nedan antar att venv är aktiverat (`python` pekar på `.venv`). Om du inte vill aktivera miljön kan du alltid köra via `.venv/bin/python` (Linux/macOS) eller `.venv\Scripts\python.exe` (Windows).

---

### Manuell körning

Alla kommandon körs från repo-roten.

#### 1. Kör hela utvärderingen mot iteration 1-datasetet

```bash
python run_evaluation.py
```

Bygger pipelinen (`PatternLayer + EntityLayer + ContextLayer + Aggregator`), kör den mot `tests/data/iteration_1/test_dataset.json` och skriver ut Total + per-kategori + per-lager (precision/recall/F1).

#### 2. Kör integrationstestet via pytest

```bash
pytest tests/integration/test_end_to_end.py -s
```

`-s` gör att utvärderingsrapporten visas i terminalen (utan `-s` fångar pytest stdout).

#### 3. Kör hela testsviten

```bash
pytest
```

Kör unit-tester per recognizer plus integrationstestet.

#### 4. Klassificera en egen text ad hoc

Starta en Python-REPL med `python` och kör:

```python
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.context import ContextLayer

pipeline = Pipeline(
    layers=[PatternLayer(), EntityLayer(), ContextLayer()],
    aggregator=Aggregator(),
)

result = pipeline.classify(
    "Mitt personnummer är 850823-1233 och IBAN SE41 3456 7890 1234 5678 90."
)

for f in result.findings:
    print(f.category.value, (f.start, f.end), repr(f.text_span), f.source)

print("sensitivity:", result.sensitivity)
print("active_layers:", result.active_layers)
print("overlaps:", result.overlapping_findings)
```

Vill du skippa Entity/Context-stubsen (t.ex. när du bara testar regex-lagret) räcker det med `layers=[PatternLayer()]`.

#### 5. Kör en enskild recognizer eller valideringsfunktion isolerat

Användbart när du felsöker Luhn/mod97/regex utan att gå via pipelinen:

```python
from gdpr_classifier.layers.pattern.recognizers.personnummer import (
    PersonnummerRecognizer, _luhn_valid, _is_valid_date,
)
from gdpr_classifier.layers.pattern.recognizers.iban import (
    IbanRecognizer, _mod97_valid,
)

print(PersonnummerRecognizer().recognize("pnr 850823-1233"))
print(IbanRecognizer().recognize("IBAN SE41 3456 7890 1234 5678 90."))

print(_is_valid_date(8, 23), _luhn_valid("8508231233"))   # True True
print(_mod97_valid("SE41345678901234567890"))              # True
```

#### 6. Kör pipelinen mot ett eget dataset

Lägg en JSON-fil i samma format som `tests/data/iteration_1/test_dataset.json` (en lista av objekt med fälten `text`, `description`, `expected_findings: [{category, start, end, text_span}]`) och kör:

```python
from gdpr_classifier import Aggregator, Pipeline
from gdpr_classifier.layers.pattern import PatternLayer
from gdpr_classifier.layers.entity import EntityLayer
from gdpr_classifier.layers.context import ContextLayer
from evaluation.dataset.loader import load_dataset
from evaluation.runner import run_evaluation
from evaluation.report import print_report

pipeline = Pipeline(
    layers=[PatternLayer(), EntityLayer(), ContextLayer()],
    aggregator=Aggregator(),
)
dataset = load_dataset("path/till/ditt_dataset.json")
report = run_evaluation(pipeline, dataset)
print_report(report)
```

`load_dataset` tar en relativ sökväg; byt cwd till repo-roten eller ge en absolut sökväg om du kör från annat håll.
