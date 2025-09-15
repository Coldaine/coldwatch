#!/usr/bin/env sh
set -eu

echo "Setting up dev tools with uv..."
uv pip install -e .[dev]
uvx pre-commit install

echo "Running hooks once on the whole repo..."
uvx pre-commit run --all-files || true

echo "\nDone. Useful commands:\n  make check   # run hooks\n  make lint    # ruff --fix\n  make format  # black\n"

