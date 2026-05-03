# Contributing to URIS-AI

Thank you for your interest in contributing to URIS-AI! This document provides guidelines and instructions for contributing.

## Code of Conduct

By participating in this project, you agree to maintain a respectful and inclusive environment for all contributors.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone <your-fork-url>`
3. Set up development environment (see [Setup Guide](docs/setup.md))
4. Create a feature branch: `git checkout -b feature/your-feature`

## Development Workflow

### 1. Before Making Changes

- Check existing issues and PRs to avoid duplication
- Discuss major changes in an issue first
- Ensure your local main branch is up to date

### 2. Making Changes

- Write clear, concise commit messages
- Follow the existing code style
- Add tests for new functionality
- Update documentation as needed

### 3. Code Quality

Run these checks before committing:

```bash
# Format code
poetry run black src/ tests/

# Lint code
poetry run ruff check src/ tests/

# Type check
poetry run mypy src/

# Run tests
poetry run pytest
```

### 4. Commit Messages

Follow conventional commits format:

```
<type>(<scope>): <subject>

<body>

<footer>
```

Types:

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

Examples:

```
feat(api): add flood risk prediction endpoint

Implements the /regions/{id}/risk endpoint that returns
flood risk predictions for a specific region.

Closes #123
```

### 5. Pull Requests

- Create a PR from your feature branch to `develop`
- Fill out the PR template completely
- Link related issues
- Ensure all CI checks pass
- Request review from maintainers

## Code Style

### Python

- Follow PEP 8 style guide
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use Black for formatting
- Use Ruff for linting

Example:

```python
def calculate_risk_score(
    flood_risk: float,
    traffic_impact: float,
    service_access: float,
) -> float:
    """
    Calculate Urban Risk Score from component scores.

    Args:
        flood_risk: Flood risk score (0-100)
        traffic_impact: Traffic impact score (0-100)
        service_access: Service accessibility score (0-100)

    Returns:
        Urban Risk Score (0-100)
    """
    weights = {"flood": 0.5, "traffic": 0.3, "service": 0.2}
    return (
        weights["flood"] * flood_risk
        + weights["traffic"] * traffic_impact
        + weights["service"] * service_access
    )
```

### Documentation

- Use docstrings for all public functions and classes
- Follow Google docstring format
- Include examples in docstrings when helpful
- Keep README.md up to date

### Testing

- Write unit tests for all new functions
- Write property-based tests for core algorithms
- Write integration tests for component interactions
- Aim for >80% code coverage

Example test:

```python
def test_calculate_risk_score():
    """Test Urban Risk Score calculation."""
    score = calculate_risk_score(
        flood_risk=80.0,
        traffic_impact=60.0,
        service_access=40.0,
    )
    assert 0 <= score <= 100
    assert score == pytest.approx(66.0)
```

## Project Structure

```
uris-ai/
├── src/uris_ai/          # Source code
│   ├── api/              # FastAPI application
│   ├── dashboard/        # Streamlit dashboard
│   ├── data/             # Data ingestion and processing
│   ├── ml/               # ML models and engines
│   ├── models/           # Database models
│   ├── services/         # Business logic services
│   └── utils/            # Utility functions
├── tests/                # Test files
├── infrastructure/       # Infrastructure as Code
├── docs/                 # Documentation
└── scripts/              # Utility scripts
```

## Testing Guidelines

### Unit Tests

- Test individual functions and classes
- Mock external dependencies
- Use fixtures for common test data

### Property-Based Tests

- Use Hypothesis for property-based testing
- Test universal properties of algorithms
- Run minimum 100 iterations per property

### Integration Tests

- Test component interactions
- Use test containers for databases
- Mock external APIs

### End-to-End Tests

- Test complete user workflows
- Run against staging environment
- Use Selenium/Playwright for UI tests

## Documentation

### Code Documentation

- Docstrings for all public APIs
- Inline comments for complex logic
- Type hints for all function signatures

### User Documentation

- Update README.md for user-facing changes
- Add examples to docs/ folder
- Keep API documentation current

### Developer Documentation

- Document architecture decisions
- Explain complex algorithms
- Provide setup instructions

## Review Process

1. **Automated Checks**
   - Linting (Ruff)
   - Type checking (mypy)
   - Tests (pytest)
   - Security scan (Trivy)

2. **Code Review**
   - At least one approval required
   - Address all review comments
   - Keep discussions constructive

3. **Merge**
   - Squash commits if needed
   - Update changelog
   - Delete feature branch after merge

## Release Process

1. Update version in `pyproject.toml`
2. Update CHANGELOG.md
3. Create release branch: `release/v1.0.0`
4. Test thoroughly
5. Merge to main
6. Tag release: `git tag v1.0.0`
7. Deploy to production

## Getting Help

- Check existing documentation
- Search existing issues
- Ask in discussions
- Contact maintainers

## Recognition

Contributors will be recognized in:

- CONTRIBUTORS.md file
- Release notes
- Project documentation

Thank you for contributing to URIS-AI!
