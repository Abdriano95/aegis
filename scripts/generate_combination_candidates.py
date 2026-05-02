#!/usr/bin/env python3
"""
Generate CombinationLayer test candidates (FAS A) for Issue #73.

Model-family asymmetry: gemma2:9b (Ollama) generates candidates here;
qwen2.5:7b-instruct is the evaluation model used separately at evaluation time.

Circularity note: All four structural cells are generated synthetically.
Cell 2 (edge cases) is NOT constructed manually. This is a known
methodological limitation to document in the FAS B data statement.

Guide-parser note: _extract_section and related helpers are copied from
generate_article9_candidates.py because scripts/ is not a Python package.
Technical debt: refactor to scripts/_guide_utils.py in iteration 3.
"""
from __future__ import annotations

import argparse
import datetime
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.layers.llm import LLMProviderError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("generate_combination_candidates")


ALLOWED_CATEGORIES = {"context.yrke", "context.plats", "context.organisation"}
ALLOWED_SPECIFICITY = {"låg", "mellan", "hög"}
SPECIFICITY_ORDER = {"låg": 0, "mellan": 1, "hög": 2}

SYSTEM_PROMPT = "Du är en assistent som genererar fiktiv testdata i strikt JSON-format."
GUIDE_PATH = project_root / "docs" / "combination_annotation_guidelines.md"

_JSON_SCHEMA = """\
Svara EXAKT med följande JSON-struktur, ingenting annat:
{
  "text": "<svensk text, minst 30 tecken, idiomatisk svenska>",
  "description": "<beskriv vilken cell + regel som triggas och varför>",
  "expected_findings": [
    {
      "category": "context.yrke|context.plats|context.organisation",
      "text_span": "<exakt substring av text, minst 5 tecken>",
      "specificity_level": "låg|mellan|hög"
    }
  ]
}

OBS: Inkludera INTE context.kombination i expected_findings — det beräknas automatiskt.
Varje text_span MÅSTE vara en exakt substring (case-sensitive) av text-fältet."""


# ---------------------------------------------------------------------------
# Guide parser  (copied from generate_article9_candidates.py — see module doc)
# ---------------------------------------------------------------------------

def _extract_section(guidelines_md: str, section_id: str) -> str:
    """Extract a markdown section by its numeric ID (e.g. '3', '4.1', '5.2')."""
    lines = guidelines_md.split("\n")
    extracted_lines: list[str] = []
    in_section = False
    section_level = 0

    header_pattern = re.compile(r"^(#+)\s+([0-9.]+)\s*(.*)")

    for line in lines:
        match = header_pattern.match(line)
        if match:
            level_str, sid, _ = match.groups()
            level = len(level_str)
            sid = sid.rstrip(".")

            if sid == section_id:
                in_section = True
                section_level = level
                extracted_lines.append(line)
                continue
            elif in_section:
                if level <= section_level:
                    break

        if in_section:
            extracted_lines.append(line)

    return "\n".join(extracted_lines)


def extract_guide_sections(guide_path: Path) -> dict[str, str]:
    """Return {section_id: section_text} for all numbered sections in the guide."""
    md = guide_path.read_text(encoding="utf-8")
    header_pattern = re.compile(r"^(#+)\s+([0-9.]+)\s*(.*)", re.MULTILINE)
    section_ids = [m.group(2).rstrip(".") for m in header_pattern.finditer(md)]
    return {sid: _extract_section(md, sid) for sid in section_ids}


def extract_combination_rule(guide_path: Path, rule: str) -> str:
    """Return the text of rule 'A', 'B', 'C', or 'D' from section 5.2."""
    md = guide_path.read_text(encoding="utf-8")
    section_52 = _extract_section(md, "5.2")
    pattern = re.compile(
        rf"(Regel {re.escape(rule)}\s*--.*?)(?=Regel [A-D]|$)",
        re.DOTALL,
    )
    match = pattern.search(section_52)
    return match.group(1).strip() if match else ""


def get_guidelines_git_hash(filepath: Path) -> str:
    """Return git commit hash of the guidelines file; warn and return '' on failure."""
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%H", "--", str(filepath)],
            capture_output=True,
            text=True,
            cwd=str(project_root),
        )
        if result.returncode != 0 or not result.stdout.strip():
            logger.warning("Could not determine git hash for guidelines.")
            return ""
        return result.stdout.strip()
    except Exception as e:
        logger.warning(f"Git hash lookup failed: {e}")
        return ""


