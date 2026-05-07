# PrivateMap-Bench NeurIPS 2026 Code Release

This folder is the sanitized executable code package for reproducing the
PrivateMap-Bench NeurIPS 2026 processed-artifact benchmark results. It is meant
to be used with the matching dataset package:

- `dataset_neurips2026_sanitized/`
- `dataset_neurips2026_sanitized.zip`

The code package does not include raw ROS bags, processed data, paper drafts,
Git history, local build files, or machine-specific caches.

## Contents

- `src/privatemap/`: benchmark Python package.
- `scripts/`: offline filtering, privacy attack, utility, aggregation, figure,
  table, and validation scripts.
- `configs/`: NeurIPS 2026 synchronized benchmark configs.
- `tests/`: unit tests and small synthetic fixtures.
- `ros2/`: optional TurtleBot4 helper scripts for future data collection.
- `docs/`: schema, release policy, reproduction notes, and dataset/benchmark
  cards.

## Dataset Synchronization

The NeurIPS config uses repository-relative paths such as
`data/processed/env1_A_mapping/map.yaml`. To reproduce the released results,
place the dataset release contents under this code folder so the code root has a
`data/` directory:

```bash
unzip dataset_neurips2026_sanitized.zip
cp -a dataset_neurips2026_sanitized/data ./data
```

After that, the expected layout is:

```text
code_neurips2026_sanitized/
  configs/experiment_neurips2026.yaml
  data/processed/
  data/filtered/
  data/results/
  data/paper_assets/
  data/annotations/
  scripts/
  src/
```

Do not rename the `env*` run folders or the `data/` subdirectories. The config,
dataset, result CSVs, and paper values all use the same run IDs.

The dataset also contains five legacy processed `run_*` folders retained for
audit and future extension. Those legacy folders are not referenced by
`configs/experiment_neurips2026.yaml` and are not included in the NeurIPS 2026
reported aggregate results, figures, or tables.

## Environment

Using `venv`:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

Using conda:

```bash
conda env create -f environment.yml
conda activate privatemap-bench
pip install -e .
```

## Reproduce Results

From the code release root, after placing the dataset `data/` directory:

```bash
python3 scripts/04_run_filters.py --config configs/experiment_neurips2026.yaml
python3 scripts/05_run_attacks.py --config configs/experiment_neurips2026.yaml
python3 scripts/06_run_utility_eval.py --config configs/experiment_neurips2026.yaml
python3 scripts/07_aggregate_results.py --config configs/experiment_neurips2026.yaml
python3 scripts/10_build_paper_assets.py --config configs/experiment_neurips2026.yaml
```

Expected reported scale:

- 15 NeurIPS runs across 3 layout variants.
- 300 logical filtered artifacts.
- 2310 privacy result rows.
- 5580 utility result rows.
- 1126 aggregate result rows.

## Quick Verification

```bash
pytest -q
python3 scripts/11_validate_submission_readiness.py --config configs/experiment_neurips2026.yaml
```

The validation script checks processed-artifact paths and generated results. It
may report paper-template checks only when the full paper tree is present; the
paper tree is intentionally excluded from this code release.
