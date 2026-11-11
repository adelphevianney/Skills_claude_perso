PYTHON ?= python3

.PHONY: install lint typecheck test gate validate sonar check package clean

install:
	$(PYTHON) -m pip install -r requirements-dev.txt

lint:
	ruff check .
	ruff format --check .

typecheck:
	$(PYTHON) -m mypy tools tests
	@# Chaque skill est typé séparément : ses scripts s'importent depuis leur propre dossier.
	@for scripts in skills/*/scripts; do \
		skill=$$(dirname "$$scripts"); \
		ls "$$scripts"/*.py >/dev/null 2>&1 || continue; \
		echo "mypy $$skill"; \
		MYPYPATH="$$scripts" $(PYTHON) -m mypy "$$skill" || exit 1; \
	done

test:
	$(PYTHON) -m pytest

gate:
	$(PYTHON) -m tools.quality_gate tools skills

validate:
	$(PYTHON) -m tools.validate_skills skills

## Auto-contrôle : le skill sonar-review analyse le dépôt ; toute issue MINOR ou plus grave échoue
sonar:
	$(PYTHON) skills/sonar-review/scripts/sonar_metrics.py tools skills --json sonar-metrics.json --fail-on MINOR

## Tout ce que la CI vérifie, dans le même ordre
check: lint typecheck validate test gate sonar

package:
	@test -n "$(SKILL)" || (echo "Usage : make package SKILL=<nom>" && exit 1)
	$(PYTHON) -m tools.package_skill skills/$(SKILL) --output dist

clean:
	rm -rf dist .coverage coverage.xml htmlcov .pytest_cache .mypy_cache .ruff_cache quality-report.json sonar-metrics.json
