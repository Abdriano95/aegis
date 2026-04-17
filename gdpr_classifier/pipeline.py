"""Detection pipeline.

Defines the Pipeline, which orchestrates the configured active layers:
it feeds the input text through each layer, collects their findings,
and hands the combined result to the aggregator for merging and
final classification.
"""
