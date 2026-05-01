#!/usr/bin/env python3
"""Generate Article 9 test dataset candidates using an LLM (FAS A2).

Uses the gdpr-classifier LLMProvider abstraction to generate synthetic Swedish
texts containing specific Article 9 data categories, or negative controls.
Validates the generated output (specifically text spans) and re-prompts once
if needed before dropping the candidate. Integrates with the annotation guidelines.
"""

import argparse
import datetime
import json
import logging
import os
import re
import subprocess
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


def check_guidelines_status(filepath: Path) -> str:
    """Ensure guidelines are committed and return the commit hash."""
    # Check if modified
    try:
        status_output = subprocess.check_output(
            ["git", "status", "--porcelain", str(filepath)],
            cwd=str(project_root),
            text=True
        ).strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Git status check failed: {e}")
        sys.exit(1)
        
    if status_output:
        logger.error(f"The file {filepath.relative_to(project_root)} is modified.")
        logger.error("Please commit your changes to the annotation guidelines before generating candidates to ensure traceability.")
        sys.exit(1)
        
    # Get commit hash
    try:
        commit_hash = subprocess.check_output(
            ["git", "rev-parse", f"HEAD:{filepath.relative_to(project_root)}"],
            cwd=str(project_root),
            text=True
        ).strip()
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to get git commit hash: {e}")
        sys.exit(1)
        
    return commit_hash


def extract_guideline_section(guidelines_md: str, section_id: str) -> str:
    """Extract a specific section from the markdown guidelines.
    
    Args:
        guidelines_md: The full markdown text.
        section_id: The section identifier (e.g., "4.1" or "5").
        
    Returns:
        The text of the section including its header, up to the next header
        of the same or higher level.
    """
    lines = guidelines_md.split("\n")
    extracted_lines = []
    in_section = False
    section_level = 0
    
    # Regex to match headers like "## 5. " or "### 4.1 "
    # Capture the '#' to determine level, and the ID part.
    header_pattern = re.compile(r"^(#+)\s+([0-9.]+)\s*(.*)")
    
    for line in lines:
        match = header_pattern.match(line)
        if match:
            level_str, sid, _ = match.groups()
            level = len(level_str)
            
            # Remove trailing dot if exists, e.g. "5." -> "5"
            sid = sid.rstrip(".")
            
            if sid == section_id:
                in_section = True
                section_level = level
                extracted_lines.append(line)
                continue
            elif in_section:
                # If we encounter another header of same or higher (fewer #) level, stop
                if level <= section_level:
                    break
                    
        if in_section:
            extracted_lines.append(line)
            
    return "\n".join(extracted_lines)


def get_category_section_id(category: str) -> str:
    """Map category enum values to their section IDs in the guidelines."""
    mapping = {
        Category.HALSODATA.value: "4.1",
        Category.ETNISKT_URSPRUNG.value: "4.2",
        Category.POLITISK_ASIKT.value: "4.3",
        Category.RELIGIOS_OVERTYGELSE.value: "4.4",
        Category.FACKMEDLEMSKAP.value: "4.5",
        Category.GENETISK_DATA.value: "4.6",
        Category.BIOMETRISK_DATA.value: "4.7",
        Category.SEXUELL_LAGGNING.value: "4.8",
    }
    return mapping.get(category, "")


