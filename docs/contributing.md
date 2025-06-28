# Contributing Guide

## Development Setup

1. **Fork and Clone**
   ```bash
   git clone https://github.com/your-user-name/py-isa-xform.git
   cd py-isa-xform
   ```

2. **Environment Setup**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e .
   pip install pytest pytest-cov black flake8 mypy
   ```

3. **Verify Setup**
   ```bash
   python -m pytest tests/ -v
   black --check src/ tests/
   flake8 src/ tests/
   ```

## Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   # or: git checkout -b fix/your-bug-description
   ```

2. **Make Changes**
   - Follow existing code style
   - Add tests for new functionality
   - Update documentation as needed

3. **Test Changes**
   ```bash
   python -m pytest tests/ -v --cov=src/isa_xform
   black src/ tests/
   flake8 src/ tests/
   mypy src/isa_xform/
   ```

4. **Commit with Clear Messages**
   ```bash
   git commit -m "feat: add support for custom directives

   - Add CustomDirectiveNode class
   - Implement directive parsing in Parser
   - Add tests and documentation"
   ```

5. **Push and Create PR**
   ```bash
   git push origin feature/your-feature-name
   ```

## Testing

For detailed testing information, see [Testing Guide](testing.md).

### Test Requirements
- Write tests for all new functionality
- Test both success and failure cases
- Use descriptive test names

### Quick Test Commands
```bash
# All tests
python -m pytest tests/ -v

# Specific file
python -m pytest tests/test_parser.py -v

# With coverage
python -m pytest tests/ --cov=src/isa_xform --cov-report=html
```

## Pull Request Guidelines

### Before Submitting
1. All tests pass
2. Code passes linting and formatting checks
3. Documentation updated
4. Changes tested

### PR Description Template
```markdown
## Description
Brief description of changes.

## Changes Made
- List of specific changes
- New features/bug fixes

## Testing
- How changes were tested
- New tests added

## Related Issues
Closes #123
```

## Issue Reporting

### Bug Reports
Include:
- Clear description
- Steps to reproduce
- Expected vs actual behavior
- Environment details (OS, Python version)
- Minimal code example

### Feature Requests
Include:
- Description and use case
- Proposed implementation
- Code examples

## Documentation

For architecture and API details, see:
- [Architecture](architecture.md) - System design
- [API Reference](api-reference.md) - Complete API docs
- [Parser](parser.md) - Parser implementation
- [Symbol Table](symbol_table.md) - Symbol management

### Documentation Updates
- Update docs when adding features
- Keep examples current
- Add docstrings for public APIs
- Maintain consistent formatting

## Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and general discussion
- **PR Reviews**: Ask questions during code review

## Recognition

Contributors are recognized in:
- README.md contributor list (upcoming)
- Release notes for significant contributions
- Documentation attribution

## Code of Conduct

- Be respectful and inclusive
- Use welcoming language
- Be collaborative and constructive
- Focus on community benefit

## License

Contributions are licensed under the same license as the project. 