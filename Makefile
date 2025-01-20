VENV_PATH = $(VENV_ROOT)/tatenmitdaten/packages/monitor

venv:
	rm -rf $(VENV_PATH)
	uv venv $(VENV_PATH) --python 3.12
	ln -sfn $(VENV_PATH) venv
	. venv/bin/activate && uv pip install setuptools

install:
	. venv/bin/activate && uv pip install -e .[dev]

setup: venv install

check:
	venv/bin/flake8 src/monitor --ignore=E501
	venv/bin/mypy src/monitor --check-untyped-defs --python-executable venv/bin/python


.PHONY: setup venv install check