def create_prompt(category: str | None, is_negative: bool, guidelines_context: str = "") -> str:
    """Create a generation prompt for the LLM."""
    if is_negative:
        return (
            "Din uppgift är att skriva en kort, realistisk, men helt fiktiv text "
            "på svenskt vardagsspråk (t.ex. ett e-postmeddelande, chattmeddelande, en intern anteckning eller en systemlogg) "
            "som representerar vanlig arbetsplatskommunikation. Skriv på idiomatisk svenska så som en modersmålstalare skulle formulera sig, inte som en maskinöversättning.\n\n"
            "Texten får INNEHÅLLA vanliga personuppgifter (artikel 4-data) som påhittade namn, e-post, telefonnummer "
            "eller adresser MEN DEN FÅR ABSOLUT INTE INNEHÅLLA NÅGON ARTIKEL 9-DATA (känsliga personuppgifter "
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
        f"på svenskt vardagsspråk (t.ex. ett e-postmeddelande, chattmeddelande, en intern anteckning eller en ärendelogg) "
        f"som representerar arbetsplatskommunikation eller kundtjänstärenden. Skriv på idiomatisk svenska så som en modersmålstalare skulle formulera sig, inte som en maskinöversättning.\n\n"
        f"Texten MÅSTE INNEHÅLLA information som klassificeras som GDPR Artikel 9-kategorin: '{category}'. "
        f"Använd inga riktiga personers data, hitta på namn, situationer och all information.\n\n"
        f"VARNING! Baserat på vanliga misstag, observera följande:\n"
        f"- Geografiskt ursprung (t.ex. 'från Stockholm' eller 'född i Tyskland') är INTE etnicitet.\n"
        f"- Yrken (t.ex. 'sjuksköterska' eller 'präst') är INTE i sig hälsodata eller religiös övertygelse.\n"
        f"- Projektnamn eller diskussionsämnen är INTE personliga politiska åsikter.\n\n"
        f"Läs noga följande utdrag från annoteringsguiden för att förstå vad som räknas som '{category}':\n"
        f"--- START GUIDE ---\n"
        f"{guidelines_context}\n"
        f"--- SLUT GUIDE ---\n\n"
        f"Returnera texten samt vilka artikel 9-fynd som finns i texten. "
        f"För varje fynd, ange EXAKT vilken textsträng (text_span) som utgör den känsliga uppgiften. "
        f"text_span MÅSTE vara den minsta möjliga exakta passagen som avslöjar uppgiften, INTE hela meningen. "
        f"Textsträngen måste finnas exakt som den är skriven inuti texten (case-sensitive).\n\n"
        f"Svara EXAKT med följande JSON-struktur, ingenting annat:\n"
        "{\n"
        '  "text": "<din påhittade text>",\n'
        f'  "description": "Exempel som innehåller {category}",\n'
        '  "expected_findings": [\n'
        '    {\n'
        f'      "category": "{category}",\n'
        '      "text_span": "<den exakta känsliga passagen>"\n'
        '    }\n'
        '  ]\n'
        "}"
    )


