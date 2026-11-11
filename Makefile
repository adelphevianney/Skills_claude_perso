PYTHON ?= python3

.PHONY: install lint typecheck test gate validate check package clean

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

typecheck:
	$(PYTHON) -m mypy tools tests

test:
	$(PYTHON) -m pytest

gate:
	$(PYTHON) -m tools.quality_gate tools skills

validate:
	$(PYTHON) -m tools.validate_skills skills

## Tout ce que la CI vérifie, dans le même ordre
check: lint typecheck validate test gate

package:
	@test -n "$(SKILL)" || (echo "Usage : make package SKILL=<nom>" && exit 1)
	$(PYTHON) -m tools.package_skill skills/$(SKILL) --output dist

clean:
	rm -rf dist .coverage coverage.xml htmlcov .pytest_cache .mypy_cache .ruff_cache quality-report.json
