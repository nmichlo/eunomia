FORCE:

install-requirements: FORCE
	python3 -m pip install -U pip
	python3 -m pip install -U twine
	python3 -m pip install -U -r docs/requirements.txt
	python3 -m pip install -U -r requirements-test.txt
	python3 -m pip install -U -r requirements.txt

clean: FORCE
	rm -rf ./dist/
	rm -rf ./build/
	rm -rf ./eunomia.egg-info/
	rm -rf ./.pytest_cache/
	rm -rf ./.coverage

test:
	python3 -m pytest --cov=eunomia tests/

build:
	python3 setup.py sdist bdist_wheel

publish-test: clean build
	python3 -m twine upload --repository testpypi dist/*

publish: clean build
	python3 -m twine upload dist/*
