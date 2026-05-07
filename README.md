# PrivateMap-Bench NeurIPS 2026 Code Release

  This repository contains the anonymized executable code package for reproducing
  the PrivateMap-Bench NeurIPS 2026 processed-artifact benchmark results.

  The benchmark is designed to be used with the matching sanitized dataset release.
  The code repository itself does not include raw ROS bags, paper drafts, Git
  history, local build files, machine-specific caches, or unreviewed image
  artifacts.

  ## Contents

  - `src/privatemap/`: benchmark Python package.
  - `scripts/`: filtering, privacy attack, utility evaluation, aggregation,
    figure, table, export, and validation scripts.
  - `configs/`: synchronized NeurIPS 2026 benchmark configurations.
  - `tests/`: unit tests and small synthetic fixtures.
  - `ros2/`: optional TurtleBot4 helper scripts for future data collection.
  - `docs/`: schema, release policy, reproduction notes, and dataset/benchmark
    cards.

  The main reproduction configuration is:

  ```bash
  configs/experiment_neurips2026.yaml

  ## Dataset Setup

  To reproduce the released results, the repository root must contain a data/
  directory from the matching sanitized dataset release.

  The expected layout is:

  privatemap-bench/
    configs/experiment_neurips2026.yaml
    data/processed/
    data/filtered/
    data/results/
    data/paper_assets/
    data/annotations/
    scripts/
    src/

  Do not rename the env* run folders or any data/ subdirectories. The
  configuration, dataset, result CSVs, generated figures/tables, and reported
  paper values all use the same run IDs.

  The dataset may also contain five legacy processed run_* folders retained for
  audit and future extension. These legacy folders are not referenced by
  configs/experiment_neurips2026.yaml and are not included in the NeurIPS 2026
  reported aggregate results, figures, or tables.

  ## Environment

  Using venv:

  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  pip install -e .

  Using conda:

  conda env create -f environment.yml
  conda activate privatemap-bench
  pip install -e .

  ## Reproduce Results

  From the repository root, after adding the dataset data/ directory:

  python3 scripts/04_run_filters.py --config configs/experiment_neurips2026.yaml
  python3 scripts/05_run_attacks.py --config configs/experiment_neurips2026.yaml
  python3 scripts/06_run_utility_eval.py --config configs/experiment_neurips2026.yaml
  python3 scripts/07_aggregate_results.py --config configs/experiment_neurips2026.yaml
  python3 scripts/10_build_paper_assets.py --config configs/experiment_neurips2026.yaml

  Generated outputs are written to:

  - data/results/privacy_results.csv
  - data/results/utility_results.csv
  - data/results/aggregated_results.csv
  - data/results/aggregated_results.json
  - data/paper_assets/figures/
  - data/paper_assets/tables/

  Expected reported scale:

  - 15 NeurIPS runs across 3 layout variants.
  - 300 logical filtered artifacts.
  - 2310 privacy result rows.
  - 5580 utility result rows.
  - 1126 aggregate result rows.

  ## Quick Verification

  Run the unit tests:

  pytest -q

  Validate the synchronized NeurIPS release package:

  python3 scripts/11_validate_submission_readiness.py --config configs/experiment_neurips2026.yaml

  The validation script checks configured processed-artifact paths, generated
  result files, and generated paper assets. Paper-template checks may only run when
  the full local paper tree is present; the paper tree is intentionally excluded
  from this anonymous code release.

  ## Privacy and Release Policy

  Indoor robot data can expose people, screens, documents, floor plans, routines,
  and other sensitive information. This release is designed to contain only
  reviewed processed artifacts and generated benchmark outputs.

  Do not commit or publish raw ROS bags, unreviewed RGB keyframes, contact sheets,
  raw camera images, private local paths, or identifying metadata.

  See the following documents for release details:

  - docs/data_release_policy.md
  - docs/dataset_card_neurips2026.md
  - docs/benchmark_card_neurips2026.md
  - docs/reproduce_neurips2026.md

  ## Optional Future Data Collection

  The ros2/ helper scripts document the TurtleBot4 collection workflow used by
  the project. Raw data collection is not required to reproduce the NeurIPS 2026
  processed-artifact benchmark results.

  Raw ROS bags and raw camera data must remain outside the public code release.

  ## License

  See LICENSE for repository licensing. External assets, TurtleBot4 software,
  ROS 2 packages, and conference templates may have separate licenses.