# ---------------------------------------------------------------------------
# Prompt construction — thick injection, one function per cell/rule
# ---------------------------------------------------------------------------

def create_prompt_cell1_rule_a(sections: dict[str, str]) -> str:
    """Cell 1 Regel A: ≥2 signals with hög specificitet → identifiable."""
    return (
        "Du genererar en fiktiv, realistisk svensk text (t.ex. e-post, intern anteckning, ärendelogg) "
        "för ett GDPR-testdataset. Texten ska trigga REGEL A i pusselbitseffekten.\n\n"
        "REGEL A i korthet: Minst TVÅ signaler med HÖG specificitet gör kombinationen identifierande.\n"
        "Exempel: VD (hög yrke) + Hvitfeldtska gymnasiets musiklinje (hög organisation).\n\n"
        "Läs noga dessa guidesektioner:\n\n"
        f"--- SIGNALTYPER ---\n{sections.get('3', '')}\n\n"
        f"--- YRKESSPECIFICITET ---\n{sections.get('4.1', '')}\n\n"
        f"--- PLATSSPECIFICITET ---\n{sections.get('4.2', '')}\n\n"
        f"--- ORGANISATIONSSPECIFICITET ---\n{sections.get('4.3', '')}\n\n"
        f"--- KOMBINATIONSREGEL A ---\n{sections.get('regel_a', '')}\n\n"
        "Krav på texten:\n"
        "- Exakt 2 signaler (valfri kombination av yrke/plats/organisation), BÅDA med hög specificitet\n"
        "- Inga direkta identifierare (personnummer, mejl, namn, adresser)\n"
        "- Inga artikel 9-uppgifter (hälsa, religion, etnicitet, etc.)\n"
        "- Fiktiv situation, idiomatisk svenska\n\n"
        + _JSON_SCHEMA
    )


def create_prompt_cell1_rule_b(sections: dict[str, str]) -> str:
    """Cell 1 Regel B: ≥3 signals with ≥mellan specificitet → identifiable."""
    return (
        "Du genererar en fiktiv, realistisk svensk text (t.ex. e-post, intern anteckning, ärendelogg) "
        "för ett GDPR-testdataset. Texten ska trigga REGEL B i pusselbitseffekten.\n\n"
        "REGEL B i korthet: Minst TRE signaler med minst MELLAN specificitet (varav åtminstone en hög eller mellan) "
        "gör kombinationen identifierande.\n"
        "Exempel: barnmorska (mellan yrke) + Borås Stads förlossningsavdelning (mellan organisation) + Borås (mellan plats).\n\n"
        "Läs noga dessa guidesektioner:\n\n"
        f"--- SIGNALTYPER ---\n{sections.get('3', '')}\n\n"
        f"--- YRKESSPECIFICITET ---\n{sections.get('4.1', '')}\n\n"
        f"--- PLATSSPECIFICITET ---\n{sections.get('4.2', '')}\n\n"
        f"--- ORGANISATIONSSPECIFICITET ---\n{sections.get('4.3', '')}\n\n"
        f"--- KOMBINATIONSREGEL B ---\n{sections.get('regel_b', '')}\n\n"
        "Krav på texten:\n"
        "- Exakt 3 signaler (yrke + plats + organisation), ALLA med minst mellan specificitet\n"
        "- Inga direkta identifierare (personnummer, mejl, namn, adresser)\n"
        "- Inga artikel 9-uppgifter\n"
        "- Fiktiv situation, idiomatisk svenska\n\n"
        + _JSON_SCHEMA
    )


