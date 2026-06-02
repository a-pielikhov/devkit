PACKAGES   = devkit-core devkit-git devkit-net devkit-file devkit-encode
VENV       = .venv
DEVKIT     = $(VENV)/bin/devkit
DEV_IMAGE  = devkit-dev
DEV_VENV   = devkit-dev-venv

.PHONY: check fmt lint type test fix dev dev-clean run init install

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

# Run the dev version of devkit without entering a shell.
# Usage: make run ARGS="git list-merged"
run:
	$(DEVKIT) $(ARGS)

# Launch an isolated dev shell inside Docker where the dev devkit shadows the
# pipx-installed binary. Edits to devkit-*/src/ are live without rebuild.
# Requires Docker (https://docs.docker.com/get-docker/) and a TTY.
dev:
	@test -t 0 || { printf 'make dev requires a TTY.\nFor one-off commands use: make run ARGS="<command>"\n'; exit 1; }
	@command -v docker >/dev/null 2>&1 || { printf 'make dev requires Docker.\nInstall: https://docs.docker.com/get-docker/\n'; exit 1; }
	@docker image inspect $(DEV_IMAGE) >/dev/null 2>&1 \
		|| { printf '→ building dev image (first time only)…\n'; docker build -t $(DEV_IMAGE) -f Dockerfile.dev .; }
	@printf '\n  devkit dev shell  ·  docker\n  edits to devkit-*/src/ are live\n  type exit or Ctrl+D to leave\n\n'
	@docker run -it --rm \
		-v "$(CURDIR):/workspace" \
		-v $(DEV_VENV):/workspace/.venv \
		-w /workspace \
		-e TERM \
		$(DEV_IMAGE) \
		bash -c 'uv sync --quiet && export PATH="/workspace/.venv/bin:$$PATH" VIRTUAL_ENV="/workspace/.venv" && devkit completion regenerate >/dev/null 2>&1 && exec zsh'

# Remove the dev Docker image and its venv volume (run before rebuilding).
dev-clean:
	@docker rmi $(DEV_IMAGE) 2>/dev/null && echo "→ image removed" || echo "→ image not found"
	@docker volume rm $(DEV_VENV) 2>/dev/null && echo "→ venv volume removed" || echo "→ venv volume not found"

# One-time dev environment setup after cloning.
# Run once: make init
init:
	uv sync --quiet
	uv run pre-commit install

install:
	@echo "→ building wheels…"
	@rm -f dist/*.whl
	uv build --all --out-dir=./dist
	@echo "→ reinstalling via pipx…"
	pipx install dist/devkit_cli-*.whl --force --pip-args="--find-links=$$(pwd)/dist"
	@echo "→ verify: head -3 ~/.local/pipx/venvs/devkit-cli/bin/devkit"
