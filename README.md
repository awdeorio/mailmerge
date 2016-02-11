# mailmerge
A simple, command line mail merge tool.

By Andrew DeOrio

2016

## Quickstart
1. Install libraries
   ````
   pip install -r requirements.txt
   ````

1. Create a sample template email and database.
    ```
    ./mailmerge.py
    ```

1. Edit the template email and database
    ```
    mailmerge_email.txt
    mailmerge_database.csv
    ```

1. Dry run
    ```
    ./mailmerge.py
    ```

1. Send the emails
    ```
    ./mailmerge.py --no-pretend
    ```


## Install
Optionally, use a virtual environment
```
virtualenv venv
. ./venv/bin/activate
```

Install libraries
```
pip install -r requirements.txt
```

# Todo
* `--limit / --no-limit` options
* Remove my email address from sample
* Simple example in README
* Complex example in README (e.g., student grade email with optional warning)
* Make yourself the first recipient
* Sanity check `sendmail` executable
* Step-by-step guide (first limit 1, then no-pretend with self, then no-limit)
* `--database` option
* `--template` option
* `--output` option for log file
* `--sample` option to create sample database and template files
