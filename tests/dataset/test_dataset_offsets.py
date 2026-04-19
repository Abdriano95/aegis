import json
import pathlib

DATASET_PATH = pathlib.Path(__file__).parents[2] / "tests" / "data" / "iteration_1" / "test_dataset.json"


def test_all_expected_findings_have_valid_offsets() -> None:
    data = json.loads(DATASET_PATH.read_text(encoding="utf-8"))
    for item in data:
        text = item["text"]
        for finding in item.get("expected_findings", []):
            start = finding["start"]
            end = finding["end"]
            text_span = finding["text_span"]
            assert 0 <= start <= end <= len(text), (
                f"Offset out of bounds: start={start}, end={end}, len={len(text)!r} in {text!r}"
            )
            assert text[start:end] == text_span, (
                f"Span mismatch: text[{start}:{end}]={text[start:end]!r} != {text_span!r} in {text!r}"
            )
