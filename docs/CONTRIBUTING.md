# Contributing to Pi Bridge

First off, thank you for considering contributing to Pi Bridge!

## How Can I Contribute?

### Reporting Bugs
- Ensure the bug was not already reported by searching on GitHub under [Issues](https://github.com/mcyork/pi-bridge/issues).
- If you're unable to find an open issue addressing the problem, [open a new one](https://github.com/mcyork/pi-bridge/issues/new). Be sure to include a **title and clear description**, as much relevant information as possible, and a **code sample** or an **executable test case** demonstrating the expected behavior that is not occurring.

### Suggesting Enhancements
- Open a new issue and describe the enhancement you have in mind.
- Please provide a clear and detailed explanation of the feature you want and why it's important.

### Pull Requests
- Fork the repo and create your branch from `main`.
- Make sure your code lints.
- Issue that pull request!

## Styleguides

### Code Style
- **Formatting**: Code is formatted with [Black](https://black.readthedocs.io/) (88 char line length)
- **Python**: Generally follows PEP 8 conventions
- **Consistency**: Run `black pi_bridge_tool/` before committing

### Before Submitting
- **Format code**: `black pi_bridge_tool/`
- **Test locally**: `pip install -e . && pi-bridge --help`
- **Test functionality**: Add a test Pi and run a command
- **Check syntax**: `python -m py_compile pi_bridge_tool/main.py`

Thanks again for your contribution!
