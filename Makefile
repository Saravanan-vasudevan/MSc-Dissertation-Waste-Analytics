.PHONY: setup run clean docker

# Default Python — override with `make run PYTHON=python3.11` if needed
PYTHON ?= python3

setup:
	$(PYTHON) -m venv .venv
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt
	@echo ""
	@echo "Done. Run 'make run' to start the dashboard."

run:
	.venv/bin/streamlit run app/dashboard.py

# Regenerate data/processed/merthyr_recycling_rates.csv from the raw CSVs
processed:
	.venv/bin/python -c "from src.data_loader import write_processed_csv; write_processed_csv()"

# Run all analysis scripts (saves figures to working directory)
analysis:
	.venv/bin/python analysis/model_diagnostics.py
	.venv/bin/python analysis/generate_ssa_figures.py
	.venv/bin/python analysis/generate_acf_pacf_figures.py
	.venv/bin/python analysis/trend_significance_tests.py
	.venv/bin/python analysis/ssa_parameter_grid_search.py

docker:
	docker compose up --build

clean:
	rm -rf .venv __pycache__ app/__pycache__ app/pages/__pycache__
	rm -rf figures/*.png figures/*.jpg
