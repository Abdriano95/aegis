"""Finding dataclass.

A Finding represents a single detected piece of potential personal
data in a text. It carries the GDPR category, the character span
(start, end) and matched text, a confidence score in [0, 1], and the
source (which layer or recognizer produced it). Findings are the
unit of exchange between layers, the aggregator, and the evaluator.
"""
