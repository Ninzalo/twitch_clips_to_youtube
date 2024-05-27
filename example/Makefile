.PHONY: run
run:
	poetry run python3.12 main.py

.PHONY: stdin-run
stdin-run:
	poetry run python3.12 main.py -c

.PHONY: update
update:
	poetry install
	poetry add git+https://github.com/Ninzalo/twitch_clips_to_youtube.git
