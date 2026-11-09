#!/bin/bash -l
# Run the baseline on one GPU node. Submit from the repository root, with your own partition and account:
#   sbatch --partition=<gpu partition> --account=<account> slurm/run_baseline.sbatch [subset] [models] [run_id] [conditions]
# Defaults: subset core, models "instruct thinking", run id <date>_<subset>_<job id>, all conditions.
#SBATCH --job-name=omnitalk-qwen3-omni
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --gpus=2
#SBATCH --cpus-per-task=32
#SBATCH --time=02:00:00
#SBATCH --output=logs/%x-%j.out

set -uo pipefail
cd "${SLURM_SUBMIT_DIR:?submit this script with sbatch from the repository root}"
source slurm/site.env

SUBSET="${1:-core}"
MODELS="${2:-instruct thinking}"
RUN_ID="${3:-$(date +%Y%m%d)_${SUBSET}_${SLURM_JOB_ID}}"
CONDITIONS="${4:-}"
OUT="outputs/${RUN_ID}"
mkdir -p "$OUT"
EXTRA=()
if [ -n "$CONDITIONS" ]; then
  EXTRA+=(--conditions "$CONDITIONS")
fi

date
nvidia-smi --query-gpu=name,memory.total --format=csv
"$OMNITALK_PYTHON" scripts/verify_clips.py || exit 2
for model in $MODELS; do
  "$OMNITALK_PYTHON" -u scripts/run_baseline.py --model "$model" --subset "$SUBSET" --output-dir "$OUT" "${EXTRA[@]}"
  status=$?
  echo "model $model exit $status"
  date
  if [ "$status" -ne 0 ]; then
    echo "stopping the job: $model did not finish"
    exit "$status"
  fi
done
"$OMNITALK_PYTHON" scripts/score_run.py --run "$OUT"
