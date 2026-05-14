# Arkivering: TEMP I-6-instrumentering

**Datum:** 2026-05-14
**Issue:** [#106](https://github.com/Abdriano95/aegis/issues/106) (I-6)
**Status:** Arkiverad efter I-6-omformulering (Beslut 51)

## Bakgrund

TEMP-instrumenteringen lades till i commit `7c8247a` för att stödja
empirisk tröskelkalibrering i I-6 fas 1. Den möjliggjorde:

- CLI-parametrar i `run_evaluation.py` för att variera Aggregator-trösklarna
  (`--medium-threshold`, `--high-confidence-bypass`, `--min-evidence-count`)
  utan att ändra kod mellan körningar.
- En global passräknare i `aggregator.py` (`_mechanism3_pass_count`) som
  rapporterade hur många gånger Mekanism 3 godkände en
  `context.kombination`-fynd per körning.

Den togs bort i samma commit som lägger till denna arkiv-fil när I-6
omformulerades och kalibreringen stängdes utan fortsatt fas 2. Se
commit-meddelandet på den commit som introducerar denna fil för
borttagningens fulla motivering och hash.

## Borttagen kod

### `gdpr_classifier/aggregator.py`

**1. Modulnivå-globals och funktioner (rader 19–31 i pre-borttagningsformen):**

```python
# TEMP I-6 calibration, remove before commit
_mechanism3_pass_count = 0


def reset_mechanism3_counter() -> None:
    """TEMP I-6 calibration, remove before commit"""
    global _mechanism3_pass_count
    _mechanism3_pass_count = 0


def get_mechanism3_count() -> int:
    """TEMP I-6 calibration, remove before commit"""
    return _mechanism3_pass_count
```

**2. Increment-block i `_passes_mechanism_3` (rader 340–343 i pre-borttagningsformen):**

Pre-borttagning-form av funktionens nedre del:

```python
        passes = len(evidence) >= self.min_evidence_count
        # TEMP I-6 calibration, remove before commit
        if passes:
            global _mechanism3_pass_count
            _mechanism3_pass_count += 1
        return passes
```

Återställd form efter borttagning (pre-7c8247a):

```python
        return len(evidence) >= self.min_evidence_count
```

### `run_evaluation.py`

**1. Argparse-import (rad 5):**

```python
import argparse  # TEMP I-6 calibration, remove before commit
```

**2. Import av counter-funktioner (rader 8–11):**

```python
from gdpr_classifier.aggregator import (  # TEMP I-6 calibration, remove before commit
    get_mechanism3_count,
    reset_mechanism3_counter,
)
```

**3. `_parse_args()`-funktion (rader 24–31):**

```python
# TEMP I-6 calibration, remove before commit
def _parse_args() -> argparse.Namespace:
    """TEMP I-6 calibration, remove before commit"""
    parser = argparse.ArgumentParser(description="Run GDPR evaluation pipeline.")
    parser.add_argument("--medium-threshold", type=float, default=None)
    parser.add_argument("--high-confidence-bypass", type=float, default=None)
    parser.add_argument("--min-evidence-count", type=int, default=None)
    return parser.parse_args()
```

**4. Args-anrop och kwargs-konstruktion (rader 35–43):**

```python
    args = _parse_args()  # TEMP I-6 calibration, remove before commit
    # TEMP I-6 calibration, remove before commit
    aggregator_kwargs = {}
    if args.medium_threshold is not None:
        aggregator_kwargs["medium_threshold"] = args.medium_threshold
    if args.high_confidence_bypass is not None:
        aggregator_kwargs["high_confidence_bypass"] = args.high_confidence_bypass
    if args.min_evidence_count is not None:
        aggregator_kwargs["min_evidence_count"] = args.min_evidence_count
```

**5. Aggregator-instansiering med kwargs (rad 53):**

```python
        aggregator=Aggregator(**aggregator_kwargs),  # TEMP I-6 calibration, remove before commit
```

Återställd form efter borttagning:

```python
        aggregator=Aggregator(),
```

**6. Counter-reset-anrop (rad 60):**

```python
    reset_mechanism3_counter()  # TEMP I-6 calibration, remove before commit
```

**7. Counter-print (rader 63–64):**

```python
    # TEMP I-6 calibration, remove before commit
    print(f"Mekanism 3 pass count: {get_mechanism3_count()}")
```

## Motivering för borttagning

I-6 omformulerades efter två substansella fynd:

1. **Fas 1-invarians (13 körningar):** Aggregator-trösklarna påverkar inte
   finding-listan, endast `Classification.identifiability`. Matcher
   (Lager 1–3) och aggregator (Lager 4) är separerade per Beslut 18
   (Single Responsibility). I-6:s ursprungliga premiss om
   Precision-lyft via trösklar är inte arkitekturellt möjlig.

2. **num_ctx-fixens försumbara delta (post-fix):** Omkörning mot fixad
   provider gav F1 -0.15 procentenheter på full pipeline, inom decode-bruset.
   Trunkering påverkade inte iteration 2:s utvärdering mätbart, och fortsatt
   kalibrering mot post-fix-baslinje ger inget nytt forskningsbidrag.

Beslut 51 (Loggbok iteration 3): behåll defaults från Beslut 20
(`medium_threshold=0.7`, `high_confidence_bypass=0.85`,
`min_evidence_count=2`). Bidraget formaliseras som arkitektonisk
designinsikt i rapporten, inte som kalibreringstabell.

TEMP-instrumenteringen tjänar inget syfte i
post-omformulerings-arkitekturen.

## Återskapning vid behov

Om framtida arbete behöver återta TEMP-instrumenteringen:

1. Se introduktionen i commit `7c8247a` (`tools(i6): empirical token
   measurement for layer prompts` — instrumenteringen infördes som del av
   I-6 fas 1).
2. Se borttagningen i samma commit som lägger till denna fil (commit-meddelandet
   beskriver vilka filer som påverkades och varför).
3. Sessionsloggar i `docs/iteration_3_implementation.md` (Session 2026-05-14
   till 2026-05-14d) beskriver användningsmönstret och hur räknaren
   tolkades mot fas 1-tabellen i `docs/iteration_3_threshold_calibration.md`.

Koden i denna fil är verbatim — kopiera in och uppdatera importerna i
`run_evaluation.py` så återskapas instrumenteringen exakt.

## Referenser

- `docs/iteration_3_threshold_calibration.md` (fas 1-data, 13 körningar
  med invarianta finding-counts TP=212/FP=100/FN=21)
- `docs/iteration_3_num_ctx_fix.md` (num_ctx-fixens pre/post/delta-tabeller)
- `docs/iteration_3_token_measurement.md` (Utfall C — token-mätningen som
  motiverade num_ctx-fixen)
- Beslut 51, Loggbok iteration 3 (omformulering av I-6)
- Beslut 20 (defaults som behålls), Beslut 18 (Single Responsibility)
