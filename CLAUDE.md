# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Mailmerge is a command-line mail merge tool that uses plain text files and the Jinja2 template engine. It reads a CSV database, renders email templates with Jinja2, and sends personalized emails via SMTP.

## Git Workflow

**IMPORTANT: This project uses a develop/main branching strategy:**

- **`develop`** - Integration branch for all development work
- **`main`** - Stable release branch

**Workflow:**
1. Create feature branches from `develop`: `git checkout develop && git pull && git checkout -b feature-name`
2. Make changes and commit to your feature branch
3. Create pull requests targeting `develop` (not `main`)
4. After review and CI passes, PRs are merged into `develop`
5. Releases are created by merging `develop` into `main`

## Core Architecture

### Main Components

- **`mailmerge/__main__.py`**: CLI entry point using Click framework
  - Parses command-line arguments
  - Orchestrates the mail merge workflow
  - Handles dry-run vs. real sending modes
  - Implements rate limiting and message limiting

- **`mailmerge/template_message.py`**: Email template rendering
  - `TemplateMessage` class combines email.message with Jinja2 templates
  - Transforms markdown to HTML (via `markdown` library)
  - Handles attachments and inline images with Content-ID headers
  - Manages multipart message structure (text/plain, text/html, attachments)
  - Character encoding detection (ASCII vs UTF-8)

- **`mailmerge/sendmail_client.py`**: SMTP client for sending emails
  - `SendmailClient` class reads server configuration
  - Supports multiple security modes: SSL/TLS, STARTTLS, PLAIN, XOAUTH, and no security
  - Implements rate limiting with timestamps
  - Password prompting for authenticated connections

- **`mailmerge/exceptions.py`**: Custom exceptions
  - `MailmergeError`: Base exception for all mailmerge errors
  - `MailmergeRateLimitError`: Raised when rate limit is exceeded

### Data Flow

1. CLI reads three input files: template (`.txt`), database (`.csv`), config (`.conf`)
2. CSV database is parsed row-by-row using `csv.DictReader` with auto-detected dialect
3. For each row, `TemplateMessage.render()` renders the template with Jinja2 context
4. Message transformations are applied:
   - Character encoding detection
   - Recipient extraction from TO/CC/BCC headers
   - Markdown-to-HTML conversion (if Content-Type: text/markdown)
   - Attachment processing with Content-ID generation
   - Inline image reference transformation in HTML
5. `SendmailClient.sendmail()` sends via SMTP, respecting rate limits

### Key Design Patterns

- **Progressive Enhancement**: Messages start as simple text and become multipart only when needed (markdown, attachments)
- **Path Resolution**: Attachment paths are relative to template directory, resolved with symlink handling
- **Content-ID Mapping**: Inline images use RFC 2822 Message-IDs to link attachments to HTML references
- **Security Modes**: Different SMTP authentication methods are encapsulated in separate methods

## Development Commands

### Setup Development Environment

```bash
python3 -m venv env
source env/bin/activate
pip install --editable .[dev,test]
```

### Testing

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_template_message.py

# Run specific test function
pytest tests/test_template_message.py::test_simple

# Run with coverage report
pytest --cov ./mailmerge --cov-report term-missing
```

### Linting and Code Quality

```bash
# Style checking
pycodestyle mailmerge tests setup.py

# Docstring checking
pydocstyle mailmerge tests setup.py

# Static analysis
pylint mailmerge tests setup.py

# Check MANIFEST.in
check-manifest

# Run all linters and tests in clean environment
tox
```

### Running Mailmerge Locally

```bash
# After pip install --editable, the mailmerge command is available
mailmerge --help

# Common usage patterns
mailmerge --sample  # Create sample files
mailmerge  # Dry run with first message
mailmerge --no-limit  # Dry run with all messages
mailmerge --no-dry-run  # Send first message for real
mailmerge --no-dry-run --no-limit  # Send all messages
```

## Testing Strategy

- Tests use `pytest` with fixtures in `tests/testdata/`
- Mock SMTP connections with `pytest-mock`
- Freeze time for deterministic date headers with `freezegun`
- Test data includes various email formats: plain text, HTML, markdown, multipart
- Coverage target: comprehensive coverage of all code paths

## Important Notes

- **Python Version**: Requires Python 3.10+ (matches Click 8.3 requirement; Python 3.6-3.9 are EOL or soon EOL)
- **Character Encoding**: Auto-detects ASCII vs UTF-8 based on message content
- **Multipart Message Structure**: Uses `multipart/related` for attachments, `multipart/alternative` for text/HTML variants
- **Jinja2 Configuration**: Uses `StrictUndefined` to catch template errors early
- **CSV Dialect Detection**: Auto-detects comma, semicolon, tab delimiters with CSV sniffer
- **BOM Handling**: Opens CSV files with `utf-8-sig` encoding to handle Excel-generated files
- **Rate Limiting**: Enforces inter-message delays based on messages-per-minute configuration
- **Dry Run Default**: CLI defaults to dry-run mode to prevent accidental mass emailing

## File Structure

```
mailmerge/
├── mailmerge/
│   ├── __init__.py           # Public API exports
│   ├── __main__.py           # CLI implementation
│   ├── template_message.py   # Template rendering and message construction
│   ├── sendmail_client.py    # SMTP client
│   └── exceptions.py         # Custom exceptions
├── tests/
│   ├── test_main.py          # CLI tests
│   ├── test_template_message.py  # Template rendering tests
│   ├── test_sendmail_client.py   # SMTP client tests
│   ├── test_ratelimit.py     # Rate limiting tests
│   └── testdata/             # Test fixtures
├── pyproject.toml            # Project metadata and dependencies
└── tox.ini                   # Multi-environment testing config
```

## Dependencies

**Core Runtime:**
- `click>=8.3` - CLI framework (requires 8.3+ for separate stderr capture by default; 8.1.x had different behavior)
- `jinja2` - Template engine
- `markdown` - Markdown to HTML conversion
- `html5lib` - HTML parsing for inline image transformation

**Development:**
- `pytest`, `pytest-cov`, `pytest-mock` - Testing framework
- `pycodestyle`, `pydocstyle`, `pylint` - Linters
- `freezegun` - Time mocking for tests
- `tox` - Multi-environment testing
