Mailmerge
=========

[![CI main](https://github.com/awdeorio/mailmerge/workflows/CI/badge.svg?branch=develop)](https://github.com/awdeorio/mailmerge/actions?query=branch%3Adevelop)
[![codecov](https://codecov.io/gh/awdeorio/mailmerge/branch/develop/graph/badge.svg)](https://codecov.io/gh/awdeorio/mailmerge)
[![PyPI](https://img.shields.io/pypi/v/mailmerge.svg)](https://pypi.org/project/mailmerge/)

A simple, command line mail merge tool.

`mailmerge` uses plain text files and the [jinja2 template engine](http://jinja.pocoo.org/docs/latest/templates/).

**Table of Contents**
- [Quickstart](#quickstart)
- [Install](#install)
- [Example](#example)
- [Advanced template example](#advanced-template-example)
- [HTML formatting](#html-formatting)
- [Markdown formatting](#markdown-formatting)
- [Attachments](#attachments)
- [Inline Image Attachments](#inline-image-attachments)
- [Contributing](#contributing)
- [Acknowledgements](#acknowledgements)

## Quickstart
```console
$ pip install mailmerge
$ mailmerge
```

`mailmerge` will guide you through the process.  Don't worry, it won't send real emails by default.

## Install
System-wide install.
```console
$ pip install mailmerge
```

System-wide install requiring administrator privileges.  Use this if you get a `Permission denied` error.
```console
$ sudo pip install mailmerge
```

Fedora package install.
```console
$ sudo dnf install python3-mailmerge
```

## Example
This example will walk you through the steps for creating a template email, database and STMP server configuration.  Then, it will show how to test it before sending real emails.

### Create a sample template email, database, and config
```console
$ mailmerge --sample
Created sample template email "mailmerge_template.txt"
Created sample database "mailmerge_database.csv"
Created sample config file "mailmerge_server.conf"

Edit these files, then run mailmerge again.
```

### Edit the SMTP server config `mailmerge_server.conf`
The defaults are set up for GMail.  Be sure to change your username.  If you use 2-factor authentication, create an [app password](https://support.google.com/accounts/answer/185833?hl=en) first.  Other configuration examples are in the comments of `mailmerge_server.conf`.

**Pro-tip:** SSH or VPN into your network first.  Running mailmerge from the same network as the SMTP server can help you avoid spam filters and server throttling.  This tip doesn't apply to Gmail.
```
[smtp_server]
host = smtp.gmail.com
port = 465
security = SSL/TLS
username = YOUR_USERNAME_HERE
```

### Edit the template email message `mailmerge_template.txt`
The `TO`, `SUBJECT`, and `FROM` fields are required.  The remainder is the body of the message.  Use `{{ }}` to indicate customized parameters that will be read from the database.  For example, `{{email}}` will be filled in from the `email` column of `mailmerge_database.csv`.
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
First, dry run one email message (`mailmerge` defaults).  This will fill in the template fields of the first email message and print it to the terminal.
```console
$ mailmerge
>>> message 1
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Thu, 19 Dec 2019 19:49:11 -0000

Hi, Myself,

Your number is 17.
>>> sent message 1
>>> Limit was 1 message.  To remove the limit, use the --no-limit option.
>>> This was a dry run.  To send messages, use the --no-dry-run option.
```

If this looks correct, try a second dry run, this time with all recipients using the `--no-limit` option.
```console
$ mailmerge --no-limit
>>> message 1
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Thu, 19 Dec 2019 19:49:33 -0000

Hi, Myself,

Your number is 17.
>>> sent message 1
>>> message 2
TO: bob@bobdomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Thu, 19 Dec 2019 19:49:33 -0000

Hi, Bob,

Your number is 42.
>>> sent message 2
>>> This was a dry run.  To send messages, use the --no-dry-run option.
```

### Send first email
We're being extra careful in this example to avoid sending spam, so next we'll send *only one real email* (`mailmerge` default).  Recall that you added yourself as the first email recipient.
```console
$ mailmerge --no-dry-run
>>> message 1
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Thu, 19 Dec 2019 19:50:24 -0000

Hi, Myself,

Your number is 17.
>>> sent message 1
>>> Limit was 1 message.  To remove the limit, use the --no-limit option.
```

You may have to type your email password when prompted. (If you use GMail with 2-factor authentication, don't forget to use the [app password](https://support.google.com/accounts/answer/185833?hl=en) you created while [setting up the SMTP server config](#edit-the-smtp-server-config-mailmerge_serverconf).)

Now, check your email and make sure the message went through.  If everything looks OK, then it's time to send all the messages.

### Send all emails
```console
$ mailmerge --no-dry-run --no-limit
>>> message 1
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Thu, 19 Dec 2019 19:51:01 -0000

Hi, Myself,

Your number is 17.
>>> sent message 1
>>> message 2
TO: bob@bobdomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: text/plain; charset="us-ascii"
Content-Transfer-Encoding: 7bit
Date: Thu, 19 Dec 2019 19:51:01 -0000

Hi, Bob,

Your number is 42.
>>> sent message 2
```

## Advanced template example
This example will send progress reports to students.  The template uses more of the advanced features of the [jinja2 template engine documentation](http://jinja.pocoo.org/docs/latest/templates/) to customize messages to students.

#### Template `mailmerge_template.txt`
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

#### Database `mailmerge_database.csv`
Again, we'll use the best practice of making yourself the first recipient, which is helpful for testing.
```
email,name,p1,p2,p3,midterm,grade
myself@mydomain.com,"My Self",100,100,100,100,A+
borderline@fixme.com,"Borderline Name",50,50,50,50,C-
failing@fixme.com,"Failing Name",0,0,0,0,F
```

## HTML formatting
Mailmerge supports HTML formatting.

### HTML only
This example will use HTML to format an email.  Add `Content-Type: text/html` just under the email headers, then begin your message with `<html>`.

#### Template `mailmerge_template.txt`
```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
Content-Type: text/html

<html>
<body>

<p>Hi, {{name}},</p>

<p>Your number is {{number}}.</p>

<p>Sent by <a href="https://github.com/awdeorio/mailmerge">mailmerge</a></p>

</body>
</html>
```


### HTML and plain text
This example shows how to provide both HTML and plain text versions in the same message.  A user's mail reader can select either one.

#### Template `mailmerge_template.txt`
```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary"

This is a MIME-encoded message. If you are seeing this, your mail
reader is old.

--boundary
Content-Type: text/plain; charset=us-ascii

Hi, {{name}},

Your number is {{number}}.

Sent by mailmerge https://github.com/awdeorio/mailmerge

--boundary
Content-Type: text/html; charset=us-ascii

<html>
<body>

<p>Hi, {{name}},</p>

<p>Your number is {{number}}.</p>

<p>Sent by <a href="https://github.com/awdeorio/mailmerge">mailmerge</a></p>

</body>
</html>
```


## Markdown formatting
Mailmerge supports [Markdown](https://daringfireball.net/projects/markdown/syntax) formatting by including the custom custom header `Content-Type: text/markdown` in the message. Mailmerge will render the markdown to HTML, then include both HTML and plain text versions in a multiplart message. A recipient's mail reader can then select either format.

### Template `mailmerge_template.txt`
```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
CONTENT-TYPE: text/markdown

You can add:

- Emphasis, aka italics, with *asterisks*.
- Strong emphasis, aka bold, with **asterisks**.
- Combined emphasis with **asterisks and _underscores_**.
- Unordered lists like this one.
- Ordered lists with numbers:
    1. Item 1
    2. Item 2
- Preformatted text with `backticks`.
- How about some [hyperlinks](http://bit.ly/eecs485-wn19-p6)?

# This is a heading.
## And another heading.

Here's an image not attached with the email:
![python logo not attached](http://pluspng.com/img-png/python-logo-png-open-2000.png)
```

## Attachments
This example shows how to add attachments with a special `ATTACHMENT` header.

#### Template `mailmerge_template.txt`
```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
ATTACHMENT: file1.docx
ATTACHMENT: ../file2.pdf
ATTACHMENT: /z/shared/{{name}}_submission.txt

Hi, {{name}},

This email contains three attachments.
Pro-tip: Use Jinja to customize the attachments based on your database!
```

Dry run to verify attachment files exist. If an attachment filename includes a template, it's a good idea to dry run with the `--no-limit` flag.
```console
$ mailmerge
>>> message 1
TO: myself@mydomain.com
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>

Hi, Myself,

This email contains three attachments.
Pro-tip: Use Jinja to customize the attachments based on your database!

>>> attached /Users/awdeorio/Documents/test/file1.docx
>>> attached /Users/awdeorio/Documents/file2.pdf
>>> attached /z/shared/Myself_submission.txt
>>> sent message 1
>>> This was a dry run.  To send messages, use the --no-dry-run option.
```

## Inline Image Attachments

This example shows how to add inline-image-attachments so that the images are rendered directly in the email body. You **must** add the inline-image as an attachment before referencing it in the body.

#### HTML Example: Template `mailmerge_template.txt`

```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
Content-Type: text/html
ATTACHMENT: image.jpg
ATTACHMENT: second/image.jpg

<html>
<body>

<p>Hi, {{name}},</p>

<img alt="Sample image" src="image.jpg" />

The second image: <img alt="second" src="second/image.jpg">

<p>Sent by <a href="https://github.com/awdeorio/mailmerge">mailmerge</a></p>

</body>
</html>
```

#### Markdown Example: Template `mailmerge_template.txt`
```
TO: {{email}}
SUBJECT: Testing mailmerge
FROM: My Self <myself@mydomain.com>
ATTACHMENT: image.jpg
CONTENT-TYPE: text/markdown

Hi, {{name}},

![image alt-description](image.jpg)
```

## Contributing
Contributions from the community are welcome! Check out the [guide for contributing](CONTRIBUTING.md).


## Acknowledgements
Mailmerge is written by Andrew DeOrio <awdeorio@umich.edu>, [http://andrewdeorio.com](http://andrewdeorio.com).  Sesh Sadasivam (@seshrs) contributed many features and bug fixes.
