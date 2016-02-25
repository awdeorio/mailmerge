# mailmerge
A simple, command line mail merge tool.

Andrew DeOrio <awdeorio@umich.edu><br>
http://andrewdeorio.com<br>

`mailmerge` uses plain text files and the powerful [jinja2 template engine documentation](http://jinja.pocoo.org/docs/latest/templates/).  It sends messages using the `sendmail` utility.

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

# A more complicated example
This example will send progress reports to students.  The template uses some more of the advanced features of the [jinja2 template engine documentation](http://jinja.pocoo.org/docs/latest/templates/) to customize messages to students.

**progress_report_template.txt**
```
TO: {{email}}
SUBJECT: EECS 280 Mid-semester Progress Report
FROM: My Self <myself@mydomain.com>

Dear {{name}},

This email contains our record of your grades EECS 280, as well as an estimated letter grade.

Project 1: {{p1}}
Project 2: {{p2}}
Project 3: {{p3}}
Midterm exam: {{midterm}}

At this time, your estimated letter grade is {{grade}}.

{% if grade == "C-" -%}
I am concerned that if the current trend in your scores continues, you will be on the border of the pass/fail line.

I have a few suggestions for the rest of the semester.  First, it is absolutely imperative that you turn in all assignments.  Attend lecture and discussion sections.  Get started early on the programming assignments and ask for help.  Finally, plan a strategy to help you prepare well for the final exam.

The good news is that we have completed about half of the course grade, so there is an opportunity to fix this problem.  The other professors and I are happy to discuss strategies together during office hours.
{% elif grade in ["D+", "D", "D-", "E", "F"] -%}
I am writing because I am concerned about your grade in EECS 280.  My concern is that if the current trend in your scores continues, you will not pass the course.

If you plan to continue in the course, I urge you to see your instructor in office hours to discuss a plan for the remainder of the semester.  Otherwise, if you plan to drop the course, please see your academic advisor.
{% endif -%}
```

**progress_report_database.csv**
Again, we'll use the best practice of making yourself the first recipient, which is helpful for testing.
```
email,name,p1,p2,p3,midterm,grade
myself@mydomain.com,"My Self",100,100,100,100,A+
borderline@fixme.com,"Borderline Name",50,50,50,50,C-
failing@fixme.com,"Failing Name",0,0,0,0,F
```

**Dry run one message**<br>
Test one message without actually sending any email.
```
$ mailmerge --template progress_report_template.txt --database progress_report_database.csv 
>>> message 0
TO: myself@mydomain.com
SUBJECT: EECS 280 Mid-semester Progress Report
FROM: My Self <myself@mydomain.com>

Dear My Self,

This email contains our record of your grades EECS 280, as well as an estimated letter grade.

Project 1: 100
Project 2: 100
Project 3: 100
Midterm exam: 100

At this time, your estimated letter grade is A+.


>>> sent message 0 DRY RUN
>>> Limit was 1 messages.  To remove the limit, use the --no-limit option.
>>> This was a dry run.  To send messages, use the --no-dry-run option.
```

# Todo
* Sanity check `sendmail` executable on start
* `--output` option for log file
* Unit tests
