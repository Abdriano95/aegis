"""Layer protocol.

Defines the Layer protocol that every detection layer (pattern,
entity, context, ...) must implement. A layer exposes a single
``detect(text: str) -> list[Finding]`` method that returns all
findings produced for the given text. The pipeline treats layers
uniformly through this protocol.
"""
