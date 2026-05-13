"""Evaluation runner.

Executes the pipeline on the test dataset and returns an evaluation report.
"""

from __future__ import annotations

from typing import Any

from evaluation.confusion_matrix import ConfusionMatrix
from evaluation.dataset.labeled_text import LabeledText
from evaluation.matcher import match
from evaluation.metrics import f1, precision, recall
from evaluation.report import DimensionStats, Report, RunMetrics, SampleResult
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
    dim_id_none: int = 0
    dim_id_indirect: int = 0
    dim_id_direct: int = 0
    dim_dc_none: int = 0
    dim_dc_special: int = 0
    dim_dc_criminal: int = 0

    for item in dataset:
        classification = pipeline.classify(item.text)

        match getattr(classification, "identifiability", Identifiability.NONE):
            case Identifiability.INDIRECT:
                dim_id_indirect += 1
            case Identifiability.DIRECT:
                dim_id_direct += 1
            case Identifiability.NONE | None:
                dim_id_none += 1
            case _:
                dim_id_none += 1  # Count any unexpected value as NONE

        match getattr(classification, "data_class", DataClass.NONE):
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
        per_dimension=DimensionStats(
            identifiability_none=dim_id_none,
            identifiability_indirect=dim_id_indirect,
            identifiability_direct=dim_id_direct,
            data_class_none=dim_dc_none,
            data_class_special=dim_dc_special,
            data_class_criminal=dim_dc_criminal,
        ),
    )