def create_prompt_cell1_rule_c(sections: dict[str, str]) -> str:
    """Cell 1 Regel C: ≥2 signals with ≥mellan + hög narrativ specificitet → identifiable."""
    return (
        "Du genererar en fiktiv, realistisk svensk text (t.ex. e-post, intern anteckning, ärendelogg) "
        "för ett GDPR-testdataset. Texten ska trigga REGEL C i pusselbitseffekten.\n\n"
        "REGEL C i korthet: Minst TVÅ signaler med minst MELLAN specificitet OCH hög narrativ specificitet "
        "gör kombinationen identifierande.\n"
        "Narrativ specificitet (hög) = texten innehåller en händelsereferens, tidsmarkör eller demografisk detalj "
        "som markant smalnar av populationen.\n"
        "Exempel: 'Den nya barnmorskan som började i augusti på Borås förlossningsavdelning' "
        "(yrke mellan + organisation mellan + narrativ hög).\n\n"
        "Läs noga dessa guidesektioner:\n\n"
        f"--- SIGNALTYPER ---\n{sections.get('3', '')}\n\n"
        f"--- YRKESSPECIFICITET ---\n{sections.get('4.1', '')}\n\n"
        f"--- PLATSSPECIFICITET ---\n{sections.get('4.2', '')}\n\n"
        f"--- ORGANISATIONSSPECIFICITET ---\n{sections.get('4.3', '')}\n\n"
        f"--- NARRATIV SPECIFICITET ---\n{sections.get('4.4', '')}\n\n"
        f"--- KOMBINATIONSREGEL C ---\n{sections.get('regel_c', '')}\n\n"
        "Krav på texten:\n"
        "- Minst 2 signaler med minst mellan specificitet\n"
        "- Texten MÅSTE innehålla tydlig narrativ specificitet (hög): händelsereferens, tidsmarkör eller demografisk detalj\n"
        "- Inga direkta identifierare (personnummer, mejl, namn, adresser)\n"
        "- Inga artikel 9-uppgifter\n"
        "- Fiktiv situation, idiomatisk svenska\n\n"
        + _JSON_SCHEMA
    )


def create_prompt_cell2_borderline(sections: dict[str, str]) -> str:
    """Cell 2: edge case — combination that could go either way."""
    return (
        "Du genererar en fiktiv, realistisk svensk text (t.ex. e-post, intern anteckning, ärendelogg) "
        "för ett GDPR-testdataset. Texten ska vara ett GRÄNSFALL för pusselbitseffekten — en situation "
        "där bedömningen är genuint svår och kunde gå åt båda hållen.\n\n"
        "Typiska gränsfall:\n"
        "- Två mellanspecifika signaler utan narrativ förstärkning (nära Regel B men uppfyller det inte)\n"
        "- En hög + en låg signal utan ytterligare kontext (nära Regel A men saknar den andra høga)\n"
        "- Tre signaler varav en är hög och resten låga\n\n"
        "Läs noga dessa guidesektioner:\n\n"
        f"--- SIGNALTYPER ---\n{sections.get('3', '')}\n\n"
        f"--- YRKESSPECIFICITET ---\n{sections.get('4.1', '')}\n\n"
        f"--- PLATSSPECIFICITET ---\n{sections.get('4.2', '')}\n\n"
        f"--- ORGANISATIONSSPECIFICITET ---\n{sections.get('4.3', '')}\n\n"
        f"--- NARRATIV SPECIFICITET ---\n{sections.get('4.4', '')}\n\n"
        f"--- KOMBINATIONSREGLER (alla) ---\n{sections.get('5.2', '')}\n\n"
        "Krav på texten:\n"
        "- 1-3 signaler men kombinationen uppfyller INTE tydligt Regel A, B eller C\n"
        "- description-fältet MÅSTE motivera varför det är ett gränsfall "
        "(t.ex. 'gränsfall: två mellan-signaler, faller under Regel D men nära Regel B')\n"
        "- Inga direkta identifierare (personnummer, mejl, namn, adresser)\n"
        "- Inga artikel 9-uppgifter\n"
        "- Fiktiv situation, idiomatisk svenska\n\n"
        + _JSON_SCHEMA
    )


def create_prompt_cell3_no_signals(sections: dict[str, str]) -> str:
    """Cell 3: negative control — no signals at all."""
    return (
        "Du genererar en fiktiv, realistisk svensk text (t.ex. e-post, mötesbeslut, teknisk logg, systemmeddelande) "
        "för ett GDPR-testdataset. Texten ska INTE innehålla några signaler av typerna yrke, plats eller organisation.\n\n"
        "Syftet är att verifiera att systemet inte hallucinerar signaler i neutral text.\n\n"
        "Referens — vad som INTE ska förekomma i texten:\n\n"
        f"--- SIGNALTYPER (undvik dessa) ---\n{sections.get('3', '')}\n\n"
        "Krav på texten:\n"
        "- Inga yrkestitlar, roller eller funktioner\n"
        "- Inga ortnamn, stadsdelar eller geografiska platser\n"
        "- Inga organisationer, myndigheter, företag eller institutioner\n"
        "- Texten kan handla om scheman, möten, tekniska processer, abstrakta beslut, administrativa rutiner\n"
        "- expected_findings ska vara en TOM lista []\n"
        "- Inga direkta identifierare (personnummer, mejl, namn)\n"
        "- Inga artikel 9-uppgifter\n"
        "- Fiktiv situation, idiomatisk svenska\n\n"
        "Svara EXAKT med följande JSON-struktur, ingenting annat:\n"
        "{\n"
        '  "text": "<svensk text, minst 30 tecken, utan yrke/plats/organisation>",\n'
        '  "description": "Cell 3 negativ kontroll: inga signaler",\n'
        '  "expected_findings": []\n'
        "}"
    )


