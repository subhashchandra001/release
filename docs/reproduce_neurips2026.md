# Reproducing the NeurIPS 2026 PrivateMap-Bench Results

Use `configs/experiment_neurips2026.yaml` to reproduce the NeurIPS 2026 benchmark outputs.

## Privacy warning

Raw ROS bags, unreviewed RGB keyframes, and contact sheets are private and must not be committed or publicly released unless explicitly reviewed and cleared.

## Pipeline

Run from the repository root:

```bash
python3 scripts/04_run_filters.py --config configs/experiment_neurips2026.yaml
python3 scripts/05_run_attacks.py --config configs/experiment_neurips2026.yaml
python3 scripts/06_run_utility_eval.py --config configs/experiment_neurips2026.yaml
python3 scripts/07_aggregate_results.py --config configs/experiment_neurips2026.yaml
python3 scripts/10_build_paper_assets.py --config configs/experiment_neurips2026.yaml
```

## Expected outputs

- `data/results/privacy_results.csv`
- `data/results/utility_results.csv`
- `data/results/aggregated_results.csv`
- `data/results/aggregated_results.json`
- figures in `data/paper_assets/figures/`
- tables in `data/paper_assets/tables/`

## Current generated scale

- 15 TurtleBot4 runs
- 3 environment/layout variants
- 300 filtered artifacts
- 2310 privacy result rows
- 5580 utility result rows
- 1126 aggregate result rows

## Legacy processed runs

The dataset release also contains five legacy processed `run_*` folders retained
for audit and future extension. They are not part of
`configs/experiment_neurips2026.yaml` and are not included in the reported
NeurIPS 2026 aggregate results, figures, or tables.

## Validation

```bash
pytest -q
python3 scripts/11_validate_submission_readiness.py --config configs/experiment_neurips2026.yaml --strict
git diff --check
```
