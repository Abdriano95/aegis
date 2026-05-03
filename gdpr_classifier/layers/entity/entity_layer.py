"""EntityLayer implementation.

SpaCy-baserad NER-detektion som mappar PRS -> Category.NAMN,
LOC -> Category.ADRESS och ORG -> Category.ORGANISATION. Se
``docs/arkitektur.md`` avsnitt 5 för kategori-mapping och
source-taggar. Modellen ``sv_core_news_lg`` laddas vid konstruktion.
"""

from __future__ import annotations

import spacy

from gdpr_classifier.core import Category, Finding


class EntityLayer:
    def __init__(self, model_name: str = "sv_core_news_lg"):
        self._nlp = spacy.load(model_name)
        self._label_map = {
            "PRS": (Category.NAMN, "entity.spacy_PRS"),
            "LOC": (Category.ADRESS, "entity.spacy_LOC"),
            "ORG": (Category.ORGANISATION, "entity.spacy_ORG"),
        }

    @property
    def name(self) -> str:
        return "entity"

    def detect(self, text: str) -> list[Finding]:
        findings: list[Finding] = []
        doc = self._nlp(text)
        for ent in doc.ents:
            if ent.label_ not in self._label_map:
                continue
            if ent.text.strip().isdigit():
                continue
            if "@" in ent.text:
                continue
            # A lone first name without a surname is not reliably a personal data finding.
            if ent.label_ == "PRS" and len(ent.text.split()) < 2:
                continue
            category, source = self._label_map[ent.label_]
            findings.append(Finding(
                category=category,
                start=ent.start_char,
                end=ent.end_char,
                text_span=ent.text,
                confidence=0.8,
                source=source,
                metadata={"ner_label": ent.label_},
            ))
        return findings
