"""Prediction matcher.

Compares findings predicted by the pipeline against the ground-truth
LabeledFindings at the span level, producing true positives, false
positives, and false negatives that feed into the confusion matrix.
"""
