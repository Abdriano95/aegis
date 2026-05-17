"""Unit tests for the prompt loader module.

Tests cover:
- Loading a valid YAML prompt file
- Validation error on missing required field
- Load error on invalid YAML syntax
- Version resolution with "latest"
- Deterministic prompt assembly
- Validation error on invalid examples type
- Validation error on example with missing keys
- Loading with only required fields (optional fields omitted)
"""

from unittest.mock import MagicMock

import pytest

from gdpr_classifier.layers.article9 import Article9Layer
from gdpr_classifier.layers.llm.provider import LLMProvider
from gdpr_classifier.prompts.loader import (
    Prompt,
    PromptLoadError,
    PromptValidationError,
    load_prompt,
    resolve_prompt_version,
)


# --- Helpers ---

_VALID_YAML = """\
metadata:
  version: "v1"
  created: "2026-04-30"
  author: "test"
  layer: "article9"
  source_citations:
    - "Liu et al. (2023)"
  notes: "Test prompt."

system_prompt: |
  You are a GDPR classifier.

task_instruction: |
  Detect article 9 categories.

context: |
  GDPR article 9 covers special categories.

reasoning_instructions: |
  Think step by step.

examples:
  - input: "Patient has diabetes."
    output: '{"category": "halsodata"}'
    rationale: "Health data is article 9."
  - input: "Meeting at 14:00."
    output: '{"category": null}'
    rationale: "No sensitive data."

output_format: |
  Return JSON with category field.
"""

_MINIMAL_YAML = """\
metadata:
  version: "v1"
  created: "2026-04-30"
  author: "test"
  layer: "test"

system_prompt: |
  You are a classifier.

task_instruction: |
  Classify text.

output_format: |
  Return JSON.
"""

_MISSING_TASK_YAML = """\
metadata:
  version: "v1"
  created: "2026-04-30"
  author: "test"
  layer: "test"

system_prompt: |
  You are a classifier.

output_format: |
  Return JSON.
"""


def _write_prompt(tmp_path, layer, version, content):
    """Write a YAML prompt file under tmp_path/layer/version.yaml."""
    layer_dir = tmp_path / layer
    layer_dir.mkdir(parents=True, exist_ok=True)
    yaml_path = layer_dir / f"{version}.yaml"
    yaml_path.write_text(content, encoding="utf-8")
    return yaml_path


# --- Core test cases ---


class TestLoadValidPrompt:
    """Test that a valid YAML file loads correctly."""

    def test_returns_prompt_dataclass(self, tmp_path):
        _write_prompt(tmp_path, "article9", "v1", _VALID_YAML)
        prompt = load_prompt("article9", base_dir=tmp_path)

        assert isinstance(prompt, Prompt)

    def test_metadata_preserved(self, tmp_path):
        _write_prompt(tmp_path, "article9", "v1", _VALID_YAML)
        prompt = load_prompt("article9", base_dir=tmp_path)

        assert prompt.metadata["version"] == "v1"
        assert prompt.metadata["layer"] == "article9"
        assert "Liu et al. (2023)" in prompt.metadata["source_citations"]

    def test_system_prompt_extracted(self, tmp_path):
        _write_prompt(tmp_path, "article9", "v1", _VALID_YAML)
        prompt = load_prompt("article9", base_dir=tmp_path)

        assert "GDPR classifier" in prompt.system_prompt

    def test_assembled_prompt_contains_all_parts(self, tmp_path):
        _write_prompt(tmp_path, "article9", "v1", _VALID_YAML)
        prompt = load_prompt("article9", base_dir=tmp_path)

        assert "Detect article 9 categories" in prompt.assembled_prompt
        assert "special categories" in prompt.assembled_prompt
        assert "Think step by step" in prompt.assembled_prompt
        assert "--- Examples ---" in prompt.assembled_prompt
        assert "Return JSON with category field" in prompt.assembled_prompt

    def test_system_prompt_not_in_assembled(self, tmp_path):
        """system_prompt is separate, not included in assembled_prompt."""
        _write_prompt(tmp_path, "article9", "v1", _VALID_YAML)
        prompt = load_prompt("article9", base_dir=tmp_path)

        assert "You are a GDPR classifier" not in prompt.assembled_prompt


