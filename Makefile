.PHONY: test reproduce validate

CONFIG := configs/experiment_neurips2026.yaml

test:
	pytest -q

reproduce:
	python3 scripts/04_run_filters.py --config $(CONFIG)
	python3 scripts/05_run_attacks.py --config $(CONFIG)
	python3 scripts/06_run_utility_eval.py --config $(CONFIG)
	python3 scripts/07_aggregate_results.py --config $(CONFIG)
	python3 scripts/10_build_paper_assets.py --config $(CONFIG)

validate:
	python3 scripts/11_validate_submission_readiness.py --config $(CONFIG)
