# Contributing to Dijital Kütüphane

Thank you for your interest in contributing to Dijital Kütüphane! This document provides guidelines and instructions for contributing to the project.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Submitting Changes](#submitting-changes)
- [Coding Standards](#coding-standards)
- [Reporting Bugs](#reporting-bugs)
- [Suggesting Enhancements](#suggesting-enhancements)

## Code of Conduct

This project adheres to a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior via [GitHub Security Advisories](https://github.com/fatih-es/dijital-kutuphane/security/advisories) or contact the project maintainer via [GitHub Discussions](https://github.com/fatih-es/dijital-kutuphane/discussions).

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- Poppler (for PDF rendering)
- Tesseract-OCR (optional, for OCR features)

### Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/fatih-es/dijital-kutuphane.git
   cd dijital-kutuphane
   ```

3. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # If available
   ```

5. Copy environment templates:
   ```bash
   cp .env.example .env
   cp config.json.example config.json
   ```

6. Configure your environment variables in `.env`

7. Run the application:
   ```bash
   python main.py
   ```

## Submitting Changes

### Workflow

1. Create a new branch from `main`:
   ```bash
   git checkout -b feature/your-feature-name
   # or
   git checkout -b fix/your-bug-fix
   ```

2. Make your changes following the coding standards

3. Add tests for your changes (if applicable)

4. Run tests:
   ```bash
   pytest
   ```

5. Run linting:
   ```bash
   ruff check .
   black .
   mypy .
   ```

6. Commit your changes with a descriptive message:
   ```bash
   git commit -m "Add: feature description"
   # or
   git commit -m "Fix: bug description"
   ```

7. Push to your fork:
   ```bash
   git push origin feature/your-feature-name
   ```

8. Create a Pull Request

### Pull Request Guidelines

- Fill in the PR template completely
- Link related issues
- Describe what you changed and why
- Add screenshots for UI changes
- Ensure all tests pass
- Update documentation if needed

## Coding Standards

### Python Code Style

- Follow PEP 8 guidelines
- Use type hints where appropriate
- Write docstrings for functions and classes
- Keep functions small and focused
- Use meaningful variable and function names

### Example:

```python
def process_pdf(file_path: str, config: dict) -> dict:
    """
    Process a PDF file and extract metadata.
    
    Args:
        file_path: Path to the PDF file
        config: Configuration dictionary
        
    Returns:
        Dictionary containing extracted metadata
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not a valid PDF
    """
    # Implementation
    pass
```

### Git Commit Messages

Use conventional commit format:

- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting, etc.)
- `refactor:` Code refactoring
- `test:` Adding or updating tests
- `chore:` Maintenance tasks

Example:
```
feat: add PDF metadata extraction
fix: resolve memory leak in image processing
docs: update API documentation
```

## Reporting Bugs

### Before Reporting

1. Check existing issues to avoid duplicates
2. Verify the bug still exists in the latest version
3. Gather information about the bug

### Bug Report Template

When reporting a bug, please include:

- **Description**: Clear description of the bug
- **Steps to Reproduce**: Detailed steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Environment**:
  - OS: [e.g., Windows 11, Ubuntu 22.04]
  - Python version: [e.g., 3.11.0]
  - Application version: [e.g., 1.0.0]
- **Logs**: Relevant error logs
- **Screenshots**: If applicable

## Suggesting Enhancements

### Feature Requests

We welcome feature suggestions! When requesting a feature:

1. Check if it's already been requested
2. Describe the use case clearly
3. Explain why this feature would be useful
4. Provide examples or mockups if applicable

### Implementation

If you want to implement a feature:

1. Open an issue to discuss it first
2. Get feedback from maintainers
3. Follow the development setup above
4. Submit a pull request

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_auth.py

# Run with coverage
pytest --cov=.
```

### Writing Tests

- Write unit tests for individual functions
- Write integration tests for API endpoints
- Test edge cases and error conditions
- Keep tests independent and fast

## Questions?

If you have questions:

- Open an issue with the `question` label
- Check existing documentation
- Join our [GitHub Discussions](https://github.com/fatih-es/dijital-kutuphane/discussions)

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to Dijital Kütüphane! 🚀
