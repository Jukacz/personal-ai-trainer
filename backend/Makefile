PYTHON ?= python
VENV_PYTHON ?=  .venv/bin/python
DOTENVX ?= dotenvx
ENV_FILE ?= .env

.PHONY: run run-dotenvx run-uvicorn run-uvicorn-dotenvx seed-mock seed-mock-dotenvx

run:
	$(PYTHON) run_api.py

run-dotenvx:
	$(DOTENVX) run -f $(ENV_FILE) -- $(PYTHON) run_api.py

run-uvicorn:
	uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

run-uvicorn-dotenvx:
	$(DOTENVX) run -f $(ENV_FILE) -- uvicorn api.app:app --reload --host 0.0.0.0 --port 8000

seed-mock:
	$(VENV_PYTHON) scripts/seed_mock_data_for_users.py --execute

seed-mock-dotenvx:
	$(DOTENVX) run -f $(ENV_FILE) -- $(VENV_PYTHON) scripts/seed_mock_data_for_users.py --execute
