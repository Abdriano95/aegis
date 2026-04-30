"""Prompt loader for the GDPR classifier.

Loads structured prompt definitions from versioned YAML files and assembles
them into a deterministic prompt string suitable for LLM consumption.

Assembly order follows Reynolds & McDonell (2021) component-structured
prompts: task_instruction → context → reasoning_instructions → examples →
output_format. system_prompt is kept separate for use as the LLMProvider
system_prompt parameter.

Security: yaml.safe_load is used exclusively (never yaml.load) to prevent
arbitrary code execution from untrusted YAML.

YAML Schema
-----------
Required fields: metadata, system_prompt, task_instruction, output_format
Optional fields: context, reasoning_instructions, examples

When present, ``examples`` must be a list of dicts, each containing the
keys ``input``, ``output``, and ``rationale``.

References:
    Reynolds & McDonell (2021): component-structured prompts
    Brown et al. (2020): few-shot prompting with input-output examples
    Wei et al. (2022): chain-of-thought reasoning instructions
    Karras et al. (2025): structured JSON output format
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

import yaml


# --- Exceptions ---


class PromptError(Exception):
    """Base class for prompt-related errors."""


class PromptLoadError(PromptError):
    """File not found, IO error, or YAML parse failure."""


class PromptValidationError(PromptError):
    """Missing required field, wrong type, or invalid example schema."""


# --- Data model ---


@dataclass(frozen=True)
class Prompt:
    """Loaded and assembled prompt ready for LLM consumption.

    Attributes:
        metadata: The metadata dict from the YAML file header.
        system_prompt: Role instruction, sent via LLMProvider's
            system_prompt parameter.
        assembled_prompt: Deterministic concatenation of
            task_instruction, context (if present),
            reasoning_instructions (if present), examples (if present),
            and output_format, separated by double newlines.
    """

    metadata: dict
    system_prompt: str
    assembled_prompt: str


# --- Constants ---

_REQUIRED_FIELDS = ("metadata", "system_prompt", "task_instruction", "output_format")
_OPTIONAL_FIELDS = ("context", "reasoning_instructions", "examples")
_EXAMPLE_KEYS = {"input", "output", "rationale"}
_PROMPTS_DIR = Path(__file__).parent
_VERSION_PATTERN = re.compile(r"^v(\d+)\.yaml$")


# --- Public API ---


def load_prompt(
    layer: str,
    version: str = "latest",
    base_dir: Path | None = None,
) -> Prompt:
    """Load and assemble a prompt from a versioned YAML file.

    Args:
        layer: Layer name (e.g. ``"article9"``, ``"combination"``).
        version: Version string (``"v1"``, ``"v2"``, ...) or ``"latest"``.
            When ``"latest"`` is used, the file with the highest vN number
            in the layer directory is selected.
        base_dir: Base directory containing layer subdirectories.
            Defaults to the package's ``prompts/`` directory. Primarily
            used for testing via dependency injection.

    Returns:
        A :class:`Prompt` with metadata, system_prompt, and the
        deterministically assembled prompt string.

    Raises:
        PromptLoadError: If the file cannot be found, the layer directory
            does not exist, or YAML parsing fails.
        PromptValidationError: If required fields are missing, fields have
            wrong types, or examples have invalid structure.
    """
    prompts_dir = base_dir if base_dir is not None else _PROMPTS_DIR
    resolved_prompts_dir = prompts_dir.resolve()

    if "/" in layer or "\\" in layer or ".." in layer or Path(layer).is_absolute():
        raise PromptLoadError(f"Invalid layer: {layer}")

    layer_dir = (prompts_dir / layer).resolve()

    if not layer_dir.is_relative_to(resolved_prompts_dir):
        raise PromptLoadError(f"Path traversal detected for layer: {layer}")

    if not layer_dir.is_dir():
        raise PromptLoadError(f"Layer directory not found: {layer_dir}")

    yaml_path = _resolve_version(layer_dir, version, resolved_prompts_dir)
    raw = _load_yaml(yaml_path)
    _validate(raw, yaml_path)

    return Prompt(
        metadata=raw["metadata"],
        system_prompt=raw["system_prompt"].strip(),
        assembled_prompt=_assemble(raw),
    )


# --- Internal helpers ---


def _resolve_version(layer_dir: Path, version: str, prompts_root: Path) -> Path:
    """Resolve version string to a YAML file path.

    For ``"latest"``: scan directory for files matching ``vN.yaml``,
    extract N as integer, return file with the highest N.
    For explicit version (e.g. ``"v1"``): return ``layer_dir / "v1.yaml"``.
    """
    if "/" in version or "\\" in version or ".." in version or Path(version).is_absolute():
        raise PromptLoadError(f"Invalid version: {version}")

    if version == "latest":
        candidates: list[tuple[int, Path]] = []
        for entry in layer_dir.iterdir():
            match = _VERSION_PATTERN.match(entry.name)
            if match:
                resolved_entry = entry.resolve()
                if resolved_entry.is_relative_to(prompts_root):
                    candidates.append((int(match.group(1)), resolved_entry))
        if not candidates:
            raise PromptLoadError(
                f"No valid versioned prompt files (vN.yaml) found in {layer_dir}"
            )
        candidates.sort(key=lambda x: x[0])
        return candidates[-1][1]

    # Explicit version
    path = (layer_dir / f"{version}.yaml").resolve()

    if not path.is_relative_to(prompts_root):
        raise PromptLoadError(f"Path traversal detected for version: {version}")

    if not path.exists():
        raise PromptLoadError(f"Prompt file not found: {path}")
    return path


def _load_yaml(path: Path) -> dict:
    """Load and parse a YAML file using yaml.safe_load."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as exc:
        raise PromptLoadError(f"YAML parse error in {path}: {exc}") from exc
    except OSError as exc:
        raise PromptLoadError(f"Cannot read {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise PromptLoadError(
            f"Expected YAML mapping at top level in {path}, got {type(data).__name__}"
        )
    return data


