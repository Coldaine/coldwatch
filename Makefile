SHELL := /bin/sh

.PHONY: setup lint format check hooks

setup: ## Install dev tools and git hooks (via uv)
	uv pip install -e .[dev]
	uvx pre-commit install
	@echo "\n✔ Dev tools installed. Try: 'make check'"

hooks: ## Reinstall pre-commit hooks
	uvx pre-commit install

lint: ## Lint (Ruff) with autofix
	uvx ruff check --fix .

format: ## Format (Black)
	uvx black .

check: ## Run pre-commit on all files
	uvx pre-commit run --all-files

help:
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | sed 's/:.*##/: /'