def generate_candidate(provider, category: str | None, is_negative: bool, guidelines_context: str = "") -> dict | None:
    """Generate a single candidate and validate text spans and lengths."""
    import time
    
    prompt = create_prompt(category, is_negative, guidelines_context)
    system_instruction = "Du är en assistent som genererar fiktiv testdata i strikt JSON-format."
    
    # Try up to 2 times for validation, plus unlimited retries for 429 errors
    validation_attempts = 0
    max_validation_attempts = 2
    
    while validation_attempts < max_validation_attempts:
        if validation_attempts == 1:
            logger.info("  Validation failed on attempt 1. Re-prompting...")
            prompt += "\n\nOBS: I ditt förra svar misslyckades valideringen. Se till att 'text' är minst 30 tecken, och att 'text_span' (om sådan finns) är en EXAKT, case-sensitive sub-sträng av 'text' och minst 5 tecken lång."

        # Proactive sleep to avoid free-tier rate limits (5 RPM for 2.5-flash)
        time.sleep(15)
        
        try:
            data = provider.generate_json(
                prompt=prompt,
                system_prompt=system_instruction,
            )
        except LLMProviderError as e:
            logger.error(f"  Provider error: {e}")
            if "429" in str(e):
                logger.info("  Rate limit hit (429). Sleeping for 60 seconds before retrying...")
                time.sleep(60)
                continue # Retry without consuming a validation attempt
            validation_attempts += 1
            continue
            
        validation_attempts += 1
            
        # Basic schema validation
        if not isinstance(data, dict) or "text" not in data or "expected_findings" not in data:
            logger.warning("  Missing required keys in JSON.")
            continue
            
        text = data["text"]
        findings = data["expected_findings"]
        
        # Validate text length
        if len(text) < 30:
            logger.warning(f"  Text is too short ({len(text)} chars).")
            continue
            
        # Validate and fix spans
        valid_spans = True
        for finding in findings:
            text_span = finding.get("text_span")
            if not text_span:
                valid_spans = False
                break
                
            if len(text_span) < 5:
                logger.warning(f"  text_span is too short ({len(text_span)} chars).")
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
    parser = argparse.ArgumentParser(description="Generate synthetic dataset candidates (FAS A2).")
    parser.add_argument("--output", required=True, help="Path to output JSON file.")
    parser.add_argument("--model", default="gemini-2.5-flash", help="Model to use (default: gemini-2.5-flash).")
    parser.add_argument("--target-per-category", type=int, default=6, help="Target count per positive category.")
    parser.add_argument("--negative-controls", type=int, default=12, help="Target count for negative controls.")
    parser.add_argument("--temperature", type=float, default=0.7, help="Temperature for generation.")
    args = parser.parse_args()
    
    logger.info(f"Starting generation with model {args.model}")
    
    # Read annotation guidelines and check git status
    guidelines_path = project_root / "docs" / "annotation_guidelines.md"
    if not guidelines_path.exists():
        logger.error(f"Guidelines file not found at {guidelines_path}")
        sys.exit(1)
        
    guidelines_commit = check_guidelines_status(guidelines_path)
    
    with open(guidelines_path, "r", encoding="utf-8") as f:
        guidelines_md = f.read()
        
    general_principles = extract_guideline_section(guidelines_md, "5")
    
    # Parse .env if it exists (without adding dotenv dependency)
    env_file = project_root / ".env"
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    if key.strip() not in os.environ:
                        os.environ[key.strip()] = val.strip()
                        
    # Instantiate provider
    try:
        # Override the environment variable LLM_PROVIDER if the model starts with 'gemini'
        # to ensure get_llm_provider fetches the right one if not explicitly set.
        if args.model.startswith("gemini"):
            os.environ["LLM_PROVIDER"] = "gemini"
        
        provider = get_llm_provider(model_name=args.model)
        # Override temperature for generation
        provider._temperature = args.temperature
    except Exception as e:
        logger.error(f"Failed to instantiate LLM provider: {e}")
        sys.exit(1)
        
    candidates = []
    category_counts = {cat.value: 0 for cat in TARGET_CATEGORIES}
    dropped_count = 0
    negative_count = 0
    
    # Generate positive candidates
    for cat in TARGET_CATEGORIES:
        logger.info(f"Generating positive candidates for {cat.value}...")
        section_id = get_category_section_id(cat.value)
        cat_guidelines = extract_guideline_section(guidelines_md, section_id)
        full_context = f"{cat_guidelines}\n\n{general_principles}"
        
        for i in range(args.target_per_category):
            logger.info(f"  Candidate {i+1}/{args.target_per_category}")
            candidate = generate_candidate(provider, cat.value, is_negative=False, guidelines_context=full_context)
            if candidate:
                candidates.append(candidate)
                category_counts[cat.value] += 1
            else:
                dropped_count += 1
                
    # Generate negative candidates
    logger.info("Generating negative controls...")
    for i in range(args.negative_controls):
        logger.info(f"  Negative Candidate {i+1}/{args.negative_controls}")
        candidate = generate_candidate(provider, None, is_negative=True)
        if candidate:
            candidates.append(candidate)
            negative_count += 1
        else:
            dropped_count += 1
            
    total_generated = sum(category_counts.values()) + negative_count
    target_total = (len(TARGET_CATEGORIES) * args.target_per_category) + args.negative_controls
    
    logger.info("=" * 40)
    logger.info("GENERATION COMPLETE")
    logger.info("=" * 40)
    logger.info(f"Target: {target_total}, Generated: {total_generated}, Dropped: {dropped_count}")
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
            "negative_controls": negative_count,
            "dropped": dropped_count
        },
        "guideline_reference": {
            "path": "docs/annotation_guidelines.md",
            "git_commit": guidelines_commit,
            "generated_at": datetime.datetime.now().isoformat()
        }
    }
    
    meta_path = output_path.parent / ".candidates_metadata.json"
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    logger.info(f"Wrote metadata to {meta_path}")


if __name__ == "__main__":
    main()