class TestMissingRequiredField:
    """Test that missing required fields raise PromptValidationError."""

    def test_missing_task_instruction(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _MISSING_TASK_YAML)

        with pytest.raises(PromptValidationError, match="task_instruction"):
            load_prompt("test_layer", base_dir=tmp_path)


class TestInvalidYaml:
    """Test that invalid YAML raises PromptLoadError."""

    def test_malformed_yaml(self, tmp_path):
        bad_yaml = "metadata:\n  version: [unterminated"
        _write_prompt(tmp_path, "test_layer", "v1", bad_yaml)

        with pytest.raises(PromptLoadError, match="YAML parse error"):
            load_prompt("test_layer", base_dir=tmp_path)

    def test_nonexistent_layer(self, tmp_path):
        with pytest.raises(PromptLoadError, match="Layer directory not found"):
            load_prompt("nonexistent", base_dir=tmp_path)

    def test_nonexistent_version(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _VALID_YAML)

        with pytest.raises(PromptLoadError, match="not found"):
            load_prompt("test_layer", version="v99", base_dir=tmp_path)


class TestLatestVersionResolution:
    """Test that version='latest' selects the highest vN.yaml."""

    def test_selects_highest_version(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _VALID_YAML)

        v2_yaml = _VALID_YAML.replace('version: "v1"', 'version: "v2"')
        _write_prompt(tmp_path, "test_layer", "v2", v2_yaml)

        prompt = load_prompt("test_layer", version="latest", base_dir=tmp_path)
        assert prompt.metadata["version"] == "v2"

    def test_ignores_non_matching_files(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _VALID_YAML)
        # Write a non-matching file that should be ignored
        (tmp_path / "test_layer" / "README.md").write_text("docs")

        prompt = load_prompt("test_layer", version="latest", base_dir=tmp_path)
        assert prompt.metadata["version"] == "v1"

    def test_numeric_not_lexicographic(self, tmp_path):
        """v10 > v9, not v9 > v10 (lexicographic)."""
        _write_prompt(tmp_path, "test_layer", "v9", _VALID_YAML.replace(
            'version: "v1"', 'version: "v9"'
        ))
        _write_prompt(tmp_path, "test_layer", "v10", _VALID_YAML.replace(
            'version: "v1"', 'version: "v10"'
        ))

        prompt = load_prompt("test_layer", version="latest", base_dir=tmp_path)
        assert prompt.metadata["version"] == "v10"


class TestDeterministicAssembly:
    """Test that the same input always produces the same assembled_prompt."""

    def test_same_input_same_output(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _VALID_YAML)

        prompt1 = load_prompt("test_layer", base_dir=tmp_path)
        prompt2 = load_prompt("test_layer", base_dir=tmp_path)

        assert prompt1.assembled_prompt == prompt2.assembled_prompt

    def test_assembly_order(self, tmp_path):
        """Verify task comes before context, context before examples, etc."""
        _write_prompt(tmp_path, "test_layer", "v1", _VALID_YAML)
        prompt = load_prompt("test_layer", base_dir=tmp_path)

        text = prompt.assembled_prompt
        task_pos = text.index("Detect article 9 categories")
        context_pos = text.index("special categories")
        reasoning_pos = text.index("Think step by step")
        examples_pos = text.index("--- Examples ---")
        output_pos = text.index("Return JSON with category field")

        assert task_pos < context_pos < reasoning_pos < examples_pos < output_pos


# --- Additional validation tests ---


class TestExamplesValidation:
    """Test validation of the examples field."""

    def test_examples_wrong_type(self, tmp_path):
        bad_yaml = _VALID_YAML.replace(
            'examples:\n  - input: "Patient has diabetes."',
            'examples: "not a list"',
        ).replace(
            '    output: \'{"category": "halsodata"}\'\n'
            '    rationale: "Health data is article 9."\n'
            '  - input: "Meeting at 14:00."\n'
            '    output: \'{"category": null}\'\n'
            '    rationale: "No sensitive data."',
            "",
        )
        _write_prompt(tmp_path, "test_layer", "v1", bad_yaml)

        with pytest.raises(PromptValidationError, match="examples.*list"):
            load_prompt("test_layer", base_dir=tmp_path)

    def test_example_missing_keys(self, tmp_path):
        bad_yaml = _MINIMAL_YAML + '\nexamples:\n  - input: "text"\n    output: "json"\n'
        _write_prompt(tmp_path, "test_layer", "v1", bad_yaml)

        with pytest.raises(PromptValidationError, match="missing keys"):
            load_prompt("test_layer", base_dir=tmp_path)


