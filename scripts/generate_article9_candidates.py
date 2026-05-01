#!/usr/bin/env python3
"""Generate Article 9 test dataset candidates using an LLM.

Uses the gdpr-classifier LLMProvider abstraction to generate synthetic Swedish
texts containing specific Article 9 data categories, or negative controls.
Validates the generated output (specifically text spans) and re-prompts once
if needed before dropping the candidate.
"""

import argparse
import datetime
import json
import logging
import sys
from pathlib import Path

# Add the project root to sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from gdpr_classifier.core.category import Category
from gdpr_classifier.config import get_llm_provider
from gdpr_classifier.layers.llm import LLMProviderError


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("generate_candidates")


# List of target Article 9 categories
TARGET_CATEGORIES = [
    Category.HALSODATA,
    Category.ETNISKT_URSPRUNG,
    Category.POLITISK_ASIKT,
    Category.RELIGIOS_OVERTYGELSE,
    Category.FACKMEDLEMSKAP,
    Category.BIOMETRISK_DATA,
    Category.GENETISK_DATA,
    Category.SEXUELL_LAGGNING,
]


def create_prompt(category: str | None, is_negative: bool = False) -> str:
    """Create a generation prompt for the LLM."""
    if is_negative:
        return (
            "Din uppgift är att skriva en kort, realistisk, men helt fiktiv text "
            "på svenska (t.ex. ett e-postmeddelande, chattmeddelande, en intern anteckning eller en systemlogg) "
            "som representerar vanlig arbetsplatskommunikation. "
            "Texten får INNEHÅLLA vanliga personuppgifter (t.ex. påhittade namn, e-post, telefonnummer "
            "eller adresser) MEN DEN FÅR ABSOLUT INTE INNEHÅLLA NÅGON ARTIKEL 9-DATA (känsliga personuppgifter "
            "som hälsa, ras, politisk åsikt, religion, facktillhörighet, sexuell läggning, genetisk eller "
            "biometrisk data).\n\n"
            "Returnera texten och en lista med fynd. Eftersom detta är ett negativt testfall "
            "ska din lista över expected_findings vara TOM.\n\n"
            "Svara EXAKT med följande JSON-struktur, ingenting annat:\n"
            "{\n"
            '  "text": "<din påhittade text>",\n'
            '  "description": "Negativ kontroll: arbetsplatskommunikation utan artikel 9-data",\n'
            '  "expected_findings": []\n'
            "}"
        )
    
    return (
        f"Din uppgift är att skriva en kort, realistisk, men helt fiktiv text "
        f"på svenska (t.ex. ett e-postmeddelande, chattmeddelande, en intern anteckning eller en ärendelogg) "
        f"som representerar arbetsplatskommunikation eller kundtjänstärenden. "
        f"Texten MÅSTE INNEHÅLLA information som klassificeras som GDPR Artikel 9-kategorin: '{category}'. "
        f"Använd inga riktiga personers data, hitta på namn, situationer och all information.\n\n"
        f"Returnera texten samt vilka artikel 9-fynd som finns i texten. "
        f"För varje fynd, ange exakt vilken textsträng (text_span) som utgör den känsliga uppgiften. "
        f"Textsträngen måste finnas exakt som den är skriven inuti texten (case-sensitive).\n\n"
        f"Svara EXAKT med följande JSON-struktur, ingenting annat:\n"
        "{\n"
        '  "text": "<din påhittade text>",\n'
        f'  "description": "Exempel som innehåller {category}",\n'
        '  "expected_findings": [\n'
        '    {\n'
        f'      "category": "{category}",\n'
        '      "text_span": "<exakt textsträng från din genererade text som utgör uppgiften>"\n'
        '    }\n'
        '  ]\n'
        "}"
    )


