"""Probe prompts for Ollama model evaluation (Issue #84).

Contains two categories of probe prompts:
- PROMPTS_CATEGORY_A: JSON output validity (5 prompts, trivial tasks)
- PROMPTS_CATEGORY_B: Swedish language comprehension on Article 9-like tasks
  (9 prompts, mix of positive and negative controls)

These are deliberately simplified compared to production prompts (#70, #72).
They lack few-shot examples, chain-of-thought, and full GDPR context.
The goal is to measure baseline format compliance and classification ability.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProbePrompt:
    """A single probe prompt with expected outcome for model evaluation.

    Attributes:
        id: Unique identifier (e.g. "a1_extract_name", "b3_religion_positive").
        category: "A" (JSON validity) or "B" (Swedish comprehension).
        system_prompt: System-level instruction for the LLM.
        task_prompt: The task description sent as the user prompt.
        text: The input text to analyze.
        expected_json_keys: Set of keys that must be present in the JSON response.
        expected_classification: Expected classification dict for category B,
            None for category A.
    """

    id: str
    category: str
    system_prompt: str
    task_prompt: str
    text: str
    expected_json_keys: set[str]
    expected_classification: dict | None


# ---------------------------------------------------------------------------
# System prompts
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT_A = (
    "Du är en hjälpsam assistent. Svara alltid med giltig JSON."
)

_SYSTEM_PROMPT_B = (
    "Du är en GDPR-expert. Analysera om texten innehåller direkt uttryckta "
    "känsliga personuppgifter enligt GDPR artikel 9 (hälsodata, etniskt "
    "ursprung, politisk åsikt, religiös övertygelse, fackmedlemskap, "
    "biometrisk data, sexuell läggning). Svara med JSON med fälten "
    '"contains_sensitive" (boolean) och "category" (string eller null).'
)

# ---------------------------------------------------------------------------
# Category A: JSON output validity (5 prompts)
# ---------------------------------------------------------------------------

PROMPTS_CATEGORY_A: list[ProbePrompt] = [
    ProbePrompt(
        id="a1_extract_name",
        category="A",
        system_prompt=_SYSTEM_PROMPT_A,
        task_prompt='Extrahera personnamnet ur texten. Returnera JSON med fältet "name".',
        text="Hej, mitt namn är Erik Svensson.",
        expected_json_keys={"name"},
        expected_classification=None,
    ),
    ProbePrompt(
        id="a2_list_places",
        category="A",
        system_prompt=_SYSTEM_PROMPT_A,
        task_prompt='Lista alla platser som nämns i texten. Returnera JSON med fältet "places" (en lista).',
        text="Jag besökte Stockholm, Göteborg och Malmö i somras.",
        expected_json_keys={"places"},
        expected_classification=None,
    ),
    ProbePrompt(
        id="a3_give_category",
        category="A",
        system_prompt=_SYSTEM_PROMPT_A,
        task_prompt='Kategorisera texten. Returnera JSON med fältet "category" (en sträng).',
        text="Idag köpte jag en ny cykel.",
        expected_json_keys={"category"},
        expected_classification=None,
    ),
    ProbePrompt(
        id="a4_count_words",
        category="A",
        system_prompt=_SYSTEM_PROMPT_A,
        task_prompt='Räkna antalet ord i texten. Returnera JSON med fältet "count" (ett heltal).',
        text="Den lilla katten sov på mattan.",
        expected_json_keys={"count"},
        expected_classification=None,
    ),
    ProbePrompt(
        id="a5_extract_date",
        category="A",
        system_prompt=_SYSTEM_PROMPT_A,
        task_prompt='Extrahera datumet ur texten. Returnera JSON med fältet "date".',
        text="Mötet är planerat till den 15 mars 2026.",
        expected_json_keys={"date"},
        expected_classification=None,
    ),
]

# ---------------------------------------------------------------------------
# Category B: Swedish language comprehension, Article 9-like tasks (9 prompts)
# ---------------------------------------------------------------------------

_TASK_PROMPT_B = (
    "Analysera följande text och avgör om den innehåller direkt uttryckta "
    "känsliga personuppgifter enligt GDPR artikel 9. Returnera JSON med "
    '"contains_sensitive" (true/false) och "category" (kategorinamn som '
    'sträng, eller null om ingen känslig uppgift finns).'
)

PROMPTS_CATEGORY_B: list[ProbePrompt] = [
    # --- Positive controls (5) ---
    ProbePrompt(
        id="b1_health_positive",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Patienten diagnostiserades med diabetes typ 2 och ordinerades metformin.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={"contains_sensitive": True, "category": "halsodata"},
    ),
    ProbePrompt(
        id="b2_health_positive2",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Hen har behandlats för depression i tre år och medicinerar med sertralin.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={"contains_sensitive": True, "category": "halsodata"},
    ),
    ProbePrompt(
        id="b3_religion_positive",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Familjen firar Eid och Fatima bär hijab till skolan varje dag.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={
            "contains_sensitive": True,
            "category": "religios_overtygelse",
        },
    ),
    ProbePrompt(
        id="b4_ethnicity_positive",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Ahmed är född i Eritrea och tillhör den tigrinya-talande gruppen.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={
            "contains_sensitive": True,
            "category": "etniskt_ursprung",
        },
    ),
    ProbePrompt(
        id="b5_politics_positive",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Lars är aktiv medlem i Socialdemokraterna och kandiderar till kommunfullmäktige.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={
            "contains_sensitive": True,
            "category": "politisk_asikt",
        },
    ),
    # --- Negative controls (4) ---
    ProbePrompt(
        id="b6_negative_profession",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Anna arbetar som sjuksköterska på Sahlgrenska universitetssjukhuset.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={"contains_sensitive": False, "category": None},
    ),
    ProbePrompt(
        id="b7_negative_meeting",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Nästa styrelsemöte i bostadsrättsföreningen är den 14 april kl 18:00.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={"contains_sensitive": False, "category": None},
    ),
    ProbePrompt(
        id="b8_negative_orgname",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Capio vårdcentral Axess erbjuder drop-in-vaccinering på tisdagar.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={"contains_sensitive": False, "category": None},
    ),
    ProbePrompt(
        id="b9_negative_food",
        category="B",
        system_prompt=_SYSTEM_PROMPT_B,
        task_prompt=_TASK_PROMPT_B,
        text="Vi serverar halal-certifierad lunch i personalmatsalen varje fredag.",
        expected_json_keys={"contains_sensitive", "category"},
        expected_classification={"contains_sensitive": False, "category": None},
    ),
]
