ifndef FILES
	export FILES:=ahs tests examples
endif


.PHONY: docs lint test format

format:
	uv run ruff format ${FILES}
	uv run ruff check --fix-only --exit-zero ${FILES}

lint:
	uv run ruff check ${FILES}
	uv run mypy ${FILES}


test:
	uv run pytest tests