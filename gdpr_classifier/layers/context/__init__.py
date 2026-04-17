"""Context-based detection layer.

Holds the ContextLayer, which will perform contextual analysis to
classify sensitive data (GDPR Article 9) that cannot be reliably
detected via patterns or NER alone. Stub for iteration 1.
"""

from __future__ import annotations

from .context_layer import ContextLayer

__all__ = ["ContextLayer"]
