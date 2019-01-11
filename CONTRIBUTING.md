Contributing to Mailmerge
=========================

## Install development environment
Set up a development environment.  This will install a `mailmerge` executable in virtual environment's `PATH` which points to the local python development source code.
```console
$ python3 -m venv env  # or "virtualenv env" for python2
$ source env/bin/activate
$ pip install --editable .[dev]
```

## Testing and code quality
Run unit tests
```console
$ pytest
```

Test code style
```console
$ pycodestyle mailmerge tests setup.py
$ pydocstyle mailmerge tests setup.py
$ pylint --reports=n  mailmerge tests setup.py
```

Test python2/python3 compatibility.  This will automatically create virtual environments and run all style and functional tests in each environment.
```console
$ tox
```
