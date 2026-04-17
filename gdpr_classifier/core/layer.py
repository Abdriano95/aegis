"""Layer protocol."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from .finding import Finding


@runtime_checkable
class Layer(Protocol):
    @property
    def name(self) -> str: ...

    def detect(self, text: str) -> list[Finding]: ...