def create_prompt_cell4_signals_not_identifiable(sections: dict[str, str]) -> str:
    """Cell 4: negative control — signals present but not identifiable (Rule D)."""
    return (
        "Du genererar en fiktiv, realistisk svensk text (t.ex. e-post, intern anteckning, ärendelogg) "
        "för ett GDPR-testdataset. Texten ska innehålla EN ELLER TVÅ signaler (yrke, plats, organisation) "
        "men kombinationen ska INTE vara identifierande — Regel D (default) gäller.\n\n"
        "Typiska Regel D-fall:\n"
        "- Enstaka lågspecifik signal ('Många jobbar som lärare i Stockholm')\n"
        "- Kombinationer av enbart lågspecifika signaler utan narrativ förstärkning\n\n"
        "Läs noga dessa guidesektioner:\n\n"
        f"--- SIGNALTYPER ---\n{sections.get('3', '')}\n\n"
        f"--- YRKESSPECIFICITET ---\n{sections.get('4.1', '')}\n\n"
        f"--- PLATSSPECIFICITET ---\n{sections.get('4.2', '')}\n\n"
        f"--- ORGANISATIONSSPECIFICITET ---\n{sections.get('4.3', '')}\n\n"
        f"--- KOMBINATIONSREGEL D (default) ---\n{sections.get('regel_d', '')}\n\n"
        "Krav på texten:\n"
        "- Max 2 signaler, INGA med hög specificitet\n"
        "- Kombinationen faller tydligt under Regel D (inte identifierande)\n"
        "- expected_findings innehåller de individuella signalerna men INGET context.kombination\n"
        "- Inga direkta identifierare (personnummer, mejl, namn, adresser)\n"
        "- Inga artikel 9-uppgifter\n"
        "- Fiktiv situation, idiomatisk svenska\n\n"
        + _JSON_SCHEMA
    )


# ---------------------------------------------------------------------------
# Rule engine for Cell 2 aggregate detection
# ---------------------------------------------------------------------------

def _should_add_aggregate_cell2(findings: list[dict]) -> bool:
    """Return True if Cell 2 findings formally trigger Rule A or Rule B."""
    levels = [f.get("specificity_level", "") for f in findings]
    high_count = sum(1 for lv in levels if lv == "hög")
    at_least_mellan = sum(
        1 for lv in levels if SPECIFICITY_ORDER.get(lv, -1) >= SPECIFICITY_ORDER["mellan"]
    )
    if high_count >= 2:
        return True
    if len(findings) >= 3 and at_least_mellan >= 3:
        return True
    return False


# ---------------------------------------------------------------------------
# Aggregate computation
# ---------------------------------------------------------------------------

def compute_aggregate_span(text: str, findings: list[dict]) -> dict:
    """Compute context.kombination deterministically as text[min(starts):max(ends)].

    Aggregate findings intentionally carry no specificity_level — FAS B annotators
    verify specificity at the individual signal level, not on the aggregate span.
    """
    starts = [text.find(f["text_span"]) for f in findings]
    ends = [s + len(f["text_span"]) for s, f in zip(starts, findings)]
    agg_start = min(starts)
    agg_text = text[agg_start : max(ends)]
    return {
        "category": "context.kombination",
        "text_span": agg_text,
        "start": agg_start,
        "end": agg_start + len(agg_text),
        "is_identifiable": True,
    }


# ---------------------------------------------------------------------------
# Candidate generation with 2-attempt retry loop
# ---------------------------------------------------------------------------

