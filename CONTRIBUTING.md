Contributing to Mailmerge
=========================

## Install development environment
Set up a development virtual environment.
```console
$ python3 -m venv env
$ source env/bin/activate
$ pip install --editable .[dev]
```

A `mailmerge` entry point script is installed in your virtual environment.
```console
$ which mailmerge
/Users/awdeorio/src/mailmerge/env/bin/mailmerge
```

### Python2 development environment
Mailmerge is tested to work in both Python 2 and Python 3.  Set up a Python 2 virtual environment.
```console
$ virtualenv -p python2 env2
$ source env2/bin/activate
$ pip install -e .[dev]
```

## Testing and code quality
Run unit tests
```console
$ pytest
```

Measure unit test case coverage
```console
$ pytest --cov ./mailmerge
```

Test code style
```console
$ pycodestyle mailmerge tests setup.py
$ pydocstyle mailmerge tests setup.py
$ pylint mailmerge tests setup.py
$ check-manifest
```

Test Python 2 and Python 3 compatibility.  This will automatically create virtual environments and run all style and functional tests in each environment.  Use `pyenv` to provide different versions of Python.
```console
$ eval "$(pyenv init -)"
$ tox
```