def generate_candidate(provider, category: str | None, is_negative: bool) -> dict | None:
    """Generate a single candidate and validate text spans."""
    prompt = create_prompt(category, is_negative)
    system_instruction = "Du är en assistent som genererar fiktiv testdata i strikt JSON-format."
    
    # Try twice (initial + 1 re-prompt)
    for attempt in range(2):
        if attempt == 1:
            logger.info("  Validation failed on attempt 1. Re-prompting...")
            prompt += "\n\nOBS: I ditt förra svar stämde inte 'text_span' överens med något avsnitt i 'text'. Var extremt noga med att 'text_span' är en EXAKT sub-sträng av 'text'."

        try:
            data = provider.generate_json(
                prompt=prompt,
                system_prompt=system_instruction,
            )
        except LLMProviderError as e:
            logger.error(f"  Provider error: {e}")
            continue
            
        # Basic schema validation
        if not isinstance(data, dict) or "text" not in data or "expected_findings" not in data:
            logger.warning("  Missing required keys in JSON.")
            continue
            
        text = data["text"]
        findings = data["expected_findings"]
        
        # Validate and fix spans
        valid_spans = True
        for finding in findings:
            text_span = finding.get("text_span")
            if not text_span:
                valid_spans = False
                break
                
            start_idx = text.find(text_span)
            if start_idx == -1:
                logger.warning(f"  text_span '{text_span}' not found in text.")
                valid_spans = False
                break
                
            finding["start"] = start_idx
            finding["end"] = start_idx + len(text_span)
            
            # Ensure category is valid enum
            cat = finding.get("category")
            try:
                Category(cat)
            except ValueError:
                logger.warning(f"  Invalid category '{cat}'.")
                valid_spans = False
                break
                
        if valid_spans:
            if "description" not in data:
                data["description"] = f"Genererad test-text för {category if category else 'negativ kontroll'}"
            return data
            
    logger.error("  Candidate failed validation after re-prompt. Dropping.")
    return None


def main():
    parser = argparse.ArgumentParser(description="Generate synthetic dataset candidates.")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument("--model", default="qwen2.5:7b-instruct", help="Model to use.")
    parser.add_argument("--target-per-category", type=int, default=6, help="Target count per positive category.")
    parser.add_argument("--negative-controls", type=int, default=12, help="Target count for negative controls.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation.")
    args = parser.parse_args()
    
    logger.info(f"Starting generation with model {args.model}")
    
    # Instantiate provider
    try:
        provider = get_llm_provider(model_name=args.model)
        # Override temperature for generation
        provider._temperature = args.temperature
    except Exception as e:
        logger.error(f"Failed to instantiate LLM provider: {e}")
        sys.exit(1)
        
    candidates = []
    category_counts = {cat.value: 0 for cat in TARGET_CATEGORIES}
    negative_count = 0
    
    # Generate positive candidates
    for cat in TARGET_CATEGORIES:
        logger.info(f"Generating positive candidates for {cat.value}...")
        for i in range(args.target_per_category):
            logger.info(f"  Candidate {i+1}/{args.target_per_category}")
            candidate = generate_candidate(provider, cat.value, is_negative=False)
            if candidate:
                candidates.append(candidate)
                category_counts[cat.value] += 1
                
    # Generate negative candidates
    logger.info("Generating negative controls...")
    for i in range(args.negative_controls):
        logger.info(f"  Negative Candidate {i+1}/{args.negative_controls}")
        candidate = generate_candidate(provider, None, is_negative=True)
        if candidate:
            candidates.append(candidate)
            negative_count += 1
            
    total_generated = sum(category_counts.values()) + negative_count
    target_total = (len(TARGET_CATEGORIES) * args.target_per_category) + args.negative_controls
    
    logger.info("=" * 40)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 40)
    logger.info(f"Target: {target_total}, Generated: {total_generated}")
    if total_generated < target_total:
        logger.warning(f"!!! FELL SHORT OF TARGET: Generated {total_generated} instead of {target_total} !!!")
        
    # Write dataset candidates
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(candidates, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote {len(candidates)} candidates to {output_path}")
    
    # Write metadata
    metadata = {
        "generation_date": datetime.datetime.now().isoformat(),
        "model": args.model,
        "temperature": args.temperature,
        "target_per_category": args.target_per_category,
        "negative_controls_target": args.negative_controls,
        "actual_generated": {
            "total": total_generated,
            "per_category": category_counts,
            "negative_controls": negative_count
        }
    }
    
    meta_path = output_path.parent / ".candidates_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote metadata to {meta_path}")


if __name__ == "__main__":
    main()