def generate_candidate(
    provider,
    prompt_fn,
    sections: dict[str, str],
    cell_label: str,
    always_aggregate: bool = False,
    allow_aggregate_if_rule_fires: bool = False,
) -> dict | None:
    """Generate and validate one candidate. Returns None if all attempts fail.

    always_aggregate=True  → Cell 1: add aggregate whenever ≥2 valid findings exist.
    allow_aggregate_if_rule_fires=True → Cell 2: add aggregate only if rule engine fires.
    Both False → Cell 3, Cell 4: never add aggregate.
    """
    prompt = prompt_fn(sections)

    for attempt in range(2):
        if attempt == 1:
            logger.info(f"  [{cell_label}] Validation failed. Re-prompting...")
            prompt += (
                "\n\nOBS: I ditt förra svar misslyckades valideringen. "
                "Se till att 'text' är minst 30 tecken, och att varje 'text_span' "
                "är en EXAKT, case-sensitive sub-sträng av 'text' och minst 5 tecken lång. "
                "category måste vara en av: context.yrke, context.plats, context.organisation. "
                "specificity_level måste vara en av: låg, mellan, hög. "
                "Inkludera INTE context.kombination i expected_findings."
            )

        try:
            data = provider.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT)
        except LLMProviderError as e:
            logger.error(f"  [{cell_label}] Provider error: {e}")
            continue

        if not isinstance(data, dict) or "text" not in data or "expected_findings" not in data:
            logger.warning(f"  [{cell_label}] Missing required keys.")
            continue

        text = data["text"]
        raw_findings = data.get("expected_findings", [])

        if not isinstance(text, str) or len(text) < 30:
            logger.warning(f"  [{cell_label}] Text too short ({len(text) if isinstance(text, str) else 'non-string'} chars).")
            continue

        valid_findings: list[dict] = []
        skip = False
        for finding in raw_findings:
            text_span = finding.get("text_span", "")
            category = finding.get("category", "")
            specificity = finding.get("specificity_level", "")

            if not isinstance(text_span, str) or len(text_span) < 5:
                logger.warning(f"  [{cell_label}] text_span too short or missing: '{text_span}'")
                skip = True
                break

            if category not in ALLOWED_CATEGORIES:
                logger.warning(f"  [{cell_label}] Invalid category: '{category}'")
                skip = True
                break

            if specificity not in ALLOWED_SPECIFICITY:
                logger.warning(f"  [{cell_label}] Invalid specificity_level: '{specificity}'")
                skip = True
                break

            start_idx = text.find(text_span)
            if start_idx == -1:
                # Case-insensitive fallback with case-correct recovery
                lower_idx = text.lower().find(text_span.lower())
                if lower_idx == -1:
                    logger.warning(f"  [{cell_label}] text_span not found in text: '{text_span}'")
                    skip = True
                    break
                text_span = text[lower_idx : lower_idx + len(text_span)]
                start_idx = lower_idx

            valid_findings.append({
                "category": category,
                "text_span": text_span,
                "start": start_idx,
                "end": start_idx + len(text_span),
                "specificity_level": specificity,
            })

        if skip:
            continue

        # Cell 1 requires ≥2 findings to form a valid combination
        if always_aggregate and len(valid_findings) < 2:
            logger.warning(
                f"  [{cell_label}] Cell 1 requires ≥2 findings, got {len(valid_findings)}. Retrying."
            )
            continue

        if not data.get("description"):
            data["description"] = f"Genererad test-text för {cell_label}"

        data["expected_findings"] = valid_findings

        if always_aggregate and len(valid_findings) >= 2:
            data["expected_findings"].append(compute_aggregate_span(text, valid_findings))
        elif allow_aggregate_if_rule_fires and _should_add_aggregate_cell2(valid_findings):
            data["expected_findings"].append(compute_aggregate_span(text, valid_findings))

        return data

    logger.error(f"  [{cell_label}] Candidate dropped after 2 attempts.")
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate CombinationLayer test candidates (FAS A) for Issue #73."
    )
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument("--model", default="gemma2:9b", help="Ollama model (default: gemma2:9b).")
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--cell1-rule-a", type=int, default=4, dest="cell1_rule_a")
    parser.add_argument("--cell1-rule-b", type=int, default=3, dest="cell1_rule_b")
    parser.add_argument("--cell1-rule-c", type=int, default=3, dest="cell1_rule_c")
    parser.add_argument("--cell2", type=int, default=7)
    parser.add_argument("--cell3", type=int, default=6)
    parser.add_argument("--cell4", type=int, default=7)
    args = parser.parse_args()

    logger.info(f"Model: {args.model}  temperature: {args.temperature}")
    logger.info(
        f"Targets — cell1_rule_a:{args.cell1_rule_a}  cell1_rule_b:{args.cell1_rule_b}  "
        f"cell1_rule_c:{args.cell1_rule_c}  cell2:{args.cell2}  "
        f"cell3:{args.cell3}  cell4:{args.cell4}  "
        f"total:{args.cell1_rule_a + args.cell1_rule_b + args.cell1_rule_c + args.cell2 + args.cell3 + args.cell4}"
    )

    if not GUIDE_PATH.exists():
        logger.error(f"Guidelines not found: {GUIDE_PATH}")
        sys.exit(1)

    guidelines_hash = get_guidelines_git_hash(GUIDE_PATH)
    sections = extract_guide_sections(GUIDE_PATH)
    # Pre-extract individual rule paragraphs for focused prompt injection
    for rule in ("A", "B", "C", "D"):
        sections[f"regel_{rule.lower()}"] = extract_combination_rule(GUIDE_PATH, rule)

    try:
        provider = get_llm_provider(model_name=args.model)
        provider._temperature = args.temperature
    except Exception as e:
        logger.error(f"Failed to instantiate LLM provider: {e}")
        sys.exit(1)

    # (label, prompt_fn, target, always_aggregate, allow_aggregate_if_rule_fires)
    runs = [
        ("Cell 1 Regel A", create_prompt_cell1_rule_a, args.cell1_rule_a, True, False),
        ("Cell 1 Regel B", create_prompt_cell1_rule_b, args.cell1_rule_b, True, False),
        ("Cell 1 Regel C", create_prompt_cell1_rule_c, args.cell1_rule_c, True, False),
        ("Cell 2 gränsfall", create_prompt_cell2_borderline, args.cell2, False, True),
        ("Cell 3 inga signaler", create_prompt_cell3_no_signals, args.cell3, False, False),
        ("Cell 4 signaler ej id.", create_prompt_cell4_signals_not_identifiable, args.cell4, False, False),
    ]
    run_keys = [
        "cell1_rule_a", "cell1_rule_b", "cell1_rule_c",
        "cell2_borderline", "cell3_no_signals", "cell4_signals_not_identifiable",
    ]

    candidates: list[dict] = []
    actual_counts: dict[str, int] = {k: 0 for k in run_keys}
    dropped_counts: dict[str, int] = {k: 0 for k in run_keys}

    for (label, prompt_fn, target, always_agg, rule_agg), key in zip(runs, run_keys):
        logger.info(f"=== {label}: generating {target} candidates ===")
        for i in range(target):
            logger.info(f"  {label}: {i + 1}/{target}")
            candidate = generate_candidate(
                provider, prompt_fn, sections, label,
                always_aggregate=always_agg,
                allow_aggregate_if_rule_fires=rule_agg,
            )
            if candidate:
                candidates.append(candidate)
                actual_counts[key] += 1
            else:
                dropped_counts[key] += 1

    total_generated = sum(actual_counts.values())
    total_dropped = sum(dropped_counts.values())
    target_total = sum(t for _, _, t, _, _ in runs)

    logger.info("=" * 40)
    logger.info(f"DONE — generated:{total_generated}  dropped:{total_dropped}  target:{target_total}")
    if total_generated < target_total:
        logger.warning(f"FELL SHORT: {total_generated}/{target_total}")

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote {len(candidates)} candidates → {output_path}")

    metadata = {
        "generation_date": datetime.datetime.now().isoformat(),
        "model": args.model,
        "provider": type(provider).__name__.replace("Provider", "").lower(),
        "provider_endpoint": getattr(provider, "endpoint", None),
        "temperature": args.temperature,
        "target_distribution": {
            "cell1_rule_a": args.cell1_rule_a,
            "cell1_rule_b": args.cell1_rule_b,
            "cell1_rule_c": args.cell1_rule_c,
            "cell2_borderline": args.cell2,
            "cell3_no_signals": args.cell3,
            "cell4_signals_not_identifiable": args.cell4,
        },
        "actual_generated": {
            **actual_counts,
            "total": total_generated,
            "dropped": dropped_counts,
        },
        "guideline_reference": {
            "path": "docs/combination_annotation_guidelines.md",
            "git_commit": guidelines_hash,
            "generated_at": datetime.datetime.now().isoformat(),
        },
    }

    meta_path = output_path.parent / ".combination_candidates_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote metadata → {meta_path}")


if __name__ == "__main__":
    main()
