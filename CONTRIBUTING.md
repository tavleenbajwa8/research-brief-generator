# Contributing to Research Brief Generator

Thank you for your interest in contributing to the Research Brief Generator! This document provides guidelines and information for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Contributing Guidelines](#contributing-guidelines)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Reporting Issues](#reporting-issues)

## Code of Conduct

This project and everyone participating in it is governed by our Code of Conduct. By participating, you are expected to uphold this code.

## Getting Started

1. Fork the repository
2. Clone your fork locally
3. Create a new branch for your feature
4. Make your changes
5. Test your changes
6. Submit a pull request

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/research-brief-generator.git
   cd research-brief-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -e .[dev]
   ```

4. Set up environment variables:
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

## Contributing Guidelines

### Types of Contributions

We welcome the following types of contributions:

- **Bug fixes**: Fix issues and improve reliability
- **New features**: Add new functionality
- **Documentation**: Improve or add documentation
- **Tests**: Add or improve test coverage
- **Performance improvements**: Optimize code performance
- **Code quality**: Improve code structure and readability

### Before You Start

1. Check existing issues and pull requests to avoid duplication
2. Discuss major changes in an issue before starting work
3. Ensure your changes align with the project's goals and architecture

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_schemas.py

# Run tests with verbose output
pytest -v
```

### Writing Tests

- Write tests for all new functionality
- Ensure test coverage is maintained or improved
- Use descriptive test names
- Follow the existing test patterns
- Mock external dependencies appropriately

### Test Structure

- Unit tests go in `tests/`
- Use fixtures from `tests/conftest.py`
- Test both success and failure cases
- Test edge cases and boundary conditions

## Code Style

### Python Style Guide

We follow PEP 8 with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all function parameters and return values
- Use docstrings for all public functions and classes
- Follow the existing code style in the project

### Code Formatting

We use several tools to maintain code quality:

```bash
# Format code with Black
black app/ tests/ cli.py

# Sort imports with isort
isort app/ tests/ cli.py

# Check code style with flake8
flake8 app/ tests/ cli.py

# Type checking with mypy
mypy app/
```

### Pre-commit Hooks

Consider setting up pre-commit hooks to automatically format and check your code:

```bash
pip install pre-commit
pre-commit install
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass
2. Run code formatting tools
3. Update documentation if needed
4. Add tests for new functionality
5. Update the changelog if applicable

### Pull Request Guidelines

1. **Title**: Use a clear, descriptive title
2. **Description**: Provide a detailed description of changes
3. **Related Issues**: Link to related issues using keywords
4. **Screenshots**: Include screenshots for UI changes
5. **Testing**: Describe how you tested your changes

### Example Pull Request

```markdown
## Description
Add support for custom research depth levels in the CLI interface.

## Changes
- Added `--depth` parameter to CLI commands
- Updated schema validation for depth levels
- Added tests for depth parameter validation
- Updated documentation

## Testing
- [x] Unit tests pass
- [x] CLI integration tests pass
- [x] Manual testing with various depth levels

## Related Issues
Closes #123
```

## Reporting Issues

### Bug Reports

When reporting bugs, please include:

1. **Clear description** of the problem
2. **Steps to reproduce** the issue
3. **Expected behavior** vs actual behavior
4. **Environment details** (OS, Python version, etc.)
5. **Error messages** and stack traces
6. **Screenshots** if applicable

### Feature Requests

When requesting features, please include:

1. **Clear description** of the feature
2. **Use case** and motivation
3. **Proposed implementation** (if you have ideas)
4. **Alternative solutions** you've considered

### Issue Template

```markdown
## Summary
Brief description of the issue or feature request.

## Environment
- OS: [e.g., Ubuntu 20.04, Windows 10]
- Python Version: [e.g., 3.9.7]
- Package Version: [e.g., 1.0.0]

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What you expected to happen.

## Actual Behavior
What actually happened.

## Additional Information
Any other relevant information, logs, or screenshots.
```

## Getting Help

If you need help with contributing:

1. Check the documentation in the README
2. Look at existing issues and pull requests
3. Ask questions in issues or discussions
4. Join our community channels (if available)

## Recognition

Contributors will be recognized in:

- The project README
- Release notes
- Contributor statistics

Thank you for contributing to the Research Brief Generator! 