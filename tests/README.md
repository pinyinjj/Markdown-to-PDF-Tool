# Functional Tests for Markdown to PDF Tool

This directory contains functional tests for the Markdown to PDF Tool.

## Prerequisites

To run these tests, you need to have the following dependencies installed in your environment:

- `pytest`
- `playwright` (and its chromium browser: `playwright install chromium`)
- `pdf-watermark`
- `pillow`
- `markdown`

If you are using the project's virtual environment, you can install them with:

```bash
venv\Scripts\python.exe -m pip install pytest playwright pdf-watermark pillow markdown
venv\Scripts\python.exe -m playwright install chromium
```

## Running the Tests

You can run all tests using `pytest`:

```bash
venv\Scripts\python.exe -m pytest tests
```

Or run individual test scripts:

```bash
venv\Scripts\python.exe -m pytest tests/test_markdown_processor.py
venv\Scripts\python.exe -m pytest tests/test_watermark_utils.py
venv\Scripts\python.exe -m pytest tests/test_pdf_conversion.py
venv\Scripts\python.exe -m pytest tests/test_pdf_watermark.py
venv\Scripts\python.exe -m pytest tests/test_i18n.py
```

## Test Structure

- `test_i18n.py`: Tests internationalization and translation functions.
- `test_markdown_processor.py`: Tests Markdown parsing, front matter removal, and H1 title extraction.
- `test_watermark_utils.py`: Tests generation of watermark images from text using Pillow.
- `test_pdf_conversion.py`: Tests converting Markdown files to PDF using Playwright.
- `test_pdf_watermark.py`: Tests adding watermarks to PDF files using the `pdf-watermark` tool.
- `test_md_with_images.py`: Tests converting Markdown files with local image references.
