#!/bin/bash
set -u
SUMMARY="i6_logs/phase1.summary.txt"
echo "=== Fas 1 screening (1 körning per konfig), start $(date) ===" > "$SUMMARY"

# 16 valid configs (med, high, evidence)
configs=(
  "0.5 0.75 1" "0.5 0.75 2"
  "0.5 0.85 1" "0.5 0.85 2"
  "0.5 0.95 1" "0.5 0.95 2"
  "0.65 0.75 1" "0.65 0.75 2"
  "0.65 0.85 1" "0.65 0.85 2"
  "0.65 0.95 1" "0.65 0.95 2"
  "0.8 0.85 1" "0.8 0.85 2"
  "0.8 0.95 1" "0.8 0.95 2"
)

for cfg in "${configs[@]}"; do
  read -r M H E <<<"$cfg"
  TAG="m${M}_h${H}_e${E}"
  LOG="i6_logs/phase1_${TAG}.log"
  echo "" >> "$SUMMARY"
  echo "=== Config M=$M H=$H E=$E   ($(date)) ===" >> "$SUMMARY"
  py run_evaluation.py --medium-threshold "$M" --high-confidence-bypass "$H" --min-evidence-count "$E" > "$LOG" 2>&1
  echo "exit=$?" >> "$SUMMARY"
  grep -A 5 "Total Metrics" "$LOG" | head -7 >> "$SUMMARY"
  grep "Mekanism 3" "$LOG" >> "$SUMMARY"
  grep -A 3 "Per Dimension" "$LOG" | head -5 >> "$SUMMARY"
done

echo "" >> "$SUMMARY"
echo "=== Fas 1 complete $(date) ===" >> "$SUMMARY"
