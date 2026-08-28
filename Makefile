# Prérequis : uv (https://docs.astral.sh/uv/)
UV ?= uv

setup:
	$(UV) sync --locked --all-extras

test:             ## 28 tests : oracles He-Litterman/Idzorek + propriétés algébriques + moteur (3 s, sans réseau)
	$(UV) run pytest

lint:
	$(UV) run ruff check src tests
