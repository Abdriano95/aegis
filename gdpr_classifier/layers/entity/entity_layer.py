"""EntityLayer implementation.

Stub for iteration 1. The EntityLayer will later wrap a named entity
recognition model (SpaCy or KB-BERT) to produce findings for person
names, locations, and organizations (see ``docs/arkitektur.md`` section
5). For now, ``detect`` returns an empty list so the pipeline can
instantiate and run all three layers without error already in
iteration 1.
"""

from __future__ import annotations

from gdpr_classifier.core import Finding


class EntityLayer:
    @property
    def name(self) -> str:
        return "entity"

    def detect(self, text: str) -> list[Finding]:
        return []
