all: fly-in.py

install: all
	python3 -m pip install --update pyglet

run: all
	python3 fly-in.py

debug: all
	python3 -m pdb fly-in.py

clean: all
	rm -rf utils/__pycache__ .mypy_cache

lint: all
	python3 -m flake8 fly-in.py utils/parsing.py utils/pathfinder.py utils/setup.py utils/visualizer.py utils/__init__.py
	python3 -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs fly-in.py utils/parsing.py utils/pathfinder.py utils/setup.py utils/visualizer.py utils/__init__.py

.PHONY: all install run debug clean lint
