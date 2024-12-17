ifndef SOURCE_FILES
	export SOURCE_FILES:=ahs
endif
ifndef TEST_FILES
	export TEST_FILES:=tests
endif


.PHONY: docs lint test format

format:
	poetry run ruff format ${SOURCE_FILES} ${TEST_FILES}
	poetry run ruff check --fix-only --exit-zero ${SOURCE_FILES} ${TEST_FILES}

lint:
	poetry run ruff check ${SOURCE_FILES} ${TEST_FILES}
	poetry run mypy ${SOURCE_FILES} ${TEST_FILES}

