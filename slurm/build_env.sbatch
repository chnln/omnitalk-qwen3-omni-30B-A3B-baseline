#!/bin/bash -l
# Build the Python environment from requirements.lock.txt. No GPU needed. Submit from the repository root:
#   OMNITALK_VENV=/path/to/venv sbatch --partition=<cpu or build partition> --account=<account> slurm/build_env.sbatch
#SBATCH --job-name=omnitalk-build-env
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=8
#SBATCH --time=00:45:00
#SBATCH --output=logs/%x-%j.out

set -euo pipefail
cd "${SLURM_SUBMIT_DIR:?submit this script with sbatch from the repository root}"
VENV="${OMNITALK_VENV:?set OMNITALK_VENV to the directory of the new virtual environment}"

uv venv --python 3.12 "$VENV"
uv pip install --python "$VENV/bin/python" -r requirements.lock.txt
"$VENV/bin/python" -c "import decord, librosa, qwen_omni_utils, torch, transformers, vllm; print(vllm.__version__, torch.__version__, transformers.__version__)"
