venv_path = $(VENV_PATH)/tatenmitdaten/packages/monitor

venv:
	rm -rf $(venv_path)
	python3.12 -m venv $(venv_path)
	ln -sfn $(venv_path) venv
	$(venv_path)/bin/python -m pip install --upgrade pip-tools pip setuptools

install:
	$(venv_path)/bin/python -m pip install -e .[dev]

setup: venv install

check:
	$(venv_path)/bin/flake8 monitor --ignore=E501
	$(venv_path)/bin/mypy monitor --check-untyped-defs --python-executable $(venv_path)/bin/python


.PHONY: setup venv install check