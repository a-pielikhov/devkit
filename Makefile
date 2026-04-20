PACKAGES = devkit-core devkit-git devkit-net devkit-file devkit-encode

.PHONY: check fmt lint type test

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
