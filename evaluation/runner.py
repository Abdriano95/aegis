"""Evaluation runner.

Executes the pipeline on the test dataset and returns an evaluation report.
"""

from __future__ import annotations

from typing import Any

from evaluation.confusion_matrix import ConfusionMatrix
from evaluation.dataset.labeled_text import LabeledText
from evaluation.matcher import match
from evaluation.metrics import f1, precision, recall
from evaluation.report import DimensionStats, MechanismStats, Report, RunMetrics, SampleResult
from gdpr_classifier.core.category import Category
from gdpr_classifier.core.classification import DataClass, Identifiability


def _calc_metrics(tp: int, fp: int, fn: int) -> RunMetrics:
    return RunMetrics(
        tp=tp,
        fp=fp,
        fn=fn,
        recall=recall(tp=tp, fn=fn),
        precision=precision(tp=tp, fp=fp),
        f1=f1(tp=tp, fp=fp, fn=fn),
    )


def run_evaluation(pipeline: Any, dataset: list[LabeledText]) -> Report:
    """Runs the full evaluation flow over the dataset."""
    cm = ConfusionMatrix()
    samples: list[SampleResult] = []
    mech_article9: int = 0
    mech_bypass: int = 0
    mech_mechanism3: int = 0
    mech_low: int = 0
    mech_none: int = 0
    dim_id_none: int = 0
    dim_id_low: int = 0
    dim_id_medium: int = 0
    dim_id_high: int = 0
    dim_dc_none: int = 0
    dim_dc_ordinary: int = 0
    dim_dc_special: int = 0
    dim_dc_criminal: int = 0

    for item in dataset:
        classification = pipeline.classify(item.text)
        match classification.mechanism_used:
            case "article9":
                mech_article9 += 1
            case "bypass":
                mech_bypass += 1
            case "mechanism3":
                mech_mechanism3 += 1
            case "low":
                mech_low += 1
            case "none" | None:
                mech_none += 1
            case _:
                mech_none += 1 # Count any unexpected value as "none"

        match getattr(classification, "identifiability", Identifiability.NONE):
            case Identifiability.LOW:
                dim_id_low += 1
            case Identifiability.MEDIUM:
                dim_id_medium += 1
            case Identifiability.HIGH:
                dim_id_high += 1
            case Identifiability.NONE | None:
                dim_id_none += 1
            case _:
                dim_id_none += 1  # Count any unexpected value as NONE

        match getattr(classification, "data_class", DataClass.NONE):
            case DataClass.ORDINARY:
                dim_dc_ordinary += 1
            case DataClass.SPECIAL:
                dim_dc_special += 1
            case DataClass.CRIMINAL:
                dim_dc_criminal += 1
            case DataClass.NONE | None:
                dim_dc_none += 1
            case _:
                dim_dc_none += 1  # Count any unexpected value as NONE

        match_result = match(classification.findings, item.expected_findings)
        cm.add_match_result(match_result)
        samples.append(
            SampleResult(
                text=item.text,
                false_positives=list(match_result.false_positives),
                false_negatives=list(match_result.false_negatives),
            )
        )

    # Compute Total Metrics
    t_tp, t_fp, t_fn = cm.get_total_stats()
    total_metrics = _calc_metrics(t_tp, t_fp, t_fn)

    # Compute Per Category
    per_category: dict[Category, RunMetrics] = {}
    categories = set(list(cm.category_tp.keys()) + list(cm.category_fp.keys()) + list(cm.category_fn.keys()))
    for cat in categories:
        c_tp, c_fp, c_fn = cm.get_category_stats(cat)
        per_category[cat] = _calc_metrics(c_tp, c_fp, c_fn)

    # Compute Per Layer
    per_layer: dict[str, RunMetrics] = {}
    layers = set(list(cm.layer_tp.keys()) + list(cm.layer_fp.keys()))
    for layer in layers:
        l_tp, l_fp, l_fn = cm.get_layer_stats(layer)
        per_layer[layer] = _calc_metrics(l_tp, l_fp, l_fn)

    return Report(
        total=total_metrics,
        per_category=per_category,
        per_layer=per_layer,
        samples=samples,
        per_mechanism=MechanismStats(
            high_via_article9=mech_article9,
            medium_via_bypass=mech_bypass,
            medium_via_mechanism3=mech_mechanism3,
            low_count=mech_low,
            none_count=mech_none,
        ),
        per_dimension=DimensionStats(
            identifiability_none=dim_id_none,
            identifiability_low=dim_id_low,
            identifiability_medium=dim_id_medium,
            identifiability_high=dim_id_high,
            data_class_none=dim_dc_none,
            data_class_ordinary=dim_dc_ordinary,
            data_class_special=dim_dc_special,
            data_class_criminal=dim_dc_criminal,
        ),
    )
