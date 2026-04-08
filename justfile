default: zip

UV_RUN := "uv run --"

# Format using Ruff
ruff *files:
	{{UV_RUN}} ruff format --force-exclude {{files}}

# Check formatting and lints using Ruff
ruff-check *files:
	{{UV_RUN}} ruff check --force-exclude --fix {{files}}

# Check type hints using mypy
mypy *files:
	{{UV_RUN}} mypy {{files}}

# Run pytest
pytest:
  {{UV_RUN}} python -m  pytest

# Run pytest+ts tests
test: pytest ts-test

# Clean up build files
clean:
	rm -rf build/

link:
   ln -s "/Users/vincent/code/yujing-anki/src" "/Users/vincent/Library/Application Support/Anki2/addons21/yujing"

