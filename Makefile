.PHONY: check
check:
	poetry run pre-commit run --all-files
