Contributing to Mailmerge
=========================

## Install development environment
Set up a development virtual environment.
```console
$ python3 -m venv env
$ source env/bin/activate
$ pip install --editable .[dev,test]
```

A `mailmerge` entry point script is installed in your virtual environment.
```console
$ which mailmerge
/Users/awdeorio/src/mailmerge/env/bin/mailmerge
```

## Testing and code quality
Run unit tests
```console
$ pytest
```

Measure unit test case coverage
```console
$ pytest --cov ./mailmerge --cov-report term-missing
```

Test code style
```console
$ pycodestyle mailmerge tests setup.py
$ pydocstyle mailmerge tests setup.py
$ pylint mailmerge tests setup.py
$ check-manifest
```

Run linters and tests in a clean environment.  This will automatically create a temporary virtual environment.
```console
$ tox
```