class TestOptionalFieldsOmitted:
    """Test that prompts with only required fields load correctly."""

    def test_minimal_prompt(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _MINIMAL_YAML)
        prompt = load_prompt("test_layer", base_dir=tmp_path)

        assert "Classify text" in prompt.assembled_prompt
        assert "Return JSON" in prompt.assembled_prompt
        # No examples or reasoning in minimal prompt
        assert "--- Examples ---" not in prompt.assembled_prompt


# --- Version-pinning: status filtering for "latest" ---


def _versioned(version: str, *, experimental: bool = False) -> str:
    """Return _VALID_YAML re-stamped to ``version``, optionally experimental."""
    meta = f'version: "{version}"'
    if experimental:
        meta += '\n  status: "experimental"'
    return _VALID_YAML.replace('version: "v1"', meta)


class TestStatusFiltering:
    """version='latest' must skip prompts marked status: experimental."""

    def test_latest_skips_experimental(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _versioned("v1"))
        _write_prompt(
            tmp_path, "test_layer", "v2", _versioned("v2", experimental=True)
        )

        prompt = load_prompt("test_layer", version="latest", base_dir=tmp_path)
        assert prompt.metadata["version"] == "v1"
        assert (
            resolve_prompt_version("test_layer", "latest", base_dir=tmp_path)
            == "v1"
        )

    def test_missing_status_treated_as_active(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _versioned("v1"))
        _write_prompt(tmp_path, "test_layer", "v2", _versioned("v2"))

        assert (
            resolve_prompt_version("test_layer", "latest", base_dir=tmp_path)
            == "v2"
        )

    def test_explicit_version_ignores_status(self, tmp_path):
        _write_prompt(tmp_path, "test_layer", "v1", _versioned("v1"))
        _write_prompt(
            tmp_path, "test_layer", "v2", _versioned("v2", experimental=True)
        )

        prompt = load_prompt("test_layer", version="v2", base_dir=tmp_path)
        assert prompt.metadata["version"] == "v2"
        assert (
            resolve_prompt_version("test_layer", "v2", base_dir=tmp_path) == "v2"
        )

    def test_malformed_candidate_skipped(self, tmp_path, caplog):
        _write_prompt(tmp_path, "test_layer", "v1", _versioned("v1"))
        _write_prompt(
            tmp_path, "test_layer", "v2", "metadata:\n  version: [unterminated"
        )

        with caplog.at_level("WARNING"):
            version = resolve_prompt_version(
                "test_layer", "latest", base_dir=tmp_path
            )
        assert version == "v1"
        assert any("v2.yaml" in r.message for r in caplog.records)

    def test_all_experimental_raises(self, tmp_path):
        _write_prompt(
            tmp_path, "test_layer", "v1", _versioned("v1", experimental=True)
        )
        _write_prompt(
            tmp_path, "test_layer", "v2", _versioned("v2", experimental=True)
        )

        with pytest.raises(PromptLoadError, match="non-experimental"):
            resolve_prompt_version("test_layer", "latest", base_dir=tmp_path)


class TestArticle9PromptVersionPinning:
    """Article9Layer.prompt_version must resolve away experimental article9 v6.

    Runs against the real prompts directory. The provider is never invoked by
    the property (resolution is a pure filesystem read).
    """

    def test_latest_resolves_to_v5(self):
        layer = Article9Layer(MagicMock(spec=LLMProvider))
        assert layer.prompt_version == "v5"

    def test_explicit_v6_is_preserved(self):
        layer = Article9Layer(MagicMock(spec=LLMProvider), prompt_version="v6")
        assert layer.prompt_version == "v6"

    def test_resolver_helper_on_real_article9(self):
        assert resolve_prompt_version("article9", "latest") == "v5"
