ifndef FILES
	export FILES:=ahs tests examples
endif


.PHONY: docs lint test format

format:
	poetry run ruff format ${FILES}
	poetry run ruff check --fix-only --exit-zero ${FILES}

lint:
	poetry run ruff check ${FILES}
	poetry run mypy ${FILES}


test:
	poetry run pytest tests