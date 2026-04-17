"""ContextLayer implementation.

Stub for iteration 1 (and iteration 2). The ContextLayer will later
perform contextual analysis - zero-shot classification or a local LLM -
to classify sensitive data (GDPR Article 9) that cannot be reliably
detected via patterns or NER alone (see ``docs/arkitektur.md`` section
6). For now, ``detect`` returns an empty list so the pipeline can
instantiate and run all three layers without error already in
iteration 1.
"""

from __future__ import annotations

from gdpr_classifier.core import Finding


class ContextLayer:
    @property
    def name(self) -> str:
        return "context"

    def detect(self, text: str) -> list[Finding]:
        return []
