"""Prompt construction infrastructure for the GDPR classifier.

This package provides versioned, research-grounded prompt definitions for the
LLM-based classification layers (Article9Layer and CombinationLayer). Prompts
are stored as YAML files with a structured schema and loaded via
:func:`load_prompt`.

YAML Schema
------------
Each prompt YAML file contains the following fields:

**Required:**
- ``metadata`` (dict): Version, author, citations, and notes.
- ``system_prompt`` (str): Role instruction for the LLM.
- ``task_instruction`` (str): What the layer should detect or assess.
- ``output_format`` (str): Expected JSON response schema.

**Optional:**
- ``context`` (str): Background information and regulatory context.
- ``reasoning_instructions`` (str): Chain-of-thought guidance.
- ``examples`` (list[dict]): Few-shot examples with input/output/rationale.

Assembly Order
--------------
The ``assembled_prompt`` concatenates fields in deterministic order:
task_instruction → context → reasoning_instructions → examples → output_format.
``system_prompt`` is kept separate for the LLMProvider system_prompt parameter.

This order follows Reynolds & McDonell (2021) component-structured prompts:
the model first receives the task, then supporting context, then reasoning
structure, then concrete examples (Brown et al., 2020), and finally the
expected output format (Karras et al., 2025).

References
----------
- Reynolds & McDonell (2021): component-structured prompts
- Brown et al. (2020): few-shot prompting
- Wei et al. (2022): chain-of-thought reasoning
- Karras et al. (2025): structured JSON output
"""

from .loader import (
    Prompt,
    PromptError,
    PromptLoadError,
    PromptValidationError,
    load_prompt,
)

__all__ = [
    "Prompt",
    "PromptError",
    "PromptLoadError",
    "PromptValidationError",
    "load_prompt",
]
