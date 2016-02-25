# mailmerge
A simple, command line mail merge tool.

Andrew DeOrio <awdeorio@umich.edu><br>
http://andrewdeorio.com<br>
2016

# Quickstart
`mailmerge` will guide you through the process.  Don't worry, it won't send real emails by default.
```
$ pip install mailmerge
$ mailmerge
```

# Example
This example will walk you through the steps for creating a template email, and database.  Then, it will show how to test it before sending real emails.

### Create a sample template email and database.
```
$ mailmerge --sample
```

### Edit the template email message `mailmerge_template.txt`
Take note that `TO`, `SUBJECT`, and `FROM` fields are required.  The remainder is the body of the message.  Use `{{ }}` to indicate customized parameters that will be read from the database.  For example, `{{email}}` will be filled in from the `email` column of `mailmerge_database.csv`.
```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, {{name}},

Your number is {{number}}.
```

### Edit the database `mailmerge_database.csv`
Notice that the first line is a header that matches the parameters in the template example, for example, `{{email}}`.

**Pro-tip**: Add yourself as the first recipient.  This is helpful for testing.
```
email,name,number
myself@mydomain.com,"Myself",17
bob@bobdomain.com,"Bob",42
```

### Dry run
First, dry run one email message.  This will fill in the template fields of the first email message and print it to the terminal.
```
$ mailmerge --dry-run --limit 1
>>> message 0
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Myself,

Your number is 17.

>>> sent message 0 DRY RUN
>>> Limit was 1 messages.  To remove the limit, use the --no-limit option.
>>> This was a dry run.  To send messages, use the --no-dry-run option.
```

If this looks correct, try a second dry run, this time with all recipients using the `--no-limit` option.
```
$ mailmerge --dry-run --no-limit
>>> message 0
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Myself,

Your number is 17.

>>> sent message 0 DRY RUN
>>> message 1
TO: bob@bobdomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Bob,

Your number is 42.

>>> sent message 1 DRY RUN
>>> This was a dry run.  To send messages, use the --no-dry-run option.
```

### Send first email
We're being extra careful in this example to avoid sending spam, so next we'll send *only one real email*.  Recall that you added yourself as the first email recipient.
```
$ mailmerge --no-dry-run --limit 1
>>> message 0
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Myself,

Your number is 17.

>>> sent message 0
>>> Limit was 1 messages.  To remove the limit, use the --no-limit option.
```

Now, check your email make sure the message went through.  If everything looks OK, then it's time to send all the messages.

### Send all emails
```
$ mailmerge --no-dry-run --no-limit
>>> message 0
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Myself,

Your number is 17.

>>> sent message 0
>>> message 1
TO: bob@bobdomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Bob,

Your number is 42.

>>> sent message 1
```

### Bounced messages
If there is an error sending email, your system may report that you have mail when you log in.  For example, bounce messages may be in `/var/mail/${USER}`.

# Todo
* Complex example in README.  For example, student progress report.  Reference [jinja2 template engine documentation](http://jinja.pocoo.org/docs/latest/templates/)
* Sanity check `sendmail` executable on start
* `--output` option for log file
* Unit tests