def _validate(data: dict, path: Path) -> None:
    """Validate prompt data against the schema.

    Checks:
    - All required fields are present and are strings (except metadata → dict).
    - Optional fields, if present, have correct types.
    - ``examples``, if present, is a list of dicts each containing
      ``input``, ``output``, and ``rationale`` keys.
    """
    # Required fields
    for field in _REQUIRED_FIELDS:
        if field not in data:
            raise PromptValidationError(
                f"Missing required field '{field}' in {path}"
            )

    # Type checks for required fields
    if not isinstance(data["metadata"], dict):
        raise PromptValidationError(
            f"Field 'metadata' must be a dict in {path}, "
            f"got {type(data['metadata']).__name__}"
        )
    for field in ("system_prompt", "task_instruction", "output_format"):
        if not isinstance(data[field], str):
            raise PromptValidationError(
                f"Field '{field}' must be a string in {path}, "
                f"got {type(data[field]).__name__}"
            )

    # Optional string fields
    for field in ("context", "reasoning_instructions"):
        if field in data and not isinstance(data[field], str):
            raise PromptValidationError(
                f"Optional field '{field}' must be a string in {path}, "
                f"got {type(data[field]).__name__}"
            )

    # Optional examples field
    if "examples" in data:
        if not isinstance(data["examples"], list):
            raise PromptValidationError(
                f"Field 'examples' must be a list in {path}, "
                f"got {type(data['examples']).__name__}"
            )
        for i, example in enumerate(data["examples"]):
            if not isinstance(example, dict):
                raise PromptValidationError(
                    f"Example {i} must be a dict in {path}, "
                    f"got {type(example).__name__}"
                )
            missing_keys = _EXAMPLE_KEYS - set(example.keys())
            if missing_keys:
                raise PromptValidationError(
                    f"Example {i} is missing keys {missing_keys} in {path}"
                )


def _assemble(data: dict) -> str:
    """Assemble the prompt string in deterministic order.

    Order (Reynolds & McDonell, 2021):
    1. task_instruction (required)
    2. context (optional)
    3. reasoning_instructions (optional)
    4. examples (optional, rendered per Brown et al., 2020)
    5. output_format (required)

    Components are separated by double newlines.
    """
    parts: list[str] = [data["task_instruction"].strip()]

    if "context" in data and data["context"]:
        parts.append(data["context"].strip())

    if "reasoning_instructions" in data and data["reasoning_instructions"]:
        parts.append(data["reasoning_instructions"].strip())

    if "examples" in data and data["examples"]:
        parts.append(_render_examples(data["examples"]))

    parts.append(data["output_format"].strip())

    return "\n\n".join(parts)


def _render_examples(examples: list[dict]) -> str:
    """Render examples in Brown et al. (2020) few-shot format.

    Format::

        --- Examples ---
        Example 1:
        Input: <text>
        Output: <text>
        Rationale: <text>

        Example 2:
        Input: <text>
        Output: <text>
        Rationale: <text>
        --- End Examples ---
    """
    lines: list[str] = ["--- Examples ---"]
    for i, ex in enumerate(examples, start=1):
        if i > 1:
            lines.append("")  # blank line between examples
        lines.append(f"Example {i}:")
        lines.append(f"Input: {ex['input']}")
        lines.append(f"Output: {ex['output']}")
        lines.append(f"Rationale: {ex['rationale']}")
    lines.append("--- End Examples ---")
    return "\n".join(lines)
