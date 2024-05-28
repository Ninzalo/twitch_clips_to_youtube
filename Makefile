.PHONY: install
install:
	@poetry run pre-commit install

.PHONY: check
check:
	@poetry run pre-commit run --all-files
