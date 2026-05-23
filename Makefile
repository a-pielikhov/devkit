PACKAGES = devkit-core devkit-git devkit-net devkit-file devkit-encode

.PHONY: check fmt lint type test dev install

check: fmt lint type test

fmt:
	uv run ruff format --check .

lint:
	uv run ruff check .

type:
	uv run mypy .

test:
	@for pkg in $(PACKAGES); do \
		echo "=== $$pkg ==="; \
		(cd $$pkg && uv run --with pytest pytest -q) || exit 1; \
	done

fix:
	uv run ruff format .
	uv run ruff check --fix .

dev:
	@bash dev.sh

install:
	@echo "→ building wheels…"
	@rm -f dist/*.whl
	uv build --all --out-dir=./dist
	@echo "→ reinstalling via pipx…"
	pipx install dist/devkit_cli-*.whl --force --pip-args="--find-links=$$(pwd)/dist"
	@echo "→ verify: head -3 ~/.local/pipx/venvs/devkit-cli/bin/devkit"
