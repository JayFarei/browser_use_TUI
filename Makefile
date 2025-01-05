.PHONY: venv run clean

VENV_DIR = .venv
PYTHON = $(VENV_DIR)/bin/python
PIP = $(VENV_DIR)/bin/pip

venv:
	@echo "Setting up virtual environment..."
	@python3 -m venv $(VENV_DIR) || python -m venv $(VENV_DIR)
	@$(PIP) install --upgrade pip -q
	@echo "Installing dependencies..."
	@$(PIP) install -r requirements.txt -q --progress-bar on

run: venv
	@$(PYTHON) agent.py

clean:
	@rm -rf $(VENV_DIR)

.DEFAULT_GOAL := run 